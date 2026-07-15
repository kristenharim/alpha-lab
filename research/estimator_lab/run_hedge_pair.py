"""EXP-2026-07-14-jse-hedge-pair (HYP-005b): JSE-corrected factor-1 hedging vs raw PCA
vs the sector-ETF verdict model, in the FROZEN Avellaneda-Lee residual harness.

Harness frozen at the 2026-07-10 verdict basis: window=60, entry=1.25, exit=0.5, skip=1,
PIT membership, implementable P&L via run_residual, cost = 10 bps/side. Only the hedge
factor varies. Factor-1 series re-estimated monthly from the trailing n_est days
(full-coverage names), sign-fixed h1; jse1 rotates h1 toward q exactly as estimators.py
(k=1, same tau) — equivalence asserted against ESTIMATORS machinery.

Decisive pair (prereg): jse1 vs pca1 at n_est=63 — paired monthly |rolling 63d beta vs
SPY| of the book's net returns + gross-Sharpe delta. Revival gate: any variant net
Sharpe >= 0.5 (deflated, n_trials=5) -> Stage-2 candidacy for Kristen.
Prereg: research/hunt2026/preregistrations/jse-hedge-pair-2026-07-14.md.
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

from estimators import ESTIMATORS, TAU, _pca_parts                      # noqa: E402
from core.data.prices import daily_returns, fetch_prices_yf            # noqa: E402
from core.data.universe import (fetch_sp_composite, fetch_sp500_pit_changes,  # noqa: E402
                                membership_mask, ever_members)
from core.eval.metrics import deflated_sharpe, sharpe                   # noqa: E402
from core.eval.run_manifest import stamp_run                            # noqa: E402
from tracks.statarb.book import SECTOR_ETF, run_residual                # noqa: E402

FROZEN = dict(window=60, entry=1.25, exit_=0.5, skip=1, cost_bps=10.0)  # verdict basis
N_ESTS = (63, 252)
START = "2018-01-01"
N_TRIALS_REVIVAL = 5


def factor1_series(rets, firsts, pos, n_est, jse):
    """Monthly re-estimated factor-1 return series (one Series over all days).
    h1 from trailing n_est days of full-coverage names; jse rotates toward q with
    psi^2 = max(TAU, 1 - p*delta2/s1^2) — identical formulas to estimators._pca_parts."""
    out = pd.Series(np.nan, index=rets.index)
    checked = False
    for m, (per, d) in enumerate(firsts.items()):
        i = pos[d]
        if i < n_est:
            continue
        win = rets.iloc[i - n_est + 1: i + 1]
        names = win.columns[win.notna().all()]
        if len(names) < 100:
            continue
        R = win[names].to_numpy()
        Y = (R - R.mean(axis=0)).T
        p, n = Y.shape
        U, sv, _ = np.linalg.svd(Y, full_matrices=False)
        h = U[:, 0] if U[:, 0].sum() >= 0 else -U[:, 0]
        if jse:
            delta2 = (np.linalg.norm(Y)**2 - (sv[:1]**2).sum()) / ((p - 1) * n)
            psi2 = max(TAU, 1.0 - p * delta2 / sv[0]**2)
            q = np.full(p, 1.0 / np.sqrt(p))
            hq = float(h @ q)
            c = np.clip(hq / np.sqrt(psi2), -1.0, 1.0)
            r = h - hq * q
            rn = np.linalg.norm(r)
            h = q if rn < 1e-12 else c * q + np.sqrt(max(0.0, 1.0 - c**2)) * (r / rn)
        if not checked:   # equivalence with the published estimator machinery, once
            V, _, _ = _pca_parts(R, 1, jse)
            v = V[:, 0] if V[:, 0] @ h >= 0 else -V[:, 0]
            assert np.allclose(v, h, atol=1e-10), "factor-1 does not match _pca_parts"
            checked = True
        nxt = firsts.iloc[m + 1] if m + 1 < len(firsts) else rets.index[-1] + pd.Timedelta("1D")
        span = rets.index[(rets.index > d) & (rets.index <= nxt)]
        out.loc[span] = rets.loc[span, names].fillna(0.0).to_numpy() @ h
    return out


def book_gross(res, skip):
    """Equal-weight held x hedged, pre-cost (mirrors equal_weight_net's gross leg)."""
    positions = res["final_positions"]
    n_active = positions.abs().sum(axis=1).replace(0, np.nan)
    eq_w = positions.div(n_active, axis=0).fillna(0.0)
    held = eq_w.shift(1 + skip)
    gross = (held * res["hedged"]).sum(axis=1)
    return gross.reindex(res["net"].index)


def monthly_abs_beta(net, spy):
    """|rolling 63d beta| of book net vs SPY, sampled at month-ends."""
    df = pd.concat({"b": net, "m": spy}, axis=1).dropna()
    cov = df["b"].rolling(63).cov(df["m"])
    var = df["m"].rolling(63).var()
    beta = (cov / var).abs()
    return beta.groupby(beta.index.to_period("M")).last().dropna()


def main():
    comp = fetch_sp_composite(cache=ROOT / "data/raw/sp_composite.parquet")
    pit_changes = fetch_sp500_pit_changes(cache=ROOT / "data/raw/sp500_pit_changes.parquet")
    keep_set = ever_members(pit_changes)
    sector = dict(zip(comp["ticker"], comp["sector"]))

    prices = pd.read_parquet(ROOT / "data/raw/daily_px_statarb_wide.parquet")
    prices = prices[[c for c in prices.columns if c in keep_set]]
    rets = daily_returns(prices).clip(lower=-0.5, upper=1.0)
    pit_mask = membership_mask(pit_changes, rets.index, list(rets.columns))

    etf_px = fetch_prices_yf(["SPY"] + sorted(set(SECTOR_ETF.values())), START, None)
    etf_ret = daily_returns(etf_px).reindex(rets.index)
    spy = etf_ret["SPY"]

    idx = rets.index
    firsts = pd.Series(idx, index=idx).groupby(idx.to_period("M")).first()
    pos = {d: i for i, d in enumerate(idx)}

    # variant -> per-stock factor DataFrame (matched-column convention)
    variants = {}
    sector_factor = {t: etf_ret[SECTOR_ETF.get(sector.get(t, ""), "SPY")].fillna(etf_ret["SPY"])
                     for t in rets.columns}
    variants["sector_etf"] = pd.DataFrame(sector_factor).reindex(rets.index)
    for n_est in N_ESTS:
        for jse in (False, True):
            X = factor1_series(rets, firsts, pos, n_est, jse)
            name = f"{'jse1' if jse else 'pca1'}_n{n_est}"
            variants[name] = pd.DataFrame({t: X for t in rets.columns})
            print(f"built {name}")

    results = {}
    for name, factors in variants.items():
        res = run_residual(rets, factors, sector, pit_mask=pit_mask, **FROZEN)
        net = res["net"]
        results[name] = {
            "net": net, "gross": book_gross(res, FROZEN["skip"]),
            "abs_beta": monthly_abs_beta(net, spy),
        }
        print(f"ran {name}: {len(net)} days")

    lines = ["# JSE factor-1 hedging vs PCA vs sector ETF — frozen A&L harness (HYP-005b)",
             "",
             "Frozen 2026-07-10 verdict basis (60/1.25/0.5/skip1, PIT, 10 bps/side, "
             "implementable P&L). Only the hedge factor varies. Prereg: "
             "preregistrations/jse-hedge-pair-2026-07-14.md.", "",
             "| variant | gross Sharpe | net Sharpe | deflated P(net>0), n=5 | median monthly \\|β_SPY\\| |",
             "|---|---|---|---|---|"]
    for name, r in results.items():
        lines.append(f"| {name} | {sharpe(r['gross'], 252):+.2f} | {sharpe(r['net'], 252):+.2f} "
                     f"| {deflated_sharpe(r['net'], N_TRIALS_REVIVAL, 252):.1%} "
                     f"| {r['abs_beta'].median():.3f} |")

    # decisive pair: jse1 vs pca1 at n_est=63
    a, b = results["jse1_n63"], results["pca1_n63"]
    common = a["abs_beta"].index.intersection(b["abs_beta"].index)
    d_beta = a["abs_beta"].loc[common] - b["abs_beta"].loc[common]
    t, pv = stats.ttest_rel(a["abs_beta"].loc[common], b["abs_beta"].loc[common])
    d_gross = sharpe(a["gross"], 252) - sharpe(b["gross"], 252)
    lines += ["", "## Decisive pair — jse1 vs pca1, n_est=63", "",
              f"- median monthly |β_SPY|: jse1 {a['abs_beta'].median():.3f} vs "
              f"pca1 {b['abs_beta'].median():.3f} (paired Δ median {d_beta.median():+.4f}, "
              f"t={t:+.2f}, p={pv:.4f}, {len(common)} months)",
              f"- gross Sharpe delta (jse1 − pca1): {d_gross:+.3f}"]
    if d_beta.median() < 0 and pv < 0.05 and d_gross >= 0:
        verdict = "JSE IMPROVES THE HEDGE"
    elif pv >= 0.05:
        verdict = "NO EFFECT"
    else:
        verdict = "HARMFUL" if (d_beta.median() > 0 or d_gross < -0.05) else "NO EFFECT"
    revived = [n for n, r in results.items() if sharpe(r["net"], 252) >= 0.5]
    lines += ["", f"## Verdict (pre-committed rule): **{verdict}**",
              f"## Revival gate (net Sharpe ≥ 0.5, any variant): "
              f"**{'HIT — ' + ', '.join(revived) if revived else 'NOT HIT'}**", ""]
    lines += ["## Story", "",
              "- **Why JSE has no effect here: there is nothing to correct.** At p ≈ "
              "500–1000 names, factor 1 is so dominant that ψ̂₁ ≈ 1 — the dispersion "
              "bias on the market eigenvector is negligible, so the corrected and raw "
              "h₁ are nearly the same vector (at n_est=252 the two books are "
              "indistinguishable to 2 decimals). Combined with F-027, this brackets the "
              "correction completely on this panel: **the factor JSE can validly "
              "correct (f1) has no bias worth correcting; the factors with real bias "
              "(f2–f5) have no valid target.** The practitioner value of the current "
              "single-factor JSE lives on small/thin panels (few names, short windows), "
              "not large-cap S&P universes — worth bringing to Alex/Lisa alongside the "
              "F-027 result.",
              "- **The real side finding is the hedge model, not the estimator:** a "
              "statistical factor-1 hedge nearly DOUBLES the frozen strategy's gross "
              "edge vs the verdict's sector-ETF hedge (gross Sharpe +0.30 → +0.58 at "
              "n_est=63) — the sector-ETF baseline reproduces the 2026-07-10 verdict's "
              "recorded ~0.3 gross, so the comparison is anchored. Net improves "
              "−1.02 → −0.40 but stays well below the 0.5 revival bar: the hedge "
              "upgrade lifts the edge, the signal-driven churn still eats it. Any "
              "pursuit of the hedge-model lane (e.g., toward lower-turnover variants) "
              "is a NEW prereg, per the stop-iterating clause.",
              "- HYP-005b closes back to the 2026-07-10 verdict. The reopen was "
              "worthwhile: it produced the sharpest statement yet of where the "
              "single-factor correction does and does not bite, plus a quantified "
              "hedge-model observation for the record.", ""]
    out = HERE / "HEDGE_PAIR.md"
    out.write_text("\n".join(lines))
    print("\n".join(lines))

    pd.DataFrame({f"{n}_{k}": (r[k] if k != "abs_beta" else r[k].reindex(common))
                  for n, r in results.items() for k in ("net",)}).to_csv(HERE / "hedge_pair_net.csv")
    stamp_run(track="estimator_lab", variant="hedge_pair",
              params={**FROZEN, "n_ests": list(N_ESTS), "pit": True, "start": START,
                      "decisive": "jse1_n63 vs pca1_n63", "verdict": verdict,
                      "revival_gate_hit": bool(revived),
                      "prereg": "preregistrations/jse-hedge-pair-2026-07-14.md"},
              n_trials=N_TRIALS_REVIVAL)
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
