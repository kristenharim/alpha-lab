"""Agent 7 regime & concentration analysis. Read-only vs repo; outputs to agent7/.

Implements exactly the metrics predeclared in PREDECLARED_REGIMES.md.
Run: cd research/hunt2026 && ../../.venv/bin/python ../../redteam/2026-07-10/agent7/regime_analysis.py
"""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HUNT = Path(__file__).resolve().parents[3] / "research" / "hunt2026"
sys.path.insert(0, str(HUNT))
import harness  # frozen, checksum-verified

OUT = Path(__file__).parent
BOOKS = ["vol_managed_qqq", "vol_core_svxy", "trend_vol_qqq", "defensive_ensemble",
         "dual_momentum_gold", "dual_momentum_gem", "momentum_concentrated"]
BENCH = {"vol_managed_qqq": "QQQ", "vol_core_svxy": "QQQ", "trend_vol_qqq": "QQQ",
         "defensive_ensemble": "6040", "dual_momentum_gold": "SPY",
         "dual_momentum_gem": "SPY", "momentum_concentrated": "SPY"}
W1 = ("2025-07-10", "2026-07-10")
W2 = ("2021-07-10", "2026-07-10")


def const_weight_bench(panel, wdict, start, end):
    class _B:
        @staticmethod
        def target_weights(p):
            c = p["close"]
            W = pd.DataFrame(0.0, index=c.index, columns=c.columns)
            for t, w in wdict.items():
                W[t] = w
            return W
    return harness.run(_B, panel, start, end)


def daily_gross_exposure(spec_mod, panel):
    # replicate harness weight pipeline to get per-day held gross exposure
    W = spec_mod.target_weights(panel).astype(float).fillna(0.0)
    gross_exp = W.abs().sum(axis=1)
    scale = (harness.MAX_GROSS / gross_exp).clip(upper=1.0).fillna(1.0)
    W = W.mul(scale, axis=0)
    return W.shift(1).abs().sum(axis=1)


def build_regimes(panel):
    c = panel["close"]
    spy, vix = c["SPY"], c["^VIX"]
    lab = pd.DataFrame(index=c.index)
    lab["R1"] = np.where(spy >= spy.rolling(200).mean(), "bull", "bear")
    lab["R2"] = np.select([vix < 20, vix < 30], ["low", "high"], default="crisis")
    lab["R3"] = np.where(c["IEF"].pct_change(63) > 0, "falling", "rising")
    lab["R4"] = np.where(c["TIP"].pct_change(126) - c["IEF"].pct_change(126) > 0,
                         "rising_be", "falling_be")
    lab["R5"] = np.where(c["HYG"].pct_change(63) - c["IEF"].pct_change(63) > 0,
                         "risk_on", "risk_off")
    lab["R6"] = np.where(np.sign(spy.pct_change(63)) == np.sign(spy.pct_change(252)),
                         "persistent", "choppy")
    return lab.shift(1)  # state at close t labels return of t+1


def stress_episodes(panel, start, end):
    vix = panel["close"]["^VIX"]
    idx = vix.index
    crisis = (vix >= 30)
    # pad +-5 trading days, merge gaps < 10
    pos = np.where(crisis.values)[0]
    if len(pos) == 0:
        return []
    eps, s, e = [], pos[0], pos[0]
    for p in pos[1:]:
        if p - e < 10 + 10:  # gap incl padding overlap
            e = p
        else:
            eps.append((s, e)); s, e = p, p
    eps.append((s, e))
    out = []
    for s, e in eps:
        a, b = idx[max(0, s - 5)], idx[min(len(idx) - 1, e + 5)]
        if b > pd.Timestamp(start) and a <= pd.Timestamp(end):
            out.append((a, b))
    return out


def dd_window(net):
    nav = (1 + net).cumprod()
    dd = nav / nav.cummax() - 1
    trough = dd.idxmin()
    peak = nav.loc[:trough].idxmax()
    return peak, trough, float(dd.min())


def regime_table(net, bench_net, lab, window_name, book):
    rel = net - bench_net
    logr = np.log1p(net)
    rows = []
    peak, trough, mdd = dd_window(net)
    dd_days = net.loc[peak:trough]
    dd_neg_total = np.log1p(dd_days[dd_days < 0]).sum()
    for R in ["R1", "R2", "R3", "R4", "R5", "R6"]:
        for v in lab[R].reindex(net.index).dropna().unique():
            m = lab[R].reindex(net.index) == v
            n = int(m.sum())
            seg, segrel = net[m], rel[m]
            dd_seg = dd_days[(lab[R].reindex(dd_days.index) == v) & (dd_days < 0)]
            rows.append({
                "book": book, "window": window_name, "regime": f"{R}:{v}",
                "days": n, "pct_days": round(100 * n / len(net), 1),
                "sum_log_net": round(float(np.log1p(seg).sum()), 4),
                "sum_rel": round(float(segrel.sum()), 4),
                "sharpe": (round(float(seg.mean() / seg.std() * np.sqrt(252)), 2)
                           if n >= 15 and seg.std() > 0 else None),
                "avg_gross": None,  # filled by caller
                "dd_share": (round(float(np.log1p(dd_seg).sum() / dd_neg_total), 2)
                             if dd_neg_total < 0 else 0.0),
            })
    return pd.DataFrame(rows), (peak, trough, mdd)


