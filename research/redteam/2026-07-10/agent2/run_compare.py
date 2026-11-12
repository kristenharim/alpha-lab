"""Adjudicator-written driver for Agent 2's independent engine (agent died before writing it).
Compares harness.run net_daily vs the independent weight_engine, per book, daily, 1bp tolerance."""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HUNT = Path.home() / "projects/alpha-lab/research/hunt2026"
sys.path.insert(0, str(HUNT))
import harness  # the engine under audit
sys.path.insert(0, str(Path(__file__).parent))
from indep_engine import weight_engine

BOOKS = ["vol_managed_qqq", "vol_core_svxy", "trend_vol_qqq", "defensive_ensemble",
         "dual_momentum_gold", "dual_momentum_gem", "momentum_concentrated"]
panel = pd.read_parquet(HUNT / "panel_2005.parquet")
etf = set(harness.META["etfs"])
CUT = harness.META["cut"]  # 1y holdout start

print(f"{'book':24} {'harness_net':>12} {'indep_net':>12} {'max|Δday|(bp)':>14} {'viol':>5}")
worst = 0.0
for name in BOOKS:
    spec = harness.load_spec(HUNT / "specs" / name)
    W = spec.target_weights(panel).astype(float).fillna(0.0)
    bps = {t: (harness.ETF_BPS if t in etf else harness.STOCK_BPS) for t in W.columns}
    # harness path
    r = harness.run(spec, panel, start=CUT)
    h_net = r["net_daily"]
    # independent path on identical weights
    i_net, viol = weight_engine(W, panel["close"], bps, start=CUT)
    i_net = i_net.reindex(h_net.index)
    dmax = float((h_net - i_net).abs().max()) * 1e4  # bp
    worst = max(worst, dmax)
    print(f"{name:24} {h_net.sum():>12.4f} {i_net.sum():>12.4f} {dmax:>14.4f} {viol:>5}")
print(f"\nworst daily divergence across all books: {worst:.4f} bp  "
      f"(tolerance 1.0 bp: {'PASS' if worst < 1.0 else 'FAIL'})")
