"""Trend-gated vol-targeted QQQ: Faber 200d gate x Moreira-Muir vol targeting, BIL when off."""
import json
from pathlib import Path

import numpy as np
import pandas as pd

P = json.loads((Path(__file__).parent / "params.json").read_text())
LEVERAGE_CAP = 2.0   # harness gross cap, not a tunable
HYSTERESIS = 0.01    # ponytail: fixed 1% band around the SMA, literature-free constant
TOL_BAND = 0.05      # ponytail: fixed no-trade band on weight changes


def target_weights(panel):
    close = panel["close"]["QQQ"]
    sma = close.rolling(P["sma_window"]).mean()
    rets = close.pct_change(fill_method=None)
    rv = rets.rolling(P["rv_lookback"]).std() * np.sqrt(252)
    raw_on = (P["sigma_target"] / rv).clip(upper=LEVERAGE_CAP)

    c, s, tgt = close.to_numpy(), sma.to_numpy(), raw_on.to_numpy()
    wq = np.zeros(len(c))
    wb = np.zeros(len(c))
    state = None  # unknown until SMA is valid
    cur_q = cur_b = 0.0
    for i in range(len(c)):  # ponytail: plain loop, ~1900 days, milliseconds
        if np.isnan(s[i]):
            continue
        if state is None:
            state = c[i] > s[i]
        elif state:
            if c[i] < s[i] * (1 - HYSTERESIS):
                state = False
        else:
            if c[i] > s[i] * (1 + HYSTERESIS):
                state = True
        if state and not np.isnan(tgt[i]):
            tq, tb = tgt[i], 0.0
        else:
            tq, tb = 0.0, 1.0
        if abs(tq - cur_q) > TOL_BAND or abs(tb - cur_b) > TOL_BAND:
            cur_q, cur_b = tq, tb
        wq[i], wb[i] = cur_q, cur_b

    return pd.DataFrame({"QQQ": wq, "BIL": wb}, index=close.index)
