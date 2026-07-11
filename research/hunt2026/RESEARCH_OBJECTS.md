# Research-object registry — every spec decomposed into layers

A spec is not the unit of research; the layer is. Every experiment should change exactly
ONE layer against a registered baseline, so attribution is clean. New specs must add a row
here at pre-registration time.

Layers: **A** economic hypothesis · **B** estimator · **C** portfolio construction ·
**D** execution.

| spec | A: hypothesis | B: estimator | C: portfolio | D: execution |
|---|---|---|---|---|
| vol_managed_qqq | equity premium; vol clusters, doesn't forecast return | 21d realized vol | vol target 0.25, cap 2x | daily, 0.05 band |
| vol_core_svxy | + variance risk premium | 21d RV + VIX vs 63d median | 60/40 core + 0.3 sleeve | daily |
| trend_vol_qqq | equity premium + trend | 21d RV + 200d SMA | vol target × binary gate | daily, hysteresis |
| bench_qqq_sma200_2x | equity premium + trend | 200d SMA only | binary 2x/0 | daily, hysteresis |
| bench_qqq_buyhold | equity premium | none | constant 1x | none |
| trend_gated_spy_2x | equity premium + trend | 200d SMA | binary 2x/BIL | daily, hysteresis |
| breadth_gated_leverage | participation breadth predicts regime | RSP/SPY 63d rel return | binary 2x / vol-managed | daily |
| dual_momentum_gem / _gold | cross-asset relative + absolute momentum | 252d total return | winner-take-all 1.5x | monthly |
| tsmom_multi_asset | time-series momentum across assets | 252d sign, 63d vol | inverse-vol, 15% target | monthly |
| defensive_ensemble | diversified premia combine | sleeve 63d vols | inverse-vol sleeves, 18% target | monthly |
| momentum_concentrated | cross-sectional stock momentum | 12-1 return, 62d vol | top-20 inverse-vol, BSC target | monthly, 4 tranches |
| gap_drift | post-shock underreaction (PEAD proxy) | 60d sigma z, 20d vol median | equal-weight events, SPY fill, 1.5x | daily entry t+1, 60d hold |
| deep_dip_reversion | deep dislocations mean-revert | 60d OLS beta, s-score | 15 slots, SPY fill, 1.5x | daily t+1 |
| ew_levered_vix_gate | equity premium, EW tilt | VIX level gate | EW book, 2x/1x | banded rebalance |
| vix_panic_buyer | post-panic recovery drift | VIX vs 60d median | 1.5x base + 0.5x add | daily hysteresis |
| composite_book | mixed | mixed | fixed sleeves | monthly + bands |
| svxy_vix_carry | variance risk premium | VIX vs 25 & 10d RV | 50/50, binary | daily |
| pca_minvar_raw | low-vol anomaly | **sample PCA k=1** | long-only min-var, 2% cap, 2x | monthly |
| pca_minvar_jse | low-vol anomaly | **JSE/ψ̂-corrected PCA k=1** | long-only min-var, 2% cap, 2x | monthly |

## Matched pairs on file (change exactly one layer)

- pca_minvar_raw vs pca_minvar_jse — layer B (estimator). Result: JSE ≥ raw in all three
  eval modes (1y blind, 5y, 44-window walk-forward), delta tiny at k=1 long-only.
- bench_qqq_sma200_2x vs vol_managed_qqq vs trend_vol_qqq — layers B/C decomposition of
  trend+vol. Walk-forward verdict: each component alone ≈ +13pp median excess; the combo
  HALVES median excess (+8pp) but cuts worst-12m from ~−31% to −22%. Combining is a
  tail-hedge purchase priced in median return, not free alpha.

## Open layer experiments (pre-register before running)

1. Layer B: JSE at k=3-5, unconstrained/benchmark-relative min-var, walk-forward. (The
   Goldberg program's real test; the k=1 capped version answered only direction.)
2. Layer D: open+close execution in the harness → overnight/intraday split becomes
   tradable (reopens F-006).
3. Layer C: turnover-penalty (no-trade band) sweep as a *portfolio* experiment on the
   existing vol-managed family — one knob, pre-registered range.
4. Layer B: EWMA vs realized-window vol estimator inside vol_managed_qqq (matched pair).
