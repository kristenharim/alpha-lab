"""vix_panic_buyer: 1.5x SPY base, add to 2.0x while VIX is in a relative spike.

Hold SPY at base_leverage continuously. Spike trigger at the close: VIX >=
spike_mult x its trailing 60d median. While triggered, hold 2.0x SPY; release
back to base_leverage when VIX < release_mult x its 60d median (hysteresis).
All in SPY at 2 bps/side; the only turnover is the 0.5x add/release, a few
times a year.
"""
import json
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).parent
PARAMS = json.loads((HERE / "params.json").read_text())

MEDIAN_WINDOW = 60  # trading days; structural, not tuned


def target_weights(panel):
    spike = float(PARAMS["spike_mult"])
    release = float(PARAMS["release_mult"])
    base = float(PARAMS["base_leverage"])

    vix = panel["close"]["^VIX"]
    med = vix.rolling(MEDIAN_WINDOW, min_periods=MEDIAN_WINDOW).median()
    ratio = (vix / med).to_numpy()

    # hysteresis state machine: on at >= spike, off at < release
    n = len(ratio)
    lev = np.full(n, base)
    on = False
    for t in range(n):
        r = ratio[t]
        if not np.isnan(r):
            if not on and r >= spike:
                on = True
            elif on and r < release:
                on = False
        if on:
            lev[t] = 2.0

    close = panel["close"]
    W = pd.DataFrame(0.0, index=close.index, columns=close.columns)
    W["SPY"] = np.where(close["SPY"].notna().to_numpy(), lev, 0.0)
    return W
