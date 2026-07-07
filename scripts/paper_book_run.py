"""Nightly driver for the Stage-5 paper book (HYP-005).

`--dry-run` replays the last N trading days of a cached panel through the SAME plumbing the live loop
uses (reconcile -> signal -> submit(FakeBroker) -> mark NAV -> ledgers -> report), no network/keys. It's
a mini-backtest through the paper machinery.

`--live` runs ONE nightly step against Alpaca **paper**: fetch today's bars, run the parity gate, submit
the target book, log, report. The per-night step is shared with --dry-run (so it's exercised by the test
suite); the live DATA path (Alpaca fetch + keyed broker calls) is validated by the first keyed run —
that run IS the smoke test. Needs ALPACA_API_KEY_ID / ALPACA_API_SECRET_KEY in the env.

Usage: .venv/bin/python scripts/paper_book_run.py --dry-run [--days 60] [--window 60]
       .venv/bin/python scripts/paper_book_run.py --live [--window 60]
"""
import argparse
import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from core.broker.base import FakeBroker
from core.data.prices import daily_returns
from tracks.statarb.paper.ledger import Ledger
from tracks.statarb.paper.reconcile import Reconciler
from tracks.statarb.paper.report import bracket_report, to_markdown
from tracks.statarb.paper.signal import target_book

DEEP_BUCKETS = ("long_deep", "long_verydeep")
PANEL_CACHE = Path("data/raw/daily_px_statarb_wide.parquet")
NOTIONAL = 1_000_000.0


def _load_panel(days: int, window: int) -> pd.DataFrame:
    """Real cached survivor panel if present; else a deterministic synthetic one."""
    need = days + window + 5
    if PANEL_CACHE.exists():
        px = pd.read_parquet(PANEL_CACHE).dropna(how="all")
        return px.tail(need).dropna(axis=1, how="any")
    rng = np.random.default_rng(0)
    dates = pd.bdate_range("2024-01-01", periods=need)
    tickers = [f"SYN{i:02d}" for i in range(40)]
    steps = rng.normal(0, 0.02, size=(need, len(tickers)))
    return pd.DataFrame(100 * np.exp(np.cumsum(steps, axis=0)), index=dates, columns=tickers)


def _market_factors(prices: pd.DataFrame) -> pd.DataFrame:
    """Dry-run factor = cross-sectional mean return (crude market proxy). Not the sector-ETF factor,
    so dry-run is illustrative; the parity gate (live) uses the real factors."""
    mkt = daily_returns(prices).mean(axis=1)
    return pd.DataFrame({t: mkt for t in prices.columns}).reindex(daily_returns(prices).index)


def _nightly_step(d, prices, factors, rets, broker, ledger, reconciler, prev_book, window) -> dict:
    """One trading day through the paper machinery. Shared by --dry-run and --live so the live path
    reuses tested logic; returns today's book (to carry as tomorrow's prev_book)."""
    if hasattr(broker, "prices"):                       # FakeBroker needs the mark; AlpacaBroker doesn't
        broker.prices.update(prices.loc[d].to_dict())

    for ticker in list(broker.positions()):             # 1. reconcile held names
        reconciler.classify(ticker, broker.asset_status(ticker))

    today_ret = rets.loc[d]                              # 2. mark yesterday's book, per bucket + floored
    by_bucket: dict = {}
    for t, info in prev_book.items():
        by_bucket[info["bucket"]] = by_bucket.get(info["bucket"], 0.0) + \
            info["weight"] * float(today_ret.get(t, 0.0))
    net = sum(by_bucket.values())
    floored = net - sum(by_bucket.get(b, 0.0) for b in DEEP_BUCKETS)
    ledger.append("daily_nav", {"date": str(d.date()), "net": net, "floored_net": floored,
                                "n_pos": len(prev_book), "net_by_bucket": by_bucket})

    book = target_book(prices.loc[:d], factors.loc[:d], window=window)   # 3. today's target book
    new_book = {r.ticker: {"weight": r.target_weight, "bucket": r.bucket} for r in book.itertuples()}
    for r in book.itertuples():
        ledger.append("targets", {"date": str(d.date()), "ticker": r.ticker, "s_score": r.s_score,
                                  "bucket": r.bucket, "residual": r.residual,
                                  "target_weight": r.target_weight})

    for t in new_book.keys() - prev_book.keys():        # 4. opens / closes vs yesterday
        ledger.append("positions", {"open_date": str(d.date()), "ticker": t,
                                    "side": "long" if new_book[t]["weight"] > 0 else "short",
                                    "entry_bucket": new_book[t]["bucket"]})
    for t in prev_book.keys() - new_book.keys():
        ledger.append("positions", {"close_date": str(d.date()), "ticker": t,
                                    "close_reason": "band_flip", "realized_pnl": None})

    broker.submit_targets({t: v["weight"] * NOTIONAL for t, v in new_book.items()})   # 5. submit + fills
    for fill in broker.fills():
        ledger.append("fills", {"ts": str(d.date()), **fill, "borrow_bps": None, "locate_status": None})
    return new_book


