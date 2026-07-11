"""Agent 9 — return-source decomposition of the 7 frozen books.

Read-only vs repo; writes CSVs into redteam/2026-07-10/agent9/.
Uses the frozen harness P&L convention so numbers are comparable to results/.
"""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[3]          # ~/projects/alpha-lab
H26 = ROOT / "research" / "hunt2026"
OUT = Path(__file__).parent
sys.path.insert(0, str(H26))
import harness  # noqa: E402

BOOKS = ["vol_managed_qqq", "vol_core_svxy", "trend_vol_qqq", "defensive_ensemble",
         "dual_momentum_gold", "dual_momentum_gem", "momentum_concentrated"]
CUT = harness.META["cut"]          # 2025-07-10 (holdout start)
LONG_START = "2008-01-01"          # panel_2005 with GFC included


def const_spec(weights: dict):
    class _S:
        @staticmethod
        def target_weights(p):
            c = p["close"]
            W = pd.DataFrame(0.0, index=c.index, columns=c.columns)
            for t, w in weights.items():
                W[t] = np.where(c[t].notna(), w, 0.0)
            return W
    return _S


def nw_tstat(y, lag=5):
    """Newey-West t-stat of the mean of y."""
    y = np.asarray(y, float)
    y = y[~np.isnan(y)]
    n = len(y)
    m = y.mean()
    e = y - m
    s = e @ e / n
    for L in range(1, lag + 1):
        w = 1 - L / (lag + 1)
        s += 2 * w * (e[:-L] @ e[L:]) / n
    return m / np.sqrt(s / n)


def ols(y, x):
    """y = a + b x. Returns beta, ann alpha, alpha NW t, R2, up/down beta."""
    df = pd.concat({"y": y, "x": x}, axis=1).dropna()
    b = df["y"].cov(df["x"]) / df["x"].var()
    resid = df["y"] - b * df["x"]
    a = resid.mean()
    r2 = 1 - ((resid - a) ** 2).sum() / ((df["y"] - df["y"].mean()) ** 2).sum()
    up = df[df["x"] > 0]
    dn = df[df["x"] < 0]
    bu = up["y"].cov(up["x"]) / up["x"].var()
    bd = dn["y"].cov(dn["x"]) / dn["x"].var()
    return dict(beta=b, alpha_ann=a * 252, alpha_t=nw_tstat(resid), r2=r2,
                beta_up=bu, beta_dn=bd)


def stats_row(r):
    r = r.dropna()
    nav = (1 + r).cumprod()
    yrs = len(r) / 252
    return dict(ann_ret=(nav.iloc[-1]) ** (1 / yrs) - 1,
                ann_vol=r.std() * np.sqrt(252),
                sharpe=r.mean() / r.std() * np.sqrt(252) if r.std() > 0 else 0,
                max_dd=(nav / nav.cummax() - 1).min())


def run_window(panel, start, end=None, label=""):
    res = {}
    for b in BOOKS:
        mod = harness.load_spec(H26 / "specs" / b)
        r = harness.run(mod, panel, start=start, end=end)
        res[b] = r
    spy = harness.run(const_spec({"SPY": 1.0}), panel, start=start, end=end)
    qqq = harness.run(const_spec({"QQQ": 1.0}), panel, start=start, end=end)
    b6040 = harness.run(const_spec({"SPY": 0.6, "BIL": 0.4}), panel, start=start, end=end)
    return res, spy, qqq, b6040


def held_weights(panel, spec_dir, start, end=None):
    """Held (t-1 lagged, gross-scaled) weights over window, mirroring harness."""
    mod = harness.load_spec(spec_dir)
    W = mod.target_weights(panel).astype(float).fillna(0.0)
    g = W.abs().sum(axis=1)
    W = W.mul((harness.MAX_GROSS / g).clip(upper=1.0).fillna(1.0), axis=0)
    held = W.shift(1)
    idx = held.index
    if start is not None:
        idx = idx[idx > pd.Timestamp(start)]
    if end is not None:
        idx = idx[idx <= pd.Timestamp(end)]
    return held.reindex(idx)


