"""EXP-OPS-REALITY (layer D): reconcile the hunt2026 paper books against the Alpaca PAPER account.

READ-ONLY vs the broker: this script only ever calls get_orders / get_all_positions; it never
submits, cancels, or modifies anything. It measures the gap between the frozen backtest execution
model (10 bps/side stocks, 2 bps/side ETFs, next-day fills, no rejects; research/hunt2026/
harness.py) and reality:

  per run-date: side-adjusted slippage per h26 fill vs that date's ledger reference close,
  rejected/zero-fill order counts, intended-vs-actual position gap, per-book slippage drag
  (fills pro-rated by each book's share of the aggregate target), silent-flat detection
  (nonzero targets, no fills, no position, 2+ consecutive nights -> alarm).

Agreement bands are pre-registered in research/hunt2026/preregistrations/ops-reality-2026-07-10.md;
one JSONL row per night appends to ledgers/hunt2026/_reconcile.jsonl.

Usage: .venv/bin/python scripts/hunt_paper_reconcile.py            # latest ledger date
       .venv/bin/python scripts/hunt_paper_reconcile.py --since 2026-07-10   # replay from date

Nightly wiring (Director-approved plist edit required, research agents may not alter
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

# Cutover 2026-07-15 (memos/mc-account-isolation-cutover-2026-07-15.md): momentum_concentrated
# executes in its own dedicated Alpaca paper account, so it is EXCLUDED from the shared-account
# reconcile below and reconciled exactly (sole book in its account) into _reconcile_mc.jsonl.
MC_BOOK = "momentum_concentrated"
MC_CRED_NAMES = ("ALPACA_MC_API_KEY_ID", "ALPACA_MC_API_SECRET_KEY")
RECONCILE_MC = LEDGER_DIR / "_reconcile_mc.jsonl"

# Pre-registered agreement bands (research/hunt2026/preregistrations/ops-reality-2026-07-10.md).
# Enforced exactly as pre-registered, never re-tuned here (§Stop-iterating: this harness gets no
# parameters to sweep):
#   - slippage: the statistic is the TRAILING MEAN over the last >=TRAIL_MIN_FILLS fills per class,
#     never a single night. A per-night breach is LOGGED ONLY; single fills embed overnight drift
#     (measured per-fill stdev ~250 bps against a 15 bps band), so one night carries no signal.
#     The decision trigger is the same band breached on the trailing statistic for
#     SLIPPAGE_BREACH_NIGHTS consecutive nights (§Failure/kill).
#   - reject rate: a per-night band, "< 2% of h26-tagged orders per night"; >= 2% is a listed
#     Alternative Result (sizing/tradability bugs). Operational, not noisy like slippage, so it
#     alarms the same night; 2026-07-15 lost 19/19 orders in silence before this was wired.
BANDS = {"stock_bps": (0.0, 15.0), "etf_bps": (0.0, 5.0),
         "reject_rate": 0.02, "book_drag_bps_month": 30.0}
TRAIL_MIN_FILLS = 20
SLIPPAGE_BREACH_NIGHTS = 10   # pre-registered decision trigger; consecutive nights out of band


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

def orders_from_client(tc, since: str, statuses: str = "closed") -> list[dict]:
    """Orders since `since` as plain dicts. get_orders only, never submits/cancels.
    `statuses`: "closed" (default; the execution/slippage metric), "open", or "all"
    (open+closed, used only to observe pending flatten orders for foreign positions)."""
    from alpaca.trading.enums import QueryOrderStatus
    from alpaca.trading.requests import GetOrdersRequest
    status = {"closed": QueryOrderStatus.CLOSED, "open": QueryOrderStatus.OPEN,
              "all": QueryOrderStatus.ALL}[statuses]
    orders = tc.get_orders(filter=GetOrdersRequest(
        status=status, limit=500, after=dt.datetime.fromisoformat(since)))
    out = []
    for o in orders:
        out.append({
            "ticker": o.symbol,
            "side": str(getattr(o.side, "value", o.side)),
            "status": str(getattr(o.status, "value", o.status)).lower(),
            "qty": float(getattr(o, "qty", 0) or 0),          # submitted quantity
            "filled_qty": float(o.filled_qty or 0),
            "fill_price": float(o.filled_avg_price) if o.filled_avg_price else None,
            "client_order_id": getattr(o, "client_order_id", None) or "",
            "submitted": str(getattr(o, "submitted_at", ""))[:10],
        })
    return out


def positions_from_client(tc) -> dict[str, float]:
    return {p.symbol: float(p.qty) for p in tc.get_all_positions()}


def account_equity(tc) -> float | None:
    """Read-only account equity (get_account only). None if unavailable."""
    try:
        return float(tc.get_account().equity)
    except Exception:
        return None


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


def foreign_decomposition(foreign: dict[str, float], closes: dict[str, float], price_asof: str,
                          symbol_orders: dict[str, list[dict]] | None = None,
                          equity: float | None = None) -> tuple[list[dict], dict]:
    """Read-only decomposition of the foreign (in-no-book-target) positions. Returns
    (per-position rows, account-level totals). A flatten order for a position is a closed/open
    order on that symbol whose side OPPOSES the holding (sell to flatten a long, buy a short).
    Pure: `symbol_orders` = {symbol: [order dicts]} (may be None); `equity` may be None."""
    symbol_orders = symbol_orders or {}
    rows: list[dict] = []
    gross_long = gross_short = net = 0.0
    priced_ct = unpriced_ct = 0
    for sym in sorted(foreign):
        q = foreign[sym]
        p = closes.get(sym)
        priced = p is not None and p == p and p != 0.0     # p==p rejects NaN
        price = float(p) if priced else None
        mv = round(q * price, 2) if priced else None                 # signed market value
        amv = round(abs(q) * price, 2) if priced else None           # absolute market value
        if priced:
            priced_ct += 1
            net += q * price
            if q > 0:
                gross_long += q * price
            else:
                gross_short += -q * price
        else:
            unpriced_ct += 1
        want = "sell" if q > 0 else "buy"
        f_orders = [o for o in symbol_orders.get(sym, []) if o.get("side") == want]
        sub = round(sum(abs(float(o.get("qty") or 0)) for o in f_orders), 6)
        fil = round(sum(abs(float(o.get("filled_qty") or 0)) for o in f_orders), 6)
        rows.append({
            "symbol": sym,
            "qty": q,
            "side": "long" if q > 0 else "short",
            "price": price,
            "market_value": mv,
            "abs_market_value": amv,
            "price_asof": price_asof,
            "priced": priced,
            "flatten_order": bool(f_orders),
            "flatten_submitted_qty": sub,
            "flatten_filled_qty": fil,
            "flatten_remaining_qty": round(max(sub - fil, 0.0), 6),
            "order_status": f_orders[-1]["status"] if f_orders else None,
        })
    gross = round(gross_long + gross_short, 2)
    totals = {
        "gross_long": round(gross_long, 2),
        "gross_short": round(gross_short, 2),
        "net": round(net, 2),
        "gross": gross,
        "priced_count": priced_ct,
        "unpriced_count": unpriced_ct,
        "symbol_count": len(foreign),
        "equity": round(equity, 2) if equity else None,
        "gross_over_equity": round(gross / equity, 4) if equity else None,
        "net_over_equity": round(net / equity, 4) if equity else None,
    }
    return rows, totals


def _slippage_bps(o: dict, ref: float) -> float:
    """Side-adjusted cost vs reference close; positive = worse than model."""
    sign = 1.0 if o["side"] == "buy" else -1.0
    return sign * (o["fill_price"] - ref) / ref * 1e4


def _drift_exec_bps(o: dict, ref: float, open_px: float | None) -> tuple[float | None, float | None]:
    """Split the pre-registered slippage into the two things it actually contains. The run submits
    after the close and the fill lands at the NEXT open, so every fill inherits the overnight gap
    before execution begins:
        drift = side-adjusted (next open - run-date close) / close     <- the market, not us
        exec  = side-adjusted (fill - next open) / next open           <- what execution cost
    drift + exec is slippage_bps to rounding. Reported only; the pre-registered statistic and its
    bands are untouched, this just says which half moved."""
    if not open_px:
        return None, None
    sign = 1.0 if o["side"] == "buy" else -1.0
    return (round(sign * (open_px - ref) / ref * 1e4, 2),
            round(sign * (o["fill_price"] - open_px) / open_px * 1e4, 2))


def opens_by_session(op) -> dict[str, dict[str, float]]:
    """{session date: {symbol: adjusted open}}. Keyed by session, not by run date, because a
    20:30 run's orders carry the NEXT calendar day as their submitted date while a by-hand
    daytime run's carry the same day, and each fills in its own session."""
    if op is None:
        return {}
    return {str(d)[:10]: {s: float(v) for s, v in row.items() if v == v}
            for d, row in op.iterrows()}


