"""Ablation sweep: run the residual book under a cumulative stack of production layers, one comparison
table. Emits the per-signal log + net-returns parquet per config (the compute->present seam that feeds
QuantStats / the ML meta-model / the notebook). Full history, S&P 500.

Usage: .venv/bin/python scripts/statarb_ablation_run.py [--cost-bps 10]
"""
import argparse
from pathlib import Path

import pandas as pd

from core.data.prices import (daily_returns, fetch_prices_yf, fetch_volume_yf, rolling_dollar_adv)
from core.data.registry import register
from core.data.universe import fetch_sp_composite
from core.eval.run_manifest import stamp_run
from core.eval.scorecard import scorecard
from tracks.statarb import filters as F
from tracks.statarb.paper.ledger import Ledger
from tracks.statarb.trades import trade_stats
from tracks.statarb.book import SECTOR_ETF, run_residual

COLS = ["config", "n_signals", "n_entered", "win_rate", "avg_holding_days",
        "ann_return", "sharpe", "max_drawdown", "deflated_sharpe_prob"]


def ablation_table(rows: list[dict]) -> str:
    head = "| " + " | ".join(COLS) + " |"
    sep = "| " + " | ".join("---" for _ in COLS) + " |"
    def fmt(v):
        return f"{v:.2f}" if isinstance(v, float) else str(v)
    body = ["| " + " | ".join(fmt(r.get(c, "")) for c in COLS) + " |" for r in rows]
    return "\n".join([head, sep, *body]) + "\n"


