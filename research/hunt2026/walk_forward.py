"""Walk-forward evaluation of frozen specs: rolling 12-month windows, quarterly steps.

Because every spec is FROZEN (weights don't depend on the scoring window), one full-panel
run per spec yields the daily net series; rolling windows are then read off that stream.
Convention note: windows share one continuous P&L path (no fresh cost ramp-in per window)
— slightly flattering vs independent runs, identically so for every spec.

Honesty flags per spec:
- fit_end: windows ending before this date overlap the spec's fit window (in-sample-ish).
- data_start: ETF specs run from 2006; stock specs only from 2015 (no fake pre-2014 stocks).

Usage: walk_forward.py [--panel panel_2005.parquet] [spec ...]
Writes walkforward/<spec>.json + walkforward/summary.md.
"""
import json
import sys
import traceback
from pathlib import Path

import numpy as np
import pandas as pd

import harness

HERE = Path(__file__).parent
WIN, STEP = 252, 63  # 12m windows, quarterly steps

# fit-window end per spec generation (used to flag in-sample-ish windows)
FIT_END = {"round1": "2025-07-10", "round2": "2021-07-10", "benchmark": "1900-01-01"}

REGIMES = [("GFC", "2007-10-01", "2009-06-30"), ("euro_2011", "2011-05-01", "2011-12-31"),
           ("china_2015", "2015-06-01", "2016-02-29"), ("volmageddon_2018", "2018-01-15", "2018-12-31"),
           ("covid_2020", "2020-02-15", "2020-12-31"), ("inflation_bear_2022", "2022-01-01", "2022-12-31"),
           ("ai_rally_2023", "2023-01-01", "2023-12-31"), ("expansion_2024_26", "2024-01-01", "2026-07-10")]


def spec_generation(d: Path) -> str:
    if (d / "benchmark").exists():
        return "benchmark"
    return "round2" if (d / "round2").exists() else "round1"


def rolling_windows(net: pd.Series):
    """(end_date, 12m_net_return) at quarterly steps; skips windows with dead (all-zero) tails."""
    nav = (1 + net).cumprod()
    out = []
    for i in range(WIN, len(nav), STEP):
        w = net.iloc[i - WIN:i]
        if (w == 0).mean() > 0.5:  # spec not active (warm-up / no data) — not a real window
            continue
        out.append((net.index[i - 1], float((1 + w).prod() - 1)))
    return out


def main(argv):
    panel_name = "panel_2005.parquet"
    if argv and argv[0] == "--panel":
        panel_name, argv = argv[1], argv[2:]
    panel = pd.read_parquet(HERE / panel_name)
    out_dir = HERE / "walkforward"
    out_dir.mkdir(exist_ok=True)

    spy_net = harness.spy_benchmark(panel)["net_daily"]
    spy_windows = dict(rolling_windows(spy_net))

    spec_dirs = sorted((HERE / "specs").iterdir()) if not argv else [HERE / "specs" / n for n in argv]
    rows = []
    for d in spec_dirs:
        if not (d / "spec.py").exists():
            continue
        gen = spec_generation(d)
        try:
            r = harness.run(harness.load_spec(d), panel)
            wins = rolling_windows(r["net_daily"])
            if not wins:
                raise ValueError("no active windows")
            fit_end = pd.Timestamp(FIT_END[gen])
            rets = np.array([w[1] for w in wins])
            oos = np.array([w[1] for w in wins if w[0] > fit_end])
            vs_spy = np.array([w[1] - spy_windows[w[0]] for w in wins if w[0] in spy_windows])
            regime = {}
            for name, a, b in REGIMES:
                rr = [w[1] for w in wins if pd.Timestamp(a) <= w[0] <= pd.Timestamp(b)]
                if rr:
                    regime[name] = {"n": len(rr), "median": float(np.median(rr)),
                                    "worst": float(min(rr))}
            rec = {"spec": d.name, "generation": gen,
                   "n_windows": len(wins), "n_oos_windows": int(len(oos)),
                   "first_window_end": str(wins[0][0].date()), "last_window_end": str(wins[-1][0].date()),
                   "median_12m": float(np.median(rets)), "mean_12m": float(rets.mean()),
                   "pct_ge_18": float((rets >= 0.18).mean()),
                   "pct_positive": float((rets > 0).mean()),
                   "pct_beat_spy": float((vs_spy > 0).mean()) if len(vs_spy) else None,
                   "median_excess_vs_spy": float(np.median(vs_spy)) if len(vs_spy) else None,
                   "worst_12m": float(rets.min()), "best_12m": float(rets.max()),
                   "oos_median_12m": float(np.median(oos)) if len(oos) else None,
                   "oos_pct_ge_18": float((oos >= 0.18).mean()) if len(oos) else None,
                   "regimes": regime,
                   "windows": [(str(k.date()), v) for k, v in wins], "error": None}
        except Exception:
            rec = {"spec": d.name, "generation": gen, "error": traceback.format_exc()}
        (out_dir / f"{d.name}.json").write_text(json.dumps(rec, indent=2))
        rows.append(rec)
        print(f"{d.name}: " + (f"{rec['n_windows']}w median {rec['median_12m']:+.1%} "
              f"≥18%: {rec['pct_ge_18']:.0%} beatSPY: {rec['pct_beat_spy']:.0%} "
              f"worst {rec['worst_12m']:+.1%}" if not rec["error"] else "ERROR"))

    ok = sorted([r for r in rows if not r["error"]],
                key=lambda r: -(r["median_excess_vs_spy"] or -9))
    spy_rets = np.array(list(spy_windows.values()))
    lines = ["# hunt2026 walk-forward — rolling 12m windows, quarterly steps",
             "",
             f"Panel: {panel_name}. SPY: {len(spy_rets)} windows, median "
             f"{np.median(spy_rets):+.1%}, ≥18% in {(spy_rets >= 0.18).mean():.0%}, "
             f"worst {spy_rets.min():+.1%}.",
             "Windows before a spec's fit_end overlap its fit window — `oos_*` columns are the",
             "clean subset (round1 fit_end 2025-07-10; round2 2021-07-10). Adjacent windows",
             "overlap (252d window, 63d step): ~4x fewer effectively independent draws.", "",
             "| spec | gen | wins | median 12m | ≥18% | >0 | beat SPY | med excess | worst | oos med | oos ≥18% |",
             "|---|---|---|---|---|---|---|---|---|---|---|"]
    for r in ok:
        fmt = lambda v, p="+.1%": ("" if v is None else f"{v:{p}}")
        lines.append(f"| {r['spec']} | {r['generation'][:5]} | {r['n_windows']} "
                     f"| {r['median_12m']:+.1%} | {r['pct_ge_18']:.0%} | {r['pct_positive']:.0%} "
                     f"| {fmt(r['pct_beat_spy'], '.0%')} | {fmt(r['median_excess_vs_spy'])} "
                     f"| {r['worst_12m']:+.1%} | {fmt(r['oos_median_12m'])} "
                     f"| {fmt(r['oos_pct_ge_18'], '.0%')} |")
    for r in rows:
        if r["error"]:
            lines.append(f"| {r['spec']} | {r['generation'][:5]} | ERROR | | | | | | | | |")
    (out_dir / "summary.md").write_text("\n".join(lines) + "\n")
    print("\n".join(lines[:10]))


if __name__ == "__main__":
    main(sys.argv[1:])
