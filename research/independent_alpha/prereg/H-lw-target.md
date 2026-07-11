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
