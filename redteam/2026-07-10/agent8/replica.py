# Agent 8 clean-room replicas — built ONLY from params.json + MECHANISM.md +
# SPEC_CONVENTIONS.md. Original spec.py files were NEVER read (they are executed
# elsewhere, as black boxes, to produce reference weights).
#
# Predeclared conventions (chosen BEFORE any diff was inspected — see report.md):
#  C1. realized vol = rolling std (ddof=1) of simple close-to-close pct returns,
#      window = lookback, min_periods = lookback, annualized sqrt(252).
#  C2. no-trade band is sequential: keep previous weight unless |raw - prev| > band.
#  C3. monthly rebalance = signal computed at the last trading day of each month's
#      close; target held constant until the next rebalance.
#  C4. SMA hysteresis 1%: risk-on when close > sma*1.01, risk-off when close <
#      sma*0.99, otherwise keep prior state; initial state = (close >= sma).
#  C5. "12-1 momentum" = close.shift(21)/close.shift(252) - 1 at formation date.
#  C6. membership = panel["member"] == 1 at the formation date.
#  C7. any book-internal gross cap = scale the whole weight row to gross 2.0.
import json
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).parent
HUNT = Path.home() / "projects/alpha-lab/research/hunt2026"
META = json.loads((HUNT / "sandbox_meta.json").read_text())
ANN = np.sqrt(252)


def rv(close, n):
    return close.pct_change(fill_method=None).rolling(n, min_periods=n).std() * ANN


def band_filter(raw, band):
    """C2: sequential no-trade band on a single weight series."""
    out = raw.copy()
    prev = np.nan
    vals = raw.to_numpy()
    res = np.empty_like(vals)
    for i, v in enumerate(vals):
        if np.isnan(v):
            res[i] = prev if not np.isnan(prev) else np.nan
            continue
        if np.isnan(prev) or abs(v - prev) > band:
            prev = v
        res[i] = prev
    out[:] = res
    return out


def month_ends(idx):
    return idx.to_series().groupby([idx.year, idx.month]).apply(lambda s: s.index[-1]).values


def week_ends(idx):
    iso = idx.isocalendar()
    key = list(zip(iso.year, iso.week))
    return idx.to_series().groupby(key).apply(lambda s: s.index[-1]).sort_values().values


def zeros(panel, cols):
    return pd.DataFrame(0.0, index=panel.index, columns=list(cols))


# --- 1. vol_managed_qqq -----------------------------------------------------
def vol_managed_qqq(panel):
    p = json.loads((HUNT / "specs/vol_managed_qqq/params.json").read_text())
    raw = (p["sigma_target"] / rv(panel["close"]["QQQ"], p["vol_lookback"])).clip(upper=2.0)
    W = zeros(panel, ["QQQ"])
    W["QQQ"] = band_filter(raw, p["tolerance_band"]).fillna(0.0)
    return W


# --- 2. vol_core_svxy -------------------------------------------------------
def vol_core_svxy(panel):
    p = json.loads((HUNT / "specs/vol_core_svxy/params.json").read_text())
    st = p["sigma_target"]
    c = panel["close"]
    w_qqq = 0.6 * (st / rv(c["QQQ"], 21)).clip(upper=2.0)
    w_spy = 0.4 * (st / rv(c["SPY"], 21)).clip(upper=2.0)
    vix = c["^VIX"]
    gate = vix < vix.rolling(p["vix_gate_window"], min_periods=p["vix_gate_window"]).median()
    W = zeros(panel, ["QQQ", "SPY", "SVXY"])
    W["QQQ"] = w_qqq.fillna(0.0)
    W["SPY"] = w_spy.fillna(0.0)
    W["SVXY"] = np.where(gate, p["svxy_weight"], 0.0)
    g = W.abs().sum(axis=1)
    W = W.mul((2.0 / g).clip(upper=1.0).fillna(1.0), axis=0)  # C7
    return W


# --- 3. trend_vol_qqq -------------------------------------------------------
def trend_vol_qqq(panel):
    p = json.loads((HUNT / "specs/trend_vol_qqq/params.json").read_text())
    c = panel["close"]["QQQ"]
    sma = c.rolling(p["sma_window"], min_periods=p["sma_window"]).mean()
    state = pd.Series(np.nan, index=c.index)
    on = None
    for i, (px, m) in enumerate(zip(c.to_numpy(), sma.to_numpy())):
        if np.isnan(m):
            state.iloc[i] = np.nan
            continue
        if on is None:
            on = px >= m
        elif px > m * 1.01:
            on = True
        elif px < m * 0.99:
            on = False
        state.iloc[i] = on
    raw = (p["sigma_target"] / rv(c, p["rv_lookback"])).clip(upper=2.0)
    wq = band_filter(raw, 0.05)
    W = zeros(panel, ["QQQ", "BIL"])
    W["QQQ"] = np.where(state == 1, wq, 0.0)
    W["BIL"] = np.where(state == 0, 1.0, 0.0)
    return W.fillna(0.0)


