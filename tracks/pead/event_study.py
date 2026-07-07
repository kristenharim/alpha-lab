"""CARs around earnings events; drift spread between SUE quantiles."""
import numpy as np
import pandas as pd


def car_matrix(events: pd.DataFrame, returns: pd.DataFrame, market: pd.Series,
               window: tuple[int, int] = (-1, 60)) -> pd.DataFrame:
    lo, hi = window
    rel_days = list(range(lo, hi + 1))
    rows = []
    for _, ev in events.iterrows():
        t, d = ev["ticker"], pd.Timestamp(ev["date"])
        if t not in returns.columns:
            rows.append([np.nan] * len(rel_days))
            continue
        abnormal = (returns[t] - market).dropna()
        pos = abnormal.index.searchsorted(d)
        seg = []
        for k in rel_days:
            i = pos + k
            seg.append(abnormal.iloc[i] if 0 <= i < len(abnormal) else np.nan)
        rows.append(np.nancumsum(seg))
    return pd.DataFrame(rows, columns=rel_days, index=events.index)


def drift_spread(cars: pd.DataFrame, events: pd.DataFrame, q: int = 5) -> pd.Series:
    sue = events.loc[cars.index, "sue"]
    labels = pd.qcut(sue.rank(method="first"), q, labels=False)
    top = cars[labels == q - 1].mean()
    bot = cars[labels == 0].mean()
    return top - bot
