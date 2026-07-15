# Vol-timing project — final memo (2026-07-14)

One experiment, preregistered and frozen before code, three-reviewer-checked,
adversarially recomputed. Trail: DATA_GATE.md → PREREG.md (frozen + dispositions) →
run_voltiming.py → VOLTIMING.md (+ story) → this memo.

## 1. Data-readiness verdict
READY for index-level option-implied hypotheses with free data only: VIX (panel),
VIX3M (pulled, manifest-logged), VVIX/SKEW/VIX9D available; SVXY + BIL in-panel,
splits/dividends verified; zero missingness. NOT available without payment:
historical option chains / IV surfaces / strike-level skew (OptionMetrics, CBOE
DataShop) — not acquired, per rules. Honest scope: VIX-family indices are genuinely
option-implied, but this is index-level information, not variance-swap or
futures-roll P&L.

## 2. Frozen hypothesis and mechanism
Hold SVXY in contango (VIX/VIX3M < 1 at prior close), BIL when inverted. Mechanism:
vol-carry sign ≈ term-structure slope; inversion = negative expected carry +
concentrated crash risk. Parameter-free (threshold 1.0), one-day delay, not a
repackage of the failed price-only rules (slope is 3M-maturity implied information,
absent from every prior spec) — though still a daily-close gate, with NR-3's
gap-blindness pre-stated.

## 3. Benchmarks
B1 constant SVXY; B2 exposure-matched constant 0.9216 SVXY + 0.0784 BIL (w̄ frozen
signal-side pre-run); same harness costs (2 bps/side); no leverage/financing;
~0.5%/yr strategy churn handicap pre-computed.

## 4. Net and tail results (2014-01 → 2026-07-10; holdout 2025-07-11 →)
- Primary ΔF (mean daily log diff vs B2, annualized): **+8.46%**, bootstrap 95% CI
  [−11.9%, +37.0%], realized MDE ≈ 35%/yr. Arithmetic secondary +1.99% [−11.5, +18.7].
- **The point estimate is one day**: 2018-02-06 contributes +1.45 cumulative log vs
  +1.06 total. Ex-that-day ΔF = −3.1%/yr; post-2018 −3.6%/yr; holdout −7.6%/yr
  (OFF days averaged +0.66%/day of foregone carry).
- Tails: strategy maxDD −66% vs B2 −92% — also the same day (forced-ON counterfactual:
  −93.9%, worse than B2). Crash windows: improved COVID (+34.5pp vs B2, beating the
  random-episode bar) but only 1/5 windows beat their placebo bars; worsened the 2022
  slow bear and Aug-2024 (gate ON, as pre-stated).

## 5. Placebo and adversarial results
P1 shuffled and P4 random-episode bars (+11.5%, +11.8%) exceed ΔF → fail; P2 5-day
delay flips the sign (decay 219%); P5 info-free vol gate: real signal beats it on
maxDD and 3/5 crash windows (the slope information does add something vs a generic
"VIX is high" gate — the only surviving positive note). Adversarial recompute:
every number reproduced, no computation error; the latency ("too slow, reopenable")
reading RETRACTED — ex-2018/2020 the episode decomposition is negative everywhere,
the prereg's own retire branch; placebo bars were themselves a windfall lottery
(conditional bars ~+1.6%), but the strategy loses under every deconfounded slicing,
including vs the mean lucky placebo.

## 6. Classification (pre-committed ladder)
Ladder verdict AMBIGUOUS via rule 4 with P1/P4 failed → pre-committed default:
**NO EVIDENCE OF TIMING ALPHA.** Not "risk-management improvement" either — the
crash-window improvements did not beat their random-episode nulls (1/5).

## 7. Forward paper trading
**No.** At a realized MDE of 35%/yr and a value proposition consisting of rare
single-day dodges (two payout events in 12.5 years), forward paper trading cannot
accumulate evidence on any useful horizon. Nothing here changes live allocations.

## 8. One next action
**Stop this line; retire the 1-day-lag term-structure gate** (its own preregistered
diagnostics hit the retire branch once the windfall day is removed). The single
earned reopening path, if the crash-insurance question stays interesting, is a
longer-history replication: build a constant-maturity short-vol proxy from free CBOE
VIX-futures data back to ~2006 and rerun the IDENTICAL frozen spec against 2008 /
May-2010 / Aug-2011 as fresh catastrophes with a pre-committed dodge test — a new
prereg, run only on your go-ahead (free data, but nontrivial build). An intraday-
signal variant is NOT recommended: expected value ≈ breakeven ex-catastrophe and the
4:15pm print makes same-close execution look-ahead in this design.

## Process notes
Two blocking statistical fixes landed pre-run (rule-2 placebo nulls; single log
estimand) and both mattered — rule 2 would have fired spuriously under the original
B1-anchored bars, and the log/arithmetic split (+8.5% vs +2.0%) correctly flagged
variance-drag avoidance rather than conditional-mean timing. The house
reachability rule caught its target for the second time today (realized MDE 35%/yr,
pre-stated as likely-unreachable rule 3). FAILURES.md-worthy lesson: crash-insurance
rules cannot be priced on a panel with n = 2 catastrophes; extend the instrument
history before testing, not after.
