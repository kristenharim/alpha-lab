# Red-Team Audit — Final Report (Adjudicator, 2026-07-10)

**Process note.** The 10-agent + adjudicator workflow was killed mid-run by a monthly
spend limit (0/11 agents returned structured reports). However, 9 of 10 auditors had
already written their scratch analysis code and output CSVs to disk before dying. This
adjudication **re-ran that code directly** and reproduced the findings first-hand; where an
agent's driver was missing or buggy, the adjudicator wrote/fixed it (noted per finding).
This is therefore a genuine reproduction, not a paraphrase of unseen agent claims — but it
is narrower than the full charter (Agents 6/7/10 analyses only partially harvested; see
"Remaining audit work").

## 1. Scope & checksums
Frozen commit `78e1a36` (HEAD later moved — a sibling session committed; audit ran against
frozen content). Panels verified against SCOPE.md md5s: panel_2005 `dc14c2da…` (5413 rows,
2005-01-03→2026-07-10), train `232488b8…`, holdout `ab574ab3…`. Suite 152 passed / 1
skipped at freeze. Roster: 7 books. No production file, spec, manifest, ledger, scheduler,
or broker order was modified.

## 2. Executive verdict
**No CRITICAL finding. No confirmed bug in the shared engine, the accounting, or any of the
7 books' look-ahead behavior.** The platform's core evidence is trustworthy at the code and
accounting level. The material findings are one HIGH methodological weakness (the 7-book
roster is ~2–3 independent risk sleeves, not 7; measured "outperformance" vs *1× naive*
benchmarks is leverage, not skill), and two MEDIUM data/fidelity issues confined to the one
stock book and to backtest-vs-live rebalance timing. Forward trading evidence remains
**zero** (no fills yet); every forward-evidence score is floored accordingly.

## 3. Confirmed bugs
None (repo). Two bugs were found in the *audit agents' own scratch code* (Agent 1 path
`parents[2]`→`[3]`; Agent 8 replica groupby `KeyError(uint32 year,month)`), fixed by the
adjudicator to complete the checks; neither implicates the repo.

## 4. Confirmed methodological weaknesses

**F-RT-01 — Diversification of the 7-book roster is overstated; excess-vs-naive is leverage,
not alpha. [HIGH, CONFIRMED METHODOLOGICAL WEAKNESS]**
Component: portfolio construction / benchmark choice. Reproduced from Agent 9
(`beta_alpha_holdout.csv`, `corr_holdout.csv`, `factor_attrib_holdout.csv`) + Agent 5
(`stress_holdout.csv`).
- Book-return correlations (holdout year) cluster hard: vol_managed_qqq / vol_core_svxy /
  trend_vol_qqq pairwise **0.82–0.93**; dual_momentum_gem 0.87 with vol_core_svxy;
  momentum_concentrated 0.74–0.78 with that group. Only dual_momentum_gold stands apart
  (0.20–0.45, its gold loading). Effective independent sleeves ≈ **2–3**, not 7.
- Against the **exposure-matched** control (Agent 9 `ctrl` = QQQ/SPY at the book's own avg
  gross), holdout alpha is economically ~0 or negative: vol_managed_qqq excess **+0.3%/yr**
  (alpha_spy t=0.43, ns); vol_core_svxy **−16.7%/yr**, Sharpe −0.16 vs control (the SVXY
  sleeve was a net drag in the holdout); trend_vol_qqq **−5.5%/yr** (tail-hedge, confirms
  F-014). The **only** book beating its control on risk-adjusted terms is **defensive_ensemble**:
  Sharpe 2.29 vs 1.59, **+0.70** Sharpe, alpha_spy t=1.71, beta 0.92.
- The +9.5% "excess_vs_naive" in Agent 5 is vs **1× QQQ**; it collapses to +0.3% vs
  1.43×-exposure-matched QQQ. **The gap is leverage.**
Consequence: equal-capital 7-way allocation concentrates ~70% of portfolio risk in one
levered-US-tech-equity factor. Belief change: **confirms** prior labels (F-014/F-020/F-015)
quantitatively; **new** = vol_core_svxy's SVXY sleeve actively subtracted vs its control in
the holdout year → strengthens the case to watch it for demotion. Not a bug; not
invalidating. Remediation: report excess only vs exposure-matched controls (already logged
nightly); treat the roster as 2–3 sleeves in any future allocator. Does not require
rerunning trials.

