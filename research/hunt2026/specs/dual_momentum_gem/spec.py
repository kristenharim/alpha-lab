"""Levered dual momentum ETF rotation (Antonacci GEM adapted).

Monthly at the last close of each month: rank SPY/QQQ/EFA by trailing 12-month
total return. If the winner beats BIL's 12-month total return (absolute-momentum
gate), hold the winner at 1.5x; otherwise hold TLT at 1.0x. Weights held until
the next month-end. Single position, ~12 trades/yr, ETF costs only.
"""
import json
from pathlib import Path

import pandas as pd

PARAMS = json.loads((Path(__file__).parent / "params.json").read_text())

EQUITY_MENU = ["SPY", "QQQ", "EFA"]
CASH_PROXY = "BIL"
DEFENSIVE = "TLT"


def target_weights(panel: pd.DataFrame) -> pd.DataFrame:
    lb = int(PARAMS["lookback_days"])
    skip = int(PARAMS["skip_days"])
    lev = float(PARAMS["equity_leverage"])

    close = panel["close"][EQUITY_MENU + [CASH_PROXY, DEFENSIVE]]
    idx = close.index

    # total return over [t-lb, t-skip], from adjusted closes (no future info)
    mom = close.shift(skip) / close.shift(lb) - 1.0

    # last trading day of each month = day whose successor is in a new month;
    # the panel's final date is never treated as a month-end (its successor is unknown)
    month_end = idx[:-1][idx[1:].month != idx[:-1].month]

    W = pd.DataFrame(0.0, index=idx, columns=EQUITY_MENU + [DEFENSIVE])
    # ponytail: ~140 month-ends, plain loop is fast and readable
    rebal = pd.DataFrame(index=month_end, columns=W.columns, dtype=float)
    for t in month_end:
        m = mom.loc[t]
        row = pd.Series(0.0, index=W.columns)
        if not m.isna().any():
            best = m[EQUITY_MENU].idxmax()
            if m[best] > m[CASH_PROXY]:
                row[best] = lev
            else:
                row[DEFENSIVE] = 1.0
        rebal.loc[t] = row

    # hold each month-end allocation until the next rebalance
    W = rebal.reindex(idx).ffill().fillna(0.0)
    return W


if __name__ == "__main__":
    # self-check: gross <= 1.5 always, one position at a time, no ^VIX
    import sys
    sys.path.insert(0, str(Path(__file__).parents[2]))
    import harness
    W = target_weights(harness.load_train())
    assert (W.abs().sum(axis=1) <= 1.5 + 1e-9).all()
    assert ((W != 0).sum(axis=1) <= 1).all()
    assert "^VIX" not in W.columns
    print("self-check OK")
