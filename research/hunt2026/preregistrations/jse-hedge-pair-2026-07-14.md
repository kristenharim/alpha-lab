# Pre-registration — JSE-corrected factor-1 hedging in the statarb residual harness (HYP-005b)

### EXP-2026-07-14-jse-hedge-pair

**Stage-0 note.** Kristen's call, 2026-07-14: HYP-005 (residual reversion, DEAD 2026-07-10)
is REOPENED as HYP-005b on a materially new mechanism — the hedge factor, not the signal
parameters. She explicitly removed the no-revival clause: if pre-committed bars clear,
revival proceeds through the normal Stage gates (her call). The 2026-07-10 verdict and its
story (P&L-identity bug; 4x gross-edge-vs-cost gap) stand unedited on the record.

**Hypothesis** (one falsifiable sentence, mechanism included):
Hedging each stock with a JSE-corrected statistical factor-1 instead of the raw PCA
factor-1 produces measurably purer residuals — lower absolute market beta of the hedged
book and a larger implementable gross edge for the frozen Avellaneda–Lee reversion harness
— because factor 1 is the one factor whose JSE target (equal-weight direction) is valid
(F-027's lesson), and mis-estimated factor-1 leaks market movement into "residuals" that
the strategy then wrongly bets will revert.

**Layer touched** (exactly one) + registered baselines:
Layer B — the hedge-factor estimator only. The reversion harness is FROZEN at the
2026-07-10 verdict configuration: window=60, entry=1.25, exit=0.5, skip=1, PIT membership,
implementable P&L (hedged_returns engine), cost = 10 bps/side (the verdict's cost basis —
revival cannot come from a cheaper cost assumption). Baselines: sector-ETF hedge (the
published verdict's model, rerun under identical settings) and pca1 (raw statistical
factor-1). Decisive pair: **jse1 vs pca1** — isolates the correction.

**Alpha type tag**: estimator (measurement) with a pre-registered revival gate (market).

**Factor construction (frozen):** monthly re-estimation; at each month-start, take the
trailing n_est days of returns for names with full coverage, top-1 SVD direction h₁
(sign-fixed positive-sum); pca1 factor return = h₁ᵀr_t (unit-norm weights) for the
following month; jse1 = identical except h₁ is JSE-rotated toward q per
estimators.py (k=1, same τ) — equivalence with ESTIMATORS["jse1"]'s eigenvector asserted.
Registered estimation windows: n_est ∈ {63 (decisive — largest predicted correction), 252}.

**Registered variants** (4 new + 1 baseline rerun, all reported): {pca1, jse1} × n_est ∈
{63, 252}, plus sector-ETF under identical settings. n_trials: decisive JSE question = 2
chances (two windows); any revival claim = 5 chances this run (plus the track's full
history — the ledger's cumulative statarb count applies).

**Decisive statistic (pre-committed), on n_est=63:** paired monthly comparison jse1 vs
pca1 of (a) |rolling 63d β| of the hedged book's net returns vs SPY — the mechanism stat —
and (b) gross annualized Sharpe of the book. Verdict:
- "JSE improves the hedge" if median monthly |β|(jse1) < |β|(pca1) with paired p < 0.05
  AND gross Sharpe delta ≥ 0;
- "no effect" if |β| difference insignificant;
- "harmful" if |β|(jse1) > |β|(pca1) with p < 0.05 or gross Sharpe delta < −0.05.

**Revival gate (pre-committed, Kristen's requested path):** if ANY variant's NET Sharpe
(frozen params, 10 bps/side, deflated with n_trials=5) ≥ 0.5 — the repo's own alive bar —
HYP-005b advances to Stage-2 replication candidacy for Kristen's review. Honest prior
from the record: the dead verdict measured gross edge ~0.3 Sharpe vs 5.3%/yr costs (a 4x
gap), so this gate requires the hedge upgrade to multiply the gross edge several-fold —
registered as a long shot so that IF it happens, it counts and nothing needs re-running.

**Expected result:** hedge-purity improvement is the live question: |β| lower for jse1
with a small positive gross-edge delta (direction per F-010; magnitude likely small per
every JSE result on record). Net Sharpe likely remains far below 0.5 for all variants
(the churn is signal-driven, not hedge-driven).

**Alternative result:** statistical-factor hedging (both pca1 and jse1) is no better or
worse than sector ETFs (sector structure already captures the systematic risk that
matters at this horizon), and/or jse1 ≈ pca1 (at n_est=63 with ~500+ names, ψ̂₁ ≈ 1 so
the correction barely moves h₁ — consistent with F-026's psi floor finding).

**Failure / kill condition (stop-iterating):** one run of the registered grid. No other
estimation windows, no k > 1, no signal-parameter changes, no cost re-assumptions. Any
follow-up design (e.g., multi-factor hedge, Ledoit-Wolf hedge — STATE.md's old idea) is a
new prereg. If "no effect" or "harmful" → FAILURES.md entry and HYP-005b closes back to
the 2026-07-10 verdict.

**Trial-ledger row:** same commit. **Derived from prior holdout results?** YES — adaptive
loop: reacts to F-027 (factor-1 is JSE's valid target), F-010/F-021 (magnitude priors),
and the HYP-005 post-mortem (implementable-P&L engine, cost basis). factor_lab read-only.

---
**Result** (filled after the run, never edited above this line): **NO EFFECT** on the
decisive pair (jse1 vs pca1, n_est=63: paired |β_SPY| Δ median −0.0004, p=0.13; gross
Sharpe Δ −0.02); **revival gate NOT HIT** (best net Sharpe −0.40, bar +0.5). Root cause:
ψ̂₁ ≈ 1 at p≈500–1000 — factor 1 carries no correctable dispersion bias on this panel, so
jse1 ≈ pca1 (identical to 2dp at n_est=252). With F-027 this brackets the correction:
the valid-target factor has no bias; the biased factors have no valid target. Side
finding for the record: statistical factor-1 hedging nearly doubles the frozen strategy's
gross edge vs the sector-ETF verdict model (+0.30 → +0.58 gross Sharpe; baseline
reproduces the 2026-07-10 verdict's ~0.3), net −1.02 → −0.40 — hedge lifts the edge,
signal churn still eats it. HYP-005b closes back to the 2026-07-10 verdict; hedge-model
lane = new prereg if pursued. FAILURES.md F-028. Full tables + story:
research/estimator_lab/HEDGE_PAIR.md.
