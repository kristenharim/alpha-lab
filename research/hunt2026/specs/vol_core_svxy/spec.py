"""vol_core_svxy — vol-managed QQQ+SPY core with VIX-gated SVXY carry sleeve.

Core: 60/40 QQQ/SPY, each scaled to a constant-vol target (sigma_target / rv21,
leverage capped at 2x per leg). Sleeve: hold svxy_weight in SVXY only when VIX
closes below its own rolling vix_gate_window-day median (calm/contango regimes).
Gross scaled down proportionally to <= 2.0. ^VIX is signal-only, never held.
"""
import json
from pathlib import Path

import numpy as np
import pandas as pd

PARAMS = json.loads((Path(__file__).parent / "params.json").read_text())

MAX_GROSS = 2.0
LEG_LEV_CAP = 2.0
CORE_SPLIT = {"QQQ": 0.6, "SPY": 0.4}


def target_weights(panel: pd.DataFrame) -> pd.DataFrame:
    close = panel["close"]
    sigma = PARAMS["sigma_target"]

    W = pd.DataFrame(0.0, index=close.index, columns=["QQQ", "SPY", "SVXY"])

    # core: constant-vol scaled QQQ/SPY
    for tkr, split in CORE_SPLIT.items():
        rets = close[tkr].pct_change()
        rv21 = rets.rolling(21).std() * np.sqrt(252)
        W[tkr] = split * (sigma / rv21).clip(upper=LEG_LEV_CAP)

    # sleeve: SVXY only in calm regimes (VIX below its rolling median)
    vix = close["^VIX"]
    gate = vix < vix.rolling(PARAMS["vix_gate_window"]).median()
    W["SVXY"] = np.where(gate & close["SVXY"].notna(), PARAMS["svxy_weight"], 0.0)

    W = W.fillna(0.0)
    gross = W.abs().sum(axis=1)
    W = W.mul((MAX_GROSS / gross).clip(upper=1.0).fillna(1.0), axis=0)
    return W


if __name__ == "__main__":
    # ponytail: minimal self-check — gross cap and no ^VIX weight
    import sys
    sys.path.insert(0, str(Path(__file__).parents[2]))
    import harness
    W = target_weights(harness.load_train())
    assert (W.abs().sum(axis=1) <= MAX_GROSS + 1e-9).all()
    assert "^VIX" not in W.columns
    print("self-check OK", W.abs().sum(axis=1).max())
