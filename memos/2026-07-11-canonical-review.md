# Alpha Lab — Canonical Project-Level Synthesis & Independent Review

**Date:** 2026-07-11 · **Status:** CANONICAL (authoritative project-level synthesis) · **Type:** read-only review
**Git HEAD at authorship:** `de0ad01` (branch `main`, 47 commits ahead of origin, unpushed)
**Scope note:** No strategy, allocation, scheduler, frozen experiment, book, ledger, or manifest deployment
state was modified in producing this document. This is evidence + synthesis only. Where the
`DEPLOYMENT_MANIFEST.md` and any other doc disagree on deployment state, **the manifest wins**.

**Primary sources:** `DEPLOYMENT_MANIFEST.md`; `research/hunt2026/{STATUS,RESEARCH_OBJECTS,CONFIDENCE_LADDER,TRIAL_LEDGER,FAILURES,PREREGISTRATION}.md`, `results*/`, `robustness/`, `walkforward/`; `memos/hunt2026-*.md`; `redteam/2026-07-10/{SCOPE,CHARTER,AUDIT_*_COMPLETION}.md` + `adjudicator/FINAL_REPORT.md` + `agent9/*.csv`; `research/discovery/*`; `research/independent_alpha/*` (`independence/betas.csv`, scoreboards, `INDEPENDENCE_MATRIX.md`); `research/estimator_lab/*`; `research/{macro_data_layer,stock_universe_repair}/*`; `ledgers/hunt2026/*.jsonl`.

---

## 0. One-paragraph verdict

Alpha Lab is a **strong research and governance apparatus governing a weak set of strategies**. It has
technically clean implementations (independent-engine reproduction to 0.0000 bp; 6/7 clean-room to 0.000
bp; no leakage), **one credible portfolio-construction object** (`defensive_ensemble`), **no validated
independent alpha** (one Level-3 market source, cross-market replication run and refused), and **zero
forward evidence** (go-live 2026-07-10; market not open since; 0 fills). Nothing is a live-capital
candidate. The single most decision-relevant fact: the vol books' headline "excess vs naive" is
**leverage, not alpha** — it survives a single-factor regression but not an exposure-matched benchmark.

---

## 1. The four reconciliations (corrections requested 2026-07-11)

### 1.1 Stock-universe counts — one table

All counts computed from primary artifacts: `data/raw/sp500_pit.parquet` (PIT change-log, 2,712 dated
membership snapshots), `research/hunt2026/panel_2005.parquet` (the frozen price panel),
`research/stock_universe_repair/coverage.csv` (continuity audit), and
`research/stock_universe_repair/POLYGON_STATUS.md` (missing-name join).

