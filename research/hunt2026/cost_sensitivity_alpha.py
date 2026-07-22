"""Does any spec still have alpha once it pays measured costs, faces its OWN benchmark, and is
charged for the fact that twenty of them were tried?

cost_sensitivity.py scored excess against the spec's gross exposure times SPY, which is the
verdict memo's convention. That convention has a hole the spec list itself exposes:
bench_qqq_buyhold, a passive hold with no strategy in it, shows +9.28% of "excess", because the
benchmark is SPY and the holding is QQQ. Every QQQ-shaped spec inherits that premium for free.

So the benchmark is not chosen here, it is FITTED. Each spec's daily net is regressed on a fixed,
declared menu of liquid ETFs with a constant, and the constant is the alpha. Newey-West standard
errors, reused from research/attribution/run_attribution.py. A levered QQQ book gets a QQQ beta
near its leverage and an alpha near zero, which is the honest answer that gross-exposure-times-SPY
could not give.

Then the selection charge. Twenty specs were tried, so the best Sharpe in the field is partly the
luckiest draw. The deflated Sharpe from robustness.py answers "is this Sharpe bigger than what the
luckiest of N tries would produce by chance", recomputed here on the HOLDOUT window at each cost
level rather than the 5y window.

The menu is fixed in advance and identical for every spec. Picking regressors per spec would be
the same cherry-picking this exists to remove.

NOT A RE-SCORING: results/ stays write-once and untouched, and the holdout was spent on
2026-07-10. Re-pricing an already-seen return stream cannot un-spend it.

Usage: .venv/bin/python research/hunt2026/cost_sensitivity_alpha.py
Writes results_sensitivity/alpha.md.
"""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from statistics import NormalDist

HERE = Path(__file__).parent
REPO = HERE.parents[1]
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(REPO))

import harness   # noqa: E402
from research.attribution.run_attribution import nw_ols   # noqa: E402

ND = NormalDist()
# Declared in advance, identical for every spec: broad equity, size, duration, and the two real
# diversifiers in the sandbox. Six regressors on ~250 daily observations.
MENU = ["SPY", "QQQ", "IWM", "TLT", "GLD", "DBC"]
SCENARIOS = (("frozen", 10.0), ("measured", 58.0))


def fmt(x):
    return f"{x:+.2%}"


def bench_returns(panel):
    """Daily simple returns for the benchmark menu over the holdout window.
    The panel is (field, ticker) columned, same access the harness itself uses."""
    closes = panel["close"][MENU]
    return closes.pct_change().loc[harness.META["cut"]:].dropna(how="any")


def score(spec_dir, panel, stock_bps):
    original = harness.STOCK_BPS
    harness.STOCK_BPS = stock_bps
    try:
        return harness.run(harness.load_spec(spec_dir), panel, start=harness.META["cut"])
    finally:
        harness.STOCK_BPS = original


def fitted_alpha(net_daily, bench):
    """Annualized alpha and its Newey-West t, against the fitted benchmark mix."""
    y, X = net_daily.align(bench, join="inner", axis=0)
    if len(y) < 60:
        return None
    design = np.column_stack([np.ones(len(X)), X.values])
    beta, se, t, r2, n = nw_ols(y.values, design)
    return {"alpha_ann": float(beta[0] * 252), "t": float(t[0]), "r2": float(r2),
            "betas": {m: float(b) for m, b in zip(MENU, beta[1:])}}


def deflated(net_daily, all_sharpes):
    """P(this Sharpe beats the luckiest of N tries), robustness.py's formula on the holdout."""
    sr = net_daily.mean() / net_daily.std()
    n_trials = len(all_sharpes)
    em = 0.5772156649
    sr0 = np.std(all_sharpes, ddof=1) * ((1 - em) * ND.inv_cdf(1 - 1 / n_trials)
                                         + em * ND.inv_cdf(1 - 1 / (n_trials * np.e)))
    T = len(net_daily)
    g3, g4 = float(net_daily.skew()), float(net_daily.kurt()) + 3
    denom = np.sqrt(max(1e-12, 1 - g3 * sr + (g4 - 1) / 4 * sr ** 2))
    return {"sharpe_ann": float(sr * np.sqrt(252)),
            "dsr": float(ND.cdf((sr - sr0) * np.sqrt(T - 1) / denom)),
            "luck_bar_ann": float(sr0 * np.sqrt(252))}


