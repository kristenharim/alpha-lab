"""Time-series momentum across asset classes (Moskowitz-Ooi-Pedersen 2012), ETF version.

Monthly on the first trading day: for each of 15 liquid ETFs spanning equities,
bonds, credit, commodities, FX, and REITs, go long (short) if its trailing 252d
total return is positive (negative). Position sizes are inverse-63d-vol weighted,
then the whole book is scaled so trailing 63d realized portfolio vol targets 15%
annualized, gross capped at 2.0. All parameters are MOP 2012 literature defaults;
nothing is fit to this panel.
"""
import json
from pathlib import Path

import numpy as np
import pandas as pd

PARAMS = json.loads((Path(__file__).parent / "params.json").read_text())

MENU = ["SPY", "QQQ", "IWM", "EFA", "EEM", "TLT", "IEF", "GLD", "SLV",
        "DBC", "USO", "UUP", "HYG", "LQD", "VNQ"]
VOL_WINDOW = 63          # MOP use ex-ante vol; 3 months is the standard proxy
VOL_FLOOR = 0.05


def target_weights(panel: pd.DataFrame) -> pd.DataFrame:
    lb = int(PARAMS["lookback"])
    vt = float(PARAMS["vol_target"])
    cap = float(PARAMS["gross_cap"])

    close = panel["close"][MENU]
    idx = close.index
    ret = close.pct_change(fill_method=None)

    sign = np.sign(close / close.shift(lb) - 1.0)
    sigma = (ret.rolling(VOL_WINDOW).std() * np.sqrt(252)).clip(lower=VOL_FLOOR)
    inv = 1.0 / sigma
    raw = sign * inv.div(inv.sum(axis=1), axis=0)   # sum|w| = 1 by construction

    # first trading day of each month (skip the panel's first date: no lookback yet)
    rebal = idx[1:][idx[1:].month != idx[:-1].month]

    W = raw.reindex(rebal)
    # portfolio vol proxy: today's weights held constant over the trailing window
    pvol = pd.Series(
        [(ret.loc[:t].iloc[-VOL_WINDOW:] * W.loc[t]).sum(axis=1).std() * np.sqrt(252)
         for t in rebal], index=rebal)
    scale = (vt / pvol).clip(upper=cap).where(pvol > 0, 0.0)
    W = W.mul(scale, axis=0).fillna(0.0)

    return W.reindex(idx).ffill().fillna(0.0)


if __name__ == "__main__":
    # self-check: gross <= 2.0, monthly turnover only, no ^VIX
    import sys
    sys.path.insert(0, str(Path(__file__).parents[2]))
    import harness
    panel = pd.read_parquet(Path(__file__).parents[2] / "train5y.parquet")
    W = target_weights(panel)
    assert (W.abs().sum(axis=1) <= 2.0 + 1e-9).all()
    assert (W.diff().abs().sum(axis=1) > 1e-12).sum() < 100  # ~monthly rebalance
    r = harness.run(sys.modules[__name__], panel, start="2018-07-10")
    print({k: round(v, 4) for k, v in r.items() if isinstance(v, float)})
