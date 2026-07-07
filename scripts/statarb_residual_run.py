"""StatArb residual mean-reversion (Avellaneda & Lee 2010, ETF variant), wide universe.

For each stock: rolling single-factor regression on its SECTOR ETF (betas lagged, no look-ahead)
-> idiosyncratic residual -> s-score of the cumulative residual. Trade the mean-reversion: long
when s <= -1.25, short when s >= +1.25, flat inside +/-0.5. Dollar-neutral, equal-weight across
active names, net of costs -> shared scorecard.

`run_residual` is the single audited code path (CLI here + the ablation sweeper both call it). With
all layers off it reproduces the equal-weight formula bit-for-bit (parity gate); the weights path is
used only when a sector/name cap is active.

Usage: .venv/bin/python scripts/statarb_residual_run.py [--window 60 --entry 1.25 --exit 0.5]
"""
import argparse
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from core.data.prices import daily_returns, fetch_prices_yf
from core.data.registry import register
from core.data.universe import (fetch_sp_composite, fetch_sp500_pit_changes,
                                 membership_mask, ever_members)
from core.eval.scorecard import scorecard, to_markdown
from tracks.statarb import filters as F
from tracks.statarb.bands import band_positions
from tracks.statarb.pnl import equal_weight_net
from tracks.statarb.residual import rolling_residual
from tracks.statarb.trades import extract_trades

SECTOR_ETF = {
    "Information Technology": "XLK", "Financials": "XLF", "Health Care": "XLV",
    "Consumer Discretionary": "XLY", "Consumer Staples": "XLP", "Energy": "XLE",
    "Industrials": "XLI", "Materials": "XLB", "Utilities": "XLU",
    "Real Estate": "XLRE", "Communication Services": "XLC",
}


