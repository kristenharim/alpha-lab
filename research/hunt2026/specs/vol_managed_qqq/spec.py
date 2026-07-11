"""Vol-managed levered QQQ (Moreira-Muir vol timing) with a no-trade tolerance band."""
import json
from pathlib import Path

import numpy as np
import pandas as pd

P = json.loads((Path(__file__).parent / "params.json").read_text())
LEVERAGE_CAP = 2.0  # harness gross cap, not a tunable


def target_weights(panel):
    close = panel["close"]["QQQ"]
    rets = close.pct_change(fill_method=None)
    rv = rets.rolling(P["vol_lookback"]).std() * np.sqrt(252)
    raw = (P["sigma_target"] / rv).clip(upper=LEVERAGE_CAP).fillna(0.0).to_numpy()

    # tolerance band: hold current weight until target drifts > band away
    band = P["tolerance_band"]
    w = np.empty_like(raw)
    cur = 0.0
    for i, tgt in enumerate(raw):  # ponytail: plain loop, ~3k days, milliseconds
        if abs(tgt - cur) > band:
            cur = tgt
        w[i] = cur

    return pd.DataFrame({"QQQ": w}, index=close.index)
