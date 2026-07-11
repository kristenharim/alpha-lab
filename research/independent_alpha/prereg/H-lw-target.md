# PREREG H-lw-target — Ledoit-Wolf constant-correlation vs identity shrinkage target

*Frozen 2026-07-10 (Agent 5, Experiment Engineer). Format extends
`research/hunt2026/PREREGISTRATION.md`. Nothing above the Result line may be edited
after the first scoring run.*

- **Experiment ID:** EXP-2026-07-10-lw-cc-target
- **Hypothesis ID:** H-lw-target
- **Ranked:** EXPERIMENT_QUEUE.md #3 (high) · closes the exact "blunt target" open item
  flagged in `research/estimator_lab/RESULTS.md`

**Hypothesis** (one falsifiable sentence, mechanism included): The current LW estimator
(`sklearn.covariance.ledoit_wolf`, `estimators.py:49`) shrinks toward a **scaled identity**,
which discards the strong common-correlation structure of S&P 500 names; shrinking instead
toward the **constant-correlation target** (Ledoit-Wolf 2004: keep sample variances, replace
the correlation matrix with its off-diagonal mean) is a less-biased target and lowers realized
min-var portfolio volatility.

**Layer touched** (exactly one): **B — estimator** (shrinkage target only; the min-var
optimizer, universe, windows, and holds are unchanged). Registered baseline: the **`lw` row**
in `estimator_lab/RESULTS.md` — unconstrained mean vol **11.64%**, net Sharpe 0.35, turnover
3.23; long-only **13.70%**, Sharpe 0.73. Reigning champion to beat: **`mp`** (11.27%
unconstrained).

**Alpha type tag:** estimator. A win is a **better covariance estimate, not a market forecast** —
it improves the risk model, not the return signal.

**Control:** `lw_cov` as shipped — `ledoit_wolf(R − R.mean())`, identity target.

**Treatment:** `lw_cc` — Ledoit-Wolf shrinkage with the **constant-correlation target** F
(F_ii = s_ii; F_ij = r̄·√(s_ii·s_jj), r̄ = mean sample pairwise correlation), shrinkage
intensity δ* from the LW-2004 closed form (π, ρ, γ). Un-tuned: δ* is the analytic optimum, not
a swept parameter. ONE layer changed: the target of an existing shrinkage estimator.

**Universe:** PIT S&P 500 members, 369–487 eligible names/month, exactly the estimator_lab
design (`run_minvar.py` on `panel_2005` PIT members), trailing **252d** windows, one-month
holds, `|w| ≤ 5%` cap, both books (unconstrained sum-w=1 and long-only).

**Sample / train / eval (non-overlapping, holdout fixed BEFORE running):**
- Full grid: **137 months, 2015-02 → 2026-06** (the estimator_lab span).
- Parameter-free (analytic δ*, no fit), so the primary paired-t runs on all 137 months. **Blind
  sign-stability holdout:** last **24 months (2024-07 → 2026-06)** — the CC−identity vol delta
  must not flip sign there. Inspect only on 2015-02 → 2024-06 before running the holdout months.

**Forecast + execution timestamps:** weights set at **close d** from the trailing 252d window;
returns earned **d+1 … next month-end** (the harness convention: day d excluded from the OOS
hold, per RESULTS.md "Holding-window alignment"). No live order — offline estimator grid.

**Expected effect size:** CC target lowers **unconstrained** mean realized vol vs identity LW by
**~10–40 bps** (its live regime, where LW already sits mid-pack at 11.64%). Prior it still
**loses to MP** (11.27%) — MP clipping is the incumbent champion. Long-only expected ≈ inert
(all estimators compress to 11.7–14.2% there). Honest prior P(beats identity) ≈ 0.55;
P(beats MP) ≈ 0.2.

**Primary statistic:** mean realized annualized portfolio vol (unconstrained book) and the
**paired t-stat of monthly realized vol, lw_cc − lw_identity**. **Secondary:** net Sharpe,
mean turnover, the same paired-t long-only, and lw_cc − mp (does it dethrone the champion?).

