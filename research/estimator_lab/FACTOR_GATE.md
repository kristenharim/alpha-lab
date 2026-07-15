# Per-factor-gated JSE vs blanket (EXP-2026-07-14-jse-factor-gate)

Gate: correct factor j iff psi_hat_j >= psi_min AND relative eigengap >= g_min; failing factors stay raw PCA. Matched pair vs blanket jse5 (identical lam/D/delta2/tau/rotation). Decisive cell: long-only, n=63. Prereg: preregistrations/jse-factor-gate-2026-07-14.md.

## Gate pass rates per factor (share of months passing, decisive window n=63)

| config (psi_min, g_min) | f1 | f2 | f3 | f4 | f5 |
|---|---|---|---|---|---|
| (0.3, 0.05) | 100% | 99% | 98% | 91% | 86% |
| (0.3, 0.1) | 100% | 96% | 90% | 72% | 60% |
| (0.5, 0.05) | 100% | 99% | 98% | 91% | 86% |
| (0.5, 0.1) | 100% | 96% | 90% | 72% | 60% |
| (0.7, 0.05) | 100% | 99% | 98% | 91% | 86% |
| (0.7, 0.1) | 100% | 96% | 90% | 72% | 60% |

## n=63 long_only  **(decisive cell)** — 138 months

| config | med Δ vs jse5 (bps vol) | paired t | p | med Δ vs pca5 |
|---|---|---|---|---|
| (0.3, 0.05) | +0.00 | -1.30 | 0.1967 | -0.92 |
| (0.3, 0.1) | +0.00 | -2.81 | 0.0057 | -1.20 |
| (0.5, 0.05) | +0.00 | -1.30 | 0.1967 | -0.92 |
| (0.5, 0.1) | +0.00 | -2.81 | 0.0057 | -1.20 |
| (0.7, 0.05) | +0.00 | -1.30 | 0.1967 | -0.92 |
| (0.7, 0.1) | +0.00 | -2.81 | 0.0057 | -1.20 |

(jse3 − pca3 median benefit, the recovery bar: -1.12 bps)

## n=63 unconstrained — 138 months

| config | med Δ vs jse5 (bps vol) | paired t | p | med Δ vs pca5 |
|---|---|---|---|---|
| (0.3, 0.05) | +0.00 | -0.49 | 0.6245 | +17.99 |
| (0.3, 0.1) | +0.00 | -0.39 | 0.6956 | +18.69 |
| (0.5, 0.05) | +0.00 | -0.49 | 0.6245 | +17.99 |
| (0.5, 0.1) | +0.00 | -0.39 | 0.6956 | +18.69 |
| (0.7, 0.05) | +0.00 | -0.49 | 0.6245 | +17.99 |
| (0.7, 0.1) | +0.00 | -0.39 | 0.6956 | +18.69 |

(jse3 − pca3 median benefit, the recovery bar: +27.42 bps)

## n=252 long_only — 138 months

| config | med Δ vs jse5 (bps vol) | paired t | p | med Δ vs pca5 |
|---|---|---|---|---|
| (0.3, 0.05) | +0.00 | +1.16 | 0.2477 | -0.30 |
| (0.3, 0.1) | +0.00 | -0.82 | 0.4132 | -0.30 |
| (0.5, 0.05) | +0.00 | +1.16 | 0.2477 | -0.30 |
| (0.5, 0.1) | +0.00 | -0.82 | 0.4132 | -0.30 |
| (0.7, 0.05) | +0.00 | +1.16 | 0.2477 | -0.30 |
| (0.7, 0.1) | +0.00 | -0.82 | 0.4132 | -0.30 |

(jse3 − pca3 median benefit, the recovery bar: -0.39 bps)

## n=252 unconstrained — 138 months

| config | med Δ vs jse5 (bps vol) | paired t | p | med Δ vs pca5 |
|---|---|---|---|---|
| (0.3, 0.05) | +0.00 | +0.23 | 0.8190 | +11.24 |
| (0.3, 0.1) | +0.00 | -1.16 | 0.2490 | +11.25 |
| (0.5, 0.05) | +0.00 | +0.23 | 0.8190 | +11.24 |
| (0.5, 0.1) | +0.00 | -1.16 | 0.2490 | +11.25 |
| (0.7, 0.05) | +0.00 | +0.23 | 0.8190 | +11.24 |
| (0.7, 0.1) | +0.00 | -1.16 | 0.2490 | +11.25 |

(jse3 − pca3 median benefit, the recovery bar: +15.25 bps)

## Verdict (pre-committed rule, decisive cell): **REDUNDANT** (0/6 configs meet all three conditions)

## Story

- **The ψ̂ gate never binds.** Minimum ψ̂ per factor across all 138 months (n=63): [0.94, 0.91, 0.88, 0.849, 0.826] — even factor 5 never drops below 0.826, far above every registered ψ_min. All three ψ_min values therefore produce identical results. This is the prereg's pre-registered alternative world: in detection-threshold terms the S&P top-5 factors are ALL strong at these p/n — the weak-factor quality problem does not exist here, and the how-many-factors question is not about ψ̂-quality on this panel.
- **The separation gate is the only one that binds** (Assumption-3 analogue): at g_min=0.10, f4 fails 28% and f5 40% of months — near-degeneracy between the small factors is the real quality issue, exactly where per-direction correction is ill-posed.
- **Where the gate binds, the direction favors gating but the size is noise-grade:** 88/138 months differ from blanket at g_min=0.10; mean paired delta -0.36 bps vol, 65% hit rate, pooled t = −2.81 (p = 0.0057). Real signal, ~10x smaller than the pre-committed −0.2 bps median bar.
- **Design lesson (for the next prereg, not this one):** a median-based decisive stat cannot fire when treatment == control in most months (74% identical at g_min=0.05). The rule stands as written — verdict REDUNDANT — but a bound-months or mean-based statistic would have been the right pre-commitment for a gate that binds in a minority of months.
- Net: the Goldberg program returns to its F-021 FINAL closed state; the stale 'JSE k=3–5 unconstrained' queue item retires with it.
