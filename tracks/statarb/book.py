"""The residual-reversion book: one audited code path from returns to net P&L.

`run_residual` is called by the CLI runner, the ablation sweeper, and the tests. With
all production layers off it reproduces the equal-weight formula exactly (parity gate);
the weights path is used only when a sector/name cap is active.

Signal vs P&L space (2026-07-10 engine fix): signals come from the RESIDUAL (which
subtracts the trailing alpha estimate — fine for ranking, impossible to earn), but P&L
is scored on HEDGED returns (stock minus lagged-beta x sector ETF), the return an
implementable book with an ETF hedge overlay actually realizes, charged for the
overlay's own turnover at ETF spreads.
"""
import pandas as pd

from tracks.statarb import filters as F
from tracks.statarb.bands import band_positions
from tracks.statarb.pnl import equal_weight_net
from tracks.statarb.residual import (drift_adjusted_s_score, hedged_returns, rolling_alpha,
                                     rolling_beta, rolling_residual, s_score)
from tracks.statarb.trades import extract_trades

ETF_COST_BPS = 1.0  # per-side cost on the hedge overlay; sector ETFs are pennies-wide


def overlay_cost(weights: pd.DataFrame, beta: pd.DataFrame,
                 etf_cost_bps: float = ETF_COST_BPS) -> pd.Series:
    """Turnover cost of the ETF hedge overlay implied by `weights` (per-name book
    weights) and lagged betas. Charged per name on |d(w*beta)|; conservative — ignores
    the netting of hedge legs across names sharing an ETF."""
    hedge = (weights * beta.shift(1)).fillna(0.0)
    return hedge.diff().abs().sum(axis=1) * etf_cost_bps / 1e4 * 2

SECTOR_ETF = {
    "Information Technology": "XLK", "Financials": "XLF", "Health Care": "XLV",
    "Consumer Discretionary": "XLY", "Consumer Staples": "XLP", "Energy": "XLE",
    "Industrials": "XLI", "Materials": "XLB", "Utilities": "XLU",
    "Real Estate": "XLRE", "Communication Services": "XLC",
}


def run_residual(rets, factors, sectors, *, window=60, entry=1.25, exit_=0.5, skip=1,
                 long_floor=None, cost_bps=5.0, liquidity_adv=0.0, dollar_adv=None,
                 sector_cap_=0.0, name_cap=0.0, blackout=None, features=None, pit_mask=None,
                 drift_correct=False):
    """Single audited path. All-layers-off (+ pit_mask=None) reproduces the equal-weight
    P&L exactly (parity gate); the weights path activates only when a cap is set.
    `drift_correct` swaps the entry signal for the Avellaneda-Lee modified s-score
    (drift-adjusted; the salvage variant). Returns {net, trades, resid, hedged,
    base_positions, final_positions}."""
    resid = rolling_residual(rets, factors, window=window)
    hedged = hedged_returns(rets, factors, window=window)
    beta = rolling_beta(rets, factors, window=window)
    if drift_correct:
        alpha = rolling_alpha(rets, factors, window=window)
        s = drift_adjusted_s_score(resid, alpha.shift(1), window=window)
    else:
        s = s_score(resid, window=window)
    base_positions = s.apply(lambda col: band_positions(col, entry=entry, exit_=exit_,
                                                        long_floor=long_floor))
    if pit_mask is not None:
        base_positions = base_positions.where(pit_mask, 0)

    positions = base_positions
    removed_by = {}
    if liquidity_adv and dollar_adv is not None:
        positions, rem = F.liquidity_filter(positions, dollar_adv, liquidity_adv)
        removed_by["liquidity"] = rem
    if blackout is not None:
        positions, rem = F.earnings_blackout(positions, blackout)
        removed_by["earnings"] = rem

    if sector_cap_ > 0 or name_cap > 0:
        w = F.sector_cap(F.to_weights(positions), sectors, name_cap or 1.0, sector_cap_ or 1.0)
        held = w.shift(1 + skip)
        gross = (held * hedged).sum(axis=1)
        turnover = w.diff().abs()
        cost = (turnover * cost_bps / 1e4 * 2).sum(axis=1) + overlay_cost(w, beta)
        net = (gross - cost).fillna(0)
        net = net[net.ne(0).cumsum() > 0]          # drop warm-up (equal_weight_net trims internally)
    else:
        net = equal_weight_net(positions, hedged, skip, cost_bps)
        n_active = positions.abs().sum(axis=1).replace(0, pd.NA)
        eq_w = positions.div(n_active, axis=0).fillna(0.0)
        net = net - overlay_cost(eq_w, beta).reindex(net.index).fillna(0)

    if features is None:
        features = {"volatility": rets.rolling(window).std(),
                    "volume_ratio": pd.DataFrame(1.0, index=rets.index, columns=rets.columns)}
    trades = extract_trades(base_positions, positions, resid, s, features, sectors, removed_by,
                            lag=1 + skip, pnl_rets=hedged)
    return {"net": net, "trades": trades, "resid": resid, "hedged": hedged,
            "base_positions": base_positions, "final_positions": positions}