**Success condition:** lw_cc reduces unconstrained mean realized vol vs lw_identity with paired
t < −2, sign stable in the 2024-07→2026-06 holdout → the "blunt target" item is answered
**yes, target matters**; record on the CONFIDENCE ladder as an estimator improvement (note
whether it also beats MP).

**Failure / kill condition** (decidable, includes stop-iterating rule): |paired t| < 2 (no
significant vol reduction vs identity) → **kill and close the docket item**: LW's target choice
is inert on this n=252 / strong-factor design (consistent with F-021's diagnosis that the
dispersion these corrections target is nearly absent at n=252). Do **not** try further LW target
variants on this window; the reopen regime is small-n (n≈63), already docketed separately.

**Cost model:** turnover is emitted per estimator (RESULTS.md column); net Sharpe already nets a
per-unit-turnover cost in the existing harness. LW-identity turnover is 3.23 (high) — if lw_cc
lowers vol **and** turnover, that is a double win; if it lowers vol but raises turnover, the net
Sharpe column adjudicates. No new cost assumptions introduced.

**Leakage checks:** δ*, r̄, and F are computed **inside** each trailing 252d window; the hold is
the next month, disjoint from the fit window (day d excluded). No forward data enters the
estimate.

**Survivorship checks:** PIT membership (369–487/month, no lookahead index); identical eligible
set to the shipped estimator grid, so the CC vs identity comparison is matched name-for-name each
month. Delisted names retained where `panel_2005` has their history.

**Runtime estimate:** ~20 s single-core (adds one estimator to the existing 9×2×137 grid).
**Complexity score:** 1/5 (~15-line `lw_cc` function in `estimators.py` + one `ESTIMATORS` entry
+ re-run `run_minvar.py`).

**Information-gain estimate:** MODERATE — a clean docket-closer either way; retires the exact open
item RESULTS.md flagged. Low novelty, high tidiness.

**Trial count:** adds **TRIAL_LEDGER.md #21** (estimator; tag = estimator research) in the same
commit. Adaptive-loop flag: derived from the estimator_lab OOS record (F-021, RESULTS.md) ⇒
**yes, adaptive** — note in the hunt-level ledger.

**Derived from prior holdout results?** Yes — RESULTS.md's LW/MP grid and its "blunt target" note.
Sanctioned docket item, not fishing.

---
**Result** (filled after the run, never edited above this line):

**Run:** 2026-07-11, `research/independent_alpha/experiments/run_lw_cc.py` (standalone; imports
the shipped `estimator_lab` harness read-only, adds `lw_cc`, runs {lw, mp, lw_cc} on the exact
grid). Outputs: `experiments/lw_cc_results.csv`, `experiments/lw_cc_diag.csv`. Runtime ~8 s.
Grid actually produced **138 months** (2015-01 → 2026-06) — the shipped `results.csv` yields the
same 138; the "137 / 2015-02" in RESULTS.md is a prose rounding, not a spec mismatch.

**VERDICT: KILL.** The pre-registered success condition (unconstrained vol *reduction* vs
identity, paired t < −2, holdout sign-stable) is failed on every clause — and failed in the
*adverse* direction. Docket item "does the LW target matter here" is answered: **for the primary
(unconstrained) book, shrinking to the constant-correlation target makes realized vol
significantly WORSE, not better.** No more LW-target variants on this n=252 window.

**PRIMARY (unconstrained, sum w=1, |w|≤5%), lw_cc − lw_identity, monthly realized ann. vol:**
- mean vol: **lw_cc 12.494% vs lw_identity 11.621%** → **+0.873 vol%pts (+87.3 bps), i.e. vol INCREASED.**
- paired **t = +3.688, p = 3.3e-4** (n=138). A *significant increase*, opposite the hypothesized decrease.
- **Holdout 2024-07 → 2026-06 (n=24): lw_cc − lw = −0.111 vol%pts → sign FLIPPED** vs the full-sample
  +0.873. So even the direction is unstable; the pre-registered holdout stability requirement also fails.

Success requires a reduction with t < −2 AND holdout-stable sign — none of the three hold. The
literal kill trigger as written (|paired t| < 2, "inert") does *not* fit either: |t| = 3.69 > 2. The
effect is significant but adverse, which is a *stronger* fail than inertness — the stop-iterating
rationale (LW's target choice does not lower unconstrained vol on this n=252 / strong-factor design,
consistent with F-021) applies a fortiori. Verdict is KILL / close the docket, reached via
"significant adverse primary + holdout flip," not via the |t|<2 clause. Stated so it is not misread.