| Figure | Value | Exact definition | Source |
|---|---|---|---|
| Ever-S&P-500 members since 2014 | **1,202** | Union of `members` across all 2,712 PIT change-log dates | `sp500_pit.parquet` (recomputed) |
| Distinct tickers as columns in the panel | 1,730 | All tradable columns in `panel_2005` (superset: non-S&P, ETFs, signal tickers) | `panel_2005.parquet` |
| Ever-members **present** in the panel | **820** | ever-members ∩ panel close columns | recomputed (820 + 382 = 1,202) |
| Ever-members **missing** from the panel | **382** | ever-members with **no column at all** (never fetched) | `POLYGON_STATUS.md` / `polygon_reference.py` |
| Ever-members audited by the continuity audit | **777** | rows in `coverage.csv` (build's membership-mask set; 43 fewer than 820 — narrower "recent members" filter + share-class normalization) | `coverage.csv` |
| — of those, **zero-coverage** (empty column) | **168 (22%)** | flagged member, `priced_member_days = 0` (all-NaN price column) | `coverage.csv` (`coverage==0`) |
| — **genuinely usable** PIT history (≥99%) | **595 (77%)** | `coverage ≥ 0.99` | `coverage.csv` |
| — partial (0 < cov < 0.99) | 14 | | `coverage.csv` |
| — priced at least once (cov > 0) | 609 | 595 clean + 14 partial | `coverage.csv` |
| **Member-day-weighted coverage** | **87.21%** | Σ priced_member_days / Σ member_days = 1,382,942 / 1,585,826 | `coverage.csv` (recomputed) |
| Per-ticker mean coverage (unweighted) | 77.95% | simple mean of the `coverage` column | `coverage.csv` |

**Empty columns vs usable histories (the distinction requested):**
- **Genuinely usable PIT price histories:** ~**595–609** names (≥99% / >0 coverage). This is the *effective*
  tradable stock universe `momentum_concentrated` ever ranked over.
- **Empty columns** (member flagged, price column all-NaN): **168** — present in the panel schema but
  contribute nothing; a name whose column is NaN cannot be ranked or held.
- **No column at all:** **382** ever-members never fetched (delisted/merged/renamed before the yfinance
  window).
- **Net:** of **1,202** ever-members, only ~**49–51%** are usable histories. The stock book is built on
  survivors. Bias is **bounded** (not falsely positive) because cross-sectional momentum's rank IC ≈ 0
  (F-016, t = −0.07) — the incomplete universe makes the book *incomplete*, not *inflated*.

**The "87.2%" vs "77.95%" gap** is not a contradiction: 87.2% is member-day-weighted (how much of the
index is priceable on a typical day); 77.95% is the unweighted per-ticker mean (dragged down by dead
names with few member-days and zero coverage). Both are correct measures of different things.

**Repair status:** identifier/delisting track materially advanced (Polygon reference-tier joins
auto-dated 205 of 382 missing delistings + 54 FIGIs; `id_map.csv` hand-seeds 15). **Price track still
BLOCKED** — Polygon's provisioned plan returns `403 NOT_AUTHORIZED` on daily aggregates; a
survivorship-complete price panel needs a price-tier upgrade or FactSet/Tiingo/CRSP. `panel_stocks_v2`
does not yet exist; the frozen v1 panel and `momentum_concentrated`'s BLOCKED verdict are preserved.

### 1.2 The 271 foreign positions — decomposition

Source: `ledgers/hunt2026/_reconcile.jsonl`, last record `run_at 2026-07-11T00:32:08`.
Computation in `scripts/hunt_paper_reconcile.py:162-164`:
`foreign = {sym: qty for sym,qty in get_all_positions() if sym not in known and |qty|>1e-9}`;
`foreign_dollars = Σ |qty| × close`.

| Field | Value | Note |
|---|---|---|
| Count (n) | **271 symbols** | held in no book target and not a benchmark leg |
| **Gross exposure** (Σ \|qty\|×close) | **$141,671.51** | the `dollars` field **is gross** (uses `abs(qty)`) |
| Gross / account equity | **1.405×** ($141,672 / $100,794) | exceeds 1.0 → margin/leverage present |
| Timestamp (snapshot as-of) | 2026-07-11T00:32:08 | last read-only reconcile |
| Origin | legacy stat-arb dead-name roster | manifest: "Dead statarb book flattened 2026-07-10; fill Monday open" |
| Gross long | **NOT RECORDED** | reconcile persists only {n, gross dollars, sorted symbols}; per-position `qty`/`side` not stored |
| Gross short | **NOT RECORDED** | same |
| Net exposure | **NOT RECORDED** | signs discarded before persistence; net is not recoverable from the ledger |
| Priced vs unpriced positions | **NOT RECORDED as a count** | unpriced names contribute $0 to the gross via `closes.get(s) or 0.0`, but the split is not logged |
| Submitted flatten quantity | **NOT RECORDED** | reconcile is read-only and never submits; the flatten closes (submitted 2026-07-10 by the run script) are not captured in any committed ledger artifact |
| Remaining quantity | **271 symbols / $141,671.51 gross** (per-symbol qty not stored) | these 271 *are* the un-flattened remainder |
| Status | **stat-arb flatten / AMAT NOT COMPLETE** | reconcile alarm; `position_gap_frac 2.5684` |

**Honest limitation (as of the committed ledger):** the long/short/net/priced-unpriced/flatten-quantity
decomposition was **not derivable from any committed artifact** — the reconcile schema persisted only
aggregate gross dollars, the count, and the symbol list. This was an observability gap in the reconcile
schema, now closed (see addendum).

**Addendum — read-only broker snapshot, 2026-07-11 (resolves the fields above).** A read-only
`get_all_positions` / `get_account` / `get_orders(OPEN)` snapshot (no ledger write, no order submitted)
and the new decomposition instrumentation (`scripts/hunt_paper_reconcile.py`, commit `da5dc8e`) measure
the signed decomposition directly:

| Field | Value |
|---|---|
| Foreign positions | **271** (285 total − 14 in-book) |
| Long legs / short legs / unpriced | **106 / 165 / 0** |
| Gross long | **$55,419.78** |
| Gross short | **$86,251.64** |
| **Gross** (Σ \|mv\|) | **$141,671.42** (matches the $141,671.51 gross to price drift) |
| **Net** (Σ signed mv) | **−$30,831.86** |
| Gross / equity | 1.406 |
| Net / equity | **−0.306** |
| \|Net\| / gross | **0.218** |
| Open flatten orders | **271** (1,563 shares submitted, **0 filled**) |
| Account equity | $100,794.31 |

**Interpretation:** the $141.7K gross is **primarily offsetting long/short inventory** — 78% of the gross
nets out (|net|/gross = 0.22) — **but it carries a material residual net short of −$30.8K (−30.6% of
equity)**, a real directional tilt, not negligible. This is consistent with the legacy stat-arb book being
a long/short (106L/165S) roster mid-flatten. **Flatten is NOT complete:** 271 positions still held and
1,563 flatten shares still unfilled (0 filled) — it fills at Monday's open. Per the standing rule, the
flatten is **not** to be called complete until broker positions **and** remaining flatten quantities are
both zero.

### 1.3 The 68 order outcomes — split (canceled and rejected kept separate)

Source: `_reconcile.jsonl`. Classification logic `hunt_paper_reconcile.py:125-141`
(filled → fills[]; `status=="replaced"` → replaced; `status=="canceled"` → canceled;
else rejected/expired/closed-zero-fill → rejects[]).

| Outcome | Count | Source |
|---|---|---|
| Submitted (total) | **68** | first run `n_orders 68` |
| Accepted / still open | **0** | terminal-status query (`QueryOrderStatus.CLOSED`) returns only resolved orders |
| Filled | **0** | `n_fills 0` every run |
| Partial | **0** | `n_partial 0` |
| **Canceled** | **68** | `n_canceled 68` (records 1–3, corrected schema); per-order `status` = "canceled" for all 68 |
| **Rejected** | **0** | `n_rejects 0` (corrected schema) |
| Expired | **0** | expired would route to the reject bucket (line 140); bucket is empty |
| Replaced | **0** | `n_replaced 0` |

**Reconciling the two conflicting records:** the **first** reconcile (`22:56:54`, record 0) reported
`n_rejects 68, reject_rate 1.0` under a **pre-fix schema** that lacked `n_canceled/n_partial/n_replaced`
fields and lumped canceled orders into "rejects" — yet even there, every entry in its `rejects[]` array
carries `status: "canceled"`. The **later** reconciles (`22:58`, `00:31`, `00:32`, records 1–3) use the
corrected classifier: **`n_canceled 68`, `n_rejects 0`**. Authoritative split = **68 canceled, 0
rejected**. Cause (script `:224` self-report): "order(s) self-canceled by re-runs" — the 68
aggregate-target day-orders from Friday's 20:30 submission were canceled by subsequent nightly re-runs
before Monday's open; **none ever reached a fill**. This is expected weekend behavior, not a rejection by
the broker.

### 1.4 CAPM alpha vs exposure-matched excess — why they disagree

**The paradox:** `independence/betas.csv` and the red-team's own regression show *positive, significant*
alpha for the vol books, while the exposure-matched excess is *~0 or negative*. Both are correct; they
answer different questions. The "alpha" shrinks monotonically to zero as the benchmark is made to match
the book's actual exposure. Worked for **vol_managed_qqq** (all from `redteam/.../agent9/*.csv` and
`independence/betas.csv`):

