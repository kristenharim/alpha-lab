"""EXP-2026-07-10-lw-cc-target (prereg H-lw-target).

Standalone runner. Adds an lw_cc estimator (Ledoit-Wolf shrinkage toward the
constant-correlation target, analytic delta* from LW-2004) and re-runs the exact
estimator_lab walk-forward for {lw (identity), mp, lw_cc}. Imports the shipped
harness read-only; writes only into this experiments/ dir. Does NOT touch the
shipped results.csv / summary.csv.

Primary: unconstrained mean realized ann. vol + paired t of monthly realized vol
lw_cc - lw_identity. Holdout: CC-identity vol delta sign must not flip in
2024-07..2026-06.
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

EL = Path("/Users/kristenho/projects/alpha-lab/research/estimator_lab")
sys.path.insert(0, str(EL))
# read-only imports of the shipped harness
from estimators import lw_cov, mp_cov, sample_cov  # noqa: E402
from run_minvar import minvar_weights, EXCLUDE, COST, PANEL, WINDOW, START  # noqa: E402

HERE = Path(__file__).parent
HOLDOUT_START = pd.Timestamp("2024-07-01")  # last 24 months of the 137-month span


def lw_cc_cov(R, return_diag=False):
    """Ledoit-Wolf 2004 shrinkage toward the constant-correlation target.

    Port of the canonical covCor.m. R is (t x n) daily returns (not demeaned).
    Sigma = delta* * F + (1 - delta*) * S, S = (1/t) X'X (X demeaned),
    F_ii = s_ii, F_ij = rbar*sqrt(s_ii*s_jj), rbar = mean off-diag sample corr,
    delta* = clip(kappa/t, 0, 1), kappa = (pi - rho)/gamma.
    """
    x = R - R.mean(axis=0)
    t, n = x.shape
    sample = (x.T @ x) / t  # 1/t convention (LW-2004)

    var = np.diag(sample).copy()
    sqrtvar = np.sqrt(var)
    outer = np.outer(sqrtvar, sqrtvar)
    rbar = (np.sum(sample / outer) - n) / (n * (n - 1))
    prior = rbar * outer
    np.fill_diagonal(prior, var)

    # pi-hat: sum of asymptotic variances of sample-cov entries
    y = x ** 2
    phiMat = (y.T @ y) / t - sample ** 2  # (1/t)sum x_it^2 x_jt^2 - s_ij^2
    phi = phiMat.sum()

    # rho-hat: sum of asymptotic covariances of the target with the sample cov
    term1 = ((x ** 3).T @ x) / t
    help_ = (x.T @ x) / t
    helpDiag = np.diag(help_)
    term2 = helpDiag[:, None] * sample
    term3 = help_ * var[:, None]
    term4 = var[:, None] * sample
    thetaMat = term1 - term2 - term3 + term4
    np.fill_diagonal(thetaMat, 0.0)
    rho = np.diag(phiMat).sum() + rbar * np.sum((np.outer(1.0 / sqrtvar, sqrtvar)) * thetaMat)

    # gamma-hat: misfit of the target
    gamma = np.sum((sample - prior) ** 2)

    kappa = (phi - rho) / gamma
    delta = max(0.0, min(1.0, kappa / t))
    sigma = delta * prior + (1.0 - delta) * sample
    if return_diag:
        Fmin = np.linalg.eigvalsh(prior).min()
        return sigma, delta, rbar, Fmin
    return sigma


ESTS = {"lw": lw_cov, "mp": mp_cov, "lw_cc": lw_cc_cov}


def run():
    panel = pd.read_parquet(PANEL)
    close, member = panel["close"], panel["member"].fillna(0.0)
    stocks = [t for t in close.columns if t not in EXCLUDE]
    rets = close[stocks].pct_change(fill_method=None)
    idx = close.index

    firsts = pd.Series(idx, index=idx).groupby(idx.to_period("M")).first()
    firsts = firsts[firsts >= pd.Timestamp(START)]
    pos = {d: i for i, d in enumerate(idx)}

    rows, diag = [], []
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

        # lw_cc diagnostics (delta* in [0,1], F PSD)
        _, delta, rbar, Fmin = lw_cc_cov(R, return_diag=True)
        diag.append({"date": d, "delta": delta, "rbar": rbar, "F_mineig": Fmin, "p": len(names)})

        for est, fn in ESTS.items():
            Sigma = fn(R)
            for lo in (False, True):
                w = minvar_weights(Sigma, lo)
                if w is None:
                    continue
                pr = Hret @ w
                rows.append({
                    "date": d, "est": est,
                    "book": "long_only" if lo else "unconstrained",
                    "n_names": len(names),
                    "vol": pr.std(ddof=1) * np.sqrt(252),
                    "ret": pr.sum(),
                    "weights": pd.Series(w, index=names),
                })

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
    out.to_csv(HERE / "lw_cc_results.csv", index=False)
    diagdf = pd.DataFrame(diag)
    diagdf.to_csv(HERE / "lw_cc_diag.csv", index=False)
    return out, diagdf


def report(out, diagdf):
    print("=== SANITY: analytic delta* and target PSD-ness ===")
    print(f"  months: {len(diagdf)}")
    print(f"  delta*  min={diagdf.delta.min():.4f}  max={diagdf.delta.max():.4f}  "
          f"mean={diagdf.delta.mean():.4f}  (must be in [0,1])")
    print(f"  rbar    min={diagdf.rbar.min():.4f}  max={diagdf.rbar.max():.4f}  mean={diagdf.rbar.mean():.4f}")
    print(f"  F min eig  min={diagdf.F_mineig.min():.3e}  (>=0 => target PSD every month)")
    assert diagdf.delta.between(0, 1).all(), "delta* out of [0,1]"
    assert (diagdf.F_mineig >= -1e-8).all(), "constant-corr target not PSD"

    print("\n=== mean realized ann. vol per estimator ===")
    for book in ("unconstrained", "long_only"):
        g = out[out.book == book]
        wide = g.pivot(index="date", columns="est", values="vol").dropna()
        print(f"  [{book}]  months={len(wide)}")
        for est in ("lw", "mp", "lw_cc"):
            ge = g[g.est == est]
            ann = ge["ret_net"].mean() * 12
            annvol = ge["ret_net"].std(ddof=1) * np.sqrt(12)
            sharpe = ann / annvol if annvol > 0 else np.nan
            print(f"    {est:6} vol={wide[est].mean()*100:.3f}%  "
                  f"sharpe_net={sharpe:.3f}  turnover={ge['turnover'].mean():.3f}")

    print("\n=== PRIMARY: paired t of monthly realized vol, lw_cc - lw_identity ===")
    for book in ("unconstrained", "long_only"):
        wide = out[out.book == book].pivot(index="date", columns="est", values="vol").dropna()
        d = (wide["lw_cc"] - wide["lw"]) * 100  # vol %-points
        t, p = stats.ttest_rel(wide["lw_cc"], wide["lw"])
        tag = "PRIMARY" if book == "unconstrained" else "secondary"
        print(f"  [{book:13}] ({tag}) lw_cc-lw = {d.mean():+.4f} vol%pts ({d.mean()*100:+.2f} bps)  "
              f"t={t:+.3f}  p={p:.4g}")
        # holdout sign stability
        h = d[d.index >= HOLDOUT_START]
        full_sign = np.sign(d.mean())
        hold_sign = np.sign(h.mean())
        print(f"                 holdout 2024-07..2026-06 (n={len(h)}): "
              f"lw_cc-lw = {h.mean():+.4f} vol%pts  sign {'STABLE' if hold_sign==full_sign else 'FLIPPED'}")

    print("\n=== SECONDARY: lw_cc - mp (does it dethrone the champion?) ===")
    for book in ("unconstrained", "long_only"):
        wide = out[out.book == book].pivot(index="date", columns="est", values="vol").dropna()
        d = (wide["lw_cc"] - wide["mp"]) * 100
        t, p = stats.ttest_rel(wide["lw_cc"], wide["mp"])
        print(f"  [{book:13}] lw_cc-mp = {d.mean():+.4f} vol%pts  t={t:+.3f}  p={p:.4g}")


if __name__ == "__main__":
    out, diagdf = run()
    report(out, diagdf)