def _fill_open(opens: dict[str, dict[str, float]], o: dict) -> float | None:
    """The open of the session this order actually filled in: the first session on or after its
    submitted date. None when unknown, which leaves the split unreported rather than misaligned."""
    sub = o.get("submitted")
    if not (opens and sub):
        return None
    sessions = [d for d in opens if d >= sub]
    return opens[min(sessions)].get(o["ticker"]) if sessions else None


def drop_reprocessed_dates(prior_rows: list[dict], dates: list[str]) -> list[dict]:
    """Drop any existing row whose date is about to be recomputed, so a same-date rerun
    replaces the row instead of appending a duplicate (idempotent per date)."""
    dates = set(dates)
    return [r for r in prior_rows if r["date"] not in dates]


def reconcile_date(date: str, books: dict[str, dict], orders: list[dict],
                   positions: dict[str, float], closes: dict[str, float],
                   prior_flat: dict[str, int] | None = None,
                   symbol_orders: dict[str, list[dict]] | None = None,
                   equity: float | None = None,
                   opens: dict[str, float] | None = None) -> dict:
    """One night's reconciliation row. `books` = {book: ledger row} incl. '_account';
    `closes` = {symbol: run-date reference close}; `prior_flat` = consecutive-flat-night
    counts per book from the previous reconcile row. `symbol_orders`/`equity` are optional
    read-only observability inputs for the foreign-position decomposition (default off).
    `opens` = {session date: {symbol: open}}, the price each fill actually landed at; optional,
    and used only to decompose slippage into overnight drift vs execution."""
    opens = opens or {}
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
            drift_bps, exec_bps = _drift_exec_bps(o, ref, _fill_open(opens, o)) if ref else (None, None)
            fills.append({**o, "ref_close": ref,
                          "class": "etf" if o["ticker"] in ETFS else "stock",
                          "partial": is_partial,
                          "slippage_bps": round(_slippage_bps(o, ref), 2) if ref else None,
                          "drift_bps": drift_bps, "exec_bps": exec_bps})
        elif o["status"] == "replaced":
            replaced += 1     # broker/venue order replacement, classified, not a reject
        elif o["status"] == "canceled":
            # our own cancel_all_orders on idempotent re-runs, expected, not a broker reject
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
    # foreign positions: held symbols in NO book target and not a benchmark leg; this is the
    # dead stat-arb residue (+ any AMAT-style leftover). Empty => flatten complete. Directly
    # answers "did the stat-arb flatten / AMAT clear?" each night.
    known = set(agg)
    foreign = {sym: q for sym, q in positions.items()
               if sym not in known and abs(q) > 1e-9}
    foreign_dollars = round(sum(abs(q) * (closes.get(s) or 0.0) for s, q in foreign.items()), 2)
    foreign_rows, foreign_totals = foreign_decomposition(foreign, closes, date, symbol_orders, equity)
    flatten_remaining_total = round(sum(r["flatten_remaining_qty"] for r in foreign_rows), 6)
    # "flatten complete" ONLY when broker positions AND remaining flatten quantities are both zero
    flatten_complete = len(foreign) == 0 and flatten_remaining_total == 0.0
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
    reject_rate = round(len(rejects) / n, 4) if n else None
    if not flatten_complete:
        alarms.append(f"FOREIGN-POSITIONS: {len(foreign)} held symbol(s) in no book target "
                      f"(${foreign_dollars:,.0f}), {flatten_remaining_total:g} flatten share(s) "
                      f"remaining — stat-arb flatten / AMAT not yet complete")
    # The reject_rate band was pre-registered and printed but never alarmed, so 2026-07-15 lost
    # 19/19 orders to broker expiry in silence (exit 1 that day came from FOREIGN-POSITIONS alone).
    # "rejects" here is the pre-registered zero-fill metric (rejected OR expired OR closed unfilled);
    # the wording says so, because "N rejected" sent the 2026-07-16 investigation the wrong way.
    if reject_rate is not None and reject_rate >= BANDS["reject_rate"]:   # pre-reg: band is "< 2%"
        alarms.append(f"REJECT-RATE: {len(rejects)}/{n} order(s) ({reject_rate:.0%}) closed with no "
                      f"fill — rejected/expired, band < {BANDS['reject_rate']:.0%}")
    return {"date": date, "run_at": dt.datetime.now().isoformat(timespec="seconds"),
            "n_orders": n, "n_fills": len(fills), "n_rejects": len(rejects),
            "n_canceled": canceled, "n_partial": partials, "n_replaced": replaced,
            "reject_rate": reject_rate,
            "slippage": {"stock": _stats("stock"), "etf": _stats("etf")},
            "position_gap_frac": round(gap / notional, 4),
            "foreign_positions": {"n": len(foreign), "dollars": foreign_dollars,
                                  "symbols": sorted(foreign),
                                  "positions": foreign_rows, "totals": foreign_totals,
                                  "flatten_remaining_total": flatten_remaining_total,
                                  "flatten_complete": flatten_complete},
            "fills": fills, "rejects": rejects, "books": book_rows, "alarms": alarms}