| # | Model | Benchmark it subtracts | vol_managed_qqq "alpha" | signif. | window |
|---|---|---|---|---|---|
| A1 | 1-factor **SPY** regression | β·SPY, β fit freely (β_SPY≈1.03) | **+11.47%/yr** | t = 3.36 | long (n=4,659) |
| A2 | 2-factor **SPY+QQQ** regression | β_SPY·SPY + β_QQQ·QQQ (β_SPY −0.39, β_QQQ +1.38) | **+5.53%/yr** | — | full (n=5,413), `betas.csv` |
| A3 | 1-factor **QQQ** regression | β·QQQ (β_QQQ≈1.03) | **+6.20%/yr** | t = 2.65 | long |
| B1 | **Exposure-matched** (avg gross × QQQ, buy-hold) | 1.448× QQQ | **+1.01%/yr** | Sharpe Δ +0.162 | long |
| B2 | Exposure-matched, out-of-sample | 1.427× QQQ | **+0.32%/yr** | t = 0.43 (ns) | holdout (n=252) |
| B3 | B1 minus financing on excess leverage | + ~5% × (1.45−1.03)× | **≈ −1.1%/yr** | — | derived |

**Assumptions and why the number moves:**

- **Exposure definition is the whole story.** Model A benchmarks against a **fitted market β** (~1.03×
  QQQ). Model B benchmarks against the book's **average gross exposure** (~1.45× QQQ). The book *times*
  exposure between 0 and 2×; its realized β-to-QQQ (1.03) is **lower** than its average notional gross
  (1.45) because the vol-scaling de-levers precisely when the market is most volatile (down), pulling
  realized beta below average notional. Model A credits that uncounted **(1.45 − 1.03) ≈ 0.42×** of
  persistent QQQ leverage as *alpha*; Model B charges it as *beta*.
