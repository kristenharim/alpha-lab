"""Today's target book — the live signal, reusing the backtest math verbatim.

`rolling_residual` + `band_positions` are imported UNCHANGED from the backtest, so
the live book is the backtest book by construction (the parity harness, added
before go-live, proves it bit-for-bit). Given a trailing daily price panel and the
matched factor returns, emit today's target: one signed equal-weight row per active
name, tagged with the s-score bucket the floored-premium resolver keys on.
"""
import numpy as np
import pandas as pd

from core.data.prices import daily_returns
from tracks.statarb.bands import band_positions
from tracks.statarb.residual import rolling_residual, s_score

# Bucket boundaries (spec §signal). Entry is |s|>=1.25; the two deep-long buckets
# are the survivorship-fragile trades the floored series zeroes out.
ENTRY = 1.25


def _bucket(s: float, pos: int) -> str:
    if pos < 0:
        return "short"
    if not np.isfinite(s):
        return "long_shallow"          # held long, s missing → shallowest label
    if s < -3:
        return "long_verydeep"
    if s < -2:
        return "long_deep"
    return "long_shallow"              # -2 <= s <= -entry


def _clean(x):
    """NaN/inf → None so the JSONL ledger stays valid JSON."""
    return float(x) if np.isfinite(x) else None


def target_book(prices: pd.DataFrame, factors: pd.DataFrame,
                window: int = 60, entry: float = ENTRY, exit_: float = 0.5) -> pd.DataFrame:
    """prices, factors: aligned daily panels (index=date, cols=ticker); factors[t] is
    t's matched factor return. Returns TODAY's (= last index date's) book:
    columns ticker, s_score, bucket, residual, target_weight (signed, equal-weight,
    sum|w|=1). Empty frame if no name is active."""
    rets = daily_returns(prices)
    resid = rolling_residual(rets, factors, window=window)
    s = s_score(resid, window=window)
    # stateful bands over the whole trailing window; today's held position = last row
    pos = s.apply(lambda col: band_positions(col, entry=entry, exit_=exit_))

    today_s, today_pos, today_resid = s.iloc[-1], pos.iloc[-1], resid.iloc[-1]
    active = today_pos[today_pos != 0]
    n = len(active)
    if n == 0:
        return pd.DataFrame(columns=["ticker", "s_score", "bucket", "residual", "target_weight"])

    rows = [{
        "ticker": t,
        "s_score": _clean(today_s[t]),
        "bucket": _bucket(today_s[t], int(p)),
        "residual": _clean(today_resid[t]),
        "target_weight": float(p) / n,     # signed equal weight; scaled to $ by the driver
    } for t, p in active.items()]
    return pd.DataFrame(rows)
