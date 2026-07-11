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

**Verdict: KILL** (run 2026-07-11, EXP-2026-07-10-reversal-x-liquidity).
Runner: `research/independent_alpha/experiments/run_H_E1.py` · CSV:
`experiments/H_E1_results.csv`. Reuses ic_screen's panel load, PIT `member` mask,
month-end dates, n≥50 guard (applied per tercile: ≥150 ok names/date, each of the
two edge terciles ≥50). n = 135 months, 2015-01 → 2026-06, identical to the F-016
baseline. Terciles via `pd.qcut(volume_shock, 3)` on the per-date ok cross-section
(reversal, volume_shock, and forward return all valid).

*Primary statistic — high-demand (top volume_shock tercile) 21d reversal IC:*
mean = **+0.00687, t = +0.41**, hit 54.1%, n = 135. Indistinguishable from zero — and
from the dead unconditional baseline (+0.00515, t = 0.34).

*Interaction (high − low tercile), paired t:* 21d mean = **−0.00247, t = −0.18**;
63d mean = +0.02362, **t = +1.94**. The mechanism's sign only appears at 63d and even
there falls short of the t > 2 bar. At the pre-registered 21d horizon the sign is
*wrong* (quiet names carry marginally more reversal IC than high-demand names: low
+0.00934 vs high +0.00687).

*By-era stability (high tercile, 21d):* 2015-19 +0.036 → 2020-24 −0.012 → 2025-26
−0.034. The only positive era is the oldest; the effect decays to negative and does
not persist — the opposite of a robust conditional signal.

*Blind holdout (2024-07 → 2026-06, 21 months):* **sign flips.** High-tercile 21d IC:
dev +0.016 → holdout −0.045. Interaction 21d: dev −0.006 → holdout +0.015 (also flips).
63d likewise flips (hi +0.028 → −0.024; interaction +0.029 → −0.007).

*Frozen conditions applied mechanically:*
- SUCCESS requires high-tercile t > 2 AND interaction t > 2 AND holdout sign-stable.
  Got high-tercile t = 0.41, interaction 21d t = −0.18, holdout flips → **not met.**
- KILL triggers on high-tercile IC ≈ 0 OR interaction t < 2 (either horizon). All three
  fire: high-tercile IC ≈ 0 (t = 0.41); interaction t = −0.18 (21d) and +1.94 (63d),
  both < 2 → **KILL fires on every clause.**

*Bug check (unusually-strong-result guard, inverted — here for an unusually-*weak*
result, confirm the pipeline isn't silently killing a real effect):* recomputed the
unconditional reversal ic21 independently from raw panel (own shift/member/rank-corr)
→ **0.00515, t = 0.339, n = 135, exact match** to the frozen `ic_screen_stats.csv`
row 1. Load, PIT membership, 21d shift, and Spearman IC are all faithful; terciles are
strict subsets of that same cross-section, so the null conditional result is real, not a
plumbing artifact. Leakage-safe by construction: reversal (21d trailing) and volume_shock
(21d/252d trailing) both fully known at close t; forward returns start t+1.

*Interpretation:* the liquidity-demand conditioner does not revive reversal in the
large-cap monthly-rebalance regime. The mechanism-implied ordering (high-demand IC ≫
quiet IC) is absent at 21d, only weakly and non-significantly present at 63d, and unstable
out-of-sample. This is a genuine negative, consistent with F-016 (dead unconditional IC).

*Docket action (per the frozen stop-iterating rule):* closes **NR-1**'s last named
untested angle at the daily-bar / monthly-rebalance resolution. **Stop running conditional
daily-bar reversal probes on this panel** — do not test a second liquidity conditioner
here. Any reopen of NR-1 now requires intraday data, as NR-1 already stipulated. Ceiling
was level 1 (signal-space); nothing is booked. Adds TRIAL_LEDGER #19 as a measurement /
watch entry (coordinator appends centrally; not edited here).
