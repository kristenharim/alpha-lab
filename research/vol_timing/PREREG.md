# Preregistration — VIX term-structure gate on SVXY carry (EXP-2026-07-14-vol-timing)

Written before any strategy return is computed. Data gate + hypothesis:
DATA_GATE.md. Reviewer round (statistical + implementation + data-integrity)
precedes execution; dispositions appended. FROZEN on incorporation.

## Hypothesis
Hold SVXY when VIX/VIX3M < 1 at the prior close; hold BIL otherwise. Beats constant
SVXY net of costs, improvement concentrated in tail outcomes. Mechanism, sign, delay,
non-repackaging argument: DATA_GATE.md Phase 1.

## Data and availability timing
Corrected hunt panel (SVXY, BIL, ^VIX closes; auto-adjusted); `data/raw/
vix3m_daily.parquet` (manifest row 2026-07-14). Signal at close t uses only values
published by close t (4:15pm caveat handled: weights set at close t+1, earn t+2 —
one-full-day delay). SVXY product regime change 2018-02-28 (−1x → −0.5x): all
results additionally split pre/post.

## Sample, training, holdout
Full: 2014-01-02 → 2026-07-10 (panel). Training (for the ONE trained constant, w̄):
2014-01-02 → 2025-07-10. Claim-bearing holdout: 2025-07-11 → 2026-07-10 (~250 days,
hunt convention; contains the 2025 inversion cluster). No parameter is fitted on the
holdout; the signal itself has NO fitted parameters.

## Exact signal & strategy (all parameters fixed here)
- Signal s_t = 1{VIX_t / VIX3M_t < 1.0}. Threshold 1.0 is a natural constant; no
  lookbacks, no smoothing, no hysteresis (whipsaw cost accepted; median inversion
  episode = 1 day).
- Strategy weights at close t: SVXY = s_{t−1}, BIL = 1 − s_{t−1} (harness then lags
  one more day by convention → total delay 1 trading day from signal to earning).
- Gross 1.0 always; no leverage, no financing.

## Benchmarks (frozen)
- B1: constant 1.0 SVXY (buy-and-hold, same harness costs).
- B2 (exposure-matched): constant [w̄·SVXY + (1−w̄)·BIL], **w̄ = 0.9216** = mean of
  1{VIX_t/VIX3M_t < 1.0} over training dates on the corrected panel calendar
  (computed signal-side, frozen here before any return is touched). B2 separates
  timing from average de-risking.
- Context only (not gates): existing parent vol_core_svxy (different objective,
  reported for orientation); SPY buy-and-hold.

## Costs / financing / rolls
Harness ETF costs 2 bps per side on turnover; full entry cost first day. No
financing (gross 1). No futures rolls (ETF instrument; roll drag is inside SVXY —
identical across strategy and benchmarks). PRE-COMPUTED CHURN NULL (signal-side):
162 signal transitions over 12.5y, each trading both legs (|ΔW| = 2 → 4 bps/switch)
→ expected switching drag ≈ 0.5%/yr that B2 (zero turnover) does not pay — the
primary outcome carries this known handicap. Known harness asymmetry: constant-mix
B2 rebalances drift-free at zero cost (~1–2 bps/yr flattery, accepted).

## Primary outcome (single estimand — stat-review blocking fix)
Mean daily LOG-return difference, log(1+r_strat) − log(1+r_B2) — its mean IS the
CAGR difference, so vol drag sits inside the estimand coherently. Stationary block
bootstrap (mean block 21d, 2000 draws, seed 3) CI on the SAME quantity, full sample;
holdout reported directionally. MANDATORY SECONDARY: arithmetic daily mean difference
with its own CI. Pre-stated reading: log improvement WITHOUT arithmetic improvement =
variance-drag avoidance (risk management); BOTH = conditional-mean timing. MANDATORY
MDE LINE in the report (from OFF-day count and SVXY vol): reviewer pre-estimate — the
CI resolves only a ~12–20%/yr edge (vs F-007-scale effects of +3–6%/yr), so rule 3 is
likely unreachable at plausible effect sizes and a rule-2/4 outcome with positive
sub-MDE point estimates is the EXPECTED result under a true-but-modest mechanism.

## Secondary outcomes (all mandatory)
Max drawdown; crash-period returns (pre-listed windows: 2018-02-01→2018-02-15
Volmageddon; 2020-02-19→2020-03-23 COVID; 2022-01-03→2022-10-14 slow bear;
2024-07-15→2024-08-09 yen-carry gap; 2025-04 gap cluster); realized vol; convexity
profile (monthly-return regression on SPY monthly ± quadratic, descriptive);
turnover; capacity note (SVXY AUM/ADV, qualitative).

## Placebos (all mandatory, pre-committed)
P1 shuffled signal: circular 63d block shuffle of the ON/OFF series (1000 draws,
seed 5) — the strategy's log-mean excess over B2 must exceed the shuffled 95th pct.
P2 delayed signal: s_{t−6} (5 extra days) — pre-stated: if the delayed version
retains > 50% of the excess, the "timing" is regime beta, not signal timing.
P3 fixed-exposure: B2 itself (the primary comparison).
P4 random rebalance dates: alternating geometric-run binaries with OFF-run mean =
2.98d (the real mean inversion episode) and ON-run mean set so the ON fraction =
0.9234 (1000 draws, seed 7), each run through the identical s-lag and cost path —
same bar as P1. The P1∧P4 conjunction is conservative (joint null rate < 5%,
reported empirically).
P5 stress-correlated, information-free gate (stat-review blocking fix — the
discriminating null for rule 2): OFF on days whose lagged 21d SPY realized vol is
in its top 7.84% (threshold = training-period quantile matching the real signal's
OFF fraction), same lag and cost path. P5 carries NO term-structure information;
the real signal must beat it on every rule-2 tail metric, else rule 2 cannot fire.

