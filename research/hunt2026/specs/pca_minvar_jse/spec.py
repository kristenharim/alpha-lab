"""PCA min-var with the JSE dispersion-bias correction (GPS line): monthly, trailing-252d
demeaned returns, top-1 SVD, leading eigenvector rotated toward equal-weight to the
corrected angle (h = psi*b + noise, so the sample angle to q = 1/sqrt(p) is too wide),
Sherman-Morrison min-var weights, long-only, 2% cap, 2x leverage.
Matched control: specs/pca_minvar_raw (identical except the correction)."""
import json
from pathlib import Path

import numpy as np
import pandas as pd

P = json.loads((Path(__file__).parent / "params.json").read_text())
TAU = 0.01  # floor on psi^2 (weak-factor guard, factor_lab convention)

# non-stock tickers, never in the universe (from sandbox_meta.json, frozen)
_EXCLUDE = {
    "SPY", "QQQ", "IWM", "DIA", "MDY", "EFA", "EEM", "VGK", "EWJ", "TLT", "IEF",
    "SHY", "BIL", "LQD", "HYG", "TIP", "GLD", "SLV", "DBC", "USO", "UNG", "VNQ",
    "UUP", "FXE", "XLB", "XLE", "XLF", "XLI", "XLK", "XLP", "XLU", "XLV", "XLY",
    "XLRE", "XLC", "RSP", "SVXY", "^VIX",
}
NAME_CAP = 0.02


def _minvar_row(Y):
    """Y: (p x n) demeaned return matrix -> long-only capped weights (sum 1) or None."""
    p, n = Y.shape
    U, sv, _ = np.linalg.svd(Y, full_matrices=False)
    h, sigma1 = U[:, 0], sv[0]
    if h.sum() < 0:  # SVD sign is arbitrary; market factor aligns with equal-weight
        h = -h
    delta2 = (np.sum(Y * Y) - sigma1**2) / ((p - 1) * n)

    # JSE correction: psi2 = max(tau, 1 - p*delta2/sigma1^2); rotate h toward q
    psi2 = max(TAU, 1.0 - p * delta2 / sigma1**2)
    q = np.full(p, 1.0 / np.sqrt(p))
    hq = float(h @ q)
    c_true = min(1.0, hq / np.sqrt(psi2))
    resid = h - hq * q
    rn = np.linalg.norm(resid)
    v = q if rn < 1e-12 else c_true * q + np.sqrt(max(0.0, 1.0 - c_true**2)) * (resid / rn)

    # Sigma = lam1 v v' + delta2 I; Sherman-Morrison closed form for Sigma^{-1} 1
    lam1 = sigma1**2 / n
    ones = np.ones(p)
    w = ones / delta2 - (lam1 * float(v @ ones) / (delta2 * (delta2 + lam1))) * v

    w = np.clip(w, 0.0, None)
    if w.sum() <= 0:
        return None
    w /= w.sum()
    w = np.minimum(w, NAME_CAP)
    return w / w.sum()


def target_weights(panel):
    close = panel["close"]
    member = panel["member"].fillna(0.0)
    window, lev = int(P["window"]), float(P["leverage"])

    stocks = [t for t in close.columns if t not in _EXCLUDE]
    c = close[stocks]
    rets = c.pct_change(fill_method=None)
    idx = close.index

    # first trading day of each month, with a full return window behind it
    firsts = pd.Series(idx, index=idx).groupby(idx.to_period("M")).first()
    pos = {d: i for i, d in enumerate(idx)}

    snap_dates, snap_rows = [], []
    for d in firsts:
        i = pos[d]
        if i < window:
            continue
        win = rets.iloc[i - window + 1: i + 1]  # trailing 252 return days incl. d
        elig = (member.loc[d, stocks] > 0) & win.notna().all()
        names = elig.index[elig]
        if len(names) < 100:  # ponytail: degenerate universe -> skip, hold prior book
            continue
        Y = win[names].to_numpy().T
        Y = Y - Y.mean(axis=1, keepdims=True)
        w = _minvar_row(Y)
        if w is None:
            continue
        snap_dates.append(d)
        snap_rows.append(pd.Series(lev * w, index=names))

    if not snap_dates:
        return pd.DataFrame(0.0, index=idx, columns=stocks[:1])
    W = pd.DataFrame(snap_rows, index=pd.DatetimeIndex(snap_dates)).fillna(0.0)
    return W.reindex(idx).ffill().fillna(0.0)


if __name__ == "__main__":
    # self-check: warmup empty, gross == 2 after warmup, long-only, cap ~2%, no ETF/VIX
    rng = np.random.default_rng(0)
    nn, t = 150, 800
    idx = pd.bdate_range("2018-01-01", periods=t)
    names = [f"S{i}" for i in range(nn)] + ["SPY", "^VIX"]
    mkt = rng.normal(0.0003, 0.01, t)
    px = pd.DataFrame(
        100 * np.exp(np.cumsum(mkt[:, None] + rng.normal(0, 0.015, (t, nn + 2)), 0)),
        index=idx, columns=names)
    panel = pd.concat({"close": px, "member": pd.DataFrame(1.0, index=idx, columns=names)}, axis=1)
    W = target_weights(panel)
    assert "SPY" not in W.columns and "^VIX" not in W.columns
    assert (W.iloc[:252].abs().sum(axis=1) == 0).all()
    live = W[W.abs().sum(axis=1) > 0]
    assert np.allclose(live.sum(axis=1), 2.0, atol=1e-9)
    assert (W.values >= 0).all()
    # cap is single-pass (cap then renormalize, per shared design): allow mild inflation
    assert (live.values <= 2.0 * 0.02 * 1.15).all()
    print("self-check OK")
