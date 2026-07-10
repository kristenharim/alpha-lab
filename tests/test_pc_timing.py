"""Offline tests for PC factor-timing. The key one is no-look-ahead: corrupting FUTURE returns must
not change any past month's projected PC values."""
import numpy as np
import pandas as pd

from core.backtest.engine import backtest
from tracks.gkx.models import expanding_window_predict
from tracks.gkx.pc_timing import (
    equal_weight_pc_benchmark,
    rolling_pc_returns,
    signal_weights_from_pc_scores,
    to_wide,
)


def _wide(n_signals=8, n_months=140, seed=1):
    rng = np.random.default_rng(seed)
    dates = pd.period_range("2010-01", periods=n_months, freq="M").to_timestamp()
    factor = rng.normal(0, 0.03, n_months)                       # a shared factor -> real PCs exist
    data = {f"s{i}": 0.6 * factor + rng.normal(0, 0.02, n_months) for i in range(n_signals)}
    return pd.DataFrame(data, index=dates)


def test_rolling_pc_shapes_and_sign_anchor():
    wide = _wide()
    pc_panel, loadings, cols = rolling_pc_returns(wide, k=3, min_train=36, refit_every=12)
    assert set(pc_panel["signalname"].unique()) == {"pc0", "pc1", "pc2"}
    assert pc_panel["date"].min() > wide.index[35]               # first 36 months reserved for the fit
    # sign anchor is deterministic: every active component sums to >= 0
    for ld in loadings.values():
        assert (ld.sum(axis=1) >= -1e-9).all()


def test_no_lookahead_future_corruption_does_not_leak():
    wide = _wide()
    clean, _, _ = rolling_pc_returns(wide, k=3, min_train=36, refit_every=12)
    cut = 100                                                    # corrupt everything from month 100 on
    poisoned_wide = wide.copy()
    poisoned_wide.iloc[cut:] += 999.0
    poisoned, _, _ = rolling_pc_returns(poisoned_wide, k=3, min_train=36, refit_every=12)
    cut_date = wide.index[cut]
    a = clean[clean["date"] < cut_date].reset_index(drop=True)
    b = poisoned[poisoned["date"] < cut_date].reset_index(drop=True)
    # PC returns before the corruption are byte-identical -> no future data reached the fit or projection
    pd.testing.assert_frame_equal(a, b)


def test_signal_weights_are_gross_normalized_and_scoped():
    wide = _wide()
    pc_panel, loadings, cols = rolling_pc_returns(wide, k=3, min_train=36)
    preds = expanding_window_predict(pc_panel, model="ols", min_train_months=24)
    w = signal_weights_from_pc_scores(preds, loadings, cols)
    active = w.loc[(w.abs().sum(axis=1) > 0)]
    assert not active.empty
    assert np.allclose(active.abs().sum(axis=1), 1.0)            # gross exposure normalized to 1
    assert set(w.columns) <= set(cols)


def test_end_to_end_runs_through_backtest():
    wide = _wide()
    pc_panel, loadings, cols = rolling_pc_returns(wide, k=3, min_train=36)
    preds = expanding_window_predict(pc_panel, model="ridge", min_train_months=24)
    w = signal_weights_from_pc_scores(preds, loadings, cols)
    net = backtest(w, wide, cost_bps=5.0)["net"].dropna()
    assert len(net) > 0 and np.isfinite(net).all()


def test_equal_weight_pc_benchmark_matches_signal_universe():
    wide = _wide()
    _, loadings, cols = rolling_pc_returns(wide, k=3, min_train=36)
    ew = equal_weight_pc_benchmark(loadings, cols, list(loadings.keys()))
    active = ew.loc[(ew.abs().sum(axis=1) > 0)]
    assert np.allclose(active.abs().sum(axis=1), 1.0)
