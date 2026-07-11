import numpy as np
import pandas as pd
import pytest
from tracks.statarb.bands import band_positions
from tracks.statarb.pairs import (normalize_prices, select_pairs, select_pairs_sectored,
                                  spread_zscore, pair_pnl, pair_zscore_oos)
from tracks.statarb.residual import residual_returns, s_score, rolling_residual


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


def test_band_long_floor_skips_and_stops_falling_knives():
    # deep dip below the floor: never enter long
    deep = pd.Series([0.0, -3.0, -0.2])
    assert band_positions(deep, entry=1.25, exit_=0.5, long_floor=2.5).tolist() == [0, 0, 0]
    # enter at a shallow dip, then it keeps falling past the floor -> stop out the long
    knife = pd.Series([0.0, -1.5, -3.0, -0.2])
    assert band_positions(knife, entry=1.25, exit_=0.5, long_floor=2.5).tolist() == [0, 1, 0, 0]
    # short side is unaffected by long_floor
    up = pd.Series([0.0, 3.0, 0.1])
    assert band_positions(up, entry=1.25, exit_=0.5, long_floor=2.5).tolist() == [0, -1, 0]


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


def test_rolling_residual_orthogonal_and_lagged():
    idx = pd.date_range("2022-01-01", periods=300, freq="B")
    rng = np.random.default_rng(9)
    fac = pd.Series(rng.normal(0, 0.01, 300), index=idx)
    # two stocks: S1 = 1.2*fac + noise, S2 = 0.8*fac + noise
    stock = pd.DataFrame({
        "S1": 1.2 * fac.values + rng.normal(0, 0.004, 300),
        "S2": 0.8 * fac.values + rng.normal(0, 0.004, 300),
    }, index=idx)
    factors = pd.DataFrame({"S1": fac.values, "S2": fac.values}, index=idx)
    resid = rolling_residual(stock, factors, window=60)
    # residuals should be much less correlated with the factor than the raw returns
    r = resid.dropna()
    assert abs(np.corrcoef(r["S1"], fac.reindex(r.index))[0, 1]) < 0.3
    assert abs(np.corrcoef(r["S2"], fac.reindex(r.index))[0, 1]) < 0.3
    # first window rows are NaN (no look-ahead: beta needs a trailing window, then lag)
    assert resid["S1"].iloc[:60].isna().all()


def test_s_score_mean_reverting_signal():
    idx = pd.date_range("2024-01-01", periods=80, freq="B")
    # a residual series with a clear excursion then reversion
    resid = pd.Series(np.concatenate([np.zeros(40), np.full(10, -0.02), np.zeros(30)]), index=idx)
    s = s_score(resid, window=30)
    # during the negative excursion, cumulative residual dips -> s-score negative
    assert s.iloc[45] < 0


def test_hedged_returns_identity():
    # hedged == residual + lagged alpha (the unhedgeable drift the engine no longer credits)
    from tracks.statarb.residual import hedged_returns, rolling_beta, rolling_residual
    rng = np.random.default_rng(7)
    idx = pd.date_range("2022-01-03", periods=100, freq="B")
    fac = pd.DataFrame(rng.normal(0, 0.01, (100, 3)), index=idx, columns=list("ABC"))
    rets = 0.8 * fac + pd.DataFrame(rng.normal(0.001, 0.02, (100, 3)), index=idx, columns=list("ABC"))
    w = 30
    resid = rolling_residual(rets, fac, window=w)
    hedged = hedged_returns(rets, fac, window=w)
    beta = rolling_beta(rets, fac, window=w)
    alpha = rets.rolling(w).mean() - beta * fac.rolling(w).mean()
    diff = (hedged - resid - alpha.shift(1)).astype(float).abs()
    assert diff.max().max() < 1e-12


def test_drift_adjusted_s_score_zero_drift_matches_s_score():
    # with zero drift the modified s-score equals the plain one wherever the AR(1) fit is valid
    from tracks.statarb.residual import drift_adjusted_s_score, s_score
    rng = np.random.default_rng(3)
    idx = pd.date_range("2022-01-03", periods=200, freq="B")
    resid = pd.DataFrame(rng.normal(0, 0.01, (200, 4)), index=idx, columns=list("ABCD"))
    w = 40
    plain = s_score(resid, window=w)
    zero = pd.DataFrame(0.0, index=idx, columns=list("ABCD"))
    mod = drift_adjusted_s_score(resid, zero, window=w)
    both = mod.notna() & plain.notna()
    assert both.to_numpy().sum() > 100
    assert (mod - plain).abs()[both].max().max() < 1e-12


def test_drift_adjusted_s_score_drift_moves_signal_against_entry():
    # negative drift (a falling name) must make the long side LESS attractive: s_mod > s
    from tracks.statarb.residual import drift_adjusted_s_score
    rng = np.random.default_rng(5)
    idx = pd.date_range("2022-01-03", periods=200, freq="B")
    resid = pd.DataFrame(rng.normal(0, 0.01, (200, 2)), index=idx, columns=list("AB"))
    neg = pd.DataFrame(-0.002, index=idx, columns=list("AB"))
    mod = drift_adjusted_s_score(resid, neg, window=40)
    from tracks.statarb.residual import s_score
    plain = s_score(resid, window=40)
    diff = (mod - plain)[mod.notna() & plain.notna()].stack()
    assert len(diff) > 100 and (diff > 0).all()