def run_residual(rets, factors, sectors, *, window=60, entry=1.25, exit_=0.5, skip=1,
                 long_floor=None, cost_bps=5.0, liquidity_adv=0.0, dollar_adv=None,
                 sector_cap_=0.0, name_cap=0.0, blackout=None, features=None, pit_mask=None):
    """Single audited path. All-layers-off (+ pit_mask=None) reproduces the current equal-weight
    P&L exactly (parity gate); the weights path activates only when a cap is set. Returns
    {net, trades, base_positions, final_positions}."""
    resid = rolling_residual(rets, factors, window=window)
    cum = resid.cumsum()
    s = (cum - cum.rolling(window).mean()) / cum.rolling(window).std()
    base_positions = s.apply(lambda col: band_positions(col, entry=entry, exit_=exit_,
                                                        long_floor=long_floor))
    if pit_mask is not None:
        base_positions = base_positions.where(pit_mask, 0)

    positions = base_positions
    removed_by = {}
    if liquidity_adv and dollar_adv is not None:
        positions, rem = F.liquidity_filter(positions, dollar_adv, liquidity_adv)
        removed_by["liquidity"] = rem
    if blackout is not None:
        positions, rem = F.earnings_blackout(positions, blackout)
        removed_by["earnings"] = rem

    if sector_cap_ > 0 or name_cap > 0:
        w = F.sector_cap(F.to_weights(positions), sectors, name_cap or 1.0, sector_cap_ or 1.0)
        held = w.shift(1 + skip)
        gross = (held * resid).sum(axis=1)
        turnover = w.diff().abs()
        cost = (turnover * cost_bps / 1e4 * 2).sum(axis=1)
        net = (gross - cost).fillna(0)
        net = net[net.ne(0).cumsum() > 0]          # drop warm-up (equal_weight_net trims internally)
    else:
        net = equal_weight_net(positions, resid, skip, cost_bps)

    if features is None:
        features = {"volatility": rets.rolling(window).std(),
                    "volume_ratio": pd.DataFrame(1.0, index=rets.index, columns=rets.columns)}
    trades = extract_trades(base_positions, positions, resid, s, features, sectors, removed_by,
                            lag=1 + skip)
    return {"net": net, "trades": trades, "resid": resid,
            "base_positions": base_positions, "final_positions": positions}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--window", type=int, default=60)
    ap.add_argument("--entry", type=float, default=1.25)
    ap.add_argument("--exit", type=float, default=0.5, dest="exit_")
    ap.add_argument("--cost-bps", type=float, default=5.0)
    ap.add_argument("--long-floor", type=float, default=None, dest="long_floor",
                    help="falling-knife stress test: forbid longs while s < -long_floor")
    ap.add_argument("--n-trials", type=int, default=20,
                    help="declared # of strategy variants tried, for the deflated-Sharpe haircut")
    ap.add_argument("--skip", type=int, default=1,
                    help="days between signal close and execution (0 reproduces the naive run)")
    ap.add_argument("--cap", choices=["all", "large", "small"], default="all",
                    help="large = S&P 500 only, small = S&P 600 only")
    ap.add_argument("--start", default="2018-01-01")
    ap.add_argument("--pit", action="store_true",
                    help="point-in-time S&P 500 membership (removes inclusion look-ahead). Sharpe is "
                         "an UPPER BOUND — delisting survivorship is unfixable on free data.")
    args = ap.parse_args()

    out = Path("artifacts/statarb")
    out.mkdir(parents=True, exist_ok=True)

    comp = fetch_sp_composite(cache=Path("data/raw/sp_composite.parquet"))
    pit_changes = None
    if args.pit:
        pit_changes = fetch_sp500_pit_changes(cache=Path("data/raw/sp500_pit_changes.parquet"))
        keep_set = ever_members(pit_changes)
        sector = dict(zip(comp["ticker"], comp["sector"]))
    else:
        keep = {"large": ["500"], "small": ["600"], "all": ["500", "600"]}[args.cap]
        comp = comp[comp["index"].isin(keep)]
        sector = dict(zip(comp["ticker"], comp["sector"]))
        keep_set = set(comp["ticker"])

    px_cache = Path("data/raw/daily_px_statarb_wide.parquet")
    prices = pd.read_parquet(px_cache) if px_cache.exists() else fetch_prices_yf(
        sorted(keep_set), args.start, None)
    prices = prices[[c for c in prices.columns if c in keep_set]]
    rets = daily_returns(prices).clip(lower=-0.5, upper=1.0)

    etf_px = fetch_prices_yf(["SPY"] + sorted(set(SECTOR_ETF.values())), args.start, None)
    etf_ret = daily_returns(etf_px).reindex(rets.index)
    factor = {}
    for t in rets.columns:
        etf = SECTOR_ETF.get(sector.get(t, ""), "SPY")
        s = etf_ret[etf] if etf in etf_ret else etf_ret["SPY"]
        factor[t] = s.fillna(etf_ret["SPY"])
    factors = pd.DataFrame(factor).reindex(rets.index)

    pit_mask = None
    if args.pit:
        pit_mask = membership_mask(pit_changes, rets.index, list(rets.columns))

    res = run_residual(rets, factors, sector, window=args.window, entry=args.entry,
                       exit_=args.exit_, skip=args.skip, long_floor=args.long_floor,
                       cost_bps=args.cost_bps, pit_mask=pit_mask)
    net = res["net"]

    active = res["final_positions"].shift(1 + args.skip).abs()
    med_active = int(active.sum(axis=1).replace(0, pd.NA).dropna().median())
    tag = "point-in-time membership" if args.pit else f"{args.cap} cap"
    floor_tag = f", long-floor {args.long_floor}" if args.long_floor is not None else ""
    title = (f"StatArb residual reversion (Avellaneda-Lee) — {tag}{floor_tag}, {rets.shape[1]} names, "
             f"~{med_active} pos/day, skip={args.skip}, {args.cost_bps}bps")
    bench = {"equal_weight_universe": rets.mean(axis=1)}
    card = scorecard(net, bench, n_trials=args.n_trials, periods_per_year=252)
    stem = "residual_pit" if args.pit else "residual"
    if args.long_floor is not None:
        stem += f"_floor{args.long_floor}"
    (out / f"{stem}_scorecard.md").write_text(to_markdown(card, title))
    net.to_frame("net").to_parquet(out / f"{stem}_pnl.parquet")
    register(Path("data/manifest.jsonl"), name="statarb_" + stem, source="yfinance",
             filters={"window": args.window, "entry": args.entry, "names": int(rets.shape[1]),
                      "pit": bool(args.pit)},
             path=str(out / f"{stem}_pnl.parquet"), rows=int(net.ne(0).sum()))
    print(to_markdown(card, title))


if __name__ == "__main__":
    main()
