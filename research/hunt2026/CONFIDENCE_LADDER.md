# Confidence ladder — how much we believe each result, and why

Two separate axes. **ROBUSTNESS** (the ladder): how hard has this result been to kill.
**ECONOMIC VALUE** (the scorecard): even if real, is it worth running. A spec can be
level-3 robust and economically near-worthless (see trend_vol_qqq's F-014 attribution).

## The ladder (robustness axis)

| Level | Name | Bar |
|---|---|---|
| 0 | Untested idea | Written down, no data touched |
| 1 | Literature-replicated | Mechanism reproduced on train data, matches published direction |
| 2 | Single blind pass | Passed one pre-registered holdout (1y or 5y blind) |
| 3 | Multiple walk-forward passes | Positive median excess and role confirmed across the 82-window walk-forward (walkforward/summary.md) |
| 4 | Cross-market replication | Same mechanism works on a different universe/asset class/data vendor |
| 5 | Live paper success | Beat its naive benchmark on the Alpaca paper book over a pre-registered horizon |
| 6 | Live capital | Survived real money |

A spec sits at the highest level whose evidence still stands. Later evidence can demote
(momentum_concentrated passed a blind but the walk-forward refuted generalization → capped
below 3). **Nothing in this repo is above level 3, and the vol-managed family is capped
there with a penalty:** cross-market replication was RUN and FAILED (F-020 — the mechanism
improves Sharpe in only 3/7 correlation clusters, p=0.77), so level 4 is not merely
unattempted, it was tested and refused. The edge is confirmed as US-large-cap-equity-
specific, not universal. The paper book is designed but not live
(robustness/xmarket.md; memos/hunt2026-walkforward.md).

## Current placement — every TRIAL_LEDGER.md row

Evidence sources: TRIAL_LEDGER.md (status), walkforward/summary.md (WF numbers),
FAILURES.md (F-xxx), robustness/deflated.md (DSR).

| # | spec | level | justification |
|---|---|---|---|
| 1 | vol_managed_qqq | **3** | 1y blind pass + 82-window WF: +13.4pp median excess, 78% beat-SPY; DSR 81.5% |
| 2 | vol_core_svxy | **3** | 1y blind pass + WF: +12.4pp median excess, 85% beat-SPY (5y window not blind) |
| 3 | breadth_gated_leverage | retired | param-fragile, WF worst −44.5%; static-leverage pattern killed (F-011) |
| 4 | trend_gated_spy_2x | retired | −40% DD class, superseded by trend_vol_qqq (F-011) |
| 5 | momentum_concentrated | **2 (capped, sleeve-only)** | 1y blind excess pass stands as a draw; WF −4.6pp median excess (F-015) + dead rank IC (F-016) block level 3 |
| 6 | dual_momentum_gem | retired | 1y star was whipsaw-favorable; WF +9.3pp but retired for fragility (ledger #6, F-012) |
| 7 | svxy_vix_carry | retired | failed both blinds, gap risk as pre-registered (F-007) |
| 8 | gap_drift | **2 (watch)** | 1y blind +5.8% excess pass; 5y decay + WF worst −53.4% block promotion (F-009) |
| 9 | ew_levered_vix_gate | retired | negative 1y excess; static leverage (F-011) |
| 10 | deep_dip_reversion | retired | 5y +2.1%, confirms reversal cost trap (F-008, negative-result registry NR-1) |
| 11 | vix_panic_buyer | retired | WF found −62.1% GFC window; blind windows just lacked a cascade (F-013) |
| 12 | composite_book | retired | beta in a costume, −44% DD (ledger #12, F-011) |
| 13 | pca_minvar_raw | control | kept only as the Goldberg pair baseline; retired as a default (F-010) |
| 14 | pca_minvar_jse | **1 (watch)** | direction (JSE ≥ raw) right in all 3 eval modes but delta ≈ noise at k=1 long-only (F-010); k=3-5 is the registered real test |
| 15 | tsmom_multi_asset | **2 (sleeve-only)** | 5y blind ran clean but standalone below bar (+10.5%); value is 2022 crisis alpha (+13.7%); WF −8.8pp median excess blocks standalone |
| 16 | trend_vol_qqq | **3** | 5y blind +24.7% + WF best-in-family tail (worst −22.0%); F-014 caps the *value* claim, not the robustness |
| 17 | dual_momentum_gold | **2 (discounted)** | 5y blind +29.1% but gold-menu design was hindsight-tinted (ledger hunt-2 flag); WF +6.9pp median excess unremarkable |
| 18 | defensive_ensemble | **3** | 5y blind pass + WF role-confirm as capital preserver: 84% positive, worst −18.3%, DSR 95.8% |

Benchmarks (SPY, bench_qqq_buyhold, bench_qqq_sma200_2x) are controls, not laddered.

## Economic value scorecard — promoted books only

Robustness says "real"; this says "worth it". 1-5 each, 5 best. Promoted list per
memos/hunt2026-walkforward.md (Stage 4 gate: Kristen).

Definitions:
- **Value vs naive**: median WF excess over the book's own naive benchmark (not SPY).
- **Capacity**: how much money the expression absorbs before eating itself.
- **Complexity**: fewer moving parts = higher score (each part is a place to be wrong).
- **Uniqueness**: is this crowded/published or ours.

| book | value vs naive | capacity | complexity | uniqueness | reading |
|---|---|---|---|---|---|
| vol_managed_qqq | **4** — +13.4pp vs SPY, +8.1pp vs bench_qqq_buyhold's +5.3pp | **5** — QQQ + cash | **5** — one estimator, one knob, plateau-stable (robustness/param_maps.md) | **1** — textbook vol targeting | best value-per-part; the alpha is mostly "vol-managed beta", which is fine and priced honestly |
| vol_core_svxy | **4** — +12.4pp, 85% beat-SPY, highest hit rate | **3** — SVXY sleeve is capacity- and gap-limited (F-007 heritage) | **3** — core + carry sleeve, two estimators | **2** — VRP harvesting is published but the gated-sleeve expression is ours | carry sleeve buys hit rate with gap risk; only sanctioned SVXY expression |
| trend_vol_qqq | **2** — F-014: +8.0pp median vs +13.4pp for either naive parent; the combo is a priced tail hedge, not additive alpha | **5** — QQQ + cash | **4** — two estimators, hysteresis | **1** — trend + vol targeting, fully published | buy it for the −22% worst window, never for the median |
| defensive_ensemble | **2** — +1.4pp median excess; value lives in the drawdown column (worst −18.3%, 84% positive) | **5** — liquid ETFs | **3** — multi-sleeve, monthly inverse-vol | **2** — diversified-premia recipe, sleeve mix is ours | capital preserver, not an 18% machine (memos/hunt2026-walkforward.md pt 4) |

Promotion to level 5 requires: a pre-registered paper-book horizon and benchmark delta
recorded in PREREGISTRATION.md format BEFORE the book goes live.
