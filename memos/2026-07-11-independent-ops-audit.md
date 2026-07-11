# Independent Operations & Research-Validity Audit — Alpha Lab Paper-Trading Incubation

**Date:** 2026-07-11 · **Type:** read-only audit → docs-only governance artifact (adjudicated) ·
**Auditor scope:** systematic-trading operations + research validity.
**As-of:** 2026-07-11, weekend — market not open since the 2026-07-10 go-live (0 fills).
**Scope note:** No strategy logic, allocation, schedule, frozen specification, or broker state was modified in
producing this document. Where this audit and `DEPLOYMENT_MANIFEST.md` disagree on deployment state, the
manifest wins.

**Primary evidence:** `DEPLOYMENT_MANIFEST.md`, `scripts/hunt_paper_run.py`, `scripts/hunt_paper_reconcile.py`,
`core/broker/{alpaca,base}.py`, `research/hunt2026/harness.py`, `ledgers/hunt2026/*.jsonl`,
`memos/2026-07-11-canonical-review.md`, `redteam/2026-07-10/**`.

**Adjudications applied (2026-07-11, Kristen):** freeze preserved through the first post-open operational
transition; no alerting / dead-man / gross-limit / buying-power / emergency-stop code added before the existing
flatten + reconciliation cycle is observed; readiness split into four dimensions; four label reclassifications;
§7 thresholds retuned; §7 remains a proposal **for approval only after the clean-cycle report** — nothing in §7
is implemented.

---

## 0. One-line finding

An elite research and governance apparatus, with an unusually honest self-review, wrapping a **contaminated,
un-flattened broker account with zero fills and no automated live risk/alerting layer.** The research clock is
mature; the *forward* clock has not legitimately started. This is the expected, correct state for an incubation
on its first operational transition — the gaps below are pre-clean-start work items, not defects in the frozen
research.

---

## 1. Component checklist (labels adjudicated)

### Research integrity — strong

| Component | Status | Evidence |
|---|---|---|
| Frozen specifications | COMPLETE | books frozen at `c9e22c8` / `833000d`; roster FROZEN through +3-month gate |
| Versioned datasets | PARTIAL | `data/manifest.jsonl` lineage + frozen `panel_2005.parquet`; stock panel has a survivorship hole |
| Point-in-time inputs | PARTIAL | PIT membership enforced in code/rules; ETF books clean; stock-universe PIT incomplete |
| Survivorship controls | PARTIAL | 382/1,202 ever-members missing, 168 zero-coverage; bias **bounded** (momentum rankIC≈0), not eliminated |
| Leakage prevention | COMPLETE | pairs look-ahead caught (Sharpe 4.77→−0.06); future-poison red-team RULED OUT all 7 |
| Realistic costs | PARTIAL | 10bps stock / 2bps ETF + `MAX_GROSS=2` charged in backtest; **financing on leverage not yet modeled** (reclass. 4 + §7.10) |
| Walk-forward + holdout | COMPLETE | blind 1Y/5Y holdouts + walk-forward per book |
| Exposure-matched benchmarks | COMPLETE | logged nightly (`bench_spy_nav` = book gross × SPY); load-bearing correction, done right |
| Multiple-testing controls | COMPLETE | deflated Sharpe, honest effective n_trials ≈ 2.3 (repo DSR was conservative) |
| Documented kill criteria | PARTIAL | per-book demote/kill rules exist — human review-gate, not automated (correct for incubation) |

### Portfolio construction — observability strong, sizing naive by design

