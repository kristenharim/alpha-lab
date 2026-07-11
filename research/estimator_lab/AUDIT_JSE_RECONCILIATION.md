# AUDIT — JSE/PCA result reconciliation (forensic, 2026-07-10)

Charge: reconcile the three conflicting F-021 narratives — (1) original n=252 run
"long-only economically zero", (2) n=63 rerun "sign flip", (3) crossover sweep
"long-only helps at every n incl. 252" — and find the first line where they diverge.
No new hypotheses, no tuning. Re-runs done in `audit/` (frozen scripts untouched;
audit copies differ only in the panel path and, for the crossover copy, WINDOWS=(252,)).

## Verdict: (a) REPORTING DRIFT — the pipelines agree to machine precision

There is no method difference and no bug. Every pipeline, re-run on the current panel,
produces the **identical** monthly delta series (max month-level difference 2.7e-16).
The conflict lives entirely in prose:

1. **RESULTS.md's own table always showed the long-only effect as significant.**
   RESULTS.md line 50 (committed at 32f71c6): `long_only k=3: −0.6 bps, t=−8.2, p<0.001`.
   The paired t WAS computed (run_minvar.py:126, `stats.ttest_rel`) and WAS reported.
   The narrative two paragraphs later (RESULTS.md line 59: "statistically significant at
   k=3,5 but economically zero (< 1 bp)") and the F-021 entry (FAILURES.md line 221-222:
   "long-only the gap is ~0") rounded a small-but-real negative into "zero". That
   rounding is the first divergence.
2. **The n=63 "sign flip" narrative (5562106) was wrong.** n=252 long-only was already
   negative and significant; n=63 only made it 4x larger (−0.5 → −2.0 bps). No sign
   flipped in long-only, ever. (Unconstrained is positive/harmful at every n — also no flip.)
