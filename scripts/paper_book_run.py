"""Nightly driver for the Stage-5 paper book (HYP-005).

`--dry-run` replays the last N trading days of a cached panel through the SAME
plumbing the live loop uses — reconcile → signal → submit(FakeBroker) → mark NAV →
ledgers → report — with no network, no keys, no Alpaca. It's a mini-backtest run
through the paper machinery: it exercises every unit and prints the bracket monitor
so you can see the shape of what the live book will produce.

Live (Alpaca paper) is NOT wired yet — AlpacaBroker + the parity gate come before
the first real run. Invoking without --dry-run says so and exits.

Usage: .venv/bin/python scripts/paper_book_run.py --dry-run [--days 60] [--window 60]
"""
import argparse
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


def _load_panel(days: int, window: int) -> pd.DataFrame:
    """Real cached survivor panel if present; else a deterministic synthetic one so
    the dry-run works on any machine. Tail to just what the replay needs."""
    need = days + window + 5
    if PANEL_CACHE.exists():
        px = pd.read_parquet(PANEL_CACHE).dropna(how="all")
        return px.tail(need).dropna(axis=1, how="any")
    rng = np.random.default_rng(0)
    dates = pd.bdate_range("2024-01-01", periods=need)
    tickers = [f"SYN{i:02d}" for i in range(40)]
    steps = rng.normal(0, 0.02, size=(need, len(tickers)))
    px = pd.DataFrame(100 * np.exp(np.cumsum(steps, axis=0)), index=dates, columns=tickers)
    return px


def _market_factors(prices: pd.DataFrame) -> pd.DataFrame:
    """Dry-run factor = the cross-sectional mean return (a crude market proxy),
    broadcast to every column. NOT the sector-ETF factor the backtest uses, so this
    is illustrative, not bit-parity — the parity harness (pre-go-live) is where the
    real factors and bit-for-bit check live."""
    mkt = daily_returns(prices).mean(axis=1)
    return pd.DataFrame({t: mkt for t in prices.columns}).reindex(daily_returns(prices).index)


def dry_run(days: int, window: int, out_root: Path) -> dict:
    prices = _load_panel(days, window)
    factors = _market_factors(prices)
    rets = daily_returns(prices)
    replay_dates = rets.index[-days:]

    ledger = Ledger(out_root)
    reconciler = Reconciler()
    broker = FakeBroker(prices={})
    notional = 1_000_000.0
    prev_book: dict[str, dict] = {}     # ticker -> {weight, bucket}

    for d in replay_dates:
        panel = prices.loc[:d]
        today_px = prices.loc[d]
        broker.prices.update(today_px.to_dict())

        # 1. reconcile held names (dry-run: FakeBroker reports all 'tradable' → still_open)
        for ticker in list(broker.positions()):
            reconciler.classify(ticker, broker.asset_status(ticker))

        # 2. mark yesterday's book into today, per bucket, and derive floored_net
        today_ret = rets.loc[d]
        by_bucket: dict[str, float] = {}
        for t, info in prev_book.items():
            by_bucket[info["bucket"]] = by_bucket.get(info["bucket"], 0.0) + \
                info["weight"] * float(today_ret.get(t, 0.0))
        net = sum(by_bucket.values())
        floored = net - sum(by_bucket.get(b, 0.0) for b in DEEP_BUCKETS)
        ledger.append("daily_nav", {
            "date": str(d.date()), "net": net, "floored_net": floored,
            "n_pos": len(prev_book), "net_by_bucket": by_bucket,
        })

        # 3. today's target book
        book = target_book(panel, factors, window=window)
        new_book = {r.ticker: {"weight": r.target_weight, "bucket": r.bucket}
                    for r in book.itertuples()}
        for r in book.itertuples():
            ledger.append("targets", {"date": str(d.date()), "ticker": r.ticker,
                                      "s_score": r.s_score, "bucket": r.bucket,
                                      "residual": r.residual, "target_weight": r.target_weight})

        # 4. position opens/closes vs yesterday (dry-run exits are band_flip, no dead names)
        for t in new_book.keys() - prev_book.keys():
            ledger.append("positions", {"open_date": str(d.date()), "ticker": t,
                                        "side": "long" if new_book[t]["weight"] > 0 else "short",
                                        "entry_bucket": new_book[t]["bucket"]})
        for t in prev_book.keys() - new_book.keys():
            ledger.append("positions", {"close_date": str(d.date()), "ticker": t,
                                        "close_reason": "band_flip", "realized_pnl": None})

        # 5. submit the full book to the broker; record fills
        broker.submit_targets({t: v["weight"] * notional for t, v in new_book.items()})
        for fill in broker.fills():
            ledger.append("fills", {"ts": str(d.date()), **fill,
                                    "borrow_bps": None, "locate_status": None})
        prev_book = new_book

    rep = bracket_report(ledger.read("daily_nav"), ledger.read("positions"))
    (out_root / "scorecard.md").write_text(to_markdown(rep))
    return rep


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true", help="replay on FakeBroker, no network")
    ap.add_argument("--days", type=int, default=60, help="trading days to replay")
    ap.add_argument("--window", type=int, default=60, help="residual/s-score lookback")
    args = ap.parse_args()

    if not args.dry_run:
        sys.exit("live Alpaca path not wired yet (AlpacaBroker + parity gate are the "
                 "pre-go-live TODO). Run with --dry-run to exercise the plumbing.")

    out_root = Path("artifacts/statarb/paper")
    rep = dry_run(args.days, args.window, out_root)
    print(to_markdown(rep))
    print(f"ledgers + scorecard → {out_root}/")


if __name__ == "__main__":
    main()
