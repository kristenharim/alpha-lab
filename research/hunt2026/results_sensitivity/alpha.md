# hunt2026 holdout: fitted-benchmark alpha, at measured cost, deflated for the trial count

**Sensitivity analysis, not a re-scoring.** `results/` is write-once and untouched.

Benchmark menu, fixed in advance and identical for every spec: `SPY, QQQ, IWM, TLT, GLD, DBC`.
Alpha is the regression constant, annualized, with Newey-West t. Beta-matched excess in
`summary.md` used gross exposure times SPY, which credits a QQQ book with QQQ's own
outperformance; this does not.

DSR is the probability the spec's Sharpe beats what the luckiest of 18 candidate tries would show by chance. Below about 50% the result is
indistinct from selection luck. Specs marked `benchmark` are reference points: not
counted as trials, never eligible for a verdict.

| spec | alpha frozen | alpha at 58 | t | R² | Sharpe | DSR | verdict |
|---|---|---|---|---|---|---|---|
| dual_momentum_gold | +25.80% | +25.80% | 2.11 | 0.91 | 1.61 | 75% | ALPHA |
| dual_momentum_gem | +10.73% | +10.73% | 0.79 | 0.84 | 1.88 | 83% | positive, weak |
| defensive_ensemble | +6.70% | +6.70% | 1.36 | 0.92 | 2.05 | 86% | positive, weak |
| tsmom_multi_asset | +4.13% | +4.13% | 1.01 | 0.86 | 1.98 | 86% | positive, weak |
| vix_panic_buyer | +1.59% | +1.59% | 0.64 | 0.98 | 1.66 | 78% | positive, weak |
| pca_minvar_jse | +2.49% | +1.54% | 0.13 | 0.62 | 0.55 | 38% | positive, weak |
| pca_minvar_raw | +2.32% | +1.37% | 0.11 | 0.62 | 0.55 | 37% | positive, weak |
| bench_qqq_buyhold | +0.00% | +0.00% | 6.42 | 1.00 | 1.57 | 75% | benchmark |
| momentum_concentrated | +0.30% | -4.32% | -0.34 | 0.68 | 1.26 | 65% | no |
| vol_managed_qqq | -4.57% | -4.57% | -0.71 | 0.94 | 1.43 | 70% | no |
| composite_book | +0.43% | -4.68% | -0.63 | 0.89 | 1.33 | 67% | no |
| deep_dip_reversion | +13.54% | -5.40% | -0.36 | 0.55 | 0.79 | 47% | no |
| gap_drift | +3.65% | -5.66% | -0.57 | 0.80 | 1.21 | 63% | no |
| bench_qqq_sma200_2x | -5.97% | -5.97% | -0.59 | 0.91 | 1.40 | 70% | benchmark |
| vol_core_svxy | -6.06% | -6.06% | -1.05 | 0.96 | 1.41 | 70% | no |
| trend_gated_spy_2x | -6.20% | -6.20% | -0.78 | 0.86 | 1.42 | 70% | no |
| trend_vol_qqq | -7.15% | -7.15% | -0.71 | 0.85 | 1.32 | 66% | no |
| breadth_gated_leverage | -7.19% | -7.19% | -1.45 | 0.94 | 1.21 | 63% | no |
| ew_levered_vix_gate | -3.13% | -7.97% | -0.92 | 0.84 | 1.03 | 56% | no |
| svxy_vix_carry | -15.91% | -15.91% | -1.47 | 0.65 | 0.48 | 35% | no |

Bar for ALPHA: positive alpha, Newey-West t above 2, and DSR above 50%. **1 of 18** candidates clear it at measured cost: dual_momentum_gold.

Every caveat from summary.md still applies, and one more: the cost estimate is 25
fills through a simulated paper fill engine, and it is now carrying a conclusion
about which strategies have alpha. That is a lot of weight on a small sample.
