# Pre-registration — JSE crossover in n, and can ψ̂ predict when JSE helps?

### EXP-2026-07-10-est-crossover (EXP-EST-CROSSOVER)

**Hypothesis** (one falsifiable sentence, mechanism included):
The JSE dispersion-bias correction's benefit to long-only min-var is a monotone
function of estimation-window length n — it helps where ψ̂ is meaningfully below 1
(small n), fades as ψ̂ → 1 (large n) — and the OBSERVABLE median ψ̂, computed from the
estimation window alone (available before any portfolio is built), predicts the sign
of the month's paired jse−pca realized-vol delta.

**Layer touched** (exactly one) + registered baseline:
Layer B — estimator only. Design held exactly as the Estimator Lab walk-forward
(research/estimator_lab/run_minvar.py conventions: PIT S&P 500 members, monthly
rebalance 2015-02 → 2026-06, 137 shared months, k=3, 5% cap, hold d+1…next_d,
delisted→0). Baseline = pca3 (raw PCA, k=3); test = jse3, matched pair per month.
Only the estimation window n varies: n ∈ {42, 63, 90, 126, 189, 252}. Months are
restricted to those with ≥252 days of history so all six n share the identical
month set (clean pooling).

**Alpha type tag**: estimator

**Expected result** (numeric, on matched-pair walk-forward deltas):
- Long-only paired Δ (jse3 − pca3, realized next-month ann. vol): negative and
  significant (paired t, p < 0.05) for n ≤ ~90 (order −1 to −3 bps, per the n=63
  run); shrinking toward 0 by n ≈ 126–189; ~0 to slightly positive at n = 252.
  Monotone (non-decreasing) in n.
- Unconstrained paired Δ: ≥ 0 at ALL n (correction noise amplified by unconstrained
  weights), largest at the smallest n.
- Predictor (the real prize): per month log median ψ̂ across the k=3 factors,
  eigengap (λ₁−λ₂)/λ₁, p/n — all computed from the estimation window only. Pooled
  across all n × months, long-only monthly Δ correlates POSITIVELY with median ψ̂
  (higher ψ̂ → less JSE help), Spearman p < 0.05. Pre-committed thresholds: months
  with median ψ̂ < 0.90 show mean Δ < 0 (JSE helps); months with median ψ̂ ≥ 0.95
  show no improvement (Δ ≈ 0 or > 0).

**Alternative result** (what the world looks like if the hypothesis is false):
No n shows a significant long-only improvement (the n=63 result was a fluke of that
one window length), or the Δ-vs-n profile is non-monotone noise, or ψ̂ is
uncorrelated with the paired delta (pooled Spearman |ρ| ≈ 0, p ≥ 0.05) — the
theory's observable has no predictive content and "ψ̂-gated JSE" is not a rule,
just a description of two runs.

**Failure / kill condition** (pre-committed; decidable from the run's output):
KILL if (a) no n ∈ {42, 63, 90, 126, 189, 252} has long-only jse3 beating pca3 with
paired-t p < 0.05, OR (b) the pooled long-only Spearman correlation of monthly Δ
with that month's median ψ̂ is not significant at p < 0.05. Stop-iterating rule:
one run of the six registered windows; no post-hoc window additions, no k retuning,
no threshold search beyond reporting the pre-committed 0.90 / 0.95 cuts (any scanned
"best" threshold is reported as in-sample color only, never as the finding).

**Trial-ledger row**: TRIAL_LEDGER.md — robustness-experiment row added in the same
commit (1 experiment, 6 registered window lengths, adaptive loop YES).

**Derived from prior holdout results?** YES — adaptive loop: the design reacts to
F-021 (JSE dead at n=252) and its n=63 reopen (JSE helps long-only, t up to 6.5).
The two endpoint results are already known; the pre-registered NEW content is the
four unseen windows (42, 90, 126, 189), the monotonicity claim, and the ψ̂ predictor
test (no prior run logged ψ̂ per month). Flagged in the ledger.

---
**Result** (filled after the run, never edited above this line):