def trailing_means(rows: list[dict]) -> dict:
    """Trailing-mean slippage over the last >=TRAIL_MIN_FILLS fills per class across all
    reconcile rows, the pre-registered agreement statistic."""
    out = {}
    for cls in ("stock", "etf"):
        fs = [f for r in rows for f in r.get("fills", [])
              if f["class"] == cls and f.get("slippage_bps") is not None][-TRAIL_MIN_FILLS:]
        xs = [f["slippage_bps"] for f in fs]
        # same window, split into the overnight gap the fill inherited vs what execution cost.
        # Reported alongside; the banded statistic is still the slippage mean.
        def _mean(key):
            ys = [f[key] for f in fs if f.get(key) is not None]
            return round(sum(ys) / len(ys), 2) if len(ys) >= TRAIL_MIN_FILLS else None
        out[cls] = {"n": len(xs),
                    "mean_bps": round(sum(xs) / len(xs), 2) if len(xs) >= TRAIL_MIN_FILLS else None,
                    "drift_bps": _mean("drift_bps"), "exec_bps": _mean("exec_bps")}
    return out


def slippage_breach_nights(trail: dict, prior: dict | None = None) -> dict:
    """Consecutive nights the trailing-mean statistic has sat outside its band, per class.

    Mirrors the flat_nights counter. Resets to 0 the first night back in band, and stays 0 while
    there are fewer than TRAIL_MIN_FILLS fills (mean_bps is None => no statistic yet, not a breach).
    """
    prior = prior or {}
    out = {}
    for cls, (lo, hi) in (("stock", BANDS["stock_bps"]), ("etf", BANDS["etf_bps"])):
        m = (trail.get(cls) or {}).get("mean_bps")
        breached = m is not None and not (lo <= m <= hi)
        out[cls] = prior.get(cls, 0) + 1 if breached else 0
    return out


