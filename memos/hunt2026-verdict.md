# hunt2026 verdict — blind-year alpha hunt (written 2026-07-10)

**Protocol.** Freeze cut 2025-07-10. All research, design, and parameter choices used only
data ≤ cut (train.parquet, 2014→cut). The holdout year (cut → 2026-07-10) was chmod-000 during
research and building, unlocked only for the one-shot evaluation; results are write-once.
Specs frozen in git (ff71245) before the holdout was touched. Shared harness for every spec:
weights at close t earn t+1 close-to-close, 10 bps/side stocks, 2 bps ETFs, gross ≤ 2x.
Filter: holdout net ≥ +18%.

**Trial count: 14.** (12 curated from 21 research candidates + the Goldberg matched pair.)
Every one is listed below — no quiet drawer.

## The one-line honest summary

**11 of 14 passed +18%, but SPY itself returned +21.2% (harness) / +22.4% (raw) and QQQ
+31.5% over the blind year — so the bar was clearable by unlevered beta.** In this draw the
filter had almost no discriminating power: any ~1.5x long book passed. The pass list is NOT
a list of edges. The exposure-matched excess column is the honest ranking.

## Full results (blind year, net of costs)

SPY same window: **+21.17%**, Sharpe 1.59, maxDD −8.9%. Benchmarks: QQQ +31.5%, IWM +34.9%.

| spec | net | Sharpe | maxDD | avg gross | beta-matched SPY | **excess** | ≥18% |
|---|---|---|---|---|---|---|---|
| dual_momentum_gem | +58.6% | 1.78 | −16.8% | 1.50 | +31.8% | **+26.8%** | PASS |
| vol_managed_qqq | +42.5% | 1.59 | −18.9% | 1.43 | +30.2% | +12.3%¹ | PASS |
| composite_book | +39.0% | 1.49 | −16.1% | 2.00 | +42.2% | −3.3% | PASS |
| gap_drift | +37.5% | 1.55 | −14.7% | 1.50 | +31.8% | **+5.8%** | PASS |
| vol_core_svxy | +36.1% | 1.31 | −19.0% | 1.76 | +37.2% | −1.1% | PASS |
| vix_panic_buyer | +36.1% | 1.61 | −15.8% | 1.55 | +32.9% | +3.2% | PASS |
| momentum_concentrated | +35.4% | 1.21 | −12.6% | 0.89 | +18.8% | **+16.6%** | PASS |
| trend_gated_spy_2x | +31.5% | 1.43 | −12.8% | 1.70 | +36.0% | −4.5% | PASS |
| breadth_gated_leverage | +28.2% | 1.36 | −17.3% | 1.43 | +30.4% | −2.1% | PASS |
| ew_levered_vix_gate | +28.2% | 1.20 | −14.8% | 1.91 | +40.4% | −12.3% | PASS |
| deep_dip_reversion | +27.6% | 1.18 | −12.2% | 1.50 | +31.8% | −4.2% | PASS |
| pca_minvar_jse | +13.0% | 0.71 | −14.8% | 2.00 | +42.3% | −29.4% | fail |
| pca_minvar_raw | +12.8% | 0.70 | −14.8% | 2.00 | +42.3% | −29.5% | fail |
| svxy_vix_carry | +5.9% | 0.42 | −16.2% | 1.00 | +21.2% | −15.3% | fail |

¹ vol_managed_qqq's proper benchmark is exposure-matched QQQ (1.43 × 31.5% ≈ +45%): against
that it is slightly *under*, i.e. its "excess" over SPY is the QQQ−SPY spread, not timing alpha.
The vol-timing kicker did not pay this particular year; its value proposition is drawdown
control across regimes (train: positive all subperiods, 2020/2022 clipped).

Quarterlies and month-by-month for every spec: `research/hunt2026/results/*.json` and
`results/summary.md`. SPY quarters: +6.7 / +2.7 / −4.4 / +14.4 (+1.1 stub). The March-2026
drawdown (−4.9% SPY month) is where books separated: deep_dip_reversion made +12.2% that
quarter (reversion paid in the selloff), momentum_concentrated +3.6%, the levered-beta books
lost 8-12%.

## What actually looks like alpha (candidates for the paper book, Kristen gates)

1. **momentum_concentrated** — +35.4% at avg 0.89x gross; +16.6% over exposure-matched SPY
   with BELOW-market exposure and the year's shallowest big-book drawdown (−12.6%).
   Cross-sectional stock selection, not leverage. Mechanism: 12-1 momentum, top-20, vol-scaled.
   Falsifier forward: 6-12 months of paper NAV underperforming exposure-matched SPY, or a
   momentum-crash month (−15%+ vs market) without the vol targeting containing it.