- **The gap is an identity, not a mystery:** regression-α(QQQ) − exposure-matched-excess ≈
  (avg_gross − β_QQQ) × r_QQQ = (1.448 − 1.033) × 16.37% ≈ **+6.8%/yr** — which is essentially the entire
  +6.20% one-factor-QQQ alpha. Subtract a benchmark 0.42× larger and the alpha evaporates.
- **Financing.** Neither model charges borrow explicitly. But Model B forces you to compare against
  *actually holding* the leverage; add a ~5% short-rate cost on the 0.42× excess exposure (≈ −2.1%/yr)
  and the +1.0% long-window excess goes **negative** (row B3). Model A's free-β intercept hides this.
- **Statistics converge out-of-sample.** Model A's alpha is significant only on the **full in-sample**
  window (t = 3.36, n = 4,659) where a persistent bull-era leverage premium looks like skill. On the
  **blind 252-day holdout**, the same regression alpha is **+5.20%/yr, t = 0.43 — not significant** — and
  agrees with the exposure-matched excess (+0.32%). Both models say the same thing OOS: **no significant
  alpha.**

**The exception that proves the rule — defensive_ensemble.** Its raw exposure-matched excess is *negative*
(−4.74%/yr long) because it deliberately earns less return than a 1.88× SPY control — **but at far lower
risk**: `sharpe_minus_ctrl` = **+0.281 (long)** and **+0.702 (holdout)**, and its regression alpha is
+9.42%/yr (t = 3.24 long) / +17.71%/yr (t = 1.71 holdout). Here the two models **agree** there is genuine
*risk-adjusted* portfolio value — it is not levered beta. This is why it is the one book that survives as
a portfolio-construction object rather than a leverage vehicle.

**Bottom line:** the vol/trend cluster has **no independent alpha** once benchmarked fairly — it is a
vol-timed levered-QQQ position whose "excess" is the leverage. `defensive_ensemble` is the only book with
value that survives exposure matching (on a Sharpe basis). This is consistent across every source and is
the load-bearing conclusion of the review.

---

## 2. Authoritative state (verified from disk / broker)

| Item | State |
|---|---|
| Git HEAD | `de0ad01` 2026-07-11 00:59; `main` **47 commits ahead of origin, unpushed**; tree clean but for untracked scratch |
| Account | **Alpaca PAPER only** (no real-money code path); equity **$100,794** |
| Books | **7** (authoritative per manifest), equal capital ≈ $14.4k, started 2026-07-10; ONE aggregate account target submitted nightly |
| Fills | **0** (market not open since Fri go-live); 68 orders → 68 canceled |
| Broker residue | 271 foreign positions, $141,672 gross; stat-arb flatten / AMAT **not complete** (fill expected Monday) |
| Scheduler | `com.rimrim.hunt2026-paper` (weekdays 20:30, loaded) + `com.rimrim.earnings-collect` (21:15, **enabled read-only**) |
| Discovery | **MAINTENANCE MODE** (2026-07-10) |
| Estimator lab | complete; F-021 CLOSED |
| Earnings lane | **0/300 matured**; dormant, 6 arming conditions |
| Universe repair | 168/777 zero-coverage; identifier track advanced; price track BLOCKED |
| Macro data | FRED **PASS** (keyless); VIX3M research-PASS / live-BLOCK |

