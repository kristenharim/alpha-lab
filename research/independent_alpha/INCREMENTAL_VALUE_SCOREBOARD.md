# INCREMENTAL_VALUE_SCOREBOARD.md — does each watch-tier book add value beyond the frozen ensemble?

**Agent 9, independent-alpha program. Real computation, 2026-07-10.**
Script: `research/independent_alpha/independence/compute_incremental.py` (run with `.venv/bin/python`).
Outputs: `independence/incremental_metrics.csv`, `independence/bootstrap.csv`.
Reuses Agent 7's return-series reconstruction (`independence/compute_independence.py`:
`book_returns` / `factor_returns`). Paper-only; nothing here touches live specs.

---

## Question

Control = the **frozen ensemble of the 4 promoted books** (vol_managed_qqq, vol_core_svxy,
trend_vol_qqq, defensive_ensemble). For each watch-tier candidate
(dual_momentum_gold, dual_momentum_gem, momentum_concentrated), does
**control + candidate** beat **control** on a pre-registered, leverage-neutral basis?

## Method (pre-registered, no retrospective allocation optimization)

- Daily net series per book from the exact runner path (`compute_book` → `_heal_etfs` →
  `harness.run`) on `panel_2005.parquet`, costs 2/10 bps. Window **2005-01-03 → 2026-07-10, n = 5,413**.
- **Two fixed weighting designs**, both applied identically to control and treatment:
  - **equal-capital** — simple mean of member series.
  - **equal-risk** — inverse-vol weights (1/σ, full-sample, a fixed rule, not tuned).
- **Primary method**: circular block-bootstrap (L=21d ≈ 1 month, 4,000 reps) of the
  **difference in net Sharpe**, with treatment **re-scaled to control's vol each replicate**
  so the test is *skill, not leverage*. Report **P(ΔSharpe > 0)** and 95% CI.
- Secondary: return at equal vol, max-DD, worst-12m, turnover, factor-adjusted alpha
  (on 1+SPY+QQQ), sub-period ΔSharpe (halves + thirds), and residual distinctness
  (candidate regressed on control → marginal residual alpha + corr).
- **Level-4 gate** (all must hold): ΔSharpe > 0 under the primary bootstrap with
  P(ΔSharpe>0) meaningfully above 0.5 and a CI clear of 0; increment **not concentrated in
  one period**; survives realistic costs (series already net); **not merely added
  beta/leverage** (must survive the equal-vol Sharpe test + carry positive marginal residual
  alpha vs control); **still distinct after residualization**.
- Self-check: adding a duplicate of an existing member returns ΔSharpe ≈ 0 (got −0.009). ✔

## Control (frozen 4-book ensemble)

| design | Sharpe | CAGR | ann vol | max DD | worst-12m | factor-α (ann) | α t-stat |
|---|---|---|---|---|---|---|---|
| equal-capital | 0.99 | 20.4% | 21.0% | −30.6% | −26.2% | 7.0% | 2.82 |
| equal-risk | 1.00 | 19.4% | 19.8% | −26.9% | −22.8% | 7.0% | 2.87 |

The control already carries a real, significant factor-adjusted alpha (t ≈ 2.8) — it is a
strong benchmark to beat. That is the point: the question is *marginal*, not standalone.

## Scoreboard — incremental effect of each candidate

Primary numbers are the **equal-risk** design (equal-capital in brackets where it differs).

| candidate | ΔSharpe | **P(ΔSharpe>0)** | boot 95% CI | Δret @ equal vol | resid-α vs ctrl (t) | corr to ctrl | Level-4? |
|---|---|---|---|---|---|---|---|
| dual_momentum_gold | **+0.003** [+0.007] | **0.53** [0.56] | [−0.07, +0.08] | +0.06% [+0.18%] | +2.3%/yr (t=0.5) | 0.60 | **NO** |
| dual_momentum_gem | **−0.010** [−0.011] | **0.36** [0.37] | [−0.06, +0.05] | −0.25% [−0.27%] | +0.0%/yr (t=0.0) | 0.75 | **NO** |
| momentum_concentrated | **−0.057** [−0.037] | **0.07** [0.09] | [−0.13, +0.02] | −1.33% [−0.94%] | −2.8%/yr (t=−1.0) | 0.59 | **NO** |

### Read-out

- **dual_momentum_gold** — the *least bad* addition, and still non-incremental. ΔSharpe is a
  rounding error (+0.003 / +0.007) and the bootstrap is a coin flip (**P = 0.53**), CI
  straddles 0. Its marginal residual alpha vs the control (+2.3%/yr) is **not significant**
  (t = 0.5). Sub-period ΔSharpe is unstable — thirds run [+0.011, **−0.056**, +0.043]: whatever
  tiny edge exists lives in one third and reverses in the middle. **Concentrated, not
  significant → fails the gate.**
- **dual_momentum_gem** — ΔSharpe negative, P = 0.36, marginal residual alpha exactly 0.0
  (t = 0.0) at **corr 0.75** to the control. It is the most redundant of the three: it adds
  nothing the frozen ensemble does not already span. **Fails.**
- **momentum_concentrated** — **actively harmful.** ΔSharpe −0.057, **P = 0.07** (i.e. ~93%
  chance it *lowers* Sharpe), negative marginal residual alpha (−2.8%/yr, t = −1.0), and the
  damage is worst in the recent half (ΔSharpe H2 = −0.10, thirds [0.00, −0.096, −0.076]).
  This is the dead cross-sectional-momentum book (F-015/16, 0/10 rank IC) dragging the
  portfolio. **Fails hardest.**

### On the "improved max-DD" mirage

Raw (un-re-levered) treatment max-DD looks *better* for every candidate (e.g. gold −24% vs
control −27%, ΔmaxDD +0.026 to +0.055). This is **pure dilution, not skill**: the candidate
books carry lower vol, so mixing them de-risks the book. The effect vanishes once you re-lever
to equal vol — which is exactly why the Sharpe/equal-vol test (scale-free) shows no gain.
Reporting the DD improvement as "value added" would be the classic *added-beta/leverage*
trap the gate is built to catch. Turnover barely moves (Δ ≈ −0.004, candidates are low-turnover).

## Verdict

**None of the three watch-tier books reaches Level 4.** No candidate is incrementally positive
under the pre-registered primary method:

| candidate | outcome | ladder |
|---|---|---|
| dual_momentum_gold | non-incremental (ΔSharpe ≈ 0, P ≈ 0.53, insignificant residual-α, period-concentrated) | stays **Level 2 (watch)** |
| dual_momentum_gem | redundant (corr 0.75, residual-α ≈ 0) | stays **Level 2 (watch)** |
| momentum_concentrated | value-destructive (P(ΔSharpe>0) ≈ 0.07, negative residual-α) | **Level 2 → recommend demote / retire from portfolio consideration** |

This is exactly the outcome **F-014** (trend+vol combine HALVES median excess), the
cross-market non-replication **F-020** (3/7), and Agent 7's independence result
(`INDEPENDENCE_MATRIX.md`: n_eff ≈ 3 clusters, everything long-biased US equity risk,
raw pairwise corr 0.49–0.96) predict: the seven books are one risk family, so bolting a
correlated long-biased sleeve onto an already-diversified 4-book control adds no independent
forecasting value — only leverage/dilution, which the equal-vol test strips out.

**Level-4 count: 0 of 3.** The frozen 4-book ensemble is not improved by any watch-tier book.

---

*Distinctions honored: this measures **Portfolio alpha** (does the source improve the combined
book?), which is strictly weaker than an independent **Market** forecast. Even a positive result
here would NOT have been an independent market alpha — and none was positive.*
