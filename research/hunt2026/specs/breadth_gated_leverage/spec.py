"""Breadth-gated leverage: RSP/SPY participation signal gates SPY exposure."""
import json
from pathlib import Path

import numpy as np
import pandas as pd

P = json.loads((Path(__file__).parent / "params.json").read_text())


def target_weights(panel):
    close = panel["close"]
    lb = int(P["breadth_lookback"])

    ratio = close["RSP"] / close["SPY"]
    breadth = ratio / ratio.shift(lb) - 1.0

    spy_ret = close["SPY"].pct_change(fill_method=None)
    rv21 = spy_ret.rolling(21).std() * np.sqrt(252)

    risk_off = (P["risk_off_vol_target"] / rv21).clip(upper=P["leverage_on"])
    w_spy = pd.Series(np.where(breadth > 0, P["leverage_on"], risk_off),
                      index=close.index)
    # no weight until both signals exist
    w_spy[breadth.isna() | rv21.isna()] = 0.0

    W = pd.DataFrame(0.0, index=close.index, columns=["SPY"])
    W["SPY"] = w_spy
    return W


if __name__ == "__main__":
    # self-check: gross never exceeds cap, no weight before warmup
    idx = pd.bdate_range("2020-01-01", periods=300)
    rng = np.random.default_rng(0)
    px = pd.DataFrame(100 * np.exp(np.cumsum(rng.normal(0, 0.01, (300, 2)), axis=0)),
                      index=idx, columns=["SPY", "RSP"])
    panel = pd.concat({"close": px}, axis=1)
    W = target_weights(panel)
    assert (W.abs().sum(axis=1) <= 2.0 + 1e-12).all()
    assert (W.iloc[:63].abs().sum(axis=1) == 0).all()
    print("self-check OK")
