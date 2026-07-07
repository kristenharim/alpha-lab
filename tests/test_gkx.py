import numpy as np
import pandas as pd
import pytest
from tracks.gkx.cz_data import validate_panel, load_cz_long_short
from tracks.gkx.models import expanding_window_predict


def _panel(n_signals=4, n_months=60, seed=3):
    rng = np.random.default_rng(seed)
    dates = pd.period_range("2015-01", periods=n_months, freq="M").to_timestamp()
    rows = [{"date": d, "signalname": f"s{i}", "ret": rng.normal(0.005 * (i % 2), 0.02)}
            for d in dates for i in range(n_signals)]
    return pd.DataFrame(rows)


def test_validate_panel_rejects_missing_cols():
    with pytest.raises(ValueError):
        validate_panel(pd.DataFrame({"a": [1]}))


def test_validate_panel_renames_signal_id():
    df = pd.DataFrame({"date": ["2015-01-01"], "signal_id": ["s0"], "ret": [0.01]})
    out = validate_panel(df)
    assert "signalname" in out.columns


def test_expanding_window_shapes_and_no_lookahead():
    preds = expanding_window_predict(_panel(), model="ridge", min_train_months=24)
    assert {"date", "signal", "y_true", "y_pred"} <= set(preds.columns)
    assert preds["date"].min() > pd.Timestamp("2016-12-01")  # first 24m reserved for training


def test_load_cz_long_short(tmp_path):
    # mimic CZ decile format: two signals, 3 months, deciles 01/10 + LS, ret in percent
    rows = []
    for d in pd.date_range("2015-01-31", periods=3, freq="ME"):
        for sig in ("s0", "s1"):
            for port, ret in [("01", 1.0), ("10", 2.0), ("LS", 1.5)]:
                rows.append({"signalname": sig, "port": port, "date": d, "ret": ret})
    path = tmp_path / "cz.parquet"
    pd.DataFrame(rows).to_parquet(path)
    out = load_cz_long_short(path)
    assert set(out.columns) >= {"signalname", "date", "ret"}
    assert (out["ret"] == 0.015).all()          # only LS rows, percent -> decimal
    assert len(out) == 6                          # 2 signals x 3 months