# --- 4. defensive_ensemble --------------------------------------------------
def defensive_ensemble(panel):
    p = json.loads((HUNT / "specs/defensive_ensemble/params.json").read_text())
    lb = p["sleeve_vol_lookback"]
    c = panel["close"]
    rets = c.pct_change(fill_method=None)
    idx = panel.index

    # Sleeve A: SPY, inverse-realized-variance scaled to the vol target, 200d gate.
    rv63 = rv(c["SPY"], lb)
    expo = ((p["vol_target"] / rv63) ** 2).clip(upper=2.0)
    gate = c["SPY"] > c["SPY"].rolling(200, min_periods=200).mean()
    A = zeros(panel, ["SPY"])
    A["SPY"] = np.where(gate, expo, 0.0)
    A = A.fillna(0.0)

    # Sleeve B: 12m TSMOM, long-or-flat, equal weight across cross-asset ETFs.
    uni_b = ["SPY", "TLT", "GLD", "UUP", "DBC"]
    mom = c[uni_b].pct_change(252, fill_method=None)
    B = (mom > 0).astype(float) / len(uni_b)

    # Sleeve C: dual momentum SPY/QQQ/EFA vs BIL, defensive TLT/BIL.
    uni_c = ["SPY", "QQQ", "EFA"]
    r252 = c[uni_c + ["BIL", "TLT"]].pct_change(252, fill_method=None)
    C = zeros(panel, ["SPY", "QQQ", "EFA", "TLT", "BIL"])
    rw = r252[uni_c]
    winner = rw.idxmax(axis=1)
    risk_on = rw.max(axis=1) > r252["BIL"]
    defwin = np.where(r252["TLT"] > r252["BIL"], "TLT", "BIL")
    for i, d in enumerate(idx):
        if rw.loc[d].isna().all() or np.isnan(r252["BIL"].loc[d]):
            continue
        if risk_on.loc[d]:
            C.loc[d, winner.loc[d]] = 1.0
        else:
            C.loc[d, defwin[i]] = 1.0

    sleeves = {"A": A, "B": B, "C": C}
    cols = sorted(set().union(*[s.columns for s in sleeves.values()]))
    # sleeve daily returns (harness convention: held = shift(1))
    sret = {k: (s.shift(1) * rets[s.columns]).sum(axis=1, min_count=1).fillna(0.0)
            for k, s in sleeves.items()}
    svol = {k: r.rolling(lb, min_periods=lb).std() * ANN for k, r in sret.items()}

    W = zeros(panel, cols)
    me = month_ends(idx)
    cur = None
    for d in idx:
        if d in me or cur is None:
            iv = {k: (1.0 / svol[k].loc[d]) if svol[k].loc[d] and svol[k].loc[d] > 0 else np.nan
                  for k in sleeves}
            tot = np.nansum(list(iv.values()))
            if not tot or np.isnan(tot):
                cur = pd.Series(0.0, index=cols)
            else:
                cur = pd.Series(0.0, index=cols)
                for k, s in sleeves.items():
                    if not np.isnan(iv[k]):
                        cur = cur.add(s.loc[d].reindex(cols).fillna(0.0) * (iv[k] / tot),
                                      fill_value=0.0)
                book_ret = sum((iv[k] / tot) * sret[k] for k in sleeves if not np.isnan(iv[k]))
                bv = book_ret.rolling(lb, min_periods=lb).std().loc[d] * ANN
                lev = p["vol_target"] / bv if bv and bv > 0 else 0.0
                cur = cur * lev
                g = cur.abs().sum()
                if g > p["gross_cap"]:
                    cur = cur * (p["gross_cap"] / g)
        W.loc[d] = cur
    return W.fillna(0.0)


# --- 5. dual_momentum_gold --------------------------------------------------
def dual_momentum_gold(panel):
    p = json.loads((HUNT / "specs/dual_momentum_gold/params.json").read_text())
    c = panel["close"]
    lb = p["lookback"]
    r = c[["SPY", "QQQ", "GLD", "BIL", "TLT"]].pct_change(lb, fill_method=None)
    W = zeros(panel, ["SPY", "QQQ", "GLD", "TLT", "BIL"])
    me = set(month_ends(panel.index))
    cur = None
    for d in panel.index:
        if d in me or cur is None:
            row = r.loc[d]
            cur = pd.Series(0.0, index=W.columns)
            risk = row[["SPY", "QQQ", "GLD"]]
            if not risk.isna().all() and not np.isnan(row["BIL"]):
                w = risk.idxmax()
                if risk[w] > row["BIL"]:
                    cur[w] = p["risk_leverage"]
                else:
                    d_w = "TLT" if row["TLT"] > row["BIL"] else "BIL"
                    cur[d_w] = p["defensive_leverage"]
        W.loc[d] = cur
    return W


