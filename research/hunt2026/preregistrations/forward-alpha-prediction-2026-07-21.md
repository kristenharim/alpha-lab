# Pre-registration — does the fitted-benchmark reading predict the forward result?

### EXP-2026-07-21-forward-alpha-prediction

**This amends nothing.** The alpha-forward experiment (2026-07-14) already fixed its evaluator,
its thresholds and its review dates before any forward data existed, and none of that moves here.
What is missing is a written-down PREDICTION. Without one, the 6m and 12m reviews can be read
after the fact to agree with whatever `memos/hunt2026-benchmark-and-cost-review-2026-07-21.md`
concluded, which would make that memo unfalsifiable. This registers the prediction while the
forward sample is still six days old.

**Hypothesis** (one falsifiable sentence, mechanism included):
The hunt's holdout returns were factor exposure rather than selection skill, so when each live
book is scored against a benchmark that captures its actual exposures, forward alpha will be
indistinguishable from zero for every book except `dual_momentum_gold`, and `momentum_concentrated`
will additionally keep paying 40 to 60 bps per fill in single-name execution that the frozen cost
model does not charge.

**Layer touched** (exactly one) + registered baseline:
None. Measurement only. No spec, weight, allocation or scheduler change follows from this
document under any outcome. The baseline is the alpha-forward experiment's own frozen M2/M2g
replication (`research/attribution/frozen_betas_2026-07-14.json`).

**Alpha type tag**: attribution

**Expected result** (numeric, on which evaluator):

Evaluator 1, `scripts/hunt_alpha_review.py --evaluate` at the pre-existing review dates
(6m 2027-01-14, 12m 2027-07-14). Per-book prediction of the 12m Newey-West t on forward alpha,
against that experiment's own frozen thresholds (t ≥ 2.4 promising, t < 2.0 or negative =
factor-harvesting confirmed):

| book | fitted alpha at 58 bps (holdout) | predicted 12m forward outcome |
|---|---|---|
| dual_momentum_gold | +25.80%, t 2.11 | the only book that may reach t ≥ 2.0 |
| dual_momentum_gem | +10.73%, t 0.79 | t < 2.0 |
| defensive_ensemble | +6.70%, t 1.36 | t < 2.0 |
| momentum_concentrated | -4.32%, t -0.34 | t < 2.0 |
| vol_managed_qqq | -4.57%, t -0.71 | t < 2.0 |
| vol_core_svxy | -6.06%, t -1.05 | t < 2.0 |
| trend_vol_qqq | -7.15%, t -0.71 | t < 2.0 |

Evaluator 2, `research/hunt2026/exec_side_split.py` on the accumulated MC fills. Predicted at the
12m date, or earlier once the sell leg reaches n ≥ 20 fills:
- median exec cost per fill in [40, 60] bps;
- POSITIVE on both sides independently, buys and sells, each with n ≥ 20.

**Alternative result** (what the world looks like if the hypothesis is false):
A book other than `dual_momentum_gold` reaches 12m NW t ≥ 2.0, or `momentum_concentrated` does.
Then the six-ETF fitted benchmark used in the memo was mis-specified, or the holdout year was
unrepresentative of the books' factor loadings, and the memo's central claim that the field was
harvesting beta is wrong. Separately, if measured execution falls below 20 bps per fill once the
sample grows, or flips negative on either side, then the 25-fill estimate was an artifact of the
paper fill engine and every cost-sensitivity conclusion drawn from it needs withdrawing.

**Decisive statistic (pre-committed)**: count of correct per-book predictions out of 7 at the 12m
date, plus the two execution predictions scored independently. Verdict rule:
- 7 of 7 books correct → the fitted-benchmark reading is supported and the memo stands;
- 5 or 6 correct → partially supported, no claim about individual books;
- 4 or fewer → the reading is not predictive and the memo is downgraded to a description of one
  holdout year, not a finding about these strategies.
No book is scored as "correct" on the basis of a t-statistic between 2.0 and 2.4, which is the
alpha-forward experiment's own undecided band.

**Failure / kill condition** (pre-committed; includes the stop-iterating rule):
One evaluation at each pre-existing review date. The benchmark menu
(`SPY, QQQ, IWM, TLT, GLD, DBC`) is frozen by this document and may not be re-cut, re-weighted or
extended after seeing forward data. No re-running with a different cost figure once the fill
sample grows: a revised cost estimate is new evidence for a NEW pre-registration, not a re-score
of this one. If the prediction fails, the failure goes in FAILURES.md and the memo carries a
correction header. Nothing here licenses stopping, starting or resizing a book under any outcome;
that remains a Stage-4 decision for Kristen on separate evidence.

**Trial-ledger row**: TRIAL_LEDGER.md — Robustness experiments table, added in the same commit.

**Derived from prior holdout results?** YES, and doubly so. The predictions come from a
re-reading of the already-spent holdout, and the books being predicted were themselves selected by
that holdout. This document has no power to establish alpha and is not evidence for any strategy.
It can only do one thing: expose the memo's reading to being wrong.

**Result** (filled after the run, never edited above this line): PENDING, forward sample opened
2026-07-15, first review 2027-01-14.
