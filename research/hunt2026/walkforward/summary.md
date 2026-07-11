# hunt2026 walk-forward — rolling 12m windows, quarterly steps

Panel: panel_2005.parquet. SPY: 82 windows, median +14.2%, ≥18% in 34%, worst -36.8%.
Windows before a spec's fit_end overlap its fit window — `oos_*` columns are the
clean subset (round1 fit_end 2025-07-10; round2 2021-07-10). Adjacent windows
overlap (252d window, 63d step): ~4x fewer effectively independent draws.

| spec | gen | wins | median 12m | ≥18% | >0 | beat SPY | med excess | worst | oos med | oos ≥18% |
|---|---|---|---|---|---|---|---|---|---|---|
| vol_managed_qqq | round | 82 | +27.0% | 59% | 82% | 78% | +13.4% | -30.8% | +25.3% | 75% |
| bench_qqq_sma200_2x | bench | 80 | +26.6% | 54% | 72% | 64% | +13.4% | -32.3% | +26.6% | 54% |
| vol_core_svxy | round | 82 | +28.1% | 61% | 84% | 85% | +12.4% | -31.1% | +23.7% | 75% |
| dual_momentum_gem | round | 70 | +20.5% | 51% | 83% | 63% | +9.3% | -24.3% | +22.4% | 50% |
| vix_panic_buyer | round | 82 | +21.7% | 59% | 80% | 77% | +8.2% | -62.1% | +31.0% | 100% |
| trend_vol_qqq | round | 80 | +16.5% | 49% | 80% | 66% | +8.0% | -22.0% | +30.3% | 63% |
| breadth_gated_leverage | round | 82 | +22.8% | 57% | 85% | 73% | +7.3% | -44.5% | +23.9% | 75% |
| dual_momentum_gold | round | 70 | +17.7% | 50% | 71% | 59% | +6.9% | -25.7% | +42.3% | 58% |
| bench_qqq_buyhold | bench | 82 | +18.6% | 51% | 88% | 74% | +5.3% | -38.5% | +18.6% | 51% |
| gap_drift | round | 82 | +19.5% | 55% | 74% | 65% | +5.0% | -53.4% | +28.6% | 100% |
| trend_gated_spy_2x | round | 80 | +17.9% | 50% | 71% | 64% | +5.0% | -27.0% | +27.7% | 75% |
| deep_dip_reversion | round | 82 | +18.0% | 50% | 73% | 63% | +4.1% | -53.4% | +3.0% | 25% |
| pca_minvar_raw | round | 44 | +17.4% | 48% | 77% | 59% | +3.5% | -15.8% | +14.0% | 0% |
| pca_minvar_jse | round | 44 | +17.5% | 50% | 77% | 59% | +3.4% | -15.7% | +14.2% | 25% |
| ew_levered_vix_gate | round | 48 | +18.6% | 52% | 81% | 54% | +2.3% | -34.1% | +23.0% | 50% |
| defensive_ensemble | round | 80 | +15.0% | 36% | 84% | 57% | +1.4% | -18.3% | +17.3% | 42% |
| composite_book | round | 82 | +13.7% | 41% | 76% | 48% | -0.9% | -32.8% | +19.6% | 50% |
| svxy_vix_carry | round | 82 | +3.8% | 27% | 67% | 38% | -4.4% | -27.4% | +7.2% | 0% |
| momentum_concentrated | round | 44 | +6.5% | 27% | 77% | 41% | -4.6% | -13.5% | +15.4% | 50% |
| tsmom_multi_asset | round | 80 | +5.6% | 14% | 71% | 29% | -8.8% | -13.8% | +10.0% | 21% |