def _row(name, out):
    card = scorecard(out["net"], {}, n_trials=20, periods_per_year=252)
    return {"config": name, **trade_stats(out["trades"]), "sharpe": card["sharpe"],
            "ann_return": card["ann_return"], "max_drawdown": card["max_drawdown"],
            "deflated_sharpe_prob": card["deflated_sharpe_prob"]}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cost-bps", type=float, default=10.0)
    ap.add_argument("--start", default="2018-01-01")
    ap.add_argument("--liquidity-adv", type=float, default=5e6)
    ap.add_argument("--sector-cap", type=float, default=0.20)
    ap.add_argument("--name-cap", type=float, default=0.02)
    args = ap.parse_args()

    out_dir = Path("artifacts/statarb/ablation")
    out_dir.mkdir(parents=True, exist_ok=True)
    log_root = Path("artifacts/statarb/signal_log")
    if log_root.exists():                     # idempotent: don't double-append on re-run
        import shutil
        shutil.rmtree(log_root)

    comp = fetch_sp_composite(cache=Path("data/raw/sp_composite.parquet"))
    comp = comp[comp["index"] == "500"]
    sectors = dict(zip(comp["ticker"], comp["sector"]))
    expected = len(sectors)

    # reuse the wide price cache if present, else fetch S&P 500
    px_cache = Path("data/raw/daily_px_statarb_wide.parquet")
    if px_cache.exists():
        prices = pd.read_parquet(px_cache)
        prices = prices[[c for c in prices.columns if c in sectors]]
    else:
        prices = fetch_prices_yf(sorted(sectors), args.start, None)
        prices = prices[[c for c in prices.columns if c in sectors]]
    # universe integrity — a truncated pull would silently shift the headline Sharpe. Fail loud.
    if prices.shape[1] < 0.9 * expected:
        raise RuntimeError(f"universe truncated: {prices.shape[1]}/{expected} S&P 500 names have "
                           f"price data — refusing to run (would misstate the headline Sharpe)")
    print(f"universe: {prices.shape[1]}/{expected} S&P 500 names")

    rets = daily_returns(prices).clip(lower=-0.5, upper=1.0)
    etf = daily_returns(fetch_prices_yf(["SPY"] + sorted(set(SECTOR_ETF.values())),
                                        args.start, None)).reindex(rets.index)
    factors = pd.DataFrame({t: etf.get(SECTOR_ETF.get(sectors.get(t, ""), "SPY"),
                                       etf["SPY"]).fillna(etf["SPY"])
                            for t in rets.columns}).reindex(rets.index)

    # liquidity + volume_ratio feature
    vol_cache = Path("data/raw/daily_vol_statarb.parquet")
    volume = (pd.read_parquet(vol_cache) if vol_cache.exists()
              else fetch_volume_yf(sorted(rets.columns), args.start, None))
    if not vol_cache.exists():
        volume.to_parquet(vol_cache)
    volume = volume.reindex(rets.index)[[c for c in rets.columns if c in volume.columns]]
    adv = rolling_dollar_adv(prices.reindex(rets.index), volume, window=20)
    features = {"volatility": rets.rolling(60).std(),
                "volume_ratio": (volume / volume.rolling(20).mean()).reindex_like(rets)}

    # earnings blackout — graceful: a partial/failed fetch only weakens the blackout layer, never
    # the universe or the headline result. Cached to a parquet (shared across the two venvs).
    blackout = None
    earn_cache = Path("data/raw/statarb_earnings.parquet")
    try:
        from tracks.pead.events import fetch_earnings_yf
        earn = pd.read_parquet(earn_cache) if earn_cache.exists() else fetch_earnings_yf(sorted(rets.columns))
        if not earn_cache.exists():
            earn.to_parquet(earn_cache)
        cov = earn["ticker"].nunique() / rets.shape[1]
        print(f"earnings coverage: {cov:.0%} of names")
        blackout = F.earnings_window_mask(rets.index, earn, before=2, after=1, columns=list(rets.columns))
    except Exception as e:
        print(f"earnings blackout degraded ({type(e).__name__}: {e}) — 'all_on' == 'sector_cap'")

    CB = args.cost_bps
    liq = dict(liquidity_adv=args.liquidity_adv, dollar_adv=adv)
    cap = dict(sector_cap_=args.sector_cap, name_cap=args.name_cap)
    configs = [
        ("baseline", dict(cost_bps=0.0)),
        ("costs", dict(cost_bps=CB)),
        ("liquidity", dict(cost_bps=CB, **liq)),
        ("sector_cap", dict(cost_bps=CB, **liq, **cap)),
        ("all_on", dict(cost_bps=CB, **liq, **cap, **({"blackout": blackout} if blackout is not None else {}))),
    ]

    rows = []
    for name, kw in configs:
        out = run_residual(rets, factors, sectors, window=60, entry=1.25, exit_=0.5,
                           skip=1, features=features, **kw)
        rows.append(_row(name, out))
        out["net"].to_frame("net").to_parquet(out_dir / f"{name}_net.parquet")
        if name == "costs":   # persist for the real-engine gated ML backtest (equal-weight path)
            out["final_positions"].to_parquet(out_dir / "costs_positions.parquet")
            out["resid"].to_parquet(out_dir / "resid.parquet")
            out["hedged"].to_parquet(out_dir / "hedged.parquet")
        led = Ledger(log_root / name)
        for t in out["trades"]:
            led.append("signal_log", t)
        print(f"  {name}: Sharpe {rows[-1]['sharpe']:.2f}, {rows[-1]['n_signals']} signals")

    md = ablation_table(rows)
    (out_dir / "table.md").write_text("# StatArb ablation — S&P 500, full history\n\n" + md)
    pd.DataFrame(rows).to_parquet(out_dir / "table.parquet")
    register(Path("data/manifest.jsonl"), name="statarb_ablation", source="yfinance",
             filters={"cost_bps": CB, "configs": [c[0] for c in configs]},
             path=str(out_dir / "table.parquet"), rows=len(rows))
    stamp_run("statarb", "ablation",
              {"cost_bps": CB, "liquidity_adv": args.liquidity_adv,
               "sector_cap": args.sector_cap, "name_cap": args.name_cap}, n_trials=len(configs))
    print("\n" + md)


if __name__ == "__main__":
    main()
