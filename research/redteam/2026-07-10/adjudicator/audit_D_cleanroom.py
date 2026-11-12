"""Audit D: clean-room completion. Patches Agent 8's buggy month_ends/week_ends helpers
(pandas groupby-apply KeyError), then compares clean-room weights (built from specs only)
vs the frozen spec.py weights, per book, daily. Tolerance 1bp on net returns."""
import sys
from pathlib import Path
import numpy as np
import pandas as pd

RT = Path.home() / "projects/alpha-lab/redteam/2026-07-10/agent8"
HUNT = Path.home() / "projects/alpha-lab/research/hunt2026"
sys.path.insert(0, str(HUNT))
import harness  # only for load_spec (reference weights) + run (reference net)
sys.path.insert(0, str(RT))
import replica


def month_ends(idx):
    idx = pd.DatetimeIndex(idx)
    pos = pd.Series(np.arange(len(idx)), index=idx).groupby([idx.year, idx.month]).last().values
    return idx[pos].values


def week_ends(idx):
    idx = pd.DatetimeIndex(idx)
    iso = idx.isocalendar()
    pos = pd.Series(np.arange(len(idx)), index=idx).groupby(
        [iso.year.values, iso.week.values]).last().values
    return idx[np.sort(pos)].values


replica.month_ends = month_ends
replica.week_ends = week_ends

panel = pd.read_parquet(HUNT / "panel_2005.parquet")
CUT = harness.META["cut"]
print(f"{'book':24} {'wt_maxdiff':>11} {'net_maxdiff_bp':>14} {'cr_total':>9} {'sp_total':>9} {'first_diff_date':>16}")
for name, fn in replica.BOOKS.items():
    W_cr = fn(panel).astype(float).fillna(0.0)
    spec = harness.load_spec(HUNT / "specs" / name)
    W_sp = spec.target_weights(panel).astype(float).fillna(0.0)
    cols = sorted(set(W_cr.columns) | set(W_sp.columns))
    A = W_cr.reindex(columns=cols, fill_value=0.0)
    B = W_sp.reindex(columns=cols, fill_value=0.0)
    wdiff = (A - B).abs()
    wmax = float(wdiff.max().max())
    # net comparison via the SAME independent scorer for both weight sets (isolates weights)
    cr_net = replica.score(W_cr, panel, start=CUT)["net_daily"]
    sp_net = replica.score(W_sp, panel, start=CUT)["net_daily"]
    ndiff = (cr_net - sp_net).abs()
    nmax_bp = float(ndiff.max()) * 1e4
    fdate = ""
    over = wdiff.max(axis=1)
    hits = over[over > 1e-6]
    if len(hits):
        fdate = str(hits.index[0].date())
    print(f"{name:24} {wmax:>11.4f} {nmax_bp:>14.3f} "
          f"{(1+cr_net).prod()-1:>9.4f} {(1+sp_net).prod()-1:>9.4f} {fdate:>16}")
