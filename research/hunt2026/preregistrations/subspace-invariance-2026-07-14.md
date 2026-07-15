# Pre-registration — is min-var a subspace functional? (rotation-invariance test, Avenue 2)

### EXP-2026-07-14-subspace-invariance

**Stage-0 note.** Kristen's call, 2026-07-14: test the central algebraic claim from the
step-4 design exploration (four-subagent synthesis). Avenue 2 (Grassmannian) derived that
for a factor-plus-residual covariance Σ = HΛHᵀ + D, unconstrained min-var
w ∝ Σ⁻¹1 = δ⁻²(I − P)1 + HΛ⁻¹Hᵀ1, i.e. w ∝ (I − P)1 + O(δ²/λ) — the portfolio depends on
the subspace projector P = HHᵀ only, and the *individual* eigenvectors (the "frame", the
unrecoverable in-subspace rotation of Theorem 1) enter solely through the O(δ²/λ)
correction. If true on real data, the impossible part of the multifactor problem is
HARMLESS to min-var and step 4 should operate on the subspace, not the frame. This is a
MEASUREMENT/diagnostic (an algebraic claim about the estimator), not a return or alpha
claim; no live spec is touched.

**Hypothesis** (one falsifiable sentence, mechanism included):
Realized out-of-sample min-var volatility is (near-)invariant to a random within-subspace
rotation of the estimated factor frame (H → HR, R ∈ O(k), which leaves P = HHᵀ exactly
unchanged) while remaining strongly sensitive to the subspace P itself, because min-var is
a subspace functional to O(δ²/λ); the residual frame-dependence is largest where the
retained-factor eigenvalue spread is largest (S&P large-cap: dominant market λ₁ ≫ weak λ₅).

**Layer touched** (exactly one) + registered baseline:
Layer B — estimator diagnostic. Fixed k-factor covariance Σ = HΛHᵀ + D from the trailing
window (H, Λ = top-k SVD; D = diag idiosyncratic residual var), UNCONSTRAINED min-var
w ∝ Σ⁻¹1 via minvar_weights (the exact object the algebra describes; long-only reported as
robustness). Baseline = the raw full-frame PCA min-var (R = I).

**Alpha type tag**: estimator (diagnostic; realized-risk metric, not return).

**Portfolios compared (per universe, window, month), all from the SAME H, Λ, D:**
- **full**: Σ = HΛHᵀ + D → w_full (baseline).
- **rot(R)**: Σ_R = (HR)Λ(HR)ᵀ + D for M=20 Haar-random orthogonal k×k R → {w_R};
  P is provably unchanged (assert ‖(HR)(HR)ᵀ − HHᵀ‖ < 1e-10 once). Frame identity scrambled.
- **flat**: Σ = λ̄P + D (within-subspace spectrum collapsed to its mean) → w_flat.
- **proj**: w ∝ (I − P)1, sum-normalized → w_proj (pure leading-order term, no eigenvalues).
- **CONTROL rand-subspace**: P̃ = projector onto a Haar-random k-dim subspace of ℝ^p
  (M=20 draws) → w_ctl. Changes P entirely; the power check that vol DOES depend on P.

**Metrics (realized next-month annualized vol of each portfolio's OOS return):**
- within-subspace rotation CV = std_R(V_rot)/mean_R(V_rot), per month, median over months.
- rel gaps (median over months): (V_flat − V_full)/V_full ; (V_proj − V_full)/V_full ;
  control (V_ctl − V_full)/V_full.

**Registered cells:** universe ∈ {large S&P500, mid S&P400, small S&P600} × window
∈ {63, 252}, k = 5 primary (k = 1, 3 reported — rotation test needs k ≥ 2). Decisive cell:
**large-cap, n_est=63, k=5** — the most λ-heterogeneous (dominant market factor), the
hardest test of the O(δ²/λ) approximation.

**Decisive statistic (pre-committed), decisive cell:**
- (i) within-subspace rotation median CV ≤ 0.02 (realized vol ~invariant to the frame);
- (ii) control rand-subspace median rel excess ≥ 0.25 (vol IS sensitive to P — test has power);
- (iii) proj median rel gap vs full ≤ 0.10 (leading-order projector term is near-sufficient).
Verdict:
- "SUBSPACE FUNCTIONAL CONFIRMED" if (i) AND (ii) AND (iii);
- "FRAME-IDENTITY IRRELEVANT, WEIGHTING MATTERS" if (i) AND (ii) but (iii) fails (the frame
  ordering doesn't matter but the eigenvalue weighting does — partial, still redirects step 4
  to the subspace + eigenvalues);
- "FRAME MATTERS — approximation breaks on S&P λ-heterogeneity" if (i) fails;
- "NO POWER" if (ii) fails (design invalid; do not interpret (i)).

**Expected result:** (i) holds (small CV), (ii) holds strongly (random subspace is far
worse), (iii) is the live question — proj may lose more than 10% on large-cap because λ₁≫λ₅
makes the O(δ²/λ₅) term non-negligible; if so the honest read is "subspace + eigenvalues,
not pure projector."

**Alternative result:** within-subspace CV is large (frame genuinely matters) — Avenue 2's
leading-order claim does not survive S&P eigenvalue heterogeneity, and step 4 cannot ignore
the frame. That would partially rehabilitate targeted-eigenvector approaches.

**Failure / kill condition (stop-iterating):** one run of the registered cells. No other k,
window, universe, or M after seeing results; no alternative rotation laws. Follow-ups
(subspace-averaging estimator, the Avenue-3 SOCP) are new preregs. Result → a CONFIDENCE/
findings note (confirmation) or FAILURES.md (if the claim breaks); no live spec touched.

**Trial-ledger row:** same commit. n_trials = 1 (diagnostic — a single algebraic claim,
no strategy search; deflation N/A, flagged as measurement per the ops-reality precedent).
**Derived from prior holdout results?** YES — reacts to F-028/F-029 (dominant well-estimated
market factor ⇒ the λ-heterogeneity that stresses the approximation) and to the step-4
subagent synthesis. factor_lab read-only; all code in research/estimator_lab/.

---
**Result** (filled after the run, never edited above this line): **SUBSPACE FUNCTIONAL
CONFIRMED** — all three pre-committed conditions met at the decisive cell (large-cap,
n=63, k=5): (i) within-subspace rotation median CV 0.0142 ≤ 0.02 (vol invariant to the
frame), (ii) rand-subspace control +0.26 ≥ 0.25 (vol depends on P — ~19x more than on the
frame), (iii) pure-projector w∝(I−P)1 median gap +1.9% ≤ 10% (leading-order term
near-sufficient). Holds despite λ₁/λ₅≈9; flat-Λ marginally BETTER than full (−0.7%). The
in-subspace rotation (Theorem 1's hard term / Kristen's Davis-Kahan assignment) is harmless
to min-var ⇒ step 4 should de-bias the SUBSPACE + eigenvalues, not individual eigenvectors.
Confirmation (not a failure) — recorded in CONFIDENCE_LADDER.md, no FAILURES entry. Scope:
unconstrained min-var (exact-algebra object); long-only deferred. Full tables + story:
research/estimator_lab/SUBSPACE_INVARIANCE.md.
