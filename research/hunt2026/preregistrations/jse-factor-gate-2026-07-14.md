# Pre-registration — per-factor-gated JSE: correct only the factors the theorem covers

### EXP-2026-07-14-jse-factor-gate

**Stage-0 note.** Kristen's hypothesis (2026-07-14): the estimator program's open k=3–5
question is mis-posed as a count question — the binding constraints are the *per-factor
quality conditions* of the dispersion-bias theorem (factor_lab,
`unified_dispersion_bias_proof_051926_cleaned.md`): per-column prevalence, the ρⱼ > δ²/n
detection threshold, and Assumption-3 spectral separation. Blanket-correcting all k factors
spends the correction's variance cost on factors it does not validly cover. Kristen
approved this Stage-0 directly in session. Supersedes the stale queue item
"JSE k=3–5 unconstrained min-var, walk-forward", which F-021 FINAL already answered for
blanket correction (unconstrained JSE worse at every k and every n; program closed at
"real but tiny long-only edge"). This experiment reopens the program on a genuinely new
axis: WHERE the correction is applied, not how hard.

**Hypothesis** (one falsifiable sentence, mechanism included):
Gating the JSE correction per factor — rotating sample eigenvector hⱼ only when factor j
passes theory-native quality gates (shrinkage estimate ψ̂ⱼ ≥ ψ_min and relative eigengap
gapⱼ ≥ g_min), leaving failing factors as raw PCA — beats blanket correction at k=5,
because the theorem's floor formula stops applying below the detection threshold and the
1/ψ̂ inflation amplifies noise on exactly the weak factors 4–5; supporting evidence
already on record: blanket k=5 underperforms k=3 at n=63 long-only (−1.6 vs −2.0 bps,
F-021 RESOLVED), the signature of weak-factor drag.

**Layer touched** (exactly one) + registered baseline:
Layer B — estimator only. The Estimator Lab walk-forward machinery
(research/estimator_lab/run_minvar.py conventions: same 138 months, same ~450–470-name
point-in-time S&P panel, same monthly rebalance and paired-delta scoring) is held fixed.
Matched pair discipline: the gated variant differs from its baseline ONLY in the gate —
same k, same τ floor on corrected factors, same rotation target (equal-weight q), same
δ̂² estimator. Registered baselines: jse5 (blanket, the direct parent), pca5 (raw), jse3
(the best existing blanket cell, recovery target).

**Alpha type tag**: estimator

**Gate definitions (frozen — the only knobs, no post-hoc quality metrics):**
For each rebalance month, from the sample spectrum of the estimation window
(p assets, n obs, top-k eigenpairs (λⱼ, hⱼ), δ̂² = residual Frobenius / ((p−k)·n)):
- ψ̂ⱼ = sqrt(max(0, 1 − p·δ̂²/sⱼ²)) — the factor_lab shrinkage estimate (its ψ̂ⱼ² > 0 is
  the sample analogue of the ρⱼ > δ²/n detection threshold; ψ_min > 0 demands margin).
- gapⱼ = (λⱼ − λⱼ₊₁)/λⱼ — sample analogue of Assumption-3 separation (λₖ₊₁ from the
  same sample spectrum for j = k).
- Factor j is corrected iff ψ̂ⱼ ≥ ψ_min AND gapⱼ ≥ g_min; otherwise hⱼ enters the
  covariance untouched (raw PCA weight, no rotation, no 1/ψ̂ inflation).

**Registered variants** (6 gate configs, all reported, nothing added after results):
(ψ_min, g_min) ∈ {0.3, 0.5, 0.7} × {0.05, 0.10}, all at k=5.
Decisive cell (pre-committed): **long-only book, n=63** — the regime where the JSE effect
is confirmed alive (F-021 FINAL: long-only helps at every n, largest at small n).
Diagnostics (reported, not decisive): the same 6 configs at n=252 long-only, and both
windows unconstrained (if gating rescues unconstrained min-var, that reopens F-021's
unconstrained verdict — report only; any reopen is its own future prereg).

