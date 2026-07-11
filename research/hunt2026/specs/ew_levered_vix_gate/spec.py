"""ew_levered_vix_gate: 2x equal-weight S&P 500 with a VIX tail gate.

Hold every current S&P 500 member (PIT mask, stocks only) equal-weight at
leverage L. L = 2.0 while VIX < gate; L = 1.0 while VIX >= gate; re-enter 2.0
after `reentry_days` consecutive closes back under the gate (hysteresis).
Weights drift with returns between trades; a name is traded back to target
only when its weight drifts more than `band` relative from target
(Garleanu-Pedersen no-trade band), plus membership adds/drops and gate flips.
"""
import json
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).parent
PARAMS = json.loads((HERE / "params.json").read_text())
META = json.loads((HERE.parent.parent / "sandbox_meta.json").read_text())


def target_weights(panel):
    gate = float(PARAMS["vix_gate"])
    reentry = int(PARAMS["reentry_days"])
    band = float(PARAMS["band"])

    excl = set(META["etfs"]) | set(META["signal_only"])
    tickers = [t for t in panel["close"].columns if t not in excl]
    close = panel["close"][tickers]
    member = (panel["member"][tickers].fillna(0.0).to_numpy() > 0.5)
    valid = close.notna().to_numpy()
    rets = close.pct_change(fill_method=None).to_numpy()
    vix = panel["close"]["^VIX"].to_numpy()

    n_days, n_tk = member.shape
    W = np.zeros((n_days, n_tk))
    w = np.zeros(n_tk)
    lev = 1.0 if (not np.isnan(vix[0]) and vix[0] >= gate) else 2.0
    below = 0
    prev_univ = np.zeros(n_tk, dtype=bool)

    for t in range(n_days):
        univ = member[t] & valid[t]
        # drift held weights with today's close-to-close returns
        r = np.nan_to_num(rets[t])
        denom = 1.0 + float(w @ r)
        if denom > 0.05:  # guard against degenerate NAV; never triggers on daily data
            w = w * (1.0 + r) / denom

        # gate state machine on today's VIX close (info through the close only)
        new_lev = lev
        v = vix[t]
        if not np.isnan(v):
            if lev == 2.0:
                if v >= gate:
                    new_lev = 1.0
                    below = 0
            else:
                if v < gate:
                    below += 1
                    if below >= reentry:
                        new_lev = 2.0
                else:
                    below = 0

        n = int(univ.sum())
        if n == 0:
            w = np.zeros(n_tk)
            W[t] = w
            prev_univ = univ
            continue
        target = new_lev / n

        if new_lev != lev:
            # gate flip: full re-equalization at the new leverage
            w = np.where(univ, target, 0.0)
            lev = new_lev
        else:
            w[~univ] = 0.0                      # membership drops
            w[univ & ~prev_univ] = target       # membership adds
            idx = np.where(univ)[0]             # no-trade band per name
            breach = np.abs(w[idx] / target - 1.0) > band
            w[idx[breach]] = target
        prev_univ = univ

        # hard gross cap (levered book drifts above 2.0 on down days)
        g = float(np.abs(w).sum())
        if g > 2.0:
            w = w * (2.0 / g)
        W[t] = w

    return pd.DataFrame(W, index=close.index, columns=tickers)
