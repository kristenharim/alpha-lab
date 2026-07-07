"""Signal-parity harness (spec non-negotiable, the pre-go-live gate).

"Same function" does not guarantee "same numbers" once the signal is fed a live, GROWING panel instead
of the cached backtest panel: look-ahead can sneak in through timing, session boundaries, or the rolling
window's warm-up on a shorter panel. This proves, on sampled historical dates, that `target_book` fed a
panel FROZEN at date d reproduces the book computed over the FULL panel at d, bit-for-bit (same tickers,
same signed weights, same buckets). A silent parity break makes every live-vs-backtest comparison
meaningless, so this gate must pass before any live run is permitted.
"""
import pandas as pd

from core.data.prices import daily_returns
from tracks.statarb.bands import band_positions
from tracks.statarb.paper.signal import _bucket, target_book
from tracks.statarb.residual import rolling_residual


def book_at(prices: pd.DataFrame, factors: pd.DataFrame, date, window: int = 60,
            entry: float = 1.25, exit_: float = 0.5) -> dict:
    """Reference book for `date`, computed over the FULL panel then sliced to that row:
    {ticker: (signed_weight, bucket)}."""
    rets = daily_returns(prices)
    resid = rolling_residual(rets, factors, window=window)
    cum = resid.cumsum()
    s = (cum - cum.rolling(window).mean()) / cum.rolling(window).std()
    pos = s.apply(lambda c: band_positions(c, entry=entry, exit_=exit_))
    row, srow = pos.loc[date], s.loc[date]
    active = row[row != 0]
    n = len(active)
    return {t: (float(p) / n, _bucket(srow[t], int(p))) for t, p in active.items()}


def parity_mismatches(prices: pd.DataFrame, factors: pd.DataFrame, dates,
                      window: int = 60, entry: float = 1.25, exit_: float = 0.5,
                      tol: float = 1e-9) -> list:
    """Dates where the frozen-panel live book differs from the full-panel reference book.
    Empty list == parity holds == the gate passes."""
    bad = []
    for d in dates:
        live = target_book(prices.loc[:d], factors.loc[:d], window=window, entry=entry, exit_=exit_)
        live_map = {r.ticker: (r.target_weight, r.bucket) for r in live.itertuples()}
        ref = book_at(prices, factors, d, window=window, entry=entry, exit_=exit_)
        same = set(live_map) == set(ref) and all(
            abs(live_map[t][0] - ref[t][0]) <= tol and live_map[t][1] == ref[t][1]
            for t in live_map)
        if not same:
            bad.append(d)
    return bad