3. **The month-set "discrepancy" (137 vs 138, 2015-02 vs 2015-01) is two labeling
   conventions plus one real tail month.** The original run's rebalance dates were
   2015-01-02 → 2026-05-01 (137 rebalances; verified from `git show
   32f71c6:research/estimator_lab/results.csv`). RESULTS.md line 3 described them by
   **hold-end month** (first hold ends 2015-02-02, last ends 2026-06-01 → "2015-02 →
   2026-06"). CROSSOVER.md line 3 describes the same construction by **rebalance date**
   ("2015-01 → 2026-06"). The head never differed. The one real difference is a new
   2026-06-01 rebalance at the tail, added by the panel regeneration (below).

### First divergence, named

| divergence | where | nature |
|---|---|---|
| "economically zero" vs −0.6 bps t=−8.2 in the same file | `research/estimator_lab/RESULTS.md` line 59 (vs its own table, line 50); echoed in `research/hunt2026/FAILURES.md` F-021 lines 221-222 | prose rounding, not code |
| "sign flip at n=63" | 5562106 commit message + FAILURES.md "F-021 RESOLVED" entry line 236 ("the n=252 long-only null (~0) was a regime artifact") | prose; the n=252 value was never null |
| 137/2015-02 vs 138/2015-01 | `RESULTS.md` line 3 (hold-end labeling) vs `CROSSOVER.md` line 3 (rebalance-date labeling) | labeling convention + 1 tail month from panel regeneration |

**Code divergence: none.** `run_crossover.py:14` imports `EXCLUDE, PANEL, START,
minvar_weights` from `run_minvar.py`, and `run_crossover.py:81-83` asserts its
single-SVD estimators equal `estimators.py`'s `pca3`/`jse3` at 1e-12. Month-set
construction is line-for-line identical (`run_minvar.py:62-81` vs `run_crossover.py:58-77`;
both gate on ≥252d history at n=252, hold >10 days, ≥100 eligible names). Same cap
(5%, clip-then-renormalize, `minvar_weights`), same realized-vol formula
(`std(ddof=1)·√252` on daily hold returns), same delisting handling (hold NaN → 0),
same paired test (`ttest_rel` on the two vol columns).

## Protocol item 1 — the three runs, reconstructed

| | run 1 (original n=252) | run 2 (n=63) | run 3 (crossover) |
|---|---|---|---|
| commit | 32f71c6 (2026-07-10 21:57:48) | 5562106 (22:23:26) | eb121f8 (22:58:17; narrated d4512ef) |
| script | run_minvar.py, WINDOW=252 | run_minvar.py, EL_WINDOW=63 | run_crossover.py, n∈{42..252}, k=3 |
| panel | **pre-regeneration** panel_2005.parquet (superseded; gitignored, not recoverable) | current panel | current panel |
| panel id | n/a (old) | md5 dc14c2daaff9160fb1cd1de3aca399d3, mtime 2026-07-10 21:57:10 | same |
| rebalance months | 137: 2015-01-02, 2015-02-02, 2015-03-02 … 2026-03-02, 2026-04-01, 2026-05-01 | 138: same head … 2026-04-01, 2026-05-01, 2026-06-01 | 138, identical set to run 2 (index-equal) |
| universe | PIT member>0, window-complete returns, ≥100 names, 37-ticker ETF EXCLUDE | same | same (imported) |
| missing data | hold NaN → 0 (delist = cash-out) | same | same |
| cap | ±5% clip then renormalize (single pass) | same | same (same function) |
| books | unconstrained + long-only | same | same |
| realized vol | std(ddof=1)·√252 of daily hold returns | same | same |
| paired test | ttest_rel(jse_k, pca_k) per book — run AND reported | same | same |

The panel regeneration between run 1 and run 2 (mtime 21:57:10; phantom all-NaN
2026-05-25 row dropped, panel extended) is the ONLY data difference. Its effect,
measured month-by-month: **136 of 137 overlapping months identical to machine
precision; only 2026-05-01 changed** (the month whose hold contained the phantom row;
long-only vols moved ≤0.42 vol-bps, unconstrained ≤0.79), **plus one new tail month
2026-06-01**. That moved the long-only k=3 headline from −0.56 bps t=−8.21 (137m) to
−0.53 bps t=−7.39 (138m). No sign, ranking, or significance changed.

## Protocol item 2 — the actual n=252 long-only delta series, both pipelines

Both pipelines re-run in `audit/` on the current panel (2026-07-10):

- run_minvar path vs crossover path: **same 138 months (index-equal), max per-month
  |difference| = 2.7e-16** — identical series, not offset, not rescaled.
- fresh run_minvar vs committed `results.csv` (4b35553): max diff **0.0** (byte-reproducible).
- fresh crossover vs committed `crossover.csv`: max diff **0.0**.
- committed 32f71c6 `results.csv` vs current: differs only as described above
  (2026-05-01 + tail month) — consistent with old-panel provenance, not with any code change.
- n=63 check: run_minvar w63 path vs crossover n=63 — same 138 months, max diff 1.2e-16.

## Protocol items 4–5 — corrected numbers (current panel, 138 months, k=3, paired t)

| n | book | Δ (jse3 − pca3, ann. vol bps) | t | p |
|---|---|---|---|---|
| 252 | long-only | **−0.53** | −7.39 | 1.3e-11 |
| 252 | unconstrained | +18.4 | +9.69 | 3.1e-17 |
| 63 | long-only | **−1.98** | −5.99 | 1.7e-08 |
| 63 | unconstrained | +36.9 | +8.09 | 2.8e-13 |

(Original 137-month/old-panel n=252 long-only for the record: −0.56, t=−8.21.)

**The crossover sweep's conclusion STANDS**: no crossover, long-only JSE helps at every
n with monotone decay (−2.6 → −0.5 bps), unconstrained hurts at every n. It does not
need re-running — its endpoints are byte-reproducible and equal to the standalone runs
on the same panel. The scientific/operational/paper split in the Director's provisional
note survives unchanged: directionally real long-only, below deployment materiality,
constraint-dependent sign + p/n monotonicity is the publishable shape.

## Housekeeping

- `audit/` contains the scratch copies + fresh outputs (frozen scripts untouched).
- RESULTS.md/CROSSOVER.md left as-is (historical record); this file + the F-021
  amendment are the corrections of record.
- Recommendation: RESULTS.md-style headers should state rebalance-date ranges, not
  hold-end months — that single labeling choice caused the entire "month-set
  discrepancy" scare.
