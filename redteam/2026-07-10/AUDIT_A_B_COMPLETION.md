# Red-Team Audits A (Perturbation) & B (Regime/Tail) — Completion (2026-07-11)

Harvested and reproduced from the dead fleet's on-disk code (Agent 6 `runner.py`,
Agent 7 `regime_analysis.py` + saved tables). Read-only; no spec/manifest/deployment change.
Audits C (adversarial) and D (6-book clean-room) + the stock-universe repair remain open.

## Audit A — Perturbation robustness (292 non-leverage variants across 7 books)

Metric = degradation of benchmark-relative excess vs each book's base, per predeclared
symmetric perturbation (costs ½/2×/4×, 1–2 day signal/exec delay, missed rebalance, random
missed trades, ±20% params, alt start dates, alt universe, whole-shares, leverage ×0.75/0.5).

| statistic | value | reading |
|---|---|---|
| median degradation | **−0.001** | books are near-invariant to typical perturbation |
| fraction within −0.10 of base | **82%** | robust majority |
| worst degradation | **−2.01** | `missobs_2pct` (drop 2% of price obs) |

**Verdict: SURVIVES with two bounded caveats.**
1. **Execution perturbations are immaterial** — cost 2–4×, delays, partial/missed fills, alt
   start/universe all sit in the robust 82%. Confirms the low-turnover vol family is
   insensitive to execution assumptions (corroborates the earlier holdout stress: total-net
   [0.401, 0.423] under stress vs 0.408 base).
2. **Missing-observation sensitivity is the real fragility** — dropping 2% of daily prices
   degrades excess by up to −2.0. This is a **data-quality**, not execution, failure mode,
   and it ties directly to **F-RT-03** (the momentum_concentrated NaN-universe problem). Low
   risk for the 6 ETF books (ETF prints rarely missing); a genuine concern for the stock book.
3. **One param is cliff-ish** — `param_lb-20` (lookback −20%) cost −1.79 for one momentum
   book; most ±20% param variants are in the robust band. Consistent with the earlier
   parameter-stability finding (vol_managed on a plateau; momentum/trend have some jumpy
   cells). Not disqualifying; the frozen param is not re-picked.
Leverage-reduction degradation (×0.5 → −0.18 to −1.6) is **mechanical** (halving leverage
halves levered excess), not a robustness failure — excluded from the statistic above.

## Audit B — Regime & tail concentration

### Does one period explain the returns? (concentration_table.csv)
- **Holdout year (W1) returns are single-month-concentrated:** best-month share
  vol_managed_qqq **0.46**, vol_core_svxy **0.53**, dual_momentum_gem **0.47** — roughly half
  of the 1-year return came from one month (the April-2026 recovery, per the monthly tables).
  **MEDIUM caveat: the +18% holdout pass leaned heavily on one strong month.**
- **5-year (W2) returns are spread across years** (best-month share 0.10–0.26) — but the
  levered books' 2022 is deeply negative (vol_managed 2022 log −0.37, gold −0.29, gem −0.36)
  and the recovery concentrates in 2023/2025.
- **dual_momentum_gold's edge is concentrated: rel_top10 = 0.68** (68% of its
  benchmark-relative return from its top 10 months; 2025 rel +0.59). **Independently confirms
  F-020 (gold = 2024–25 regime artifact) from a third angle.**

### Tail behavior in known stress episodes (stress_episode_table.csv, book/benchmark)
| episode | vol_managed | vol_core_svxy | trend_vol_qqq | defensive_ens | gold | gem |
|---|---|---|---|---|---|---|
| 2022-04-19 (bear onset) | **−12.8%** | **−15.7%** | **+0.1%** | **−0.3%** | −13.4% | −12.2% |
| 2022-09-19 | −2.9% | −2.0% | +0.2% | +0.6% | +0.2% | **−9.7%** |
| 2025-03-27 (gold spike) | −3.8% | −4.5% | +0.4% | **+4.7%** | **+15.1%** | −4.5% |

**Verdict: mechanisms match their stated roles.**
- **trend_vol_qqq and defensive_ensemble genuinely protect in the bear onset** (+0.1% / −0.3%
  while levered books lost 13–16%) — validates the tail-hedge (F-014) and capital-preserver
  labels with independent regime evidence.
- **The levered vol books (vol_managed, vol_core, gem) carry real bear-market tail risk**
  (−12 to −16% in the 2022 onset) that full-period Sharpe hides. Not a defect — it is the
  disclosed levered-beta risk — but it means their forward drawdowns will be large in a bear.
- **gem's single-position concentration bites** (−9.7% on 2022-09-19, worst of the roster
  that day) — the known whipsaw fragility.

## Net effect on beliefs
No belief overturned; three prior conclusions **independently corroborated** (F-014 tail
hedge, F-020 gold artifact, levered-beta tail risk). One **new bounded caveat**: the holdout
year's pass was ~half one month, and the books degrade under missing-observation rate — both
argue for weighting the 5-year and forward evidence over the single holdout year.

## Still open (next audit, needs budget or targeted in-session runs)
- Audit C (adversarial implementation: prev-close / next-open / conservative fills).
- Audit D (clean-room for the 6 non-vol_managed books — Agent 8's driver had a groupby bug).
- Stock-universe repair project (permanent ID mapping; F-RT-03) → then re-run IC screen +
  momentum_concentrated as a **new** frozen trial, retaining the original blocked verdict.
