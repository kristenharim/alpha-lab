"""Agent 1 leakage battery: truncation test + future-poison test on all 7 active books.

Truncation: weights at date t computed from panel[:t] must equal weights at t from the
full panel — any diff means the spec's weight at t depends on data after t (look-ahead)
OR on panel-end conventions (backtest/live drift). Distinguished by the poison test:
poisoning FUTURE data and seeing past weights change is look-ahead proper.
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HUNT = Path(__file__).resolve().parents[3] / "research" / "hunt2026"
sys.path.insert(0, str(HUNT))
import harness  # noqa: E402

BOOKS = ["vol_managed_qqq", "vol_core_svxy", "trend_vol_qqq", "defensive_ensemble",
         "dual_momentum_gold", "momentum_concentrated", "dual_momentum_gem"]

panel = pd.read_parquet(HUNT / "panel_2005.parquet")
print(f"panel_2005: {panel.index[0].date()} -> {panel.index[-1].date()}, "
      f"{len(panel)} rows, tz={panel.index.tz}, dup_dates={panel.index.duplicated().any()}, "
      f"monotonic={panel.index.is_monotonic_increasing}")

TEST_DATES = [d for d in ["2018-02-06", "2020-03-18", "2022-06-15", "2024-06-28",
                          "2025-01-31", "2025-11-12", "2026-03-31"]
              if pd.Timestamp(d) in panel.index]
print("truncation dates:", TEST_DATES)

mods = {b: harness.load_spec(HUNT / "specs" / b) for b in BOOKS}
W_full = {b: mods[b].target_weights(panel).astype(float).fillna(0.0) for b in BOOKS}

print("\n== TRUNCATION TEST (max |w_trunc(t) - w_full(t)| at t) ==")
trunc_fail = {}
for d in TEST_DATES:
    t = pd.Timestamp(d)
    sub = panel[panel.index <= t]
    for b in BOOKS:
        Wt = mods[b].target_weights(sub).astype(float).fillna(0.0)
        a = Wt.loc[t]
        f = W_full[b].loc[t].reindex(a.index).fillna(0.0)
        diff = float((a - f).abs().max())
        if diff > 1e-9:
            trunc_fail.setdefault(b, []).append((d, diff))
            top = (a - f).abs().nlargest(3)
            print(f"  DIFF {b} @ {d}: max {diff:.4f}  ({dict(top.round(4))})")
for b in BOOKS:
    if b not in trunc_fail:
        print(f"  OK   {b}: identical at all {len(TEST_DATES)} dates")

print("\n== FUTURE-POISON TEST (scale last 21 rows of close x7; weights before must not move) ==")
poison = panel.copy()
tail = poison.index[-21:]
cl = poison["close"].copy()
cl.loc[tail] = cl.loc[tail] * 7.0
poison[[("close", c) for c in cl.columns]] = cl.values  # reassign close block
cutoff = panel.index[-22]
for b in BOOKS:
    Wp = mods[b].target_weights(poison).astype(float).fillna(0.0)
    a = Wp.loc[:cutoff]
    f = W_full[b].loc[:cutoff].reindex(columns=a.columns).fillna(0.0)
    diff = float((a - f.reindex(a.index).fillna(0.0)).abs().max().max())
    if diff > 1e-9:
        col = (a - f).abs().max().idxmax()
        row = (a - f).abs().max(axis=1).idxmax()
        print(f"  LEAK {b}: max {diff:.5f} at {row.date()} col {col}")
    else:
        print(f"  OK   {b}: past weights unchanged under future poison")
