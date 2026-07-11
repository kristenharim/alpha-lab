"""Vol-scaled concentrated 12-1 momentum: top-20 S&P members, inverse-vol weights,
monthly refresh in 4 weekly tranches, Barroso-Santa-Clara 20% vol targeting
(cap 2.0x, floor 0.5x), hard de-lever to 1.0x when SPY < 200d SMA."""
import json
from pathlib import Path

import numpy as np
import pandas as pd

P = json.loads((Path(__file__).parent / "params.json").read_text())

# non-stock tickers, never in the momentum universe (from sandbox_meta.json, frozen)
_EXCLUDE = {
    "SPY", "QQQ", "IWM", "DIA", "MDY", "EFA", "EEM", "VGK", "EWJ", "TLT", "IEF",
    "SHY", "BIL", "LQD", "HYG", "TIP", "GLD", "SLV", "DBC", "USO", "UNG", "VNQ",
    "UUP", "FXE", "XLB", "XLE", "XLF", "XLI", "XLK", "XLP", "XLU", "XLV", "XLY",
    "XLRE", "XLC", "RSP", "SVXY", "^VIX",
}

LEV_CAP, LEV_FLOOR = 2.0, 0.5
N_TRANCHES = 4  # monthly refresh spread over 4 weekly tranches


def target_weights(panel):
    close = panel["close"]
    member = panel["member"].fillna(0.0)
    k = int(P["n_names"])
    vol_lb = int(P["vol_lookback"])
    vol_target = float(P["vol_target_ann"])

    stocks = [t for t in close.columns if t not in _EXCLUDE]
    c = close[stocks]
    rets = c.pct_change(fill_method=None)

    mom = c.shift(21) / c.shift(252) - 1.0          # 12-1 momentum
    vol = rets.rolling(vol_lb).std()                 # 62d daily vol per name

    # last trading day of each ISO week = tranche rebalance days
    idx = close.index
    rebal_days = pd.Series(idx, index=idx).groupby(idx.to_period("W")).last().values

    tranches = [None] * N_TRANCHES
    snap_dates, snap_rows = [], []
    for i, d in enumerate(rebal_days):
        m_row, v_row = mom.loc[d], vol.loc[d]
        elig = (member.loc[d, stocks] > 0) & m_row.notna() & v_row.notna() & (v_row > 0)
        if elig.sum() >= k:
            top = m_row[elig].nlargest(k)
            iw = 1.0 / v_row[top.index]
            tranches[i % N_TRANCHES] = iw / iw.sum()
        live = [t for t in tranches if t is not None]
        if not live:
            continue
        combined = pd.concat(live, axis=1).sum(axis=1) / N_TRANCHES
        snap_dates.append(d)
        snap_rows.append(combined)

    if not snap_dates:
        return pd.DataFrame(0.0, index=idx, columns=stocks[:1])

    base = pd.DataFrame(snap_rows, index=pd.DatetimeIndex(snap_dates)).fillna(0.0)
    base = base.reindex(idx).ffill().fillna(0.0)

    # Barroso-Santa-Clara: scale by realized vol of the (unlevered) strategy
    r_base = (base.shift(1) * rets[base.columns]).sum(axis=1, min_count=1)
    rv = r_base.rolling(vol_lb).std() * np.sqrt(252)
    lev = (vol_target / rv).clip(lower=LEV_FLOOR, upper=LEV_CAP).fillna(1.0)

    # momentum crashes are post-bear events: hard de-lever under the 200d SMA
    spy = close["SPY"]
    bear = spy < spy.rolling(200).mean()
    lev = lev.where(~bear, lev.clip(upper=1.0))

    W = base.mul(lev, axis=0)
    # safety: never rely on the harness clip (base gross can exceed 1 only by float eps)
    g = W.abs().sum(axis=1)
    W = W.mul((LEV_CAP / g).clip(upper=1.0).fillna(1.0), axis=0)
    return W


if __name__ == "__main__":
    # self-check: warmup empty, gross within cap, long-only, ^VIX/ETFs never held
    rng = np.random.default_rng(0)
    n, t = 60, 700
    idx = pd.bdate_range("2018-01-01", periods=t)
    names = [f"S{i}" for i in range(n)] + ["SPY", "^VIX"]
    px = pd.DataFrame(100 * np.exp(np.cumsum(rng.normal(0.0003, 0.02, (t, n + 2)), 0)),
                      index=idx, columns=names)
    mem = pd.DataFrame(1.0, index=idx, columns=names)
    panel = pd.concat({"close": px, "member": mem}, axis=1)
    W = target_weights(panel)
    assert (W.abs().sum(axis=1) <= 2.0 + 1e-9).all()
    assert (W.iloc[:250].abs().sum(axis=1) == 0).all()
    assert (W.values >= 0).all()
    assert "^VIX" not in W.columns and "SPY" not in W.columns
    row = W.iloc[-1]
    assert 15 <= (row > 0).sum() <= 30  # ~20 names, tranche overlap can vary
    print("self-check OK")
