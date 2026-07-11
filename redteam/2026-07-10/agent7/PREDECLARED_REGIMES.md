# Agent 7 — PREDECLARED regime definitions and concentration metrics
Declared 2026-07-10, BEFORE computing any regime-conditional results.
Commit audited: ffb5778. Written before any run of the analysis script.

## Data and windows
- Panel: train5y.parquet + holdout5y.parquet (checksums verified vs SCOPE.md).
- Windows: W1 = 1y blind holdout (2025-07-10, 2026-07-10]; W2 = 5y (2021-07-10, 2026-07-10].
  Round-1 books (vol_managed_qqq, vol_core_svxy, dual_momentum_gem, momentum_concentrated)
  are NOT blind on W2 (fit windows overlapped) — W2 regime numbers for them are
  stress-test attribution, not blind evidence. Round-2 books (trend_vol_qqq,
  defensive_ensemble, dual_momentum_gold) are blind on W2.
- Book returns: frozen harness.run() on the frozen specs (I am not the engine auditor;
  engine correctness is assumed here and flagged as a dependency).

## Regime labels — all computed from panel closes at day t, applied to the return of day t+1
(matches the harness held = W.shift(1) convention; no look-ahead)

- R1 TREND: bull if SPY close >= SMA200(SPY close) at t, else bear.
- R2 VOL: low if ^VIX close < 20 at t; high if 20 <= VIX < 30; crisis if VIX >= 30.
- R3 RATES: falling if IEF 63d total return > 0 at t, else rising.
- R4 INFLATION proxy: rising breakevens if (TIP 126d ret − IEF 126d ret) > 0 at t, else falling.
  (No CPI in panel; this is the only time-observable inflation proxy available.)
- R5 CREDIT/LIQUIDITY proxy: risk-on if (HYG 63d ret − IEF 63d ret) > 0 at t, else risk-off.
- R6 TREND PERSISTENCE: persistent if sign(SPY 63d ret) == sign(SPY 252d ret) at t, else choppy.
- R7 STRESS EPISODES: maximal contiguous runs of R2==crisis (VIX>=30), padded ±5 trading
  days, merged if gaps < 10 trading days. Reported as event windows with dates.

No other regime definitions will be added after results are seen. If a regime has < 15
days in a window, its Sharpe is not reported (n too small), only its summed contribution.

## Benchmarks (per DEPLOYMENT_MANIFEST.md naive bench)
- vol_managed_qqq, vol_core_svxy, trend_vol_qqq: QQQ buy-and-hold (harness convention, 2bps entry).
- defensive_ensemble: 60/40 SPY/BIL, monthly-rebalanced via harness.
- dual_momentum_gold, dual_momentum_gem, momentum_concentrated: SPY buy-and-hold.
- SPY buy-and-hold reported for all books as a common yardstick.

## Concentration metrics (predeclared)
- C1: share of window total log net return contributed by top 5 / 10 / 20 daily returns;
  same for daily benchmark-relative return (book net − bench net).
- C2: best single month's share of total net log return; HHI of positive monthly contributions.
- C3 (W2 only): calendar-year decomposition of net and benchmark-relative return;
  flag if any single year > 50% of the 5y benchmark-relative sum.
- C4: per regime — trading-day count, % of days, summed log net return, summed
  benchmark-relative return, annualized Sharpe (if n >= 15), and share of the max
  drawdown path (sum of negative daily log returns inside the book's max-DD window, by regime).
- C5: minimum k such that replacing the book's k best benchmark-relative days with the
  benchmark's return flips the window's benchmark-relative total to <= 0.

## Mechanism tests (declared)
- M1 vol_managed_qqq / vol_core_svxy / trend_vol_qqq: mechanism says levered in calm, small
  in high vol. Check avg gross exposure by R2 bucket; winning regime should be R2=low.
  A large positive contribution from R2=crisis would contradict the stated mechanism.
- M2 defensive_ensemble: mechanism says survives bear years; check R1=bear contribution
  vs 60/40 bench.
- M3 dual momentum books: mechanism says absolute-momentum gate steps aside in bears;
  check R1=bear exposure and contribution.
- M4 momentum_concentrated: de-levers below SPY SMA200; check gross exposure in R1=bear.
- Also: state what fraction of the 1y blind window falls in each regime — if bear/crisis
  coverage in the blind window is ~0, the blind year is declared uninformative about
  those regimes (evidence gap, not a bug).
