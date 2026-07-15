# JSE factor-1 beta-overlay — regime map by universe factor-SNR (EXP-2026-07-14-jse-regime-map)

Fixed one-factor long-only min-var (5% cap); jse1 vs pca1 differ only in the factor-1 correction. Primary = monthly L1 weight turnover (survivorship-robust). Prereg: preregistrations/jse-regime-map-2026-07-14.md.

## n_est = 63

| universe | months | mean ψ̂₁ | med turnover pca1 | med turnover jse1 | Δ turnover (jse−pca) | paired t | p | Δ realized vol |
|---|---|---|---|---|---|---|---|---|
| large | 98 | 0.9789 | 0.3275 | 0.3333 | +0.0044 | +12.06 | 0.0000 | -0.0002 |
| mid | 98 | 0.9802 | 0.3377 | 0.3418 | +0.0045 | +10.72 | 0.0000 | -0.0006 |
| small | 98 | 0.9759 | 0.3742 | 0.3828 | +0.0064 | +5.99 | 0.0000 | -0.0011 |

## n_est = 252

| universe | months | mean ψ̂₁ | med turnover pca1 | med turnover jse1 | Δ turnover (jse−pca) | paired t | p | Δ realized vol |
|---|---|---|---|---|---|---|---|---|
| large | 89 | 0.9956 | 0.0878 | 0.0884 | +0.0002 | +5.40 | 0.0000 | -0.0000 |
| mid | 89 | 0.9958 | 0.1015 | 0.1016 | +0.0003 | +7.32 | 0.0000 | -0.0001 |
| small | 89 | 0.9950 | 0.1148 | 0.1153 | +0.0005 | +6.69 | 0.0000 | -0.0002 |

## Decisive cell (n_est=63)

- mean ψ̂₁: large 0.9789 · mid 0.9802 · small 0.9759 (gradient present)
- turnover reduction (jse−pca): large +0.0044 · mid +0.0045 · small +0.0064 (churn grows on noisier universe)
- small-cap significance: p=0.0000

## Verdict (pre-committed rule): **HARMFUL — JSE raises turnover (destabilizes), most on the noisiest universe**

## Story

- **The overlay hypothesis is falsified, and informatively.** JSE on factor 1 does not stabilize the hedge — it churns it: turnover rises on every universe (t=6–12, all p≈0), and the harm GROWS as the universe gets noisier (small +64 bps-of-weight vs large +44). This is the weight-stability face of F-027/F-028: the correction perturbs an already-good market eigenvector, and each monthly re-perturbation shows up as extra weight movement for essentially zero realized-vol payoff (Δvol ≈ 0).
- **The premise only weakly holds on accessible data.** ψ̂₁ is ~0.976–0.996 on ALL cached universes including small-cap — the market factor is well-estimated even in the S&P 600 at these p (~600 names). There IS a faint SNR gradient (small ψ̂₁ 0.976 < large 0.979), and the churn tracks it, but nothing here reaches the p≪strong-factor regime where the correction could earn its keep. The honest boundary statement: single-factor JSE's benefit does not live anywhere in the S&P large/mid/small-cap universe — it needs genuinely thin panels (tens of names) or much shorter windows, i.e. a different asset class.
- **What this settles for the beta-overlay framing:** as a risk-model overlay judged on hedge/weight stability, single-factor JSE is a small net negative on S&P-scale universes — it costs turnover and returns no vol reduction. The regime map is the deliverable: it draws the boundary rather than claiming a universal benefit, which is exactly the defensible thing to bring to Alex/Lisa. Any noisy-panel test (synthetic SNR, tens-of-names universes) is a new prereg.
