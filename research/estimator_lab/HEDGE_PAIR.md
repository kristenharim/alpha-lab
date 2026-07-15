# JSE factor-1 hedging vs PCA vs sector ETF — frozen A&L harness (HYP-005b)

Frozen 2026-07-10 verdict basis (60/1.25/0.5/skip1, PIT, 10 bps/side, implementable P&L). Only the hedge factor varies. Prereg: preregistrations/jse-hedge-pair-2026-07-14.md.

| variant | gross Sharpe | net Sharpe | deflated P(net>0), n=5 | median monthly \|β_SPY\| |
|---|---|---|---|---|
| sector_etf | +0.30 | -1.02 | 0.0% | 0.041 |
| pca1_n63 | +0.58 | -0.40 | 1.1% | 0.059 |
| jse1_n63 | +0.56 | -0.43 | 0.9% | 0.057 |
| pca1_n252 | +0.35 | -0.58 | 0.4% | 0.056 |
| jse1_n252 | +0.35 | -0.58 | 0.4% | 0.056 |

## Decisive pair — jse1 vs pca1, n_est=63

- median monthly |β_SPY|: jse1 0.057 vs pca1 0.059 (paired Δ median -0.0004, t=-1.53, p=0.1305, 91 months)
- gross Sharpe delta (jse1 − pca1): -0.023

## Verdict (pre-committed rule): **NO EFFECT**
## Revival gate (net Sharpe ≥ 0.5, any variant): **NOT HIT**

## Story

- **Why JSE has no effect here: there is nothing to correct.** At p ≈ 500–1000 names, factor 1 is so dominant that ψ̂₁ ≈ 1 — the dispersion bias on the market eigenvector is negligible, so the corrected and raw h₁ are nearly the same vector (at n_est=252 the two books are indistinguishable to 2 decimals). Combined with F-027, this brackets the correction completely on this panel: **the factor JSE can validly correct (f1) has no bias worth correcting; the factors with real bias (f2–f5) have no valid target.** The practitioner value of the current single-factor JSE lives on small/thin panels (few names, short windows), not large-cap S&P universes — worth bringing to Alex/Lisa alongside the F-027 result.
- **The real side finding is the hedge model, not the estimator:** a statistical factor-1 hedge nearly DOUBLES the frozen strategy's gross edge vs the verdict's sector-ETF hedge (gross Sharpe +0.30 → +0.58 at n_est=63) — the sector-ETF baseline reproduces the 2026-07-10 verdict's recorded ~0.3 gross, so the comparison is anchored. Net improves −1.02 → −0.40 but stays well below the 0.5 revival bar: the hedge upgrade lifts the edge, the signal-driven churn still eats it. Any pursuit of the hedge-model lane (e.g., toward lower-turnover variants) is a NEW prereg, per the stop-iterating clause.
- HYP-005b closes back to the 2026-07-10 verdict. The reopen was worthwhile: it produced the sharpest statement yet of where the single-factor correction does and does not bite, plus a quantified hedge-model observation for the record.
