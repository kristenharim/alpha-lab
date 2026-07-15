"""Nightly paper-book runner for the promoted hunt2026 books.

Seven books (fixed registry below), each a frozen hunt2026 spec. Every night: build a fresh
panel (panel_2005.parquet history + latest yfinance ETF bars), take each spec's target_weights
LAST row as tonight's target book, size it to an equal share (equity/7) of account equity, log a
ledger row (targets, fills, nav, both benchmark navs) per book, and — only with --live — submit.

Execution routing (cutover 2026-07-15, memos/mc-account-isolation-cutover-2026-07-15.md): the six
ETF books aggregate into the SHARED Alpaca paper account (ALPACA_*, tag h26); momentum_concentrated
executes ALONE in a DEDICATED paper account (ALPACA_MC_*, tag h26mc) so its single-stock fills,
marks, and survivorship are broker-attributable. Sizing is unchanged — divisor stays 7.

DEFAULT IS --dry-run: compute + print orders, write a ledger row marked "dry", submit NOTHING.
--live submits to Alpaca paper only (never real money). Do NOT run --live unattended before review.

Usage: .venv/bin/python scripts/hunt_paper_run.py --dry-run [--equity 100000]
       .venv/bin/python scripts/hunt_paper_run.py --live
"""
import argparse
import json
import sys
from pathlib import Path

import pandas as pd

HUNT = Path(__file__).resolve().parents[1] / "research" / "hunt2026"
sys.path.insert(0, str(HUNT))
import harness  # noqa: E402

META = json.loads((HUNT / "sandbox_meta.json").read_text())
SPECS = HUNT / "specs"
PANEL = HUNT / "panel_2005.parquet"
LEDGER_DIR = Path(__file__).resolve().parents[1] / "ledgers" / "hunt2026"
NAV_WINDOW = 252  # trailing days for the nav / benchmark-nav index (base 1.0)

# Fixed registry: book -> naive benchmark. "qqq" = bench_qqq_buyhold; "6040" = 60/40 SPY/BIL;
# "spy" = SPY buy-and-hold.
BOOKS = {
    "vol_managed_qqq": "qqq",   # core
    "vol_core_svxy": "qqq",
    "trend_vol_qqq": "qqq",
    "defensive_ensemble": "6040",
    "dual_momentum_gold": "spy",       # watch-tier (gold-menu hindsight; forward test decides)
    "momentum_concentrated": "spy",    # watch-tier (rank IC ~ 0, F-015/16; construction on trial)
    "dual_momentum_gem": "spy",        # watch-tier (whipsaw-fragile per 5y; forward test decides)
}
# Execution routing (cutover 2026-07-15, memos/mc-account-isolation-cutover-2026-07-15.md):
# momentum_concentrated executes in its own dedicated Alpaca paper account so its single-stock
# fills/marks/survivorship are broker-attributable; the six ETF books stay in the shared account.
# SIZING IS UNCHANGED: notional per book = shared_equity / N_BOOKS_TOTAL (still 7, never len(SHARED)).
MC_BOOK = "momentum_concentrated"
MC_CRED_NAMES = ("ALPACA_MC_API_KEY_ID", "ALPACA_MC_API_SECRET_KEY")
N_BOOKS_TOTAL = len(BOOKS)                          # 7 — the sizing divisor, frozen across the split
SHARED_BOOKS = [b for b in BOOKS if b != MC_BOOK]   # the six ETF books, aggregated into the shared acct


