"""composite_book: 1.2x banded-EW S&P core + 0.5x gap-drift sleeve + 0.3x SPY panic
sleeve, whole-book VIX-40 halving gate. Gross <= 2.0 by construction.

Standalone reimplementation — no imports from sibling specs.
"""
import json
from pathlib import Path

import numpy as np
import pandas as pd

P = json.loads((Path(__file__).parent / "params.json").read_text())

# house constants (not tunables): 20% relative no-trade band on the EW core,
# 5%-of-sleeve per-name cap in the drift sleeve, 3x volume confirm windows.
BAND = 0.20
NAME_CAP = 0.05
SIGMA_WIN, VOLMED_WIN = 60, 20

ETFS = {"SPY", "QQQ", "IWM", "DIA", "MDY", "EFA", "EEM", "VGK", "EWJ", "TLT",
        "IEF", "SHY", "BIL", "LQD", "HYG", "TIP", "GLD", "SLV", "DBC", "USO",
        "UNG", "VNQ", "UUP", "FXE", "XLB", "XLE", "XLF", "XLI", "XLK", "XLP",
        "XLU", "XLV", "XLY", "XLRE", "XLC", "RSP", "SVXY"}


def _core_weights(close, member):
    """Equal-weight PIT members with a 20% relative no-trade band. Sums to 1."""
    rets = close.pct_change(fill_method=None).to_numpy()
    elig = ((member.to_numpy() > 0) & close.notna().to_numpy())
    T, N = elig.shape
    W = np.zeros((T, N))
    w = np.zeros(N)
    for t in range(T):
        e = elig[t]
        n = e.sum()
        if n == 0:
            W[t] = 0.0
            continue
        tgt = 1.0 / n
        if t > 0:
            r = np.nan_to_num(rets[t])
            w = w * (1.0 + r)           # drift with returns (no trade)
            w[~e] = 0.0                 # drops leave the book
        w[e & (w <= 0)] = tgt           # adds enter at target
        # band: reset any name drifted >20% relative from equal weight
        off = e & (np.abs(w / tgt - 1.0) > BAND)
        w[off] = tgt
        w = w / w.sum()                 # keep sleeve gross constant
        W[t] = w
    return pd.DataFrame(W, index=close.index, columns=close.columns)


def _drift_sleeve(close, volume, member):
    """Gap-drift events: 1d return >= z_thresh sigmas with 3x volume confirm,
    enter close t+1, hold 60d, equal weight capped at 5% of sleeve, idle in SPY.
    Returns (per-name stock weights, SPY residual), sleeve gross = 1."""
    d = P["drift_rules"]
    ret = close.pct_change(fill_method=None)
    sigma = ret.rolling(SIGMA_WIN).std().shift(1)
    z = ret / sigma
    volmed = volume.rolling(VOLMED_WIN).median().shift(1)
    event = (z >= d["z_thresh"]) & (volume >= d["vol_mult"] * volmed) & (member > 0)
    # event at t -> active t+1 .. t+hold
    active = event.rolling(d["hold_days"], min_periods=1).sum().shift(1).fillna(0) > 0
    n = active.sum(axis=1)
    per_name = np.minimum(NAME_CAP, 1.0 / n.replace(0, np.nan))
    Wd = active.mul(per_name, axis=0).fillna(0.0)
    spy_resid = (1.0 - Wd.sum(axis=1)).clip(lower=0.0)
    return Wd, spy_resid


def _gate_scale(vix):
    """0.5 while gated (VIX >= halve_at), back to 1.0 after reenter_days
    consecutive closes below reenter_below."""
    g = P["vix_gate"]
    v = vix.ffill().to_numpy()
    scale = np.ones(len(v))
    halved, streak = False, 0
    for t in range(len(v)):
        if v[t] >= g["halve_at"]:
            halved, streak = True, 0
        elif halved:
            streak = streak + 1 if v[t] < g["reenter_below"] else 0
            if streak >= g["reenter_days"]:
                halved = False
        scale[t] = 0.5 if halved else 1.0
    return pd.Series(scale, index=vix.index)


def target_weights(panel):
    close, volume, member = panel["close"], panel["volume"], panel["member"]
    stocks = [t for t in close.columns if t not in ETFS and t != "^VIX"]
    sw = P["sleeve_weights"]

    core = _core_weights(close[stocks], member[stocks]) * sw["core"]
    Wd, spy_resid = _drift_sleeve(close[stocks], volume[stocks], member[stocks])

    W = core.add(Wd * sw["drift"], fill_value=0.0)
    W["SPY"] = spy_resid * sw["drift"] + sw["panic_spy"]

    W = W.mul(_gate_scale(close["^VIX"]), axis=0)

    # ponytail: fp-safety clip so summed gross never tips past 2.0
    gross = W.abs().sum(axis=1)
    W = W.mul((2.0 / gross).clip(upper=1.0).fillna(1.0), axis=0)
    return W.fillna(0.0)


if __name__ == "__main__":
    import sys
    sys.path.insert(0, str(Path(__file__).parents[2]))
    import harness
    panel = harness.load_train()
    W = target_weights(panel)
    assert "^VIX" not in W.columns or W["^VIX"].abs().sum() == 0
    assert (W.abs().sum(axis=1) <= 2.0 + 1e-9).all()
    for label, start in [("last2y", "2023-07-10"), ("full", "2015-01-01")]:
        r = harness.run(harness.load_spec(Path(__file__).parent), panel, start=start)
        print(label, {k: round(v, 4) for k, v in r.items()
                      if isinstance(v, float)}, "viol:", r["gross_cap_violations"])
