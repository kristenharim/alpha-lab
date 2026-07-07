"""Asset-growth contrarian sort (Cooper-Gulen-Schill) on free data.

Annual total assets from SEC EDGAR -> YoY growth -> contrarian score (long low-growth,
short high-growth). Signal lagged 6 months for 10-K availability (no look-ahead), held
monthly through the shared quantile engine + scorecard.

Usage: .venv/bin/python scripts/asset_growth_run.py
Limitation: 60-name large-cap universe (survivorship-biased placeholder). WRDS/Compustat
would give a point-in-time universe and cleaner PIT assets.
"""
import argparse
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from core.backtest.engine import backtest
from core.backtest.portfolio import quantile_weights
from core.data.prices import fetch_prices_yf
from core.data.registry import register
from core.data.universe import fetch_sp_composite
from core.eval.scorecard import scorecard, to_markdown
from tracks.asset_growth.edgar import fetch_annual_assets
from tracks.asset_growth.signal import asset_growth, growth_score
from tracks.pead.universe import UNIVERSE

LAG_MONTHS = 6  # 10-K availability lag before a fiscal-year-end asset figure is tradeable


def resolve_universe(name: str) -> list[str]:
    if name == "wide":
        comp = fetch_sp_composite(cache=Path("data/raw/sp_composite.parquet"))
        return list(comp["ticker"])
    return UNIVERSE  # "mega" — the original 60-name placeholder


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--universe", choices=["wide", "mega"], default="wide")
    args = ap.parse_args()

    out = Path("artifacts/asset_growth")
    out.mkdir(parents=True, exist_ok=True)
    tickers = resolve_universe(args.universe)

    cache = Path(f"data/raw/edgar_assets_{args.universe}.parquet")
    if cache.exists():
        assets = pd.read_parquet(cache)
    else:
        assets = fetch_annual_assets(tickers)
        cache.parent.mkdir(parents=True, exist_ok=True)
        assets.to_parquet(cache)

    score = growth_score(asset_growth(assets))  # date(fy-end) x ticker, contrarian

    px_cache = Path(f"data/raw/monthly_px_{args.universe}.parquet")
    if px_cache.exists():
        px = pd.read_parquet(px_cache)
    else:
        px = fetch_prices_yf(list(score.columns), "2010-01-01", None, interval="1mo")
        px.to_parquet(px_cache)
    monthly_ret = px.resample("ME").last().pct_change().dropna(how="all")
    # winsorize against corporate-action / bad-tick artifacts (e.g. a delisted shell's
    # near-zero price jumping to a post-reverse-split value → fake +30,000% month).
    # Real monthly equity moves rarely exceed +300%; anything beyond is a data error.
    monthly_ret = monthly_ret.clip(lower=-0.90, upper=3.0)

    # lag each fiscal-year-end score to its availability date, then as-of forward-fill
    # onto the monthly grid (cap staleness ~13 months so a signal expires between reports)
    score_avail = score.copy()
    score_avail.index = score_avail.index + pd.DateOffset(months=LAG_MONTHS)
    score_avail = score_avail[~score_avail.index.duplicated(keep="last")].sort_index()
    monthly_score = score_avail.reindex(monthly_ret.index, method="ffill",
                                        tolerance=pd.Timedelta("400D"))

    # coverage: names with both an asset-growth score and price history
    covered = sorted(set(score.columns) & set(monthly_ret.columns))
    ms = monthly_score[covered]
    # only trade months with a healthy cross-section — thin early months make quintiles
    # of 1-2 undiversified names, producing junk (e.g. a single short blowing past -100%)
    MIN_NAMES = 50
    ms = ms[ms.notna().sum(axis=1) >= MIN_NAMES]
    median_names = int(ms.notna().sum(axis=1).median())

    weights = quantile_weights(ms.dropna(how="all"))
    res = backtest(weights, monthly_ret, cost_bps=10).dropna()
    res = res[res["turnover"].ne(0).cumsum() > 0]  # drop pre-signal months

    title = (f"Asset-growth contrarian (Cooper-Gulen-Schill) — {args.universe} universe, "
             f"{len(covered)} names w/ data, ~{median_names}/month")
    bench = {"equal_weight_universe": monthly_ret[covered].mean(axis=1)}
    card = scorecard(res["net"], bench, n_trials=1, periods_per_year=12)
    (out / "scorecard.md").write_text(to_markdown(card, title))
    res.to_parquet(out / "pnl.parquet")
    register(Path("data/manifest.jsonl"), name="asset_growth", source="edgar+yfinance",
             filters={"universe": args.universe, "names_with_data": len(covered),
                      "lag_months": LAG_MONTHS},
             path=str(out / "pnl.parquet"), rows=len(res))
    print(to_markdown(card, title))
    print(f"\nUniverse: {args.universe} | {len(tickers)} requested | "
          f"{len(covered)} with both assets+prices | ~{median_names} names/month in sort")


if __name__ == "__main__":
    main()