def build_live_panel(lookback_days: int = 20) -> pd.DataFrame:
    """panel_2005 history extended with the latest yfinance ETF/^VIX bars, ETF closes ffilled.

    Only the ETF + signal columns are refreshed (every hunt2026 book here is ETF-only). ffill heals
    stray holiday-calendar NaNs in the union index that would otherwise poison rolling windows.
    NETWORK — script-only; tests pass a fixture panel to compute_book directly.
    """
    from core.data.prices import fetch_prices_yf

    panel = pd.read_parquet(PANEL)
    tickers = [t for t in META["etfs"] + META["signal_only"] if t in panel["close"].columns]
    # stock books (momentum_concentrated) need fresh member-stock closes too
    member_last = panel["member"].iloc[-1]
    tickers += [t for t in member_last.index[member_last > 0]
                if t not in tickers and t in panel["close"].columns]
    start = (panel.index[-1] - pd.Timedelta(f"{lookback_days} days")).strftime("%Y-%m-%d")
    fresh = fetch_prices_yf(tickers, start=start, end=None)  # adjusted closes
    # ponytail: adjusted-close seam between panel and fresh may jog a few bps; fine for a signal
    idx = panel.index.union(fresh.index)
    close = panel["close"].reindex(idx)
    for t in fresh.columns:
        if t in close.columns:
            close[t] = fresh[t].reindex(idx).combine_first(close[t])
    out = {f: panel[f].reindex(idx) for f in ("open", "close", "volume", "member")}
    out["close"] = close
    out["member"] = out["member"].ffill()  # membership carries onto new dates
    p = pd.concat(out, axis=1)
    p.columns.names = ["field", "ticker"]
    return _heal_etfs(p)


def _heal_etfs(panel: pd.DataFrame) -> pd.DataFrame:
    """ffill ETF/signal closes (holiday-gap NaNs poison rolling windows). Idempotent; also cleans
    a raw fixture/cached panel before feeding specs."""
    tickers = [t for t in META["etfs"] + META["signal_only"] if t in panel["close"].columns]
    close = panel["close"].copy()
    close[tickers] = close[tickers].ffill()
    panel = panel.copy()
    panel["close"] = close
    return panel


def _nav(spec_mod, panel, start) -> float:
    return 1.0 + harness.run(spec_mod, panel, start=start)["total_net"]


def _spec_from_weights(W: pd.DataFrame):
    """Wrap a fixed weight frame as a harness spec: SPY held at the book's own gross exposure
    each day (the exposure-matched SPY benchmark)."""
    exposure = W.abs().sum(axis=1)

    class _S:
        @staticmethod
        def target_weights(p):
            c = p["close"]
            df = pd.DataFrame(0.0, index=c.index, columns=["SPY"])
            df["SPY"] = exposure.reindex(c.index).fillna(0.0)
            return df

    return _S


def _naive_spec(kind: str):
    if kind == "qqq":
        return harness.load_spec(SPECS / "bench_qqq_buyhold")
    if kind == "spy":
        class _Sspy:  # SPY buy-and-hold
            @staticmethod
            def target_weights(p):
                c = p["close"]
                df = pd.DataFrame(0.0, index=c.index, columns=["SPY"])
                df.loc[c["SPY"].notna(), "SPY"] = 1.0
                return df
        return _Sspy

    class _S6040:  # 60/40 SPY/BIL buy-and-hold
        @staticmethod
        def target_weights(p):
            c = p["close"]
            df = pd.DataFrame(0.0, index=c.index, columns=["SPY", "BIL"])
            df.loc[c["SPY"].notna(), "SPY"] = 0.6
            df.loc[c["BIL"].notna(), "BIL"] = 0.4
            return df

    return _S6040


