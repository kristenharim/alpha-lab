"""Agent 9 — incremental portfolio value of each watch-tier book beyond the frozen ensemble.

Reuses Agent 7's return-series reconstruction (compute_independence.book_returns /
factor_returns): daily net series per book from the exact runner path
(compute_book -> _heal_etfs -> harness.run on panel_2005.parquet, costs 2/10 bps).

Control  = frozen ensemble of the 4 PROMOTED books (vol_managed_qqq, vol_core_svxy,
           trend_vol_qqq, defensive_ensemble), equal-weight (equal-capital) AND
           inverse-vol (equal-risk). No retrospective allocation optimization.
Treatment = control + one candidate watch-tier book (dual_momentum_gold / _gem /
           momentum_concentrated) under the SAME pre-registered weighting rule.

Pre-registered primary method: block-bootstrap of the DIFFERENCE in net Sharpe
(equal-risk design, treatment scaled to control vol so we test skill not leverage),
P(delta Sharpe > 0). Promotion-to-Level-4 gate:
  incremental positive under the primary method, not concentrated in one period,
  survives realistic costs (series are already net), not merely added beta/leverage
  (compared at equal vol + marginal residual alpha vs control), still distinct after
  residualization (candidate residual-to-control alpha & correlation).

Run: .venv/bin/python research/independent_alpha/independence/compute_incremental.py
Writes incremental_metrics.csv + bootstrap.csv here; prints the scoreboard numbers.
"""
import sys
from pathlib import Path
import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from compute_independence import book_returns, factor_returns  # noqa: E402
sys.path.insert(0, str(HERE.parents[2] / "research" / "hunt2026"))
sys.path.insert(0, str(HERE.parents[2] / "scripts"))
import harness  # noqa: E402
from hunt_paper_run import BOOKS, SPECS  # noqa: E402

PROMOTED = ["vol_managed_qqq", "vol_core_svxy", "trend_vol_qqq", "defensive_ensemble"]
CANDIDATES = ["dual_momentum_gold", "dual_momentum_gem", "momentum_concentrated"]
ANN = np.sqrt(252)
RNG = np.random.default_rng(20260710)


def sharpe(r):
    s = r.std()
    return float(r.mean() / s * ANN) if s > 0 else 0.0


def max_dd(r):
    nav = (1 + r).cumprod()
    return float((nav / nav.cummax() - 1).min())


def worst_12m(r):
    nav = (1 + r).cumprod()
    roll = nav / nav.shift(252) - 1
    return float(roll.min())


def cagr(r):
    nav = (1 + r).cumprod()
    yrs = len(r) / 252
    return float(nav.iloc[-1] ** (1 / yrs) - 1)


def ew(cols, books):
    """equal-capital ensemble = simple mean of member net series."""
    return books[cols].mean(axis=1)


def inv_vol_w(cols, books):
    """equal-risk weights ~ 1/sigma (full-sample, fixed rule, NOT optimized)."""
    vol = books[cols].std()
    w = (1 / vol) / (1 / vol).sum()
    return w


def irp(cols, books):
    """inverse-vol (equal-risk) ensemble net series."""
    w = inv_vol_w(cols, books)
    return (books[cols] * w).sum(axis=1)


def scale_to(series, target_vol):
    """scale a return series to a target daily vol (leverage-neutralize)."""
    s = series.std()
    return series * (target_vol / s) if s > 0 else series


def factor_alpha(r, factors):
    X = np.column_stack([np.ones(len(r)), factors["SPY"].values, factors["QQQ"].values])
    coef, *_ = np.linalg.lstsq(X, r.values, rcond=None)
    resid = r.values - X @ coef
    # t-stat on alpha (per-day), annualize point estimate
    dof = len(r) - 3
    s2 = (resid @ resid) / dof
    xtx_inv = np.linalg.inv(X.T @ X)
    se_alpha = np.sqrt(s2 * xtx_inv[0, 0])
    t_alpha = coef[0] / se_alpha if se_alpha > 0 else 0.0
    return coef[0] * 252, float(t_alpha), coef[1], coef[2]


