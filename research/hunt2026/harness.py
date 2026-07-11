"""hunt2026 shared scoring harness. One P&L convention for every spec — implementable only.

Spec interface (frozen): a module exposing  target_weights(panel) -> DataFrame
  - panel: MultiIndex-column frame, level 0 in {open, close, volume, member}, level 1 = ticker.
  - returns daily target weights (dates x tickers), fraction of NAV, set at each date's CLOSE
    using information through that close. May cover any subset of panel dates/tickers.

P&L convention (identical for all specs — no residual-space accounting):
  - weights set at close t earn close-to-close returns at t+1 (held = W.shift(1))
  - costs per side: 10 bps stocks, 2 bps ETFs, charged on |change in weight|
  - gross exposure sum|w| capped at 2.0: days above are scaled down (violation counted)
  - signal-only tickers (^VIX) must carry zero weight — nonzero raises
"""
import importlib.util
import json
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).parent
META = json.loads((HERE / "sandbox_meta.json").read_text())
STOCK_BPS, ETF_BPS, MAX_GROSS = 10.0, 2.0, 2.0


def load_train():
    return pd.read_parquet(HERE / "train.parquet")


def load_full():
    """EVALUATOR ONLY: train + holdout concatenated (history needed for lookbacks)."""
    return pd.concat([pd.read_parquet(HERE / "train.parquet"),
                      pd.read_parquet(HERE / "holdout.parquet")])


def load_spec(spec_dir):
    spec_dir = Path(spec_dir)
    s = importlib.util.spec_from_file_location(spec_dir.name, spec_dir / "spec.py")
    mod = importlib.util.module_from_spec(s)
    s.loader.exec_module(mod)
    return mod


def per_side_bps(tickers):
    etf = set(META["etfs"])
    return pd.Series([ETF_BPS if t in etf else STOCK_BPS for t in tickers], index=tickers)


def run(spec_mod, panel, start=None, end=None):
    """Score a spec on panel, P&L restricted to [start, end]. Returns dict of results."""
    W = spec_mod.target_weights(panel).astype(float).fillna(0.0)
    bad = [t for t in W.columns if t in META["signal_only"] and W[t].abs().sum() > 0]
    if bad:
        raise ValueError(f"weights on signal-only tickers: {bad}")

    gross_exp = W.abs().sum(axis=1)
    violations = int((gross_exp > MAX_GROSS + 1e-9).sum())
    scale = (MAX_GROSS / gross_exp).clip(upper=1.0).fillna(1.0)
    W = W.mul(scale, axis=0)

    close = panel["close"][W.columns]
    rets = close.pct_change(fill_method=None)
    held = W.shift(1)
    gross = (held * rets).sum(axis=1, min_count=1).fillna(0.0)
    bps = per_side_bps(W.columns)
    cost = (W.diff().abs().fillna(W.abs()) * (bps / 1e4)).sum(axis=1)
    net = gross - cost

    idx = net.index
    if start is not None:
        idx = idx[idx > pd.Timestamp(start)]
    if end is not None:
        idx = idx[idx <= pd.Timestamp(end)]
    net, gross, cost = net.reindex(idx), gross.reindex(idx), cost.reindex(idx)

    nav = (1 + net).cumprod()
    monthly = nav.resample("ME").last().pct_change(fill_method=None)
    monthly.iloc[0] = nav.resample("ME").last().iloc[0] - 1
    quarterly = nav.resample("QE").last().pct_change(fill_method=None)
    quarterly.iloc[0] = nav.resample("QE").last().iloc[0] - 1
    return {
        "net_daily": net,
        "total_net": float(nav.iloc[-1] - 1),
        "total_gross": float((1 + gross).prod() - 1),
        "ann_vol": float(net.std() * np.sqrt(252)),
        "sharpe": float(net.mean() / net.std() * np.sqrt(252)) if net.std() > 0 else 0.0,
        "max_dd": float((nav / nav.cummax() - 1).min()),
        "avg_gross_exposure": float(held.reindex(idx).abs().sum(axis=1).mean()),
        "avg_daily_turnover": float(W.diff().abs().sum(axis=1).reindex(idx).mean()),
        "cost_drag_ann": float(cost.mean() * 252),
        "gross_cap_violations": violations,
        "monthly": monthly,
        "quarterly": quarterly,
    }


def spy_benchmark(panel, start=None, end=None):
    """Buy-and-hold SPY net series over the identical window (2 bps entry)."""
    class _Spy:
        @staticmethod
        def target_weights(p):
            c = p["close"]
            return pd.DataFrame(0.0, index=c.index, columns=c.columns).assign(SPY=1.0)
    return run(_Spy, panel, start, end)


if __name__ == "__main__":
    # self-check on train data: SPY buy-and-hold must roughly match SPY total return
    panel = load_train()
    r = spy_benchmark(panel, start="2024-01-01")
    spy = panel["close"]["SPY"]
    raw = spy.iloc[-1] / spy[spy.index > "2024-01-01"].iloc[0] - 1
    assert abs(r["total_net"] - raw) < 0.02, (r["total_net"], raw)
    print(f"self-check OK: harness SPY {r['total_net']:.2%} vs raw {raw:.2%}, "
          f"sharpe {r['sharpe']:.2f}, cost drag {r['cost_drag_ann']:.4%}")
