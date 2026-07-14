# Clean-Cycle Report — TEMPLATE (unpopulated)

**Status:** DOCUMENTATION-ONLY TEMPLATE. No results populated, no outcomes inferred, no manifest change, not
committed. Populate ONLY from broker + ledger evidence after the real first post-open cycle, then return for
approval **before** committing or changing `DEPLOYMENT_MANIFEST.md`.

**How to populate (rules):**
- Every value comes from a cited artifact — read-only `get_account` / `get_all_positions` / `get_orders`
  snapshots and `ledgers/hunt2026/*.jsonl` (esp. `_reconcile.jsonl`). Never infer a field; leave it
  `INCONCLUSIVE` with the reason if the evidence is missing.
- Keep **canceled** and **rejected** separate everywhere.
- Do not draw performance/alpha conclusions. This is an **operational** report.
- Do not record a clean-start timestamp (§11) unless §3 (all four gates), §5 (reconcile), and §9 (no material
  contamination) all pass.
- §7-of-the-audit risk controls remain **proposal-only** — this template neither implements nor assumes them.

> Fill placeholders written as `<…>`. Mark gate/verdict cells with the allowed enum only. Blank cells stay blank
> until evidenced.

---

## 1. Cycle identification

| Field | Value | Source |
|---|---|---|
| Broker session date (regular session being reconciled) | `<YYYY-MM-DD>` | exchange calendar / fill dates |
| Snapshot timestamp — pre-cycle baseline | `<ISO8601>` | read-only `get_account`/`get_all_positions` |
| Snapshot timestamp — post-cycle | `<ISO8601>` | read-only snapshot |
| Scheduler run ID | `<launchd run / nightly.log marker>` | `artifacts/hunt2026/paper/nightly.log` |
| Strategy / spec commit | `<git sha>` | frozen specs (`ff71245` / `354bf47` baseline) |
| Reconciliation-code commit | `<git sha>` | `scripts/hunt_paper_reconcile.py` HEAD |
| Clean-start candidate timestamp | `<ISO8601 or blank>` | recorded in §11 only if all conditions pass |

---

## 2. Pre-cycle baseline

Source: read-only `get_account` + `get_all_positions` + `get_orders(OPEN/ALL)` at the §1 pre-cycle snapshot;
cross-check `_reconcile.jsonl` last pre-open row.

| Metric | Value | Source |
|---|---|---|
| Equity | `<$>` | `get_account().equity` |
| Cash | `<$>` | `get_account().cash` |
| Buying power | `<$>` | `get_account().buying_power` |
| Gross long | `<$>` | Σ long market value |
| Gross short | `<$>` | Σ |short market value| |
| Gross exposure (Σ\|mv\|) | `<$>` | positions |
| Net exposure (Σ signed mv) | `<$>` | positions |
| Foreign positions (count) | `<n>` | `foreign_positions.n` |
| Open flatten orders (count) | `<n>` | `get_orders(OPEN)` opposing held side |
| Flatten quantity — submitted | `<shares>` | `flatten_submitted_qty` Σ |
| Flatten quantity — filled | `<shares>` | `flatten_filled_qty` Σ |
| Flatten quantity — remaining | `<shares>` | `flatten_remaining_total` |

---

## 3. Four-part flatten gate

Mark each **PASS / FAIL / INCONCLUSIVE** with the evidence that decided it. "No open orders remain" is NOT
sufficient. Gate = COMPLETE only if all four PASS.

| # | Gate | Result | Evidence |
|---|---|---|---|
| 1 | Foreign position count = 0 | `<PASS\|FAIL\|INCONCLUSIVE>` | `<foreign_positions.n = ?>` |
| 2 | Remaining flatten quantity = 0 | `<PASS\|FAIL\|INCONCLUSIVE>` | `<flatten_remaining_total = ?>` |
| 3 | No terminally failed flatten order (filled/canceled/rejected/expired) attached to a nonzero position | `<PASS\|FAIL\|INCONCLUSIVE>` | `<per-symbol order_status vs qty>` |
| 4 | Independent broker snapshot agrees with the ledger (positions, signed exposure, flatten quantities) | `<PASS\|FAIL\|INCONCLUSIVE>` | `<fresh get_* vs _reconcile.jsonl diff>` |

**Overall flatten gate:** `<COMPLETE / NOT COMPLETE>` — `<one-line reason>`

---

## 4. Residual exception table

One row per still-held foreign / unresolved position (empty if gate fully PASSes). No corrective orders are
proposed here without explicit authorization.

| Symbol | Signed qty | Side | Price | Signed MV | Order status | Submitted qty | Filled qty | Remaining qty | Asset status | Tradable | Probable cause | Manual-intervention recommendation |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| `<SYM>` | `<±q>` | `<long/short>` | `<$>` | `<±$>` | `<status>` | `<q>` | `<q>` | `<q>` | `<active/halted/delisted>` | `<yes/no>` | `<cause>` | `<recommendation>` |

*(If empty: "No residual exceptions — all foreign inventory flattened and reconciled.")*

---

## 5. Seven-book target reconciliation

Source: `_account` aggregate target row vs `get_all_positions`; per-symbol at the run-date reference close.

| Field | Value | Source |
|---|---|---|
| Intended aggregate holdings (Σ target $) | `<$>` | `_account.target_dollars` |
| Actual broker holdings (Σ held $) | `<$>` | positions × ref close |
| Position-gap fraction | `<%>` | `position_gap_frac` |
| Missing target symbols (in target, not held) | `<list / none>` | set diff |
| Foreign symbols (held, in no target) | `<list / none>` | `foreign_positions.symbols` |
| Silent-flat books (nonzero target, no fill, no position ≥2 nights) | `<list / none>` | `books[*].flat_nights ≥ 2` |

