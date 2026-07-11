# gap_drift — mechanism

Post-earnings-announcement drift: investors anchor on pre-announcement expectations and
update slowly, so a large positive surprise keeps paying for ~60 trading days. The other
side is the anchoring crowd plus passive/index flow that ignores firm-level news. We detect
the announcement with free data only — a 1d return >= 2.5 trailing-60d sigmas confirmed by
volume >= 3x the trailing 20d median — enter at the next close (skip-1), equal-weight all
live events with a 5% per-name cap, hold 60 trading days, park idle capital in SPY, and run
the book at 1.5x gross. The edge persists because harvesting it means warehousing
single-name event risk for 60 days, which fast money will not hold and slow money does not
screen for. In-house evidence: +8.2-8.5% 60d top-minus-bottom CAR on 530 events, monotone
in horizon; event-window entries were the best trades in the statarb log.

**Falsifier (forward):** the post-event long leg stops beating SPY over the 60d window —
if a rolling 12-month event-level average excess return vs SPY goes <= 0 (or the strategy's
excess over 1.5x SPY is negative for two consecutive quarters with >= 20 events live), the
underreaction has been arbitraged away or the gap+volume proxy is catching noise, and the
spec is dead.