**F-RT-02 — Effective independent trials ≈ 2.3, not 18. [MEDIUM, CONFIRMED METH. WEAKNESS]**
Agent 4 (`a4_dsr_audit.py`, reproduced): the 18 trials have mean pairwise corr **+0.60**;
eigenvalue-effective count **2.3**. Monte-Carlo E[max Sharpe | null, empirical cov, N=18] =
**0.49 ann**, *below* the repo's deflation threshold sr0 = 0.53 ann → the repo's DSR was
**conservative, not inflated**. Post-deflation, Newey-West(10)-adjusted: defensive_ensemble
**96.9%**, dual_momentum_gold 91.3%, trend_vol_qqq 91.0%, vol_core_svxy 85.2%,
vol_managed_qqq 83.2%, dual_momentum_gem 73.4%, momentum_concentrated 80.2%. Belief change:
none — corroborates the repo's own honest trial-count discipline. Scope limit: all on
overlapping windows / ≤11y history; DSR assumptions (iid-ish, Gaussian tails) only partially
met, so read as ordinal, not literal probabilities.

## 5. Plausible unresolved concerns

**F-RT-03 — momentum_concentrated stock universe: ~13% of members unpriceable per day.
[MEDIUM, PLAUSIBLE CONCERN]**
Agent 3 (`check_panel.py`, reproduced): mean **64 of ~503** member-days/day carry NaN close
(max 503 at panel start). Worst offenders are renamed/merged tickers the member-mask still
names under the old symbol — FB(→META), ANTM(→ELV), ABC(→COR), CTXS, PXD, WRK — plus
long-NaN names like BK/MMC/K. **Soft survivorship**: a name whose column is NaN can't be
ranked or held, so momentum_concentrated silently selects only from priceable members.
Bound: affects **only** momentum_concentrated (the other 6 books are ETF-only). Mitigant:
that book already has **no measured selection alpha** (rank IC ≈ 0, F-015/F-016), so the
defect contaminates no *believed* edge. Not testable to full precision without a
survivorship-complete price source (CRSP/Polygon). Belief change: lowers data-integrity
confidence for the stock book specifically; leaves ETF books untouched.

**F-RT-04 — Backtest-vs-live rebalance-timing drift on monthly books. [MEDIUM, PLAUSIBLE
CONCERN]**
Agent 1 truncation test (reproduced): truncating the panel at a month-end changes
dual_momentum_gem's pick (SPY↔QQQ↔EFA) and shifts momentum_concentrated tranche weights ~1–2%.
**Root cause is a guard, not leakage**: `dual_momentum_gem/spec.py:32` defines a month-end
as "a day whose successor is in a new month," so the panel's final row is deliberately never
treated as month-end. On the full backtest a completed month-end rebalances *on* that day;
the live runner (panel ends "today") defers until the next session confirms the boundary →
the live book rebalances **~1 trading day later** than the backtest. Direction is **safe**
(more conservative, no look-ahead — confirmed by F-RT-06). Impact: ≤1-day slippage on ~12
rebalances/yr, immaterial to returns, but means forward paper NAV will not tick-for-tick
match the frozen backtest. Disclose in the +3-month review; no fix required.

## 6. Issues RULED OUT (tested, not merely assumed)

**F-RT-05 — Engine / accounting bug. RULED OUT.** An independent engine with **zero
alpha-lab imports** (Agent 2 `indep_engine.weight_engine`, adjudicator wrote the driver)
reproduces `harness.run` net returns to **0.0000 bp max daily divergence on all 7 books**
(tolerance was 1 bp). Gross-cap violations: 0. Clean-room reimplementation-from-spec (Agent 8)
completed for vol_managed_qqq: net & weight abs-diff **0.0** every day of the holdout year.

**F-RT-06 — Forward look-ahead / data leakage. RULED OUT.** Future-poison test (Agent 1,
reproduced): scaling the **last 21 days of every close ×7** changes **zero** past weights on
**all 7 books** — the definitive test. Any spec consuming future data would move past
weights; none do. `held = W.shift(1)` in `harness.py` positions t uses info through t−1; the
two truncation flags (§F-RT-04) are the end-of-panel month-end guard, not leakage.

**Data calendar integrity. RULED OUT** (Agent 3): no duplicate dates, monotonic, no
weekends, no >5-day gaps, train/holdout non-overlapping, panel_2005 vs train identical on
overlap (max rel diff 0.0), ^VIX 0 NaN and in [9.1, 82.7]. One residual: the phantom
2026-05-25 all-NaN row persists in the **train/holdout** parquets (the fix reached only
panel_2005) — contributes ~0 to holdout P&L (all-NaN → 0 return); see §11 (relabel, LOW).

**Execution-cost sensitivity (vol family). RULED OUT as a fragility.** Agent 5
(`stress_holdout.csv`, reproduced): vol_managed_qqq total-net across base/half/2×/4× costs,
vol-stressed, 1–2 day delay, 50% partial, 10% missed = **[0.401, 0.423]** (base 0.408) — low
turnover (cost drag 0.16%/yr base) makes it near-invariant to execution assumptions.