**Adjudicated contradictions:** 6-vs-7 books → **7**; `dual_momentum_gem` retired-in-ledger but **live as
a control**; Level-4 replication **run and failed** (F-020, 3/7 clusters, p=0.77), not "unattempted";
`CANONICAL_STATE.md` and `macro_data_layer` superseded; red-team FINAL_REPORT clean-room ("6 NOT
TESTABLE") superseded by AUDIT_C_D (6/7 to 0.000 bp); CAPM-α vs exposure-matched excess reconciled in §1.4.

---

## 3. Research results (condensed; full evidence in cited files)

**Independent alpha:** none validated. Registry's own words: "the honest number of live, distinct,
independent market forecasts is **1** (AS-01 vol-managed equity), 2 if you credit trend, 3 if you credit
the VRP sleeve." 12 market sources catalogued; 7 falsified/retired.

**Red-team (10 agents + adjudicator; workflow killed mid-run by spend limit, adjudicator reproduced all
code first-hand):** 0 repo bugs; engine RULED OUT (0.0000 bp independent reproduction, all 7); look-ahead
RULED OUT (future-poison, all 7); clean-room 6/7 to 0.000 bp, `defensive_ensemble` 277.6 bp = docs↔code
gap (F-RT-07, fixed docs, frozen code unchanged); perturbation SURVIVES (real fragility = missing-obs,
F-RT-03, the 13% NaN stock universe); adversarial all 7 SURVIVE; levered vol books carry a −12 to −16%
2022 bear-onset tail. Confirmed methodological weaknesses: **F-RT-01** (7 books ≈ 2–3 sleeves;
excess-vs-naive is leverage), **F-RT-02** (effective trials ≈ 2.3 not 18 → repo DSR was *conservative*),
**F-RT-07**. Per-book: vol_managed / trend_vol / defensive = SURVIVES; vol_core / gold / gem =
PROVISIONAL; momentum_concentrated = BLOCKED. No book INVALIDATED.

**Discovery:** MAINTENANCE MODE. EXP-A bond carry **REJECTED** (t=1.53<2, holdout sign reversal, F-022);
EXP-B conditional-vol **MECHANISM UNSUPPORTED** (wild-cluster bootstrap p=0.4375). No independent source
found. Earnings lane 0/300 matured.

**Estimator lab:** JSE effect real but immaterial — long-only helps at every window (−2.6 bps at n=42 →
−0.5 bps at n=252, all p<1e-4), unconstrained hurts (+18 to +49 bps); **no crossover**; ψ̂ has no timing
content; MP-clipping best unconstrained, pca1 best long-only. F-021 = reporting drift only (pipelines
agree to 2.7e-16). **Academically interesting, operationally immaterial.**

**Data:** FRED PASS (keyless CSV, all 9 series unrevised, 1-bd lag); VIX3M research conditional-PASS /
live-BLOCK (yfinance 6-bd stale); universe repair BLOCKED on survivorship-complete vendor.

---

## 4. Rankings, cards, performance — key tables

### Most promising (overall): `defensive_ensemble` > vol/trend cluster (as one object) > everything else.

### 5Y (blind where noted) + walk-forward + DSR, regimes separate

| Book | 1Y-blind net | 5Y CAGR | 5Y blind? | 5Y Sharpe | 5Y maxDD | WF median excess | WF worst | DSR |
|---|---|---|---|---|---|---|---|---|
| vol_managed_qqq | +42.5% | +23.3% | No | 0.94 | −35.2% | +13.4pp | −30.8% | 81.5% |
| vol_core_svxy | +36.1% | +24.3% | No | 0.93 | −33.8% | +12.4pp | −31.1% | 81.2% |
| trend_vol_qqq | — | +24.7% | **Yes** | 1.11 | −19.6% | +8.0pp | −22.0% | 89.8% |
| defensive_ensemble | — | +19.9% | **Yes** | 1.32 | −13.4% | +1.4pp | −18.3% | **95.8%** |
| dual_momentum_gold | — | +29.1% | **Yes** | 1.07 | −35.7% | +6.9pp | −25.7% | 87.7% |
| dual_momentum_gem | +58.6% | +18.0% | No | 0.74 | −37.5% | +9.3pp | −24.3% | 68.2% |
| momentum_concentrated | +35.4% | +16.6% | No | 0.80 | −17.1% | **−4.6pp** | −13.5% | 72.4% |

Benchmarks: 1Y SPY +21.2% / QQQ +31.5%; 5Y SPY CAGR +13.0%.
**Exposure-matched excess (the decision number, §1.4):** vol_managed +0.3%/yr (t=0.43, ns), vol_core
−16.7%/yr, trend −5.5%/yr (holdout); only **defensive_ensemble** beats its control on Sharpe (+0.70).

### Year-by-year (concentration test)

| Book | 2021* | 2022 | 2023 | 2024 | 2025 | 2026* |
|---|---|---|---|---|---|---|
| SPY | +9.8% | −18.2% | +26.2% | +24.9% | +17.7% | +10.6% |
| vol_managed_qqq | +14.6% | **−30.8%** | +79.1% | +35.0% | +22.6% | +21.1% |
| trend_vol_qqq | +14.6% | **−11.2%** | +59.9% | +35.0% | +19.3% | +15.0% |
| defensive_ensemble | +8.1% | **+0.4%** | +11.4% | +22.3% | +45.2% | +15.3% |
| dual_momentum_gold | +11.2% | −25.5% | +16.3% | +51.1% | **+106.3%** | +19.3% |

**Concentration flags:** levered vol books' cumulative edge sits in 2023 (+79/+87%); `dual_momentum_gold`
is entirely the 2024–26 gold regime (rel_top10 0.68 per red-team) — remove it and the book is ordinary;
`defensive_ensemble`'s value shows in the 2022 down year (+0.4%). Single partial years are too short for a
meaningful Sharpe; round-1 books are **not blind** on the 5Y window.

### Portfolio

n_eff (raw) **2.80** / (residual) **4.12**; ~3 genuine clusters. Vol/trend cluster residual pairwise corr
**0.79**, crisis corr **0.765** (fails together). One market cluster + one portfolio wrap + shadow
controls (0/3 add incremental value; momentum_concentrated P(ΔSharpe>0)=**0.07**). **Not diversified**;
~2.8 effective bets. Roster correctly **frozen** through the +3-month gate.

### Confidence (red-team 8-axis, forward floored to 5)

| Book | code | engine | data | stats | mechanism | bench-rel | exec | robust | fwd | overall |
|---|---|---|---|---|---|---|---|---|---|---|
| defensive_ensemble | 95 | 98 | 90 | 80 | 80 | 75 | 80 | 82 | 5 | ~75 SURVIVES |
| vol_managed_qqq | 95 | 98 | 90 | 70 | 75 | 45 | 85 | 88 | 5 | ~68 SURVIVES |
| trend_vol_qqq | 95 | 98 | 90 | 72 | 70 | 55 | 85 | 85 | 5 | ~68 SURVIVES |
| vol_core_svxy | 95 | 98 | 88 | 68 | 55 | 30 | 78 | 70 | 5 | ~55 PROVISIONAL |
| dual_momentum_gold | 92 | 98 | 88 | 74 | 45 | 45 | 82 | 68 | 5 | ~55 PROVISIONAL |
| dual_momentum_gem | 92 | 98 | 88 | 62 | 55 | 40 | 82 | 70 | 5 | ~52 PROVISIONAL |
| momentum_concentrated | 92 | 98 | 55 | 60 | 35 | 40 | 75 | 60 | 5 | ~35 BLOCKED |

---

## 5. Verdicts

| Object | Verdict |
|---|---|
| defensive_ensemble | SURVIVES AUDIT WITH LIMITATIONS → CREDIBLE FOR CONTINUED PAPER STUDY |
| vol_managed_qqq / trend_vol_qqq | SURVIVES AUDIT WITH LIMITATIONS (levered beta + real tail overlay; not alpha) |
| vol_core_svxy / dual_momentum_gold / dual_momentum_gem | PROVISIONAL |
| momentum_concentrated | BLOCKED |
| EXP-A bond carry | REJECTED (F-022) |
| EXP-B conditional-vol | BLOCKED / unsupported on current panel |
| XS momentum, reversal, low-vol, VIX-panic, deep-dip, participation-breadth | REJECTED / INVALIDATED |
| JSE / estimator | ACADEMICALLY INTERESTING BUT OPERATIONALLY IMMATERIAL |
| Any book | FORWARD-VALIDATED / LIVE-CAPITAL CANDIDATE = **NONE** (0 fills) |

---

## 6. Unknowns & final judgment

**Top unknowns (priority):** (1) do real fills match the backtest — **wait, watch nightly**; (2) does any
book produce exposure-matched *forward* excess — the whole alpha question is unanswered forward; (3) does
`defensive_ensemble` diversify forward; (4) gold vs gem divergence once positions differ; (5)
`momentum_concentrated` on a repaired universe (vendor-blocked); (6) earnings PIT IC (0/300).

**Final judgment:**
1. **Discovered:** a rigorous method and one honest negative — in free-data US equities the only thing
   that survives blind + walk-forward + red-team is **vol/trend risk-management of the equity premium**
   (one source), plus one **portfolio wrap** (defensive_ensemble). The most valuable discovery is what
   does *not* work.
2. **Independent alpha? No.** One capped Level-3 source; cross-market refused.
3. **Diversified? No** (n_eff 2.8; crisis corr 0.765).
4. **Live-capital ready? No** (0 fills, one BLOCKED book, un-flattened residue, core edge = leverage).
5. **Watch next 20 days (operational only):** Monday fills land; the 271 foreign positions / AMAT flatten
   cleanly; slippage in-band (≤15 bps stock / ≤5 bps ETF); no silent flattening; benchmarks reconcile.
   **No alpha judgments.**
6. **Review at +3 months:** exposure behavior, gold-vs-gem divergence, sophistication vs naive controls.
7. **Single most valuable next evidence:** the first clean set of **real fills** with reconcile-measured
   slippage vs the frozen 10/2-bps execution model. Until then every performance number is a backtest,
   and the honest state is: excellent process, one credible portfolio object, no proven independent
   alpha, no forward evidence.

---

## Operational-transition marker — Monday 2026-07-13 (recorded 2026-07-11)

**Monday is an OPERATIONAL-TRANSITION day, not a performance day.** The dead stat-arb inventory flattens
at Monday's open. Pre-flatten baseline (read-only `get_account`/`get_all_positions`/`get_orders`,
2026-07-11, nothing written): equity **$100,794.31**, buying power **$112,436.94**, cash $125,542.99,
long_mv $62,540.43, short_mv −$87,289.11; foreign inventory **271 positions**, gross **$141,671.42**, net
**−$30,831.86**, 106 long / 165 short legs; **271 open flatten orders, 1,563 shares submitted, 0 filled.**

