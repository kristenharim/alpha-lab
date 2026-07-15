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
| defensive-asset (dual_momentum_gold third-asset menu) | 2026-07-10 | 10 (GLD/TLT/DBC/XLU/XLP/UUP/SLV/VNQ/NONE/EQW-def) | **yes — adaptive loop: reacts to hunt-2 blind result + ledger's "gold hindsight" flag** | GLD-vs-NONE window win share, split pre/post 2024-01-01 (preregistrations/defensive-asset-2026-07-10.md) — **result: REGIME ARTIFACT** (GLD wins 13% of pre-2024 windows; robustness/defensive_asset.md); live book unchanged, Stage-4 flag |
| ic-earnings-fwd (layer A, new info source: point-in-time earnings surprises) | 2026-07-10 | 1 primary (SUE→20d rank IC) + 1 secondary (day+1 confirmation) + 2 pre-registered conditioners (sector-relative, dispersion regime) | no — literature prior (PEAD); forward-only collection, no hunt2026 holdout input | 20d rank IC ≥ 0.03 & t ≥ 2 at n ≥ 300 pt-in-time events; kill IC < 0.01 or t < 1 at n ≥ 600 (preregistrations/exp-ic-earnings-fwd-2026-07-10.md) — **ACCUMULATING** from 2026-07-10 |
| est-crossover (layer B, JSE window-length crossover + ψ̂ predictor, Estimator Lab) | 2026-07-10 | 6 window lengths (n=42/63/90/126/189/252; k=3; jse3 vs pca3 matched pair, both books) | **yes — adaptive loop: reacts to F-021 n=252 fail + its n=63 reopen; endpoints already seen, the 4 interior windows + ψ̂ predictor test are new** | long-only paired t per n + pooled Spearman(monthly Δ, median ψ̂), pre-committed ψ̂ cuts 0.90/0.95 (preregistrations/est-crossover-2026-07-10.md) — **result: NO CROSSOVER** (long-only JSE helps at all n, −2.6→−0.5 bps monotone; ψ̂ has zero within-n timing content, both cuts rejected; F-021 CLOSED, estimator_lab/CROSSOVER.md) |
| ops-reality (layer D, execution vs frozen cost model) | 2026-07-10 | 0 spec variants (read-only measurement harness; thresholds fixed before any fill existed) | no — operational, reacts to go-live not to any performance number | trailing-mean slippage in [0,15] bps stocks / [0,5] bps ETFs; reject rate < 2%/night; per-book tracking drag < 30 bps/month; silent-flat alarms = 0 (preregistrations/ops-reality-2026-07-10.md) — **ACCUMULATING** nightly in ledgers/hunt2026/_reconcile.jsonl |
| turnover-band (layer C, portfolio no-trade band overlay on the vol-managed family) | 2026-07-14 | 12 (band ∈ {0.01,0.02,0.05,0.10,0.20,0.40} L1 × {vol_managed_qqq, vol_core_svxy}) + 2 band=0 baselines | **yes — adaptive loop: targets blind-promoted books; effect sized from their published cost-drag/turnover** | per (book, band): median 12m-window net delta (banded − baseline) ≥ +5 bps AND turnover cut ≥ 20% = helps; all within ±5 bps = flat; all ≤ 0 = harmful → FAILURES.md (preregistrations/turnover-band-2026-07-14.md) — **result: MIXED, mechanism NOT supported** (deltas 5–10x the cost saved, non-monotone = timing noise; real effect ≈ cost saved ≤ +13 bps/yr; vmq's internal band already banks it; no adoptable value, no live change; robustness/turnover_band.md) |
| ewma-vol (layer B, EWMA vs realized-window vol estimator inside vol_managed_qqq, matched pair) | 2026-07-14 | 3 (EWMA com ∈ {10 matched-pair decisive, 5, 15.67=λ0.94} through the identical band/cap path) vs the frozen realized-21 baseline | **yes — adaptive loop: targets a blind-promoted book; redteam vol_lookback plateau motivated fixing memory and testing shape** | matched pair only: median paired 12m net delta ≥ +10 bps AND win share ≥ 55% = EWMA better; ≤ −10 bps AND ≤ 45% = realized better; else keep frozen estimator (preregistrations/ewma-vol-2026-07-14.md) |

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
| 19 | EXP reversal × liquidity-shock (H-E1) | IA | measurement — **KILL** (signal-space, L1) | high-demand 21d IC +0.0069 t=0.41 ≈ dead baseline; interaction t<2 both horizons; holdout sign flips → closes NR-1's last named daily-bar angle |
| 20 | EXP MOC vs MOO fill (H-D1) | IA | execution measurement — **KILL** | net B−A paired t=0.17, overnight-gap t=1.25 (both <2), 2022+ holdout sign unstable → keep next-open, close H-D3; no live spec changed |
| 21 | EXP LW constant-corr target (H-lw-target) | IA | estimator — **KILL** | unconstrained lw_cc−identity +87bps t=+3.69 (adverse direction), holdout flips → LW-target docket closed; off-primary long-only −103bps t=−12.5 (stable) noted, not the registered book |
| 22 | EXP residual-diagonal shrink (H-idio-shrink) | IA | estimator — **INCONCLUSIVE** | pca3 unconstr vol −47bps t=−6.32 (holdout stable) BUT non-monotone in α and net Sharpe 0.79→0.69, still loses to MP → vol bought with churn; frozen monotonicity clause unmet |
| 23 | EXP-A bond-carry predictability (Discovery) | DISC | measurement — **REJECTED** (F-022) | carry coef t=1.53<2, rank-IC t=0.43, holdout sign flips; after ΔDGS10 control z-coef→t=1.05 (mechanical duration); β_SPY=−0.144; orthogonality NOT INDEPENDENT (roll_corr 0.737>0.65). No portfolio; free-data carry lane closed |
| 24 | EXP-B conditional-vol mechanism (Discovery) | DISC | mechanism — **UNSUPPORTED** (F-020 addendum) | 3/4 property signs hold & stable (vol-clustering strongest t=3.36) but 4-property model not jointly significant at cluster level (wild-cluster bootstrap p=0.44, G=5); narrows F-020 descriptively (benefit concentrates in high-premium/high-clustering equity+gold), no transportable mechanism |

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
