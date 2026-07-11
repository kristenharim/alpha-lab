"""deep_dip_reversion — long-only concentrated deep-dip residual reversion.

The low-turnover inversion of the statarb kill: same 60d sector-ETF residual
s-score (tracks/statarb code path), but LONG-only at the deep -2.5 threshold,
exit at -0.5 or 25 trading days. Equal slots (gross/15 each, no daily
re-equalization), max 15 concurrent names, idle capital in SPY, 1.5x gross.
Signal at close t -> position at close t+1 (matches the statarb engine's
skip=1 evidence convention; the harness adds its own execution lag on top).
"""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[4]          # alpha-lab repo root
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from tracks.statarb.residual import rolling_residual, s_score  # noqa: E402

P = json.loads((Path(__file__).parent / "params.json").read_text())

GROSS = 1.5          # book scale (design constant)
MAX_NAMES = 15       # concurrent slots (design constant)
WINDOW = 60          # residual/s-score window, the statarb engine default
SECTOR_ETF = {       # same map as tracks/statarb/book.py
    "Information Technology": "XLK", "Financials": "XLF", "Health Care": "XLV",
    "Consumer Discretionary": "XLY", "Consumer Staples": "XLP", "Energy": "XLE",
    "Industrials": "XLI", "Materials": "XLB", "Utilities": "XLU",
    "Real Estate": "XLRE", "Communication Services": "XLC",
}
# ponytail: universe facts hardcoded from sandbox_meta.json (frozen sandbox)
NON_STOCKS = {
    "SPY", "QQQ", "IWM", "DIA", "MDY", "EFA", "EEM", "VGK", "EWJ", "TLT",
    "IEF", "SHY", "BIL", "LQD", "HYG", "TIP", "GLD", "SLV", "DBC", "USO",
    "UNG", "VNQ", "UUP", "FXE", "XLB", "XLE", "XLF", "XLI", "XLK", "XLP",
    "XLU", "XLV", "XLY", "XLRE", "XLC", "RSP", "SVXY", "^VIX",
}


def target_weights(panel):
    close = panel["close"]
    member = panel["member"].fillna(0.0)
    stocks = [t for t in close.columns if t not in NON_STOCKS]

    rets = close.pct_change(fill_method=None)
    sec = pd.read_parquet(Path(__file__).parents[2] / "sectors.parquet")
    etf_of = sec.set_index("ticker")["sector"].map(SECTOR_ETF)
    # per-stock matched factor return; SPY fallback (unmapped names, pre-inception XLC/XLRE)
    factor = pd.DataFrame(
        {t: rets[etf_of.get(t, "SPY")] if etf_of.get(t) in rets else rets["SPY"]
         for t in stocks}, index=rets.index)
    factor = factor.apply(lambda c: c.fillna(rets["SPY"]))

    resid = rolling_residual(rets[stocks], factor, window=WINDOW)
    s = s_score(resid, window=WINDOW)

    S = s.to_numpy()
    M = (member[stocks].to_numpy() > 0)
    OK = close[stocks].notna().to_numpy()
    n_days, n_stk = S.shape
    W = np.zeros((n_days, n_stk))
    held_days = {}                                   # col index -> days held
    for i in range(n_days):
        # exits: s reverted, max hold reached, or price gone
        for j in list(held_days):
            held_days[j] += 1
            s_ij = S[i, j]
            if (held_days[j] >= P["max_hold"] or not OK[i, j]
                    or (not np.isnan(s_ij) and s_ij >= P["exit_s"])):
                del held_days[j]
        # entries: deepest s first, into free slots
        free = MAX_NAMES - len(held_days)
        if free > 0:
            cand = np.where(~np.isnan(S[i]) & (S[i] <= P["entry_s"]) & M[i] & OK[i])[0]
            cand = [j for j in cand if j not in held_days]
            for j in sorted(cand, key=lambda j: S[i, j])[:free]:
                held_days[j] = 0
        for j in held_days:
            W[i, j] = GROSS / MAX_NAMES              # fixed slot, no re-equalization

    Wdf = pd.DataFrame(W, index=close.index, columns=stocks)
    Wdf = Wdf.shift(1, fill_value=0.0)               # signal close t -> position close t+1
    Wdf = Wdf.where(close[stocks].notna(), 0.0)      # never hold a NaN-price name

    out = pd.DataFrame(0.0, index=close.index, columns=close.columns)
    out[stocks] = Wdf
    out["SPY"] = GROSS - Wdf.sum(axis=1)             # idle in SPY; gross == 1.5 always
    return out
