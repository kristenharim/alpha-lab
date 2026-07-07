import numpy as np
import pandas as pd
import pytest
from tracks.statarb.bands import band_positions
from tracks.statarb.pairs import (normalize_prices, select_pairs, select_pairs_sectored,
                                  spread_zscore, pair_pnl, pair_zscore_oos)
from tracks.statarb.residual import residual_returns, s_score


# ---- shared band logic ----

def test_band_positions_enter_hold_exit():
    # series crosses -2 (enter long), stays, then reverts past -0.5 (exit)
    z = pd.Series([0.0, -2.5, -1.0, -0.2, 2.5, 0.1])
    pos = band_positions(z, entry=2.0, exit_=0.5)
    assert pos.iloc[0] == 0        # nothing
    assert pos.iloc[1] == 1        # z<=-2 -> long spread
    assert pos.iloc[2] == 1        # hold (between exit and entry)
    assert pos.iloc[3] == 0        # |z|<=0.5 -> flat
    assert pos.iloc[4] == -1       # z>=2 -> short spread
    assert pos.iloc[5] == 0        # exit


# ---- pairs (Gatev-Goetzmann-Rouwenhorst) ----

def test_normalize_prices_starts_at_one():
    idx = pd.date_range("2024-01-01", periods=3, freq="B")
    px = pd.DataFrame({"A": [10, 11, 12], "B": [50, 55, 60]}, index=idx)
    norm = normalize_prices(px)
    assert np.allclose(norm.iloc[0], 1.0)


def test_select_pairs_picks_closest():
    idx = pd.date_range("2024-01-01", periods=50, freq="B")
    rng = np.random.default_rng(0)
    base = np.cumsum(rng.normal(0, 0.5, 50)) + 100
    px = pd.DataFrame({
        "A": base,
        "B": base + rng.normal(0, 0.1, 50),   # tracks A closely
        "C": np.cumsum(rng.normal(0, 0.5, 50)) + 100,  # unrelated
    }, index=idx)
    pairs = select_pairs(px, n_pairs=1)
    assert pairs[0] == ("A", "B") or pairs[0] == ("B", "A")


def test_select_pairs_sectored_only_within_sector():
    idx = pd.date_range("2024-01-01", periods=40, freq="B")
    rng = np.random.default_rng(4)
    base = np.cumsum(rng.normal(0, 0.5, 40)) + 100
    px = pd.DataFrame({
        "A": base, "B": base + rng.normal(0, 0.1, 40),   # tech, close
        "C": np.cumsum(rng.normal(0, 0.5, 40)) + 100,     # fin
        "D": np.cumsum(rng.normal(0, 0.5, 40)) + 100,     # fin
    }, index=idx)
    sectors = {"A": "Tech", "B": "Tech", "C": "Fin", "D": "Fin"}
    pairs = select_pairs_sectored(px, sectors, n_pairs=5)
    # no cross-sector pair may appear
    for a, b in pairs:
        assert sectors[a] == sectors[b]


def test_pair_pnl_no_lookahead_and_profits_on_convergence():
    idx = pd.date_range("2024-01-01", periods=4, freq="B")
    # positions long spread (+1) from day1; A outperforms B next day
    pos = pd.Series([1, 1, 1, 1], index=idx)
    ret_a = pd.Series([0.0, 0.03, 0.0, 0.0], index=idx)
    ret_b = pd.Series([0.0, 0.01, 0.0, 0.0], index=idx)
    pnl = pair_pnl(pos, ret_a, ret_b)
    # day2 pnl = pos(day1) * (ret_a-ret_b)(day2) = 1*(0.03-0.01)=0.02
    assert np.isclose(pnl.iloc[1], 0.02)
    assert np.isclose(pnl.iloc[0], 0.0)   # no position lag on day0


def test_pair_zscore_oos_uses_formation_stats_only():
    fidx = pd.date_range("2024-01-01", periods=60, freq="B")
    tidx = pd.date_range("2024-03-25", periods=30, freq="B")
    # formation: A and B track with small spread noise
    rng = np.random.default_rng(5)
    fa = pd.Series(100 + np.cumsum(rng.normal(0, 0.3, 60)), index=fidx)
    fb = pd.Series(fa.values + rng.normal(0, 0.5, 60), index=fidx)
    # trading: B jumps up -> spread goes sharply negative -> z should be large negative
    ta = pd.Series(fa.iloc[-1] + np.cumsum(rng.normal(0, 0.3, 30)), index=tidx)
    tb = pd.Series(ta.values + 5.0, index=tidx)   # B persistently 5 above A
    z = pair_zscore_oos(fa, fb, ta, tb)
    assert z.index.equals(tidx)
    assert z.dropna().iloc[-1] < -2   # divergence flagged out-of-sample


def test_spread_zscore_zero_mean():
    idx = pd.date_range("2024-01-01", periods=60, freq="B")
    rng = np.random.default_rng(1)
    a = pd.Series(np.cumsum(rng.normal(0, 0.5, 60)) + 100, index=idx)
    b = pd.Series(a.values + rng.normal(0, 1.0, 60), index=idx)
    z = spread_zscore(a, b, window=20)
    assert abs(z.dropna().mean()) < 1.0


# ---- residual reversion (Avellaneda-Lee lite) ----

def test_residual_returns_orthogonal_to_factor():
    idx = pd.date_range("2024-01-01", periods=100, freq="B")
    rng = np.random.default_rng(2)
    factor = pd.Series(rng.normal(0, 0.01, 100), index=idx, name="MKT")
    # stock = 1.5*factor + noise
    stock = pd.DataFrame({"A": 1.5 * factor.values + rng.normal(0, 0.005, 100)}, index=idx)
    resid = residual_returns(stock, factor.to_frame())
    # residual should be ~uncorrelated with the factor
    assert abs(np.corrcoef(resid["A"], factor)[0, 1]) < 0.2


def test_s_score_mean_reverting_signal():
    idx = pd.date_range("2024-01-01", periods=80, freq="B")
    # a residual series with a clear excursion then reversion
    resid = pd.Series(np.concatenate([np.zeros(40), np.full(10, -0.02), np.zeros(30)]), index=idx)
    s = s_score(resid, window=30)
    # during the negative excursion, cumulative residual dips -> s-score negative
    assert s.iloc[45] < 0
