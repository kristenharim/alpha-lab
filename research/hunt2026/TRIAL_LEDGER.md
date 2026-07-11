# hunt2026 trial ledger — every hypothesis, every loop, every adaptive step

The number that deflates a result is not "how many specs ran" but "how many chances the
process gave itself." This ledger counts both. Benchmarks are controls, not trials.

## Hunt-level table

| Hunt | Date | Hypotheses tested | Derived from prior holdout results? | Finalists | Pass bar | Bar |
|---|---|---|---|---|---|---|
| Hunt 1 (1y blind) | 2026-07-10 | 14 | no (research from train ≤2025-07 only) | 14 | 11 raw / 4 by excess | ≥+18% net, 1y |
| Hunt 2 (5y blind) | 2026-07-10 | 4 | **yes — designs chosen after seeing Hunt-1 5y stress** | 4 | 3 | ≥+18% CAGR, 5y |

**Effective trial count: > 18.** Hunt 2 was an adaptive loop: its 4 designs were selected
knowing which Hunt-1 families died in the 2022 window. Formally the process had 18 registered
chances plus one selection step over the design space; every future hunt that reacts to a
holdout result must add a row here and say so in this column.

## Robustness experiments (registered probes of frozen specs — not new spec trials)

| Exp | Date | Variants registered | Derived from prior holdout results? | Decisive stat |
|---|---|---|---|---|
| defensive-asset (dual_momentum_gold third-asset menu) | 2026-07-10 | 10 (GLD/TLT/DBC/XLU/XLP/UUP/SLV/VNQ/NONE/EQW-def) | **yes — adaptive loop: reacts to hunt-2 blind result + ledger's "gold hindsight" flag** | GLD-vs-NONE window win share, split pre/post 2024-01-01 (preregistrations/defensive-asset-2026-07-10.md) |

## Spec-level registry

| # | spec | hunt | status | result summary |
|---|---|---|---|---|
| 1 | vol_managed_qqq | 1 | survivor (stress-passed 5y too) | 1y +42.5%; 5y +23.3% (not blind on 5y) |
| 2 | vol_core_svxy | 1 | survivor (stress) | 1y +36.1%; 5y +24.3% (not blind) |
| 3 | breadth_gated_leverage | 1 | retired | 1y pass on beta; 5y +14.7%, param-fragile |
| 4 | trend_gated_spy_2x | 1 | retired | 5y +16.5%, −40% DD; superseded by trend_vol_qqq |
| 5 | momentum_concentrated | 1 | sleeve-only (WF demoted, F-015) | best beta-matched excess both windows; misses raw bar on 5y |
| 6 | dual_momentum_gem | 1 | retired | 1y star (+58.6%), 5y +17.9% — whipsaw-fragile |
| 7 | svxy_vix_carry | 1 | retired | failed both windows; gap risk as pre-registered |
| 8 | gap_drift | 1 | watch | 1y +5.8% excess; 5y decayed to +12.3% CAGR |
| 9 | ew_levered_vix_gate | 1 | retired | negative excess 1y; 5y +11.5% |
| 10 | deep_dip_reversion | 1 | retired → failure DB | 5y +2.1%; reversion at daily freq confirmed dead |
| 11 | vix_panic_buyer | 1 | retired (WF: −62% GFC window, F-013) | 1y +3.2% excess; 5y +21.2% (not blind) |
| 12 | composite_book | 1 | retired | beta in a costume; −44% DD in 5y |
| 13 | pca_minvar_raw | 1 | control (kept) | Goldberg pair control |
| 14 | pca_minvar_jse | 1 | watch (estimator research) | beat raw by +15bps 1y / +10bps CAGR 5y — direction right, expression muted |
| 15 | tsmom_multi_asset | 2 | survivor (as sleeve only) | 5y blind +10.5% standalone; +13.7% in 2022 — crisis alpha |
| 16 | trend_vol_qqq | 2 | survivor (tail-hedge variant, F-014) | 5y blind +24.7%, Sharpe 1.11 |
| 17 | dual_momentum_gold | 2 | survivor (discounted) | 5y blind +29.1%; gold-menu design hindsight |
| 18 | defensive_ensemble | 2 | survivor (capital-preserver: WF median +15%, worst −18%) | 5y blind +19.9%, Sharpe 1.32, −13.4% DD, flat 2022 |

## Controls / benchmarks (not trials)

| benchmark | purpose |
|---|---|
| SPY buy-and-hold | market base rate (built into every evaluator) |
| bench_qqq_buyhold | naive base for all QQQ specs |
| bench_qqq_sma200_2x | gate-only naive: isolates trend_vol_qqq's gate component |
| vol_managed_qqq (dual role) | vol-target-only naive: isolates trend_vol_qqq's vol component |

## Rules going forward

1. Every new spec gets a row BEFORE its first holdout/walk-forward score.
2. Every adaptive loop (designing after seeing an out-of-sample result) gets a hunt-level
   row with the derivation flagged.
3. Retired specs stay in the table and get a failure-database entry (FAILURES.md).
4. Implementation claims are reported as the delta vs the naive benchmark, not the raw return.

> 2026-07-10 (later): statuses revised by the 82-window walk-forward (walkforward/summary.md); see FAILURES.md F-013..F-015.