def slippage_alarms(breach: dict, trail: dict) -> list[str]:
    """Fire ONLY at the pre-registered trigger: SLIPPAGE_BREACH_NIGHTS consecutive nights out of
    band on the trailing statistic. A shorter streak is overnight noise and is logged, not alarmed."""
    out = []
    for cls, (lo, hi) in (("stock", BANDS["stock_bps"]), ("etf", BANDS["etf_bps"])):
        nights = breach.get(cls, 0)
        if nights < SLIPPAGE_BREACH_NIGHTS:
            continue
        m = (trail.get(cls) or {}).get("mean_bps")
        below = m is not None and m < lo
        # Pre-reg §Alternative result: a negative trailing mean means the reference-close convention
        # itself is biased, i.e. suspect the measurement before believing the free money.
        why = (" — negative beyond the band implicates the reference-close convention, so suspect a "
               "measurement bug before an execution win") if below else ""
        t = trail.get(cls) or {}
        if t.get("drift_bps") is not None and t.get("exec_bps") is not None:
            # which half moved: the overnight gap the fills inherited, or execution itself
            why = (f" — that mean splits into {t['drift_bps']:+.1f} bps of overnight drift "
                   f"(close to next open) and {t['exec_bps']:+.1f} bps of execution" + why)
        out.append(f"SLIPPAGE-{cls.upper()}: trailing mean {m:+.1f} bps outside the "
                   f"[{lo:g}, {hi:g}] bps band for {nights} consecutive nights — pre-registered "
                   f"decision trigger: flag to the Research Director. Do NOT tune specs or the "
                   f"frozen cost model from inside this experiment{why}")
    return out