**Expected result** (numeric, on which evaluator):
Paired monthly realized-vol deltas over the 138 walk-forward months (est-crossover
machinery). Expected: (a) gated_jse5 − jse5 (blanket) median ≤ −0.2 bps realized vol with
paired t significant (p < 0.05) for at least the middle gate configs; (b) gated_jse5
recovers to ≥ jse3's benefit vs pca (closing the k=5-worse-than-k=3 gap); (c) gate
pass-rate diagnostics show factors 1–2 passing in ≥ 90% of months and factors 4–5 failing
in ≥ 30% of months — the empirical "effective k" of the S&P panel, which is the honest
answer to the how-many-factors question.

**Alternative result** (what the world looks like if the hypothesis is false):
Gating deltas within ±0.1 bps of blanket (τ = 0.01 on ψ² already neutralizes weak factors
well enough that the gate is redundant), or gated worse (the correction on weak-but-
detectable factors was earning its keep and the gate removes real signal), or factors 4–5
pass ≥ 90% of months (S&P factors are all strong at these windows — the quality problem
doesn't exist at this p/n and the k question was never about quality).

**Decisive statistic (pre-committed)**: on the decisive cell (long-only, n=63, k=5):
median paired monthly delta (gated − blanket) and its paired t, per gate config. Verdict:
- "gating helps" if ≥ 1 registered config has median ≤ −0.2 bps AND p < 0.05, AND that
  config's gated_jse5-vs-pca5 benefit ≥ jse3-vs-pca3 benefit (recovery condition);
- "redundant" if all configs within ±0.1 bps or p ≥ 0.05;
- "harmful" if all configs ≥ +0.1 bps.
Config selection accounting: 6 registered chances at the decisive cell → n_trials = 6.

**Failure / kill condition** (pre-committed; includes the stop-iterating rule):
One run of the 6 registered configs. No new gate metrics (prevalence proxies, bulk-edge
distances, cross-validated thresholds), no ψ_min/g_min values outside the registered grid,
no k other than 5, no window other than the two registered — regardless of results. If
"redundant" or "harmful" → FAILURES.md entry; the Goldberg program returns to its F-021
FINAL closed state and the stale k=3–5 queue item is retired with it. If "gating helps",
the result is still an estimator-lab finding, NOT a deployment: any live use follows the
existing deployment bar (F-021 FINAL: ≤ ~2.6 bps vol/yr was judged not deployable — gated
would need to clear a materially larger benefit and a separate Stage-4 approval).

**Trial-ledger row**: TRIAL_LEDGER.md — Robustness experiments table, added in the same
commit.

**Derived from prior holdout results?** YES — adaptive loop, twice over: reacts to F-021
FINAL (blanket verdicts at every n) and to the k=5 < k=3 long-only ordering at n=63 that
motivates the gate. Flagged in the ledger row.

**factor_lab scope guard**: the gate formulas cite factor_lab theory
(detection-threshold remark, Assumption 3, ψ̂ estimator from
`dispersion_bias_correction_cleaned.md` §2.4) but ALL implementation lives in alpha-lab's
research/estimator_lab/; factor_lab code is read-only and untouched.

---
**Result** (filled after the run, never edited above this line): **REDUNDANT** (0/6
configs meet the pre-committed rule; decisive-cell medians all +0.00 bps). The ψ̂ gate
never binds — minimum ψ̂ across all 138 months is 0.826 (factor 5), above every registered
ψ_min: the pre-registered alternative world where the S&P top-5 factors are all above the
detection threshold with margin. Only the separation gate binds (f5 fails 40% of months at
g_min=0.10); where it binds the direction favors gating (mean −0.36 bps, 65% hit rate,
pooled t=−2.81 p=0.0057) but ~10x below the bar — the same "real but tiny" family as
F-021 FINAL. Design lesson recorded: median stat can't fire when treatment == control in
most months. FAILURES.md F-026; Goldberg program returns to closed; stale "JSE k=3–5
unconstrained" queue item retired. Full tables + story:
research/estimator_lab/FACTOR_GATE.md.
