import numpy as np
import pandas as pd
from tracks.pead.events import surprise_score
from tracks.pead.event_study import car_matrix, drift_spread


def test_surprise_score():
    ev = pd.DataFrame({"ticker": ["A", "B"], "date": ["2024-02-01", "2024-02-01"],
                       "eps_actual": [1.2, 0.8], "eps_estimate": [1.0, 1.0]})
    out = surprise_score(ev)
    assert np.isclose(out.loc[0, "sue"], 0.2) and np.isclose(out.loc[1, "sue"], -0.2)


def test_car_matrix_and_drift():
    idx = pd.date_range("2024-01-01", periods=90, freq="B")
    rng = np.random.default_rng(0)
    rets = pd.DataFrame(rng.normal(0, 0.001, (90, 2)), index=idx, columns=["A", "B"])
    rets.loc[idx[10]:, "A"] += 0.002   # A drifts up after its event
    market = pd.Series(0.0, index=idx)
    ev = surprise_score(pd.DataFrame({"ticker": ["A", "B"], "date": [idx[10], idx[10]],
                                      "eps_actual": [1.5, 0.5], "eps_estimate": [1.0, 1.0]}))
    cars = car_matrix(ev, rets, market, window=(-1, 30))
    assert cars.shape[0] == 2 and 30 in cars.columns
    spread = drift_spread(cars, ev, q=2)
    assert spread.iloc[-1] > 0  # positive-surprise A drifted above B
