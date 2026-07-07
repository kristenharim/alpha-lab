# STATE — StatArb (pairs + residual reversion)

**Stage:** 1 (pairs run on real data); residual (Avellaneda-Lee) built + tested, not yet run
**Last session:** 2026-07-07

## Scope
Two free-data-replicable StatArb methods from [[LIT — StatArb, market making & systematic factors]]:
- **Pairs (Gatev-Goetzmann-Rouwenhorst)** — form pairs by min normalized-price distance on a
  trailing window, trade the spread z-score out-of-sample on the next window.
- **Residual reversion (Avellaneda-Lee, lite)** — regress each stock on factor ETFs, trade the
  mean-reverting residual via an OU s-score.

## Built
- `bands.py` — shared entry/exit band logic (long when standardized series ≤ −entry, short ≥ +entry, flat inside exit band). Used by both methods.
- `pairs.py` — normalize, select_pairs (min SSD), `pair_zscore_oos` (formation-window stats applied OOS), pair_pnl (lagged, no look-ahead)
- `residual.py` — `residual_returns` (OLS on factors), `s_score` (standardized cumulative residual)
- `scripts/statarb_run.py` — walk-forward pairs, equal-weight, costs → scorecard
- Tests 8/8 green.

## Result — pairs (2026-07-07, 60 large caps, 2018+, 252d form / 126d trade, 20 pairs, 5bps)
**Net Sharpe −0.06, ann. −0.42%, max DD −28%, 1883 obs.** Dead.

### The story (this is the value)
First run showed **Sharpe 4.77** — impossibly good. Root cause: the spread z-score was
standardized using the *trading-window* mean/std (look-ahead — each day "knew" the window's
future mean). GGR sets the ±2σ bands from the *formation* window. Fixed via `pair_zscore_oos`;
Sharpe collapsed 4.77 → −0.06. **Matches Do & Faff (2010): pairs profitability halved post-2002,
most residual profit dies after costs.** Naive distance pairs has no edge left in liquid large caps.
The 4.77→−0.06 catch is the transferable lesson (formation-vs-trading look-ahead is THE pairs bug).

## Next
1. Run the **residual (Avellaneda-Lee)** variant — regress universe on SPY + sector ETFs, trade
   s-score reversion. A-L report Sharpe ~1.1–1.5 (decaying); test whether residual reversion
   survives where distance-pairs didn't.
2. If pairs is revisited: expand to a broader/point-in-time universe (small caps, where GGR
   found most profit) and cointegration selection instead of distance.
3. Ledoit-Wolf covariance cleaning (planned `core/` util) for a portfolio-level residual book.

## Verdict for HYP-005
Pairs: **dead-for-me on liquid large caps** (as predicted). Residual variant pending. Kristen's Stage-4 call.
