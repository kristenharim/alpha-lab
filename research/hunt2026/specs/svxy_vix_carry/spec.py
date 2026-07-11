"""svxy_vix_carry: VIX-gated short-vol carry. ON = 0.5 SVXY + 0.5 SPY, OFF = 1.0 BIL.

Risk-ON at close t iff VIX_t < vix_ceiling AND VIX_t > rv_mult * 10d realized SPY vol
(annualized, in VIX points). All info through close t; harness lags one day.
"""
import json
from pathlib import Path

import numpy as np
import pandas as pd

PARAMS = json.loads((Path(__file__).parent / "params.json").read_text())


def target_weights(panel):
    close = panel["close"]
    vix = close["^VIX"]
    spy_ret = close["SPY"].pct_change()
    # trailing 10d realized vol, annualized, in VIX points (x100)
    rv = spy_ret.rolling(10).std() * np.sqrt(252) * 100.0  # 10d window fixed by construction
    on = (vix < PARAMS["vix_ceiling"]) & (vix > PARAMS["rv_mult"] * rv)

    W = pd.DataFrame(0.0, index=close.index, columns=["SVXY", "SPY", "BIL"])
    w = PARAMS["svxy_weight"]
    W.loc[on, "SVXY"] = w
    W.loc[on, "SPY"] = 1.0 - w
    W.loc[~on, "BIL"] = 1.0
    return W  # gross always exactly 1.0
