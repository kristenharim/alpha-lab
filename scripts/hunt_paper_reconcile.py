"""EXP-OPS-REALITY (layer D): reconcile the hunt2026 paper books against the Alpaca PAPER account.

READ-ONLY vs the broker — this script only ever calls get_orders / get_all_positions; it never
submits, cancels, or modifies anything. It measures the gap between the frozen backtest execution
model (10 bps/side stocks, 2 bps/side ETFs, next-day fills, no rejects — research/hunt2026/
harness.py) and reality:

  per run-date: side-adjusted slippage per h26 fill vs that date's ledger reference close,
  rejected/zero-fill order counts, intended-vs-actual position gap, per-book slippage drag
  (fills pro-rated by each book's share of the aggregate target), silent-flat detection
  (nonzero targets, no fills, no position, 2+ consecutive nights -> alarm).

Agreement bands are pre-registered in research/hunt2026/preregistrations/ops-reality-2026-07-10.md;
one JSONL row per night appends to ledgers/hunt2026/_reconcile.jsonl.

Usage: .venv/bin/python scripts/hunt_paper_reconcile.py            # latest ledger date
       .venv/bin/python scripts/hunt_paper_reconcile.py --since 2026-07-10   # replay from date

Nightly wiring (Director-approved plist edit required — research agents may not alter
deployments): run this right after hunt_paper_run in com.rimrim.hunt2026-paper by making
ProgramArguments a shell line, i.e.
  /bin/zsh -c '.venv/bin/python scripts/hunt_paper_run.py --live;
               .venv/bin/python scripts/hunt_paper_reconcile.py'
An evening reconcile measures the PREVIOUS run-date's fills (they happen at today's open).
"""
import argparse
import datetime as dt
import json
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

HUNT = ROOT / "research" / "hunt2026"
LEDGER_DIR = ROOT / "ledgers" / "hunt2026"
RECONCILE = LEDGER_DIR / "_reconcile.jsonl"
META = json.loads((HUNT / "sandbox_meta.json").read_text())
ETFS = set(META["etfs"])

# Pre-registered agreement bands (ops-reality-2026-07-10.md) — echoed in the report only;
# breaches are logged, never acted on here.
BANDS = {"stock_bps": (0.0, 15.0), "etf_bps": (0.0, 5.0),
         "reject_rate": 0.02, "book_drag_bps_month": 30.0}
TRAIL_MIN_FILLS = 20


# ---------- ledger ----------

def load_ledger_rows() -> dict[str, dict[str, dict]]:
    """{date: {book: last LIVE row}} across all book ledgers (re-runs append duplicates; last wins)."""
    out: dict[str, dict[str, dict]] = defaultdict(dict)
    for path in sorted(LEDGER_DIR.glob("*.jsonl")):
        if path.name == RECONCILE.name:
            continue
        for line in path.read_text().splitlines():
            row = json.loads(line)
            if row.get("mode") == "live":
                out[row["date"]][row["book"]] = row
    return dict(out)


# ---------- broker (the only network-touching part; read-only) ----------

def orders_from_client(tc, since: str) -> list[dict]:
    """All closed orders since `since` as plain dicts. get_orders only — never submits/cancels."""
    from alpaca.trading.enums import QueryOrderStatus
    from alpaca.trading.requests import GetOrdersRequest
    orders = tc.get_orders(filter=GetOrdersRequest(
        status=QueryOrderStatus.CLOSED, limit=500,
        after=dt.datetime.fromisoformat(since)))
    out = []
    for o in orders:
        out.append({
            "ticker": o.symbol,
            "side": str(getattr(o.side, "value", o.side)),
            "status": str(getattr(o.status, "value", o.status)).lower(),
            "filled_qty": float(o.filled_qty or 0),
            "fill_price": float(o.filled_avg_price) if o.filled_avg_price else None,
            "client_order_id": getattr(o, "client_order_id", None) or "",
            "submitted": str(getattr(o, "submitted_at", ""))[:10],
        })
    return out