## 7–8. Shared-engine & data findings
Shared engine: **clean** (F-RT-05/06). Shared data: **PIT mask correct, zero missing dead
names** (777/777 ever-members present), classic survivorship **bounded**; residual soft
survivorship (F-RT-03) is isolated to the stock book. No shared defect contaminates the ETF
books.

## 9. Strategy-by-strategy verdicts & confidence scorecard
Scores 0–100 per axis; **forward evidence floored at ≤5 for all (zero fills)** per charter.

| book | verdict | code | engine | data | stats | mechanism | exec-realism | robustness | forward | overall band |
|---|---|---|---|---|---|---|---|---|---|---|
| vol_managed_qqq | SURVIVES | 95 | 98 | 90 | 70 | 75 | 85 | 88 | 5 | 61–80 credible-for-paper |
| defensive_ensemble | SURVIVES | 95 | 98 | 90 | 80 | 80 | 80 | 82 | 5 | 61–80 (strongest) |
| trend_vol_qqq | SURVIVES (tail-hedge) | 95 | 98 | 90 | 72 | 70 | 85 | 85 | 5 | 61–80 |
| vol_core_svxy | PROVISIONAL | 95 | 98 | 88 | 68 | 55 | 78 | 70 | 5 | 41–60 (SVXY drag + tail) |
| dual_momentum_gold | PROVISIONAL | 92 | 98 | 88 | 74 | 45 | 82 | 68 | 5 | 41–60 (gold hindsight F-020) |
| dual_momentum_gem | PROVISIONAL | 92 | 98 | 88 | 62 | 55 | 82 | 70 | 5 | 41–60 |
| momentum_concentrated | BLOCKED | 92 | 98 | 55 | 60 | 35 | 75 | 60 | 5 | 21–40 (no alpha + NaN universe) |

Rationale: no book is INVALIDATED (no defect explains a *believed* edge). SURVIVES = every
material testable failure mode investigated, none invalidating, limits bounded.
momentum_concentrated is **BLOCKED**: F-RT-03 data-integrity + no measured selection alpha
means its watch-tier paper allocation buys little information until a survivorship-complete
universe exists.

## 10. Clean-room replication
vol_managed_qqq: **identical** (abs-diff 0.0, 252/252 days). Other 6: **NOT TESTABLE** from
this run (Agent 8's multi-book driver crashed on its own groupby bug). Partially covered by
F-RT-05 (independent engine, all 7) + F-RT-06 (leakage, all 7). Full clean-room of the other
6 is the top item of remaining work.

## 11. Results to rerun / relabel
- **Relabel (LOW):** note the phantom 2026-05-25 row in train/holdout parquets; holdout-year
  results are materially unaffected (~0 contribution) but the parquets should be regenerated
  with the panel_2005 fix for consistency at the next legitimate data refresh (not now —
  frozen).
- **No rerun required:** all headline results reproduce exactly; the JSE reconciliation
  (prior F-021) already closed.

## 12. Production-gate status
**Before continued paper interpretation** (charter §10): CRITICAL engine/reconciliation bugs
— **none** ✓; clean account-vs-manifest reconcile — pending first fills (harness exists,
0 fills) ⧗; stable nightly pipeline ✓; complete strategy+benchmark logging ✓; cancel/reject/
partial handling — instrumented, unexercised ⧗; target-weight reproduction — ✓ (F-RT-05/06);
no unexplained clean-room diffs > tol — ✓ for vol_managed_qqq, ⧗ for 6. **Gate status:
PASS on code/accounting; PENDING on fill-based items until Monday's fills land.**
**Before live capital:** not met (zero forward evidence, momentum_concentrated BLOCKED,
6-book clean-room incomplete) — as expected this early.

## 13. Remaining unknowns
Real slippage/fills (Monday+); whether vol_core_svxy's holdout drag vs control persists;
6-book clean-room; survivorship-complete stock universe for momentum_concentrated; and the
only thing that ultimately settles it — forward paper NAV vs exposure-matched controls.

## 14. Recommended NEXT AUDIT (not an alpha experiment)
**Re-run the full 10-agent red-team with a spend budget** to complete Agents 6/7/10
(perturbation, regime-concentration, adversarial-implementation) and the 6-book clean-room,
THEN the first **fill-based execution reconciliation** after ~20 trading days (the
`hunt_paper_reconcile.py` harness is already wired) — that audit converts the ⧗ gate items to
✓/✗. No new strategy work until it runs.
