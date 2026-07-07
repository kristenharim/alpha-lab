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
from tracks.asset_growth.neutralize import neutralize_score
from tracks.asset_growth.signal import asset_growth, growth_score
from tracks.pead.universe import UNIVERSE

LAG_MONTHS = 6  # 10-K availability lag before a fiscal-year-end asset figure is tradeable


def load_composite():
    return fetch_sp_composite(cache=Path("data/raw/sp_composite.parquet"))


def resolve_universe(name: str) -> list[str]:
    if name == "wide":
        return list(load_composite()["ticker"])
    return UNIVERSE  # "mega" — the original 60-name placeholder


def to_monthly(panel: pd.DataFrame, grid: pd.DatetimeIndex) -> pd.DataFrame:
    """Lag a fiscal-year-end panel by 10-K availability, then as-of forward-fill each
    column independently onto the monthly grid. Per-column ffill (via union+ffill) is
    essential: reindex(method='ffill') would grab a single source row per month, which
    collapses to near-empty on a sparse multi-fiscal-year-end panel. limit≈24 rows caps
    staleness so a missing report year expires the signal."""
    p = panel.copy()
    p.index = p.index + pd.DateOffset(months=LAG_MONTHS)
    p = p[~p.index.duplicated(keep="last")].sort_index()
    union = p.index.union(grid)
    return p.reindex(union).ffill(limit=24).reindex(grid)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--universe", choices=["wide", "mega"], default="wide")
    ap.add_argument("--neutralize", dest="neutralize", action="store_true", default=True,
                    help="residualize the score vs log-size + sector each month (default on)")
    ap.add_argument("--no-neutralize", dest="neutralize", action="store_false")
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

    growth = asset_growth(assets)
    score = growth_score(growth)               # date(fy-end) x ticker, contrarian
    size_level = assets.reindex(score.index)   # total-assets level as the size proxy

    px_cache = Path(f"data/raw/monthly_px_{args.universe}.parquet")
    if px_cache.exists():
        px = pd.read_parquet(px_cache)
    else:
        px = fetch_prices_yf(list(score.columns), "2010-01-01", None, interval="1mo")
        px.to_parquet(px_cache)
    monthly_ret = px.resample("ME").last().pct_change(fill_method=None).dropna(how="all")
    # winsorize against corporate-action / bad-tick artifacts (e.g. a delisted shell's
    # near-zero price jumping to a post-reverse-split value → fake +30,000% month).
    # Real monthly equity moves rarely exceed +300%; anything beyond is a data error.
    monthly_ret = monthly_ret.clip(lower=-0.90, upper=3.0)

    # lag score + size to availability and place on the monthly grid
    monthly_score = to_monthly(score, monthly_ret.index)
    monthly_size = to_monthly(size_level, monthly_ret.index)

    # coverage: names with both an asset-growth score and price history
    covered = sorted(set(score.columns) & set(monthly_ret.columns))
    ms = monthly_score[covered]

    if args.neutralize:
        comp = load_composite()
        sectors = dict(zip(comp["ticker"], comp["sector"]))
        ms = neutralize_score(ms, monthly_size[covered], sectors)

    # only trade months with a healthy cross-section — thin early months make quintiles
    # of 1-2 undiversified names, producing junk (e.g. a single short blowing past -100%)
    MIN_NAMES = 50
    ms = ms[ms.notna().sum(axis=1) >= MIN_NAMES]
    median_names = int(ms.notna().sum(axis=1).median())

    weights = quantile_weights(ms.dropna(how="all"))
    res = backtest(weights, monthly_ret, cost_bps=10).dropna()
    res = res[res["turnover"].ne(0).cumsum() > 0]  # drop pre-signal months

    neut = "size/sector-neutral" if args.neutralize else "raw"
    title = (f"Asset-growth contrarian (Cooper-Gulen-Schill) — {args.universe} universe, "
             f"{neut}, {len(covered)} names w/ data, ~{median_names}/month")
    bench = {"equal_weight_universe": monthly_ret[covered].mean(axis=1)}
    card = scorecard(res["net"], bench, n_trials=1, periods_per_year=12)
    (out / "scorecard.md").write_text(to_markdown(card, title))
    res.to_parquet(out / "pnl.parquet")
    register(Path("data/manifest.jsonl"), name="asset_growth", source="edgar+yfinance",
             filters={"universe": args.universe, "neutralized": args.neutralize,
                      "names_with_data": len(covered), "lag_months": LAG_MONTHS},
             path=str(out / "pnl.parquet"), rows=len(res))
    print(to_markdown(card, title))
    print(f"\nUniverse: {args.universe} | neutralize={args.neutralize} | {len(tickers)} requested | "
          f"{len(covered)} with both assets+prices | ~{median_names} names/month in sort")


if __name__ == "__main__":
    main()
