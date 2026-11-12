"""Audit C: adversarial implementation. Predeclared variant set (BEFORE running):
  base         : harness convention (weight at close t earns close t -> close t+1)
  open_to_open : REALISTIC live timing: you enter at opens but HOLD through overnight.
                 Position W.shift(1) earns open(t)->open(t+1). Overnight gap is captured
                 (held, not forgone). This is what hunt_paper_run actually does.
  intraday_only: pessimal: re-establish whole book at each open, earn open->close only,
                 forgo EVERY overnight gap daily. NOT how the live book trades; included
                 only to expose overnight-gap dependence (the night/day effect).
  delay1       : signal delayed one full day (held = W.shift(2))
  cost_x2      : per-side costs doubled
  fill_5bps    : +5 bps conservative slippage on every unit of turnover
  whole_shares : round each position to whole shares at a $14.4k book (rounding drag)
Report degradation of total net vs base, per book, holdout year + 5y. No worst-of-N cherry pick."""
import sys
from pathlib import Path
import numpy as np
import pandas as pd

HUNT = Path.home() / "projects/alpha-lab/research/hunt2026"
sys.path.insert(0, str(HUNT))
import harness

BOOKS = ["vol_managed_qqq", "vol_core_svxy", "trend_vol_qqq", "defensive_ensemble",
         "dual_momentum_gold", "dual_momentum_gem", "momentum_concentrated"]
panel = pd.read_parquet(HUNT / "panel_2005.parquet")
etf = set(harness.META["etfs"])
CUT, CUT5 = harness.META["cut"], "2021-07-10"
BOOK_NOTIONAL = 14400.0


def score_variant(W, variant, start):
    W = W.astype(float).fillna(0.0)
    g = W.abs().sum(axis=1)
    W = W.mul((2.0 / g).clip(upper=1.0).fillna(1.0), axis=0)
    close = panel["close"][W.columns]
    opn = panel["open"][W.columns]
    bps = pd.Series([2.0 if t in etf else 10.0 for t in W.columns], index=W.columns) / 1e4
    c2c = close.pct_change(fill_method=None)

    if variant == "open_to_open":
        # realistic: enter at opens, hold overnight -> position earns open(t)->open(t+1)
        o2o = (opn.shift(-1) / opn - 1.0)  # return realized over the day you hold from open t
        gross = (W.shift(1) * o2o).sum(axis=1, min_count=1).fillna(0.0)
    elif variant == "intraday_only":
        o2c = (close / opn - 1.0)
        gross = (W.shift(1) * o2c).sum(axis=1, min_count=1).fillna(0.0)
    elif variant == "delay1":
        gross = (W.shift(2) * c2c).sum(axis=1, min_count=1).fillna(0.0)
    else:
        gross = (W.shift(1) * c2c).sum(axis=1, min_count=1).fillna(0.0)

    turn = W.diff().abs().fillna(W.abs())
    if variant == "cost_x2":
        cost = (turn * bps * 2).sum(axis=1)
    elif variant == "fill_5bps":
        cost = (turn * (bps + 5e-4)).sum(axis=1)
    elif variant == "whole_shares":
        # round target notional to whole shares, recompute effective weight drift
        px = close.replace(0, np.nan)
        shares = (W * BOOK_NOTIONAL / px).round()
        W_eff = (shares * px / BOOK_NOTIONAL).fillna(0.0)
        gross = (W_eff.shift(1) * c2c).sum(axis=1, min_count=1).fillna(0.0)
        cost = (W_eff.diff().abs().fillna(W_eff.abs()) * bps).sum(axis=1)
    else:
        cost = (turn * bps).sum(axis=1)
    net = (gross - cost)
    idx = net.index[net.index > pd.Timestamp(start)]
    return float((1 + net.reindex(idx)).prod() - 1)


VARIANTS = ["base", "open_to_open", "intraday_only", "delay1", "cost_x2", "fill_5bps", "whole_shares"]
print(f"HOLDOUT YEAR ({CUT}+)")
print(f"{'book':22} " + " ".join(f"{v:>11}" for v in VARIANTS))
rows = {}
for name in BOOKS:
    W = harness.load_spec(HUNT / "specs" / name).target_weights(panel)
    vals = {v: score_variant(W, v, CUT) for v in VARIANTS}
    rows[name] = vals
    print(f"{name:22} " + " ".join(f"{vals[v]:>+11.4f}" for v in VARIANTS))
print("\ndegradation vs base (holdout):")
print(f"{'book':22} " + " ".join(f"{v:>11}" for v in VARIANTS[1:]))
for name in BOOKS:
    b = rows[name]["base"]
    print(f"{name:22} " + " ".join(f"{rows[name][v]-b:>+11.4f}" for v in VARIANTS[1:]))
