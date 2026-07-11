# hunt2026 5-year backdated results — 2021-07-10 → 2026-07-10 (5.0y)

SPY: total +84.2%, CAGR **+13.00%**, sharpe 0.80, maxDD -24.5%
Round-1 specs are NOT blind on 2021-2025 (fit window overlapped) — stress test only.
Round-2 specs (blind=True) were fit on data <= 2021-07-10 and are fully blind.

| spec | blind | CAGR | total | sharpe | maxDD | avg gross | ≥18%/yr |
|---|---|---|---|---|---|---|---|
| vol_core_svxy | n | +24.27% | +196.3% | 0.93 | -33.8% | 1.59 | **PASS** |
| vol_managed_qqq | n | +23.26% | +184.5% | 0.94 | -35.2% | 1.33 | **PASS** |
| vix_panic_buyer | n | +21.15% | +161.0% | 0.83 | -34.4% | 1.54 | **PASS** |
| dual_momentum_gem | n | +17.95% | +128.3% | 0.74 | -37.5% | 1.41 | fail |
| momentum_concentrated | n | +16.63% | +115.8% | 0.80 | -17.1% | 0.89 | fail |
| trend_gated_spy_2x | n | +16.46% | +114.2% | 0.80 | -40.0% | 1.73 | fail |
| composite_book | n | +15.46% | +105.1% | 0.61 | -44.1% | 1.99 | fail |
| breadth_gated_leverage | n | +14.69% | +98.5% | 0.61 | -39.0% | 1.52 | fail |
| gap_drift | n | +12.25% | +78.2% | 0.56 | -41.9% | 1.50 | fail |
| ew_levered_vix_gate | n | +11.51% | +72.4% | 0.53 | -42.3% | 1.85 | fail |
| pca_minvar_jse | n | +11.33% | +71.0% | 0.55 | -31.8% | 2.00 | fail |
| pca_minvar_raw | n | +11.23% | +70.2% | 0.55 | -31.8% | 2.00 | fail |
| svxy_vix_carry | n | +3.14% | +16.7% | 0.26 | -29.7% | 1.00 | fail |
| deep_dip_reversion | n | +2.11% | +11.0% | 0.22 | -44.1% | 1.50 | fail |