**Per-symbol difference table:**

| Symbol | Intended qty | Actual qty | Qty diff | Intended $ | Actual $ | Notional diff |
|---|---|---|---|---|---|---|
| `<SYM>` | `<q>` | `<q>` | `<Δq>` | `<$>` | `<$>` | `<Δ$>` |

**Reconcile sufficiently to begin the clean forward clock?** `<YES / NO / INCONCLUSIVE>` — `<reason; threshold:
position_gap_frac in-band, zero foreign, zero silent-flat>`

---

## 6. Order and fill summary

Canceled and rejected kept separate. Source: `get_orders` bucketed to the run-date; `_reconcile.jsonl` counts.

| Outcome | Count | Source |
|---|---|---|
| Submitted | `<n>` | `n_orders` (+canceled) |
| Broker accepted | `<n>` | accepted/open + terminal |
| Filled | `<n>` | `n_fills` |
| Partial | `<n>` | `n_partial` |
| Canceled | `<n>` | `n_canceled` |
| Rejected | `<n>` | `n_rejects` |
| Expired | `<n>` | reject-bucket subclass |
| Replaced | `<n>` | `n_replaced` |
| Still open | `<n>` | `get_orders(OPEN)` |

---

## 7. Slippage

ETFs and stocks separate. Side-adjusted vs the run-date reference close; positive = worse than model. **Do not
draw conclusions from a sample too small to support them** — if `fill count < 20` per class, report the numbers
and explicitly state the sample is below the pre-registered threshold and interpretation is withheld.

| Metric | ETF | Stock |
|---|---|---|
| Fill count | `<n>` | `<n>` |
| Median (bps) | `<>` | `<>` |
| Mean (bps) | `<>` | `<>` |
| Notional-weighted mean (bps) | `<>` | `<>` |
| 95th percentile (bps) | `<>` | `<>` |
| Worst fill (bps, symbol) | `<>` | `<>` |
| % within frozen assumption | `<% ≤ 2 bps>` | `<% ≤ 10 bps>` |

- **Reference-price definition:** `<run-date adjusted reference close used by reconcile>`
- **Fills excluded (and why):** `<list, e.g. flatten-leg fills, unpriced ref, or "none">`
- **Sample sufficiency:** `<≥20 per class → interpretable / <20 → withheld>`

---

## 8. Account changes

| Metric | Before | After | Δ |
|---|---|---|---|
| Equity | `<$>` | `<$>` | `<$>` |
| Buying power | `<$>` | `<$>` | `<$>` |
| Cash | `<$>` | `<$>` | `<$>` |
| Gross exposure | `<$>` | `<$>` | `<$>` |
| Net exposure | `<$>` | `<$>` | `<$>` |

| Derived | Value | Basis |
|---|---|---|
| Realized transition P&L | `<$>` | equity Δ adjusted for any cash flows |
| Estimated flatten costs | `<$>` | flatten fills × slippage vs ref |
| Unattributed residual | `<$>` | transition P&L − (expected MTM + flatten costs); flag if material |

---

## 9. Contamination assessment

Was the cycle affected by any of the following? Mark each and cite evidence. Any YES that is material blocks the
clean start (§10/§11).

| Source | Affected? | Evidence / note |
|---|---|---|
| Legacy inventory (stat-arb residue) | `<YES/NO>` | `<§3/§4>` |
| Flatten costs | `<YES/NO>` | `<§8>` |
| Order netting (cross-book) | `<YES/NO>` | `<aggregate submission behavior>` |
| Stale data | `<YES/NO>` | `<bar freshness at run>` |
| Rejected or partial orders | `<YES/NO>` | `<§6>` |
| Corporate actions | `<YES/NO>` | `<splits/divs on held names in window>` |
| Broker or scheduler failures | `<YES/NO>` | `<nightly.log / run ID>` |

**Material contamination remaining?** `<YES / NO>` — `<one-line reason>`

---

## 10. Readiness verdict

Choose exactly one:

- [ ] TRANSITION INCOMPLETE
- [ ] OPERATIONAL CYCLE PASSED, CLEAN CLOCK NOT STARTED
- [ ] CLEAN FORWARD INCUBATION STARTED
- [ ] MANUAL REVIEW REQUIRED

**Verdict:** `<one of the above>`
**Exact reason:** `<cite the deciding §3 gate / §5 reconcile / §9 contamination result>`

---

## 11. Clean forward start

Record a clean-start timestamp **only if** all three hold: (a) all four §3 flatten gates PASS; (b) §5 seven-book
holdings reconcile; (c) §9 shows no material contamination. Otherwise leave blank.

- **Clean-start timestamp:** `<ISO8601 — or leave BLANK>`
- **Conditions met:** §3 `<…>` · §5 `<…>` · §9 `<…>`
- **Note:** recording this here does NOT edit the manifest. Manifest update is a separate Coordinator action taken
  only after this report is approved.

---

## 12. Next action

Exactly one operational next action.

**Next action:** `<single imperative — e.g. "Re-run reconcile at next open; residual AMAT leg still unfilled" OR
"Submit clean-start manifest edit for approval">`

---

*Documentation-only template. Populate from broker + ledger evidence after the real cycle, then return for
approval before committing or changing the manifest. §7-of-the-audit risk controls stay proposal-only.*
