"""Leakage guards for the signal-quality meta-model.

Two distinct leakage species, both tested:
  (a) within-trade — exit-derived columns (holding_days, close_reason, realized_pnl...) must never
      enter the feature matrix. This is the one that produces a beautiful AUC that dies forward.
  (b) temporal — walk-forward must not predict a month using its own or future rows (the first month
      has no prior history and must stay unpredicted).

The dataset test runs anywhere (pandas only). The walk-forward test needs xgboost (train.py), so it
importorskips — it runs in .venv-report, is skipped in the audited .venv.
"""
import numpy as np
import pandas as pd
import pytest


def _fake_log(n=140):
    rng = np.random.default_rng(0)
    starts = pd.date_range("2024-01-01", periods=8, freq="MS")
    rows = []
    for _ in range(n):
        d = starts[rng.integers(0, 8)] + pd.Timedelta(days=int(rng.integers(0, 20)))
        s = float(rng.choice([-1, 1]) * rng.uniform(1.25, 3.0))
        rows.append({
            "entry_s": s, "residual": float(rng.normal(0, 0.02)),
            "sector": str(rng.choice(["A", "B", "C"])),
            "volatility": float(rng.uniform(0.01, 0.05)),
            "volume_ratio": float(rng.uniform(0.5, 3.0)),
            "entry_date": str(d.date()), "exit_date": str(d.date()),
            "holding_days": int(rng.integers(2, 15)), "close_reason": "reversion_exit",
            "realized_pnl": float(rng.normal(0, 0.02)), "counterfactual_pnl": None,
            "success": bool(rng.random() > 0.4),
        })
    return pd.DataFrame(rows)


def test_feature_matrix_has_no_exit_only_columns():
    from tracks.statarb.ml.dataset import EXIT_ONLY, build_features
    X, y, dates = build_features(_fake_log())
    assert set(X.columns).isdisjoint(EXIT_ONLY)          # (a) within-trade leakage guard
    assert "entry_s" in X.columns and "volatility" in X.columns
    assert len(X) == len(y) == len(dates)


def test_walk_forward_leaves_first_month_unpredicted():
    pytest.importorskip("xgboost")
    from tracks.statarb.ml.dataset import build_features
    from tracks.statarb.ml.train import walk_forward_oof
    X, y, dates = build_features(_fake_log())
    oof = walk_forward_oof(X, y, dates, "logistic")
    months = dates.dt.to_period("M")
    first = sorted(months.unique())[0]
    assert oof[months == first].isna().all()             # (b) no prediction without prior history
    assert oof.notna().any()                             # later months are predicted
