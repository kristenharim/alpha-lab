"""gap_drift — price/volume PEAD proxy, concentrated long, 1.5x gross.

Event day t: 1d return >= z_thresh trailing-60d sigmas AND volume >= vol_mult x
trailing-20d median volume, on PIT S&P 500 members. Enter close t+1, hold `hold`
trading days, equal-weight, 5% per-name cap, idle capital in SPY, book at 1.5x.
"""
import json
from pathlib import Path

import numpy as np
import pandas as pd

P = json.loads((Path(__file__).parent / "params.json").read_text())

GROSS = 1.5          # book scale (design constant, not a tunable)
NAME_CAP = 0.05      # per-name cap as fraction of NAV (pre-scale)
# ponytail: universe facts hardcoded from sandbox_meta.json (frozen sandbox)
NON_STOCKS = {
    "SPY", "QQQ", "IWM", "DIA", "MDY", "EFA", "EEM", "VGK", "EWJ", "TLT",
    "IEF", "SHY", "BIL", "LQD", "HYG", "TIP", "GLD", "SLV", "DBC", "USO",
    "UNG", "VNQ", "UUP", "FXE", "XLB", "XLE", "XLF", "XLI", "XLK", "XLP",
    "XLU", "XLV", "XLY", "XLRE", "XLC", "RSP", "SVXY", "^VIX",
}


def target_weights(panel):
    close = panel["close"]
    volume = panel["volume"]
    member = panel["member"].fillna(0.0)

    stocks = [t for t in close.columns if t not in NON_STOCKS]
    c, v, m = close[stocks], volume[stocks], member[stocks]

    rets = c.pct_change(fill_method=None)
    sigma = rets.rolling(60, min_periods=60).std().shift(1)   # trailing, ex event day
    z = rets / sigma
    med_vol = v.rolling(20, min_periods=20).median().shift(1)  # trailing 20d median

    event = (z >= P["z_thresh"]) & (v >= P["vol_mult"] * med_vol) & (m > 0)

    # enter close t+1, active for `hold` trading days (closes t+1 .. t+hold)
    active = event.shift(1, fill_value=False).rolling(P["hold"], min_periods=1).max() > 0
    active &= c.notna()  # drop names with no price (delisted mid-hold)

    n = active.sum(axis=1)
    per_name = np.minimum(1.0 / n.replace(0, np.nan), NAME_CAP)  # NaN when n == 0
    W = active.astype(float).mul(per_name.fillna(0.0), axis=0) * GROSS

    out = pd.DataFrame(0.0, index=close.index, columns=close.columns)
    out[stocks] = W
    out["SPY"] = GROSS - W.sum(axis=1)  # idle capital parked in SPY; gross == 1.5 always
    return out
