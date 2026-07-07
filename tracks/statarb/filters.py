"""Composable production layers for the residual-reversion book.

Each filter is a pure function of the positions matrix plus pre-built context (no network). Filters
that gate entries return (filtered_positions, removed_mask) so the signal log can attribute why a
candidate was skipped. Sector-cap operates on a weights matrix (see to_weights) because it reshapes
exposure, not membership.
"""
import pandas as pd


def liquidity_filter(positions: pd.DataFrame, dollar_adv: pd.DataFrame,
                     min_adv: float) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Force flat any name whose trailing dollar-ADV is below min_adv that day."""
    adv = dollar_adv.reindex_like(positions)
    illiquid = adv < min_adv
    removed = (positions != 0) & illiquid
    return positions.mask(illiquid, 0), removed


def earnings_window_mask(index: pd.DatetimeIndex, earnings: pd.DataFrame,
                         before: int, after: int, columns: list[str]) -> pd.DataFrame:
    """Bool mask: True on trading days within [-before, +after] of a ticker's earnings."""
    mask = pd.DataFrame(False, index=index, columns=columns)
    for t, d in zip(earnings["ticker"], pd.to_datetime(earnings["date"])):
        if t not in mask.columns:
            continue
        loc = index.searchsorted(d)          # first trading day at/after the earnings date
        col = mask.columns.get_loc(t)
        for j in range(loc - before, loc + after + 1):
            if 0 <= j < len(index):
                mask.iat[j, col] = True
    return mask


def _blackout_col(pos_col: list, blackout_col: list) -> list:
    prev, out = 0, []
    for p, b in zip(pos_col, blackout_col):
        if b and prev == 0 and p != 0:       # would be a NEW entry inside the window -> block
            p = 0
        out.append(p)
        prev = p
    return out


def earnings_blackout(positions: pd.DataFrame,
                      blackout: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Block new entries during each name's blackout window; hold existing normally."""
    bo = blackout.reindex_like(positions).fillna(False)
    out = {c: _blackout_col(positions[c].tolist(), bo[c].tolist()) for c in positions.columns}
    filtered = pd.DataFrame(out, index=positions.index)
    removed = (positions != 0) & (filtered == 0)
    return filtered, removed


def to_weights(positions: pd.DataFrame) -> pd.DataFrame:
    """Equal-weight, dollar-neutral: row-normalize positions to gross exposure 1."""
    gross = positions.abs().sum(axis=1).replace(0, pd.NA)
    return positions.div(gross, axis=0).fillna(0.0)


def _apply_caps(weights: pd.DataFrame, sectors: dict,
                name_cap: float, sector_cap_: float) -> pd.DataFrame:
    w = weights.clip(lower=-name_cap, upper=name_cap)
    sec = pd.Series(sectors).reindex(w.columns)
    for s in sec.dropna().unique():
        cols = sec[sec == s].index
        net = w[cols].sum(axis=1)
        scale = (sector_cap_ / net.abs()).clip(upper=1.0).where(net.abs() > sector_cap_, 1.0)
        w[cols] = w[cols].mul(scale, axis=0)
    return w


def sector_cap(weights: pd.DataFrame, sectors: dict,
               name_cap: float, sector_cap_: float) -> pd.DataFrame:
    """Clip single-name and per-sector net exposure, then renormalize each row to gross 1."""
    w = _apply_caps(weights, sectors, name_cap, sector_cap_)
    gross = w.abs().sum(axis=1).replace(0, pd.NA)
    return w.div(gross, axis=0).fillna(0.0)
