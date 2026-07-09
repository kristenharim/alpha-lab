# MEMO — Earnings blackout on the residual book: tested, rejected

**Date:** 2026-07-09
**Hypothesis:** HYP-006 — blocking new residual-reversion entries within ±2 days of a
name's earnings report improves the book (the textbook "reversion loses when the move
was informed" story).
**Verdict: rejected. No change to the live paper book.**

## Setup

- Engine: `run_residual` (the single audited path), S&P 500, same config as the
  ablation anchor (10 bps costs, $5M ADV floor, 20%/2% sector/name caps).
- Blackout mask: `filters.earnings_window_mask`, earnings dates from the cached
  yfinance pull (`data/raw/statarb_earnings.parquet`, 502 names). Coverage is dense
  only from ~2019 (yfinance's 28-quarter limit), so the honest evaluation window is
  **2019+, where coverage is 100%** — the old ablation's full-history `all_on` row
  diluted the filter with a decade it couldn't see.
- New data infrastructure this memo rode on: `core/data/earnings.py` (Nasdaq public
  calendar; EODHD's calendar endpoint 403s on the current plan). Forward-looking only —
  the backtest used the yfinance history above.

## Result (2019+)

| config | Sharpe | ann. return |
| --- | --- | --- |
| no blackout (live spec) | **2.43** | 11.7% |
| blackout ±2d | 2.42 | 11.6% |
| block pre-earnings entries only | 2.43 | — |
| block post-earnings entries only | 2.43 | — |

Book-level: noise. Per-entry counterfactual (the position-days only the unfiltered book
holds): **blocked entries earned +6.1 bps/position-day vs +0.9 bps for the average
position** (n=8,038, t=1.63). The filter removes better-than-average trades.

The pre/post split kills the intuition cleanly:

- **Pre-earnings entries** (the supposed hold-through-the-announcement disaster group):
  **+12.4 bps/pos-day** (n=1,399, t=1.29). Best-performing group in the study.
- **Post-earnings entries:** −1.2 bps/pos-day (n=4,536, t=−0.29). Zero.

## The story (this is the value)

The blackout was built for a failure mode this spec largely doesn't have. The signal
enters on a deep s-score with `skip=1`, so by the time a name qualifies "around
earnings," the announcement move has usually already happened — the book is harvesting
the post-event overreaction, which is exactly where residual reversion pays. Blocking
those entries throws away the juiciest dips the strategy exists to buy.

Caveats, both cutting the same direction:
1. Nothing here is significant (t ≤ 1.6, and same-day cross-correlation across
   positions overstates even that). There is no evidence the filter helps; there is
   weak evidence it hurts.
2. Survivorship bias specifically flatters "buy the earnings crash" — names that
   crashed on earnings and delisted aren't in the panel to punish the +12.4 bps. A
   CRSP-quality panel would shrink that number, but shrinking it does not rescue the
   filter (its best case is still ~zero marginal Sharpe).

## Disposition

- Live book: unchanged. The filter is a tested-and-rejected hypothesis.
- `core/data/earnings.py` stays: free data infrastructure, useful for live risk
  awareness and any future event signal (PEAD is the obvious customer).
- Reopen only with a materially different spec (e.g. an intraday variant that CAN
  enter before the announcement move) or a survivorship-free panel.

Repro: scratch driver mirrored `statarb_ablation_run`'s data prep and ran
`run_residual` with `blackout=` masks (`before=2, after=1`; pre-only `after=-1`;
post-only `before=0`). All inputs from the standard `data/raw/` caches.