# ---------- report ----------

def print_report(row: dict, trail: dict) -> None:
    print(f"\n== reconcile {row['date']} ==")
    fp = row.get("foreign_positions", {})
    complete = fp.get("flatten_complete", fp.get("n", 0) == 0)   # old rows: fall back to n==0
    if not complete:
        t = fp.get("totals", {})
        print(f"  FOREIGN positions (stat-arb/AMAT residue): {fp.get('n', 0)} sym "
              f"gross ${fp.get('dollars', 0):,.0f} "
              f"(long ${t.get('gross_long', 0):,.0f} / short ${t.get('gross_short', 0):,.0f} / "
              f"net ${t.get('net', 0):,.0f})  priced {t.get('priced_count', '?')}/{fp.get('n', 0)}"
              f"  flatten remaining {fp.get('flatten_remaining_total', 0):g}  <- NOT complete")
    else:
        print("  foreign positions: none, flatten remaining 0 (stat-arb flatten complete)")
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
            split = (f"  = drift {t['drift_bps']:+.1f} + exec {t['exec_bps']:+.1f}"
                     if t.get("drift_bps") is not None and t.get("exec_bps") is not None else "")
            print(f"  {cls:<5} slippage n={s['n']}  mean {s['mean_bps']:+.1f} bps  "
                  f"median {s['median_bps']:+.1f}  trailing {tm}  band {band}{split}")
    print(f"  position gap {row['position_gap_frac']:.2%} of notional")
    for name, b in sorted(row["books"].items()):
        flat = f"  FLAT x{b['flat_nights']}" if b["flat_nights"] else ""
        print(f"    {name:<22} model_nav {b['model_nav']}  drag {b['drag_bps']:+.2f} bps{flat}")
    for a in row["alarms"]:
        print(f"  !! {a}")


# ---------- dedicated momentum_concentrated reconcile (exact; sole book in its account) ----------

