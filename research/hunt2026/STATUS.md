# STATUS — hunt2026 decision dashboard (2026-07-10)

One page. Sources: TRIAL_LEDGER.md · FAILURES.md · walkforward/summary.md ·
robustness/*.md · CONFIDENCE_LADDER.md · memos/hunt2026-walkforward.md.

## Experiments

| metric | count | detail |
|---|---|---|
| Registered trials | 18 | 14 hunt-1 + 4 hunt-2 (adaptive loop flagged); effective N > 18 |
| Promoted | 4 | vol_managed_qqq, vol_core_svxy, trend_vol_qqq, defensive_ensemble |
| Alive as sleeve only | 2 | momentum_concentrated (F-015), tsmom_multi_asset (crisis alpha) |
| Watch | 3 | gap_drift (F-009), pca_minvar_jse (F-010), dual_momentum_gold (hindsight-discounted) |
| Retired | 8 | ledger #3,4,6,7,9,10,11,12 |
| Control | 1 | pca_minvar_raw (+ 3 benchmarks, not trials) |
| Failure-DB entries | 19 | F-001..F-019 (+ F-016 addendum); 5 hypothesis-level aggregates (NR-1..NR-5) |

## Hypothesis-family confidence

Stars = weight of evidence the family delivers net alpha here, not enthusiasm.

| family | conf | evidence |
|---|---|---|
| vol-management | ★★★★ | strongest family: +13.4pp/+12.4pp median WF excess, top DSRs (deflated.md); plateau-stable params |
| trend | ★★★ | +13.4pp median excess standalone (bench_qqq_sma200_2x); combo with vol is a tail hedge, not additive (F-014) |
| momentum (time-series / dual) | ★★ | crisis alpha in 2022 (tsmom); standalone below bar, WF −8.8pp median excess; gold variant discounted |
| momentum (cross-sectional) | ★ | dead in large caps post-2015: F-015 + F-016 (NR-2) |
| estimator (JSE/Goldberg) | ★★ | direction right in all 3 eval modes, magnitude ≈ noise at k=1 (F-010); real test pre-registered |
| carry (vol) | ★ | standalone failed both blinds (F-007); sanctioned only as vol_core_svxy sleeve |
| reversal | ☆ | 4 independent kills at daily bars / 10 bps (NR-1: F-001,003,004,008) |

## Promoted books

| book | ladder level | role | headline (walkforward/summary.md) |
|---|---|---|---|
| vol_managed_qqq | 3 | core compounder | +13.4pp med excess, 78% beat-SPY, worst −30.8% |
| vol_core_svxy | 3 | core alternative | +12.4pp, 85% beat-SPY, worst −31.1% |
| trend_vol_qqq | 3 | drawdown-sensitive variant | +8.0pp, worst −22.0% (best QQQ-family tail) |
| defensive_ensemble | 3 | capital preserver | +1.4pp, 84% positive, worst −18.3%, DSR 95.8% |

Ceiling: level 3 repo-wide. No cross-market replication (level 4) attempted; paper book
(level 5) not live.

## Paper book

| item | state |
|---|---|
| Pipeline stage 3 (paper trading) | **LIVE (Alpaca paper) since 2026-07-10** — Stage 4 gate given by Kristen 2026-07-10 |
| Live book set | **7 books** ~equal-weight (authoritative source: [DEPLOYMENT_MANIFEST.md](../../DEPLOYMENT_MANIFEST.md)): 4 promoted (vol_managed_qqq, vol_core_svxy, trend_vol_qqq, defensive_ensemble) + 3 **watch-tier** (dual_momentum_gold, dual_momentum_gem, momentum_concentrated) — watch-tier are live for forward evidence only, NOT promoted (F-015; gold-menu hindsight). Kristen authorized the 6-book gate, then added GEM (7th) knowingly. *(Was "6 books" — corrected 2026-07-10; the manifest is the single deployment authority.)* |
| Schedule | launchd com.rimrim.hunt2026-paper, weekdays 20:30 local, `--live`; ledgers/hunt2026/*.jsonl with exposure-matched-SPY + naive benchmarks per book |
| Governance note | first go-live (commits c25d8c4, d237d03) was pushed by a concurrent session ahead of the gate; surfaced to Kristen 2026-07-10, who ratified keeping all 6 running |
| Watch-tier kill rule | dual_momentum_gold / momentum_concentrated stay live only while forward NAV ≥ exposure-matched SPY; demote-to-flat on 2 consecutive quarters below |

## Next pre-registered experiments (RESEARCH_OBJECTS.md → PREREGISTRATION.md)

| exp | layer | why |
|---|---|---|
| JSE k=3-5 unconstrained min-var, walk-forward | B | Goldberg program's real test (F-010 answered direction only) |
| open+close execution in harness | D | reopens overnight premium (F-006) |
| no-trade-band turnover sweep, vol-managed family | C | cheapest possible net-return improvement on the core books |
| EWMA vs realized vol in vol_managed_qqq | B | matched pair, one layer |