| Component | Status | Evidence |
|---|---|---|
| Expected-return estimates | **NOT APPLICABLE** (reclassified) | equal-capital risk-overlay books need no ER model. **Required for future alpha-based allocation** — mandatory the moment capital is sized by forecast rather than equal-weight |
| Covariance / risk estimates | PARTIAL | computed for independence (n_eff, residual/crisis corr); not used to size |
| Leverage limits | PARTIAL | `MAX_GROSS=2` in backtest harness only; no live gross guard (deferred per §7.3) |
| Gross / net exposure controls | PARTIAL | backtest caps gross; live submit path has none (deferred per §7.3) |
| Concentration limits | NOT APPLICABLE (deferred) | equal-weight books; hard limits deferred for paper research |
| Sector / factor exposure limits | **NOT APPLICABLE** (reclassified: deferred for paper research) | hard limits deferred; **exposure monitoring remains required** and is in place (correlation/crisis below) |
| Correlation / crisis-corr monitoring | COMPLETE | residual pairwise 0.79, crisis 0.765 measured — the required exposure monitoring |
| Risk contribution by book | COMPLETE | n_eff 2.80 raw / 4.12 residual; ~3 real clusters |
| Liquidity / capacity constraints | NOT APPLICABLE | ETF-dominant at ~$14k/book |
| Allocation across overlapping books | PARTIAL | execution netting correct; capital allocation naive equal-weight (acknowledged; frozen) |

### Execution — correct core, thin protections

| Component | Status | Evidence |
|---|---|---|
| Order-generation correctness | COMPLETE | `compute_book` offline-testable; target = last row of frozen weights |
| Target-vs-current netting | COMPLETE | books aggregated into ONE account target, diffed vs held qty (`alpaca.py:35-45`) |
| Order type / TIF | COMPLETE | market, `TimeInForce.DAY` |
| Market-open handling | COMPLETE | 20:30 DAY orders queue for next open (intended) |
| Partial fills | PARTIAL | reconcile classifies partials; submit rounds to whole shares; no partial re-try |
| Cancel / replace | PARTIAL | `cancel_all_orders` each run; replacements classified in reconcile |
| Rejected orders | COMPLETE | per-order `APIError` caught → `order_errors`; run survives |
| Spread / slippage measurement | COMPLETE (untested live) | reconcile measures side-adjusted bps vs ref close; 0 fills so far |
| Market-impact assumptions | NOT APPLICABLE | fixed-bps model fine at this scale |
| Borrow / short constraints | **NOT APPLICABLE** (reclassified) | none of the 7 frozen books produces a short target. **Applicable only to short-capable books** — required before any short-target book deploys (§7.11) |
| Financing costs | **NOT APPLICABLE to execution** (reclassified) | research-validity adjustment, not an order-path concern — see Research integrity + §7.10 |
| Stale / untradeable assets | COMPLETE | `asset_status` skips halted/delisted; `price_fn None`→skip |
| Duplicate-order prevention | PARTIAL | `cancel_all` + uuid `client_order_id` (coid is random, not an idempotency key); hardening per §7.5 |
| Idempotency | PARTIAL | ledger writes idempotent per book+date; order layer relies on cancel-then-resubmit |

### Broker & operations — paper safety excellent, ops resilience thin

| Component | Status | Evidence |
|---|---|---|
| Paper endpoint enforcement | COMPLETE | hardcoded `PAPER_URL` + runtime `assert "paper" in base` + non-paper override rejected |
| Account-state reconciliation | COMPLETE | nightly read-only `get_account` / `get_all_positions` / `get_orders` |
| Cash / buying-power checks | MISSING | equity read for sizing; no pre-trade BP gate (deferred per §7.6) |
| Position reconciliation | COMPLETE | `position_gap_frac`, foreign-position decomposition |
| Open-order reconciliation | COMPLETE | open+closed pull; per-symbol flatten-order tracking |
| Corporate actions | PARTIAL | yfinance adjusted closes absorb splits/divs; no explicit CA layer; panel/fresh seam "jogs a few bps" |
| Split / dividend handling | PARTIAL | via price adjustment only |
| Halted / delisted | COMPLETE | `asset_status` |
| Scheduler health | PARTIAL | launchd loaded, exit 0, nightly.log; no dead-man's switch (deferred per §7.2) |
| Retry behavior | MISSING | one shot/night; per-order try/except, no retry |
| Alerting | MISSING | alarms are strings in nightly.log; nothing pages a human (deferred per §7.1) |
| Failure recovery | PARTIAL | cancel-all + idempotent re-run; AMAT self-heal noted |
| Audit logs | COMPLETE | ledgers + `_reconcile.jsonl` + nightly.log + git commits |
| Credential security | COMPLETE | `.env` gitignored, keys from env |
| Single-writer guarantees | PARTIAL | Coordinator governance documented/social, not code-enforced |