def analyze(panel, start, end, label):
    res, spy, qqq, b6040 = run_window(panel, start, end)
    rets = pd.DataFrame({b: res[b]["net_daily"] for b in BOOKS})
    rets["SPY"] = spy["net_daily"]
    rets["QQQ"] = qqq["net_daily"]
    rets["SPY60_BIL40"] = b6040["net_daily"]
    rets.to_csv(OUT / f"net_daily_{label}.csv")

    rows = []
    for b in BOOKS:
        r = rets[b]
        st = stats_row(r)
        o_spy = ols(r, rets["SPY"])
        o_qqq = ols(r, rets["QQQ"])
        # exposure-matched static control in the book's dominant asset
        asset = "QQQ" if "qqq" in b or b in ("vol_managed_qqq", "vol_core_svxy") else "SPY"
        avg_exp = res[b]["avg_gross_exposure"]
        ctrl = harness.run(const_spec({asset: avg_exp}), panel, start=start, end=end)
        cr = ctrl["net_daily"]
        cst = stats_row(cr)
        rows.append(dict(book=b, window=label, **st,
                         beta_spy=o_spy["beta"], alpha_spy_ann=o_spy["alpha_ann"],
                         alpha_spy_t=o_spy["alpha_t"], r2_spy=o_spy["r2"],
                         beta_up_spy=o_spy["beta_up"], beta_dn_spy=o_spy["beta_dn"],
                         beta_qqq=o_qqq["beta"], alpha_qqq_ann=o_qqq["alpha_ann"],
                         alpha_qqq_t=o_qqq["alpha_t"], r2_qqq=o_qqq["r2"],
                         ctrl_asset=asset, avg_exp=avg_exp,
                         ctrl_ann_ret=cst["ann_ret"], ctrl_sharpe=cst["sharpe"],
                         ctrl_max_dd=cst["max_dd"],
                         excess_vs_ctrl_ann=st["ann_ret"] - cst["ann_ret"],
                         sharpe_minus_ctrl=st["sharpe"] - cst["sharpe"]))
    beta_df = pd.DataFrame(rows)
    beta_df.to_csv(OUT / f"beta_alpha_{label}.csv", index=False)

    # correlation matrix + effective N
    C = rets[BOOKS].corr()
    C.to_csv(OUT / f"corr_{label}.csv")
    lam = np.linalg.eigvalsh(C.values)
    neff = lam.sum() ** 2 / (lam ** 2).sum()
    avg_pair = (C.values.sum() - len(BOOKS)) / (len(BOOKS) * (len(BOOKS) - 1))

    # tail: worst-decile SPY days
    q = rets["SPY"].quantile(0.10)
    bad = rets[rets["SPY"] <= q]
    Cb = bad[BOOKS].corr()
    Cb.to_csv(OUT / f"corr_tail_{label}.csv")
    lam_b = np.linalg.eigvalsh(Cb.values)
    neff_b = lam_b.sum() ** 2 / (lam_b ** 2).sum()
    avg_pair_b = (Cb.values.sum() - len(BOOKS)) / (len(BOOKS) * (len(BOOKS) - 1))
    tail = pd.DataFrame({
        "mean_on_worst10pct_spy_days": bad[BOOKS + ["SPY", "QQQ"]].mean(),
        "ann_all_days": rets[BOOKS + ["SPY", "QQQ"]].mean() * 252})
    tail.to_csv(OUT / f"tail_{label}.csv")

    # equal-weight 7-book portfolio
    port = rets[BOOKS].mean(axis=1)
    o = ols(port, rets["SPY"])
    pst = stats_row(port)
    summary = dict(window=label, n_days=len(rets.dropna(how="all")),
                   avg_pairwise_corr=avg_pair, eff_n_books=neff,
                   avg_pairwise_corr_tail=avg_pair_b, eff_n_books_tail=neff_b,
                   port_beta_spy=o["beta"], port_r2_spy=o["r2"],
                   port_alpha_ann=o["alpha_ann"], port_alpha_t=o["alpha_t"],
                   port_beta_up=o["beta_up"], port_beta_dn=o["beta_dn"],
                   port_ann_ret=pst["ann_ret"], port_sharpe=pst["sharpe"],
                   port_max_dd=pst["max_dd"],
                   spy_ann_ret=stats_row(rets["SPY"])["ann_ret"],
                   qqq_ann_ret=stats_row(rets["QQQ"])["ann_ret"])
    return rets, beta_df, C, summary


def timing_decomp(panel, start, end, label):
    """gross return = w_bar*r (static leverage) + (w_t-w_bar)*r (timing), per book,
    computed on the book's held weights vs its own assets."""
    close = panel["close"]
    rets_assets = close.pct_change(fill_method=None)
    rows = []
    for b in BOOKS:
        held = held_weights(panel, H26 / "specs" / b, start, end)
        cols = [c for c in held.columns if held[c].abs().sum() > 0]
        held = held[cols]
        ra = rets_assets[cols].reindex(held.index)
        gross = (held * ra).sum(axis=1, min_count=1).fillna(0.0)
        wbar = held.mean()
        static = (ra * wbar).sum(axis=1, min_count=1).fillna(0.0)
        timing = gross - static
        rows.append(dict(book=b, window=label,
                         gross_ann=gross.mean() * 252,
                         static_ann=static.mean() * 252,
                         timing_ann=timing.mean() * 252,
                         timing_t=nw_tstat(timing),
                         timing_share=timing.mean() / gross.mean() if gross.mean() else np.nan))
    df = pd.DataFrame(rows)
    df.to_csv(OUT / f"timing_decomp_{label}.csv", index=False)
    return df


