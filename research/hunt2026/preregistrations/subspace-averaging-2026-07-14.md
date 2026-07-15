# Pre-registration — target-free subspace-averaging min-var estimator (Avenue 2 constructive)

### EXP-2026-07-14-subspace-averaging

**Stage-0 note.** Kristen's call, 2026-07-14: the constructive follow-through on
EXP-2026-07-14-subspace-invariance (CONFIRMED: min-var is a subspace functional — realized
vol depends on the projector P, not the individual eigenvectors; CONFIDENCE_LADDER.md).
That result says the way to improve min-var is to improve the *subspace estimate* P̂, and
the only target-free move available is to **variance-reduce P̂ by averaging projectors
across time** (extrinsic Grassmannian mean; Ramírez–Santamaría–Scharf). This is the
"subspace-averaging estimator" from the step-4 subagent synthesis. Estimator research only;
no live spec touched; deployment stays gated by F-021 FINAL + a separate Stage-4.

**Hypothesis** (one falsifiable sentence, mechanism included):
Replacing the single-window PCA subspace P̂_m with the top-k eigenprojector P̄_m of the
average (1/L)·Σ_{l=0}^{L-1} P̂_{m-l} lowers realized out-of-sample min-var volatility for
some L>1, because the single-window subspace is partly sampling noise that averaging
cancels — but only up to the point where subspace *drift* (staleness of older windows)
reintroduces more error than the variance reduction removes, so the benefit is
interior-optimal in L and largest where the single-window subspace is noisiest (short
window, small-cap).

**Known limit (pre-stated honestly):** averaging reduces the *variance* of P̂ but NOT the
dispersion-bias *floor* — every window shares the same tilt of the estimated subspace away
from the truth, so the mean inherits it (cannot self-correct bias; only more time-series
per window shrinks the floor). Therefore the estimator can only win to the extent the
single-window subspace error is variance-dominated. F-028/F-029 showed ψ̂₁≈0.98 (the market
direction is already well-pinned = low variance there), so any gain must come from the weak
factors 2…k; whether that nets a realized-vol improvement is the open question.

**Layer touched** (exactly one) + registered baseline:
Layer B — estimator only, Estimator Lab machinery held fixed (same PIT universes, monthly
rebalance, unconstrained min-var w ∝ Σ⁻¹1 via minvar_weights). Subspace-only covariance
Σ = λ̄·P + δ̂²·(I − P), λ̄ = mean retained eigenvalue, δ̂² = idio floor (the frame is
irrelevant per the confirmed result, so a scalar in-subspace level is used — this also
matches the "flat-Λ ≈ full" finding). Matched pair: **P = P̄ (averaged, L>1) vs P = P̂_m
(single window, L=1)** — identical everything else. Baseline gate: L=1 through the averaging
code path reproduces the single-window estimator exactly; and that estimator's realized vol
matches the confirmed experiment's "flat" arm (tol on the shared cells).

**Alpha type tag**: estimator (risk-model; realized-risk metric, not return).

**Averaging scheme (frozen):** overlapping 1-month-spaced windows (natural with monthly
rebalance): at month m, average the L most recent monthly PCA projectors {P̂_m,…,P̂_{m-L+1}},
each rank-k from the trailing n_est days; P̄ = top-k eigenspace of their Euclidean mean M
(extrinsic/RSS mean). Report the k-th eigenvalue of M as the subspace-stability diagnostic
(→1 = windows agree, averaging changes little; <1 = disagreement, real de-noising). Months
with fewer than L available prior projectors are skipped (identical month set across L for
paired comparison).

**Registered variants** (3 treatment L + baseline): L ∈ {3, 6, 12}, plus L=1 baseline.
Universe ∈ {large S&P500, mid S&P400, small S&P600} × window ∈ {63, 252}, k=5 primary
(k=1,3 reported — k=1 subspace is a single direction, averaging still defined). Decisive
cell: **small-cap, n_est=63, k=5** — the noisiest single-window subspace, most headroom for
variance reduction.

**Decisive statistic (pre-committed), decisive cell:** paired monthly realized-vol delta
(subspace-averaged − single-window), per L, over the shared month set. Verdict on the BEST
registered L:
- "averaging helps" if median relative delta ≤ −0.5% AND paired p < 0.05 AND the L-curve is
  interior-shaped (best L is 3/6/12, not degenerate) OR monotone-improving within the grid;
- "no effect" if every L has |median relative delta| < 0.5% or p ≥ 0.05;
- "harmful" if the best L still has median relative delta ≥ +0.5% at p < 0.05 (staleness
  bias dominates variance reduction everywhere — consistent with a bias-dominated regime).
Selection over L = n_trials 3 at the decisive cell.

**Expected result:** small realized-vol reduction at moderate L (≈3–6) on the noisiest cells
(small-cap n=63), fading or reversing at L=12 (staleness); ≈0 on large-cap n=252 (subspace
already stable, k-th eigenvalue of M near 1). Magnitude likely single-digit bps — an
estimator finding, not a deployable edge, per the whole JSE record.

**Alternative result:** no L helps anywhere (the single-window subspace is bias-dominated —
the dispersion tilt, not sampling noise, drives its error — so averaging, which can't touch
bias, does nothing), or averaging hurts (drift dominates). Either would say target-free
variance reduction is insufficient and step 4 needs the bias-aware / rotation-bound route
(Avenue 3) rather than pure averaging.

**Failure / kill condition (stop-iterating):** one run of the registered grid. No other L,
no intrinsic (Karcher) mean, no non-overlapping/EWMA weighting schemes, no k or window
additions after seeing results. Any such follow-up is a new prereg. Result → CONFIDENCE
note (if it helps) or FAILURES.md (if null/harmful); no live spec touched regardless.

**Trial-ledger row:** same commit. n_trials = 3 (the L sweep). **Derived from prior holdout
results?** YES — reacts to EXP-2026-07-14-subspace-invariance (subspace sufficiency) and
F-028/F-029 (well-pinned market factor ⇒ gains, if any, live in the weak factors).
factor_lab read-only; all code in research/estimator_lab/.

---
**Result** (filled after the run, never edited above this line): **NO EFFECT** at the
decisive cell (small-cap n=63 k=5: point estimates favor averaging −3 to −4% vol but best
p=0.13, underpowered) — and the broader table is decisive: averaging is significantly
HARMFUL almost everywhere else (large-cap k=3 L=12 +14.6% vol p<0.001; k=5 +4.7% p=0.004).
The subspace-stability diagnostic (k-th eigenvalue of the projector mean) explains it: where
the subspace is stable (stab→0.9-0.98) averaging is neutral; where it's unstable
(stab 0.30-0.45, the short-window multi-factor cells) averaging hurts, worse with larger L.
Mechanism: the subspace disagreement is DRIFT, not sampling noise — averaging can't touch
bias and blurs drifted subspaces into a stale fit. This confirms the prereg's alternative:
the single-window subspace error is drift/bias-dominated, so target-free variance reduction
is INSUFFICIENT. Step 4's surviving constructive avenue is the BIAS-AWARE Avenue 3
(rotation-bound SOCP), not pure averaging. Baseline gate passed (L=1 == single-window
projector exactly). Kept the subspace-stability metric as a reusable drift diagnostic.
FAILURES.md F-030. Full tables + story: research/estimator_lab/SUBSPACE_AVERAGING.md.