### Forward evidence — framework strong, clock not started

| Component | Status | Evidence |
|---|---|---|
| Clean forward start date | PARTIAL | defined = post-flatten Monday 2026-07-13, gated on 4-part flatten check; not yet reached |
| Transition-period contamination | COMPLETE | performance suspended until 4 gates pass + holdings reconcile |
| Strategy- vs account-level attribution | PARTIAL | books are virtual (model NAV); one aggregate account trades → no real per-book fills; slippage pro-rated |
| Benchmark-relative returns | COMPLETE | exposure-matched + naive benches nightly |
| Realized costs / slippage | PARTIAL | reconcile ready; 0 fills to measure |
| Target tracking error | COMPLETE | `position_gap_frac` |
| Data-quality incidents | PARTIAL | manifest + coverage audits; no automated live data-quality gate (deferred per §7.7) |
| Silent-flat detection | COMPLETE | 2-consecutive-night alarm |
| Sample-size requirements | COMPLETE | 20d / 3mo / 6mo / 12mo gates; DSR with honest n |
| 20d / 3mo / 6mo / 12mo gates | COMPLETE | manifest review schedule |
| Rules preventing premature conclusions | COMPLETE | "20 days = operational only, no alpha judgments" |

### Risk controls — weakest domain; automated live safety layer deferred by adjudication

| Component | Status | Evidence |
|---|---|---|
| Per-position limits | MISSING | none in live submit (deferred per §7.4) |
| Per-book limits | PARTIAL | equal-capital notional cap only |
| Aggregate gross / net limits | MISSING | live path unguarded (deferred per §7.3) |
| Sector / factor limits | NOT APPLICABLE (deferred) | hard limits deferred; exposure monitoring in place |
| Drawdown alerts | MISSING | deferred per §7.8 |
| Volatility limits | NOT APPLICABLE | vol-targeting is inside the strategy, not a portfolio guard |
| Turnover limits | MISSING | deferred |
| Daily-loss alerts | MISSING | deferred per §7.8 |
| Broker-outage behavior | MISSING | no retry/failover (deferred per §7.2) |
| Stale-price behavior | PARTIAL | ffill heals holiday gaps; None→skip; no explicit staleness alarm (deferred per §7.7) |
| Runaway-order protection | MISSING | no cap on order size/count (deferred per §7.3–§7.5) |
| Emergency stop procedure | MISSING | no coded kill switch; human 12-month review gates only (deferred per §7.9) |

---

## 2. Critical gaps (ranked)

| # | Gap | Op risk | Research-validity risk | Capital risk (paper) | Urgency |
|---|---|---|---|---|---|
| 1 | Account not clean — 271 foreign stat-arb positions, $141.7k gross, −$30.8k net, 1,563 flatten shares unfilled | HIGH | HIGH | Med | Now / Monday |
| 2 | No alerting / dead-man's switch — failed job or fired alarm reaches no human | HIGH | Med | Med | After first cycle |
| 3 | No automated live risk guard (gross, per-position, runaway, buying-power, e-stop) | HIGH | Low | Med | After first cycle |
| 4 | 0 fills — execution model entirely unvalidated forward | Med | HIGH | Low | First open |
| 5 | Core "alpha" is un-financed leverage — vanishes exposure-matched; financing uncharged | Low | HIGH | Med | 3-mo review |
| 6 | Survivorship hole blocks `momentum_concentrated` | Low | HIGH (that book) | Low | Vendor-gated |
| 7 | No real per-book attribution — virtual books, one aggregate account | Med | Med | Low | Accept + document |
| 8 | Single-writer is social, not enforced | Med | Med | Low | Before scaling |

