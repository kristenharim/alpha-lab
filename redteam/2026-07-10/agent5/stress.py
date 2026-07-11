"""Agent 5 — execution-realism stress grid for the 7 frozen hunt2026 books.

Re-implements the harness P&L convention locally (verified to parity vs harness.run
on the base case), then applies PREDECLARED execution perturbations:

  base           : 10/2 bps per side (frozen model), execute at close t
  half_costs     : 5/1 bps
  doubled        : 20/4 bps
  quadrupled     : 40/8 bps
  vol_stressed   : 3x cost on days with ^VIX close > 25 (predeclared), 1x otherwise
  delay1         : execute one bar late (targets shifted 1 day)
  delay2         : execute two bars late
  partial50      : each day only move 50% of the way to target
  missed10       : each day's rebalance independently missed w.p. 10% (5 seeds, mean/worst)

Windows: HOLDOUT (cut 2025-07-10 -> end) and FULL (2015-01-01 -> end) on panel_2005.
Benchmarks (naive, per DEPLOYMENT_MANIFEST) are scored at BASE costs — the bench is
never stressed, so book-minus-bench deltas are conservative against the book.

Run: cd ~/projects/alpha-lab && .venv/bin/python redteam/2026-07-10/agent5/stress.py
Outputs: stress_holdout.csv, stress_full.csv, participation.csv in this directory.
"""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path.home() / "projects" / "alpha-lab"
HUNT = ROOT / "research" / "hunt2026"
sys.path.insert(0, str(HUNT))
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))
import harness  # noqa: E402
from hunt_paper_run import BOOKS, _heal_etfs, _naive_spec  # noqa: E402

OUT = Path(__file__).parent
META = harness.META
CUT = META["cut"]


def prep_W(spec_mod, panel):
    """Weights exactly as harness.run computes them (incl. gross cap scaling)."""
    W = spec_mod.target_weights(panel).astype(float).fillna(0.0)
    gross = W.abs().sum(axis=1)
    scale = (harness.MAX_GROSS / gross).clip(upper=1.0).fillna(1.0)
    return W.mul(scale, axis=0)


def score(W_exec, panel, start, end=None, cost_mult=None, bps_scale=1.0):
    """Local replica of harness P&L on an executed-weight frame.
    cost_mult: optional per-day Series multiplier on costs."""
    close = panel["close"][W_exec.columns]
    rets = close.pct_change(fill_method=None)
    held = W_exec.shift(1)
    gross = (held * rets).sum(axis=1, min_count=1).fillna(0.0)
    bps = harness.per_side_bps(W_exec.columns) * bps_scale
    cost = (W_exec.diff().abs().fillna(W_exec.abs()) * (bps / 1e4)).sum(axis=1)
    if cost_mult is not None:
        cost = cost * cost_mult.reindex(cost.index).fillna(1.0)
    net = gross - cost
    idx = net.index[net.index > pd.Timestamp(start)]
    if end is not None:
        idx = idx[idx <= pd.Timestamp(end)]
    net = net.reindex(idx)
    nav = (1 + net).cumprod()
    yrs = len(idx) / 252
    return {
        "total_net": float(nav.iloc[-1] - 1),
        "cagr": float(nav.iloc[-1] ** (1 / yrs) - 1),
        "sharpe": float(net.mean() / net.std() * np.sqrt(252)) if net.std() > 0 else 0.0,
        "max_dd": float((nav / nav.cummax() - 1).min()),
        "cost_drag_ann": float((cost.reindex(idx)).mean() * 252),
    }


def exec_partial(W, alpha):
    V = W.to_numpy()
    E = np.zeros_like(V)
    prev = np.zeros(V.shape[1])
    for i in range(len(V)):
        prev = prev + alpha * (V[i] - prev)
        E[i] = prev
    return pd.DataFrame(E, index=W.index, columns=W.columns)


def exec_missed(W, p, seed):
    rng = np.random.default_rng(seed)
    V = W.to_numpy()
    E = np.zeros_like(V)
    prev = np.zeros(V.shape[1])
    miss = rng.random(len(V)) < p
    for i in range(len(V)):
        if not miss[i]:
            prev = V[i]
        E[i] = prev
    return pd.DataFrame(E, index=W.index, columns=W.columns)


