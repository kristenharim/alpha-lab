"""EXP-B — Conditional volatility-management mechanism (measurement only).

Frozen prereg: research/discovery/prereg/EXP-B-conditional-vol-mechanism.md
Does the cross-asset variation in vol-management BENEFIT get explained by four
pre-registered fixed-sign asset properties, at the CLUSTER level?

MEASUREMENT ONLY. No portfolio, no book, no live. Vol-target spec is FROZEN at the
vol_managed_qqq live spec (sigma_target=0.25, 21d lookback, 0.05 no-trade band, 2x cap),
identical for every asset. Costs = harness convention (2 bps/side ETF on |Δw|).
"""
import json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

HERE = Path(__file__).parent
ROOT = HERE.parents[2]  # alpha-lab/
PANEL = ROOT / "research/hunt2026/panel_2005.parquet"
STATE = ROOT / "research/discovery/data/state_aligned.parquet"

# --- FROZEN vol_managed_qqq spec params (research/hunt2026/specs/vol_managed_qqq) ---
SIGMA_TARGET = 0.25
VOL_LOOKBACK = 21
TOL_BAND = 0.05
LEV_CAP = 2.0
ETF_BPS = 2.0  # harness ETF per-side cost

# --- cross-asset ETF set = sandbox_meta etfs ∩ panel columns, with clusters ---
CLUSTERS = {
    "US-equity": ["SPY", "QQQ", "IWM", "RSP", "XLB", "XLE", "XLF", "XLI",
                  "XLK", "XLP", "XLU", "XLV", "XLY", "XLC", "XLRE"],
    "intl-equity": ["EFA", "EEM", "VGK", "EWJ"],
    "rates": ["TLT", "IEF"],
    "commodities": ["GLD", "SLV", "DBC", "USO"],
    "real-estate": ["VNQ"],
}
ASSET_CLUSTER = {t: c for c, ts in CLUSTERS.items() for t in ts}
ASSETS = list(ASSET_CLUSTER)

# expected coefficient signs (frozen): +, +, -, +
EXPECTED_SIGN = {"risk_premium": +1, "vol_clustering": +1,
                 "ret_vol_asym": -1, "dd_convexity": +1}
PROPS = list(EXPECTED_SIGN)


def vol_managed_weights(close: pd.Series) -> pd.Series:
    """Frozen vol_managed_qqq rule applied to one asset's close series."""
    rets = close.pct_change(fill_method=None)
    rv = rets.rolling(VOL_LOOKBACK).std() * np.sqrt(252)
    raw = (SIGMA_TARGET / rv).clip(upper=LEV_CAP).fillna(0.0).to_numpy()
    w = np.empty_like(raw)
    cur = 0.0
    for i, tgt in enumerate(raw):  # tolerance band, plain loop (frozen spec logic)
        if abs(tgt - cur) > TOL_BAND:
            cur = tgt
        w[i] = cur
    return pd.Series(w, index=close.index)


def net_series(close: pd.Series, W: pd.Series) -> pd.Series:
    """Harness P&L convention: held=W.shift(1) earns close-to-close, 2bps on |Δw|."""
    rets = close.pct_change(fill_method=None)
    held = W.shift(1)
    gross = held * rets
    cost = W.diff().abs().fillna(W.abs()) * (ETF_BPS / 1e4)
    return (gross - cost).fillna(0.0)


def cagr(net: pd.Series) -> float:
    nav = (1.0 + net).prod()
    years = len(net) / 252.0
    return float(nav ** (1.0 / years) - 1.0)


