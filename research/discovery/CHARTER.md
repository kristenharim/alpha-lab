# Additional Discovery Program — sandbox charter

*Stood up 2026-07-10. A sandboxed research feeder, separate from the frozen 7-book paper
portfolio and the Core Evidence Program. Full governing charter: the Director brief (chat).
This file is the on-disk operating record.*

## Mission
Discover whether Alpha Lab can find **one genuinely independent economic return source** —
distinct information, distinct mechanism, positive residual return after controlling for the
existing portfolio — that is NOT another expression of the US-equity / QQQ / trend / vol-scaling
/ leverage / momentum complex. The ideal output is **one replicated research object**, not
another strategy that makes 20% by owning QQQ.

## Hard boundaries (may / may-not)
**May:** generate hypotheses, collect new data, build measurement experiments, run frozen
historical tests, create shadow-paper candidates, propose research objects.
**May NOT** (control plane owned by the Deployment Coordinator — DEPLOYMENT_MANIFEST.md § Governance):
alter the 7-book manifest, change allocations, touch schedulers, edit frozen live specs, add an
8th funded book, reinterpret watch-tier as validated, bypass the Failure DB / Red Team, or
promote anything to deployment. Any discovery exits only through Research Director → Red Team →
Stage-4 approval.

## Discovery funnel (a candidate advances stage by stage)
0 Hypothesis (mechanism only) · 1 Measurement (does the phenomenon exist? IC/decay/stability or
TS residual relationship) · 2 Independent replication (era / dataset / market / prospective) ·
3 Portfolio construction (naive vs sophisticated) · 4 **Residual independence** (the
[orthogonality_benchmark.py](orthogonality_benchmark.py) gate — not U.S. beta with new timing) ·
5 Stress & Red Team · 6 Shadow paper (separate ledger, no funded allocation) · 7 Main-program review.

## Verdict vocabulary (every completed experiment ends on one)
`REJECTED` · `MECHANISM UNSUPPORTED` · `MEASUREMENT SUPPORTED` · `REPLICATION REQUIRED` ·
`PORTFOLIO CANDIDATE` · `SHADOW-PAPER CANDIDATE` · `NOT INDEPENDENT` · `BLOCKED BY DATA` ·
`BLOCKED BY EXECUTION`.

## What is genuinely new (else it's rejected by default)
New **information** (earnings/revisions/short-interest/options/term-structure/carry/macro/flows),
NOT a new transform of close/volume/vol/MA. Plus a **distinct mechanism** (who makes it, who pays,
why it persists, what arbitrages it away) and **residual independence** vs SPY/QQQ/trend/vol/the
7 books/sectors. Reject-by-default list: another MA length, another momentum horizon, another
residual-momentum transform, another low-vol ranking, another dual-momentum menu asset, another
VIX-panic or levered-QQQ wrapper, indiscriminate ETF replication, HFT without an execution model,
auto-generation without mechanism review, parameter search, retrospective regime selection,
short-history live adaptation.

## Backlog reuse (do not regenerate)
Hypotheses already generated, deduped, and ranked live in
[../independent_alpha/HYPOTHESIS_QUEUE.md](../independent_alpha/HYPOTHESIS_QUEUE.md) +
[EXPERIMENT_QUEUE.md](../independent_alpha/EXPERIMENT_QUEUE.md); dead ends in
[../hunt2026/FAILURES.md](../hunt2026/FAILURES.md). The Discovery lanes 1-6 map onto the existing
lanes A-F — this program **extends** that backlog, it does not re-run hypothesis generation.
See [INITIAL_PROGRAM_DEDUP.md](INITIAL_PROGRAM_DEDUP.md) for the Experiment 1-5 reconciliation.
