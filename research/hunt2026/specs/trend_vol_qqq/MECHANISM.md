# trend_vol_qqq — trend-gated vol-targeted QQQ

Composition of two pre-2012 literature mechanisms, fit-free. Vol targeting harvests the
equity premium at constant risk: weight = min(2, sigma_target / rv21), which levers up in
calm markets and de-levers in turbulent ones (Moreira-Muir 2017; the negative
vol-of-vol/return relation was documented well before). The other side is investors who
hold constant dollar exposure and therefore hold too much risk exactly when risk is
expensive. Its known weak regime is a slow grind-down where vol stays moderate but drift
is negative — vol-managed books sit ~1x long through those. The 200d SMA trend gate
(Faber 2007) removes precisely that regime: below trend the book moves to BIL. A 1%
hysteresis band on the SMA cross and a 0.05 no-trade band on weights cut whipsaw turnover.
Both mechanisms were published a decade before the blind window; parameters are the
literature defaults (200d, 25% target, 21d vol), no grid search.

**Falsifier:** a V-shaped crash-recovery year where the gate whipsaws twice, each round
trip costing >5% vs the ungated vol-targeted book — that would show the trend gate
destroys more than the grind-down protection is worth going forward.
