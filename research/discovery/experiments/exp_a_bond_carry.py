"""EXP-A — Bond-carry predictability (Stage-1 MEASUREMENT, no portfolio).

Frozen prereg: research/discovery/prereg/EXP-A-bond-carry-predictability.md
Runs the frozen carry formula, tests predictability of forward duration-relative
returns, runs the duration/rate/trend kill-controls, builds a carry-z ladder daily
return, and scores it through the frozen orthogonality benchmark.

MEASUREMENT ONLY. Builds no promotable portfolio; touches no control-plane file.
Run: .venv/bin/python research/discovery/experiments/exp_a_bond_carry.py
"""
from __future__ import annotations
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

ROOT = Path(__file__).resolve().parents[3]
DATA = ROOT / "research" / "discovery" / "data" / "state_aligned.parquet"
PANEL = ROOT / "research" / "hunt2026" / "panel_2005.parquet"
OUT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "research" / "discovery"))
from orthogonality_benchmark import score_candidate  # noqa: E402

BUCKETS = ["SHY", "IEF", "TLT"]
# approx modified duration of each ETF (yrs) — static, for the mechanical-duration control only
MOD_DUR = {"SHY": 1.8, "IEF": 7.5, "TLT": 17.0}
COST_BPS_SIDE = 2.0  # ETF round-trip ~2 bps/side


def newey_west_t(y, X, L=None):
    """OLS coef + Newey-West (Bartlett) HAC t-stats and 95% CI. X includes intercept col."""
    y = np.asarray(y, float); X = np.asarray(X, float)
    n, k = X.shape
    if L is None:
        L = int(np.floor(4 * (n / 100.0) ** (2.0 / 9.0)))  # Newey-West 1994 rule
    XtX_inv = np.linalg.inv(X.T @ X)
    beta = XtX_inv @ (X.T @ y)
    u = y - X @ beta
    # HAC meat
    S = (X * u[:, None]).T @ (X * u[:, None])
    for l in range(1, L + 1):
        w = 1.0 - l / (L + 1.0)
        Xu = X * u[:, None]
        G = Xu[l:].T @ Xu[:-l]
        S += w * (G + G.T)
    cov = XtX_inv @ S @ XtX_inv
    se = np.sqrt(np.diag(cov))
    t = beta / se
    return beta, se, t, L


def build():
    sa = pd.read_parquet(DATA)
    panel = pd.read_parquet(PANEL)
    close = panel["close"][BUCKETS + ["SPY", "QQQ"]].copy()

    # --- frozen carry per bucket (yield pts, % annual). sa is already avail-lagged. ---
    carry = pd.DataFrame(index=sa.index)
    carry["SHY"] = (sa["DGS2"] - sa["DFF"]) + (sa["DGS2"] - sa["DGS3MO"]) / 1.75
    carry["IEF"] = (sa["DGS10"] - sa["DFF"]) + (sa["DGS10"] - sa["DGS5"]) / 5.0
    carry["TLT"] = (sa["DGS30"] - sa["DFF"]) + (sa["DGS30"] - sa["DGS10"]) / 20.0
    carry = carry.reindex(close.index).ffill()

    ret = close.pct_change()  # daily close-to-close simple returns
    return sa, close, carry, ret


def month_ends(idx):
    return pd.Series(idx, index=idx).groupby([idx.year, idx.month]).last().values


def fwd_return(close_col, dates, h):
    """simple return close[t]->close[t+h] for each decision date t (positional)."""
    pos = {d: i for i, d in enumerate(close_col.index)}
    vals = close_col.values
    out = {}
    for d in dates:
        i = pos[d]
        if i + h < len(vals):
            out[d] = vals[i + h] / vals[i] - 1.0
    return pd.Series(out)