**SECONDARY (does not change the frozen verdict, which keys on the unconstrained book):**

| book | metric | lw_cc | lw (identity) | mp (champ) |
|---|---|---|---|---|
| unconstrained | mean vol | 12.494% | 11.621% | 11.252% |
| unconstrained | net Sharpe | 0.301 | 0.343 | 0.685 |
| unconstrained | turnover | 3.157 | 3.222 | 1.093 |
| long_only | mean vol | **12.645%** | 13.676% | 13.111% |
| long_only | net Sharpe | 0.733 | 0.735 | 0.758 |
| long_only | turnover | 0.397 | 0.447 | 0.279 |

- **lw_cc − mp (unconstrained):** +1.242 vol%pts, t = +4.633, p = 8.3e-6 — lw_cc does NOT dethrone MP; it is
  worse than both incumbents unconstrained.
- **Long-only, lw_cc − lw_identity:** −1.031 vol%pts (−103 bps), **t = −12.5, p = 1.6e-24, holdout sign
  STABLE** (−0.884 vol%pts in 2024-07→2026-06). **lw_cc − mp (long-only):** −0.466 vol%pts, t = −6.64,
  p = 6.9e-10. So the constant-correlation target IS a real, large, stable improvement — but only in the
  *long-only* book, which was not the pre-registered primary and where lw_cc (12.645%) still trails the
  PCA/JSE leaders (~11.7% in RESULTS.md). It lowers vol AND turnover vs lw there (a double win), yet net
  Sharpe is flat (0.735 → 0.733). This is a genuine but off-primary finding; it does not rescue the frozen
  unconstrained verdict.

**Mechanism read:** the CC target imposes a single common correlation r̄ across ~450 names. In the
long-only book (weights pinned ≥0, cap-bound) that shared-correlation shrinkage stabilizes the tiny
active set and helps. In the unconstrained book, min-var exploits fine cross-sectional correlation
differences to build offsetting long/short pairs; flattening every pair-correlation to r̄ destroys exactly
that structure, so realized vol rises. Same estimator, opposite sign by book — and the pre-registered
primary is the book where it loses.

**Sanity / bug-checks (unusually clean result treated as suspect until ruled out — here the result is a
LOSS, but checked anyway):**
1. **Harness faithful:** my `lw` and `mp` per-month vols reproduce the shipped `results.csv` to
   **max|diff| = 0.0** across all 138 months, both books → the walk-forward replication is exact,
   name-for-name matched.
2. **δ\* ∈ [0,1]:** analytic LW-2004 shrinkage δ\* ranged **[0.128, 0.786]**, mean 0.243 — strictly interior,
   never clipped on real windows (`lw_cc_diag.csv`). Not swept.
3. **Target PSD:** min eigenvalue of F was **≥ 2.8e-5 > 0 every month** → constant-correlation target PSD
   throughout. r̄ ∈ [0.129, 0.567], mean 0.312 (economically sane average S&P pairwise correlation).
4. **Closed form re-derived a second way:** δ\* and the full Σ from `lw_cc_cov` match an independent
   brute-force double-loop computation of (π, ρ, γ) to **max|diff| = 0.0** on synthetic factor data →
   no vectorization error in the ρ / θ machinery.
5. **No leakage / no too-good cell:** δ\*, r̄, F all computed inside the trailing 252d window; hold is the
   disjoint next month (day d excluded). No estimator posts implausibly low vol; the primary result is a
   significant *increase*, so no over-optimistic cell to explain.

**Trial-ledger line (for the coordinator to append centrally — not edited here):** TRIAL_LEDGER.md #21 ·
EXP-2026-07-10-lw-cc-target · estimator · KILL · unconstrained lw_cc−lw_identity = +87.3 bps, t=+3.69,
holdout sign flipped → CC target significantly worse unconstrained; close LW-target docket (adaptive, from
estimator_lab OOS record). Off-primary: large stable long-only win (−103 bps vs identity, t=−12.5) noted,
does not change verdict.
