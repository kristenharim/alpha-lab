"""Levered long-only PCA min-var, RAW leading eigenvector (control leg).

Monthly at the first close of each month: estimate a 1-factor covariance model
Sigma = lam1 v v' + delta2 I from the trailing 252 days of demeaned returns,
with v = the RAW sample leading eigenvector (no dispersion-bias correction —
this is the control leg of the Goldberg et al. matched pair). Min-var weights
via Sherman-Morrison, long-only clipped, 2% name cap, levered 2x.
"""
import json
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).parent
PARAMS = json.loads((HERE / "params.json").read_text())
META = json.loads((HERE.parents[1] / "sandbox_meta.json").read_text())
EXCLUDE = set(META["etfs"]) | set(META.get("signal_only", ["^VIX"]))


def _minvar_weights(Y, cap, lev):
    """Long-only levered min-var from Sigma = lam1 v v' + delta2 I, v = raw h."""
    p, n = Y.shape
    U, s, _ = np.linalg.svd(Y, full_matrices=False)
    h = U[:, 0]
    lam1 = s[0] ** 2 / n
    delta2 = (s[1:] ** 2).sum() / ((p - 1) * n)
    # step 5: NO correction — v is the raw sample eigenvector
    v = h
    # Sherman-Morrison: Sigma^{-1} 1 ∝ 1 - lam1 (v'1)/(delta2 + lam1) v  (||v||=1)
    w = 1.0 - (lam1 * v.sum() / (delta2 + lam1)) * v
    w = np.clip(w, 0.0, None)
    w /= w.sum()
    w = np.minimum(w, cap)
    w /= w.sum()
    return w * lev


def target_weights(panel: pd.DataFrame) -> pd.DataFrame:
    window = int(PARAMS["window"])
    lev = float(PARAMS["leverage"])
    cap = 0.02

    close = panel["close"]
    stocks = [t for t in close.columns if t not in EXCLUDE]
    close = close[stocks]
    member = panel["member"][stocks]
    idx = close.index

    # first trading day of each month
    rebal_dates = idx[1:][idx[1:].month != idx[:-1].month]

    logc = np.log(close.to_numpy())
    pos = {d: i for i, d in enumerate(idx)}

    rows = {}
    for t in rebal_dates:
        i = pos[t]
        if i < window:  # need window+1 closes for window returns
            continue
        # trailing window: closes over [i-window, i], returns n = window days
        win = logc[i - window:i + 1]
        ok = ~np.isnan(win).any(axis=0)
        ok &= member.loc[t].to_numpy() == 1.0
        if ok.sum() < 2:
            continue
        R = np.diff(win[:, ok], axis=0).T  # p x n, log returns ≈ daily returns
        Y = R - R.mean(axis=1, keepdims=True)
        w = _minvar_weights(Y, cap, lev)
        row = np.zeros(len(stocks))
        row[ok] = w
        rows[t] = row

    rebal = pd.DataFrame.from_dict(rows, orient="index", columns=stocks)
    W = rebal.reindex(idx).ffill().fillna(0.0)
    return W


if __name__ == "__main__":
    # self-check: gross == 2.0 on live days, long-only, no ETFs/^VIX, cap ~respected
    import sys
    sys.path.insert(0, str(Path(__file__).parents[2]))
    import harness
    W = target_weights(harness.load_train())
    g = W.abs().sum(axis=1)
    live = g > 0
    assert (g[live].sub(2.0).abs() < 1e-9).all(), g[live].describe()
    assert (W.to_numpy() >= 0).all()
    assert not (set(W.columns) & EXCLUDE)
    assert W[live.values].to_numpy().max() <= 0.045  # cap 2% x lev, small renorm slack
    print("self-check OK")
