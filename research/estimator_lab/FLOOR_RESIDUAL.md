# Observable floor under residualization — MVP (EXP-floor-residual)

Exposure-error study. floor ℓ/θ_j vs true out-of-subspace (a)_j. τ = rank discrimination (Kendall); coverage = P(floor ≤ full sin²) → want ~1; slack = median((a) − floor) → want ~0. Memo: FLOOR_RESIDUAL_MEMO.md.

| arm | Kendall τ | coverage | median slack | med floor | med (a) |
|---|---|---|---|---|---|
| A0_validation (no resid, het) | 0.844 | 1.00 | +0.170 | 0.478 | 0.641 |
| A1_oracle_resid (het) | 0.848 | 1.00 | +0.176 | 0.479 | 0.646 |
| A2_estimated_resid mis=0.3 (het) | 0.915 | 0.99 | +0.001 | 0.049 | 0.050 |
| A2_estimated_resid mis=0.7 (het) | 0.916 | 1.00 | +0.001 | 0.048 | 0.048 |
| A1_oracle_resid (uniform-low ctrl) | 0.401 | 1.00 | +0.359 | 0.549 | 0.913 |
| NEG (B_R=0, oracle resid) | nan | 1.00 | +0.438 | 0.562 | 1.000 |

## Decision (pre-committed, residualization EFFECT = A1 − A0): **FLOOR SURVIVES oracle residualization (≈ no-op vs baseline) → pursue: finite-p calibration correction + misspecification-leakage handling**
- A0 validation τ = 0.844 (simulator valid)
- residualization Δτ = +0.003, Δslack = +0.007 (oracle A1 vs baseline A0)
- baseline calibration slack (A0) = +0.170 — floor under-reports the true out-of-subspace component at finite p (a correction target, NOT a residualization effect)
- NEG spurious-factor median floor = 0.562 (flags noise as unreliable ✓)

## Story
- **The isotropy worry — my stated primary risk — is negligible here.** Oracle residualization changes the floor's rank discrimination and calibration by ~0 vs baseline (Δτ, Δslack ≈ 0). The residual noise δ²M is rank-deficient, but k_F/p ≈ 0.8% barely perturbs the dual bulk, so the floor is essentially unaffected. My hypothesis that residualization breaks the floor was wrong, and the sim shows why.
- **There IS a baseline finite-p calibration bias** (~0.17 slack): the floor under-estimates the true out-of-subspace component at p=500/n=63 — present WITH OR WITHOUT residualization. This is the real, honest correction opportunity (a finite-p / effective-sample adjustment), and it is NOT a residualization effect.
- **The real confound is misspecification LEAKAGE, and the floor reports it honestly.** With misaligned Barra (A2), the recovered 'residual factors' are actually leaked STRONG fundamentals (median (a) ≈ 0.05 = well-estimated), and the floor correctly calls them reliable (slack ≈ 0). The diagnostic isn't fooled — but a practitioner would be: a low floor on a 'residual' factor can mean 'leaked fundamental,' not 'genuine trustworthy tail factor.' A leakage detector is the needed companion, not a floor fix.
- **The floor can only triage when the tail is heterogeneous.** Uniform-low residual SNR collapses τ to 0.40 (nothing to rank) and inflates slack to 0.36 — and pure noise (NEG) is flagged unreliable but softly (floor 0.56, not ~1).
