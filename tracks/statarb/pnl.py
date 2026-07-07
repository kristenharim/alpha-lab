"""The audited equal-weight, dollar-neutral, net-of-cost P&L series.

This is the ONE formula that produces the headline 2.67. Both the backtest (`run_residual`) and the ML
gated backtest call it, so a gated book's Sharpe comes from the exact same path as the headline number,
not a reconstruction. Lives in the installed package (not scripts/) so every venv and the notebook can
import it.
"""
import pandas as pd


def equal_weight_net(positions: pd.DataFrame, resid: pd.DataFrame,
                     skip: int, cost_bps: float) -> pd.Series:
    held = positions.shift(1 + skip)
    n_active = held.abs().sum(axis=1).replace(0, pd.NA)
    gross = (held * resid).sum(axis=1) / n_active
    turnover = positions.diff().abs()
    cost = (turnover * cost_bps / 1e4 * 2).sum(axis=1) / n_active
    net = (gross - cost).fillna(0)
    return net[net.ne(0).cumsum() > 0]
