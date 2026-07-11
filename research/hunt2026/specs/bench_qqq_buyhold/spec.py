"""BENCHMARK (not a trial): QQQ buy-and-hold at 1x. The naive base every QQQ spec must beat."""
import pandas as pd


def target_weights(panel):
    c = panel["close"]
    w = pd.DataFrame(0.0, index=c.index, columns=c.columns)
    w.loc[c["QQQ"].notna(), "QQQ"] = 1.0
    return w