def main():
    sa, close, carry, ret = build()
    me = pd.DatetimeIndex(month_ends(close.index))
    me = me[me.isin(close.index)]

    # cross-sectional monthly z-score of carry across the 3 buckets
    cm = carry.loc[me, BUCKETS]
    z = cm.sub(cm.mean(axis=1), axis=0).div(cm.std(axis=1, ddof=0), axis=0)

    # ---------- STEP 1: pooled predictive regression, forward 21d ----------
    rows = []
    for h in (5, 21, 63):
        fwd = {b: fwd_return(close[b], me, h) for b in BUCKETS}
        recs = []
        for b in BUCKETS:
            f = fwd[b]
            common = z.index.intersection(f.index)
            df = pd.DataFrame({"z": z[b].loc[common], "r": f.loc[common], "bucket": b,
                               "date": common, "dur": MOD_DUR[b]})
            recs.append(df)
        pool = pd.concat(recs).dropna()
        X = np.column_stack([np.ones(len(pool)), pool["z"].values])
        beta, se, t, L = newey_west_t(pool["r"].values, X)
        ci = (beta[1] - 1.96 * se[1], beta[1] + 1.96 * se[1])
        rows.append({"h": h, "n": len(pool), "coef_z": beta[1], "t_z": t[1],
                     "ci_lo": ci[0], "ci_hi": ci[1], "nw_lag": L})
    decay = pd.DataFrame(rows)

    # primary = 21d pool, reused for controls + IC + eras
    h = 21
    fwd = {b: fwd_return(close[b], me, h) for b in BUCKETS}
    dgs10 = sa["DGS10"].reindex(close.index).ffill()
    # realized forward rate change over the holding window (attribution control only)
    pos = {d: i for i, d in enumerate(close.index)}
    def fwd_ddgs10(d):
        i = pos[d]
        return dgs10.values[i + h] - dgs10.values[i] if i + h < len(dgs10) else np.nan
    # 200d SMA trend state per bucket at decision date
    sma200 = close.rolling(200).mean()
    recs = []
    for b in BUCKETS:
        f = fwd[b]
        common = z.index.intersection(f.index)
        trend = np.sign((close[b].loc[common] - sma200[b].loc[common]).values)
        recs.append(pd.DataFrame({
            "z": z[b].loc[common].values, "r": f.loc[common].values, "bucket": b,
            "date": common, "dur": MOD_DUR[b],
            "ddgs10": [fwd_ddgs10(d) for d in common], "trend": trend}))
    pool = pd.concat(recs).dropna().reset_index(drop=True)

    def reg(cols):
        X = np.column_stack([np.ones(len(pool))] + [pool[c].values for c in cols])
        beta, se, t, L = newey_west_t(pool["r"].values, X)
        return dict(zip(["const"] + cols, beta)), dict(zip(["const"] + cols, t)), L

    m1_b, m1_t, _ = reg(["z"])
    m2_b, m2_t, _ = reg(["z", "dur"])
    # mechanical-duration: realized rate move scaled by static duration (dur*ddgs10), + trend
    pool["dur_ddgs10"] = pool["dur"] * pool["ddgs10"]
    m3_b, m3_t, _ = reg(["z", "dur_ddgs10", "trend"])

    # ---------- monthly cross-sectional rank IC (3 buckets) ----------
    ics = []
    for d in z.index:
        zz = z.loc[d, BUCKETS].values
        rr = np.array([fwd[b].get(d, np.nan) for b in BUCKETS])
        if np.isfinite(zz).all() and np.isfinite(rr).all():
            ics.append(stats.spearmanr(zz, rr).correlation)
    ics = np.array([x for x in ics if np.isfinite(x)])
    ic_mean = ics.mean(); ic_t = ic_mean / (ics.std(ddof=1) / np.sqrt(len(ics)))

    # ---------- stability by era ----------
    eras = {"2005-09": ("2005", "2009"), "2010-14": ("2010", "2014"),
            "2015-19": ("2015", "2019"), "2020-26": ("2020", "2026")}
    era_rows = []
    for name, (a, bb) in eras.items():
        sub = pool[(pool["date"] >= f"{a}-01-01") & (pool["date"] <= f"{bb}-12-31")]
        if len(sub) > 10:
            X = np.column_stack([np.ones(len(sub)), sub["z"].values])
            beta, se, t, L = newey_west_t(sub["r"].values, X)
            sic = ics  # era IC
            m = (z.index >= f"{a}-01-01") & (z.index <= f"{bb}-12-31")
            era_ic = np.array([stats.spearmanr(z.loc[d, BUCKETS].values,
                               [fwd[b].get(d, np.nan) for b in BUCKETS]).correlation
                               for d in z.index[m]
                               if np.isfinite([fwd[b].get(d, np.nan) for b in BUCKETS]).all()])
            era_rows.append({"era": name, "n": len(sub), "coef_z": beta[1], "t_z": t[1],
                             "ic_mean": np.nanmean(era_ic)})
    era_df = pd.DataFrame(era_rows)

    # ---------- holdout: pre-2024-07 vs last 24m ----------
    ho = {}
    for name, msk in [("pre_2024_07", pool["date"] < "2024-07-01"),
                      ("holdout_24m", pool["date"] >= "2024-07-01")]:
        sub = pool[msk]
        X = np.column_stack([np.ones(len(sub)), sub["z"].values])
        beta, se, t, L = newey_west_t(sub["r"].values, X)
        ho[name] = {"n": len(sub), "coef_z": beta[1], "t_z": t[1]}

    # ---------- carry-z ladder daily return (dollar-neutral, gross=1) ----------
    # weights = z / sum|z| per month-end, held to next rebalance; daily r = sum w_i r_i
    w = z[BUCKETS].div(z[BUCKETS].abs().sum(axis=1), axis=0)
    w_daily = w.reindex(close.index).ffill().shift(1)  # decide at close t, earn t+1
    sleeve_gross = (w_daily[BUCKETS] * ret[BUCKETS]).sum(axis=1)
    # turnover + costs: |Δw| summed on rebalance days
    turn = w.diff().abs().sum(axis=1)
    cost = (turn * COST_BPS_SIDE / 1e4).reindex(close.index).fillna(0.0)
    sleeve = (sleeve_gross - cost).dropna()
    ann_turn = turn.mean() * 12  # monthly rebalances -> annualized one-way turnover

    # duration/equity exposure of the sleeve
    def ols_t(y, Xcols):
        X = np.column_stack([np.ones(len(y))] + Xcols)
        beta, se, t, L = newey_west_t(y.values, X)
        return beta, t
    eq = pd.DataFrame({"s": sleeve, "SPY": ret["SPY"], "QQQ": ret["QQQ"]}).dropna()
    beq, teq = ols_t(eq["s"], [eq["SPY"].values, eq["QQQ"].values])
    dd10 = dgs10.diff().reindex(sleeve.index)
    tlt_r = ret["TLT"].reindex(sleeve.index)
    d2 = pd.DataFrame({"s": sleeve, "dd10": dd10, "tlt": tlt_r}).dropna()
    bdur, tdur = ols_t(d2["s"], [d2["tlt"].values])
    bdd, tdd = ols_t(d2["s"], [d2["dd10"].values])

    # sleeve performance
    def sharpe(r): return r.mean() / r.std() * np.sqrt(252)
    perf = {"ann_ret": sleeve.mean() * 252, "ann_vol": sleeve.std() * np.sqrt(252),
            "sharpe": sharpe(sleeve), "ann_turnover_1way": ann_turn,
            "beta_SPY": beq[1], "t_SPY": teq[1], "beta_QQQ": beq[2], "t_QQQ": teq[2],
            "beta_TLT": bdur[1], "t_TLT": tdur[1], "beta_dDGS10": bdd[1], "t_dDGS10": tdd[1]}

    # ---------- STEP 2: orthogonality ----------
    orth = score_candidate(sleeve.rename("carry_ladder"), "exp_a_carry_ladder")

    # ---- bug-check: reproduce 21d pooled coef a 2nd way (pure numpy lstsq, no HAC) ----
    Xc = np.column_stack([np.ones(len(pool)), pool["z"].values])
    bc = np.linalg.lstsq(Xc, pool["r"].values, rcond=None)[0][1]

    # ---- persist ----
    decay.to_csv(OUT / "exp_a_horizon_decay.csv", index=False)
    era_df.to_csv(OUT / "exp_a_era_stability.csv", index=False)
    pd.DataFrame([perf]).to_csv(OUT / "exp_a_sleeve_perf.csv", index=False)
    pd.DataFrame([orth]).to_csv(OUT / "exp_a_orthogonality.csv", index=False)
    sleeve.to_frame("carry_ladder_ret").to_csv(OUT / "exp_a_sleeve_daily.csv")

    print("=" * 70)
    print("EXP-A BOND CARRY — MEASUREMENT")
    print(f"decision months: {len(z)}  pooled 21d obs: {len(pool)}  sample {close.index.min().date()}..{close.index.max().date()}")
    print("\n[carry sample tail, yield pts]"); print(carry.loc[me].tail(3).round(3).to_string())
    print("\n[STEP1] horizon decay (pooled fwd ret ~ carry_z, NW-t):")
    print(decay.round(4).to_string(index=False))
    print(f"\n  bug-check 21d coef via plain lstsq = {bc:.6f}  (NW coef = {m1_b['z']:.6f})")
    print(f"\n  M1 r21 ~ z            : coef_z={m1_b['z']:.5f}  t={m1_t['z']:.2f}")
    print(f"  M2 r21 ~ z+dur        : coef_z={m2_b['z']:.5f}  t={m2_t['z']:.2f}   dur t={m2_t['dur']:.2f}")
    print(f"  M3 r21 ~ z+dur*ddgs10+trend: coef_z={m3_b['z']:.5f}  t={m3_t['z']:.2f}  dur*dr t={m3_t['dur_ddgs10']:.2f}  trend t={m3_t['trend']:.2f}")
    print(f"\n  monthly rank IC (3 buckets): mean={ic_mean:.4f}  t={ic_t:.2f}  n_months={len(ics)}")
    print("\n[eras]"); print(era_df.round(4).to_string(index=False))
    print("\n[holdout]"); [print(f"  {k}: {v}") for k, v in ho.items()]
    print("\n[STEP1 duration/equity checks on the sleeve]")
    for k, v in perf.items(): print(f"  {k:20s} {v: .4f}")
    print("\n[STEP2 orthogonality]")
    for k, v in orth.items(): print(f"  {k:20s} {v}")


if __name__ == "__main__":
    main()
