# Pre-registration — rotation-bound robust min-var: per-factor trust from the Davis-Kahan/t₆ bound (Avenue 3)

### EXP-2026-07-14-robust-rotation-socp

**Stage-0 note.** Kristen's call, 2026-07-14: the last surviving constructive avenue from the
step-4 synthesis, and the one motivated by F-030 (target-free averaging fails because subspace
disagreement is drift, which a bias-aware method should down-weight). Avenue 3 wraps each PCA
eigenvector ĥ_j in an angular ball of radius θ_j set by the theorem's in-subspace rotation
bound (Kristen's Davis-Kahan / t₆ Monte-Carlo, reused verbatim from run_theorem_complete.py's
rotation_mc), and solves worst-case min-var over that set. Target-free (no reference
direction); the bound enters as a per-factor trust weight. Estimator research; no live spec.

**Implementation note (honest):** the exact robust program min_w max_{Σ∈U} wᵀΣw is a convex
SOCP whose worst-case per-factor variance is (|c_j|cosθ_j + s_j sinθ_j)² with c_j=ĥ_jᵀw,
s_j=‖P_⊥j w‖. This experiment implements the **no-cross-term reduction** — a fixed PSD
covariance Σ_rob = D + Σ_j λ_j[cos²θ_j ĥ_jĥ_jᵀ + sin²θ_j(I − ĥ_jĥ_jᵀ)] — which is the
Cauchy-Schwarz lower bound of the true robust variance (drops the ≥0 cross term) and captures
the identical per-factor trust mechanism (trust confident loading by cos²θ_j, inflate
off-factor cross-risk by λ_j sin²θ_j) with NO new solver dependency. Faithful in spirit, plugs
into minvar_weights. The full SOCP is a later prereg only if this reduction shows signal.

**Hypothesis** (one falsifiable sentence, mechanism included):
Building min-var on Σ_rob with per-factor sin²θ_j = the MC rotation bound rot̄_j (so
well-separated factors are trusted, drifting/low-gap factors are down-weighted) lowers
realized OOS min-var vol relative to raw PCA min-var AND relative to a uniform-θ robust
control — because distrust is allocated by the theorem to exactly the factors F-030 showed
drift most.

**Tension with prior result (pre-stated):** EXP-2026-07-14-subspace-invariance CONFIRMED that
min-var is a subspace functional — it uses the projector P, not the individual within-subspace
directions. The rotation bound θ_j is precisely about the within-subspace rotation that result
showed is HARMLESS to min-var. So the honest prior is that the per-factor structure will ≈ its
uniform control (both acting mainly through the isotropic ridge Σλ_j sin²θ_j = shrink toward
isotropy), i.e. the rotation bound adds little to min-var beyond generic shrinkage. A
per-factor win would be a genuine surprise implying the O(δ²/λ) frame-carrying correction is
large enough to matter; a per-factor ≈ uniform result CLOSES the loop (rotation bound
irrelevant to min-var, consistent with subspace-invariance).

**Layer touched** (exactly one) + registered baselines:
Layer B — estimator only, machinery fixed (PIT universes, monthly rebalance, unconstrained
min-var w∝Σ⁻¹1). Same H, Λ, D (diag idio) as raw PCA; robust only adds the θ structure.
Baselines: **full** (raw PCA k-factor min-var — the θ=0 case, baseline gate: sin²θ=0
reproduces full exactly), **lw** (Ledoit-Wolf — the generic-shrinkage reference: does robust
beat off-the-shelf shrinkage), and the **uniform-θ robust control** (all θ_j = θ̄,
sin²θ̄ = mean_j rot̄_j — isolates whether the bound's PER-FACTOR structure matters).

**Alpha type tag**: estimator (risk-model; realized-risk metric).

**Rotation bound (frozen):** per (month, window): ρ̂_j = (s_j²/p)·ψ̂_j² (debiased factor
strength, as in run_theorem_complete), rot̄_j = seeded MC (R=500) of sin²∠(ν_j,e_j) under
Φ~t₆ scaled to ρ̂ — the exact rotation_mc used in F-027. sin²θ_j = clip(κ·rot̄_j, 0, 0.999).

**Registered variants:** rob_perfactor at κ ∈ {0.5, 1 (decisive — the raw theorem bound,
untuned), 2}; rob_uniform at κ=1; plus full and lw. Universe ∈ {large S&P500, mid S&P400,
small S&P600} × window ∈ {63, 252}, k=5 (rotation MC needs k≥2). Decisive cell: **large-cap,
n_est=63, k=5** (primary universe, largest per-factor θ spread: f1 trusted, f2-5 distrusted).

**Decisive statistic (pre-committed), decisive cell, κ=1:** paired monthly realized-vol.
- (A) benefit: rob_perfactor vs full — median relative delta and paired p.
- (B) novelty: rob_perfactor vs rob_uniform — median relative delta and paired p.
Verdict:
- "PER-FACTOR TRUST HELPS" if (A) ≤ −0.5% p<0.05 AND (B) ≤ −0.25% p<0.05 (robust helps AND
  the per-factor structure beats uniform — the rotation bound earns its keep);
- "UNIFORM ROBUSTNESS ONLY" if (A) ≤ −0.5% p<0.05 but (B) not significant (robust helps as
  generic shrinkage, the per-factor bound adds nothing — closes the loop with subspace-invariance);
- "NO EFFECT" if (A) not significant;
- "HARMFUL" if (A) ≥ +0.5% p<0.05.
Also report rob vs lw (does any robust variant beat off-the-shelf shrinkage) and the κ curve
(is κ=1 the raw bound doing the work, or does a tuned κ dominate — if best κ ≠ 1, the raw
bound is not what helps). n_trials = 4 (κ sweep + uniform).

**Expected result:** per prior tension — robust likely ≈ full or a small isotropic-shrinkage
gain; per-factor ≈ uniform (no heterogeneity benefit); unlikely to beat lw. A clear per-factor
win would contradict subspace-invariance and be the interesting outcome.

**Alternative result:** per-factor genuinely beats uniform and full → the rotation bound
carries min-var-relevant information after all → escalate to the full SOCP (new prereg).

**Failure / kill condition (stop-iterating):** one run of the registered grid. No other κ,
no full-SOCP solve, no k/window/universe additions, no alternative bound definitions after
seeing results. Follow-ups are new preregs. Result → CONFIDENCE note (if per-factor helps) or
FAILURES.md (null/uniform-only/harmful); no live spec touched.

**Trial-ledger row:** same commit. **Derived from prior holdout results?** YES — reacts to
F-030 (drift ⇒ need bias-aware down-weighting), EXP-2026-07-14-subspace-invariance (the tension),
F-027 (reuses its rotation_mc). factor_lab read-only; code in research/estimator_lab/.

---
**Result** (filled after the run, never edited above this line):