def overlap(panel, start, end, label):
    """Aggregate |held weight| by ticker across the 7 books (equal-capital)."""
    agg = {}
    same_asset = {}
    helds = {b: held_weights(panel, H26 / "specs" / b, start, end) for b in BOOKS}
    for b, held in helds.items():
        m = held.abs().mean()
        for t, v in m[m > 0.005].items():
            agg.setdefault(t, {})[b] = v
    df = pd.DataFrame(agg).T.fillna(0.0) / len(BOOKS)  # equal capital / 7
    df["TOTAL_acct_frac"] = df.sum(axis=1)
    df = df.sort_values("TOTAL_acct_frac", ascending=False)
    df.to_csv(OUT / f"overlap_{label}.csv")
    # gold vs gem same-holding fraction
    hg, he = helds["dual_momentum_gold"], helds["dual_momentum_gem"]
    common_days = hg.dropna(how="all").index.intersection(he.dropna(how="all").index)
    g_pick = hg.loc[common_days].idxmax(axis=1).where(hg.loc[common_days].max(axis=1) > 0)
    e_pick = he.loc[common_days].idxmax(axis=1).where(he.loc[common_days].max(axis=1) > 0)
    same = (g_pick == e_pick).mean()
    return df, float(same)


def svxy_sleeve(panel, start, end):
    """vol_core_svxy minus its own core (60/40 vol-scaled, no SVXY) — sleeve contribution."""
    class _Core:
        @staticmethod
        def target_weights(p):
            close = p["close"]
            W = pd.DataFrame(0.0, index=close.index, columns=["QQQ", "SPY"])
            for tkr, split in {"QQQ": 0.6, "SPY": 0.4}.items():
                rv = close[tkr].pct_change().rolling(21).std() * np.sqrt(252)
                W[tkr] = split * (0.25 / rv).clip(upper=2.0)
            W = W.fillna(0.0)
            g = W.abs().sum(axis=1)
            return W.mul((2.0 / g).clip(upper=1.0).fillna(1.0), axis=0)
    core = harness.run(_Core, panel, start=start, end=end)
    full = harness.run(harness.load_spec(H26 / "specs" / "vol_core_svxy"), panel, start=start, end=end)
    return {"full_ann": stats_row(full["net_daily"])["ann_ret"],
            "core_ann": stats_row(core["net_daily"])["ann_ret"],
            "full_sharpe": stats_row(full["net_daily"])["sharpe"],
            "core_sharpe": stats_row(core["net_daily"])["sharpe"],
            "full_dd": stats_row(full["net_daily"])["max_dd"],
            "core_dd": stats_row(core["net_daily"])["max_dd"]}


def main():
    out = {}
    print("== holdout window (blind year) ==")
    panel_f = harness.load_full()
    rets_h, beta_h, C_h, sum_h = analyze(panel_f, CUT, None, "holdout")
    td_h = timing_decomp(panel_f, CUT, None, "holdout")
    ov_h, same_h = overlap(panel_f, CUT, None, "holdout")
    out["holdout"] = sum_h
    out["gold_gem_same_holding_holdout"] = same_h
    out["svxy_sleeve_holdout"] = svxy_sleeve(panel_f, CUT, None)

    print("== long window 2008-2026 (panel_2005) ==")
    panel_l = pd.read_parquet(H26 / "panel_2005.parquet")
    rets_l, beta_l, C_l, sum_l = analyze(panel_l, LONG_START, None, "long")
    td_l = timing_decomp(panel_l, LONG_START, None, "long")
    ov_l, same_l = overlap(panel_l, LONG_START, None, "long")
    out["long"] = sum_l
    out["gold_gem_same_holding_long"] = same_l
    out["svxy_sleeve_long"] = svxy_sleeve(panel_l, LONG_START, None)

    (OUT / "summary.json").write_text(json.dumps(out, indent=2, default=float))
    for name, df in [("beta_holdout", beta_h), ("beta_long", beta_l),
                     ("timing_holdout", td_h), ("timing_long", td_l)]:
        print(f"\n--- {name} ---")
        print(df.to_string(index=False))
    print("\n--- corr holdout ---\n", C_h.round(2).to_string())
    print("\n--- corr long ---\n", C_l.round(2).to_string())
    print("\n--- summary ---\n", json.dumps(out, indent=2, default=float))
    print("\n--- top overlap holdout (acct frac) ---\n", ov_h.head(12).round(3).to_string())


if __name__ == "__main__":
    main()
