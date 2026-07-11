# DEPLOYMENT MANIFEST — the single authoritative record of what is live

Rule: this file is the ONLY authority on deployment state. No research agent may enable,
disable, resize, or modify a deployment; any Stage-4 transition requires an explicit edit
here plus Kristen's approval recorded in the change note. Conflicting chat summaries,
memos, or session notes are superseded by this file. Update the reconciliation stamp on
every verified sweep of {registry, scheduler, broker account, ledgers}.

**Last reconciliation: 2026-07-10 ~22:45 PT** (registry + launchd + Alpaca positions/orders
+ ledgers all verified from disk/broker; conflicting 6-vs-7-book session notes resolved:
GEM was added at Kristen's explicit request after the 6-book gate — 7 books is authoritative.)

## Account

- Alpaca PAPER only (paper URL asserted at runtime; no real-money code path exists).
- Equity at reconcile: $100,794. Books are virtual: ONE aggregate account-level target is
  submitted nightly (orders tagged `h26-*`); per-book P&L is model NAV in the ledgers.
- Dead statarb book: **flattened 2026-07-10** (closes submitted; fill Monday open). The
  reconciler now prices ALL held names (targets ∪ positions), so foreign/stale positions
  can no longer silently persist.
- Known transient: 1 AMAT share held-for-orders rejects the book's AMAT order until the
  flatten fill settles; self-heals at the next nightly reconcile. Watch in nightly.log.

## Scheduler

- `com.rimrim.hunt2026-paper` — ~/Library/LaunchAgents, weekdays 20:30 local:
  `hunt_paper_run.py --live` then `hunt_paper_reconcile.py` (read-only reality-agreement
  measurement, EXP-OPS-REALITY), logs to artifacts/hunt2026/paper/nightly.log. Loaded, exit 0.
- `com.rimrim.earnings-collect` — weekdays 21:15, `scripts/earnings_collect.py` forward
  point-in-time earnings/surprise collector (EXP-IC-EARNINGS-FWD).
  **ENABLED and READ-ONLY** (resolved 2026-07-10, Kristen; loaded in launchctl,
  `- 0 com.rimrim.earnings-collect`):
  1. **Enabled** — the plist stays loaded and in place (do NOT unload or rename).
  2. **No trading or capital path** — it only writes PIT earnings/surprise data; it cannot
     submit an order, size a position, or alter any book.
  3. **Purpose: point-in-time data accumulation only** — grow the sample toward the
     registered target (n ≥ 300).
  4. **Deployment gate is separate from data collection.** Any earnings-based research object
     (signal, shadow sleeve, allocation change, or paper book) must still pass IC,
     residual-independence, replication, and incremental-value evidence AND a separate
     Stage-4 deployment approval before ANY paper trading. Data may grow now; nothing
     earnings-based deploys until gated.
  5. **Health review each run** — log and review collector health: event count, timestamp
     integrity, duplicate handling, and missing-data rate (nightly.log / the EXP-IC-EARNINGS-FWD
     report).

  *Supersedes the earlier "left DISABLED" note (commit `c501546`): the manifest and the actual
  launchd state now agree — enabled, read-only. Collection ≠ deployment.*

## Active books (7) — started 2026-07-10, equal capital = equity/7 (~$14.4k)

| book | tier | frozen at | naive bench | kill rule |
|---|---|---|---|---|
| vol_managed_qqq | core | c9e22c8 | QQQ buy-hold | 12m review; demote if 12m net < naive − 5pp |
| vol_core_svxy | core | c9e22c8 | QQQ buy-hold | same |
| trend_vol_qqq | core (tail-hedge role) | 833000d | QQQ buy-hold | same, judged on drawdown vs naive too |
| defensive_ensemble | capital preserver | 833000d | 60/40 SPY/BIL | 12m review; kill if maxDD worse than 60/40 AND net below it |
| dual_momentum_gold | watch | 833000d | SPY buy-hold | flat after 2 consecutive quarters NAV < exposure-matched SPY |
| dual_momentum_gem | watch (control for gold) | c9e22c8 | SPY buy-hold | same |
| momentum_concentrated | watch | c9e22c8 | SPY buy-hold | same |

Also logged nightly per book: exposure-matched SPY nav, gross, targets; account row `_account`
carries the aggregate submission + h26-filtered fills.

### Classification (reporting/interpretation only — NO allocation, logic, or frozen-spec change)

**The seven books are NOT seven independent alphas.** Forecast-independence computation
([research/independent_alpha/INDEPENDENCE_MATRIX.md](research/independent_alpha/INDEPENDENCE_MATRIX.md))
puts n_eff ≈ 2.8 across the seven; the promoted set is one market cluster + one portfolio wrap.
Report in three groups, never as seven equal candidates:

- **Core evidence — one market cluster (AS-01):** `vol_managed_qqq`, `vol_core_svxy`,
  `trend_vol_qqq`. Three implementations of the U.S. large-cap **volatility/trend
  risk-management** source (residual pairwise corr 0.79, crisis corr 0.77). Status:
  **one provisionally supported, era-replicated cluster (Level 3)** — **no Level-4
  (incremental/cross-market) or Level-5 (forward-validated) market source exists yet.**
- **Capital-preservation sleeve — Portfolio alpha:** `defensive_ensemble`. Diversification /
  drawdown control, not an independent market forecast.
- **Shadow research controls — held for forward falsification only:** `dual_momentum_gold`,
  `dual_momentum_gem`, `momentum_concentrated`. 0/3 add incremental value at equal risk
  (momentum_concentrated is value-destructive, P(ΔSharpe>0)=0.07). Their paper capital is
  **experimental allocation, not confidence-weighted deployment.**

## Roster freeze

**The 7-book roster is FROZEN as of 2026-07-10.** No additions before the +3-month gate:
more books now dilutes paper capital, muddies attribution, and adds correlated variation,
not information. Exception requires a manifest change + Kristen's approval.

## Review schedule (no edits to frozen books outside these gates)

- **+20 trading days (~2026-08-07): operational review only** — orders executed, positions
  correct, no silent flattening, slippage sane, benchmarks reconcile. No alpha judgments.
- **+3 months: early mechanism review** (exposure behavior, gold-vs-GEM divergence,
  sophistication vs naive controls).
- **+6 months: provisional review** (reality agreement, costs, watch-tier continuation).
- **+12 months: first promotion/demotion/redesign decisions.**

## Governance — single-writer control plane (established 2026-07-10)

Concurrent sessions produced duplicate fixes and overlapping commits (two independent copies
of the held-position reconcile fix; drifting 6-vs-7 book notes; the earnings-collect
enable/disable flip above). To stop this drift, the deployment-critical control plane has
**exactly one writer — the Deployment Coordinator.** Coordinator-only files:

- `scripts/hunt_paper_run.py`
- `DEPLOYMENT_MANIFEST.md`
- `research/hunt2026/STATUS.md`
- `ledgers/hunt2026/*.jsonl`
- scheduler config: `~/Library/LaunchAgents/com.rimrim.hunt2026-paper.plist`,
  `~/Library/LaunchAgents/com.rimrim.earnings-collect.plist`

Only the Coordinator may create, edit, resize, enable, disable, or reconcile these. Every
control-plane change lands as a single manifest edit + a change-log line here — no direct
sibling-session commits to these paths. Other agents/sessions may write **isolated research
artifacts only** (`research/**`, `memos/**`, `notebooks/**`, `reports/**`) and must **not**
modify the live-paper control plane — propose changes to the Coordinator instead. No research
subagent may enable live-paper submission (charter rule 20).

## Change log

- 2026-07-11 (review pointer, documentation-only, at Kristen's request): canonical project-level
  synthesis + independent review saved at `memos/2026-07-11-canonical-review.md`, committed `d5d15f8`.
  It is the authoritative project-level synthesis (reconciles the stock-universe counts 1,202/820/382/777/168,
  the 271 foreign-position decomposition, the 68-order split = 68 canceled/0 rejected, and the CAPM-vs-
  exposure-matched alpha models). Read-only: **no deployment, allocation, spec, scheduler, or frozen-experiment
  state changed**; this line is a pointer only. Where the review and this manifest disagree on deployment
  state, the manifest still wins.
- 2026-07-10: initial go-live (4 books) → +2 watch-tier (Kristen) → +GEM (Kristen) →
  sibling-session pause/resume with Kristen's "keep, resume" → statarb flattened, snapshot
  root cause fixed, 7-book restage. This manifest created; supersedes all prior notes.
- 2026-07-11 (Coordinator): docs-only fix of defensive_ensemble/MECHANISM.md to match
  frozen code (F-RT-07; spec.py byte-unchanged); reconcile harness gained a read-only
  foreign-position tracker (direct stat-arb-flatten/AMAT status) + partial/replacement
  classification (154 tests green). Red-team Audits A/B/C/D completed (all SURVIVE; one docs
  gap fixed; only stock-universe repair + real fills remain). Started research/stock_universe_repair/
  (versioned; 168/777 zero-coverage survivorship gap) and research/macro_data_layer/
  (audit-first: FRED blocked-on-key, VIX3M research-PASS/live-BLOCK). Roster FROZEN, no
  deployment/allocation change. First fills + stat-arb flatten pending Monday's open.
- 2026-07-10 (Director, later): reconcile step wired into the nightly job; earnings
  collector enabled (both pre-registered experiments EXP-OPS-REALITY / EXP-IC-EARNINGS-FWD;
  read-only vs the books). research/independent_alpha/CANONICAL_STATE.md marked superseded
  for deployment state. Ledger writes made idempotent per book+date.
- 2026-07-10 (Coordinator): book **classification** added (core-evidence / capital-preservation
  sleeve / shadow-research controls) with the "not seven independent alphas" note — reporting
  only, no allocation/logic/frozen-spec change. **Single-writer governance** established for the
  control plane (§ Governance). Flagged the earnings-collect enabled-vs-"left DISABLED"
  contradiction for Kristen (#4 vs #5); left as-found pending her call. Roster stays frozen
  through the +3-month gate — no new books, no retune, no new price/volume hunt.
- 2026-07-10 (Coordinator, resolution): Kristen resolved the earnings-collect tension —
  collector stays **ENABLED and READ-ONLY** for PIT data accumulation; the deployment gate
  applies to earnings-based *research objects*, not to *data collection*. Scheduler entry
  rewritten to state this unambiguously (5 points), plist left in place, manifest now agrees
  with actual launchd state. Documentation-only; no logic, spec, allocation, or scheduler change.
