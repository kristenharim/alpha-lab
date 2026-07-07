import numpy as np
import pandas as pd
from tracks.asset_growth.neutralize import neutralize_score


def test_neutralize_removes_size_and_sector_effect():
    # Build a score that is PURE size + sector effect (no idiosyncratic signal).
    # After neutralization the residual should be ~0 for every name.
    rng = np.random.default_rng(0)
    names = [f"T{i}" for i in range(40)]
    sectors = {n: ("Tech" if i % 2 == 0 else "Fin") for i, n in enumerate(names)}
    assets = pd.Series(rng.uniform(1e8, 1e11, 40), index=names)
    sector_effect = pd.Series([1.0 if sectors[n] == "Tech" else -1.0 for n in names], index=names)
    # score = 0.5*log(assets) + 2*sector_effect  (deterministic in size+sector)
    raw = 0.5 * np.log(assets) + 2 * sector_effect
    date = pd.Timestamp("2022-06-30")
    score = pd.DataFrame([raw.values], index=[date], columns=names)
    size = pd.DataFrame([assets.values], index=[date], columns=names)
    neut = neutralize_score(score, size, sectors)
    assert np.allclose(neut.loc[date].values, 0.0, atol=1e-6)


def test_neutralize_keeps_idiosyncratic_signal_and_orthogonal_to_size():
    rng = np.random.default_rng(1)
    names = [f"T{i}" for i in range(60)]
    sectors = {n: ("A" if i < 30 else "B") for i, n in enumerate(names)}
    assets = pd.Series(rng.uniform(1e8, 1e11, 60), index=names)
    idio = pd.Series(rng.normal(0, 1, 60), index=names)
    raw = 0.3 * np.log(assets) + idio  # size tilt + real signal
    date = pd.Timestamp("2022-06-30")
    score = pd.DataFrame([raw.values], index=[date], columns=names)
    size = pd.DataFrame([assets.values], index=[date], columns=names)
    neut = neutralize_score(score, size, sectors).loc[date]
    # residual should be ~uncorrelated with log-size...
    assert abs(np.corrcoef(neut.values, np.log(assets.values))[0, 1]) < 0.15
    # ...and still correlated with the idiosyncratic signal it should preserve
    assert np.corrcoef(neut.values, idio.values)[0, 1] > 0.8


def test_neutralize_skips_thin_rows():
    # a row with too few names is dropped (can't fit a stable cross-sectional reg)
    names = ["A", "B", "C"]
    sectors = {"A": "X", "B": "Y", "C": "Z"}
    date = pd.Timestamp("2022-06-30")
    score = pd.DataFrame([[1.0, 2.0, 3.0]], index=[date], columns=names)
    size = pd.DataFrame([[1e9, 2e9, 3e9]], index=[date], columns=names)
    neut = neutralize_score(score, size, sectors, min_names=10)
    assert neut.empty or neut.loc[date].isna().all()
