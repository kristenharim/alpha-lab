# The hunt2026 conclusion under a fitted benchmark and measured costs

**Date:** 2026-07-21
**Type:** sensitivity review. **Not a re-scoring.** The blind holdout was spent on 2026-07-10,
`research/hunt2026/results/` is write-once and untouched, and nothing here changes the recorded
result. Re-pricing an already-seen return stream cannot un-spend the holdout.
**Supersedes nothing.** `memos/hunt2026-verdict.md` remains the record of what the hunt returned.
This is what those same return streams look like under two corrections.

## Why this exists

EXP-OPS-REALITY measured live paper execution on the dedicated single-name account at roughly
+58 bps per fill against a frozen cost model charging 10. That raised an obvious question about
the hunt's conclusion, and answering it exposed a second and larger problem with how the hunt was
benchmarked.

Two corrections, applied in order:

1. **Cost.** `harness.STOCK_BPS` moves from 10 to 58 bps. ETF costs are untouched at 2, because
   the ETF books measured about zero against that. Evidence:
   `research/hunt2026/exec_side_split.py`, `memos/band-ruling-2026-07-21.md`.
2. **Benchmark.** The verdict scored excess against the spec's average gross exposure times SPY.
   The spec list itself shows what that misses: `bench_qqq_buyhold`, a passive hold containing no
   strategy, scores +9.28% of excess on that convention, because the benchmark is SPY and the
   holding is QQQ. Every QQQ-shaped spec inherits that premium for free. The benchmark is now
   fitted rather than chosen: each spec's daily net regressed on a fixed menu of SPY, QQQ, IWM,
   TLT, GLD and DBC with a constant, Newey-West errors. The menu is identical for every spec.

Then the selection charge, which the verdict applied and the first pass here did not: the deflated
Sharpe from `robustness.py`, recomputed on the holdout window, against the 18 candidates. The two
dirs carrying a `benchmark` marker are excluded from the trial count, as `robustness.py` excludes
them.

## What each test removes

| test | specs surviving |
|---|---|
| cleared the pre-registered 18% bar | 17 of 20 |
| positive excess over gross exposure times SPY | 11 of 20 |
| still positive once single names pay 58 bps | 9 of 20 |
| positive FITTED alpha, t above 2, DSR above 50% | **1 of 18 candidates** |

The survivor is `dual_momentum_gold`: +25.8% annualized alpha, t = 2.11, DSR 75%. It clears the
bar. It does not clear it comfortably.

## The finding that matters most

**The benchmark did more damage than the costs.** Costs flip four specs from positive to negative
fitted alpha. The benchmark correction had already taken most of the field to zero before costs
were touched at all.

`momentum_concentrated` is the clearest case:

| lens | result |
|---|---|
| excess over gross exposure times SPY | +18.85% |
| fitted alpha, frozen 10 bps cost | +0.30% (t = -0.34, R² = 0.68) |
| fitted alpha, measured 58 bps cost | -4.32% |

Its holdout return was its factor exposure. The gross-exposure convention gave it a low bar,
0.83 exposure times SPY, and the regression found what it was actually loading on. This is the
book the +58 bps was measured on, and the cost finding is the smaller of the two corrections
applied to it.

## The live paper books

Seven books trade forward. Their fitted alpha at measured cost:

| book | fitted alpha at 58 bps | t | DSR | reading |
|---|---|---|---|---|
| dual_momentum_gold | +25.80% | 2.11 | 75% | the only one that clears |
| dual_momentum_gem | +10.73% | 0.79 | 83% | positive, not distinguishable from noise |
| defensive_ensemble | +6.70% | 1.36 | 86% | positive, not distinguishable from noise |
| momentum_concentrated | -4.32% | -0.34 | 65% | no alpha at any cost level |
| vol_managed_qqq | -4.57% | -0.71 | 70% | no |
| vol_core_svxy | -6.06% | -1.05 | 70% | no |
| trend_vol_qqq | -7.15% | -0.71 | 67% | no |

Four of the seven have negative fitted alpha. Three of those four are levered QQQ or volatility
books whose Sharpes are real and whose alphas are not.

## A trap worth naming

Several specs with no alpha carry high deflated Sharpes: `defensive_ensemble` 86%,
`dual_momentum_gem` 83%. That is not a contradiction. DSR asks whether a Sharpe beats selection
luck, and a levered beta position has a perfectly real Sharpe. Any single one of these three
filters passes a leveraged index fund. All three together are the test.

The same trap caught this analysis mid-flight: `bench_qqq_buyhold` fits its own benchmark
perfectly, reported t = 6.42 on a numerically zero intercept, and was briefly labelled ALPHA
before the `benchmark` marker convention was applied.

## What bounds all of it

- One year of daily data. t = 2.11 on ~250 observations is a marginal claim, not a settled one.
- Six regressors can over-explain. Fitted R² runs 0.55 to 1.00.
- The luck bar for DSR is estimated from the holdout Sharpes themselves.
- The cost figure is 25 fills over 4 sessions through Alpaca's simulated paper fill engine. It
  bounds the backtest-versus-paper question and says nothing about live execution, and it is now
  carrying a conclusion about which strategies have alpha. That is a great deal of weight on a
  small sample.
- The fitted benchmark is a defensible convention, not the only one. A different menu gives
  different alphas. The menu was fixed in advance and applied identically precisely so that this
  memo cannot be accused of choosing it to taste.

## What this does and does not license

It does not license stopping or reallocating anything. The house rule from the verdict memo still
governs: forward paper NAV is the only next evidence that counts, and this analysis is a
re-reading of evidence already collected, not new evidence.

What it does license is a change in expectation. If the forward paper program returns strong
numbers from the levered QQQ and volatility books, that is the beta doing its job, and it should
not be read as validation. The books to watch for a real signal are `dual_momentum_gold`, and
`momentum_concentrated` as the one whose alpha this review says should not be there.

Reproduce with `research/hunt2026/cost_sensitivity.py` and
`research/hunt2026/cost_sensitivity_alpha.py`; output in `research/hunt2026/results_sensitivity/`.
