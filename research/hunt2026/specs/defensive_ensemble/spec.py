"""defensive_ensemble: equal-risk ensemble of three uncorrelated defensive sleeves,
vol-targeted to 18% ann. Standalone reimplementation — no sibling-spec imports.

Sleeve A: trend+vol-managed QQQ (200d SMA gate, 1% hysteresis; on: min(2, 0.25/rv21); off: BIL)
Sleeve B: multi-asset 252d-sign TSMOM, inverse-63d-vol weights, monthly rebalance
Sleeve C: dual momentum {SPY,QQQ,GLD} vs {TLT,BIL} by 252d return, single asset, monthly

All lookbacks/constants besides params.json are pre-2021 literature defaults
(Moskowitz-Ooi-Pedersen 12m TSMOM, Antonacci dual momentum, Moreira-Muir vol management).
"""
import json
from pathlib import Path

import numpy as np
import pandas as pd

P = json.loads((Path(__file__).parent / "params.json").read_text())

TSMOM_MENU = ["SPY", "QQQ", "IWM", "EFA", "EEM", "TLT", "IEF", "GLD", "SLV",
              "DBC", "USO", "UUP", "HYG", "LQD", "VNQ"]
RISK = ["SPY", "QQQ", "GLD"]
SAFE = ["TLT", "BIL"]


def target_weights(panel):
    close = panel["close"]
    tickers = sorted(set(TSMOM_MENU + RISK + SAFE))
    close = close[tickers]
    rets = close.pct_change(fill_method=None)
    idx = close.index
    month = idx.to_series().dt.to_period("M")
    reb = (month != month.shift(1)).values  # first trading day of each month

    # --- Sleeve A: trend + vol managed QQQ ---
    q = close["QQQ"]
    sma = q.rolling(200).mean()
    gate = pd.Series(np.where(q > sma * 1.01, 1.0,
                              np.where(q < sma * 0.99, 0.0, np.nan)), index=idx)
    gate = gate.ffill().fillna(0.0)
    rv21 = rets["QQQ"].rolling(21).std() * np.sqrt(252)
    lev_q = (0.25 / rv21).clip(upper=2.0)
    A = pd.DataFrame(0.0, index=idx, columns=tickers)
    A["QQQ"] = (gate * lev_q).fillna(0.0)
    A["BIL"] = 1.0 - gate

    # --- Sleeve B: 252d-sign TSMOM, inverse-63d-vol weights, monthly ---
    mom = close[TSMOM_MENU] / close[TSMOM_MENU].shift(252) - 1
    vol63 = rets[TSMOM_MENU].rolling(63).std() * np.sqrt(252)
    iv = (1.0 / vol63).replace([np.inf, -np.inf], np.nan)
    w_b = iv.div(iv.sum(axis=1), axis=0) * np.sign(mom)
    w_b = w_b.where(pd.Series(reb, index=idx), np.nan).ffill()
    B = pd.DataFrame(0.0, index=idx, columns=tickers)
    B[TSMOM_MENU] = w_b.fillna(0.0)

    # --- Sleeve C: dual momentum, single asset, monthly ---
    r252 = close / close.shift(252) - 1
    rr = r252[RISK + SAFE].fillna(-9e9)  # avoid all-NA idxmax; rows nulled below
    best_risk = rr[RISK].idxmax(axis=1)
    pick = best_risk.where(rr[RISK].max(axis=1) > rr["BIL"],
                           rr[SAFE].idxmax(axis=1))
    pick[r252[RISK + SAFE].isna().any(axis=1)] = np.nan
    onehot = pd.get_dummies(pick).reindex(columns=tickers, fill_value=0).astype(float)
    C = onehot.where(pd.Series(reb, index=idx), np.nan).ffill().fillna(0.0)

    # --- Combine: inverse-vol sleeve weights (63d vol of sleeve return streams), monthly ---
    lb = P["sleeve_vol_lookback"]
    sleeves = [A, B, C]
    svol = pd.DataFrame({
        k: (W.shift(1) * rets).sum(axis=1, min_count=1).rolling(lb).std()
        for k, W in enumerate(sleeves)})
    inv = (1.0 / svol).replace([np.inf, -np.inf], np.nan)
    sw = inv.div(inv.sum(axis=1), axis=0)
    sw = sw.where(pd.Series(reb, index=idx), np.nan).ffill().fillna(1.0 / 3.0)
    W_pre = sum(W.mul(sw[k], axis=0) for k, W in enumerate(sleeves))

    # --- Vol target the total book, cap gross ---
    bret = (W_pre.shift(1) * rets).sum(axis=1, min_count=1)
    rv_book = bret.rolling(lb).std() * np.sqrt(252)
    lev = (P["vol_target"] / rv_book).replace([np.inf, -np.inf], np.nan)
    gross_pre = W_pre.abs().sum(axis=1)
    max_lev = (P["gross_cap"] * 0.999) / gross_pre.replace(0.0, np.nan)
    lev = lev.clip(upper=max_lev).fillna(1.0)
    return W_pre.mul(lev, axis=0).fillna(0.0)