---

## 3. Recommended improvements (bucketed)

**Must fix before clean forward evidence:** complete + verify the flatten to all 4 gates; do not start the
forward clock until the seven-book holdings reconcile to the aggregate target. *(Already the Monday plan; this
audit ratifies it as blocking.)*

**Should fix during the first 20 trading days (proposal-only until approved — §7):** human-delivered alarms;
dead-man monitoring; live pre-trade gross + single-order + order-count guards; buying-power validation;
stale-price alarm; daily-loss controls; emergency stop.

**Can wait until the 3-month review:** financing/borrow accounting in forward P&L; risk-based (vs equal)
allocation once forward covariance is observed; automated kill-rule evaluation feeding (not replacing) human
sign-off.

**Unnecessary complexity (don't build):** market-impact/capacity models at this scale; per-book real
sub-accounts (virtual-book + aggregate-netting is correct — document the attribution limit); a factor-limit
optimizer (the concentration *is* the honest finding).

---

## 4. Readiness classification — four separate dimensions (adjudicated)

| Dimension | Classification | Rationale |
|---|---|---|
| 1. Research / backtest infrastructure | **READY** | frozen specs, leakage ruled out, blind holdout + walk-forward, deflated Sharpe with honest n, exposure-matched benchmarks, engine reproduction to 0.0000 bp, red-team survived |
| 2. Paper execution plumbing | **READY FOR OPERATIONAL TESTING** | netting, paper-endpoint enforcement, reject handling, read-only reconcile, silent-flat + foreign-position detection present + tested offline; unproven only because 0 fills exist yet |
| 3. Clean forward incubation | **BLOCKED** — pending the four-part flatten gate **and** seven-book reconciliation | account carries un-flattened stat-arb residue (271 positions, net −30% of equity); performance interpretation correctly suspended until gates pass + holdings reconcile |
| 4. Live-capital deployment | **NOT READY** | no forward evidence, core edge = leverage not alpha, no automated live risk/alerting layer, one BLOCKED book, un-flattened residue |

---

## 5. Evidence required to upgrade each dimension

**Dimension 3 → CLEAR (clean forward incubation):**
1. Flatten 4-gate PASS on an independent broker snapshot; new holdings reconcile to the aggregate target.
2. ≥1 clean nightly cycle with the 7 books' fills only, `position_gap_frac` in-band, no foreign positions.
3. A defined clean-start timestamp recorded in the manifest; all pre-clean fills excluded from attribution.

**Dimension 4 → toward LIMITED LIVE-CAPITAL PILOT:**
4. ≥3–6 months clean forward with trailing slippage inside the 10/2-bps pre-registered bands.
5. At least one book showing exposure-matched *forward* excess **net of financing/borrow** — the alpha question
   is currently unanswered forward.
6. The deferred safety layer (§7) implemented, approved, and demonstrated: human alarms firing, dead-man
   tripping, pre-trade guards fail-closing, buying-power gate, stale-price detection, daily-loss tiers,
   emergency stop.
7. Enforced single-writer (lock, not convention) once more than one operator touches the control plane.

Current honest state (concurs with the canonical review): excellent process, one credible portfolio object
(`defensive_ensemble`), no proven independent alpha, no forward evidence. Single most valuable next datum: the
first clean set of real fills with reconcile-measured slippage.

---

## 6. Freeze & sequencing (adjudicated)

- The current freeze is **preserved through the first post-open operational transition.**
- **No** alerting, dead-man, gross-limit, buying-power, or emergency-stop code is added before the existing
  flatten + reconciliation cycle is observed.
- §7 is a **proposal only** — build begins **only after the first clean operational cycle has completed** and is
  **explicitly approved after the clean-cycle report.** Nothing in §7 is implemented in this session.

---

## 7. Minimal implementation plan — PROPOSAL ONLY (retuned thresholds; not implemented)

**Design invariants.** All proposals are additive and observability-first. Trading-path guards **fail-closed**
(a blocked night is safe: books are frozen, one skipped rebalance is negligible). Emergency stop is **fail-safe**
(unreadable ⇒ halt). Reporting adjustments (financing, borrow) are additive columns that **never mutate a frozen
scorecard**. Items touching `submit_targets` / `hunt_paper_run.py` / plists / the manifest are **Coordinator-only**
and land as a single manifest edit + change-log line.

**Shared symbols** used below: `E` = account equity; `agg[s]` = signed aggregate target dollars per symbol
(sum across books); `G_exp = Σ|agg[s]|` = expected aggregate target gross; `price[s]` = snapshot price;
`held[s]` = current signed qty; `tradable(s)` = `asset_status(s)=="tradable"`;
`target_qty[s] = round(agg[s]/price[s])`; `proj_qty[s] = target_qty[s] if tradable(s) else held[s]`;
`delta_qty[s] = target_qty[s] − held[s]`; `order_notional[s] = |delta_qty[s]|·price[s]`;
`expected_delta[s] = |agg[s] − held[s]·price[s]|` (model-intended dollar move).

---

### 7.1 Human-delivered alarms
- **Exact calculation:** fire if a fresh `_reconcile.jsonl` row has non-empty `alarms[]`, OR `order_errors`
  non-empty, OR `reject_rate > 0.02`. Message key = `(date, alarm_text)`; suppress a key already sent.
- **Data dependencies:** `_reconcile.jsonl` (read-only), `order_errors` from the run; delivery channel (existing
  iMessage self-thread dispatcher, 🤖 prefix, or email).
- **Fail-open / fail-closed:** **fail-open** — a read-only consumer; delivery failure must not crash the run or
  gate trading. On delivery failure, drop a sentinel file for §7.2 to escalate.
- **Expected false positives:** a benign one-off reject on a thin name; the known AMAT held-for-orders transient
  during the flatten week (self-heals) — both real alarms, low severity, not errors.
- **Offline tests:** row with alarms → expected formatted message; injected/mock sender (no network); dedupe test;
  empty alarms → no send.
- **Paper-mode integration test:** after a real nightly reconcile, assert the alarm consumer reads the row and
  the mock sender receives exactly the row's alarms; assert zero sends on a clean row.
- **Rollback:** remove the post-reconcile call; pure add-on, no state.

### 7.2 Nightly dead-man monitoring
- **Exact calculation:** separate ~22:30 job on trading weekdays; alert if `_reconcile.jsonl` has no row whose
  `run_at` date == today, OR nightly.log last exit ≠ 0, OR the §7.1 delivery-failure sentinel exists.
- **Data dependencies:** `_reconcile.jsonl` mtime + last-row date; nightly.log exit line; exchange calendar (to
  know it's a trading day).
- **Fail-open / fail-closed:** **fail-open** for trading (never touches the broker); it only escalates. Kept
  deliberately minimal so it can't itself fail silently.
- **Expected false positives:** an early-close/half-day if the calendar lags; a legitimately delayed run still
  inside the cutoff window.
- **Offline tests:** stale vs fresh reconcile file → alert / no-alert; malformed file → alert; non-trading day →
  no alert.
- **Paper-mode integration test:** with the real ledger, run the monitor twice — once after a real reconcile
  (no alert), once with the clock advanced past cutoff and no new row (alert to mock channel).
- **Rollback:** unload the extra plist; no data change.

### 7.3 Pre-trade aggregate projected-gross ceiling
- **Exact calculation:** `PG = Σ_s |proj_qty[s]|·price[s]`. **Block the run** if `PG > 2.25·E` **OR**
  `PG > 1.15·G_exp`.
- **Data dependencies:** `get_account().equity`, snapshot prices, `get_all_positions` (held), `asset_status`
  per symbol, computed `agg`.
- **Fail-open / fail-closed:** **fail-closed** — any breach ⇒ submit nothing, leave prior positions, alarm.
- **Expected false positives:** untradable foreign residue inflating `PG` above `1.15·G_exp` (expected zero
  post-clean-cycle, which is exactly why this guard only arms after it); a snapshot price spike; a legitimate
  vol book stepping 0→2× (bounded by the spec's `MAX_GROSS=2`, so `PG/E` should sit ≤ ~2.0 — 2.25 gives headroom).
- **Offline tests (FakeBroker):** normal `agg` passes; `agg` scaled to 2.3·E blocks (ceiling); foreign residue
  pushing `PG > 1.15·G_exp` blocks (drift); an untradable name is carried at `held` in `proj_qty`.
- **Paper-mode integration test:** after the clean cycle, dry-run against the paper account; assert computed `PG`
  is within tolerance of realized post-trade gross; via a test-only oversized target (no real submit) confirm the
  block path fires + alarm + zero orders.
- **Rollback:** set ceilings to ∞ or remove the wrapper; frozen specs byte-unchanged.

### 7.4 Single-order sanity limit
- **Exact calculation:** for each `s` with `delta_qty[s] ≠ 0`, **block the run** if
  `order_notional[s] > 0.30·E` **OR** (`expected_delta[s] ≥ floor` **AND**
  `order_notional[s] > 1.50·expected_delta[s]`). Floor = `max($200, 0.001·E)` to exempt rounding-dominated tiny
  deltas.
- **Data dependencies:** prices, held, `agg`, `E`.
- **Fail-open / fail-closed:** **fail-closed**, all-or-nothing (one bad symbol halts the night, to keep
  attribution clean).
- **Expected false positives:** a high-priced, low-target name where one whole share dwarfs a tiny intended delta
  (mitigated by the floor); a large legitimate first-day establishment order vs a near-zero prior held.
- **Offline tests:** normal passes; one symbol at `0.31·E` blocks (equity cap); a `1.6·expected_delta` glitch
  above floor blocks; a rounding-only tiny-delta name below floor does **not** trip.
- **Paper-mode integration test:** replay a week of real targets against paper in dry-run; assert no legitimate
  nightly rebalance trips the guard; inject one synthetic glitch delta and confirm block.
- **Rollback:** remove the gate; no state.

### 7.5 Order-count + duplicate-chain guard
- **Exact calculation:** `changed = {s : delta_qty[s] ≠ 0}`; **block** if `|changed| > |changed_expected| + 5`
  (where `changed_expected` is the model's own changed-symbol set — equal by construction, so the +5 is a pure
  runaway backstop), **OR** if, after `cancel_all_orders`, any symbol in `changed` still has an active
  (open/accepted/pending) order in `get_orders(OPEN)` (no duplicate active submission chain per symbol).
- **Data dependencies:** planned `changed` set; `get_orders(status=OPEN)` after `cancel_all`.
- **Fail-open / fail-closed:** **fail-closed** (skip + alarm) on either breach.
- **Expected false positives:** a `cancel_all` that has not settled leaves stale OPEN orders (the AMAT
  held-for-orders case) → transient duplicate-chain trip; mitigate by re-querying after a short settle and
  treating `canceled`/`pending_cancel` as inactive.
- **Offline tests:** planned == unique changed passes; 6 injected duplicate orders block (count); a symbol with a
  pre-existing OPEN order blocks (chain); a `pending_cancel` order is treated inactive (no false block).
- **Paper-mode integration test:** on paper, confirm `get_orders(OPEN)` drains to 0 after `cancel_all` before
  submit; confirm a normal night's count equals unique changed symbols.
- **Rollback:** remove the count assertion + open-order precheck.

### 7.6 Projected buying-power validation
- **Exact calculation:** `bp_used = Σ_{buys} order_notional[s]` (longs consume ~1× notional under RegT paper).
  Require `BP_available − bp_used ≥ 0.20·E` **AND** projected maintenance excess
  `proj_ME = E − Σ_s m(s)·|proj_qty[s]|·price[s] > 0`, with `m(s)=0.25` long / `0.30` short (Alpaca paper
  defaults; baseline from `get_account().maintenance_margin`).
- **Data dependencies:** `get_account()` {`equity`, `buying_power`, `maintenance_margin`, `last_equity`}, prices,
  deltas.
- **Fail-open / fail-closed:** **fail-closed** (skip + alarm; no partial submit — partials muddy incubation
  attribution).
- **Expected false positives:** the conservative maintenance-rate assumption can under-state BP on a mostly-long
  ETF book and trip near a margin-model boundary; paper margin differs from live.
- **Offline tests:** mocked low BP → block; ample BP → pass; `proj_ME ≤ 0` → block; short-heavy projection uses
  0.30 rate.
- **Paper-mode integration test:** read real paper `get_account`, compute projected BP, submit the real nightly
  rebalance, then assert next-day realized `buying_power` usage ≤ the guard's projection (no under-block).
- **Rollback:** remove the check.

### 7.7 Stale-price detection
- **Exact calculation:** let `S*` = the most recently completed regular trading session from an exchange
  calendar (documented-holiday–aware). For each held/target `s`, require `last_bar_date[s] == S*`; otherwise
  flag stale. Alarm always; **fail-closed** for a book if any of its held/target names is stale. Signal-only
  names (`^VIX`, `VIX3M`) are exempt from the trading gate (logged only).
- **Data dependencies:** bar timestamps from the panel build + snapshot; exchange trading calendar
  (`pandas_market_calendars` if available, else a maintained holiday list); the `signal_only` set from
  `sandbox_meta.json`.
- **Fail-open / fail-closed:** alarm = **fail-open** (observability); the trading gate on a stale held/target
  name = **fail-closed**.
- **Expected false positives:** half-day / early-close sessions; a newly listed ETF; a calendar package lagging a
  newly declared holiday; a name legitimately not trading that session.
- **Offline tests:** panel with a stale target column → flagged + gated; fresh panel → clean; a documented
  holiday `S*` → not flagged; a stale signal-only column → logged, not gated.
- **Paper-mode integration test:** run on a real post-holiday session and confirm no false stale trip; withhold
  one symbol's latest bar in a fixture-backed live dry-run and confirm the gate fires for its book only.
- **Rollback:** detection defaults read-only; disable the fail-closed coupling flag.

### 7.8 Daily-loss controls (tiered)
- **Exact calculation:** `dl = (equity_now − last_equity) / last_equity` using `get_account().last_equity`
  (prior-close equity). Tiers: `dl ≤ −0.03` → **alert only**; `dl ≤ −0.05` → **block risk-increasing
  submissions** (allow only orders that reduce projected account gross or |net|; an order is risk-increasing if
  it raises `Σ|proj_qty·price|` vs current for that account); `dl ≤ −0.08` → **full submission halt** (equiv. to
  §7.9 cancel/halt), alert.
- **Data dependencies:** `get_account()` {`equity`, `last_equity`}, planned deltas, projected vs current gross.
- **Fail-open / fail-closed:** −3% tier **fail-open** (informational); −5% and −8% tiers **fail-closed**.
- **Expected false positives:** a levered vol book (2× QQQ) can hit −3/−5% on a normal market down day — not an
  error, correct de-risking behavior; `last_equity` distortion from a deposit/withdrawal or the Monday flatten
  MTM; corporate-action MTM jump.
- **Offline tests:** synthetic equity at −3.1 / −5.1 / −8.1% → correct tier; at −5% a risk-reducing order passes
  but a risk-increasing order blocks; at −8% all submissions halt.
- **Paper-mode integration test:** feed a shifted `last_equity` via a test harness against paper read-only,
  confirm tier classification; on a real modest down day confirm the −3% alert fires and submission still proceeds.
- **Rollback:** set tier thresholds to −∞; remove the risk-increasing classifier.

### 7.9 Emergency-stop procedure
- **Exact calculation / behavior:** a HALT sentinel (repo-root file or a manifest flag) OR an auto-trip from the
  §7.8 −8% tier. On HALT: `broker.cancel_all_orders()` + submit nothing + alert. **No automatic liquidation** —
  existing positions are left untouched. Reversible by removing the sentinel.
- **Data dependencies:** sentinel presence/readability; §7.8 daily-loss tier.
- **Fail-open / fail-closed:** **fail-safe** — an unreadable/ambiguous sentinel is treated as HALT.
- **Expected false positives:** a stale sentinel left in place blocks a legitimate night; an auto-trip on a
  distorted `last_equity` (see §7.8).
- **Offline tests:** sentinel present → `cancel_all` called + no submit + alert + **no liquidation order**;
  absent → normal; unreadable → HALT; §7.8 −8% → writes sentinel + halts, emits no sell-to-flat order.
- **Paper-mode integration test:** place the sentinel, run the live path against paper, confirm zero orders
  submitted, open orders canceled, positions unchanged (no liquidation); remove sentinel, confirm normal resumes.
- **Rollback:** delete the sentinel; remove the auto-trip wiring; stateless.

### 7.10 Leveraged-long financing (research-validity; not order-path)
- **Exact calculation:** per book per day, `lev_notional = max(gross − 1.0, 0)·NAV_book`;
  `financing_day = lev_notional · (r_on + 0.015)/360` (actual/360), `r_on` = reference overnight rate
  (SOFR/EFFR from FRED). Reported as an explicit column alongside — **not** folded into the frozen scorecard.
- **Data dependencies:** per-book daily gross series (ledgers), book NAV/notional, FRED overnight-rate series
  (already PASS, keyless).
- **Fail-open / fail-closed:** N/A to trading (reporting). Missing rate ⇒ documented flat fallback + flag.
- **Expected false positives:** none in a trading sense; the modeled charge over/under-states if the rate proxy
  diverges from a real financing cost (paper has none) — disclosed as a research adjustment.
- **Offline tests:** a book held at constant 1.45× gross for N days →
  `financing ≈ (0.45·NAV)·(r_on+1.5%)·N/360`; a long-only 1.0× book → 0.
- **Paper-mode integration test:** N/A (no real paper financing) — instead a determinism test: the reported
  financing column recomputes exactly from the ledger gross series + FRED rate.
- **Rollback:** remove the additive column; frozen numbers unaffected.

### 7.11 Short borrow (research-validity; short-capable books only)
- **Exact calculation:** `borrow_day = Σ_{shorts} |short_mv[s]| · rate[s]/360`; `rate[s]` = actual broker/locate
  rate where the API exposes it, else a documented conservative floor (propose GC floor 50 bps; hard-to-borrow
  names flagged and floored higher). Applies only to books that produce short targets — **none of the current 7**.
- **Data dependencies:** per-symbol short market values; broker borrow-rate feed if available; a documented
  floor/HTB table.
- **Fail-open / fail-closed:** N/A to trading (reporting). Missing rate ⇒ conservative floor + flag.
- **Expected false positives:** the floor over-charges an easy-to-borrow large cap and under-charges a true HTB
  name — disclosed as deliberately conservative.
- **Offline tests:** a short book at `$X` short mv over N days at floor → expected borrow; a long-only book → 0.
- **Paper-mode integration test:** inactive until a short-capable book exists; the test asserts zero borrow for
  the current 7 books.
- **Rollback:** remove the additive column.

---

*Read-only audit; committed as a docs-only governance artifact. No strategy logic, allocation, schedule, frozen
specification, or broker state was modified. §7 is a proposal for approval — nothing in it is implemented, and
build begins only after the first clean operational cycle is completed and explicitly approved after the
clean-cycle report.*
