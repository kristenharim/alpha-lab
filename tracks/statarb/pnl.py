"""The audited equal-weight, dollar-neutral, net-of-cost P&L series.

This is the single P&L formula behind the headline backtest result. Both the backtest
(`run_residual`) and the ML-gated backtest call it, so a gated book's Sharpe comes from the same
code path as the headline number, not a reconstruction. `rets` must be the IMPLEMENTABLE return
matrix (see tracks/statarb/residual.hedged_returns) — scoring on the residual itself would credit
the book with the unhedgeable trailing-alpha term (2026-07-10 engine fix).
"""
import pandas as pd


def equal_weight_net(positions: pd.DataFrame, rets: pd.DataFrame,
                     skip: int, cost_bps: float) -> pd.Series:
    held = positions.shift(1 + skip)
    n_active = held.abs().sum(axis=1).replace(0, pd.NA)
    gross = (held * rets).sum(axis=1) / n_active
    turnover = positions.diff().abs()
    cost = (turnover * cost_bps / 1e4 * 2).sum(axis=1) / n_active
    net = (gross - cost).fillna(0)
    return net[net.ne(0).cumsum() > 0]
