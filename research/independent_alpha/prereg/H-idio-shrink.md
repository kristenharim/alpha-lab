# PREREG H-idio-shrink — idiosyncratic-variance (residual-diagonal) shrinkage in PCA/JSE min-var

*Frozen 2026-07-10 (Agent 5, Experiment Engineer). Format extends
`research/hunt2026/PREREGISTRATION.md`. Nothing above the Result line may be edited
after the first scoring run.*

- **Experiment ID:** EXP-2026-07-10-idio-diag-shrink
- **Hypothesis ID:** H-idio-shrink
- **Ranked:** EXPERIMENT_QUEUE.md #4 (high) · the **only untested min-var lever** — the
  residual diagonal D — mechanistically orthogonal to every mapped estimator

**Hypothesis** (one falsifiable sentence, mechanism included): The factor-model covariance
`Σ = V·diag(λ)·Vᵀ + diag(D)` (`estimators.py:_pca_parts`) uses the **raw per-name residual
variances** for D; these are noisily estimated (one variance per name from n=252 residuals),
and **shrinking D toward its cross-sectional mean** — the one component untouched by JSE
(eigenvectors), MP/LW (spectrum), or EWMA (recency) — lowers realized min-var volatility because
the optimizer over-weights names whose idiosyncratic variance is underestimated by noise.

**Layer touched** (exactly one): **B — estimator** (the residual diagonal D only; eigenvectors
V, eigenvalues λ, universe, windows, holds unchanged). Registered baseline: **`pca3`** (best
unconstrained factor book, mean vol 13.09%, Sharpe 0.80 in RESULTS.md) and **`jse3`** (13.27%),
run with un-shrunk D.

**Alpha type tag:** estimator (risk-model improvement, not a market forecast).

**Control:** `pca_cov(R, 3)` and `pca_cov(R, 3, jse=True)` as shipped — `D = max(resid²/n,
1e-8)` per name (`_pca_parts` line 24).

**Treatment:** the same estimators with **D shrunk toward its cross-sectional mean**:
`D_shrink = α·mean(D) + (1−α)·D`, applied inside `pca_cov` before `diag(D)`. **Pre-registered α
grid = {0.25, 0.50, 0.75}, reported in full — no peeking-then-picking.** The economic call is
made on α=0.50 (the registered primary); the other two are robustness only and their existence is
declared here precisely so a post-hoc "best α" cannot be smuggled in. ONE layer changed: the
diagonal.

**Universe:** PIT S&P 500 members (369–487/month), trailing 252d windows, one-month holds, |w|≤5%,
both books — identical to the estimator_lab grid (`run_minvar.py` on `panel_2005` PIT members).

**Sample / train / eval (non-overlapping, holdout fixed BEFORE running):**
- Full grid: **137 months, 2015-02 → 2026-06**.
- α is **pre-registered, not fit**, so the primary paired-t (α=0.50 vs un-shrunk) runs on all 137
  months. **Blind sign-stability holdout:** last **24 months (2024-07 → 2026-06)** — the α=0.50
  vol delta sign must not flip. The reported {0.25,0.75} arms exist only to show monotonicity;
  they do not select α. Inspect only on 2015-02 → 2024-06 first.

**Forecast + execution timestamps:** weights at **close d** from the trailing 252d window; returns
earned **d+1 … next month-end** (day d excluded — RESULTS.md holding-window alignment). Offline
estimator grid, no live order.

**Expected effect size:** shrinking D lowers **unconstrained** pca3 mean realized vol by
**~5–25 bps**. Prior it does NOT dethrone MP (11.27%). Long-only expected ≈ inert (differences
compress there, RESULTS.md). Honest prior P(α=0.50 beats un-shrunk, unconstrained) ≈ 0.5 — the
diagonal may already be adequately estimated at n=252/p≈450, the same regime that made JSE inert
(F-021).

**Primary statistic:** mean realized annualized portfolio vol (unconstrained pca3) and the
**paired t-stat of monthly realized vol, D_shrink(α=0.50) − D_raw**. **Secondary:** the same for
jse3; net Sharpe; the {0.25,0.75} arms (monotone in α?); long-only paired-t; and D_shrink − mp.

**Success condition:** α=0.50 reduces unconstrained pca3 mean realized vol vs un-shrunk with
paired t < −2, sign stable in the 2024-07→2026-06 holdout, and the {0.25→0.75} arms trend
monotonically (a coherent lever, not a fluke cell) → record the residual-diagonal shrink as a
real estimator improvement; note whether it closes the gap to MP.

**Failure / kill condition** (decidable, includes stop-iterating rule): |paired t| < 2 at α=0.50
**and** no monotone trend across {0.25,0.75} → **kill.** The residual diagonal is already
well-estimated at n=252; **the last untested min-var lever is closed** — do not run further
diagonal-shrinkage variants on this window (the reopen, like the rest, is the small-n regime,
docketed separately via the n=63 crossover work).

**Cost model:** turnover emitted per estimator; net Sharpe nets the per-unit-turnover cost in the
existing harness. Diagonal shrinkage should barely move turnover (it perturbs weights, not the
rebalance cadence) — confirm turnover delta is small, else the vol win is bought with churn.

**Leakage checks:** D and mean(D) are computed **inside** the trailing 252d window; the hold is
the disjoint next month. α is a fixed constant, not fit to any period. No forward data.

**Survivorship checks:** PIT membership, matched name-for-name each month against the un-shrunk
control (same eligible set, only D differs). Delisted names retained where `panel_2005` has
history.

**Runtime estimate:** ~25 s single-core (adds 3 α-variants × 2 estimators to the grid, ~20s base
per RESULTS.md). **Complexity score:** 1/5 (~10-line change: shrink D inside `pca_cov`, add a
shrink-α kwarg + `ESTIMATORS` entries; re-run `run_minvar.py`).

**Information-gain estimate:** HIGH — the only mechanistically-untested min-var lever; a kill
retires the last open estimator degree of freedom, a hit is a genuine risk-model gain orthogonal
to everything mapped.

**Trial count:** adds **TRIAL_LEDGER.md #22** (estimator; tag = estimator research) in the same
commit. Adaptive-loop flag: derived from the estimator_lab OOS record (F-021, CROSSOVER) ⇒
**yes, adaptive** — note in the hunt-level ledger.

**Derived from prior holdout results?** Yes — the estimator_lab grid and JSE_BOUNDARY_MAP.
Sanctioned lever, not fishing.

---
**Result** (filled after the run, never edited above this line):
