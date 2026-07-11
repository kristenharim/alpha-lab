# Alpha Lab — Independent Red-Team Audit Charter (Kristen, 2026-07-10, verbatim)

Governing principle: **a great result remains a suspected bug until independent evidence
rules out the material failure modes.** The Red Team does not ask "how can this make more
money?" It asks "what evidence would make us stop believing this result?"

## 1. Scope and Safety
Audit authoritative state from repo + broker records, not chat summaries. Scope freeze in
SCOPE.md (commit ffb5778, checksums, roster, suite state). Work read-only: do NOT modify
frozen specs, production data, the deployment manifest, paper allocations, broker orders,
or schedulers; commit nothing to production paths. All outputs and proposed fixes go ONLY
to redteam/2026-07-10/agent<N>/ as reports + isolated patch files. The 7-book roster stays
frozen; paper trading continues; a CRITICAL finding may RECOMMEND pausing evidence
collection but may not perform it.

## 2. Audit priority
Tier 1 shared infrastructure (PIT dataset/universe; shared engine; accounting/benchmarks;
broker reconciliation; corporate actions/missing data) — a shared defect has highest
severity. Tier 2 core books (vol_managed_qqq, vol_core_svxy, trend_vol_qqq,
defensive_ensemble). Tier 3 watch books (dual_momentum_gold, dual_momentum_gem,
momentum_concentrated). Tier 4 archived/failed strategies — only enough to check the
failure records remain valid.

## 3. Independence
Same frozen commit + data checksums for all agents; isolated output directories; no
reading other agents' findings before submitting; distinguish observed evidence from
inference; reproducible commands, file paths, line numbers, output hashes; attempt to
FALSIFY existing claims; never tune or optimize. Agent agreement is corroboration of an
audit finding, not independent market evidence.

## 4. Finding classification
Every finding: ID; component; category; severity (CRITICAL / HIGH / MEDIUM / LOW); status
(CONFIRMED BUG / CONFIRMED METHODOLOGICAL WEAKNESS / PLAUSIBLE CONCERN / RULED OUT / NOT
TESTABLE WITH CURRENT DATA); evidence; reproducible procedure; consequence; affected
historical results; affected live-paper evidence; proposed remediation; whether
remediation requires rerunning trials; whether it changes any current belief. Do not call
a hypothetical possibility a bug.

## 5. Agent assignments (each agent reads its own section only)

**Agent 1 — Code & Leakage Auditor.** Read every active strategy implementation + shared
helpers. Hunt: negative shifts; indexing/off-by-one; future prices or membership; improper
warmups; rolling endpoint mistakes; forward-filled information; mutable hidden state;
stale caches; NaN propagation; silent zero-weight; timezone errors; accidental reuse of
holdout-derived files. Per suspected defect: minimal repro; earliest wrong timestamp;
file:line; quantified effect on weights/returns. Also test code vs written MECHANISM/spec.

**Agent 2 — Independent Engine Auditor.** Ignore strategy conclusions. Audit harness +
paper accounting: signal/weight/trade timestamps; return interval; open-vs-close; leverage
enforcement; cash returns; costs; turnover definition; drift between rebalances;
dividends; splits; delistings; missing data; benchmark construction; exposure matching;
compounding; virtual-book aggregation; broker reconciliation. WRITE A MINIMAL INDEPENDENT
ENGINE (no imports of alpha-lab return/accounting code) and test deterministic cases:
cash-only; one asset fixed weight; one rebalance; alternating long/cash; levered asset;
split; dividend; missing day; delisting; multiple virtual books on one account. Any
unexplained daily return difference > 1bp = failed comparison; smaller systematic
differences must still be explained. Do not assume the repo engine is correct.

**Agent 3 — Data & Universe Auditor.** Try to prove the panel contains future or
incomplete information: historical membership; current-member contamination; survivorship;
delisted names; failed downloads; stale prices; zero-volume; corporate actions;
adjusted-vs-unadjusted; dividends; splits; ETF inceptions; duplicate dates; phantom
holidays; timezone/calendar alignment; member-mask timing; price availability before
entry; symbol changes/mergers. Where full correction is impossible, produce contamination
BOUNDS. For survivorship report separately: confirmed current-member leakage; missing dead
names; likely bias direction; maximum credible impact; data needed for a conclusive audit.
Do not claim survivorship ruled out merely because PIT masks exist.