def compute_book(panel: pd.DataFrame, name: str, notional: float) -> dict:
    """Tonight's book row for `name`, offline on `panel`. No network, no broker — the testable core."""
    panel = _heal_etfs(panel)
    spec = harness.load_spec(SPECS / name)
    W = spec.target_weights(panel).astype(float).fillna(0.0)
    last = W.iloc[-1]
    targets = {t: float(w) for t, w in last.items() if abs(w) > 1e-9}
    nav_start = panel.index[-min(NAV_WINDOW, len(panel) - 1)]
    res = harness.run(spec, panel, start=nav_start)
    return {
        "date": str(panel.index[-1].date()),
        "book": name,
        "targets": targets,
        "target_dollars": {t: round(w * notional, 2) for t, w in targets.items()},
        "gross": round(float(last.abs().sum()), 4),
        "notional": round(notional, 2),
        "nav": round(1.0 + res["total_net"], 6),
        # measurement-only: today's true net daily return. The `nav` above is a rolling
        # 252d-rebased index, so nav.pct_change() is NOT the daily return — the alpha-forward
        # layer (scripts/hunt_alpha_review.py) must read ret_1d.
        "ret_1d": round(float(res["net_daily"].iloc[-1]), 8),
        "bench_spy_nav": round(_nav(_spec_from_weights(W), panel, nav_start), 6),
        "bench_naive_nav": round(_nav(_naive_spec(BOOKS[name]), panel, nav_start), 6),
    }


def _write_ledger(row: dict) -> Path:
    LEDGER_DIR.mkdir(parents=True, exist_ok=True)
    path = LEDGER_DIR / f"{row['book']}.jsonl"
    # ponytail: same-date re-runs replace the day's row instead of appending a dup
    # (idempotent per book+date+mode; a --dry-run after the nightly --live must not
    # erase the live row). Full rewrite is fine — ledgers are a few hundred rows.
    kept = []
    if path.exists():
        kept = [ln for ln in path.read_text().splitlines()
                if ln.strip() and not (
                    json.loads(ln).get("date") == row["date"]
                    and json.loads(ln).get("mode") == row.get("mode"))]
    kept.append(json.dumps(row))
    path.write_text("\n".join(kept) + "\n")
    return path


def _print_row(row: dict) -> None:
    print(f"\n[{row['mode']}] {row['book']}  {row['date']}  "
          f"gross {row['gross']:.2f}  notional ${row['notional']:,.0f}")
    print(f"  nav {row['nav']:.4f}  spy(exposure-matched) {row['bench_spy_nav']:.4f}  "
          f"naive {row['bench_naive_nav']:.4f}")
    for t, d in sorted(row["target_dollars"].items()):
        print(f"    {t:<6} w={row['targets'][t]:+.3f}  ${d:>14,.2f}")


def route_targets(rows_by_book: dict[str, dict]) -> tuple[dict[str, float], dict[str, float]]:
    """Split computed book rows into (shared_agg, mc_targets) dollar targets, one per account.

    Six ETF books aggregate into shared_agg; momentum_concentrated alone into mc_targets. Enforces
    the routing invariant that NO symbol may land in both account target sets (fail closed). Pure —
    no broker, no network, no creds — so it is unit-tested offline and reused by dry-run and live."""
    shared_agg: dict[str, float] = {}
    mc_targets: dict[str, float] = {}
    for name, row in rows_by_book.items():
        dest = mc_targets if name == MC_BOOK else shared_agg
        for t, d in row["target_dollars"].items():
            dest[t] = dest.get(t, 0.0) + d
    overlap = set(shared_agg) & set(mc_targets)
    if overlap:
        raise RuntimeError(f"routing leak: symbol(s) {sorted(overlap)} would route to BOTH the shared "
                           f"and the momentum_concentrated account in one run — refusing to submit")
    return shared_agg, mc_targets


def submit_leg(who: str, broker, targets: dict[str, float], tag: str):
    """Submit ONE account. cancel_all first (idempotent retry). Per-order rejects are caught inside
    submit_targets; this guards infra/network errors so one account's failure neither aborts the
    other leg nor loses its ledger row (the two brokers cannot be atomic). Returns (fills, submit_ok)."""
    try:
        broker.cancel_all_orders()
        broker.submit_targets(targets, tag=tag)
        fills = [f for f in broker.fills()
                 if str(f.get("client_order_id") or "").startswith(tag + "-")]
        errs = broker.order_errors()
        if errs:
            print(f"  {who}: {len(errs)} order(s) rejected (e.g. {errs[0]['ticker']}: "
                  f"{errs[0]['error'][:70]})")
        return fills, True
    except Exception as e:   # noqa: BLE001 — fail loud + keep records; next run redoes deltas
        print(f"  !! {who} SUBMIT FAILED: {str(e)[:120]} — this account was NOT traded tonight; "
              f"the next run recomputes deltas from live broker state")
        return [], False


