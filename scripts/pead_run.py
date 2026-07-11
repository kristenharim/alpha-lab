"""PEAD Stage-1/2 run on free data. Documented limitations: yfinance history ~2y,
static large-cap universe (survivorship bias). WRDS/IBES swap-in planned.

Usage: .venv/bin/python scripts/pead_run.py
"""
import sys
from pathlib import Path

import pandas as pd

from core.data.prices import daily_returns, fetch_prices_yf
from core.data.registry import register
from tracks.pead.event_study import car_matrix, drift_spread
from tracks.pead.events import fetch_earnings_yf, surprise_score
from tracks.pead.universe import UNIVERSE


def main():
    out = Path("artifacts/pead")
    out.mkdir(parents=True, exist_ok=True)

    events = surprise_score(fetch_earnings_yf(UNIVERSE))
    events = events[events["date"] >= "2024-01-01"]
    # need a full +60 trading-day window after the event
    events = events[events["date"] <= pd.Timestamp.today() - pd.Timedelta(days=95)]
    if events.empty:
        sys.exit("no events with a complete post-announcement window")

    px = fetch_prices_yf(UNIVERSE + ["SPY"], "2023-06-01", None)
    rets = daily_returns(px)
    market = rets.pop("SPY")

    cars = car_matrix(events, rets, market, window=(-1, 60))
    spread = drift_spread(cars, events, q=5)
    events.to_parquet(out / "events.parquet")
    cars.to_parquet(out / "cars.parquet")

    lines = [
        "# PEAD drift — top minus bottom SUE quintile (CAR)", "",
        f"- events: {len(events)} | window: -1..+60 | universe: {len(UNIVERSE)} large caps "
        "(survivorship-biased placeholder)",
        f"- CAR spread @ +5d:  {spread.get(5, float('nan')):.2%}",
        f"- CAR spread @ +20d: {spread.get(20, float('nan')):.2%}",
        f"- CAR spread @ +60d: {spread.get(60, float('nan')):.2%}",
    ]
    (out / "drift.md").write_text("\n".join(lines) + "\n")
    register(Path("data/manifest.jsonl"), name="pead_events", source="yfinance",
             filters={"universe": len(UNIVERSE)}, path=str(out / "events.parquet"), rows=len(events))
    print("\n".join(lines))


if __name__ == "__main__":
    main()