**Agent 4 — Statistical & Selection Auditor.** Treat the whole research history as ONE
adaptive multiple-testing process. Build the complete trial family (frozen specs, adaptive
reruns, parameter explorations, walk-forward variants, defensive-menu tests, estimator
experiments, recoverable undocumented attempts — TRIAL_LEDGER.md, FAILURES.md, git log,
preregistrations/). Evaluate where assumptions hold: Deflated Sharpe; block-bootstrap CIs;
rolling Sharpe stability; prediction intervals; parameter-surface stability; White's
Reality Check / Hansen SPA; PBO; FDR; random-strategy and random-universe controls. For
every statistic: null; trial family; dependence assumptions; block length; overlap
treatment; applicability limits. Do NOT report a statistic whose assumptions are
materially violated — say so instead. Separate observed return / beta-adjusted /
benchmark-relative alpha / uncertainty / multiplicity adjustment / economic materiality.

**Agent 5 — Market & Execution Realism Auditor.** Paper fills where available (there may
be none yet — say so; do not treat paper fills as live-market equivalent). Audit: spreads;
auction assumptions; fill timing; partials; missed fills; cancels; overnight gaps; impact;
volume participation; stock-vs-ETF liquidity; borrow/short constraints; halts; rounding;
fractional shares; broker data limits; stale quotes; order queueing across non-market
hours. Produce realistic COST BANDS not one number; stress each active book under base /
doubled spreads / stressed vol / one-bar delay / one-day delay / partial fills / missed
trades. State which assumptions are observation-backed vs hypothetical.

**Agent 6 — Robustness & Perturbation Auditor.** Try to break each active book WITHOUT
optimizing: symmetric predeclared perturbations — costs; params ±20%; rebalance date;
execution timestamp; signal delay; random missed trades; random one-bar lags; missing
observations; spread widening; alternate valid start dates; alternate universe defs;
leverage reduction. Report per book: median degradation; worst credible degradation;
fraction of perturbations retaining positive benchmark-relative value; gradual vs
cliff-like failure; plateau vs isolated peak.

**Agent 7 — Regime & Concentration Auditor.** Predeclared, time-observable regime
definitions only (declare them BEFORE computing results). Evaluate bull/bear; high/low
vol; inflation/disinflation; rate direction; liquidity; trend persistence; crisis
cascades; major stress events. Report: return contribution by regime; time in regime;
benchmark-relative contribution; drawdown contribution; whether a small subset of periods
explains most performance; whether the mechanism is economically defensible in its winning
regimes. No post-hoc regime definitions; no calendar-category causality without mechanism.

**Agent 8 — Clean-Room Replication Auditor.** IGNORE all strategy source code. Inputs:
the written frozen specs (params.json + MECHANISM.md + SPEC_CONVENTIONS.md ONLY — do not
open spec.py), permitted data fields, cost assumptions, rebalance convention.
Reimplement each of the 7 active books independently (no imports from alpha-lab strategy/
accounting code). Compare: target weights; trades; turnover; costs; daily returns; final
NAV; benchmarks. Per discrepancy: first differing date; classify as spec ambiguity /
original-code defect / replica defect / data mismatch — do not assume the replica is
right. Output a daily-difference file per book into your directory.

**Agent 9 — Risk & Return-Source Auditor.** What actually generates the returns: market
beta (static + dynamic); gross/net exposure; leverage; sector concentration; duration/rate
exposure; vol exposure; trend exposure; tail dependence; crash sensitivity; correlation
clustering; hidden overlap among books; contribution decomposition (timing, leverage,
selection, carry, vol scaling). Compare each sophisticated book to its naive control.
Answer: is it primarily beta? did sophistication add return, cut risk, or just retime? are
the 7 books fewer independent sleeves than names imply?

**Agent 10 — Adversarial Implementation Auditor.** Pre-register a SMALL set of plausible
unfavorable implementation variants (previous close; next open; one-day signal delay;
realistic opening gap; randomized execution order; reduced liquidity; missed rebalance;
doubled costs; whole shares only; conservative fills) — then report ALL of them, no
cherry-picking worst-of-hundreds. Confidence falls when small plausible changes cause
disproportionate collapse.

## 6-8. Adjudication, verdicts, scoring
A separate Adjudicator reproduces every CRITICAL/HIGH finding, resolves conflicts
(code vs data vs method vs prose), dedupes, separates strategy-specific from shared-platform
defects, lists reports to withdraw/amend/rerun, and rules whether current paper
observations remain usable. Verdicts per strategy: INVALIDATED / BLOCKED / PROVISIONAL /
SURVIVES RED-TEAM AUDIT / NOT TESTABLE. Confidence scores 0-100 on eight axes (code,
engine, data, statistics, mechanism, implementation realism, robustness, forward evidence
— forward evidence capped at 60 until sufficient observations) + one overall band. Prose
must QUOTE tables, not paraphrase.
