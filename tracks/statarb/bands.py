"""Shared entry/exit band logic for mean-reversion signals.

Given a standardized series (pair spread z-score, or residual s-score), take a
mean-reversion position: go long (+1) when the series is far BELOW zero (cheap,
expect reversion up), short (-1) when far ABOVE zero, and flatten when it returns
inside the exit band. Positions are stateful — held between crossings.

The state machine is path-dependent, so it can't be vectorized in pandas. The hot
loop is ported to C++ (core/backtest/_fastbands, via pybind11); if that extension
isn't built, we fall back to the pure-Python loop below — same signature, same
output (a parity test enforces exact equality).
"""
import pandas as pd

try:
    from core.backtest._fastbands import band_positions_c as _band_positions_c
    _HAVE_FAST = True
except ImportError:  # extension not compiled — use the pure-Python fallback
    _HAVE_FAST = False


def band_positions(series: pd.Series, entry: float = 2.0, exit_: float = 0.5,
                   long_floor: float | None = None) -> pd.Series:
    """long_floor caps how deep a LONG may go: you may only be long while the series
    is >= -long_floor. Below that (a "falling knife") you never enter, and a held long
    stops out. Default None = no floor (original behavior). Short side unaffected."""
    if _HAVE_FAST:
        floor = float("nan") if long_floor is None else float(long_floor)
        out = _band_positions_c(series.to_numpy(dtype=float), float(entry),
                                float(exit_), floor)
        return pd.Series(out, index=series.index)

    pos = 0
    out = []
    for v in series:
        if pd.isna(v):
            out.append(pos)
            continue
        too_deep = long_floor is not None and v < -long_floor
        if pos == 0:
            if v <= -entry and not too_deep:
                pos = 1
            elif v >= entry:
                pos = -1
        elif pos == 1 and too_deep:   # knife kept falling — stop out the long
            pos = 0
        elif abs(v) <= exit_:
            pos = 0
        out.append(pos)
    return pd.Series(out, index=series.index)