2. **dual_momentum_gem** — the year's best number (+58.6%, Sharpe 1.78), earned by switching
   (April +24.3% vs SPY +10.5%), beating even 1.5x QQQ (~+47%). But it is ONE position on a
   monthly switch — the estimate has enormous variance and 2022-style whipsaw is its known
   kill mode (train maxDD −41%). Falsifier: two consecutive whipsaw switches that each cost
   >5% vs buy-and-hold, or 12m paper < absolute-momentum gate's cash leg.
3. **gap_drift** — +5.8% excess from the repo's own PEAD prior at 54 avg names — the only
   stock-level *event* alpha that survived. Falsifier: excess vs 1.5x SPY ≤ 0 over 6-12
   months of paper, or event-day drift measured ≤ 0 on forward events.
4. **vix_panic_buyer** — +3.2% excess, 2.4%/day turnover, cheapest mechanism to keep running
   as an overlay. Falsifier: a spike-entry that keeps falling >10% after the add (escalation
   without recovery), repeated twice.

The other passers earned their pass from leverage in an up year (negative excess) — keep as
baselines, do not promote.

## The Goldberg / dispersion-bias matched pair (the paper-relevant result)

Identical min-var books, k=1, only the leading-eigenvector treatment differs:
**JSE +12.96% vs raw +12.81% net (+15 bps), Sharpe 0.71 vs 0.70, maxDD −14.77% vs −14.84%,
identical turnover.** Direction consistent with the theorem (correction helps, never hurt),
magnitude tiny — as expected: with k=1, long-only clipping, and a 2% name cap, the weight
vectors barely differ after the portfolio-construction pipeline flattens them. The lens is
real but this expression is too muted to measure in one year. To make the theorem bite:
k=3-5 factors (ψ̂ correction per factor), no long-only clip (market-neutral min-var or
min-var vs benchmark), tighter concentration, and multi-year windows — that is a factor_lab
→ alpha-lab bridge experiment worth its own pre-registered spec. Both books failed +18%
because defensive min-var lagged a momentum-led year at only 20% vol — the anomaly's
textbook failure regime, not evidence against the estimator.

## Deflation and other honesty

- **One blind year is one draw.** 252 daily observations put a standard error of roughly ±1.0
  on every Sharpe above; the ranking is not stable. With 14 trials against one year, the
  expected *maximum* by pure luck is large — the +58.6% top number should be read with that
  discount. Survivors are candidates for the Alpaca paper book, not proven edges.
- **The 18% bar selected exactly what it was predicted to select**: long-biased levered books
  in a +21% SPY / +31% QQQ year. The excess column, not the pass column, carries information.
- **Survivorship**: universe is PIT S&P 500 membership, but yfinance has no prices for names
  that delisted mid-sample, so train-period effect sizes are survivorship-tinted (holdout year
  much less so). Sector map is current-membership (survivorship-lite metadata).
- **Builder honesty that paid off**: builders reported their specs' known failure modes before
  the holdout (svxy_vix_carry's own brief gave it ~40-45% odds — it failed exactly as
  predicted, gap risk through a daily-close filter; breadth_gated's fragility warning showed
  up as negative excess).
- Costs were charged at 10/2 bps per side on |Δw|; leverage ≤2x enforced; no residual-space
  accounting anywhere (equal_weight_net fix, commit 92cbfad).

## Next steps (Kristen's call — Stage 4 gate)

1. Promote momentum_concentrated, dual_momentum_gem, gap_drift (+ vix_panic_buyer as overlay)
   to the Alpaca paper book — separate strategy tags, NAV marked on raw returns, exposure-
   matched SPY logged alongside so the excess is the tracked number.
2. The Goldberg bridge experiment (k>1, unconstrained min-var, pre-registered) as its own spec.
3. Data upgrades that raise the ceiling: earnings calendar key (true PEAD), Polygon/Tiingo
   (delisted names), S&P Global MCP auth (point-in-time estimates).

*House rule check: these backtests looked great; the protocol (frozen cut, locked holdout,
one shot, disclosed trials, beta-matched benchmarks) is what stands between them and the
2.67-Sharpe corpse in memos/diagnostics-2026-07-10.md. Forward paper NAV is the only next
evidence that counts.*
