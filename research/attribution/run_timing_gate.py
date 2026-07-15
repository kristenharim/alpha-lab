"""EXP-2026-07-14-timing-tm — TM timing gate on the frozen attribution.

Prereg: research/hunt2026/preregistrations/timing-tm-2026-07-14.md (frozen incl.
dispositions 1-9). M2T = M2 + gamma*(Mkt-RF)^2 per book on its claim-bearing blind
window. Gate legs: (i) signed t_gamma >= 2, (ii) TV > 0 [code assert], (iii)
leverage-normalized gamma > parent (subsumed if parent gamma <= 0; HAC diff-SE
disclosed), (iv) alpha+TV survives the financing haircut. Strong tier = 5y books
only. MDE table, lag-21 t, stationary-bootstrap p, PIT-QQQRES robustness reported.

Run from repo root: .venv/bin/python research/attribution/run_timing_gate.py
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "research/hunt2026"))
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "research/attribution"))
import harness  # noqa: E402
from run_attribution import (  # noqa: E402  (nw_ols self-check runs on import)
    BOOKS, FF_END, M1_COLS, M2_COLS, build_factors, nw_ols)
from core.eval.run_manifest import stamp_run  # noqa: E402

OUT = REPO / "research/attribution"
M2T_COLS = M2_COLS + ["MKTSQ"]
T_WEAK, T_STRONG = 2.0, 2.4
N_BOOT, BLOCK_MEAN, BOOT_SEED = 2000, 21, 3
PIT_CUT = pd.Timestamp("2021-07-09")


def frame(net_daily, fac):
    df = pd.concat([net_daily.rename("ret"), fac], axis=1, join="inner").dropna()
    return df.loc[:FF_END]


def m2t_fit(df, lag=5):
    y = (df["ret"] - df["RF"]).values
    X = np.column_stack([np.ones(len(df)), df[M2T_COLS].values])
    beta, se, t, r2, n = nw_ols(y, X, lag=lag)
    gi = 1 + M2T_COLS.index("MKTSQ")
    return dict(y=y, X=X, beta=beta, se=se, t=t, r2=r2, n=n,
                gamma=beta[gi], se_gamma=se[gi], t_gamma=t[gi], gi=gi,
                alpha=beta[0])


def stat_boot_p(df, seed=BOOT_SEED):
    """Stationary bootstrap (mean block 21) one-sided p for gamma > 0."""
    rng = np.random.default_rng(seed)
    n = len(df)
    y = (df["ret"] - df["RF"]).values
    X = np.column_stack([np.ones(n), df[M2T_COLS].values])
    gi = 1 + M2T_COLS.index("MKTSQ")
    gs = []
    for _ in range(N_BOOT):
        idx, pos = [], rng.integers(0, n)
        while len(idx) < n:
            idx.append(pos)
            pos = rng.integers(0, n) if rng.random() < 1 / BLOCK_MEAN else (pos + 1) % n
        idx = np.array(idx)
        b, *_ = np.linalg.lstsq(X[idx], y[idx], rcond=None)
        gs.append(b[gi])
    return float((np.array(gs) <= 0).mean())


def hac_diff_se(df_b, df_p, gi, lag=5):
    """HAC SE of gamma_book - gamma_parent, joint on the common window."""
    common = df_b.index.intersection(df_p.index)
    db, dp = df_b.loc[common], df_p.loc[common]
    X = np.column_stack([np.ones(len(common)), db[M2T_COLS].values])
    XtX_inv = np.linalg.inv(X.T @ X)
    ub = (db["ret"] - db["RF"]).values - X @ np.linalg.lstsq(
        X, (db["ret"] - db["RF"]).values, rcond=None)[0]
    up = (dp["ret"] - dp["RF"]).values - X @ np.linalg.lstsq(
        X, (dp["ret"] - dp["RF"]).values, rcond=None)[0]
    ud = ub - up
    xu = X * ud[:, None]
    meat = xu.T @ xu
    for L in range(1, lag + 1):
        w = 1.0 - L / (lag + 1.0)
        g = xu[L:].T @ xu[:-L]
        meat += w * (g + g.T)
    cov = XtX_inv @ meat @ XtX_inv
    return float(np.sqrt(cov[gi, gi]))


def build_factors_pit(panel):
    """build_factors with QQQRES projected on pre-blind data only (disposition 8)."""
    fac = build_factors(panel).drop(columns=["QQQRES"])
    ff5 = pd.read_parquet(REPO / "data/raw/ff5_factors_daily.parquet")
    mom = pd.read_parquet(REPO / "data/raw/ff_factors_daily.parquet")[["Mom"]]
    raw = ff5.join(mom, how="inner").loc[:FF_END]
    qqq_ex = panel["close"]["QQQ"].pct_change(fill_method=None).sub(raw["RF"]).dropna()
    common = qqq_ex.index.intersection(raw.index)
    fit = common[common <= PIT_CUT]
    Xf = np.column_stack([np.ones(len(fit)), raw.loc[fit, M1_COLS].values])
    b, *_ = np.linalg.lstsq(Xf, qqq_ex.loc[fit].values, rcond=None)
    Xa = np.column_stack([np.ones(len(common)), raw.loc[common, M1_COLS].values])
    qqqres = pd.Series(qqq_ex.loc[common].values - Xa @ b, index=common, name="QQQRES")
    return fac.join(qqqres, how="inner")


def evaluate(net_daily, fac, fac_pit, book, window, avg_gross, parent=None):
    df = frame(net_daily, fac)
    if len(df) < 30:
        return None
    f = m2t_fit(df)
    var_ann = 252.0 * float((df["Mkt-RF"] ** 2).mean())
    tv_ann = f["gamma"] * var_ann
    assert (tv_ann > 0) == (f["gamma"] > 0)                # leg (ii), code assert
    alpha_ann = f["alpha"] * 252
    rf_ann = df["RF"].mean() * 252
    stress = (alpha_ann + tv_ann) - max(avg_gross - 1.0, 0.0) * (rf_ann + 0.005)
    f21 = m2t_fit(df, lag=21)
    dpit = frame(net_daily, fac_pit)
    fp = m2t_fit(dpit) if len(dpit) >= 30 else None
    row = {"book": book, "window": window, "n_obs": f["n"],
           "gamma": f["gamma"], "se_gamma": f["se_gamma"], "t_gamma": f["t_gamma"],
           "t_gamma_lag21": f21["t_gamma"], "tv_ann": tv_ann,
           "alpha_ann": alpha_ann, "alpha_plus_tv_stress": stress,
           "mde_tv_ann": 2.84 * f["se_gamma"] * var_ann,   # t>=2, 80% power
           "R2": f["r2"], "avg_gross": avg_gross,
           "gamma_pit_qqqres": fp["gamma"] if fp else np.nan,
           "t_gamma_pit_qqqres": fp["t_gamma"] if fp else np.nan}
    if parent is not None:
        p_gamma, p_gross, p_df = parent
        norm_ok = (f["gamma"] / avg_gross) > (p_gamma / p_gross)
        leg3 = norm_ok if p_gamma > 0 else (f["gamma"] > 0)
        dse = hac_diff_se(df, p_df, f["gi"])
        row.update({"parent_gamma": p_gamma, "parent_gross": p_gross,
                    "leg3_pass": bool(leg3),
                    "diff_se": dse,
                    "distinguishable": bool(abs(f["gamma"] - p_gamma) >= dse)})
        row["timing_positive"] = bool(f["t_gamma"] >= T_WEAK and tv_ann > 0
                                      and leg3 and stress > 0)
        row["strong"] = bool(row["timing_positive"] and f["t_gamma"] >= T_STRONG
                             and window == "blind_5y")     # disposition 4
        if row["timing_positive"] or f["t_gamma"] >= T_WEAK:
            row["boot_p"] = stat_boot_p(df)
    return row


def main():
    panel = harness.load_full()
    fac = build_factors(panel)
    fac["MKTSQ"] = fac["Mkt-RF"] ** 2
    fac_pit = build_factors_pit(panel)
    fac_pit["MKTSQ"] = fac_pit["Mkt-RF"] ** 2

    rows = []
    qqq_r = panel["close"]["QQQ"].pct_change(fill_method=None)
    spy_r = panel["close"]["SPY"].pct_change(fill_method=None)
    lev = 1.5 * qqq_r - (2.0 / 1e4) * (0.75 * qqq_r.abs() / (1 + 1.5 * qqq_r))
    parent_spec = harness.load_spec(REPO / "research/hunt2026/specs/bench_qqq_sma200_2x")
    parents = {}
    ctrl_fail = []
    for wlabel, start in [("blind_1y", "2025-07-10"), ("blind_5y", "2021-07-10")]:
        cut = pd.Timestamp(start)
        for cname, s, g in [("CTRL_spy_buyhold", spy_r, 1.0),
                            ("CTRL_qqq_buyhold", qqq_r, 1.0),
                            ("CTRL_qqq_1.5x_static", lev, 1.5)]:
            row = evaluate(s[s.index > cut].dropna(), fac, fac_pit, cname, wlabel, g)
            if abs(row["t_gamma"]) >= 2:                   # disposition 6 adjudicator
                row["boot_p"] = stat_boot_p(frame(s[s.index > cut].dropna(), fac))
                if row["boot_p"] <= 0.05 or row["boot_p"] >= 0.95:
                    ctrl_fail.append((cname, wlabel, row["t_gamma"], row["boot_p"]))
            rows.append(row)
        rp = harness.run(parent_spec, panel, start=start)
        pdf = frame(rp["net_daily"], fac)
        prow = evaluate(rp["net_daily"], fac, fac_pit, "PARENT_qqq_sma200_2x",
                        wlabel, rp["avg_gross_exposure"])
        rows.append(prow)
        parents[wlabel] = (prow["gamma"], rp["avg_gross_exposure"], pdf)

    for name, (_, start) in BOOKS.items():
        spec = harness.load_spec(REPO / f"research/hunt2026/specs/{name}")
        r = harness.run(spec, panel, start=start)
        wlabel = "blind_1y" if start == "2025-07-10" else "blind_5y"
        rows.append(evaluate(r["net_daily"], fac, fac_pit, name, wlabel,
                             r["avg_gross_exposure"], parent=parents[wlabel]))
        rf_full = harness.run(spec, panel, start=None)
        rows.append(evaluate(rf_full["net_daily"], fac, fac_pit, name,
                             "full_IN-SAMPLE", rf_full["avg_gross_exposure"]))

    df = pd.DataFrame([r for r in rows if r])
    df.to_csv(OUT / "timing_gate.csv", index=False)

    books = df[df.book.isin(BOOKS) & df.window.str.startswith("blind")]
    n_pos = int(books.timing_positive.sum())
    n_strong = int(books.strong.sum())
    if ctrl_fail:
        verdict = "CONTROL-FAIL (see adjudication)"
    elif n_strong >= 1:
        verdict = "SUPPORTED (strong)"
    elif n_pos >= 1:
        verdict = "SUPPORTED (weak)"
    else:
        verdict = "NOT SUPPORTED"

    L = ["# TM timing gate — EXP-2026-07-14-timing-tm", "",
         "Prereg: timing-tm-2026-07-14.md (frozen incl. dispositions 1–9). "
         "M2T = M2 + γ·(Mkt−RF)². Blind windows claim-bearing; as-frozen panel "
         "(F1 defect inherited, disclosed). NW lag 5 primary; lag-21 and stationary-"
         "bootstrap columns are disclosure.", "",
         f"## Gate verdict: **{verdict}**",
         f"- timing-positive books: {n_pos}/7 (strong tier, 5y books only: {n_strong})",
         f"- control adjudications: {ctrl_fail if ctrl_fail else 'none needed'}", "",
         "## MDE (house rule — read NOT SUPPORTED against this)", "",
         "| book | window | n | MDE TV ann (t≥2, 80% power) |", "|---|---|---|---|"]
    for _, r in books.iterrows():
        L.append(f"| {r.book} | {r.window} | {r.n_obs} | {r.mde_tv_ann:+.1%} |")
    L += ["", "## Controls + parent", "",
          "| series | window | γ | t_γ | t_γ lag21 | TV ann |",
          "|---|---|---|---|---|---|"]
    for _, r in df[df.book.str.startswith(("CTRL", "PARENT"))].iterrows():
        L.append(f"| {r.book} | {r.window} | {r.gamma:+.2f} | {r.t_gamma:+.2f} "
                 f"| {r.t_gamma_lag21:+.2f} | {r.tv_ann:+.2%} |")
    L += ["", "## Books (blind windows; leg 3 leverage-normalized vs parent)", "",
          "| book | win | γ | t_γ | lag21 | TV | α | α+TV stress | MDE TV | leg3 "
          "| dist? | PIT-QQQRES t_γ | pass |",
          "|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for _, r in books.iterrows():
        L.append(f"| {r.book} | {r.window[-2:]} | {r.gamma:+.2f} | {r.t_gamma:+.2f} "
                 f"| {r.t_gamma_lag21:+.2f} | {r.tv_ann:+.2%} | {r.alpha_ann:+.2%} "
                 f"| {r.alpha_plus_tv_stress:+.2%} | {r.mde_tv_ann:+.1%} "
                 f"| {'P' if r.leg3_pass else 'F'} "
                 f"| {'y' if r.distinguishable else 'NO'} "
                 f"| {r.t_gamma_pit_qqqres:+.2f} "
                 f"| {'**TIMING-POSITIVE**' if r.timing_positive else '—'} |")
    L += ["", "## Full-history M2T (IN-SAMPLE context — no claim may cite this)", "",
          "| book | γ | t_γ | TV ann |", "|---|---|---|---|"]
    for _, r in df[df.window == "full_IN-SAMPLE"].iterrows():
        L.append(f"| {r.book} | {r.gamma:+.2f} | {r.t_gamma:+.2f} | {r.tv_ann:+.2%} |")
    L += ["", "## Notes", "", "(story appended post-run)", ""]
    (OUT / "TIMING_GATE.md").write_text("\n".join(L))
    print("\n".join(L))
    stamp_run(track="attribution", variant="timing_gate",
              params={"model": "M2T", "t_weak": T_WEAK, "t_strong": T_STRONG,
                      "boot": {"n": N_BOOT, "block": BLOCK_MEAN, "seed": BOOT_SEED},
                      "verdict": verdict, "n_pos": n_pos,
                      "prereg": "timing-tm-2026-07-14.md"},
              n_trials=1)


if __name__ == "__main__":
    main()
