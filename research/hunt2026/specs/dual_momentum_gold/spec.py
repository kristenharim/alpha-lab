"""Dual momentum with gold risk leg and momentum-picked defensive leg (Antonacci variant).

Monthly at the last close of each month: rank SPY/QQQ/GLD by trailing 252d total
return. If the winner beats BIL's 252d return (absolute-momentum gate), hold the
winner at 1.5x. Otherwise hold the better of TLT/BIL by 252d return at 1.0x —
defensive momentum, not hardcoded TLT, so a rising-rate bear doesn't force us
into a falling bond. Single position, ~12 trades/yr, ETF costs only.
"""
import json
from pathlib import Path

import pandas as pd

PARAMS = json.loads((Path(__file__).parent / "params.json").read_text())

RISK_MENU = ["SPY", "QQQ", "GLD"]
DEFENSIVE_MENU = ["TLT", "BIL"]


def target_weights(panel: pd.DataFrame) -> pd.DataFrame:
    lb = int(PARAMS["lookback"])
    risk_lev = float(PARAMS["risk_leverage"])
    def_lev = float(PARAMS["defensive_leverage"])

    cols = RISK_MENU + DEFENSIVE_MENU
    close = panel["close"][cols]
    idx = close.index

    # trailing total return over lb days, adjusted closes, info through close t
    mom = close / close.shift(lb) - 1.0

    # last trading day of each month = day whose successor is in a new month;
    # the panel's final date is never treated as a month-end (successor unknown)
    month_end = idx[:-1][idx[1:].month != idx[:-1].month]

    # ponytail: ~90 month-ends, plain loop is fast and readable
    rebal = pd.DataFrame(index=month_end, columns=cols, dtype=float)
    for t in month_end:
        m = mom.loc[t]
        row = pd.Series(0.0, index=cols)
        if not m.isna().any():
            best = m[RISK_MENU].idxmax()
            if m[best] > m["BIL"]:
                row[best] = risk_lev
            else:
                row[m[DEFENSIVE_MENU].idxmax()] = def_lev
        rebal.loc[t] = row

    # hold each month-end allocation until the next rebalance
    return rebal.reindex(idx).ffill().fillna(0.0)


if __name__ == "__main__":
    # self-check: gross <= 1.5 always, one position at a time, no ^VIX
    here = Path(__file__).parents[2]
    W = target_weights(pd.read_parquet(here / "train5y.parquet"))
    assert (W.abs().sum(axis=1) <= 1.5 + 1e-9).all()
    assert ((W != 0).sum(axis=1) <= 1).all()
    assert "^VIX" not in W.columns
    print("self-check OK")