def compute_benefit(close: pd.Series, rf_daily: pd.Series):
    """benefit = CAGR(vol-managed) - CAGR(buy-hold) over the asset's live window."""
    Wvm = vol_managed_weights(close)
    rets = close.pct_change(fill_method=None)
    rv = rets.rolling(VOL_LOOKBACK).std()
    live = close.notna() & rv.notna()  # after inception + 21d warmup
    idx = close.index[live]
    idx = idx[idx > idx[0]]  # drop the first (shift(1) has no prior weight)

    Wbh = pd.Series(1.0, index=close.index)
    net_vm = net_series(close, Wvm).reindex(idx).fillna(0.0)
    net_bh = net_series(close, Wbh).reindex(idx).fillna(0.0)
    benefit = cagr(net_vm) - cagr(net_bh)
    return {
        "benefit": benefit,
        "cagr_vm": cagr(net_vm),
        "cagr_bh": cagr(net_bh),
        "n_days": len(idx),
        "avg_lev": float(Wvm.reindex(idx).mean()),
        "start": str(idx[0].date()),
        "end": str(idx[-1].date()),
    }


def properties(close: pd.Series, rf_daily: pd.Series):
    rets = close.pct_change(fill_method=None).dropna()
    idx = rets.index

    # P1 risk premium: annualized mean excess return
    rf = rf_daily.reindex(idx).ffill().fillna(0.0)
    risk_premium = float((rets - rf).mean() * 252)

    # P2 vol clustering: AR(1) of squared daily returns (non-overlapping ARCH clustering;
    #    rolling-rv AR(1) reported too but is mechanically ~1 from window overlap)
    sq = (rets ** 2)
    ar1_sq = _ar1(sq)
    rv = rets.rolling(VOL_LOOKBACK).std().dropna()
    ar1_rv = _ar1(rv)
    vol_clustering = ar1_sq

    # P3 return-vol asymmetry: corr(r_t, Δσ_{t+1}), σ = 21d realized vol
    sig = rets.rolling(VOL_LOOKBACK).std() * np.sqrt(252)
    dsig_next = sig.shift(-1) - sig            # Δσ_{t+1}
    pair = pd.concat([rets, dsig_next], axis=1).dropna()
    ret_vol_asym = float(np.corrcoef(pair.iloc[:, 0], pair.iloc[:, 1])[0, 1])

    # P4 drawdown convexity: realized vol in worst-return-decile months / overall vol
    mret = (1 + rets).resample("ME").prod() - 1
    thresh = mret.quantile(0.10)
    worst_months = set(mret.index[mret <= thresh].to_period("M"))
    in_worst = rets.index.to_period("M").isin(worst_months)
    dd_convexity = float(rets[in_worst].std() / rets.std())

    return {"risk_premium": risk_premium, "vol_clustering": vol_clustering,
            "ret_vol_asym": ret_vol_asym, "dd_convexity": dd_convexity,
            "ar1_rv_overlap": ar1_rv}


def _ar1(x: pd.Series) -> float:
    x = x.dropna()
    a, b = x.iloc[1:].to_numpy(), x.iloc[:-1].to_numpy()
    if a.std() == 0 or b.std() == 0:
        return np.nan
    return float(np.corrcoef(a, b)[0, 1] * a.std() / b.std())  # OLS slope


def ols(y, X):
    """OLS with intercept. Returns beta, resid, XtX_inv, fitted."""
    n = len(y)
    Xd = np.column_stack([np.ones(n), X])
    XtX_inv = np.linalg.inv(Xd.T @ Xd)
    beta = XtX_inv @ Xd.T @ y
    fitted = Xd @ beta
    resid = y - fitted
    return beta, resid, XtX_inv, Xd, fitted


def cluster_robust_vcov(Xd, resid, XtX_inv, groups):
    """CR1 cluster-robust covariance (Liang-Zeger with small-sample correction)."""
    n, k = Xd.shape
    G = len(np.unique(groups))
    meat = np.zeros((k, k))
    for g in np.unique(groups):
        m = groups == g
        Xg, ug = Xd[m], resid[m]
        s = Xg.T @ ug
        meat += np.outer(s, s)
    c = (G / (G - 1)) * ((n - 1) / (n - k))
    return c * (XtX_inv @ meat @ XtX_inv), G


