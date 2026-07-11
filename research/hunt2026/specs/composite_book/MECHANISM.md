# composite_book

One book from everything that survived in-house EDA, with static sleeve weights (the
GKX anti-timing lesson: diversify, never rotate). The 1.2x banded equal-weight PIT
S&P 500 core is the chassis — nobody is on the other side, it just harvests levered
equity beta plus the EW size/rebalance premium at index-fund turnover (20% relative
no-trade band per name). The 0.5x gap-drift sleeve is the alpha kicker: names with a
one-day move >= 2.5 sigma on 3x median volume keep drifting for ~60 trading days
because passive-flow anchored holders underreact to announcements; entered at close
t+1, held 60d, 5%-of-sleeve per-name cap, idle capital parked in SPY. The 0.3x SPY
panic sleeve holds cheap-to-trade index beta at ETF costs (the liquidity-provision
allocation). A whole-book gate halves gross when VIX closes >= 40 and re-enters after
5 consecutive closes < 30, trimming the left tail that kills 2x books. Gross never
exceeds 2.0. The alpha sleeve is additive, not load-bearing: the market only needs
~10-11% for the book to clear 18%.

**Falsifier (forward):** the book is long-only and levered — a flat-to-down market
year kills the return target by construction, but the design falsifier is the drift
sleeve: if post-shock 60d drift on the gap+volume events runs <= 0 net of 10 bps
costs out of sample (announcement effects now priced within days), the kicker is dead
and the book is just expensive levered beta. Secondary falsifier: a fast crash that
gaps through VIX 40 (gate too slow to save the 2x core) or repeated VIX-40 whipsaws
that lock the book at half gross through the recovery.
