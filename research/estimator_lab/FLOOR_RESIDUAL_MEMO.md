# Research memo — does the observable floor survive fundamental-factor residualization?

Solo empirical study (Kristen, 2026-07-14). Object = factor-EXPOSURE estimation error, NOT
minimum-variance portfolios. Grounded in Kercheval–Gunther–Bernstein–Yao–Lan–Lin–Goldberg,
"Estimation Error in Latent High-Dimensional Factor Models" (2026), Theorem 1 + Corollary 1.

## 1. Exact question
After removing known factors with a Barra-like model (oracle OR noisy/estimated), does the
paper's observable floor ℓ/θ_j still (a) RANK and (b) CALIBRATE the true out-of-subspace
exposure error of the residual statistical factors?

## 2. The hidden assumption this actually tests (the sharp version)
Corollary 1's observable floor is derived under ISOTROPIC residual noise (z has cov δ²I; the
bulk sample eigenvalues estimate δ²/n). Residualizing y with a fundamental model applies the
cross-sectional projector M = I − B̃_F(B̃_FᵀB̃_F)⁻¹B̃_Fᵀ to every period, so the residual
noise becomes δ²·M — a RANK-DEFICIENT projector, NOT isotropic — even when B̃_F = B_F
exactly. So the floor may break from residualization ALONE, before any misspecification.
That is the primary thing under test; misspecification is secondary.

## 3. Theorem-faithful target metric
Evaluate the floor against the ESTIMABLE out-of-subspace component ONLY, never the full angle
(the full angle contains the provably-inestimable in-subspace rotation — using it as the
success criterion smuggles the unobservable term back in).
- True out-of-subspace (a)_j = ‖Π⊥_Bsig h_j‖², where Bsig = span of the top-k_R principal
  directions of the ACTUAL residual signal covariance Σ0_res (= M·(BΣ_fBᵀ)·Mᵀ, top-k_R),
  and h_j = j-th sample eigenvector of the residual panel. Computable (we planted everything).
- **Rank discrimination:** Kendall τ between ℓ/θ_j and (a)_j, across factors × MC draws.
- **Calibration (reported SEPARATELY):** coverage P(ℓ/θ_j ≤ full sin²∠(h_j,b_j)) → should
  stay ~1 (it's a lower bound); and slack S_j = (a)_j − ℓ/θ_j (bias of the floor vs the true
  estimable component — should be ~0 if the floor is unbiased; nonzero ⇒ residualization bias).

## 4. Experimental arms (minimal)
- **A0 validation** (k_F=0, M=I): raw planted data, reproduce Corollary 1 — floor tracks (a).
  Gate: if A0 τ is not high, the simulator is wrong, stop.
- **A1 oracle residualization** (B̃_F = B_F): isolates the isotropy-breaking effect alone.
- **A2 estimated residualization** (B̃_F = B_F misaligned by ρ_F): adds correlated
  misspecification; sweep ρ_F ∈ {small, large}.
- **HET** (within A1/A2): residual block has heterogeneous SNR (strong + weak + ~noise
  factors) so τ can measure triage; plus a uniform-low control.
- **NEG** (B_R = 0): no residual factors — the floor MUST flag the spurious top residual
  eigenvalues as high (unreliable), else Cor 1 is misapplied here.

## 5. Regime knobs (frozen small set)
p=500, n=63; k_F=4 strong fundamental; k_R=5 residual with planted per-factor SNR straddling
the detectability edge; δ²=1; ρ_F misalignment (oracle vs estimated); N_MC=200 seeded draws.
Distinct eigenvalues, prevalent (dense) loadings per the paper's Assumption 3. Gaussian
baseline (bounded 4th moment); heavy tails deferred.

## 6. Decision rule (pre-committed)
- **SUCCESS (pursue):** A0 τ ≥ 0.7 (simulator valid) AND A1 (oracle-residualized) τ ≥ 0.5
  with slack near 0 AND NEG flags spurious factors (high floor). ⇒ the floor survives
  residualization; then the misspecification sweep A2 and the n_eff correction are worth it.
- **FAILURE (kill / publish negative):** A1 τ collapses toward 0 or slack is large and
  systematic ⇒ residualization structurally breaks the observable floor (isotropy violation);
  the hybrid-diagnostic idea does not work as-is. This is a clean, citable negative.
