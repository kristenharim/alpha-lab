# ew_levered_vix_gate

Not an anomaly claim — an engineering claim. The return source is the equity risk
premium plus the small equal-weight-over-cap-weight rebalancing/size tilt (the lab's
most replicated finding: EW-500 posted Sharpe 1.0–1.35 in every PIT scorecard and beat
every L/S construct), levered 2x. There is nobody on the other side: no counterparty
has to lose for the risk premium to pay. The VIX gate (de-lever to 1x at VIX >= 30,
re-enter 2x after 5 consecutive closes back under, thresholds are long-history round
numbers, not fitted) exists only to cut the left tail that makes daily-rebalanced 2x
leverage path-dependent, and the 20% relative no-trade band keeps stock turnover near
index-fund levels so the 10 bps/side cost is trivial. **Falsifier:** a flat-to-down
EW S&P year fails it outright (no alpha is claimed — it needs roughly a 10%+ arithmetic
EW year to clear 18%); forward, the gate is falsified if de-lever/re-enter round trips
systematically cost more than the tail losses they avoid (whipsaw regimes where VIX
spikes above 30 without matching drawdowns), and real financing at 4-5% on the borrowed
notional erodes the levered excess that the free-margin sandbox credits.