def _print_account_targets(label: str, targets: dict[str, float], equity: float) -> None:
    gross = sum(abs(d) for d in targets.values())
    print(f"\n  == {label} ==  {len(targets)} name(s)  gross ${gross:,.0f} "
          f"({gross / equity * 100:.1f}% of ${equity:,.0f})")
    for t, d in sorted(targets.items()):
        print(f"    {t:<6} ${d:>14,.2f}")


def dry_run(equity: float) -> None:
    panel = build_live_panel()
    notional = equity / N_BOOKS_TOTAL     # UNCHANGED sizing: equity / 7, never len(SHARED_BOOKS)
    rows_by_book = {}
    for name in BOOKS:
        row = compute_book(panel, name, notional)
        row["mode"], row["fills"] = "dry", []
        rows_by_book[name] = row
        _print_row(row)
        _write_ledger(row)
    shared_agg, mc_targets = route_targets(rows_by_book)
    print("\n--- proposed account target sets (dry-run: nothing submitted) ---")
    _print_account_targets(f"SHARED account · {len(SHARED_BOOKS)} ETF books · tag h26", shared_agg, equity)
    _print_account_targets(f"DEDICATED account · {MC_BOOK} · tag h26mc", mc_targets, equity)
    print(f"\nledgers -> {LEDGER_DIR}/  (dry-run: nothing submitted)")


