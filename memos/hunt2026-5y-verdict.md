# hunt2026 round 2 — 5-year backdated verdict (2026-07-10)

Follow-on to memos/hunt2026-verdict.md. Kristen's instruction: backdate the cut 5 years,
test whether the round-1 survivors still stand, and if not, return to research mode.

**Protocol.** Cut 2021-07-10. Blind window 2021-07-10 → 2026-07-10 (5.0y, 1,256 trading
days) — contains the 2022 bear (−18% SPY), the 2023-2025 bull, the Aug-2024 vol shock, and
the Apr-2025 tariff spike. Round-2 builders saw ONLY train5y.parquet (2014 → 2021-07-09);
every post-2021 file was chmod-000 during building. Specs frozen in git before unlock;
results write-once. Same harness, same costs (10/2 bps per side), gross ≤ 2x.
**Bar: net CAGR ≥ 18% over the 5 blind years.** SPY: +13.00% CAGR, Sharpe 0.80, maxDD −24.5%.

**Total trial count across the hunt: 18** (14 round-1 + 4 round-2).

## Round 1 under the 5-year stress (NOT blind on 2021-2025 — their fit window overlapped)

Only 3/14 hold 18% CAGR: vol_core_svxy +24.3%, vol_managed_qqq +23.3%, vix_panic_buyer
+21.2% — all from the vol-managed-leverage family, all with −34% to −35% drawdowns through
2022. Static levered beta (trend_gated 2x, ew_levered, composite_book) fell to 11-16% CAGR
with −40%+ drawdowns. gap_drift decayed to +12.3%/yr over 5y (the 1-year +5.8% excess did
not generalize). deep_dip_reversion collapsed to +2.1%/yr — consistent with the statarb
post-mortem, reversion at daily frequency is dead money. dual_momentum_gem: +17.9%, just
under. momentum_concentrated: +16.6% but the shallowest drawdown of the equity books (−17%).
Full table: research/hunt2026/results5y/summary.md.

## Round 2 — fully blind on all 5 years (params fit ≤ 2021-07-10, literature defaults, no grids)

| spec | CAGR | total | Sharpe | maxDD | 2021* | 2022 | 2023 | 2024 | 2025 | 2026* |
|---|---|---|---|---|---|---|---|---|---|---|
| dual_momentum_gold | **+29.1%** | +258% | 1.07 | −35.7% | +11.2% | −25.5% | +16.3% | +51.1% | +106.3% | +19.3% |
| trend_vol_qqq | **+24.7%** | +201% | 1.11 | −19.6% | +14.6% | −11.2% | +59.9% | +35.0% | +19.3% | +15.0% |
| defensive_ensemble | **+19.9%** | +148% | **1.32** | **−13.4%** | +8.1% | **+0.4%** | +11.4% | +22.3% | +45.2% | +15.3% |
| tsmom_multi_asset | +10.5% | +65% | 0.91 | −17.4% | +0.6% | **+13.7%** | −3.9% | +12.8% | +19.5% | +11.1% |
| SPY | +13.0% | +84% | 0.80 | −24.5% | +9.8% | −18.2% | +26.2% | +24.9% | +17.7% | +10.6% |

*partial years (Jul-Dec 2021, Jan-Jul 2026).

**3 of 4 pass, and the pass is qualitatively different from round 1's:** it spans a bear
year. The headline is defensive_ensemble: +19.9% CAGR at Sharpe 1.32 with a −13.4% max
drawdown — flat through 2022 while SPY lost 18% — because the TSMOM sleeve (standalone
fail, +13.7% in 2022) supplied crisis alpha exactly when the equity sleeves needed it.
The ensemble beat every sleeve's Sharpe, which is the textbook diversification result
actually showing up out-of-sample.

dual_momentum_gold has the biggest number but the ugliest path: −25.5% in 2022 (12m gate
lags fast declines; its builder pre-registered exactly this weakness) and half the 5y total
came from the 2024-2025 gold+QQQ runs. trend_vol_qqq is the robust single-asset design:
−11% in 2022 vs QQQ's −33%, positive every other year, and its round-1 sibling was also the
most robust train finding — same mechanism surviving two different eval windows.

## Honesty section (read before promoting anything)

1. **Design hindsight is not fully removable.** Round-2 *parameters* are blind to 2021-2026,
   but the *designs* were chosen by people (and an orchestrator) who know 2022 happened and
   that gold ran 2024-2026. GLD in dual_momentum_gold's menu and "must survive a bear year"
   as a design prior are 2026 knowledge. The honest reading: defensive_ensemble's shape
   (trend + vol-managed equity + cross-asset momentum) is 1970s-2012 literature and would
   plausibly have been designed in 2021; the gold-heavy menu choice is softer. Discount
   dual_momentum_gold's +29% accordingly.
2. **18 trials, one 5-year path.** Deflated for selection, the ensemble's Sharpe 1.32 is
   still comfortably positive (5y ≈ √5 more data than round 1's single year), but the CAGR
   estimate carries ±5pp/yr of standard error. The bar-clearing margin (+1.9pp) is thin.
3. **Round-1 survivors' 5y numbers are in-sample-tinted** (fit windows overlapped 2021-2025);
   only round-2 numbers deserve the word "blind".
4. Survivorship (yfinance lacks delisted names) matters little for the ETF-only round-2
   books; it tints the round-1 stock books' train fits.
5. **Finnhub key** (stored ~/.config/rimrimos/finnhub.env, not in repo): free tier has NO
   historical earnings (calendar empty in the past, surprises = last 4 quarters), so no
   backdated true-PEAD was possible. Forward use: live surprise feed for the paper book.

## Recommendation (Stage 4 gate is Kristen's)

Paper-book promotion, in order: **defensive_ensemble** (the risk-adjusted winner and the
only book that was flat in the bear), **trend_vol_qqq** (simple, robust across both eval
windows), and **momentum_concentrated** from round 1 (the stock-selection alpha: sub-market
exposure, −17% maxDD over 5y, +16.6% excess in the 1y blind test — it misses the 18% bar
but is the most credible *alpha* in the hunt). dual_momentum_gold only with the gold-
hindsight discount stated above. Track every book against exposure-matched SPY; the excess
is the number that decides at the 6-month review.

*A great backtest is a bug until proven otherwise. Two of these designs now have a blind
pass each on non-overlapping windows of different lengths — that is evidence, not proof.
The Alpaca paper book is the next court.*
