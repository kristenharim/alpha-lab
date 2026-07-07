"""Asset-growth contrarian sort (Cooper-Gulen-Schill) on free data.

Annual total assets from SEC EDGAR -> YoY growth -> contrarian score (long low-growth,
short high-growth). Signal lagged 6 months for 10-K availability (no look-ahead), held
monthly through the shared quantile engine + scorecard.

Usage: .venv/bin/python scripts/asset_growth_run.py
Limitation: 60-name large-cap universe (survivorship-biased placeholder). WRDS/Compustat
would give a point-in-time universe and cleaner PIT assets.
"""
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from core.backtest.engine import backtest
from core.backtest.portfolio import quantile_weights
from core.data.prices import fetch_prices_yf
from core.data.registry import register
from core.eval.scorecard import scorecard, to_markdown
from tracks.asset_growth.edgar import fetch_annual_assets
from tracks.asset_growth.signal import asset_growth, growth_score
from tracks.pead.universe import UNIVERSE

LAG_MONTHS = 6  # 10-K availability lag before a fiscal-year-end asset figure is tradeable


def main():
    out = Path("artifacts/asset_growth")
    out.mkdir(parents=True, exist_ok=True)

    cache = Path("data/raw/edgar_assets.parquet")
    if cache.exists():
        assets = pd.read_parquet(cache)
    else:
        assets = fetch_annual_assets(UNIVERSE)
        cache.parent.mkdir(parents=True, exist_ok=True)
        assets.to_parquet(cache)

    score = growth_score(asset_growth(assets))  # date(fy-end) x ticker, contrarian

    px = fetch_prices_yf(list(score.columns), "2010-01-01", None)
    monthly_ret = px.resample("ME").last().pct_change().dropna(how="all")

    # lag each fiscal-year-end score to its availability date, then as-of forward-fill
    # onto the monthly grid (cap staleness ~13 months so a signal expires between reports)
    score_avail = score.copy()
    score_avail.index = score_avail.index + pd.DateOffset(months=LAG_MONTHS)
    score_avail = score_avail[~score_avail.index.duplicated(keep="last")].sort_index()
    monthly_score = score_avail.reindex(monthly_ret.index, method="ffill",
                                        tolerance=pd.Timedelta("400D"))

    weights = quantile_weights(monthly_score.dropna(how="all"))
    res = backtest(weights, monthly_ret, cost_bps=10).dropna()
    res = res[res["turnover"].ne(0).cumsum() > 0]  # drop pre-signal months

    bench = {"equal_weight_universe": monthly_ret.mean(axis=1)}
    card = scorecard(res["net"], bench, n_trials=1, periods_per_year=12)
    (out / "scorecard.md").write_text(to_markdown(card, "Asset-growth contrarian (Cooper-Gulen-Schill)"))
    res.to_parquet(out / "pnl.parquet")
    register(Path("data/manifest.jsonl"), name="asset_growth", source="edgar+yfinance",
             filters={"universe": len(UNIVERSE), "lag_months": LAG_MONTHS},
             path=str(out / "pnl.parquet"), rows=len(res))
    print(to_markdown(card, "Asset-growth contrarian (Cooper-Gulen-Schill)"))


if __name__ == "__main__":
    main()
