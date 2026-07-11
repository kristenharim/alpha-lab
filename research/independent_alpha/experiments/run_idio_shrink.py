"""EXP-2026-07-10-idio-diag-shrink — residual-diagonal (idiosyncratic-variance) shrinkage
in PCA/JSE min-var. Prereg: research/independent_alpha/prereg/H-idio-shrink.md.

Standalone. Reuses the estimator_lab harness (run_minvar walk-forward + estimators._pca_parts)
WITHOUT mutating shipped estimators.py. The ONLY change vs control is the residual diagonal D:
    D_shrink = alpha*mean(D) + (1-alpha)*D   (shrink toward cross-sectional mean, trace-preserving)
applied to pca3 and jse3, alpha in {0.25, 0.50, 0.75}. alpha=0 == shipped control.

Economic call is on alpha=0.50 ONLY (primary). {0.25,0.75} are monotonicity/robustness only.
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

EL = Path("/Users/kristenho/projects/alpha-lab/research/estimator_lab")
sys.path.insert(0, str(EL))
from estimators import _pca_parts, mp_cov  # noqa: E402  read-only reuse

HERE = Path(__file__).parent
PANEL = Path("/Users/kristenho/projects/alpha-lab/research/hunt2026/panel_2005.parquet")
WINDOW = 252
CAP = 0.05
COST = 0.001
START = "2015-01-01"
HOLDOUT_START = pd.Timestamp("2024-07-01")  # blind sign-stability window 2024-07..2026-06
ALPHAS = [0.25, 0.50, 0.75]

EXCLUDE = {
    "SPY", "QQQ", "IWM", "DIA", "MDY", "EFA", "EEM", "VGK", "EWJ", "TLT", "IEF",
    "SHY", "BIL", "LQD", "HYG", "TIP", "GLD", "SLV", "DBC", "USO", "UNG", "VNQ",
    "UUP", "FXE", "XLB", "XLE", "XLF", "XLI", "XLK", "XLP", "XLU", "XLV", "XLY",
    "XLRE", "XLC", "RSP", "SVXY", "^VIX",
}


def pca_shrink_cov(R, k, jse, alpha):
    """Shipped Sigma = V lam V' + diag(D), but D shrunk toward its mean by alpha (0=control)."""
    V, lam, D = _pca_parts(R, k, jse)
    if alpha > 0.0:
        D = alpha * D.mean() + (1.0 - alpha) * D
    return (V * lam) @ V.T + np.diag(D)


def build_estimators():
    est = {}
    for tag, jse in (("pca3", False), ("jse3", True)):
        est[f"{tag}_raw"] = (lambda R, j=jse: pca_shrink_cov(R, 3, j, 0.0))
        for a in ALPHAS:
            est[f"{tag}_a{int(a * 100):02d}"] = (lambda R, j=jse, a=a: pca_shrink_cov(R, 3, j, a))
    est["mp"] = mp_cov  # for the D_shrink - mp secondary
    return est


def minvar_weights(Sigma, long_only):
    p = Sigma.shape[0]
    ones = np.ones(p)
    try:
        w = np.linalg.solve(Sigma, ones)
    except np.linalg.LinAlgError:
        w = np.linalg.pinv(Sigma, hermitian=True) @ ones
    if not np.isfinite(w).all() or np.linalg.norm(Sigma @ w - ones) > 1e-6 * np.sqrt(p):
        w = np.linalg.pinv(Sigma, hermitian=True, rcond=1e-10) @ ones
    if abs(w.sum()) < 1e-12:
        return None
    w = w / w.sum()
    if long_only:
        w = np.clip(w, 0.0, None)
        if w.sum() <= 0:
            return None
        w = w / w.sum()
    w = np.clip(w, -CAP, CAP)
    s = w.sum()
    if abs(s) < 1e-9:
        return None
    return w / s


