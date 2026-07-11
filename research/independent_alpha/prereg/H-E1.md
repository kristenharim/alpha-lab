# PREREG H-E1 — reversal ranking conditional on liquidity-demand intensity

*Frozen 2026-07-10 (Agent 5, Experiment Engineer). Format extends
`research/hunt2026/PREREGISTRATION.md`. Nothing above the Result line may be edited
after the first scoring run.*

- **Experiment ID:** EXP-2026-07-10-reversal-x-liquidity
- **Hypothesis ID:** H-E1-reversal-x-liquidity-shock
- **Ranked:** EXPERIMENT_QUEUE.md #1 (high) · reopens **NR-1** named-untested angle
  (FAILURES.md:128–136, "vol-conditioned entry timing remains the one untested angle")

**Hypothesis** (one falsifiable sentence, mechanism included): Short-term (21d) reversal
is compensation for supplying liquidity to liquidity-*demanders*, so its cross-sectional
rank IC is positive and materially larger among names undergoing a contemporaneous
liquidity-demand shock (high abnormal volume) and ≈0 among quiet names — the unconditional
IC is dead (F-016) precisely because the two subsets net out.

**Layer touched** (exactly one): **A — economic hypothesis** (add a liquidity-shock
conditioner to the reversal signal). Registered baseline: the **unconditional
`st_reversal_21d` rank IC** measured in `robustness/ic_screen.py` — ic21 = 0.0052,
t = 0.34, hit 51.9%, n = 135 months (`ic_screen_stats.csv`, row 1). Nothing else in the
measurement pipeline changes.

**Alpha type tag:** market — but **signal-space only ⇒ evidence-ladder ceiling = level 1**.
A confirmed conditional IC is a predictive relationship, NOT a tradable book; tradability
stays gated behind NR-1's cost wall (≤2–3 bps/side or intraday execution). Do NOT promote a
rank IC to a paper book on the strength of this experiment.

**Control:** `st_reversal_21d = −(close/close.shift(21) − 1)`, unconditional monthly
Spearman rank IC over PIT members (the F-016 dead result above).

**Treatment:** the identical reversal signal, but split each rebalance date's PIT-member
cross-section into terciles of `volume_shock` (signal #6: `vol.rolling(21).mean() /
vol.rolling(252).mean()`, the abnormal-volume proxy for liquidity demand, known at close t).
Compute reversal rank IC **within** the top tercile (high demand) and within the bottom
tercile (quiet), per month. ONE layer changed: the economic conditioner. The conditioner is
a fixed, un-tuned tercile split — no parameter is fit.

**Universe:** PIT S&P 500 members via `panel_2005.parquet` field `member` (ETFs / `^VIX`
excluded via `sandbox_meta.json`); ≥50 valid names per date per tercile or the date is
dropped (mirrors `rank_ic`'s existing n≥50 guard, applied per tercile).

**Sample / train / eval (non-overlapping, holdout fixed BEFORE running):**
- Full measurement window: 135 month-end dates, 2015-01 → 2026 (the ic_screen span).
- The interaction is parameter-free (fixed tercile split), so the primary statistic runs on
  the full sample. To guard against any implicit look, the last **24 months
  (2024-07 → 2026-06)** are the **blind sign-stability holdout**: the high-tercile IC sign
  and the interaction sign must not flip there. Develop/inspect only on 2015-01 → 2024-06.

**Forecast + execution timestamps:** signal and conditioner both known at **close of month-end
day t**; forward return is close-to-close **t+1 … t+21** (21d) and **t+1 … t+63** (63d).
Measurement only — no order is placed, so no execution timestamp.

**Expected effect size:** unconditional IC ≈ 0.005 (dead). Mechanism-true prediction:
high-tercile 21d IC ≈ +0.02 to +0.04 (t > 2 over 135 months); bottom-tercile ≈ 0; interaction
(high − low) mean IC > 0 with t > 2. Honest prior P(belief change) ≈ 0.6 — plausible but the
large-cap regime is where reversal has most decayed.

**Primary statistic:** mean monthly high-tercile 21d rank IC and its t-stat
(mean/std·√n, the ic_screen convention). **Secondary:** interaction IC (high−low) paired
t-stat across months; 63d-horizon replication; by-half stability (2015-19 / 2020-24 / 2025-26).

**Success condition:** high-tercile mean IC significantly > 0 (t > 2) **and** interaction
(high−low) significantly > 0 (t > 2), sign stable in the 2024-07→2026-06 holdout. → NR-1's one
named untested angle **revives in signal space**; write a level-1 predictive entry and hand to
a cost-wall follow-up (do not book).

**Failure / kill condition** (decidable from harness output, includes stop-iterating rule):
high-tercile IC not distinguishable from zero **or** interaction t < 2 (either horizon) →
**kill.** This closes NR-1's last named untested angle at the daily-bar / monthly-rebalance
resolution: **stop running conditional daily-bar reversal probes** (do not test a second
liquidity conditioner on the same panel; the reopen then requires intraday data per NR-1).

**Cost model:** none — signal-space measurement, no turnover, no fills. (This is exactly why
the ceiling is level 1: costs are deferred to a separate NR-1 cost-wall test.)

**Leakage checks:** reversal (21d trailing) and volume_shock (21d/252d trailing) are both
fully determined at close t; forward returns start at t+1 → no fit/eval overlap. No
survivorship in the forward return (delisted names keep their realized path if present in
panel). Tercile assignment uses only close-t data.

**Survivorship checks:** membership via PIT `member` field (not today's index); a name enters
its tercile only on dates it was a member. `panel_2005` retains delisted tickers' history where
available; the ≥50/tercile floor prevents thin-cross-section artifacts.

**Runtime estimate:** ~30–45 s single-core (reuses the ic_screen load + rank loop; adds a
per-date tercile split). **Complexity score:** 2/5 (~30-line extension to `ic_screen.py`;
one new signal + tercile grouping, no new data).

**Information-gain estimate:** HIGH — decisive kill/revive of NR-1's single named untested
angle; near-zero overhead. Either branch retires a live docket item.

**Trial count:** adds **TRIAL_LEDGER.md #19** (signal-space measurement; tag = measurement /
watch, NOT a book) in the same commit. Adaptive-loop flag: derived from the F-016/NR-1
out-of-sample record ⇒ **yes, adaptive** — record in the hunt-level ledger.

**Derived from prior holdout results?** Yes — F-016 (dead unconditional IC) and NR-1 (named
reopen). This is a sanctioned reopen, not a fresh fishing expedition.

---
**Result** (filled after the run, never edited above this line):
