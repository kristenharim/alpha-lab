# Vol-timing — VIX term-structure gate on SVXY (EXP-2026-07-14-vol-timing)

Prereg: PREREG.md (frozen incl. dispositions). Full 2014-01→2026-07-10; holdout 2025-07-11→. Costs 2 bps/side; churn null ≈ 0.5%/yr pre-stated.

## Verdict (pre-committed ladder): **AMBIGUOUS**

## Primary (vs B2, exposure-matched; annualized mean daily log diff)
- ΔF = +8.46%  [boot 95% CI -11.93%, +37.00%]  (MDE ≈ 35.3%)
- arithmetic secondary: +1.99%  [CI -11.47%, +18.72%]
- holdout ΔH = -7.63% (directional only; ~14 OFF days); holdout OFF-day mean SVXY return +0.659%/day
- one-regime: best contribution year 2018; excluding it -1.55%; pre-2018 +32.68%, post-2018 -3.60%

## Levels & tails

| series | CAGR | vol | maxDD | Volmageddon | COVID | 2022 bear | yen-carry | 2025-04 gaps |
|---|---|---|---|---|---|---|---|---|
| strategy | +10.6% | 42.2% | -66.2% | -41.0% | -17.6% | -36.4% | -38.0% | -12.9% |
| B1_const_SVXY | -1.0% | 53.7% | -95.2% | -89.4% | -55.3% | -23.2% | -22.9% | -18.1% |
| B2_exposure_matched | +1.6% | 49.5% | -92.5% | -84.6% | -52.1% | -21.3% | -21.0% | -16.6% |

## Placebos
- P1 shuffled: 95th pct +11.48% vs ΔF +8.46% → fail
- P2 delayed 5d: excess -10.04% (decay 219%)
- P4 random episodes: 95th pct +11.82% → fail; rule-2-as-written null rate 0.0% (bar < 5%)
- P5 info-free stress gate: excess -1.91%, maxDD -93.5%; real beats P5 on maxDD: yes, on crash windows 3/5

## Latency diagnostics (pre-stated readings in PREREG.md)
- episode-length decomposition of Σ log-diff: {'len1': -0.09186098557815597, 'len2-5': -1.0325670526770314, 'len>5': 2.2141936224207925}
- event-time SVXY mean return day k=1..5 after inversion start: ['-0.903%', '-0.544%', '+0.120%', '-0.319%', '+1.183%'] vs unconditional +0.074%/day

## Story (post-run + adversarial recompute)

The ladder returned AMBIGUOUS via rule 4, and the pre-committed default applies:
**NO EVIDENCE of timing alpha.** The adversarial recompute reproduced every number to
the printed digit and found no computation error. Rule 2 failed on exactly one leg:
crash-window improvements beat their per-window P4 (random-episode) 95th percentiles
in only 1/5 windows (COVID +34.5pp vs bar +12.9pp passed; Volmageddon +43.6pp missed
its +76.1pp bar — random OFF-blocks covering the window also dodge the −32% day the
real signal ate; 2022 and yen-carry were negative). The maxDD leg and both P5 legs
passed. (Erratum: p4_dd_95 = +23.13pp and the per-window P4 bars were omitted from the
tables above; adversarial recompute supplies them.)

**The full-sample +8.46%/yr is one day.** 2018-02-06 contributes +1.446 cumulative log
against a full-sample total of +1.056. Excluding that single day: ΔF = −3.12%/yr.
Excluding the Volmageddon window: −2.34%/yr. Post-2018 (the tradeable product):
−3.60%/yr. Holdout: −7.63%/yr, with OFF days averaging +0.66%/day of foregone carry.
The pre-2018 +32.7% split is the same day sitting just left of the 2018-02-28 split
date — the genuinely pre-event years 2014–2017 sum to ≈ 0. The −66% vs −92% maxDD
headline is the same day again: forcing the gate ON through 2018-02-02→09 gives
strategy maxDD −93.9%, worse than B2.

**The latency reading is retracted.** Ex-2018/2020, the episode-length decomposition
is negative in aggregate (−0.64 cumulative log) — the prereg's own "negative
everywhere = no signal (retire)" branch — and the event-time profile ex-crashes keeps
only k=1 negative (−0.58%), with k≥2 positive. Faster execution would buy roughly the
k=1 day (~+2.8%/yr gross), about cancelling the −3.1%/yr ex-windfall drag to
breakeven before extra costs — and same-close execution is look-ahead under the
4:15pm print, so "reopenable with faster execution" is an empty phrase for this spec
as frozen.

**Symmetric honesty about the placebos:** P1/P4's 95th percentiles are set entirely by
the ~8% of draws that also dodge 2018-02-06 (conditional on missing it, the bars
collapse to ~+1.6%), so the placebo test was a two-event coin flip rather than a
timing test. This does not rescue the strategy: it loses under every deconfounded
slicing, including underperforming the MEAN lucky placebo draw (+8.5% vs +13.2%)
because it ate the −32% day and pays ~0.5%/yr whipsaw.

**What the experiment established:** with two catastrophe payouts in the sample and a
realized MDE of 35%/yr (double the review pre-estimate), this panel cannot price crash
insurance whose entire value is rare single days. The only earned follow-up is a
longer-history replication — extend the short-vol instrument to ~2006 via free CBOE
futures/index data (2008, May-2010, Aug-2011 as fresh out-of-original-sample
catastrophes) and rerun the IDENTICAL frozen spec with a pre-committed dodge test.
Verdict logged: NO EVIDENCE; the 1-day-lag spec is retired.
