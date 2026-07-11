"""Residual mean-reversion (Avellaneda & Lee 2010, lite).

Strip systematic risk by regressing each stock's returns on factor returns
(market/sector ETFs here; the paper also uses PCA), then trade the mean-reverting
idiosyncratic residual. The trading signal is the "s-score": a standardized level
of the cumulative residual, modeled as an Ornstein-Uhlenbeck process.
"""
import numpy as np
import pandas as pd


def residual_returns(stock_rets: pd.DataFrame, factor_rets: pd.DataFrame) -> pd.DataFrame:
    """OLS-regress each stock's returns on the factor returns; return residuals.

    Full-sample regression over the passed window (the runner applies it per
    trailing window). Residuals are the idiosyncratic return orthogonal to factors.
    """
    aligned = stock_rets.join(factor_rets, how="inner").dropna()
    F = aligned[factor_rets.columns].to_numpy()
    F = np.column_stack([np.ones(len(F)), F])  # intercept
    out = {}
    for col in stock_rets.columns:
        if col not in aligned:
            continue
        y = aligned[col].to_numpy()
        beta, *_ = np.linalg.lstsq(F, y, rcond=None)
        out[col] = pd.Series(y - F @ beta, index=aligned.index)
    return pd.DataFrame(out)


def rolling_beta(stock_rets: pd.DataFrame, factor_rets: pd.DataFrame,
                 window: int = 60) -> pd.DataFrame:
    """Rolling single-factor beta per name. `factor_rets` has the SAME columns as
    `stock_rets` — each column is that stock's matched factor return."""
    rs, fr = stock_rets.align(factor_rets, join="inner")
    mean_s = rs.rolling(window).mean()
    mean_f = fr.rolling(window).mean()
    cov = (rs * fr).rolling(window).mean() - mean_s * mean_f
    var = (fr * fr).rolling(window).mean() - mean_f ** 2
    return cov / var.replace(0, pd.NA)


def rolling_residual(stock_rets: pd.DataFrame, factor_rets: pd.DataFrame,
                     window: int = 60) -> pd.DataFrame:
    """Vectorized single-factor rolling residual across many stocks — the SIGNAL space.

    Betas are estimated on a trailing `window` and LAGGED one day before forming the
    residual, so no look-ahead. NOTE: the residual subtracts the trailing alpha
    estimate, which no portfolio can capture — it defines the signal, never the P&L.
    P&L must be scored on `hedged_returns`.
    """
    rs, fr = stock_rets.align(factor_rets, join="inner")
    beta = rolling_beta(rs, fr, window)
    alpha = rs.rolling(window).mean() - beta * fr.rolling(window).mean()
    resid = rs - alpha.shift(1) - beta.shift(1) * fr
    resid[beta.shift(1).isna()] = pd.NA
    return resid


def hedged_returns(stock_rets: pd.DataFrame, factor_rets: pd.DataFrame,
                   window: int = 60) -> pd.DataFrame:
    """Implementable per-name return of stock minus lagged-beta x factor ETF — the P&L
    space. Identity: hedged == residual + lagged alpha. Unlike the residual, this is
    what a real long/short book with an ETF hedge overlay actually earns (the trailing
    alpha term is each name's own drift and cannot be hedged away)."""
    rs, fr = stock_rets.align(factor_rets, join="inner")
    beta = rolling_beta(rs, fr, window)
    hedged = rs - beta.shift(1) * fr
    hedged[beta.shift(1).isna()] = pd.NA
    return hedged


def rolling_alpha(stock_rets: pd.DataFrame, factor_rets: pd.DataFrame,
                  window: int = 60) -> pd.DataFrame:
    """Rolling intercept of the single-factor regression — each name's trailing daily
    drift estimate. This is the term a hedged book earns ON TOP of the residual (and
    the drag the drift-adjusted s-score nets out of the signal)."""
    rs, fr = stock_rets.align(factor_rets, join="inner")
    beta = rolling_beta(rs, fr, window)
    return rs.rolling(window).mean() - beta * fr.rolling(window).mean()


def drift_adjusted_s_score(residual: pd.DataFrame, drift: pd.DataFrame,
                           window: int = 60) -> pd.DataFrame:
    """Avellaneda-Lee 'modified' s-score: s minus the standardized drift adjustment
    drift/(kappa*sigma), so a dislocation explained by the name's own trailing drift
    does not signal (their eq. for s_mod; zero tuned parameters). `drift` must be the
    LAGGED daily alpha estimate (caller shifts — no look-ahead). Names whose AR(1) fit
    implies no mean reversion (coefficient outside (0,1)) return NaN: untradable."""
    cum = residual.cumsum()
    x, xl = cum, cum.shift(1)
    mx, mxl = x.rolling(window).mean(), xl.rolling(window).mean()
    cov = (x * xl).rolling(window).mean() - mx * mxl
    var = (xl * xl).rolling(window).mean() - mxl ** 2
    b = cov / var.replace(0, np.nan)
    kappa = -np.log(b.where((b > 0) & (b < 1)))          # per-day reversion speed
    sd = cum.rolling(window).std().replace(0, np.nan)
    s = (cum - mx) / sd
    return s - drift / (kappa * sd)


def s_score(residual, window: int = 60):
    """s-score of a residual stream (Series or DataFrame of streams): standardize the
    cumulative residual (the OU level) over a trailing window. Negative s = residual
    cheap (buy). The single definition shared by the backtest and the live signal."""
    cum = residual.cumsum()
    mu = cum.rolling(window).mean()
    sd = cum.rolling(window).std()
    return (cum - mu) / sd.replace(0, np.nan)
