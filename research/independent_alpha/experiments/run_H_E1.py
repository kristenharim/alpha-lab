"""EXP-2026-07-10-reversal-x-liquidity (prereg H-E1).

Reversal rank IC conditional on liquidity-demand terciles (volume_shock).
Reuses ic_screen's panel load, PIT member mask, month-end dates, n>=50 guard.
Signal-space measurement only (ceiling = level 1). No book, no costs.

Run: .venv/bin/python research/independent_alpha/experiments/run_H_E1.py
"""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
HUNT = HERE.parents[1] / "hunt2026"


def load():
    panel = pd.read_parquet(HUNT / "panel_2005.parquet")
    meta = json.loads((HUNT / "sandbox_meta.json").read_text())
    non_stock = set(meta["etfs"]) | set(meta["signal_only"])
    return panel, non_stock


def spearman_ic(s, f):
    return s.rank().corr(f.rank())


def tercile_ic(sig, vshock, fwd, member, dates, tag_lo, tag_hi):
    """Per date: split ok cross-section into volume_shock terciles (>=50/tercile
    or drop date), reversal Spearman IC within bottom (quiet) & top (high) tercile."""
    hi, lo = [], []
    used = []
    for d in dates:
        m = member.loc[d] == 1
        s = sig.loc[d][m]
        v = vshock.loc[d][m]
        f = fwd.loc[d][m]
        ok = s.notna() & v.notna() & f.notna()
        if ok.sum() < 150:  # need >=50 per tercile across 3 terciles
            continue
        s, v, f = s[ok], v[ok], f[ok]
        try:
            terc = pd.qcut(v, 3, labels=[0, 1, 2])
        except ValueError:
            continue  # non-unique edges -> can't form 3 clean terciles
        bot = terc == 0
        top = terc == 2
        if bot.sum() < 50 or top.sum() < 50:
            continue
        hi.append(spearman_ic(s[top], f[top]))
        lo.append(spearman_ic(s[bot], f[bot]))
        used.append(d)
    hi = pd.Series(hi, index=used).dropna()
    lo = pd.Series(lo, index=used).dropna()
    return hi, lo


def tstat(x):
    x = x.dropna()
    return x.mean() / x.std() * np.sqrt(len(x))


def paired_t(a, b):
    d = (a - b).dropna()
    return d.mean(), d.mean() / d.std() * np.sqrt(len(d)), len(d)


def summ(name, ic):
    return f"{name:28s} mean={ic.mean():+.5f}  t={tstat(ic):+.3f}  hit={(ic>0).mean():.3f}  n={len(ic)}"


def main():
    panel, non_stock = load()
    member = panel["member"]
    stocks = [t for t in member.columns if t not in non_stock]
    member = member[stocks]
    close = panel["close"][stocks]
    vol = panel["volume"][stocks]

    reversal = -(close / close.shift(21) - 1)
    vshock = vol.rolling(21).mean() / vol.rolling(252).mean()

    fwd = {h: close.shift(-h) / close - 1 for h in (21, 63)}

    dates = pd.Series(close.index, index=close.index).resample("ME").last().dropna()
    dates = dates[dates >= "2015-01-01"].tolist()
    dates = [d for d in dates if fwd[63].loc[d].notna().sum() > 0]

    HOLD0, HOLD1 = pd.Timestamp("2024-07-01"), pd.Timestamp("2026-06-30")

    rows = []
    result = {}
    for h in (21, 63):
        hi, lo = tercile_ic(reversal, vshock, fwd[h], member, dates, "lo", "hi")
        d_mean, d_t, d_n = paired_t(hi, lo)
        result[h] = dict(hi=hi, lo=lo, inter_mean=d_mean, inter_t=d_t, inter_n=d_n)
        print(f"\n=== horizon {h}d ===")
        print(summ(f"high-tercile IC {h}d", hi))
        print(summ(f"low-tercile  IC {h}d", lo))
        print(f"interaction (high-low) {h}d  mean={d_mean:+.5f}  t={d_t:+.3f}  n={d_n}")

        # by-half stability (2015-19 / 2020-24 / 2025-26) on high tercile
        half = pd.cut(hi.index.year, [2014, 2019, 2024, 2026],
                      labels=["2015-19", "2020-24", "2025-26"])
        print("high-tercile by era:")
        print(hi.groupby(half, observed=True).agg(["mean", "count"]).round(5).to_string())

        # holdout sign stability
        dev_hi = hi[(hi.index < HOLD0)]
        hold_hi = hi[(hi.index >= HOLD0) & (hi.index <= HOLD1)]
        inter = (hi - lo)
        dev_in = inter[inter.index < HOLD0]
        hold_in = inter[(inter.index >= HOLD0) & (inter.index <= HOLD1)]
        print(f"holdout {h}d: hi dev_mean={dev_hi.mean():+.5f} hold_mean={hold_hi.mean():+.5f} "
              f"(n_hold={len(hold_hi)}) | interaction dev_mean={dev_in.mean():+.5f} "
              f"hold_mean={hold_in.mean():+.5f}")
        result[h]["hold_hi_sign_stable"] = np.sign(dev_hi.mean()) == np.sign(hold_hi.mean())
        result[h]["hold_in_sign_stable"] = np.sign(dev_in.mean()) == np.sign(hold_in.mean())

        rows.append(dict(horizon=h, hi_mean=hi.mean(), hi_t=tstat(hi), hi_hit=(hi>0).mean(),
                         hi_n=len(hi), lo_mean=lo.mean(), lo_t=tstat(lo),
                         inter_mean=d_mean, inter_t=d_t, inter_n=d_n,
                         hold_hi_stable=result[h]["hold_hi_sign_stable"],
                         hold_in_stable=result[h]["hold_in_sign_stable"]))

    df = pd.DataFrame(rows)
    df.to_csv(HERE / "H_E1_results.csv", index=False)
    print("\nsaved", HERE / "H_E1_results.csv")

    # ---- verdict (frozen thresholds) ----
    hi21_t = result[21]["hi_t"] = tstat(result[21]["hi"])
    hi21_mean = result[21]["hi"].mean()
    in21_t = result[21]["inter_t"]
    in63_t = result[63]["inter_t"]
    hold_ok = result[21]["hold_hi_sign_stable"] and result[21]["hold_in_sign_stable"]
    success = (hi21_t > 2) and (in21_t > 2) and hold_ok
    kill = (abs(hi21_t) < 2) or (in21_t < 2) or (in63_t < 2)
    print(f"\nPRIMARY high-tercile 21d: mean={hi21_mean:+.5f} t={hi21_t:+.3f}")
    print(f"interaction t: 21d={in21_t:+.3f} 63d={in63_t:+.3f}")
    print(f"holdout sign-stable (hi & interaction, 21d): {hold_ok}")
    print(f"SUCCESS={success}  KILL={kill}")
    return result


if __name__ == "__main__":
    main()