def reconcile_mc_date(date: str, mc_row: dict, positions: dict[str, float],
                      orders: list[dict], closes: dict[str, float], prior: dict | None,
                      opens: dict[str, dict[str, float]] | None = None,
                      live_gap: bool = True) -> dict:
    """One night's EXACT broker-vs-model reconcile for momentum_concentrated. No pro-rating, it is
    the only book in its account, so broker positions/fills attribute to it directly. Pure/offline:
    `positions` = {sym: qty} broker snapshot, `orders` = the h26mc order dicts for this date,
    `closes` = {sym: adj close}, `prior` = last MC reconcile row (for trailing drag / flat streak)."""
    targets = mc_row.get("target_dollars", {})
    notional = mc_row.get("notional") or 1.0
    legs, gap_dollars = [], 0.0
    for s in sorted(set(targets) | set(positions)):
        ref = closes.get(s)
        tgt_sh = round(targets.get(s, 0.0) / ref) if ref else None
        held_sh = positions.get(s, 0.0)
        gap_sh = (held_sh - tgt_sh) if tgt_sh is not None else None
        g_d = (gap_sh * ref) if (gap_sh is not None and ref) else 0.0
        gap_dollars += abs(g_d)
        legs.append({"sym": s, "target_shares": tgt_sh, "held_shares": held_sh,
                     "gap_shares": gap_sh, "gap_dollars": round(g_d, 2), "ref_close": ref})
    mine = [o for o in orders if str(o.get("client_order_id") or "").startswith("h26mc-")]
    filled = [o for o in mine if o["status"] == "filled"]
    partial = [o for o in mine if o["status"] == "partially_filled"]
    rejected = [o for o in mine if o["status"] in ("rejected", "canceled")]
    pending = [o for o in mine if o["status"] in ("new", "accepted", "pending_new", "held")]
    slips, drag, drifts, execs = [], 0.0, [], []
    for o in filled + partial:
        ref, fp, q = closes.get(o["ticker"]), o.get("fill_price"), o.get("filled_qty") or 0.0
        if ref and fp and q:
            d_bps, e_bps = _drift_exec_bps(o, ref, _fill_open(opens or {}, o))
            if d_bps is not None:
                drifts.append(d_bps)
                execs.append(e_bps)
            s_bps = (fp - ref) / ref * 1e4 * (1 if o["side"] == "buy" else -1)
            slips.append(round(s_bps, 2))
            # signed, per pre-reg §3 "cumulative slippage drag" and the shared path's book drag.
            # abs() here rectified the overnight-gap noise every fill carries (fills land at the
            # next open, the reference is the run-date close), so the rolling sum could only
            # ratchet up and MC-DRAG could never clear once the book traded at all.
            drag += s_bps / 1e4 * q * fp
    marked = sum(q * closes.get(s, 0.0) for s, q in positions.items() if closes.get(s))
    drag_bps = round(drag / notional * 1e4, 3)
    hist = ((prior or {}).get("drag_bps_trail", []) or [])[-20:] + [drag_bps]   # ~1 trading month
    drag_month = round(sum(hist), 2)
    flat_nights = ((prior or {}).get("flat_nights", 0) + 1) if not positions else 0
    alarms = []
    if abs(drag_month) > BANDS["book_drag_bps_month"]:      # pre-reg: "drifting" either way
        alarms.append(f"MC-DRAG: trailing ~1mo tracking drag {drag_month:+.1f} bps outside the "
                      f"±{BANDS['book_drag_bps_month']:.0f} bps band")
    if rejected:
        alarms.append(f"MC-REJECTS: {len(rejected)} rejected/canceled order(s)")
    if flat_nights >= 2 and targets:
        alarms.append(f"MC-SILENT-FLAT: model has targets but dedicated account flat {flat_nights} night(s)")
    # `positions` is a snapshot taken a minute after the 20:30 run submits, so it still reflects the
    # PREVIOUS run's book. Alarming on tonight's targets flagged every rebalance as a gap. Compare
    # against the settled expectation (last run's target shares), and allow the one share the two
    # sizing bases disagree on: the runner rounds off the live price, this rounds off the close.
    settled = {leg["sym"]: leg["target_shares"] for leg in ((prior or {}).get("legs") or [])}
    settled_gap = sum(abs(positions.get(s, 0.0) - (settled.get(s) or 0.0)) * (closes.get(s) or 0.0)
                      for s in set(settled) | set(positions)
                      if abs(positions.get(s, 0.0) - (settled.get(s) or 0.0)) > 1)
    # broker positions are a NOW snapshot, so the settled comparison only holds for the night
    # actually being run. A --since replay scores old dates against today's book: still reported,
    # never alarmed.
    if prior and settled_gap and live_gap:
        alarms.append(f"MC-POSITION-GAP: ${settled_gap:,.0f} broker-vs-settled-model share gap")
    return {"date": date, "book": MC_BOOK, "legs": legs,
            "orders": {"filled": len(filled), "partial": len(partial),
                       "rejected": len(rejected), "pending": len(pending)},
            "slippage_bps": {"n": len(slips),
                             "median": (sorted(slips)[len(slips) // 2] if slips else None),
                             "drift_median": (sorted(drifts)[len(drifts) // 2] if drifts else None),
                             "exec_median": (sorted(execs)[len(execs) // 2] if execs else None)},
            "marked_sleeve_value": round(marked, 2), "model_notional": round(notional, 2),
            "drag_bps": drag_bps, "drag_bps_trail": hist, "drag_month_bps": drag_month,
            "gap_dollars": round(gap_dollars, 2), "settled_gap_dollars": round(settled_gap, 2),
            "flat_nights": flat_nights, "alarms": alarms}


def print_mc_report(row: dict) -> None:
    o = row["orders"]
    print(f"\n[{row['date']}] {MC_BOOK} (dedicated account)")
    print(f"  orders: {o['filled']} filled / {o['partial']} partial / {o['rejected']} rejected "
          f"/ {o['pending']} pending")
    print(f"  marked sleeve ${row['marked_sleeve_value']:,.0f} vs model notional "
          f"${row['model_notional']:,.0f}  ·  drag {row['drag_bps']:.1f} bps "
          f"(trailing ~1mo {row['drag_month_bps']:.1f} bps)")
    if row["gap_dollars"]:
        print(f"  broker-vs-model gap: ${row['gap_dollars']:,.0f}")
    for a in row["alarms"]:
        print(f"  !! {a}")


def reconcile_mc(dates: list[str], ledger: dict, live_gap: bool = True) -> None:
    """Read-only dedicated-account reconcile for momentum_concentrated. Skips (with a note) if the
    ALPACA_MC_* keys are absent; monitoring must not crash the shared reconcile before cutover."""
    import os
    mc_key, mc_secret = os.environ.get(MC_CRED_NAMES[0]), os.environ.get(MC_CRED_NAMES[1])
    if not (mc_key and mc_secret):
        print(f"\n(momentum_concentrated dedicated reconcile skipped — {MC_CRED_NAMES[0]}/"
              f"{MC_CRED_NAMES[1]} not set; pre-cutover or keys not yet in .env)")
        return
    # Only reconcile dates that actually traded in the dedicated account; an "_account_mc" row is
    # written only by the post-cutover live path, so this never backfills pre-cutover broker
    # attribution even on a --since replay that crosses the cutover (reviewer caveat).
    mc_dates = [d for d in dates if MC_BOOK in ledger.get(d, {}) and "_account_mc" in ledger.get(d, {})]
    if not mc_dates:
        return
    from alpaca.trading.client import TradingClient
    tc = TradingClient(mc_key, mc_secret, paper=True)   # read-only: get_orders / get_all_positions
    positions = positions_from_client(tc)
    orders = orders_from_client(tc, since=mc_dates[0], statuses="all")
    by_date: dict[str, list[dict]] = defaultdict(list)
    for o in orders:
        if o["submitted"]:
            by_date[o["submitted"]].append(o)
    symbols = sorted({s for d in mc_dates for s in ledger[d][MC_BOOK].get("target_dollars", {})}
                     | set(positions))
    from core.data.prices import fetch_prices_yf
    mc_start = (dt.date.fromisoformat(mc_dates[0]) - dt.timedelta(days=7)).isoformat()
    px = fetch_prices_yf(symbols, start=mc_start, end=None) if symbols else None
    op = fetch_prices_yf(symbols, start=mc_start, end=None, field="Open") if symbols else None
    prior_rows = ([json.loads(x) for x in RECONCILE_MC.read_text().splitlines()]
                  if RECONCILE_MC.exists() else [])
    prior_rows = drop_reprocessed_dates(prior_rows, mc_dates)
    prior = prior_rows[-1] if prior_rows else None
    for d in mc_dates:
        closes = {}
        if px is not None:
            avail = px.loc[px.index <= d]
            if len(avail):
                closes = {s: float(v) for s, v in avail.iloc[-1].items() if v == v}
        row = reconcile_mc_date(d, ledger[d][MC_BOOK], positions, by_date.get(d, []), closes, prior,
                                opens=opens_by_session(op),
                                live_gap=live_gap and d == mc_dates[-1])
        prior = row
        prior_rows.append(row)
        print_mc_report(row)
    RECONCILE_MC.write_text("\n".join(json.dumps(r) for r in prior_rows) + "\n")
    print(f"wrote {len(mc_dates)} row(s) -> {RECONCILE_MC}")


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
    # ponytail: positions are a NOW snapshot (broker keeps no history); gap/flat metrics are
    # exact for the nightly run, indicative only when replaying old dates via --since
    positions = positions_from_client(tc)
    equity = account_equity(tc)                                    # read-only get_account
    # all orders (open+closed) grouped by symbol, observed ONLY to track pending/partial flatten
    # orders on foreign positions; never submitted or modified
    symbol_orders: dict[str, list[dict]] = defaultdict(list)
    for o in orders_from_client(tc, since=dates[0], statuses="all"):
        symbol_orders[o["ticker"]].append(o)

    # reference closes: adjusted closes for every symbol any run-date touched (same source
    # the panel builder uses). Network; tests feed reconcile_date a dict directly.
    symbols = sorted({s for d in dates for b in ledger[d].values()
                      for s in b.get("target_dollars", {})} | set(positions))
    from core.data.prices import fetch_prices_yf
    start = (dt.date.fromisoformat(dates[0]) - dt.timedelta(days=7)).isoformat()
    px = fetch_prices_yf(symbols, start=start, end=None)
    # next-session opens: the price the fills actually landed at, for the drift/exec split only
    op = fetch_prices_yf(symbols, start=start, end=None, field="Open")
    session_opens = opens_by_session(op)

    buckets = bucket_orders(orders, dates)
    prior_rows = ([json.loads(x) for x in RECONCILE.read_text().splitlines()]
                  if RECONCILE.exists() else [])
    # same-date reruns replace the day's row instead of appending a dup (idempotent per
    # date, matching _write_ledger in hunt_paper_run.py).
    prior_rows = drop_reprocessed_dates(prior_rows, dates)
    prior_flat = {n: b.get("flat_nights", 0)
                  for n, b in (prior_rows[-1]["books"].items() if prior_rows else [])}
    # carried across runs the same way flat_nights is: read the last row, re-stamp on each new one
    prior_breach = prior_rows[-1].get("slippage_breach_nights", {}) if prior_rows else {}
    for d in dates:
        closes = {}
        avail = px.loc[px.index <= d]
        if len(avail):
            closes = {s: float(v) for s, v in avail.iloc[-1].items() if v == v}
        # momentum_concentrated executes in its own account (cutover 2026-07-15); exclude it and its
        # _account_mc row from the shared reconcile so its absent shares aren't flagged silent-flat.
        shared_books = {k: v for k, v in ledger[d].items() if k not in (MC_BOOK, "_account_mc")}
        row = reconcile_date(d, shared_books, buckets.get(d, []), positions, closes, prior_flat,
                             symbol_orders=symbol_orders, equity=equity,
                             opens=session_opens)
        prior_flat = {n: b["flat_nights"] for n, b in row["books"].items()}
        prior_rows.append(row)
        trail = trailing_means(prior_rows)          # needs THIS row, so it runs after the append
        prior_breach = slippage_breach_nights(trail, prior_breach)
        row["slippage_breach_nights"] = prior_breach
        row["alarms"] += slippage_alarms(prior_breach, trail)
        print_report(row, trail)
    RECONCILE.write_text("\n".join(json.dumps(r) for r in prior_rows) + "\n")
    print(f"\nwrote {len(dates)} row(s) -> {RECONCILE}")

    # dedicated momentum_concentrated account (exact; own file). A replay's position snapshot is
    # today's, so its broker-vs-model gap is indicative only: computed, not alarmed.
    reconcile_mc(dates, ledger, live_gap=args.since is None)


if __name__ == "__main__":
    main()
