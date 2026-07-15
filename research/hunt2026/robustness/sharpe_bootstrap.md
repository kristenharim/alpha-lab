# Sharpe bootstrap — path-luck intervals, 7 live books (2026-07-14)

Circular block bootstrap of daily net returns (n_sims=1000, block=20, seed=0) on each book's own blind-evidence window; frozen specs, baseline Sharpe reproduced against the published result (tol 0.01) before bootstrapping. Complements deflated Sharpe (selection) and the agent6 perturbation grid (parameter sensitivity): this asks whether the point Sharpe survives resampling of its own return path. Read p05 against the kill bar (0.5).

| book | window | obs | sharpe | p05 | median | p95 | pct(orig) | p05 ≥ kill? |
|---|---|---|---|---|---|---|---|---|
| vol_managed_qqq | results (>2025-07-10) | 252 | 1.59 | **0.17** | 1.59 | 3.13 | 0.50 | **FAIL** |
| vol_core_svxy | results (>2025-07-10) | 252 | 1.31 | **-0.11** | 1.33 | 2.85 | 0.48 | **FAIL** |
| dual_momentum_gem | results (>2025-07-10) | 252 | 1.78 | **0.22** | 1.75 | 3.61 | 0.51 | **FAIL** |
| momentum_concentrated | results (>2025-07-10) | 252 | 1.21 | **0.20** | 1.25 | 2.34 | 0.48 | **FAIL** |
| trend_vol_qqq | results5y (>2021-07-10) | 1256 | 1.11 | **0.39** | 1.11 | 1.83 | 0.50 | **FAIL** |
| defensive_ensemble | results5y (>2021-07-10) | 1256 | 1.32 | **0.65** | 1.34 | 2.06 | 0.48 | PASS |
| dual_momentum_gold | results5y (>2021-07-10) | 1256 | 1.07 | **0.44** | 1.08 | 1.72 | 0.49 | **FAIL** |

All 7 books reported, none selected (no new search; n_trials of the underlying books unchanged). A FAIL here is a flag for the 12-month review, not an automatic demotion — the pre-registered kill rules in DEPLOYMENT_MANIFEST.md stay authoritative.

## Story (read before reacting to the FAILs)

- **Baseline gate: 7/7** — every recomputed Sharpe matched the published result before bootstrapping.
- **The holdout-year FAILs are a statement about the window, not the books.** One year of daily data puts a ±1-ish standard error on an annualized Sharpe, so p05 ≈ point − 1.3 is what the arithmetic forces: a 1y blind holdout cannot statistically separate Sharpe 1.3–1.8 from the 0.5 kill bar. This quantifies why the repo also demands 82-window walk-forward + 5y blinds instead of trusting the holdout year alone.
- **The 5y windows are the real test.** defensive_ensemble PASSES (p05 0.65 — consistent with it holding the top deflated-Sharpe probability, 95.8%, in deflated.md). trend_vol_qqq (0.39) and dual_momentum_gold (0.44) sit just under the bar — gold is already watch-tier and hindsight-discounted, so this agrees with the existing classification rather than contradicting it.
- **vol_core_svxy is the one flag worth remembering: p05 −0.11, the only negative.** Its short-vol SVXY sleeve is the classic negative-skew profile — steady gains, occasional crash — and negative skew widens the bootstrap left tail (the −skew·SR term in the Sharpe estimator variance). The smooth curve is partly crash risk, priced in by this metric.
- **pct(orig) ≈ 0.5 everywhere**: no book's headline number depends on a lucky arrangement of its own returns — no sequence-luck pathology.
