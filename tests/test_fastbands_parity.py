"""The C++ band_positions must be EXACTLY the pure-Python state machine — same ints,
every path. Positions are discrete state, so parity is exact, not approximate."""
import numpy as np
import pandas as pd
import pytest

from core.backtest import _fastbands  # skip if not built
from tracks.statarb.bands import band_positions as fast  # C++ path (extension present)


def _py(series, entry=2.0, exit_=0.5, long_floor=None):
    """Reference pure-Python implementation, frozen here as the oracle."""
    pos = 0
    out = []
    for v in series:
        if pd.isna(v):
            out.append(pos)
            continue
        too_deep = long_floor is not None and v < -long_floor
        if pos == 0:
            if v <= -entry and not too_deep:
                pos = 1
            elif v >= entry:
                pos = -1
        elif pos == 1 and too_deep:
            pos = 0
        elif abs(v) <= exit_:
            pos = 0
        out.append(pos)
    return pd.Series(out, index=series.index)


EDGE_CASES = [
    [],                                   # empty
    [0.0],                                # single flat
    [np.nan, np.nan, 3.0, np.nan, 0.0],   # leading/embedded NaN
    [-3, -3, -0.1, 3, 0.0, -3],           # long -> exit -> short -> exit -> long
    [2, 2, 2, 2],                         # sustained short, never exits
    [-2, -2, -2, -2],                     # sustained long, never exits
    [-1.5, -3.0, -1.0, -0.1],             # knife: enter shallow then plunge (with floor)
]


@pytest.mark.parametrize("vals", EDGE_CASES)
@pytest.mark.parametrize("long_floor", [None, 2.5])
def test_edge_cases(vals, long_floor):
    s = pd.Series(vals, dtype=float)
    got = fast(s, entry=1.25, exit_=0.5, long_floor=long_floor)
    exp = _py(s, entry=1.25, exit_=0.5, long_floor=long_floor)
    assert got.tolist() == exp.tolist()
    assert list(got.index) == list(exp.index)


@pytest.mark.parametrize("seed", range(25))
def test_random_panels(seed):
    rng = np.random.default_rng(seed)
    vals = rng.standard_normal(2000) * 2.0
    vals[rng.random(2000) < 0.03] = np.nan          # sprinkle NaNs
    idx = pd.date_range("2015-01-01", periods=2000, freq="B")
    s = pd.Series(vals, index=idx)
    for lf in (None, 1.5, 3.0):
        got = fast(s, entry=2.0, exit_=0.5, long_floor=lf)
        exp = _py(s, entry=2.0, exit_=0.5, long_floor=lf)
        assert got.tolist() == exp.tolist(), f"mismatch seed={seed} long_floor={lf}"
