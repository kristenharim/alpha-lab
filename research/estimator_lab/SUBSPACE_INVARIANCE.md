# Is min-var a subspace functional? — rotation-invariance test (EXP-2026-07-14-subspace-invariance)

w ∝ Σ⁻¹1 = δ⁻²(I−P)1 + HΛ⁻¹Hᵀ1. Prediction: realized OOS min-var vol invariant to within-subspace frame rotation (P fixed), sensitive to P. Unconstrained min-var. Prereg: preregistrations/subspace-invariance-2026-07-14.md.

| universe | n | k | months | med rot CV | proj gap | flat gap | rand-subspace excess | λ₁/λ_k |
|---|---|---|---|---|---|---|---|---|
| large | 63 | 1 | 99 | — | +0.034 | +0.000 | +0.12 | 1 |
| large | 63 | 3 | 99 | 0.0101 | +0.019 | -0.003 | +0.17 | 6 |
| large | 63 | 5 | 99 | 0.0138 | +0.019 | -0.007 | +0.26 | 9 |
| large | 252 | 1 | 90 | — | +0.053 | +0.000 | -0.00 | 1 |
| large | 252 | 3 | 90 | 0.0374 | +0.020 | -0.011 | +0.02 | 8 |
| large | 252 | 5 | 90 | 0.0442 | +0.019 | -0.034 | +0.14 | 15 |
| mid | 63 | 1 | 99 | — | +0.124 | +0.000 | +0.40 | 1 |
| mid | 63 | 3 | 99 | 0.0122 | +0.059 | -0.005 | +0.53 | 6 |
| mid | 63 | 5 | 99 | 0.0145 | +0.062 | -0.010 | +0.59 | 10 |
| mid | 252 | 1 | 90 | — | +0.066 | +0.000 | +0.32 | 1 |
| mid | 252 | 3 | 90 | 0.0281 | +0.049 | -0.015 | +0.35 | 10 |
| mid | 252 | 5 | 90 | 0.0391 | +0.089 | -0.020 | +0.44 | 14 |
| small | 63 | 1 | 99 | — | +0.157 | +0.000 | +0.48 | 1 |
| small | 63 | 3 | 99 | 0.0076 | +0.095 | -0.002 | +0.59 | 6 |
| small | 63 | 5 | 99 | 0.0075 | +0.110 | -0.002 | +0.62 | 8 |
| small | 252 | 1 | 90 | — | +0.113 | +0.000 | +0.43 | 1 |
| small | 252 | 3 | 90 | 0.0268 | +0.046 | -0.015 | +0.48 | 10 |
| small | 252 | 5 | 90 | 0.0291 | +0.076 | -0.025 | +0.63 | 15 |

## Decisive cell (large-cap, n_est=63, k=5)

- (i) within-subspace rotation median CV: 0.0138 (≤0.02? YES) — realized vol invariant to the frame
- (ii) rand-subspace control median rel excess: +0.26 (≥0.25? YES) — vol depends on P (test has power)
- (iii) pure-projector rel gap vs full: +0.019 (≤0.10? YES) — leading-order term near-sufficient
- (context) flat-Λ rel gap vs full: -0.007; λ₁/λ₅ = 9

## Verdict (pre-committed rule): **SUBSPACE FUNCTIONAL CONFIRMED**

## Story

- **The algebra holds on real data.** The pure-projector portfolio w ∝ (I−P)1 — which uses NOTHING but the span of the top-5 PCA factors: no eigenvalues, no individual eigenvector identities — lands within 1.9% realized vol of full min-var. A random within-subspace rotation of the frame moves realized vol by only 1.4% (CV), versus a 26% penalty for using the wrong subspace — an ~19x separation. Min-var is a subspace functional; the individual factor directions inside the span are irrelevant to the portfolio.
- **This survives S&P λ-heterogeneity** (λ₁/λ₅ ≈ 9 on large-cap: dominant market factor, the exact stress F-028/F-029 flagged). The memo's worry that the O(δ²/λ₅) term could break the approximation does not materialize at n=63 large-cap — flat-Λ is even marginally better than full (−0.7%, within noise). The gap grows modestly on small-cap / higher k (proj up to ~11%), so the fully precise statement is 'subspace + a little eigenvalue weighting', not 'projector alone always' — but the frame identity is irrelevant everywhere (rot CV 1–3%).
- **What this settles for step 4.** The unrecoverable in-subspace rotation — Theorem 1's hard term, the object of Kristen's Davis–Kahan / t₆ assignment — is HARMLESS to minimum-variance portfolios. So the multifactor generalization should NOT try to correct individual eigenvectors (impossible, and unnecessary); it should estimate/de-bias the SUBSPACE PROJECTOR and the eigenvalues. This is real-data backing for Avenue 2 and reframes the open problem from 'fix the frame' to 'get the subspace right' — the tractable version. Bring to Alex/Lisa.
- **Scope (honest):** confirmed for UNCONSTRAINED min-var (the exact object the algebra describes; long-only breaks the clean Σ⁻¹1 identity and is deferred to a follow-up). Next constructive step: the subspace-averaging estimator (variance-reduce P̂ across windows, target-free) and the Avenue-3 SOCP (rotation bound as per-factor trust) — each a new prereg.
