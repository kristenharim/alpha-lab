# Cutover plan — isolate `momentum_concentrated` into its own Alpaca paper account

**Date drafted:** 2026-07-15 · **Type:** execution-accounting change only (NOT a new alpha experiment;
does not touch the frozen forward alpha-isolation test) · **Status:** plan → implement → review → dry-run.

## Why

All seven hunt2026 books are virtual; the live runner sums them into ONE account-level target and
submits once (`hunt_paper_run.py::live_run`, tag `h26`). Single-stock fills for `momentum_concentrated`
are netted into the ETF aggregate and are **not broker-attributable**. It is the one book where broker
marks matter (single-name fills/slippage, survivorship, delistings booking 0 in the virtual ledger).
Isolating it gives an exact, broker-marked reality series for that book. The other six trade liquid
ETFs where combined execution costs nothing.

## Current architecture

- `live_run()` sizes `notional = equity / len(BOOKS)` (= equity/7), builds each book's dollar targets,
  **aggregates all 7 into `agg`**, `broker.submit_targets(agg, tag="h26")` to the shared paper account
  (`ALPACA_API_KEY_ID/SECRET`). One `_account` ledger row records the aggregate + real fills.
- `hunt_paper_reconcile.py` reconciles that one shared account; per-book drag is **pro-rated** by each
  book's share of the aggregate target (BANDS `book_drag_bps_month = 30`).

## Target architecture

- **Shared account (unchanged creds):** the six ETF books only —
  `vol_managed_qqq, vol_core_svxy, trend_vol_qqq, dual_momentum_gem, dual_momentum_gold,
  defensive_ensemble`. Aggregated and submitted with tag `h26`, exactly as today.
- **Dedicated account (`ALPACA_MC_API_KEY_ID/SECRET`):** `momentum_concentrated` only. Submitted with
  tag `h26mc`. It is the sole book in that account, so fills/positions/marks attribute to it exactly.
- Book strategy rule, weights, leverage, universe, rebalance timing, cost model, and the factor-adjusted
  forward-alpha benchmark are **unchanged**.

## Allocation / capital-sizing logic (the "mirror" rule)

`notional_per_book = shared_account_equity / 7` — computed once from the shared account, **identical to
today's formula**. The six ETF books use it (submitted to the shared account, which therefore holds ~1/7
as idle cash — nothing about the ETF books' dollar sizing changes). `momentum_concentrated` uses the
**same** `notional`, submitted to the dedicated account. Rationale: this reproduces MC's exact current
1/7 dollar share at cutover and keeps it a constant 1/7 of the canonical capital base — matching how the
virtual ledger already sizes it, so broker-vs-model tracking is apples-to-apples. The dedicated account's
own equity is a **buying-power constraint only** (fail closed if it can't support `notional × gross`),
not the sizing driver. Divisor stays **7**, never 6 — dividing by 6 would silently lever the ETF books.

## Cutover timing

- Cutover = the first `--live` nightly run after (a) `.env` has `ALPACA_MC_*`, (b) reviewers pass, and
  (c) one offline dry-run is inspected. Target: next weekday evening after review, ~2026-07-16 20:30 local
  (the nightly job window; must run after 16:00 ET). Exact timestamp stamped into this memo at cutover.
- Before the first dedicated-account submit, any pre-existing MC positions in the SHARED account are
  flattened by the normal reconcile/flatten path (MC leaving the shared target set makes its old shares
  "foreign" → flattened), so MC is not double-held across accounts.

## What stays continuous vs what begins at cutover

- **Continuous (never rewritten):** every per-book model ledger incl. `momentum_concentrated.jsonl`; the
  frozen factor-adjusted forward-alpha ledger (`ledgers/hunt2026/alpha_forward/`). These are model-marked
  and independent of execution venue — the cutover does not touch them.
- **Begins at cutover (new series):** `momentum_concentrated`'s **broker-marked execution-reality**
  series — the `_account_mc` ledger rows and the dedicated MC reconciliation. No pre-cutover broker
  attribution is claimed or backfilled; MC broker evidence starts the day the dedicated account goes live.
- The shared `_account` row and shared reconcile continue, now covering six books instead of seven.

## Safety checks (all fail closed, live path only)

1. `ALPACA_MC_*` missing → abort live (no partial submission).
2. Shared and MC key-ids identical → abort (prevents both routing to the same account).
3. MC endpoint not paper → abort (broker factory already asserts paper).
4. Any symbol present in BOTH the shared aggregate and the MC target set → abort (no symbol double-routed).
5. MC account buying power < MC gross notional → abort.
6. Dry-run produces BOTH account target sets and submits nothing.

## Rollback

Revert the `hunt_paper_run.py` / `hunt_paper_reconcile.py` / `core/broker/alpaca.py` changes (single
commit, tagged), and the next nightly run reverts to the seven-book single-account aggregate. Flatten the
dedicated MC account manually from the Alpaca paper UI. Model ledgers and the forward-alpha ledger are
untouched by rollback (they were never modified). No historical data is lost.

## Known limitations

- Mirror sizing couples MC's notional to the shared account's equity by design; if capital is later
  re-based, both accounts re-derive from the shared equity.
- The dedicated MC account may hold idle cash (its equity > MC notional); reconcile compares at the
  **position/sleeve** level (marked value of MC positions vs model), not account-NAV growth, so idle
  cash does not distort the tracking-drag signal.
- Broker-marked MC evidence has no history until cutover; the 30 bps/month tripwire needs a few weeks to
  be meaningful.
