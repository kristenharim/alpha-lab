"""EVALUATOR ONLY — one-shot blind scoring of frozen specs on the holdout year.

Usage: .venv/bin/python research/hunt2026/evaluate.py [spec_name ...]
Runs every dir under specs/ (or the named ones) through the shared harness on the
holdout window, writes results/<spec>.json and results/summary.md. No edits to any
spec after this runs — the first result per spec is THE result (results are
write-once: an existing results/<spec>.json is never overwritten).
"""
import json
import sys
import traceback
from pathlib import Path

import pandas as pd

import harness

HERE = Path(__file__).parent
CUT = harness.META["cut"]


def fmt_pct(x):
    return f"{x:+.2%}"


def main(names):
    panel = harness.load_full()
    spy = harness.spy_benchmark(panel, start=CUT)
    results_dir = HERE / "results"
    results_dir.mkdir(exist_ok=True)

    spec_dirs = sorted((HERE / "specs").iterdir()) if not names else \
        [HERE / "specs" / n for n in names]
    rows = []
    for d in spec_dirs:
        if not (d / "spec.py").exists():
            continue
        out_path = results_dir / f"{d.name}.json"
        if out_path.exists():
            print(f"{d.name}: result exists, SKIPPING (one shot per spec)")
            rows.append(json.loads(out_path.read_text()))
            continue
        try:
            r = harness.run(harness.load_spec(d), panel, start=CUT)
            rec = {"spec": d.name,
                   "total_net": r["total_net"], "total_gross": r["total_gross"],
                   "sharpe": r["sharpe"], "ann_vol": r["ann_vol"], "max_dd": r["max_dd"],
                   "avg_gross_exposure": r["avg_gross_exposure"],
                   "avg_daily_turnover": r["avg_daily_turnover"],
                   "cost_drag_ann": r["cost_drag_ann"],
                   "gross_cap_violations": r["gross_cap_violations"],
                   "monthly": {str(k.date()): float(v) for k, v in r["monthly"].items()},
                   "quarterly": {str(k.date()): float(v) for k, v in r["quarterly"].items()},
                   "pass_18": bool(r["total_net"] >= 0.18), "error": None}
        except Exception:
            rec = {"spec": d.name, "total_net": None, "pass_18": False,
                   "error": traceback.format_exc()}
        out_path.write_text(json.dumps(rec, indent=2))
        rows.append(rec)
        tn = rec["total_net"]
        print(f"{d.name}: {'ERROR' if tn is None else fmt_pct(tn)}")

    ok = [r for r in rows if r.get("total_net") is not None]
    ok.sort(key=lambda r: r["total_net"], reverse=True)
    lines = [f"# hunt2026 holdout results — blind year {CUT} → 2026-07-10",
             "",
             f"SPY same window: **{fmt_pct(spy['total_net'])}** "
             f"(sharpe {spy['sharpe']:.2f}, maxDD {fmt_pct(spy['max_dd'])})",
             f"Specs evaluated: {len(rows)} (trial count for deflation)", "",
             "| spec | net | gross | sharpe | vol | maxDD | avg gross exp | turnover/d | cost/yr | ≥18%? |",
             "|---|---|---|---|---|---|---|---|---|---|"]
    for r in ok:
        lines.append(f"| {r['spec']} | {fmt_pct(r['total_net'])} | {fmt_pct(r['total_gross'])} "
                     f"| {r['sharpe']:.2f} | {r['ann_vol']:.1%} | {fmt_pct(r['max_dd'])} "
                     f"| {r['avg_gross_exposure']:.2f} | {r['avg_daily_turnover']:.2%} "
                     f"| {r['cost_drag_ann']:.2%} | {'**PASS**' if r['pass_18'] else 'fail'} |")
    for r in rows:
        if r.get("total_net") is None:
            lines.append(f"| {r['spec']} | ERROR | | | | | | | | fail |")
    (results_dir / "summary.md").write_text("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main(sys.argv[1:])
