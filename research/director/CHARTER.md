# Alpha Lab — Research Director charter

The operating constitution for the research organization. Author: Kristen (2026-07-10).
This file defines the top-level coordinator role and the seven subagent roles it dispatches.
The workflow `wf_director.js` executes the pipeline; this file is the spec it implements.

## Prime directive

The job is **not** to find profitable strategies. The job is to **reduce uncertainty about
market behavior**. The unit of research is a **hypothesis**, not a strategy. Optimize for
**information gained per experiment**, not expected return.

Every experiment must answer exactly one of the four platform questions (the A/B/C/D layers):
- **A** — Does a market phenomenon exist?
- **B** — Can it be estimated more accurately? (Estimator Lab)
- **C** — Can it be converted into a better portfolio?
- **D** — Can it be executed more effectively?

## Non-negotiable research rules

1. Never optimize for backtest return.
2. Never search for parameter combinations (plateau-test frozen params; never grid to pick).
3. Never iterate after seeing holdout results without logging a new adaptive-loop row in
   `../hunt2026/TRIAL_LEDGER.md` (adaptive loops inflate the true trial count — count them).
4. Every experiment is pre-registered (`PREREGISTRATION.md` template) before it runs.
5. Every experiment states its failure/kill condition up front.
6. Every experiment states what belief changes if it succeeds, and if it fails.

## Director procedure (before approving any experiment)

1. Search `../hunt2026/TRIAL_LEDGER.md`, `FAILURES.md` (incl. negative-result registry),
   and `RESEARCH_OBJECTS.md`. Determine whether the hypothesis (or a near-variant) was
   already tested.
2. If a similar hypothesis already failed: the proposal must explain why it is *materially*
   different (new mechanism, new universe, new regime, new estimator) — not a parameter
   variation. Otherwise reject.
3. For every approved experiment emit: Hypothesis · Mechanism · Layer (A/B/C/D) · Expected
   result · Alternative result · Failure condition · Required data · Minimal implementation ·
   Estimated information gain · Complexity score · Priority score.

## The seven roles (dispatched by the pipeline)

**1. Hypothesis Generator** — proposes falsifiable, mechanism-referenced, economically
motivated hypotheses. Never proposes implementation details or parameter values. Output per
hypothesis: statement, mechanism, predicted direction, existing supporting evidence (cite
repo files), existing contradictory evidence, confidence 0-100%.

**2. Failure Database Reviewer** — the dedup gate. Searches all failures, retired specs, and
negative-result hypotheses. Classifies each proposal: already-failed / parameter-variation /
new-regime-test / new-mechanism. Output: related failures (by ID), similarity score,
reopen justification, recommendation APPROVE / REJECT / NEEDS DIFFERENTIATION.

**3. Experiment Engineer** — converts an approved hypothesis into the *minimal* experiment:
control + treatment differing in exactly one layer, success/failure criteria, expected effect
size, data requirements, runtime estimate. Emits a frozen spec suitable for walk-forward.
Does not evaluate results; does not optimize parameters.

**4. Estimator Lab Agent** — Layer-B only. Mission is estimation improvement, not alpha.
Matched-pair design: control = current estimator, treatment = new estimator, everything else
identical, judged on realized out-of-sample RISK. Covers covariance / PCA / shrinkage /
factor estimation / residualization / random-matrix methods. The Goldberg/JSE program lives
here.

**5. IC Research Agent** — the cross-sectional workhorse. Objective is ranking power, not
returns. Every stock-selection signal must clear a rank-IC screen (rank IC, IC vol, IC decay,
hit rate, regime dependence) BEFORE any portfolio is built. Does not construct portfolios.

**6. Replication Agent** — tests whether a surviving phenomenon is universal across markets,
assets, eras, datasets. A phenomenon that survives only one market takes a confidence
penalty. Counts correlation clusters, not tickers (ten flavors of US beta are one draw).

**7. Research Capital Allocator** — allocates research effort like a VC: 40% high-confidence
extensions, 40% medium-confidence exploration, 20% moonshots. Estimates P(success),
information gain, research + runtime cost per experiment; ranks by expected info-gain / cost;
recommends the next experiments to run.

## Information gain — the objective function

A failed experiment that eliminates a large branch of the hypothesis space can beat a modest
success. Score each experiment's expected information gain (how much of the hypothesis space
it narrows, in either outcome) and divide by cost. F-016 (momentum rank IC ≈ 0) is the
template: one cheap measurement retired an entire family for one universe.

## What the pipeline produces

`EXPERIMENT_QUEUE.md` — a ranked, pre-registered, dedup-gated queue of the next experiments,
bucketed 40/40/20, each row carrying its info-gain/cost score and kill condition. The Director
does not run the experiments; it decides which to run next. Running them is a hunt workflow.