def ensemble_turnover(cols, books, weights):
    """weighted-average constituent daily turnover. ponytail: ignores cross-book
    rebalance drift (second order for a fixed-weight book), stated as such."""
    tvs = {}
    for name in cols:
        spec = harness.load_spec(SPECS / name)
        tvs[name] = harness.run(spec, books_panel)["avg_daily_turnover"]
    return float(sum(weights[c] * tvs[c] for c in cols))


def block_bootstrap_dsharpe(ctrl, treat, L=21, n=4000):
    """circular block bootstrap of paired (ctrl, treat) rows; treat pre-scaled to
    ctrl vol each replicate so we test skill, not leverage. Returns delta-Sharpe dist."""
    c = ctrl.values
    t = treat.values
    N = len(c)
    n_blocks = int(np.ceil(N / L))
    out = np.empty(n)
    for i in range(n):
        starts = RNG.integers(0, N, n_blocks)
        idx = (starts[:, None] + np.arange(L)[None, :]).ravel() % N
        idx = idx[:N]
        cb, tb = c[idx], t[idx]
        sc, st = cb.std(), tb.std()
        sh_c = cb.mean() / sc * ANN if sc > 0 else 0.0
        tb_scaled = tb * (sc / st) if st > 0 else tb  # equal-vol
        sh_t = tb_scaled.mean() / tb_scaled.std() * ANN if tb_scaled.std() > 0 else 0.0
        out[i] = sh_t - sh_c
    return out