def dry_run(days: int, window: int, out_root: Path) -> dict:
    prices = _load_panel(days, window)
    factors = _market_factors(prices)
    rets = daily_returns(prices)
    ledger, reconciler, broker = Ledger(out_root), Reconciler(), FakeBroker(prices={})
    prev_book: dict = {}
    for d in rets.index[-days:]:
        prev_book = _nightly_step(d, prices, factors, rets, broker, ledger, reconciler, prev_book, window)
    rep = bracket_report(ledger.read("daily_nav"), ledger.read("positions"))
    (out_root / "scorecard.md").write_text(to_markdown(rep))
    return rep


def _prev_book_from_ledger(ledger: Ledger) -> dict:
    """Reconstruct yesterday's book from the last date in targets.jsonl (live state across nights)."""
    rows = ledger.read("targets")
    if not rows:
        return {}
    last = max(r["date"] for r in rows)
    return {r["ticker"]: {"weight": r["target_weight"], "bucket": r["bucket"]}
            for r in rows if r["date"] == last}


def _fetch_alpaca_panel(window: int, lookback_days: int = 90):
    """Live daily bars for the current S&P 500 + sector ETFs from Alpaca; build sector-matched factors.
    UNTESTED until keys — the first --live run validates this path."""
    from alpaca.data.historical import StockHistoricalDataClient
    from alpaca.data.requests import StockBarsRequest
    from alpaca.data.timeframe import TimeFrame

    from core.data.universe import fetch_sp_composite
    from scripts.statarb_residual_run import SECTOR_ETF

    key, secret = os.environ["ALPACA_API_KEY_ID"], os.environ["ALPACA_API_SECRET_KEY"]
    dc = StockHistoricalDataClient(key, secret)
    comp = fetch_sp_composite(cache=Path("data/raw/sp_composite.parquet"))
    comp = comp[comp["index"] == "500"]
    sectors = dict(zip(comp["ticker"], comp["sector"]))
    etfs = sorted(set(SECTOR_ETF.values()) | {"SPY"})
    start = pd.Timestamp.today().normalize() - pd.tseries.offsets.BDay(window + lookback_days)
    bars = dc.get_stock_bars(StockBarsRequest(symbol_or_symbols=sorted(sectors) + etfs,
                                              timeframe=TimeFrame.Day, start=start))
    close = bars.df["close"].unstack("symbol")
    close.index = pd.to_datetime(close.index).tz_localize(None).normalize()
    prices = close[[c for c in sorted(sectors) if c in close.columns]]
    etf_ret = daily_returns(close[[c for c in etfs if c in close.columns]])
    rets = daily_returns(prices)
    factors = pd.DataFrame({t: etf_ret.get(SECTOR_ETF.get(sectors.get(t, ""), "SPY"),
                                           etf_ret["SPY"]).fillna(etf_ret["SPY"])
                            for t in prices.columns}).reindex(rets.index)
    return prices, factors, dc


def live_run(window: int, out_root: Path) -> dict:
    if not (os.environ.get("ALPACA_API_KEY_ID") and os.environ.get("ALPACA_API_SECRET_KEY")):
        sys.exit("--live needs ALPACA_API_KEY_ID and ALPACA_API_SECRET_KEY (paper keys) in the env")

    from core.broker.alpaca import alpaca_paper_broker, snapshot_price_fn
    from tracks.statarb.paper.parity import parity_mismatches

    prices, factors, dc = _fetch_alpaca_panel(window)
    rets = daily_returns(prices)

    bad = parity_mismatches(prices, factors, list(rets.index[-5:]), window=window)   # THE gate
    if bad:
        sys.exit(f"PARITY GATE FAILED on {[str(b.date()) for b in bad]} — refusing to trade live.")

    broker = alpaca_paper_broker(snapshot_price_fn(dc, list(prices.columns)))
    ledger, reconciler = Ledger(out_root), Reconciler()
    prev_book = _prev_book_from_ledger(ledger)
    _nightly_step(rets.index[-1], prices, factors, rets, broker, ledger, reconciler, prev_book, window)
    rep = bracket_report(ledger.read("daily_nav"), ledger.read("positions"))
    (out_root / "scorecard.md").write_text(to_markdown(rep))
    return rep


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true", help="replay on FakeBroker, no network")
    ap.add_argument("--live", action="store_true", help="one nightly step against Alpaca paper (needs keys)")
    ap.add_argument("--days", type=int, default=60, help="dry-run: trading days to replay")
    ap.add_argument("--window", type=int, default=60, help="residual/s-score lookback")
    args = ap.parse_args()

    out_root = Path("artifacts/statarb/paper")
    if args.live:
        rep = live_run(args.window, out_root)
    elif args.dry_run:
        rep = dry_run(args.days, args.window, out_root)
    else:
        sys.exit("pass --dry-run (offline replay) or --live (Alpaca paper, needs keys)")
    print(to_markdown(rep))
    print(f"ledgers + scorecard -> {out_root}/")


if __name__ == "__main__":
    main()
