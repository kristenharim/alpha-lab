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
  point-in-time earnings/surprise collector (EXP-IC-EARNINGS-FWD). Loaded, exit 0.

## Active books (7) — started 2026-07-10, equal capital = equity/7 (~$14.4k)

| book | tier | frozen at | naive bench | kill rule |
|---|---|---|---|---|
| vol_managed_qqq | core | ff71245 | QQQ buy-hold | 12m review; demote if 12m net < naive − 5pp |
| vol_core_svxy | core | ff71245 | QQQ buy-hold | same |
| trend_vol_qqq | core (tail-hedge role) | 354bf47 | QQQ buy-hold | same, judged on drawdown vs naive too |
| defensive_ensemble | capital preserver | 354bf47 | 60/40 SPY/BIL | 12m review; kill if maxDD worse than 60/40 AND net below it |
| dual_momentum_gold | watch | 354bf47 | SPY buy-hold | flat after 2 consecutive quarters NAV < exposure-matched SPY |
| dual_momentum_gem | watch (control for gold) | ff71245 | SPY buy-hold | same |
| momentum_concentrated | watch | ff71245 | SPY buy-hold | same |

Also logged nightly per book: exposure-matched SPY nav, gross, targets; account row `_account`
carries the aggregate submission + h26-filtered fills.

## Review schedule (no edits to frozen books outside these gates)

- **+20 trading days (~2026-08-07): operational review only** — orders executed, positions
  correct, no silent flattening, slippage sane, benchmarks reconcile. No alpha judgments.
- **+3 months: early mechanism review** (exposure behavior, gold-vs-GEM divergence,
  sophistication vs naive controls).
- **+6 months: provisional review** (reality agreement, costs, watch-tier continuation).
- **+12 months: first promotion/demotion/redesign decisions.**

## Change log

- 2026-07-10: initial go-live (4 books) → +2 watch-tier (Kristen) → +GEM (Kristen) →
  sibling-session pause/resume with Kristen's "keep, resume" → statarb flattened, snapshot
  root cause fixed, 7-book restage. This manifest created; supersedes all prior notes.
- 2026-07-10 (Director, later): reconcile step wired into the nightly job; earnings
  collector enabled (both pre-registered experiments EXP-OPS-REALITY / EXP-IC-EARNINGS-FWD;
  read-only vs the books). research/independent_alpha/CANONICAL_STATE.md marked superseded
  for deployment state. Ledger writes made idempotent per book+date.
