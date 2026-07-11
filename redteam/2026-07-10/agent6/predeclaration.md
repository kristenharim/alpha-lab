# Agent 6 — Predeclared perturbation grid (written BEFORE any perturbation was computed)

Frozen commit 78e1a36. All checksums in SCOPE.md verified identical before this file was
written. Books: the 7 active books in DEPLOYMENT_MANIFEST.md. No perturbation result was
seen before this grid was frozen. Symmetric grids; the registered params stay frozen; no
re-picking regardless of what the maps show.

## Evaluation windows (per book's own blind-evidence window)
- Round-1 books (frozen c9e22c8: vol_managed_qqq, vol_core_svxy, dual_momentum_gem,
  momentum_concentrated): blind holdout year, start=2025-07-10 (harness convention:
  P&L on dates > start), panel = train+holdout concat (same as evaluate.py).
- Round-2 books (frozen 833000d: trend_vol_qqq, defensive_ensemble, dual_momentum_gold):
  blind 5y window, start=2021-07-10 (same as evaluate_5y.py).
- Each book also scored at baseline on the other window for context only.

## Benchmarks (from DEPLOYMENT_MANIFEST.md, computed with the identical harness convention)
- QQQ buy-and-hold: vol_managed_qqq, vol_core_svxy, trend_vol_qqq
- 60/40 SPY/BIL (constant daily target weights): defensive_ensemble
- SPY buy-and-hold: dual_momentum_gold, dual_momentum_gem, momentum_concentrated

Excess = total_net(book) − total_net(bench) over the identical window. For
alternate-start variants the bench is recomputed on the shifted window.
Degradation Δ = excess(variant) − excess(baseline), in pp of total window return.

## P&L convention
Exact copy of harness.run (cap 2.0, held = W.shift(1), close-to-close, per-side costs
10bps stocks / 2bps ETFs on |ΔW|, first-day entry charged). Runner must reproduce the
published results/summary.md and results5y/summary.md numbers at baseline before any
perturbation counts (tolerance: 0.1pp on total_net).

## Perturbation families (all books unless noted)

1. Costs: multiplier ×0.5, ×2, ×4 on both bps rates; additive +10bps/side all tickers.
2. Params ±20% (each param one-at-a-time, both directions, ints rounded):
   - vol_managed_qqq: sigma_target {0.20,0.30}; vol_lookback {17,25}; tolerance_band {0.04,0.06}
   - vol_core_svxy: sigma_target {0.20,0.30}; svxy_weight {0.24,0.36}; vix_gate_window {50,76}
   - trend_vol_qqq: sma_window {160,240}; sigma_target {0.20,0.30}; rv_lookback {17,25}
   - defensive_ensemble: vol_target {0.144,0.216}; sleeve_vol_lookback {50,76}; gross_cap {1.6,2.4→harness clips at 2.0}
   - dual_momentum_gold: lookback {202,302}; risk_leverage {1.2,1.8}; defensive_leverage {0.8,1.2}
   - dual_momentum_gem: lookback_days {202,302}; skip_days {5,21} (±20% of 0 undefined; 21 = the standard 12-1 convention, 5 = weekly skip); equity_leverage {1.2,1.8}
   - momentum_concentrated: n_names {16,24}; vol_target_ann {0.16,0.24}; vol_lookback {50,74}
3. Signal delay (execute the frozen target k trading days late): k ∈ {1, 2, 5}.
4. Rebalance-date shift (recompute the decision k trading days after the scheduled
   rebalance day): k ∈ {1, 3}; applies to the 4 discrete-rebalance books
   (dual_momentum_gold, dual_momentum_gem, momentum_concentrated, defensive_ensemble)
   via minimally patched spec copies in agent6/scratch/ (frozen specs untouched).
   For the daily-signal books this family coincides with signal delay — marked covered.
5. Execution timestamp: next-open execution (hold old weights over the night, new
   weights earn open→close): ret(t+1) = W(t-1)·r_overnight(t+1) + W(t)·r_intraday(t+1).
6. Random missed trades: each day independently with prob p ∈ {5%, 10%}, the day's
   trade does not execute (weights stay at previous executed value). Seeds {0,1,2,4,7};
   report per-seed and median.
7. Random one-bar lags: each day with prob p = 10%, the executed weight is the previous
   day's target. Seeds {0,1,2,4,7}.
8. Missing observations: each (date,ticker) close cell independently masked NaN with
   p ∈ {0.5%, 2%}; signal AND P&L recomputed on the degraded panel. Seeds {0,1,2}.
9. Alternate valid start dates (window start shifted forward by k trading days;
   end fixed): 1y-window books k ∈ {21, 42, 63}; 5y-window books k ∈ {63, 126, 252}.
10. Alternate universe definitions (predeclared, one-at-a-time):
    - vol_managed_qqq: U1 QQQ→SPY
    - vol_core_svxy: U1 core = 100% SPY (drop QQQ leg, same vol scaling)
    - trend_vol_qqq: U1 QQQ→SPY
    - defensive_ensemble: U1 TSMOM menu minus {USO,SLV,HYG}; U2 dual-mom risk menu {SPY,QQQ} (drop GLD)
    - dual_momentum_gold: U1 risk menu +EFA; U2 defensive menu {IEF,BIL}
    - dual_momentum_gem: U1 equity menu +EEM; U2 defensive TLT→IEF
    - momentum_concentrated: U1 strict membership (member 21-day rolling min);
      U2 member mask lagged 21 days
11. Leverage reduction: all final weights ×0.75 and ×0.5.

## Reported per book
median Δexcess across all variants; worst credible Δexcess (worst single predeclared
variant, randomized families represented by their per-seed worst); fraction of variants
with excess > 0; gradual vs cliff-like failure; plateau vs isolated peak (from the ±20%
param one-at-a-time results plus the existing robustness/param_maps.md read only AFTER
our own grid is computed).

Nothing outside this grid will be reported as a headline number; anything exploratory
beyond it gets labeled post-hoc explicitly.
