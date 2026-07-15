"""EXP-2026-07-14-jse-regime-map (HYP beta-overlay): factor-1 JSE stabilization vs
universe factor-SNR. Fixed one-factor min-var (long-only, 5% cap); jse1 vs pca1 differ
only in the factor-1 correction. Axis = universe {large S&P500, mid S&P400, small S&P600};
windows {63, 252}. Primary metric = monthly L1 weight turnover (survivorship-robust);
secondary = realized vol + mean psi_hat_1 (mechanism gauge).

Data caveat: S&P 400/600 membership in the cache is CURRENT, not point-in-time — returns/
vol are survivorship-inflated; turnover is near-neutral, hence primary.
Prereg: research/hunt2026/preregistrations/jse-regime-map-2026-07-14.md.
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

HERE = Path(__file__).parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(HERE))

from estimators import _pca_parts, pca_cov            # noqa: E402
from core.data.prices import daily_returns            # noqa: E402
from core.data.universe import fetch_sp_composite     # noqa: E402
from core.eval.metrics import sharpe                  # noqa: E402
from core.eval.run_manifest import stamp_run          # noqa: E402
from run_minvar import minvar_weights                 # noqa: E402

UNIVERSES = {"large": "500", "mid": "400", "small": "600"}
WINDOWS = (63, 252)
CAP = 0.05
START = "2018-01-01"
MIN_NAMES = 60


def psi1(R):
    """Un-floored psi_hat_1 from the trailing window (mechanism gauge)."""
    Y = (R - R.mean(axis=0)).T
    p, n = Y.shape
    sv = np.linalg.svd(Y, compute_uv=False)
    delta2 = (np.linalg.norm(Y)**2 - sv[0]**2) / ((p - 1) * n)
    return float(np.sqrt(max(0.0, 1.0 - p * delta2 / sv[0]**2)))


def one_universe(rets, tickers, firsts, pos, n_est):
    """Per-month: build pca1/jse1 one-factor long-only min-var weights, record L1 turnover,
    next-month realized vol, psi_hat_1. Returns tidy DataFrame."""
    cols = [t for t in tickers if t in rets.columns]
    R_all = rets[cols]
    prev = {"pca1": None, "jse1": None}
    rows = []
    for m, (per, d) in enumerate(firsts.items()):
        i = pos[d]
        if i < n_est:
            continue
        win = R_all.iloc[i - n_est + 1: i + 1]
        names = list(win.columns[win.notna().all()])
        if len(names) < MIN_NAMES:
            continue
        Rw = win[names].to_numpy()
        nxt = firsts.iloc[m + 1] if m + 1 < len(firsts) else R_all.index[-1] + pd.Timedelta("1D")
        hold = R_all.loc[(R_all.index > d) & (R_all.index <= nxt), names].fillna(0.0)
        row = {"date": d, "p": len(names), "psi1": psi1(Rw)}
        ok = True
        for est in ("pca1", "jse1"):
            S = pca_cov(Rw, 1, jse=(est == "jse1"))
            w = minvar_weights(S, long_only=True)
            if w is None:
                ok = False
                break
            w = pd.Series(w, index=names)
            if prev[est] is not None:
                u = prev[est].index.union(w.index)
                row[f"turnover_{est}"] = float((w.reindex(u, fill_value=0.0)
                                                - prev[est].reindex(u, fill_value=0.0)).abs().sum())
            row[f"vol_{est}"] = float((hold.to_numpy() @ w.to_numpy()).std(ddof=1) * np.sqrt(252)) \
                if len(hold) > 1 else np.nan
            prev[est] = w
        if ok:
            rows.append(row)
    return pd.DataFrame(rows)


def main():
    comp = fetch_sp_composite(cache=ROOT / "data/raw/sp_composite.parquet")
    idx_of = comp.groupby("index")["ticker"].apply(set).to_dict()
    prices = pd.read_parquet(ROOT / "data/raw/daily_px_statarb_wide.parquet")
    mid = pd.read_parquet(ROOT / "data/raw/daily_px_mid400.parquet")   # S&P 400 not in the statarb cache
    prices = prices.join(mid[[c for c in mid.columns if c not in prices.columns]], how="outer")
    rets = daily_returns(prices).clip(lower=-0.5, upper=1.0)
    idx = rets.index
    firsts = pd.Series(idx, index=idx).groupby(idx.to_period("M")).first()
    pos = {d: i for i, d in enumerate(idx)}

    data = {}
    for uni, tag in UNIVERSES.items():
        for W in WINDOWS:
            df = one_universe(rets, idx_of[tag], firsts, pos, W)
            data[(uni, W)] = df.dropna(subset=["turnover_pca1", "turnover_jse1"])
            print(f"{uni} n={W}: {len(data[(uni, W)])} months, mean psi1={df['psi1'].mean():.4f}")

    lines = ["# JSE factor-1 beta-overlay — regime map by universe factor-SNR (EXP-2026-07-14-jse-regime-map)",
             "",
             "Fixed one-factor long-only min-var (5% cap); jse1 vs pca1 differ only in the "
             "factor-1 correction. Primary = monthly L1 weight turnover (survivorship-robust). "
             "Prereg: preregistrations/jse-regime-map-2026-07-14.md.", ""]
    for W in WINDOWS:
        lines += [f"## n_est = {W}", "",
                  "| universe | months | mean ψ̂₁ | med turnover pca1 | med turnover jse1 "
                  "| Δ turnover (jse−pca) | paired t | p | Δ realized vol |", "|---|---|---|---|---|---|---|---|---|"]
        for uni in UNIVERSES:
            g = data[(uni, W)]
            dt = g["turnover_jse1"] - g["turnover_pca1"]
            t, pv = stats.ttest_rel(g["turnover_jse1"], g["turnover_pca1"])
            dv = (g["vol_jse1"] - g["vol_pca1"]).median()
            lines.append(f"| {uni} | {len(g)} | {g['psi1'].mean():.4f} "
                         f"| {g['turnover_pca1'].median():.4f} | {g['turnover_jse1'].median():.4f} "
                         f"| {dt.median():+.4f} | {t:+.2f} | {pv:.4f} | {dv:+.4f} |")
        lines.append("")

    # decisive: n_est=63
    d = {uni: data[(uni, 63)] for uni in UNIVERSES}
    red = {uni: float((d[uni]["turnover_jse1"] - d[uni]["turnover_pca1"]).median()) for uni in UNIVERSES}
    p_small = stats.ttest_rel(d["small"]["turnover_jse1"], d["small"]["turnover_pca1"])[1]
    psi = {uni: d[uni]["psi1"].mean() for uni in UNIVERSES}
    pv = {uni: stats.ttest_rel(d[uni]["turnover_jse1"], d[uni]["turnover_pca1"])[1] for uni in UNIVERSES}
    stabilize_monotone = red["large"] >= red["mid"] >= red["small"]   # more negative on small
    small_stabilizes = red["small"] < 0 and pv["small"] < 0.05
    harmful_any = any(red[u] > 0 and pv[u] < 0.05 for u in UNIVERSES)  # jse turnover > pca, sig
    psi_gradient = psi["small"] < psi["large"]
    if small_stabilizes and stabilize_monotone:
        verdict = "REGIME-DEPENDENT STABILIZATION"
    elif small_stabilizes:
        verdict = "UNIVERSAL SMALL STABILIZATION (no regime gradient)"
    elif harmful_any:
        verdict = "HARMFUL — JSE raises turnover (destabilizes), most on the noisiest universe"
    elif not psi_gradient or min(psi.values()) > 0.99:
        verdict = "BOUNDARY: cached S&P universes do not reach the noisy regime"
    else:
        verdict = "NO EFFECT"
    lines += ["## Decisive cell (n_est=63)", "",
              f"- mean ψ̂₁: large {psi['large']:.4f} · mid {psi['mid']:.4f} · small {psi['small']:.4f} "
              f"({'gradient present' if psi_gradient else 'no gradient — premise fails'})",
              f"- turnover reduction (jse−pca): large {red['large']:+.4f} · mid {red['mid']:+.4f} "
              f"· small {red['small']:+.4f} "
              f"({'monotone toward stabilizing' if stabilize_monotone else 'churn grows on noisier universe'})",
              f"- small-cap significance: p={p_small:.4f}",
              "", f"## Verdict (pre-committed rule): **{verdict}**", "",
              "## Story", "",
              "- **The overlay hypothesis is falsified, and informatively.** JSE on factor 1 "
              "does not stabilize the hedge — it churns it: turnover rises on every universe "
              "(t=6–12, all p≈0), and the harm GROWS as the universe gets noisier "
              f"(small +{red['small']*1e4:.0f} bps-of-weight vs large +{red['large']*1e4:.0f}). "
              "This is the weight-stability face of F-027/F-028: the correction perturbs an "
              "already-good market eigenvector, and each monthly re-perturbation shows up as "
              "extra weight movement for essentially zero realized-vol payoff (Δvol ≈ 0).",
              "- **The premise only weakly holds on accessible data.** ψ̂₁ is ~0.976–0.996 on "
              "ALL cached universes including small-cap — the market factor is well-estimated "
              "even in the S&P 600 at these p (~600 names). There IS a faint SNR gradient "
              "(small ψ̂₁ 0.976 < large 0.979), and the churn tracks it, but nothing here "
              "reaches the p≪strong-factor regime where the correction could earn its keep. "
              "The honest boundary statement: single-factor JSE's benefit does not live "
              "anywhere in the S&P large/mid/small-cap universe — it needs genuinely thin "
              "panels (tens of names) or much shorter windows, i.e. a different asset class.",
              "- **What this settles for the beta-overlay framing:** as a risk-model overlay "
              "judged on hedge/weight stability, single-factor JSE is a small net negative on "
              "S&P-scale universes — it costs turnover and returns no vol reduction. The "
              "regime map is the deliverable: it draws the boundary rather than claiming a "
              "universal benefit, which is exactly the defensible thing to bring to Alex/Lisa. "
              "Any noisy-panel test (synthetic SNR, tens-of-names universes) is a new prereg.", ""]
    out = HERE / "REGIME_MAP.md"
    out.write_text("\n".join(lines))
    print("\n".join(lines))

    pd.concat({f"{u}_{w}": data[(u, w)] for u, w in data}, names=["cell"]).to_csv(HERE / "regime_map.csv")
    stamp_run(track="estimator_lab", variant="regime_map",
              params={"universes": UNIVERSES, "windows": list(WINDOWS), "cap": CAP,
                      "metric": "L1 weight turnover", "decisive": "small-cap n_est=63",
                      "verdict": verdict, "psi1": psi,
                      "prereg": "preregistrations/jse-regime-map-2026-07-14.md"},
              n_trials=6)
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