def positions_from_client(tc) -> dict[str, float]:
    return {p.symbol: float(p.qty) for p in tc.get_all_positions()}


# ---------- pure core (offline-testable) ----------

def bucket_orders(orders: list[dict], run_dates: list[str]) -> dict[str, list[dict]]:
    """Attribute each h26 order to the latest run-date <= its submission date (orders submitted
    Friday night fill Monday; they still belong to Friday's run)."""
    run_dates = sorted(run_dates)
    out: dict[str, list[dict]] = {d: [] for d in run_dates}
    for o in orders:
        if not o["client_order_id"].startswith("h26"):
            continue
        eligible = [d for d in run_dates if d <= (o["submitted"] or "9999")]
        if eligible:
            out[eligible[-1]].append(o)
    return out


def _slippage_bps(o: dict, ref: float) -> float:
    """Side-adjusted cost vs reference close; positive = worse than model."""
    sign = 1.0 if o["side"] == "buy" else -1.0
    return sign * (o["fill_price"] - ref) / ref * 1e4


def reconcile_date(date: str, books: dict[str, dict], orders: list[dict],
                   positions: dict[str, float], closes: dict[str, float],
                   prior_flat: dict[str, int] | None = None) -> dict:
    """One night's reconciliation row. `books` = {book: ledger row} incl. '_account';
    `closes` = {symbol: run-date reference close}; `prior_flat` = consecutive-flat-night
    counts per book from the previous reconcile row."""
    acct = books.get("_account", {})
    agg = acct.get("target_dollars", {})
    prior_flat = prior_flat or {}

    fills, rejects, canceled, partials, replaced = [], [], 0, 0, 0
    for o in orders:
        if o["filled_qty"] > 0 and o["fill_price"]:
            ref = closes.get(o["ticker"])
            # a fill whose order did not end "filled" (e.g. day-order partial that canceled
            # the remainder at the close) is a PARTIAL fill, flagged but still measured
            is_partial = o["status"] not in ("filled",)
            partials += int(is_partial)
            fills.append({**o, "ref_close": ref,
                          "class": "etf" if o["ticker"] in ETFS else "stock",
                          "partial": is_partial,
                          "slippage_bps": round(_slippage_bps(o, ref), 2) if ref else None})
        elif o["status"] == "replaced":
            replaced += 1     # broker/venue order replacement — classified, not a reject
        elif o["status"] == "canceled":
            # our own cancel_all_orders on idempotent re-runs — expected, not a broker reject
            canceled += 1
        else:   # rejected / expired / closed-with-zero-fill = the pre-registered reject metric
            rejects.append({"ticker": o["ticker"], "status": o["status"]})

    def _stats(cls):
        xs = sorted(f["slippage_bps"] for f in fills
                    if f["class"] == cls and f["slippage_bps"] is not None)
        if not xs:
            return {"n": 0, "mean_bps": None, "median_bps": None}
        return {"n": len(xs), "mean_bps": round(sum(xs) / len(xs), 2),
                "median_bps": round(xs[len(xs) // 2], 2)}

    # intended vs actual: |aggregate target dollars - held dollars at ref close| / notional
    gap = 0.0
    for sym in set(agg) | set(positions):
        ref = closes.get(sym)
        held = positions.get(sym, 0.0) * ref if ref else 0.0
        gap += abs(agg.get(sym, 0.0) - held)
    notional = acct.get("notional") or 1.0
    # foreign positions: held symbols in NO book target and not a benchmark leg — this is the
    # dead stat-arb residue (+ any AMAT-style leftover). Empty => flatten complete. Directly
    # answers "did the stat-arb flatten / AMAT clear?" each night.
    known = set(agg)
    foreign = {sym: q for sym, q in positions.items()
               if sym not in known and abs(q) > 1e-9}
    foreign_dollars = round(sum(abs(q) * (closes.get(s) or 0.0) for s, q in foreign.items()), 2)
    # per-book: slippage cost dollars pro-rated by the book's share of the aggregate target
    book_rows, alarms = {}, []
    for name, row in books.items():
        if name == "_account":
            continue
        drag = 0.0
        for f in fills:
            sym, bd = f["ticker"], row.get("target_dollars", {})
            if sym in bd and f["slippage_bps"] is not None and agg.get(sym):
                share = bd[sym] / agg[sym]
                drag += f["slippage_bps"] / 1e4 * f["filled_qty"] * f["fill_price"] * share
        has_fill = any(f["ticker"] in row.get("target_dollars", {}) for f in fills)
        has_pos = any(positions.get(s, 0.0) != 0.0 for s in row.get("target_dollars", {}))
        flat = row.get("gross", 0) > 0 and not has_fill and not has_pos
        flat_nights = prior_flat.get(name, 0) + 1 if flat else 0
        if flat_nights >= 2:
            alarms.append(f"SILENT-FLAT: {name} has nonzero targets but no fills and no "
                          f"position for {flat_nights} consecutive nights")
        book_rows[name] = {"model_nav": row.get("nav"),
                           "drag_bps": round(drag / (row.get("notional") or 1.0) * 1e4, 3),
                           "flat_nights": flat_nights}

    n = len(fills) + len(rejects)   # canceled excluded: self-cancels are not execution events
    if foreign:
        alarms.append(f"FOREIGN-POSITIONS: {len(foreign)} held symbol(s) in no book target "
                      f"(${foreign_dollars:,.0f}) — stat-arb flatten / AMAT not yet complete")
    return {"date": date, "run_at": dt.datetime.now().isoformat(timespec="seconds"),
            "n_orders": n, "n_fills": len(fills), "n_rejects": len(rejects),
            "n_canceled": canceled, "n_partial": partials, "n_replaced": replaced,
            "reject_rate": round(len(rejects) / n, 4) if n else None,
            "slippage": {"stock": _stats("stock"), "etf": _stats("etf")},
            "position_gap_frac": round(gap / notional, 4),
            "foreign_positions": {"n": len(foreign), "dollars": foreign_dollars,
                                  "symbols": sorted(foreign)},
            "fills": fills, "rejects": rejects, "books": book_rows, "alarms": alarms}


def trailing_means(rows: list[dict]) -> dict:
    """Trailing-mean slippage over the last >=TRAIL_MIN_FILLS fills per class across all
    reconcile rows — the pre-registered agreement statistic."""
    out = {}
    for cls in ("stock", "etf"):
        xs = [f["slippage_bps"] for r in rows for f in r.get("fills", [])
              if f["class"] == cls and f.get("slippage_bps") is not None][-TRAIL_MIN_FILLS:]
        out[cls] = {"n": len(xs),
                    "mean_bps": round(sum(xs) / len(xs), 2) if len(xs) >= TRAIL_MIN_FILLS else None}
    return out


# ---------- report ----------

def print_report(row: dict, trail: dict) -> None:
    print(f"\n== reconcile {row['date']} ==")
    fp = row.get("foreign_positions", {})
    if fp.get("n"):
        print(f"  FOREIGN positions (stat-arb/AMAT residue): {fp['n']} sym ${fp['dollars']:,.0f} "
              f"{fp['symbols'][:8]}{'…' if fp['n'] > 8 else ''}  <- flatten NOT complete")
    else:
        print("  foreign positions: none (stat-arb flatten complete)")
    if row.get("n_canceled"):
        print(f"  {row['n_canceled']} order(s) self-canceled by re-runs (not counted as rejects)")
    if row["n_orders"] == 0:
        print("  no fills yet — nothing to measure (orders may still be queued for next open)")
        return
    print(f"  orders {row['n_orders']}  fills {row['n_fills']} "
          f"(partial {row.get('n_partial', 0)})  rejects {row['n_rejects']} "
          f"(rate {row['reject_rate']:.1%}, band < {BANDS['reject_rate']:.0%})  "
          f"replaced {row.get('n_replaced', 0)}")
    for cls, band in (("stock", BANDS["stock_bps"]), ("etf", BANDS["etf_bps"])):
        s, t = row["slippage"][cls], trail.get(cls, {})
        if s["n"]:
            tm = f"{t['mean_bps']:+.1f}" if t.get("mean_bps") is not None else "n<20"
            print(f"  {cls:<5} slippage n={s['n']}  mean {s['mean_bps']:+.1f} bps  "
                  f"median {s['median_bps']:+.1f}  trailing {tm}  band {band}")
    print(f"  position gap {row['position_gap_frac']:.2%} of notional")
    for name, b in sorted(row["books"].items()):
        flat = f"  FLAT x{b['flat_nights']}" if b["flat_nights"] else ""
        print(f"    {name:<22} model_nav {b['model_nav']}  drag {b['drag_bps']:+.2f} bps{flat}")
    for a in row["alarms"]:
        print(f"  !! {a}")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--since", help="replay all ledger run-dates >= this date (YYYY-MM-DD); "
                                    "default: latest ledger date only")
    args = ap.parse_args()

    ledger = load_ledger_rows()
    if not ledger:
        sys.exit("no live ledger rows in ledgers/hunt2026/")
    dates = sorted(d for d in ledger if not args.since or d >= args.since)
    if not args.since:
        dates = dates[-1:]

    import os

    from core.env import load_dotenv
    load_dotenv()
    key, secret = os.environ.get("ALPACA_API_KEY_ID"), os.environ.get("ALPACA_API_SECRET_KEY")
    if not (key and secret):
        sys.exit("needs ALPACA_API_KEY_ID / ALPACA_API_SECRET_KEY (paper keys) in env or .env")
    from alpaca.trading.client import TradingClient
    tc = TradingClient(key, secret, paper=True)   # read-only usage: get_orders / get_all_positions
    orders = orders_from_client(tc, since=dates[0])
    # ponytail: positions are a NOW snapshot (broker keeps no history) — gap/flat metrics are
    # exact for the nightly run, indicative only when replaying old dates via --since
    positions = positions_from_client(tc)

    # reference closes: adjusted closes for every symbol any run-date touched (same source
    # the panel builder uses). Network; tests feed reconcile_date a dict directly.
    symbols = sorted({s for d in dates for b in ledger[d].values()
                      for s in b.get("target_dollars", {})} | set(positions))
    from core.data.prices import fetch_prices_yf
    px = fetch_prices_yf(symbols, start=(dt.date.fromisoformat(dates[0])
                                         - dt.timedelta(days=7)).isoformat(), end=None)

    buckets = bucket_orders(orders, dates)
    prior_rows = ([json.loads(x) for x in RECONCILE.read_text().splitlines()]
                  if RECONCILE.exists() else [])
    prior_flat = {n: b.get("flat_nights", 0)
                  for n, b in (prior_rows[-1]["books"].items() if prior_rows else [])}
    with RECONCILE.open("a") as f:
        for d in dates:
            closes = {}
            avail = px.loc[px.index <= d]
            if len(avail):
                closes = {s: float(v) for s, v in avail.iloc[-1].items() if v == v}
            row = reconcile_date(d, ledger[d], buckets.get(d, []), positions, closes, prior_flat)
            prior_flat = {n: b["flat_nights"] for n, b in row["books"].items()}
            prior_rows.append(row)
            print_report(row, trailing_means(prior_rows))
            f.write(json.dumps(row) + "\n")
    print(f"\nappended {len(dates)} row(s) -> {RECONCILE}")


if __name__ == "__main__":
    main()
