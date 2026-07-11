# defensive_ensemble

Three documented premia with low pairwise correlation, combined at equal risk and
vol-targeted. Sleeve A harvests the equity premium at managed risk (Moreira-Muir 2017:
scaling exposure by inverse realized variance improves Sharpe because vol is
persistent but the premium is not proportionally higher in high-vol states), gated by
a 200d trend filter that has historically sidestepped the deep-drawdown regimes.
Sleeve B is cross-asset 12-month time-series momentum (Moskowitz-Ooi-Pedersen 2012):
the other side is investors who under-react to slow-moving macro information and
rebalance mechanically against trends; it is long bonds/gold/dollar in equity bear
years, which is exactly when Sleeve A is flat. Sleeve C is Antonacci-style dual
momentum, a regime switch into the strongest risk asset or into duration/cash. Because
the sleeves' Sharpe ratios survive on different return sources, the ensemble's Sharpe
exceeds any single sleeve's, so a vol target calibrated to ~18%/yr needs less leverage
than a single levered beta and survives the bear year that kills single-beta books.
All costs are ETF-cheap (2 bps/side) and rebalancing is mostly monthly.

**Falsifier:** realized pairwise sleeve correlations > 0.7 in a stress quarter
(diversification failure — the sleeves have become one levered beta), or 12 months of
paper trading below BIL.