# --- 6. momentum_concentrated -----------------------------------------------
def momentum_concentrated(panel):
    p = json.loads((HUNT / "specs/momentum_concentrated/params.json").read_text())
    c, mem = panel["close"], panel["member"]
    stocks = [t for t in c.columns if t not in META["etfs"] and t not in META["signal_only"]]
    cs = c[stocks]
    mom = cs.shift(21) / cs.shift(252) - 1.0  # C5
    vol = cs.pct_change(fill_method=None).rolling(p["vol_lookback"],
                                                  min_periods=p["vol_lookback"]).std() * ANN
    idx = panel.index
    wk = week_ends(idx)
    tranches = [pd.Series(dtype=float)] * 4
    base = pd.DataFrame(0.0, index=idx, columns=stocks)
    cur = pd.Series(0.0, index=stocks)
    wk_set = {d: i for i, d in enumerate(wk)}
    for d in idx:
        if d in wk_set:
            k = wk_set[d] % 4
            m = mom.loc[d].where(mem[stocks].loc[d] == 1.0)
            top = m.dropna().nlargest(p["n_names"]).index
            iv = 1.0 / vol.loc[d, top]
            iv = iv.replace([np.inf, -np.inf], np.nan).dropna()
            t = (iv / iv.sum()) if len(iv) and iv.sum() > 0 else pd.Series(dtype=float)
            tranches[k] = t
            cur = pd.Series(0.0, index=stocks)
            for t_ in tranches:
                cur = cur.add(t_.reindex(stocks).fillna(0.0) * 0.25, fill_value=0.0)
        base.loc[d] = cur
    rets = cs.pct_change(fill_method=None)
    bret = (base.shift(1) * rets).sum(axis=1, min_count=1).fillna(0.0)
    bvol = bret.rolling(p["vol_lookback"], min_periods=p["vol_lookback"]).std() * ANN
    lev = (p["vol_target_ann"] / bvol).clip(lower=0.5, upper=2.0)
    spy = c["SPY"]
    below = spy < spy.rolling(200, min_periods=200).mean()
    lev = np.where(below, np.minimum(lev, 1.0), lev)
    W = base.mul(pd.Series(lev, index=idx).fillna(1.0), axis=0)
    W[base.sum(axis=1) == 0] = 0.0
    return W


# --- 7. dual_momentum_gem ---------------------------------------------------
def dual_momentum_gem(panel):
    p = json.loads((HUNT / "specs/dual_momentum_gem/params.json").read_text())
    c = panel["close"]
    lb, skip = p["lookback_days"], p["skip_days"]
    px = c[["SPY", "QQQ", "EFA", "BIL"]].shift(skip)
    r = px / px.shift(lb) - 1.0
    W = zeros(panel, ["SPY", "QQQ", "EFA", "TLT"])
    me = set(month_ends(panel.index))
    cur = None
    for d in panel.index:
        if d in me or cur is None:
            row = r.loc[d]
            cur = pd.Series(0.0, index=W.columns)
            risk = row[["SPY", "QQQ", "EFA"]]
            if not risk.isna().all() and not np.isnan(row["BIL"]):
                w = risk.idxmax()
                if risk[w] > row["BIL"]:
                    cur[w] = p["equity_leverage"]
                else:
                    cur["TLT"] = 1.0
        W.loc[d] = cur
    return W


BOOKS = {
    "vol_managed_qqq": vol_managed_qqq,
    "vol_core_svxy": vol_core_svxy,
    "trend_vol_qqq": trend_vol_qqq,
    "defensive_ensemble": defensive_ensemble,
    "dual_momentum_gold": dual_momentum_gold,
    "momentum_concentrated": momentum_concentrated,
    "dual_momentum_gem": dual_momentum_gem,
}


# --- independent scorer (written from the documented convention, no imports) --
def score(W, panel, start=None, end=None):
    etf = set(META["etfs"])
    W = W.astype(float).fillna(0.0)
    gross_exp = W.abs().sum(axis=1)
    viol = int((gross_exp > 2.0 + 1e-9).sum())
    W = W.mul((2.0 / gross_exp).clip(upper=1.0).fillna(1.0), axis=0)
    close = panel["close"][W.columns]
    rets = close.pct_change(fill_method=None)
    held = W.shift(1)
    gross = (held * rets).sum(axis=1, min_count=1).fillna(0.0)
    bps = pd.Series([2.0 if t in etf else 10.0 for t in W.columns], index=W.columns)
    cost = (W.diff().abs().fillna(W.abs()) * (bps / 1e4)).sum(axis=1)
    net = gross - cost
    idx = net.index
    if start is not None:
        idx = idx[idx > pd.Timestamp(start)]
    if end is not None:
        idx = idx[idx <= pd.Timestamp(end)]
    net = net.reindex(idx)
    nav = (1 + net).cumprod()
    return {
        "net_daily": net,
        "total_net": float(nav.iloc[-1] - 1),
        "ann_vol": float(net.std() * ANN),
        "sharpe": float(net.mean() / net.std() * ANN) if net.std() > 0 else 0.0,
        "max_dd": float((nav / nav.cummax() - 1).min()),
        "avg_gross_exposure": float(held.reindex(idx).abs().sum(axis=1).mean()),
        "avg_daily_turnover": float(W.diff().abs().sum(axis=1).reindex(idx).mean()),
        "cost_drag_ann": float(cost.reindex(idx).mean() * 252),
        "violations": viol,
    }
