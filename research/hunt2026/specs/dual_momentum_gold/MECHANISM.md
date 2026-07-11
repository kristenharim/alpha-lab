# dual_momentum_gold

Antonacci dual momentum, generalized on both legs. Relative momentum picks the
strongest 12-month trend among SPY/QQQ/GLD — gold is the non-equity absolute-momentum
leg (Antonacci's own extensions), so the book can earn in regimes where equities and
bonds both stall. Absolute momentum (winner must beat BIL's 12-month return) steps the
book aside in bears. The defensive leg is itself momentum-picked between TLT and BIL:
in a rising-rate regime long bonds fail as the safe asset (visible in 2013/2018), so
TLT is never hardcoded. The other side is investors who rebalance against 12-month
trends (target-weight rebalancers, mean-reversion capital), plus the behavioral
underreaction that sustains time-series momentum; 1.5x on the risk leg pushes a
positive-expectancy, crash-gated stream toward the CAGR bar without a levered beta
that dies in a bear. All parameters are literature defaults (252d lookback, monthly
rebalance); nothing was fit.

**Falsifier:** two consecutive switch months that each cost >5% versus buy-and-hold
of the abandoned asset — a whipsaw regime where 12-month trend reverses faster than
monthly rebalancing can follow. That kills the signal, not just the sizing.
