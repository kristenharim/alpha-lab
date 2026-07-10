"""PC factor-timing — the revival variant of the GKX signal-rotation track (HYP-004).

The rotation study forecast all ~200 individual anomaly long-shorts and rotated toward the
predicted winners; it LOST to equal-weighting the zoo (0.78 vs 2.10, see gkx STATE.md). The
post-mortem's fix: richer conditioning with fewer degrees of freedom. This module does that —
compress the panel with PCA and time only the top few principal components (the dominant common
factors), then map the timed tilt back to a tradable book in signal space.

THE look-ahead trap (flagged in the vault HYP-004 note): PCA loadings MUST be fit on the trailing
window only. `rolling_pc_returns` refits PCA on an expanding window at each annual refit and projects
each out-of-sample month onto PAST loadings using the fitted (training) mean — a month's PC value
never enters its own fit, and no future month does either. The timing layer on top reuses the track's
`expanding_window_predict`, itself strictly out-of-sample.

Honest caveat: PCA sign/identity can drift across refits. Signs are anchored deterministically (each
component flipped to sum positive) and components stay variance-ordered, but a component's economic
identity may still rotate at a refit boundary; the momentum features on the PC series treat that as
noise. Documented, not hidden.
"""
import numpy as np
import pandas as pd

from tracks.gkx.cz_data import validate_panel


def to_wide(panel: pd.DataFrame) -> pd.DataFrame:
    """Long CZ panel -> date x signal return matrix, sorted by date."""
    return validate_panel(panel).pivot_table(index="date", columns="signalname", values="ret").sort_index()


def rolling_pc_returns(wide: pd.DataFrame, k: int = 10, min_train: int = 60,
                       refit_every: int = 12) -> tuple[pd.DataFrame, dict, pd.Index]:
    """Trailing-only rolling PCA over the signal-return matrix.

    Returns (pc_panel_long, loadings_by_date, signal_cols):
      - pc_panel_long: long DataFrame [date, signalname('pc0'..'pc{k-1}'), ret] of OOS-projected
        principal-component returns, ready for `expanding_window_predict`.
      - loadings_by_date: {date -> DataFrame(index pc ids, columns signals)} the loadings active on
        that date (used to map a PC tilt back to signal weights).
      - signal_cols: the signals spanned (those present across the whole window; PCA needs a full matrix).
    """
    from sklearn.decomposition import PCA

    wide = wide.dropna(axis=1, how="any")               # PCA needs a complete matrix
    if wide.shape[1] < 2:
        raise ValueError("need >=2 signals with full history for PCA")
    months = list(wide.index)
    kk = min(k, wide.shape[1])
    components = mean_ = None
    loadings_by_date: dict = {}
    rows = []
    for i in range(min_train, len(months)):
        if components is None or (i - min_train) % refit_every == 0:
            pca = PCA(n_components=kk).fit(wide.iloc[:i].values)   # strictly before month i
            comp = pca.components_.copy()
            comp *= np.where(comp.sum(axis=1) < 0, -1.0, 1.0)[:, None]  # deterministic sign anchor
            components, mean_ = comp, pca.mean_.copy()
        d = months[i]
        pc_ret = components @ (wide.iloc[i].values - mean_)         # project this month onto past loadings
        rows += [{"date": d, "signalname": f"pc{j}", "ret": float(pc_ret[j])} for j in range(kk)]
        loadings_by_date[d] = pd.DataFrame(components, index=[f"pc{j}" for j in range(kk)],
                                           columns=wide.columns)
    if not rows:
        raise ValueError("not enough months for the PCA warmup window")
    return pd.DataFrame(rows), loadings_by_date, wide.columns


def _pc_tilt_to_signal_weights(pc_weights: pd.Series, loadings: pd.DataFrame) -> pd.Series:
    """Map a PC-space weight vector to signal-space weights via the active loadings, gross-normalized."""
    pc_weights = pc_weights.reindex(loadings.index).fillna(0.0)
    sig = pd.Series(pc_weights.values @ loadings.values, index=loadings.columns)
    gross = sig.abs().sum()
    return sig / gross if gross > 0 else sig


def signal_weights_from_pc_scores(preds: pd.DataFrame, loadings_by_date: dict,
                                  signal_cols: pd.Index) -> pd.DataFrame:
    """Predicted PC returns -> cross-PC tilt (z-centered, gross 1) -> signal-space weights.

    The tilt is demeaned ACROSS the PCs each month, so it is a relative timing bet on which factors
    do well, not a directional market bet. `preds` is the output of `expanding_window_predict` on the
    PC panel; weights at date t use only info through t (predictions are OOS), so feeding them straight
    to `backtest` (which lags weights internally) dates the P&L correctly at t+1.
    """
    scores = preds.pivot_table(index="date", columns="signal", values="y_pred")
    weights = pd.DataFrame(0.0, index=scores.index, columns=signal_cols)
    for d, row in scores.iterrows():
        s = row.dropna()
        if s.empty or d not in loadings_by_date:
            continue
        tilt = s - s.mean()
        denom = tilt.abs().sum()
        if denom == 0:
            continue
        sig = _pc_tilt_to_signal_weights(tilt / denom, loadings_by_date[d])
        weights.loc[d, sig.index] = sig.values
    return weights


def equal_weight_pc_benchmark(loadings_by_date: dict, signal_cols: pd.Index,
                              dates: pd.Index) -> pd.DataFrame:
    """Signal weights from holding all PCs equally — isolates whether TIMING beats just holding
    the factors (the 'did timing add value' control, distinct from equal-weighting raw signals)."""
    weights = pd.DataFrame(0.0, index=dates, columns=signal_cols)
    for d in dates:
        if d not in loadings_by_date:
            continue
        ld = loadings_by_date[d]
        pc_w = pd.Series(np.ones(ld.shape[0]) / ld.shape[0], index=ld.index)
        sig = _pc_tilt_to_signal_weights(pc_w, ld)
        weights.loc[d, sig.index] = sig.values
    return weights