def subperiod_dsharpe(ctrl, treat):
    """delta net Sharpe (equal-vol) per calendar-year-ish half + thirds, to check
    the increment is not concentrated in one period."""
    df = pd.DataFrame({"c": ctrl, "t": treat})
    res = {}
    n = len(df)
    for label, sl in [("H1", df.iloc[: n // 2]), ("H2", df.iloc[n // 2:]),
                      ("T1", df.iloc[: n // 3]), ("T2", df.iloc[n // 3: 2 * n // 3]),
                      ("T3", df.iloc[2 * n // 3:])]:
        cs, ts = sl["c"], sl["t"]
        tsc = scale_to(ts, cs.std())
        res[label] = sharpe(tsc) - sharpe(cs)
    return res


def residual_distinctness(cand, ctrl):
    """regress candidate on control; marginal residual alpha_ann + t, and correlation.
    tests 'still distinct after residualization' — does the candidate carry return the
    control does not already span?"""
    X = np.column_stack([np.ones(len(ctrl)), ctrl.values])
    coef, *_ = np.linalg.lstsq(X, cand.values, rcond=None)
    resid = cand.values - X @ coef
    dof = len(cand) - 2
    s2 = (resid @ resid) / dof
    se = np.sqrt(s2 * np.linalg.inv(X.T @ X)[0, 0])
    t = coef[0] / se if se > 0 else 0.0
    corr = float(np.corrcoef(cand.values, ctrl.values)[0, 1])
    return coef[0] * 252, float(t), coef[1], corr


# ---- build series ----
books_panel = pd.read_parquet(HERE.parents[2] / "research" / "hunt2026" / "panel_2005.parquet")
books = book_returns(books_panel)
factors = factor_returns(books_panel)
df = books.join(factors, how="inner").dropna()
active = (books.reindex(df.index).abs().sum(axis=1) > 0)
df = df.loc[active[active].index.min():]
# all-books-active window so candidate history is real for every candidate
allact = df[list(BOOKS)].abs().min(axis=1)  # not used; use per-candidate below
books = df[list(BOOKS)]
factors = df[["SPY", "QQQ"]]
print(f"window {df.index[0].date()}..{df.index[-1].date()} n={len(df)}")

rows = []
boot_rows = []
for design, ctrl_fn, w_fn in [("equal_capital", ew, None), ("equal_risk", irp, inv_vol_w)]:
    ctrl = ctrl_fn(PROMOTED, books)
    ctrl_full = ctrl  # over full window
    # control metrics
    ta = factor_alpha(ctrl_full, factors)
    ctrl_metrics = dict(design=design, book="CONTROL(4promoted)",
                        sharpe=sharpe(ctrl_full), cagr=cagr(ctrl_full),
                        ann_vol=ctrl_full.std() * ANN, max_dd=max_dd(ctrl_full),
                        worst_12m=worst_12m(ctrl_full), alpha_ann=ta[0], alpha_t=ta[1],
                        beta_spy=ta[2], beta_qqq=ta[3],
                        d_sharpe=0.0, d_ret_eqvol=0.0, d_max_dd=0.0, d_worst12m=0.0,
                        boot_p_gt0=np.nan, boot_lo=np.nan, boot_hi=np.nan,
                        resid_alpha_ann=np.nan, resid_alpha_t=np.nan, corr_to_ctrl=np.nan)
    rows.append(ctrl_metrics)

    for cand in CANDIDATES:
        cols = PROMOTED + [cand]
        treat = ctrl_fn(cols, books)
        # equal-vol scaled treatment for fair Sharpe/return comparison
        treat_ev = scale_to(treat, ctrl.std())
        ta_t = factor_alpha(treat, factors)
        d_sh = sharpe(treat) - sharpe(ctrl)  # Sharpe is scale-invariant
        d_ret = cagr(treat_ev) - cagr(ctrl)  # return at equal vol
        d_dd = max_dd(treat) - max_dd(ctrl)
        d_w12 = worst_12m(treat) - worst_12m(ctrl)
        boot = block_bootstrap_dsharpe(ctrl, treat)
        p_gt0 = float((boot > 0).mean())
        lo, hi = np.percentile(boot, [2.5, 97.5])
        ra, rt, rb, rc = residual_distinctness(books[cand], ctrl)
        sub = subperiod_dsharpe(ctrl, treat)
        w = w_fn(cols, books) if w_fn else pd.Series(1 / len(cols), index=cols)
        turn = ensemble_turnover(cols, books, w)
        ctrl_w = (w_fn(PROMOTED, books) if w_fn else pd.Series(1 / len(PROMOTED), index=PROMOTED))
        turn_ctrl = ensemble_turnover(PROMOTED, books, ctrl_w)
        rows.append(dict(design=design, book=cand,
                         sharpe=sharpe(treat), cagr=cagr(treat_ev),
                         ann_vol=treat.std() * ANN, max_dd=max_dd(treat),
                         worst_12m=worst_12m(treat), alpha_ann=ta_t[0], alpha_t=ta_t[1],
                         beta_spy=ta_t[2], beta_qqq=ta_t[3],
                         d_sharpe=d_sh, d_ret_eqvol=d_ret, d_max_dd=d_dd, d_worst12m=d_w12,
                         boot_p_gt0=p_gt0, boot_lo=lo, boot_hi=hi,
                         resid_alpha_ann=ra, resid_alpha_t=rt, corr_to_ctrl=rc,
                         d_turnover=turn - turn_ctrl,
                         sub_H1=sub["H1"], sub_H2=sub["H2"],
                         sub_T1=sub["T1"], sub_T2=sub["T2"], sub_T3=sub["T3"]))
        boot_rows.append(dict(design=design, book=cand, mean=boot.mean(),
                              p_gt0=p_gt0, ci_lo=lo, ci_hi=hi))
        print(f"[{design}] +{cand}: dSharpe={d_sh:+.3f} dRet@eqvol={d_ret:+.4f} "
              f"dMaxDD={d_dd:+.3f} P(dSh>0)={p_gt0:.2f} CI[{lo:+.2f},{hi:+.2f}] "
              f"residAlpha={ra:+.3f}(t={rt:+.1f}) corr={rc:.2f} "
              f"sub[H1={sub['H1']:+.2f},H2={sub['H2']:+.2f}]")

out = pd.DataFrame(rows)
out.to_csv(HERE / "incremental_metrics.csv", index=False)
pd.DataFrame(boot_rows).to_csv(HERE / "bootstrap.csv", index=False)
print("\nwrote incremental_metrics.csv, bootstrap.csv")

# --- self-check: adding a book that IS the control must give ~0 increment ---
_ctrl = ew(PROMOTED, books)
_treat = ew(PROMOTED + ["vol_managed_qqq"], books)  # duplicate a member
_b = block_bootstrap_dsharpe(_ctrl, _treat, n=500)
assert abs(sharpe(_treat) - sharpe(_ctrl)) < 0.15, "duplicate-member sanity: dSharpe should be tiny"
print(f"self-check ok: dup-member dSharpe={sharpe(_treat)-sharpe(_ctrl):+.3f} (≈0 expected)")