def concentration(net, bench_net, window_name, book):
    rel = (net - bench_net)
    logr = np.log1p(net)
    tot = float(logr.sum())
    top = logr.sort_values(ascending=False)
    reltop = rel.sort_values(ascending=False)
    reltot = float(rel.sum())
    # C5
    cum = reltop.cumsum()
    k_flip = int((cum < reltot).sum() + 1) if reltot > 0 else 0
    if reltot > 0:
        k_flip = int(np.searchsorted(cum.values, reltot)) + 1
    m = np.log1p(net).resample("ME").sum()
    pos = m[m > 0]
    hhi = float(((pos / pos.sum()) ** 2).sum()) if pos.sum() > 0 else None
    yearly = np.log1p(net).groupby(net.index.year).sum()
    rel_yearly = rel.groupby(rel.index.year).sum()
    return {
        "book": book, "window": window_name,
        "total_log_net": round(tot, 4), "total_rel": round(reltot, 4),
        "top5_share": round(float(top.head(5).sum() / tot), 2) if tot else None,
        "top10_share": round(float(top.head(10).sum() / tot), 2) if tot else None,
        "top20_share": round(float(top.head(20).sum() / tot), 2) if tot else None,
        "rel_top5": round(float(reltop.head(5).sum()), 4),
        "rel_top10": round(float(reltop.head(10).sum()), 4),
        "k_flip_rel": k_flip if reltot > 0 else "already<=0",
        "best_month_share": round(float(m.max() / tot), 2) if tot > 0 else None,
        "hhi_pos_months": round(hhi, 3) if hhi else None,
        "yearly_log_net": {int(k): round(float(v), 4) for k, v in yearly.items()},
        "yearly_rel": {int(k): round(float(v), 4) for k, v in rel_yearly.items()},
    }


def main():
    panel = harness.load_full()
    lab = build_regimes(panel)
    benches = {}
    for (name, wd) in [("SPY", {"SPY": 1.0}), ("QQQ", {"QQQ": 1.0}),
                       ("6040", {"SPY": 0.6, "BIL": 0.4})]:
        benches[name] = {w: const_weight_bench(panel, wd, *win)["net_daily"]
                         for w, win in [("W1", W1), ("W2", W2)]}

    all_reg, all_conc, gross_by_regime, meta = [], [], [], {}
    for b in BOOKS:
        mod = harness.load_spec(HUNT / "specs" / b)
        ge = daily_gross_exposure(mod, panel)
        for wname, win in [("W1", W1), ("W2", W2)]:
            r = harness.run(mod, panel, *win)
            net = r["net_daily"]
            bnet = benches[BENCH[b]][wname].reindex(net.index).fillna(0.0)
            tab, (pk, tr, mdd) = regime_table(net, bnet, lab, wname, b)
            # avg gross per R1/R2 bucket (mechanism tests M1/M4)
            for R in ["R1", "R2"]:
                for v in lab[R].reindex(net.index).dropna().unique():
                    m = lab[R].reindex(net.index) == v
                    tab.loc[tab.regime == f"{R}:{v}", "avg_gross"] = round(
                        float(ge.reindex(net.index)[m].mean()), 2)
            all_reg.append(tab)
            all_conc.append(concentration(net, bnet, wname, b))
            meta[f"{b}:{wname}"] = {"total_net": round(r["total_net"], 4),
                                    "sharpe": round(r["sharpe"], 2),
                                    "max_dd": round(mdd, 4),
                                    "dd_peak": str(pk.date()), "dd_trough": str(tr.date()),
                                    "bench_total": round(float((1 + bnet).prod() - 1), 4)}

    reg = pd.concat(all_reg)
    reg.to_csv(OUT / "regime_table.csv", index=False)
    pd.DataFrame(all_conc).to_csv(OUT / "concentration_table.csv", index=False)
    (OUT / "run_meta.json").write_text(json.dumps(meta, indent=2))

    # time-in-regime for the blind year (evidence-coverage check)
    cov = {}
    idx = benches["SPY"]["W1"].index
    for R in ["R1", "R2", "R3", "R4", "R5", "R6"]:
        cov[R] = lab[R].reindex(idx).value_counts().to_dict()
    (OUT / "blind_year_regime_coverage.json").write_text(json.dumps(cov, indent=2, default=int))

    eps1 = stress_episodes(panel, *W1)
    eps2 = stress_episodes(panel, *W2)
    (OUT / "stress_episodes.json").write_text(json.dumps({
        "W1": [[str(a.date()), str(b.date())] for a, b in eps1],
        "W2": [[str(a.date()), str(b.date())] for a, b in eps2]}, indent=2))
    print("done"); print(json.dumps(meta, indent=2))


if __name__ == "__main__":
    main()
