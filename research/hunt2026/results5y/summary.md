# hunt2026 5-year backdated results — 2021-07-10 → 2026-07-10 (5.0y)

SPY: total +84.2%, CAGR **+13.00%**, sharpe 0.80, maxDD -24.5%
Round-1 specs are NOT blind on 2021-2025 (fit window overlapped) — stress test only.
Round-2 specs (blind=True) were fit on data <= 2021-07-10 and are fully blind.

| spec | blind | CAGR | total | sharpe | maxDD | avg gross | ≥18%/yr |
|---|---|---|---|---|---|---|---|
| dual_momentum_gold | Y | +29.10% | +258.5% | 1.07 | -35.7% | 1.42 | **PASS** |
| trend_vol_qqq | Y | +24.67% | +201.1% | 1.11 | -19.6% | 1.37 | **PASS** |
| defensive_ensemble | Y | +19.89% | +147.6% | 1.32 | -13.4% | 1.92 | **PASS** |
| tsmom_multi_asset | Y | +10.48% | +64.6% | 0.91 | -17.4% | 1.86 | fail |