def main():
    panel = pd.read_parquet(PANEL)["close"]
    state = pd.read_parquet(STATE)
    rf_daily = state["DFF"] / 100.0 / 252.0  # DFF is annualized %; STATE only

    rows = []
    for t in ASSETS:
        close = panel[t].dropna()
        b = compute_benefit(close, rf_daily)
        p = properties(close, rf_daily)
        rows.append({"asset": t, "cluster": ASSET_CLUSTER[t], **b, **p})
    df = pd.DataFrame(rows).set_index("asset")
    df.to_csv(HERE / "EXP-B-per-asset.csv")

    # --- bug check: replicate the FROZEN vol_managed_qqq benefit two ways ---
    import importlib.util
    spec_dir = ROOT / "research/hunt2026/specs/vol_managed_qqq"
    s = importlib.util.spec_from_file_location("vmqqq", spec_dir / "spec.py")
    mqm = importlib.util.module_from_spec(s); s.loader.exec_module(mqm)
    Wq_spec = mqm.target_weights(pd.read_parquet(PANEL))["QQQ"]
    Wq_ours = vol_managed_weights(panel["QQQ"].dropna()).reindex(Wq_spec.index)
    wdiff = float((Wq_spec.fillna(0) - Wq_ours.fillna(0)).abs().max())

    # --- standardized predictor regression (cross-asset), cluster-robust ---
    Z = (df[PROPS] - df[PROPS].mean()) / df[PROPS].std()
    y = df["benefit"].to_numpy()
    Xz = Z.to_numpy()
    beta, resid, XtX_inv, Xd, fitted = ols(y, Xz)
    ss_res = float((resid ** 2).sum())
    ss_tot = float(((y - y.mean()) ** 2).sum())
    r2 = 1 - ss_res / ss_tot
    groups = df["cluster"].to_numpy()
    Vcr, G = cluster_robust_vcov(Xd, resid, XtX_inv, groups)
    se_cr = np.sqrt(np.diag(Vcr))

    # joint Wald test on the 4 slopes (exclude intercept). NOTE: with G=5 clusters and
    # q=4 restrictions this cluster-robust Wald is near-degenerate (R@Vcr@R.T ill-conditioned)
    # -> the raw stat/p is NOT trustworthy. We report it, flag its condition number, and use
    # a Rademacher WILD CLUSTER BOOTSTRAP (null-imposed, all 2^G draws) as the credible p.
    R = np.zeros((4, 5)); R[np.arange(4), np.arange(1, 5)] = 1.0

    def joint_wald(beta_, Vcr_):
        Rb_ = R @ beta_
        M = R @ Vcr_ @ R.T
        return float(Rb_.T @ np.linalg.inv(M) @ Rb_), float(np.linalg.cond(M))

    W_stat, cond_M = joint_wald(beta, Vcr)
    q = 4
    F_joint = W_stat / q
    p_joint_raw = float(stats.f.sf(F_joint, q, G - 1))

    # naive iid OLS F (prereg says NOT to trust — treats 26 assets as independent) for reference
    k_full = Xd.shape[1]
    F_iid = (r2 / q) / ((1 - r2) / (len(y) - k_full))
    p_iid = float(stats.f.sf(F_iid, q, len(y) - k_full))

    # wild cluster bootstrap (Rademacher, null imposed: slopes=0 -> restricted fit = ybar)
    import itertools
    yhat0 = np.full_like(y, y.mean())
    u0 = y - yhat0
    uniq = list(np.unique(groups))
    Wobs = W_stat
    count_ge, ndraw = 0, 0
    for signs in itertools.product([1.0, -1.0], repeat=len(uniq)):
        smap = dict(zip(uniq, signs))
        sg = np.array([smap[g] for g in groups])
        ystar = yhat0 + sg * u0
        b_s, r_s, _, _, _ = ols(ystar, Xz)
        V_s, _ = cluster_robust_vcov(Xd, r_s, XtX_inv, groups)
        W_s, _ = joint_wald(b_s, V_s)
        ndraw += 1
        if W_s >= Wobs - 1e-9:
            count_ge += 1
    p_joint_wcb = count_ge / ndraw
    p_joint = p_joint_wcb  # credible few-cluster p-value

    coefs = {}
    signs_ok = {}
    for i, pr in enumerate(PROPS):
        b_i = beta[i + 1]
        t_i = b_i / se_cr[i + 1]
        p_i = float(2 * stats.t.sf(abs(t_i), G - 1))
        ok = np.sign(b_i) == EXPECTED_SIGN[pr]
        coefs[pr] = {"beta_std": float(b_i), "se_cr": float(se_cr[i + 1]),
                     "t": float(t_i), "p": p_i, "expected_sign": EXPECTED_SIGN[pr],
                     "sign_ok": bool(ok)}
        signs_ok[pr] = bool(ok)
    n_signs_ok = sum(signs_ok.values())

    # --- cluster-mean univariate signs (n=5 clusters) ---
    cm = df.groupby("cluster")[["benefit"] + PROPS].mean()
    cm_signs = {}
    for pr in PROPS:
        r = float(np.corrcoef(cm[pr], cm["benefit"])[0, 1])
        cm_signs[pr] = {"corr_clustermean": r,
                        "sign_ok": bool(np.sign(r) == EXPECTED_SIGN[pr])}

    # --- leave-one-cluster-out sign stability ---
    loco = {pr: [] for pr in PROPS}
    for c in CLUSTERS:
        keep = df["cluster"] != c
        Zc = (df.loc[keep, PROPS] - df.loc[keep, PROPS].mean()) / df.loc[keep, PROPS].std()
        bc, *_ = ols(df.loc[keep, "benefit"].to_numpy(), Zc.to_numpy())
        for i, pr in enumerate(PROPS):
            loco[pr].append(float(bc[i + 1]))
    loco_stable = {pr: {"signs": [int(np.sign(v)) for v in loco[pr]],
                        "all_match_expected": bool(all(np.sign(v) == EXPECTED_SIGN[pr]
                                                       for v in loco[pr]))}
                   for pr in PROPS}

    # --- independent value after asset-class dummies (within-cluster) ---
    dums = pd.get_dummies(df["cluster"], drop_first=True).astype(float)
    Xd2 = np.column_stack([Xz, dums.to_numpy()])
    b2, resid2, XtXi2, Xdd2, _ = ols(y, Xd2)
    ss_res2 = float((resid2 ** 2).sum())
    r2_dum = 1 - ss_res2 / ss_tot
    # naive (non-clustered) t on props within dummy model, df = n-k
    n2, k2 = Xdd2.shape
    sigma2 = ss_res2 / (n2 - k2)
    se2 = np.sqrt(np.diag(sigma2 * XtXi2))
    indep = {}
    for i, pr in enumerate(PROPS):
        b_i = b2[i + 1]
        t_i = b_i / se2[i + 1]
        indep[pr] = {"beta_within": float(b_i), "t": float(t_i),
                     "p": float(2 * stats.t.sf(abs(t_i), n2 - k2)),
                     "sign_ok": bool(np.sign(b_i) == EXPECTED_SIGN[pr])}

    # --- verdict (frozen kill rule) ---
    joint_sig = p_joint < 0.05
    if n_signs_ok >= 3 and joint_sig:
        # NARROWED if properties 2-4 add nothing beyond risk premium alone
        verdict = "SUPPORTED_or_NARROWED"
    else:
        verdict = "MECHANISM_UNSUPPORTED"

    out = {
        "n_assets": len(df), "n_clusters": G,
        "bug_check": {"max_weight_diff_vs_frozen_spec": wdiff,
                      "qqq_benefit": float(df.loc["QQQ", "benefit"]),
                      "qqq_cagr_vm": float(df.loc["QQQ", "cagr_vm"]),
                      "qqq_cagr_bh": float(df.loc["QQQ", "cagr_bh"])},
        "regression_std_clusterrobust": {
            "coefs": coefs, "r2": r2,
            "joint_F_raw_UNSTABLE": F_joint, "joint_p_raw_UNSTABLE": p_joint_raw,
            "joint_wald_cond_number": cond_M,
            "joint_p_wild_cluster_boot": p_joint_wcb, "wcb_ndraws": ndraw,
            "joint_F_iid_reference": F_iid, "joint_p_iid_reference": p_iid,
            "joint_p": p_joint,
            "n_signs_ok": n_signs_ok, "joint_sig_5pct": bool(joint_sig)},
        "cluster_mean_univariate": cm_signs,
        "leave_one_cluster_out": loco_stable,
        "within_cluster_dummies": {"r2_with_dummies": r2_dum, "props": indep},
        "verdict": verdict,
    }
    (HERE / "EXP-B-results.json").write_text(json.dumps(out, indent=2, default=str))
    cm.to_csv(HERE / "EXP-B-cluster-means.csv")

    pd.set_option("display.width", 200, "display.max_columns", 30)
    print("=== PER-ASSET ===")
    print(df[["cluster", "benefit", "cagr_vm", "cagr_bh", "avg_lev", "n_days",
              "risk_premium", "vol_clustering", "ret_vol_asym", "dd_convexity"]]
          .round(4).to_string())
    print("\n=== BUG CHECK ===")
    print(f"  max |w_ours - w_frozenspec| for QQQ = {wdiff:.2e}  (0 => exact replication)")
    print(f"  QQQ benefit={df.loc['QQQ','benefit']:.4f}  vm={df.loc['QQQ','cagr_vm']:.4f}  bh={df.loc['QQQ','cagr_bh']:.4f}")
    print("\n=== STANDARDIZED CLUSTER-ROBUST REGRESSION (n=%d, G=%d clusters) ===" % (len(df), G))
    for pr in PROPS:
        c = coefs[pr]
        print(f"  {pr:15} beta={c['beta_std']:+.4f}  se_cr={c['se_cr']:.4f}  t={c['t']:+.2f}  "
              f"p={c['p']:.3f}  exp={EXPECTED_SIGN[pr]:+d}  sign_ok={c['sign_ok']}")
    print(f"  R2={r2:.3f}   signs_ok={n_signs_ok}/4")
    print(f"  joint test: raw CR Wald F(4,4)={F_joint:.1f} p={p_joint_raw:.4f} [UNSTABLE, cond(M)={cond_M:.1e}]")
    print(f"              wild-cluster-boot p={p_joint_wcb:.4f} (2^{G} draws) <- credible few-cluster p")
    print(f"              iid-reference F={F_iid:.2f} p={p_iid:.4f} (prereg: do NOT trust, assets not independent)")
    print("\n=== CLUSTER-MEAN UNIVARIATE (n=5) ===")
    for pr in PROPS:
        print(f"  {pr:15} corr={cm_signs[pr]['corr_clustermean']:+.3f}  sign_ok={cm_signs[pr]['sign_ok']}")
    print("\n=== LEAVE-ONE-CLUSTER-OUT sign match to expected ===")
    for pr in PROPS:
        print(f"  {pr:15} signs={loco_stable[pr]['signs']}  all_expected={loco_stable[pr]['all_match_expected']}")
    print("\n=== WITHIN-CLUSTER (asset-class dummies), R2=%.3f ===" % r2_dum)
    for pr in PROPS:
        d = indep[pr]
        print(f"  {pr:15} beta_within={d['beta_within']:+.4f}  t={d['t']:+.2f}  p={d['p']:.3f}  sign_ok={d['sign_ok']}")
    print(f"\n=== VERDICT: {verdict} ===")


if __name__ == "__main__":
    main()
