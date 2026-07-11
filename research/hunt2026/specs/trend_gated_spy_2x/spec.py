"""Trend-gated 2x SPY (Gayed-Bilello 'Leverage for the Long Run').

Risk-on (2x SPY) when SPY close is above its 200d SMA by more than the
hysteresis band; risk-off (1x BIL) when below by more than the band;
hold prior state inside the band. BIL over SHY: no duration risk wanted.
"""
import json
from pathlib import Path

import pandas as pd

PARAMS = json.loads((Path(__file__).parent / "params.json").read_text())


def target_weights(panel: pd.DataFrame) -> pd.DataFrame:
    n, b, lev = PARAMS["sma_window"], PARAMS["band"], PARAMS["leverage"]
    spy = panel["close"]["SPY"]
    sma = spy.rolling(n).mean()

    # hysteresis state machine, vectorized: 1 above upper band, 0 below lower,
    # carry previous state inside the band
    state = pd.Series(float("nan"), index=spy.index)
    state[spy > sma * (1 + b)] = 1.0
    state[spy < sma * (1 - b)] = 0.0
    state = state.ffill()
    state[sma.isna()] = float("nan")  # no signal until SMA warm-up
    state = state.fillna(0.0)  # warm-up: flat (weight 0, no BIL either)

    valid = sma.notna()
    W = pd.DataFrame(0.0, index=spy.index, columns=["SPY", "BIL"])
    W["SPY"] = lev * state
    W["BIL"] = 1.0 * (1.0 - state) * valid  # risk-off leg only once signal live
    return W


if __name__ == "__main__":
    # self-check: hysteresis holds state inside the band
    idx = pd.date_range("2020-01-01", periods=300)
    px = pd.Series(100.0, index=idx)
    px.iloc[250:] = 103.0  # +3% pop above flat SMA -> risk-on
    panel = pd.concat({"close": pd.DataFrame({"SPY": px, "BIL": 100.0})}, axis=1)
    w = target_weights(panel)
    assert (w["SPY"].iloc[:199] == 0).all()          # warm-up flat
    assert w["SPY"].iloc[220] == 0 and w["BIL"].iloc[220] == 1.0  # at SMA: inside band -> off
    assert w["SPY"].iloc[-1] == PARAMS["leverage"] and w["BIL"].iloc[-1] == 0.0
    assert (w.abs().sum(axis=1) <= 2.0 + 1e-12).all()
    print("self-check OK")