- **AMBIGUOUS (⇒ n_eff):** A1 partly degrades vs A0 ⇒ probe whether a degrees-of-freedom
  correction (n → n_eff = n − k_F in the bulk) restores calibration; if it does, that
  correction is the contribution.

## 7. n_eff probe (built into the MVP)
Report the floor computed with the naive bulk (n − k_R trailing eigenvalues) vs a DoF-adjusted
bulk that accounts for the k_F dimensions consumed by residualization; compare slack under each.

## Deferred (do NOT build yet)
Heavy-tail arm; subspace drift across windows; real FF/Barra + real S&P residuals; the hybrid
Corollary-1 theorem and the formal n_eff derivation (theory, only if the empirics justify it);
any portfolio/min-var metric (explicitly out of scope).

---

# Phase 2 addendum — finite-sample calibration of the floor (pre-committed before run)

## Question
When does the observable floor ℓ/θ_j become a good approximation of the true out-of-subspace
error in finite samples, and how biased is it before that?

## Design
Sweep p ∈ {100, 250, 500, 1000} × n ∈ {40, 63, 126}, k_R=5 heterogeneous SNR ladder
{3, 1.5, 0.8, 0.4, 0.15} (straddles the detection edge); k=3 row and an A1
oracle-residualization spot-check at (500, 63) to test transfer. N_MC=200, seeded. Slack
S_j = (a)_j − ℓ/θ_j recorded PER FACTOR with the observable SNR proxy SNR̂_j = θ_j/ℓ − 1.
Dual-space computation (n×n Gram; h_j = Yv_j/√(npθ_j), exact per the paper's Lemma 1).

## Corrections tested (frozen)
- C1 (n_eff-style): floor × n/(n−k).
- C2 (empirical calibration): linear model of slack on [log p, log n, logit(floor)], fit on
  half the (p,n) cells, evaluated on the HELD-OUT half (and on the A1 spot-check).

## Decision rule (pre-committed)
- CALIBRATABLE: a correction using observables only cuts held-out median |slack| to < 0.05
  and ≤ 1/3 of uncorrected.
- REGIME-LIMITED: slack concentrates below an observable detectability cut (small SNR̂);
  above the cut uncorrected |slack| < 0.05. Deliverable = the trust-region rule
  ("interpret the floor only when SNR̂ > c"), not a correction.
- UNCALIBRATABLE: neither — floor bias depends on unobservables everywhere.
Stop-iterating: one run; no new correction forms after seeing results.

---

# Phase 3 addendum — the two pre-named corrections (frozen before run)

## Candidates (exactly two, from Phase-2's measured structure; no others afterward)
- **C3 (n/p-linear correction):** floor' = floor + c·(n/p) with c = 0.5 FROZEN (the Phase-2
  slack law ≈ n/(2p); stated openly as derived from Phase 2 — evaluation is therefore on
  OFF-GRID cells with a NEW seed, so the test is out-of-sample in both grid and randomness).
  Honest note: C3 turns the floor from a conservative lower bound into a calibrated point
  estimate; coverage degradation is reported alongside.
- **C4 (MP-edge-aware trust cut):** trust factor j only if SNRhat_j > 2√(n/p) + n/p + 0.5
  (the dual noise-bulk top edge (1+√(n/p))² − 1, plus frozen margin 0.5), replacing the
  constant SNRhat > 1 cut that Phase 2 showed fails at moderate n/p.

## Evaluation (new cells, seed=1, N_MC=200)
Off-grid: p ∈ {150, 350, 750} × n ∈ {50, 90}; A1 oracle-resid arm at (350, 90); boundary
stress cell (500, 252) (p/n≈2, the real-data 1-year-window regime) reported but EXCLUDED
from pass/fail (the correction claims validity for p/n ≥ 4 only).

## Decision rule (pre-committed)
- **SUCCESS:** on every pass/fail cell, median |slack after C3| among C4-trusted factors
  < 0.05, AND C4 excludes ≥ 90% of planted sub-edge factors (snr < 2√(n/p)+n/p) while
  retaining ≥ 80% of clearly-detectable ones (snr > edge+1).
- **PARTIAL:** pooled median passes but some cell or the exclusion/retention rates fail.
- **FAIL:** neither. Stop-iterating: one run; no new c, margin, or functional forms after
  seeing results. Whatever the outcome, the closed-form derivation of the slack law is lab
  theory (Kristen's), not a further sim-fitting exercise.
