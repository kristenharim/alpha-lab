# hunt2026 holdout, re-priced at measured execution cost

**Sensitivity analysis, not a re-scoring.** The blind holdout was spent on 2026-07-10;
`results/` is write-once and untouched. This re-prices the same already-seen return
streams under a harsher single-name cost. Surviving here is not passing a second test.

SPY over the same window: **+21.97%**. Pre-registered bar: 18% net.

`frozen` = 10 bps/side, the pre-registered model. `floor` = 42 bps, the
direction-independent part of measured execution. `measured` = 58 bps, its mean.
ETF costs are unchanged at 2 bps: those books measured about zero against that.

Raw net first, then the column that matters: excess over a beta-matched SPY, which is
the spec's own average gross exposure times SPY. A 2x book returning 30% while SPY
returns 22% has produced nothing.

| spec | turnover/d | gross exp | net at 58 | beta-matched | excess frozen | excess at 58 | alpha survives? |
|---|---|---|---|---|---|---|---|
| dual_momentum_gold | 1.20% | 1.50 | +79.03% | +32.96% | +46.07% | +46.07% | yes |
| dual_momentum_gem | 3.59% | 1.50 | +62.78% | +32.96% | +29.83% | +29.83% | yes |
| momentum_concentrated | 3.69% | 0.83 | +31.10% | +18.22% | +18.85% | +12.88% | yes |
| bench_qqq_sma200_2x | 2.39% | 1.95 | +53.68% | +42.89% | +10.78% | +10.78% | yes |
| bench_qqq_buyhold | 0.00% | 1.00 | +31.25% | +21.97% | +9.28% | +9.28% | yes |
| vol_managed_qqq | 3.08% | 1.53 | +40.77% | +33.65% | +7.13% | +7.13% | yes |
| vix_panic_buyer | 1.20% | 1.56 | +37.49% | +34.27% | +3.22% | +3.22% | yes |
| trend_vol_qqq | 4.72% | 1.52 | +35.16% | +33.35% | +1.81% | +1.81% | yes |
| vol_core_svxy | 7.56% | 1.76 | +39.85% | +38.62% | +1.22% | +1.22% | yes |
| defensive_ensemble | 4.27% | 1.88 | +41.12% | +41.40% | -0.29% | -0.29% | NO |
| gap_drift | 7.64% | 1.50 | +27.08% | +32.96% | +6.38% | -5.88% | NO |
| trend_gated_spy_2x | 2.39% | 1.95 | +35.14% | +42.89% | -7.75% | -7.75% | NO |
| breadth_gated_leverage | 5.59% | 1.54 | +25.61% | +33.86% | -8.25% | -8.25% | NO |
| composite_book | 4.20% | 2.00 | +33.53% | +43.94% | -3.49% | -10.41% | NO |
| svxy_vix_carry | 20.72% | 1.00 | +7.07% | +21.97% | -14.90% | -14.90% | NO |
| deep_dip_reversion | 16.97% | 1.50 | +16.72% | +32.96% | +8.07% | -16.24% | NO |
| tsmom_multi_asset | 2.07% | 1.99 | +25.18% | +43.82% | -18.65% | -18.65% | NO |
| ew_levered_vix_gate | 3.93% | 1.91 | +23.25% | +41.95% | -12.70% | -18.70% | NO |
| pca_minvar_jse | 0.75% | 2.00 | +9.53% | +43.94% | -33.41% | -34.41% | NO |
| pca_minvar_raw | 0.75% | 2.00 | +9.41% | +43.94% | -33.53% | -34.53% | NO |

- cleared the 18% bar at frozen cost: **17** of 20; at 58 bps: **16**
- POSITIVE beta-matched excess at frozen cost: **11**; at 58 bps: **9**

The second line is the one that decides anything. The bar was 18% while SPY did +21.97%, so clearing it never meant much.
