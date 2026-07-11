"""Score a news file with Claude, build daily L/S signal, run backtest + scorecard.

Usage: .venv/bin/python scripts/llm_sentiment_run.py --news data/raw/news.parquet [--masked]
News parquet schema: columns date, ticker, company, headline (source-agnostic).

Post-cutoff discipline (Decision A): refuses --start earlier than the scoring model's
training cutoff unless --masked.
"""
import argparse
import os
import sys
from pathlib import Path

import pandas as pd

from core.backtest.engine import backtest
from core.backtest.portfolio import quantile_weights
from core.data.prices import daily_returns, fetch_prices_yf
from core.data.registry import register
from core.eval.scorecard import scorecard, to_markdown
from tracks.llm_sentiment.scorer import score_headlines
from tracks.llm_sentiment.signal import daily_signal

MODEL_CUTOFF = "2026-01-31"  # claude training cutoff; unmasked eval must start after this


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--news", required=True)
    ap.add_argument("--start", default=MODEL_CUTOFF)
    ap.add_argument("--masked", action="store_true")
    ap.add_argument("--cost-bps", type=float, default=10.0)
    args = ap.parse_args()

    if not os.environ.get("ANTHROPIC_API_KEY"):
        sys.exit("ANTHROPIC_API_KEY not set — cannot score headlines.")
    if args.start < MODEL_CUTOFF and not args.masked:
        sys.exit(f"start {args.start} predates model cutoff {MODEL_CUTOFF}; "
                 "rerun with --masked (Decision A, see spec).")

    import anthropic
    news = pd.read_parquet(args.news)
    missing = {"date", "ticker", "company", "headline"} - set(news.columns)
    if missing:
        sys.exit(f"news file missing columns: {sorted(missing)}")
    news = news[news["date"].astype(str) >= args.start]
    if news.empty:
        sys.exit("no headlines in window")

    client = anthropic.Anthropic()
    scored = score_headlines(client, news.to_dict("records"), masked=args.masked)
    out = Path("artifacts/llm_sentiment")
    out.mkdir(parents=True, exist_ok=True)
    scored.to_parquet(out / "scored.parquet")

    sig = daily_signal(scored)
    px = fetch_prices_yf(sorted(sig.columns), str(sig.index.min().date()), None)
    rets = daily_returns(px)
    res = backtest(quantile_weights(sig.reindex(rets.index).ffill(limit=1)), rets, args.cost_bps)
    bench = {"equal_weight_long": rets.mean(axis=1)}
    card = scorecard(res["net"], bench, n_trials=3, periods_per_year=252)
    label = "masked" if args.masked else "unmasked"
    (out / "scorecard.md").write_text(to_markdown(card, f"LLM sentiment ({label})"))
    register(Path("data/manifest.jsonl"), name="llm_scored", source="anthropic+" + args.news,
             filters={"start": args.start, "masked": args.masked},
             path=str(out / "scored.parquet"), rows=len(scored))
    print(f"done: {len(scored)} headlines -> {out}")


if __name__ == "__main__":
    main()
