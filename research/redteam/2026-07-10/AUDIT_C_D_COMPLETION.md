# Red-Team Audits C (Adversarial Implementation) & D (Clean-Room) — Completion (2026-07-11)

Run directly in-session (scripts in `adjudicator/`). Read-only; no spec/manifest/deployment
change. This closes the four red-team gaps; only the stock-universe repair project remains.

## Audit D — Clean-room replication (all 7 books, from written specs only)

Method: fixed Agent 8's buggy `month_ends`/`week_ends` helpers (a pandas groupby-apply
`KeyError`, not strategy logic), then compared clean-room weights (built from
params.json + MECHANISM.md + SPEC_CONVENTIONS.md, **spec.py never read**) vs the frozen
spec weights. Net compared via one independent scorer on both weight sets. Tolerance 1 bp.

| book | net max-diff (holdout) | verdict |
|---|---|---|
| vol_managed_qqq | **0.000 bp** | matches |
| vol_core_svxy | **0.000 bp** | matches (0.30 wt diff pre-2011 SVXY only; washes out) |
| trend_vol_qqq | **0.000 bp** | matches (0.049 wt diff at 2008 warmup; washes out) |
| dual_momentum_gold | **0.000 bp** | matches |
| dual_momentum_gem | **0.000 bp** | matches |
| momentum_concentrated | **0.000 bp** | matches (0.038 wt diff early; washes out) |
| defensive_ensemble | **277.6 bp** | **FAILS — see F-RT-07** |

**6 of 7 reproduce to 0.000 bp.** The early-history weight diffs (vol_core/trend/momentum)
are pre-inception warmup that does not enter the holdout or 5y windows.

**F-RT-07: defensive_ensemble is not reproducible from its written specification.
[MEDIUM, CONFIRMED METHODOLOGICAL WEAKNESS]**
The clean-room diverged from day 1 (holdout total 0.36 vs 0.41). Traced to Sleeve A:
`spec.py:41` implements **inverse-vol** `lev_q = (0.25 / rv21).clip(upper=2.0)`, but
`MECHANISM.md:5` says *"scaling exposure by inverse realized **variance**"* (Moreira-Muir
language) and does not state the gate asset (code uses QQQ; a reader reasonably used SPY)
or Sleeve A's rv window (code fixes 21d). An independent implementer therefore built a
materially different Sleeve A (inverse-variance, squared). **This is a docs↔code
inconsistency, NOT a code bug and NOT leakage** (accounting ruled out by the independent
engine at 0.0000 bp; look-ahead ruled out by the poison test). Consequence: the **lead**
book's evidence rests on the specific frozen code, which is internally valid but **cannot be
rebuilt from its writeup**: a reproducibility gap that matters most precisely because
defensive_ensemble is the strongest book. Remediation (documentation only, NOT a code change,
the frozen book stays frozen mid-forward-test): correct MECHANISM.md to state inverse-vol
`0.25/rv21`, the QQQ 200d gate with 1% hysteresis, and the exact inverse-vol sleeve
combination. Does not require rerunning trials. Belief impact: does not invalidate the
result; lowers *reproducibility* confidence for defensive_ensemble until docs are tightened.

## Audit C — Adversarial implementation (predeclared variants, all reported)

Degradation of holdout-year total net vs base (harness close-to-close convention):

| book | open_to_open | intraday_only | delay1 | cost×2 | +5bps fill | whole-shares |
|---|---|---|---|---|---|---|
| vol_managed_qqq | +1.8 | −42.5 | +0.3 | −0.2 | −0.6 | +0.1 |
| vol_core_svxy | +5.1 | −40.3 | +6.7 | −0.5 | −1.3 | −0.1 |
| trend_vol_qqq | +4.5 | −35.6 | +1.1 | −0.3 | −0.8 | +0.2 |
| defensive_ensemble | +1.9 | −36.5 | +1.5 | −0.3 | −0.8 | −0.3 |
| dual_momentum_gold | −5.6 | −83.0 | −2.8 | −0.1 | −0.3 | −0.5 |
| dual_momentum_gem | +2.5 | −40.0 | +5.4 | −0.3 | −0.7 | +0.4 |
| momentum_concentrated | −0.8 | −38.0 | +1.5 | −1.3 | −0.6 | −1.0 |

(units = percentage points of holdout-year total return)

**Verdict: all 7 books SURVIVE adversarial implementation.**
- **open_to_open is the realistic live-execution model** (enter at opens, HOLD through
  overnight, what `hunt_paper_run.py` actually does): degradation is **negligible and mostly
  positive** (+1.8 to +5.1; gold −5.6). The books do **not** depend on the impossible ability
  to trade at the close they signalled on.
- **intraday_only** (re-establish the whole book at each open, forgo every overnight gap) is
  **not a valid execution model**: it is a diagnostic. Its ~−40-point collapse confirms the
  documented **night/day effect** (these ETFs' close-to-close return is ~entirely overnight in
  this window; connects to F-006). Because the books **hold** overnight, they capture it. No
  action. *This column would be a false alarm if read as an execution result; it is not one.*
- **delay1 (full 1-day signal delay), cost×2, +5bps conservative fills, whole-shares
  ($14.4k book)** are all **immaterial** (≤1.3 points): the low-turnover design absorbs them.

**Scope condition (important):** Audit C is modeled on the historical open/close panel, not
real fills. Spread, market impact, and queue position are **not** in the panel. The genuine
execution test remains the forward paper fills (Monday-open onward, via
`hunt_paper_reconcile.py`). Audit C establishes that the strategy *logic* survives plausible
execution-timing changes; it does not certify real-world fills.

## Consolidated red-team status after A/B/C/D
- **Engine/accounting:** RULED OUT (independent engine 0.0000 bp, all 7).
- **Look-ahead/leakage:** RULED OUT (future-poison, all 7).
- **Clean-room:** 6/7 exact; defensive_ensemble = docs-reproducibility gap (F-RT-07).
- **Perturbation (A):** SURVIVES; real fragility = missing-observation rate (data quality,
  stock book) not execution.
- **Regime/tail (B):** mechanisms match roles; levered-beta bear tail risk (−13/−16% 2022);
  gold artifact confirmed; holdout year ~half one month.
- **Adversarial (C):** SURVIVES under realistic execution; overnight-dependence captured by
  holding.
- **Only open item:** stock-universe repair (F-RT-03) → new frozen momentum_concentrated
  trial. And the one thing no backtest audit can settle: real forward fills.
