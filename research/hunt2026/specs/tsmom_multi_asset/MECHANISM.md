# tsmom_multi_asset — mechanism

Time-series momentum (Moskowitz-Ooi-Pedersen 2012): slow-moving capital plus
investor underreaction to news and subsequent herding sustain multi-month
positive autocorrelation in asset-class returns; hedgers and rebalancers who
trade against the trend are on the other side. The strategy is simply long that
autocorrelation across 15 ETFs spanning equities, bonds, credit, commodities,
FX, and REITs — inverse-vol sized, 15% portfolio vol target, monthly rebalance.
MOP document Sharpe ~1 on 58 futures over 1985-2009, fully out-of-sample to our
2021-07-10 design date; every parameter (12m lookback, ex-ante vol sizing, vol
target) is their default, nothing fit here. Its crisis-alpha profile — it ends
up short whatever grinds down (e.g. short TLT in a rate-rise, short equities in
a slow bear) — is the diversifier a levered-beta book lacks.

**Falsifier:** if forward 12m-sign hit rates across the menu drop to ~50% and
the book underperforms a 15%-vol scaled 60/40 over a full 2-3yr cycle that
includes a sustained trend (i.e. it fails even when trends exist, not just in
a choppy year), the autocorrelation premise is dead and the spec should be
killed.
