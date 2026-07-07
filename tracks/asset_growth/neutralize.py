"""Cross-sectional size/sector neutralization.

The asset-growth anomaly is partly a size bet (fast-growing firms cluster by size)
and can tilt sectors. Neutralizing residualizes the score each month against
log-size and sector dummies, so the long-short is orthogonal to both — isolating
the PURE asset-growth effect rather than an accidental size/sector tilt.
"""
import numpy as np
import pandas as pd


def neutralize_score(score: pd.DataFrame, size: pd.DataFrame, sectors: dict,
                     min_names: int = 10) -> pd.DataFrame:
    """Per-month OLS residual of score ~ log(size) + C(sector).

    score, size: date x ticker (size in levels, e.g. total assets — logged inside).
    sectors: ticker -> sector label. Rows with < min_names valid names are dropped.
    """
    sec = pd.Series(sectors)
    rows = {}
    for date, srow in score.iterrows():
        s = srow.dropna()
        if date not in size.index:
            continue
        sz = size.loc[date].reindex(s.index)
        valid = s.index[sz.notna() & (sz > 0)]
        if len(valid) < min_names:
            continue
        y = s[valid].to_numpy(dtype=float)
        logsz = np.log(sz[valid].to_numpy(dtype=float))
        secs = sec.reindex(valid).fillna("Unknown")
        dummies = pd.get_dummies(secs, drop_first=True).to_numpy(dtype=float)
        cols = [np.ones(len(valid)), logsz]
        if dummies.size:
            cols.append(dummies)
        X = np.column_stack(cols)
        beta, *_ = np.linalg.lstsq(X, y, rcond=None)
        rows[date] = pd.Series(y - X @ beta, index=valid)
    if not rows:
        return pd.DataFrame(columns=score.columns)
    return pd.DataFrame(rows).T.reindex(columns=score.columns)