## Decision rules (exhaustive; verdict = first match; ΔF = full-sample mean daily
log difference vs B2 annualized ×252; ΔH = holdout same; boot-CI on ΔF)
1. NO EVIDENCE of timing alpha: ΔF ≤ 0 AND no rule-2 tail case.
2. RISK-MANAGEMENT IMPROVEMENT, NOT ALPHA (all tail metrics vs B2 and vs the
   placebo nulls, per stat review): boot-CI includes 0 or ΔF ≤ 0, BUT maxDD improves
   vs B2 by more than the P4 95th percentile of maxDD improvements, AND ≥ 3 of the
   5 crash windows improve vs B2 by more than their P4 95th percentiles, AND the
   real signal beats P5 on maxDD and on ≥ 3 of 5 crash windows. The fraction of P4
   draws satisfying this rule as written is REPORTED and must be < 5%.
3. PROMISING BUT UNPROVEN VOLATILITY TIMING ALPHA: ΔF > 0 with boot-CI excluding 0,
   AND ΔH > 0 AND holdout OFF-day mean SVXY return < 0 (directional mechanism
   check; holdout has only ~14 OFF days — confirmatory-directional only), AND P1
   and P4 pass, AND P2 decays > 50%, AND not one-regime: (a) removing the calendar
   year with the largest contribution to the mean daily log difference leaves the
   remaining-day mean > 0, AND (b) the point estimate is positive in BOTH the
   pre-2018-02-28 and post-2018-02-28 SVXY-regime splits. Leave-one-EPISODE-out
   profile reported descriptively.
4. Otherwise: AMBIGUOUS — reported as-is, adversarial review before any reading.
   If reached because P1 or P4 failed, the default reading is NO EVIDENCE unless
   the adversarial review identifies a computation error.
ROBUST is not reachable in this experiment (requires forward paper trading).
No tuning after results; the only post-run additions are mechanism notes.
MANDATORY DIAGNOSTICS (latency vs no-signal, pre-stated readings): (i) episode-
length decomposition of the daily log difference (episodes of length 1, 2–5, >5
days): negative for ≤2 but positive for long episodes = mechanism intact but
implementation too slow at 1d granularity (latency problem, reopenable); negative
everywhere = no signal (retire). (ii) event-time profile: mean SVXY excess return
on day k from episode start; k ≥ 1 not below unconditional = gate systematically
late. SIGNAL-SIDE FACTS on record: the gate was ON entering all 5 crash windows;
within-window ON fractions — Volmageddon 27%, COVID 21%, 2022 bear 93%, yen-carry
80%, 2025-04 19% — so protection, if any, must appear in Volmageddon/COVID/2025-04;
the 2022 slow bear stayed in contango (little protection available), and the
Aug-2024 gap landed on a held day (inversion printed 2024-08-02) while Volmageddon's
signal fired 2018-02-02, dodging the −83% day but eating the −32% day. Mixed crash
results are the pre-stated expectation.

## Trial accounting
One registered experiment, one signal, zero fitted parameters (w̄ is a benchmark
constant, not a strategy parameter). n_trials for any deflated stat: 1 registered,
with the honesty note that the HYPOTHESIS is publicly known (selection happened in
the literature, not in this repo — stated, not quantifiable).

## Reproducibility
stamp_run (track vol_timing): git SHA; SHA-256 of panel source parquets +
vix3m_daily.parquet; seeds (3, 5, 7); w̄ = 0.9216; numpy/pandas versions (RNG-
dependent placebo percentiles); holdout n = 251; VIX3M reindexed to panel trading
dates (0 NaNs); all thresholds above. Outputs: run_voltiming.py → VOLTIMING.md +
voltiming.csv in research/vol_timing/. Local 2-asset return engine must assert
equality with harness.run on the real strategy path before any placebo loop.

## Dispositions (review round 2026-07-14: statistical + implementation
## approve-with-changes, data-integrity approve — all incorporated)
Statistical: rule-2 nulls (vs B2 + P4 percentiles + P5 gate) [blocking]; log-return
single estimand + arithmetic secondary decomposition [blocking]; MDE mandate +
holdout directional-only framing; latency diagnostics; one-regime rule made exact +
regime-split requirement; rule-4 default reading on placebo failure; P1/P4 → 1000
draws, P5 added. Implementation: w̄ = 0.9216 pre-run; churn null ≈ 0.5%/yr; P4
parameterization pinned (OFF 2.98d / ON-frac 0.9234); crash-window ON fractions on
record; delay convention verified (one day exactly; do not double-lag); stamp
extended. Data-integrity (approve): VIX3M clean, no VXV splice, zero ^VIX pull
drift, SVXY splits verified (Volmageddon = −32% then −83% close-to-close; never
quote intraday −90%), BIL dividend-adjusted; VIX-family re-pulls must re-apply the
panel-date intersection (phantom Memorial-Day row).
FROZEN with these dispositions, 2026-07-14.