def main():
    panel = harness.load_full()
    bench = bench_returns(panel)
    spec_dirs = [d for d in sorted((HERE / "specs").iterdir()) if (d / "spec.py").exists()]
    # robustness.py's convention: a dir carrying a `benchmark` marker is a reference point, not a
    # candidate. They are shown for scale but never counted as trials and never called alpha,
    # which is what stopped a passive QQQ hold scoring a t of 6.4 on a numerically zero intercept.
    is_bench = {d.name: (d / "benchmark").exists() for d in spec_dirs}
    n_trials = sum(1 for d in spec_dirs if not is_bench[d.name])

    runs = {label: {} for label, _ in SCENARIOS}
    for d in spec_dirs:
        for label, bps in SCENARIOS:
            try:
                runs[label][d.name] = score(d, panel, bps)
            except Exception as e:
                print(f"{d.name} [{label}] skipped: {e}", file=sys.stderr)

    out_rows = {}
    for label, _ in SCENARIOS:
        sharpes = [r["net_daily"].mean() / r["net_daily"].std()
                   for name, r in runs[label].items() if not is_bench[name]]
        for name, r in runs[label].items():
            rec = out_rows.setdefault(name, {})
            rec[label] = {**(fitted_alpha(r["net_daily"], bench) or {}),
                          **deflated(r["net_daily"], sharpes),
                          "net": r["total_net"]}

    ranked = sorted(out_rows.items(),
                    key=lambda kv: kv[1].get("measured", {}).get("alpha_ann", -9), reverse=True)

    lines = [
        "# hunt2026 holdout: fitted-benchmark alpha, at measured cost, deflated for the trial count",
        "",
        "**Sensitivity analysis, not a re-scoring.** `results/` is write-once and untouched.",
        "",
        f"Benchmark menu, fixed in advance and identical for every spec: `{', '.join(MENU)}`.",
        "Alpha is the regression constant, annualized, with Newey-West t. Beta-matched excess in",
        "`summary.md` used gross exposure times SPY, which credits a QQQ book with QQQ's own",
        "outperformance; this does not.",
        "",
        "DSR is the probability the spec's Sharpe beats what the luckiest of "
        f"{n_trials} candidate tries would show by chance. Below about 50% the result is",
        "indistinct from selection luck. Specs marked `benchmark` are reference points: not",
        "counted as trials, never eligible for a verdict.",
        "",
        "| spec | alpha frozen | alpha at 58 | t | R² | Sharpe | DSR | verdict |",
        "|---|---|---|---|---|---|---|---|",
    ]
    survivors = []
    for name, rec in ranked:
        fr, me = rec.get("frozen", {}), rec.get("measured", {})
        if "alpha_ann" not in me:
            continue
        alive = (not is_bench[name]) and me["alpha_ann"] > 0 and me["t"] > 2 and me["dsr"] > 0.5
        if alive:
            survivors.append(name)
        verdict = ("benchmark" if is_bench[name] else
                   "ALPHA" if alive else
                   "positive, weak" if me["alpha_ann"] > 0 else "no")
        lines.append(f"| {name} | {fmt(fr.get('alpha_ann', 0))} | {fmt(me['alpha_ann'])} "
                     f"| {me['t']:.2f} | {me['r2']:.2f} | {me['sharpe_ann']:.2f} "
                     f"| {me['dsr']:.0%} | {verdict} |")

    lines += ["",
              f"Bar for ALPHA: positive alpha, Newey-West t above 2, and DSR above 50%. "
              f"**{len(survivors)} of {n_trials}** candidates clear it at measured cost"
              + (f": {', '.join(survivors)}." if survivors else "."),
              "",
              "Every caveat from summary.md still applies, and one more: the cost estimate is 25",
              "fills through a simulated paper fill engine, and it is now carrying a conclusion",
              "about which strategies have alpha. That is a lot of weight on a small sample.",
              ]
    out = HERE / "results_sensitivity"
    out.mkdir(exist_ok=True)
    (out / "alpha.md").write_text("\n".join(lines) + "\n")
    (out / "alpha.json").write_text(json.dumps(out_rows, indent=2, default=float))
    print("\n".join(lines))


if __name__ == "__main__":
    main()