def main():
    panel = _heal_etfs(pd.read_parquet(HUNT / "panel_2005.parquet"))
    vix = panel["close"]["^VIX"]
    stress_mult = pd.Series(np.where(vix > 25, 3.0, 1.0), index=vix.index)
    print(f"panel {panel.index[0].date()} -> {panel.index[-1].date()}, "
          f"VIX>25 on {(vix > 25).mean():.1%} of days")

    windows = {"holdout": (CUT, None), "full": ("2015-01-01", None)}
    rows = {w: [] for w in windows}
    part_rows = []

    for name, bench_kind in BOOKS.items():
        spec = harness.load_spec(HUNT / "specs" / name)
        W = prep_W(spec, panel)
        minw = float(W.min().min())
        # parity check vs harness.run on holdout window
        h = harness.run(spec, panel, start=CUT)
        mine = score(W, panel, start=CUT)
        assert abs(h["total_net"] - mine["total_net"]) < 1e-9, (name, h["total_net"], mine["total_net"])

        Wb = prep_W(_naive_spec(bench_kind), panel)

        variants = {
            "base": dict(),
            "half_costs": dict(bps_scale=0.5),
            "doubled": dict(bps_scale=2.0),
            "quadrupled": dict(bps_scale=4.0),
            "vol_stressed": dict(cost_mult=stress_mult),
        }
        for wname, (start, end) in windows.items():
            bench = score(Wb, panel, start=start, end=end)
            for vname, kw in variants.items():
                r = score(W, panel, start=start, end=end, **kw)
                rows[wname].append({"book": name, "variant": vname, **r,
                                    "excess_vs_naive": r["total_net"] - bench["total_net"]})
            for k, lbl in ((1, "delay1"), (2, "delay2")):
                r = score(W.shift(k).fillna(0.0), panel, start=start, end=end)
                rows[wname].append({"book": name, "variant": lbl, **r,
                                    "excess_vs_naive": r["total_net"] - bench["total_net"]})
            r = score(exec_partial(W, 0.5), panel, start=start, end=end)
            rows[wname].append({"book": name, "variant": "partial50", **r,
                                "excess_vs_naive": r["total_net"] - bench["total_net"]})
            ms = [score(exec_missed(W, 0.10, s), panel, start=start, end=end) for s in range(5)]
            for agg, pick in (("missed10_mean", lambda k: float(np.mean([m[k] for m in ms]))),
                              ("missed10_worst", lambda k: float(min([m[k] for m in ms]) if k != "cost_drag_ann"
                                                                 else max([m[k] for m in ms])))):
                rows[wname].append({"book": name, "variant": agg,
                                    **{k: pick(k) for k in ms[0]},
                                    "excess_vs_naive": pick("total_net") - bench["total_net"]})
        # participation: worst-case daily traded dollars vs 20d median dollar volume,
        # at $100k account (equity/7 per book), holdout window only
        notional = 100_000 / 7
        dW = W.diff().abs()
        dollars = dW * notional
        dv = (panel["close"][W.columns] * panel["volume"][W.columns]).rolling(20).median()
        pr = (dollars / dv).loc[dollars.index > pd.Timestamp(CUT)]
        worst = pr.max().dropna().sort_values(ascending=False)
        if len(worst):
            part_rows.append({"book": name, "min_weight": round(minw, 6),
                              "worst_symbol": worst.index[0],
                              "worst_participation": float(worst.iloc[0]),
                              "median_participation": float(pr.stack().median())})
        print(f"{name}: parity OK, min weight {minw:.4f}")

    for wname in windows:
        df = pd.DataFrame(rows[wname]).round(6)
        df.to_csv(OUT / f"stress_{wname}.csv", index=False)
        print(f"wrote stress_{wname}.csv ({len(df)} rows)")
    pd.DataFrame(part_rows).to_csv(OUT / "participation.csv", index=False)
    print("wrote participation.csv")


if __name__ == "__main__":
    main()
