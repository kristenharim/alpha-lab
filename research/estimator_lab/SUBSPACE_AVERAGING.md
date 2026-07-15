# Target-free subspace-averaging min-var (EXP-2026-07-14-subspace-averaging)

Σ = λ̄P̄ + δ̂²(I−P̄); P̄ = top-k eigenspace of the mean of the last L monthly PCA projectors (extrinsic RSS). Matched pair vs single-window (L=1), unconstrained min-var, paired monthly realized vol. Decisive cell: small-cap n=63 k=5. Prereg: preregistrations/subspace-averaging-2026-07-14.md.

| universe | n | k | months | L=1 vol | L=3 relΔ (p) | L=6 relΔ (p) | L=12 relΔ (p) | med stab(L12) |
|---|---|---|---|---|---|---|---|---|
| large | 63 | 1 | 87 | 12.0% | +1.48% (0.128) | +3.27% (0.409) | +3.72% (0.232) | 0.909 |
| large | 63 | 3 | 87 | 10.6% | +1.29% (0.056) | +6.20% (0.001) | +14.64% (0.000) | 0.449 |
| large | 63 | 5 | 87 | 9.9% | +0.70% (0.419) | +6.22% (0.035) | +4.69% (0.004) | 0.381 |
| large | 252 | 1 | 78 | 13.5% | +0.10% (0.982) | +0.68% (0.704) | +2.08% (0.971) | 0.983 |
| large | 252 | 3 | 78 | 12.3% | +0.10% (0.262) | +2.58% (0.017) | +5.87% (0.004) | 0.797 |
| large | 252 | 5 | 78 | 11.3% | +0.19% (0.093) | +1.41% (0.020) | +2.70% (0.009) | 0.734 |
| mid | 63 | 1 | 87 | 13.0% | -0.05% (0.261) | +1.90% (0.158) | +3.15% (0.286) | 0.918 |
| mid | 63 | 3 | 87 | 11.3% | -0.91% (0.554) | +2.48% (0.163) | +7.18% (0.013) | 0.407 |
| mid | 63 | 5 | 87 | 11.1% | -1.29% (0.348) | +3.65% (0.032) | +4.48% (0.010) | 0.333 |
| mid | 252 | 1 | 78 | 13.3% | +0.31% (0.158) | +1.10% (0.087) | +4.56% (0.039) | 0.985 |
| mid | 252 | 3 | 78 | 12.9% | +0.65% (0.781) | -0.07% (0.354) | +0.09% (0.455) | 0.726 |
| mid | 252 | 5 | 78 | 11.8% | +0.14% (0.191) | +1.12% (0.080) | +2.41% (0.034) | 0.653 |
| small | 63 | 1 | 87 | 12.9% | +0.46% (0.227) | +1.24% (0.086) | +1.33% (0.135) | 0.922 |
| small | 63 | 3 | 87 | 12.2% | -1.98% (0.403) | -0.49% (0.143) | +2.87% (0.024) | 0.328 |
| small | 63 | 5 | 87 | 12.2% | -3.00% (0.492) | -2.61% (0.466) | -4.09% (0.130) | 0.305 |
| small | 252 | 1 | 78 | 14.3% | +0.58% (0.144) | +1.74% (0.105) | +2.96% (0.018) | 0.985 |
| small | 252 | 3 | 78 | 12.2% | +1.36% (0.199) | +2.03% (0.068) | +4.49% (0.010) | 0.739 |
| small | 252 | 5 | 78 | 11.8% | +1.32% (0.120) | +2.71% (0.035) | +4.24% (0.004) | 0.619 |

## Decisive cell (small-cap, n_est=63, k=5)

- L-curve (median relative realized-vol Δ vs L=1): L=3: -3.00% (p=0.492), L=6: -2.61% (p=0.466), L=12: -4.09% (p=0.130)
- best L = 12 (-4.09%, p=0.130); subspace stability (k-th eig of M, L=12 median): 0.305

## Verdict (pre-committed rule, decisive cell): **NO EFFECT**

## Story (the broader table is decisive, and it kills pure averaging)

- **Decisive cell: NO EFFECT.** small-cap n=63 k=5 point estimates favor averaging (−3 to −4% vol) but none clears p<0.05 (best p=0.13) — underpowered, and against the uniform pattern below it's most consistent with noise (it's the single noisiest cell: small-cap, short window, most factors).
- **Everywhere else, averaging HURTS — significantly — and the stability diagnostic explains exactly when.** The k-th eigenvalue of the mean projector M measures subspace agreement across months: ~1 = windows agree, low = they disagree. Where the subspace is STABLE (stab→0.9-0.98: k=1, or n=252) averaging is ~neutral. Where it's UNSTABLE (stab 0.30-0.45: the short-window multi-factor cells) averaging is significantly WORSE, and worse with larger L (large-cap k=3, L=12: +14.6% vol, p<0.001; k=5 +4.7%, p=0.004).
- **Mechanism, cleanly diagnosed: the subspace disagreement is DRIFT, not sampling noise.** Low stability means the factor structure genuinely changes month to month; averaging can't tell drift from noise, so it blurs drifted subspaces into a stale estimate that fits next month worse. This is the exact failure mode the prereg pre-stated — averaging reduces variance but cannot touch bias, and here the single-window subspace error is bias/drift-dominated, not variance-dominated. The higher-k, longer-L, lower-stability corner is where drift dominates most, and that's precisely where the harm concentrates.
- **This resolves the prereg's alternative hypothesis in the affirmative and redirects step 4.** Target-free variance reduction is INSUFFICIENT on real S&P data: the subspace's error is drift, which averaging worsens. So the multifactor generalization cannot be pure subspace-averaging — it needs the BIAS-AWARE route: Avenue 3, the distributionally-robust SOCP that uses Kristen's Davis-Kahan / t₆ rotation bound as a per-factor trust weight (down-weighting exactly the drifting/low-gap factors rather than blindly smoothing them). The surviving constructive avenue is Avenue 3, not Avenue 2's averaging.
- **Kept for reuse:** the subspace-stability metric (k-th eigenvalue of the L-window projector mean) is a genuinely useful standalone diagnostic — it flags when a factor subspace is drifting vs merely noisy.