**Four-part flatten gate — verified at the first post-open reconciliation via independent read-only broker
queries compared against the persisted `_reconcile.jsonl`. Flatten is COMPLETE only if ALL four pass:**
1. **Position gate** — foreign position count = 0.
2. **Quantity gate** — remaining flatten quantity = 0.
3. **Terminal-order gate** — no nonzero position is associated only with filled/canceled/rejected/expired
   flatten orders.
4. **Independent-reconciliation gate** — a fresh broker snapshot agrees with the ledger on positions,
   signed exposure, and flatten quantities.

Code (`da5dc8e`) auto-enforces gates 1–2; gates 3–4 are checked by hand at report time (their automation
is intentionally **not** built before Monday, per freeze). "No open orders remain" is NOT sufficient.

**Any residual → compact exception table:** symbol · signed remaining qty · side · latest price · signed
market value · last flatten-order status · submitted/filled/remaining qty · asset status & tradability ·
probable cause · manual-intervention flag. **No replacement or corrective orders without explicit
authorization.**

**Clean forward performance attribution begins ONLY after all four gates pass AND the new paper-book
holdings reconcile to their aggregate target.** Until then, all performance interpretation stays suspended.

---

*Read-only review. No strategy, allocation, scheduler, frozen experiment, book, ledger, or manifest
deployment state was modified. Documentation-only reconciliations of stock-universe counts, foreign-position
decomposition, order-outcome split, and the CAPM-vs-exposure-matched alpha models are recorded above with
their primary sources.*