def main():
    ESTIMATORS = build_estimators()
    panel = pd.read_parquet(PANEL)
    close, member = panel["close"], panel["member"].fillna(0.0)
    stocks = [t for t in close.columns if t not in EXCLUDE]
    rets = close[stocks].pct_change(fill_method=None)
    idx = close.index

    firsts = pd.Series(idx, index=idx).groupby(idx.to_period("M")).first()
    firsts = firsts[firsts >= pd.Timestamp(START)]
    pos = {d: i for i, d in enumerate(idx)}

    rows = []
    for m, (per, d) in enumerate(firsts.items()):
        i = pos[d]
        if i < WINDOW:
            continue
        nxt = firsts.iloc[m + 1] if m + 1 < len(firsts) else pd.Timestamp("2100-01-01")
        hold = rets.loc[(rets.index > d) & (rets.index <= nxt)]
        if len(hold) < 10:
            continue
        win = rets.iloc[i - WINDOW + 1: i + 1]
        elig = (member.loc[d, stocks] > 0) & win.notna().all()
        names = list(elig.index[elig])
        if len(names) < 100:
            continue
        R = win[names].to_numpy()
        Hret = hold[names].fillna(0.0).to_numpy()
        for est, fn in ESTIMATORS.items():
            Sigma = fn(R)
            for lo in (False, True):
                w = minvar_weights(Sigma, lo)
                if w is None:
                    continue
                pr = Hret @ w
                rows.append({
                    "date": d, "est": est, "book": "long_only" if lo else "unconstrained",
                    "n_names": len(names),
                    "vol": pr.std(ddof=1) * np.sqrt(252),
                    "ret": pr.sum(),
                    "weights": pd.Series(w, index=names),
                })
        if m % 24 == 0:
            print(f"  {d.date()}  p={len(names)}")

    df = pd.DataFrame(rows)
    df["turnover"] = np.nan
    for (est, book), g in df.groupby(["est", "book"]):
        prev = None
        for j in g.index:
            w = df.at[j, "weights"]
            if prev is not None:
                u = w.index.union(prev.index)
                df.at[j, "turnover"] = (w.reindex(u, fill_value=0.0)
                                        - prev.reindex(u, fill_value=0.0)).abs().sum()
            prev = w
    df["ret_net"] = df["ret"] - COST * df["turnover"].fillna(0.0)

    out = df.drop(columns="weights")
    out.to_csv(HERE / "idio_shrink_results.csv", index=False)

    # ---- per-estimator summary (mean vol, net Sharpe, turnover) ----
    summ = []
    for book, g in out.groupby("book"):
        wide = g.pivot(index="date", columns="est", values="vol").dropna()
        for est in ESTIMATORS:
            if est not in wide:
                continue
            ge = g[g["est"] == est]
            ann = ge["ret_net"].mean() * 12
            annvol = ge["ret_net"].std(ddof=1) * np.sqrt(12)
            summ.append({
                "book": book, "est": est, "mean_vol": wide[est].mean(),
                "sharpe_net": ann / annvol if annvol > 0 else np.nan,
                "mean_turnover": ge["turnover"].mean(),
                "months": len(wide),
            })
    sm = pd.DataFrame(summ)
    sm.to_csv(HERE / "idio_shrink_summary.csv", index=False)
    print("\n=== per-estimator summary ===")
    print(sm.to_string(index=False, float_format=lambda x: f"{x:.4f}"))

    # ---- paired tests: D_shrink(alpha) - D_raw, per book/base ----
    def paired(book, base, alpha, ref=None):
        """t of monthly vol delta (base_a{alpha} - base_raw) unless ref given."""
        g = out[out["book"] == book]
        wide = g.pivot(index="date", columns="est", values="vol").dropna()
        tcol = f"{base}_a{int(alpha * 100):02d}"
        ccol = ref if ref else f"{base}_raw"
        d = (wide[tcol] - wide[ccol]) * 100  # vol %-points
        t, pv = stats.ttest_rel(wide[tcol], wide[ccol])
        return wide, d, t, pv

    print("\n=== paired vol delta  D_shrink(alpha) - D_raw  (bps, negative = shrink lowers vol) ===")
    results = {}
    for book in ("unconstrained", "long_only"):
        for base in ("pca3", "jse3"):
            for a in ALPHAS:
                wide, d, t, pv = paired(book, base, a)
                bps = d.mean() * 100
                results[(book, base, a)] = (bps, t, pv, d)
                print(f"  {book:13} {base} a={a:.2f}: {bps:+7.2f} bps  t={t:+6.2f}  p={pv:.4f}")

    # ---- PRIMARY: pca3 unconstrained alpha=0.50 ----
    print("\n=== PRIMARY (pca3 unconstrained, alpha=0.50) ===")
    wide, d, t, pv = paired("unconstrained", "pca3", 0.50)
    bps = d.mean() * 100
    v_raw = wide["pca3_raw"].mean() * 100
    v_shr = wide["pca3_a50"].mean() * 100
    print(f"  mean vol raw={v_raw:.3f}%  shrink={v_shr:.3f}%  delta={bps:+.2f} bps  paired t={t:+.3f}  p={pv:.4f}")

    # holdout sign stability
    d_pre = d[d.index < HOLDOUT_START]
    d_hold = d[d.index >= HOLDOUT_START]
    sign_full = np.sign(d.mean())
    sign_hold = np.sign(d_hold.mean())
    print(f"  full-sample mean delta sign={sign_full:+.0f} ({d.mean() * 100:+.2f} bps, n={len(d)})")
    print(f"  pre-holdout (<2024-07) mean delta={d_pre.mean() * 100:+.2f} bps (n={len(d_pre)})")
    print(f"  HOLDOUT (2024-07..2026-06) mean delta={d_hold.mean() * 100:+.2f} bps (n={len(d_hold)})  sign={sign_hold:+.0f}")
    print(f"  sign stable (no flip)? {bool(sign_full == sign_hold)}")

    # monotonicity across alphas (pca3 unconstrained)
    seq = [results[("unconstrained", "pca3", a)][0] for a in ALPHAS]
    mono_dec = all(seq[i] >= seq[i + 1] for i in range(len(seq) - 1))
    mono_inc = all(seq[i] <= seq[i + 1] for i in range(len(seq) - 1))
    print(f"  pca3 unconstrained bps across a={ALPHAS}: {[round(x, 2) for x in seq]}  monotone={mono_dec or mono_inc}")

    # ---- SECONDARY: D_shrink(0.50) - mp, pca3 unconstrained ----
    print("\n=== SECONDARY: D_shrink(0.50) - mp (pca3 unconstrained) ===")
    wide2, d2, t2, pv2 = paired("unconstrained", "pca3", 0.50, ref="mp")
    print(f"  pca3_a50 - mp = {d2.mean() * 100:+.2f} bps  t={t2:+.2f}  p={pv2:.4f}  (mp vol={wide2['mp'].mean() * 100:.3f}%)")

    # turnover delta primary
    g = out[out["book"] == "unconstrained"]
    to_raw = g[g["est"] == "pca3_raw"]["turnover"].mean()
    to_shr = g[g["est"] == "pca3_a50"]["turnover"].mean()
    print(f"\n=== turnover (unconstrained pca3): raw={to_raw:.4f}  shrink50={to_shr:.4f}  delta={to_shr - to_raw:+.4f} ===")

    # sanity: raw control must match RESULTS.md (pca3 13.09%, jse3 13.27%)
    print("\n=== SANITY: raw controls vs RESULTS.md (pca3=13.09%, jse3=13.27%) ===")
    guc = out[out["book"] == "unconstrained"]
    w = guc.pivot(index="date", columns="est", values="vol").dropna()
    print(f"  pca3_raw mean vol = {w['pca3_raw'].mean() * 100:.2f}%   jse3_raw mean vol = {w['jse3_raw'].mean() * 100:.2f}%")


if __name__ == "__main__":
    main()
