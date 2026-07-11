"""Agent 2 independent engine — NO imports from alpha-lab code.

Two engines, both written from the P&L convention in the harness docstring +
SPEC_CONVENTIONS.md (weights set at close t, earn close-to-close t+1, costs per
side on |dw|, gross capped at 2.0):

  weight_engine  — replicates the stated weight-space convention with an explicit
                   python loop (independent arithmetic check of harness.run).
  share_engine   — a real account: integer-free share-based sim. Holds shares,
                   trades at close t to reach target weights, pays costs on traded
                   notional, cash earns `cash_rate_daily`, levered financing charged
                   at `borrow_rate_daily` on borrowed cash. Marks to market daily.
                   NaN close => stale-price mark (last known price), which is what a
                   broker statement would show.

The gap between the two is the convention gap (free daily re-trueing, no financing,
dropped returns on NaN days). The gap inside weight_engine vs harness is a bug.
"""
import numpy as np
import pandas as pd

MAX_GROSS = 2.0


def weight_engine(W: pd.DataFrame, close: pd.DataFrame, bps: dict,
                  start=None, end=None):
    """Stated convention, loop-based. Returns (net Series, violations int)."""
    W = W.astype(float).fillna(0.0)
    close = close[W.columns]
    dates = W.index
    n, m = len(dates), W.shape[1]
    p = close.to_numpy(dtype=float)
    w = W.to_numpy(dtype=float).copy()
    per_side = np.array([bps[t] for t in W.columns]) / 1e4

    viol = 0
    for i in range(n):
        g = np.abs(w[i]).sum()
        if g > MAX_GROSS + 1e-9:
            viol += 1
        if g > MAX_GROSS:
            w[i] *= MAX_GROSS / g

    net = np.zeros(n)
    prev_w = np.zeros(m)
    for i in range(n):
        gross = 0.0
        if i > 0:
            for j in range(m):
                if prev_w[j] != 0.0:
                    p0, p1 = p[i - 1, j], p[i, j]
                    if np.isfinite(p0) and np.isfinite(p1):
                        gross += prev_w[j] * (p1 / p0 - 1.0)
                    # NaN on either side: harness contributes 0 for this name
        cost = float((np.abs(w[i] - prev_w) * per_side).sum())
        net[i] = gross - cost
        prev_w = w[i]

    s = pd.Series(net, index=dates)
    if start is not None:
        s = s[s.index > pd.Timestamp(start)]
    if end is not None:
        s = s[s.index <= pd.Timestamp(end)]
    return s, viol


def share_engine(W: pd.DataFrame, close: pd.DataFrame, bps: dict,
                 start=None, end=None, cash_rate_daily=0.0,
                 borrow_rate_daily=0.0, trade_only_on_target_change=False):
    """Share-based sim. NAV starts at 1.0 on the first window date.
    Trades at close t to reach W.loc[t] of current NAV; pays bps on traded notional.
    NaN close = stale mark at last known price (no trading in that name that day).
    A name whose price never returns is carried at its stale mark (broker-statement
    view; a bankruptcy would really be ~0 — that difference is reported by tests).
    """
    W = W.astype(float).fillna(0.0)
    close = close[W.columns]
    dates = W.index
    p_raw = close.to_numpy(dtype=float)
    w_tgt = W.to_numpy(dtype=float).copy()
    n, m = len(dates), W.shape[1]
    per_side = np.array([bps[t] for t in W.columns]) / 1e4

    for i in range(n):  # same gross cap
        g = np.abs(w_tgt[i]).sum()
        if g > MAX_GROSS:
            w_tgt[i] *= MAX_GROSS / g

    # stale-mark price matrix
    mark = p_raw.copy()
    for j in range(m):
        last = np.nan
        for i in range(n):
            if np.isfinite(mark[i, j]):
                last = mark[i, j]
            else:
                mark[i, j] = last

    start_ts = pd.Timestamp(start) if start is not None else None
    end_ts = pd.Timestamp(end) if end is not None else None

    shares = np.zeros(m)
    cash = 1.0
    nav_series, ret_dates = [], []
    prev_nav = None
    prev_tgt = np.zeros(m)
    for i in range(n):
        d = dates[i]
        if start_ts is not None and d <= start_ts:
            # pre-window: establish positions cost-free at target (mirrors the
            # harness windowing, where pre-start costs/returns are sliced out)
            nav = 1.0
            tradable = np.isfinite(p_raw[i])
            shares = np.where(tradable, np.divide(w_tgt[i], p_raw[i],
                              out=np.zeros(m), where=tradable), shares)
            cash = nav - float(np.nansum(shares * mark[i]))
            prev_tgt = w_tgt[i]
            continue
        if end_ts is not None and d > end_ts:
            break
        # accrue cash return / financing on yesterday's balance
        if prev_nav is not None:
            if cash >= 0:
                cash *= (1.0 + cash_rate_daily)
            else:
                cash *= (1.0 + borrow_rate_daily)
        nav = cash + float(np.nansum(shares * mark[i]))
        # trade at today's close toward target
        do_trade = True
        if trade_only_on_target_change and prev_nav is not None:
            do_trade = bool(np.any(w_tgt[i] != prev_tgt))
        if do_trade:
            for j in range(m):
                if not np.isfinite(p_raw[i, j]):
                    continue  # can't trade a name with no print today
                tgt_sh = w_tgt[i, j] * nav / p_raw[i, j]
                delta = tgt_sh - shares[j]
                if delta != 0.0:
                    notional = abs(delta) * p_raw[i, j]
                    cash -= delta * p_raw[i, j] + notional * per_side[j]
                    shares[j] = tgt_sh
            nav = cash + float(np.nansum(shares * mark[i]))
        prev_tgt = w_tgt[i]
        nav_series.append(nav)
        ret_dates.append(d)
        prev_nav = nav

    nav_s = pd.Series(nav_series, index=ret_dates)
    return nav_s / nav_s.iloc[0] if len(nav_s) else nav_s
