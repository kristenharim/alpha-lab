"""BENCHMARK (not a trial): naive Faber trend gate on QQQ at 2x, no vol targeting.
Isolates the gate component of trend_vol_qqq (vol_managed_qqq isolates the other)."""
import pandas as pd


def target_weights(panel):
    c = panel["close"]
    qqq, bil = c["QQQ"], c["BIL"]
    sma = qqq.rolling(200).mean()
    on = (qqq > sma) & sma.notna()
    w = pd.DataFrame(0.0, index=c.index, columns=c.columns)
    w.loc[on & qqq.notna(), "QQQ"] = 2.0
    w.loc[~on & sma.notna() & bil.notna(), "BIL"] = 1.0
    return w