def live_run() -> None:
    import os

    from core.env import load_dotenv
    from core.broker.alpaca import alpaca_paper_broker, snapshot_price_fn

    load_dotenv()
    key, secret = os.environ.get("ALPACA_API_KEY_ID"), os.environ.get("ALPACA_API_SECRET_KEY")
    mc_key, mc_secret = os.environ.get(MC_CRED_NAMES[0]), os.environ.get(MC_CRED_NAMES[1])
    if not (key and secret):
        sys.exit("--live needs ALPACA_API_KEY_ID / ALPACA_API_SECRET_KEY (paper keys) in env or .env")
    if not (mc_key and mc_secret):   # fail closed: no dedicated-account partial submission
        sys.exit(f"--live needs {MC_CRED_NAMES[0]} / {MC_CRED_NAMES[1]} for the dedicated "
                 f"{MC_BOOK} paper account — see memos/mc-account-isolation-cutover-2026-07-15.md")
    if key == mc_key:                # fail closed: both routes must be two distinct paper accounts
        sys.exit("refusing to trade: the shared and momentum_concentrated accounts share a key id "
                 "(they must be two separate Alpaca paper accounts)")
    from alpaca.data.historical import StockHistoricalDataClient
    from alpaca.trading.client import TradingClient

    panel = build_live_panel()
    # every tradable symbol across the books (^VIX is signal-only, never held) PLUS every currently-held
    # name in BOTH accounts: reconcile must be able to price stale/foreign positions to flatten them.
    book_syms = {t for name in BOOKS for t in compute_book(panel, name, 1.0)["targets"]
                 if t not in META["signal_only"]}
    held_shared = [p.symbol for p in TradingClient(key, secret, paper=True).get_all_positions()]
    held_mc = [p.symbol for p in TradingClient(mc_key, mc_secret, paper=True).get_all_positions()]
    symbols = sorted(book_syms | set(held_shared) | set(held_mc))
    dc = StockHistoricalDataClient(key, secret)
    price_fn = snapshot_price_fn(dc, symbols)
    shared_broker = alpaca_paper_broker(price_fn)                        # ALPACA_* — six ETF books
    mc_broker = alpaca_paper_broker(price_fn, cred_names=MC_CRED_NAMES)  # ALPACA_MC_* — momentum only

    acct = shared_broker.account()
    equity = float(getattr(acct, "equity", None) or acct.cash)
    notional = equity / N_BOOKS_TOTAL     # UNCHANGED sizing: shared_equity / 7 (never len(SHARED_BOOKS))
    print(f"Alpaca paper equity ${equity:,.0f} -> ${notional:,.0f}/book across {N_BOOKS_TOTAL} books "
          f"({len(SHARED_BOOKS)} in shared acct, {MC_BOOK} in dedicated acct)")

    # compute every book at the frozen notional, then route by account (pure invariant-checked split)
    rows, rows_by_book = [], {}
    for name in BOOKS:
        row = compute_book(panel, name, notional)
        row["mode"], row["fills"] = "live", []
        rows.append(row); rows_by_book[name] = row
    shared_agg, mc_targets = route_targets(rows_by_book)   # raises if any symbol routes to both accounts

    # fail closed: the dedicated account must be able to fund momentum_concentrated's gross
    mc_acct = mc_broker.account()
    mc_bp = float(getattr(mc_acct, "buying_power", None) or getattr(mc_acct, "equity", None)
                  or getattr(mc_acct, "cash", 0.0))
    mc_gross = sum(abs(d) for d in mc_targets.values())
    if mc_gross > mc_bp:
        sys.exit(f"refusing to trade: {MC_BOOK} needs ${mc_gross:,.0f} gross but the dedicated "
                 f"account buying power is ${mc_bp:,.0f}")

    # Write the per-book MODEL rows FIRST. They are model-marked (independent of fills), so a submit
    # failure on EITHER account must never lose the night's book records — the two brokers can't be
    # made atomic, so instead we guarantee the record and submit each leg independently (reviewer fix).
    for row in rows:
        _print_row(row)
        _write_ledger(row)
    date = rows[0]["date"]
    shared_fills, shared_ok = submit_leg("shared (6 ETF books)", shared_broker, shared_agg, "h26")
    mc_fills, mc_ok = submit_leg(f"dedicated {MC_BOOK}", mc_broker, mc_targets, "h26mc")

    _write_ledger({"date": date, "book": "_account", "mode": "live", "submit_ok": shared_ok,
                   "targets": {}, "target_dollars": {t: round(d, 2) for t, d in sorted(shared_agg.items())},
                   "gross": round(sum(abs(d) for d in shared_agg.values()) / equity, 4),
                   "notional": round(equity, 2), "nav": None, "bench_spy_nav": None,
                   "bench_naive_nav": None, "fills": shared_fills})
    # NEW at cutover: momentum_concentrated's broker-marked execution-reality row (dedicated account).
    _write_ledger({"date": date, "book": "_account_mc", "mode": "live", "submit_ok": mc_ok,
                   "targets": {}, "target_dollars": {t: round(d, 2) for t, d in sorted(mc_targets.items())},
                   "gross": round(mc_gross / equity, 4), "notional": round(equity, 2),
                   "mc_buying_power": round(mc_bp, 2), "nav": None, "bench_spy_nav": None,
                   "bench_naive_nav": None, "fills": mc_fills})
    if not (shared_ok and mc_ok):
        print("  !! PARTIAL NIGHT: one account did not trade (see alarm above); its ledger row is "
              "written with submit_ok=false — the next run reconciles and completes it")
    print(f"\nledgers -> {LEDGER_DIR}/  (live: shared ETF aggregate + dedicated {MC_BOOK} submission)")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true", help="compute + print, ledger marked dry, submit nothing")
    ap.add_argument("--live", action="store_true", help="submit tonight's books to Alpaca PAPER (needs keys)")
    ap.add_argument("--equity", type=float, default=100_000.0, help="dry-run: notional account equity to split")
    args = ap.parse_args()
    if args.live:
        live_run()
    else:  # default: dry-run (never submits)
        dry_run(args.equity)


if __name__ == "__main__":
    main()
