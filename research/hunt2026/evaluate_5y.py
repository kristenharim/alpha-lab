"""5-year backdated evaluation: score specs from 2021-07-10 -> 2026-07-10.

Bar: net CAGR >= 18%. Results in results5y/ (write-once per spec).
HONESTY NOTE baked into every record: round-1 specs (fit window through 2025-07-10)
are NOT blind on 2021->2025 — this is a stress test for them. Round-2 specs
(fit on train5y only) ARE blind on the full window; the record carries a `blind` flag.
"""
import json
import sys
import traceback
from pathlib import Path

import numpy as np
import pandas as pd

import harness

HERE = Path(__file__).parent
CUT5 = "2021-07-10"
ROUND2_MARKER = "round2"  # spec dirs containing a file named `round2` are blind on 5y


def main(names):
    panel = harness.load_full()
    spy = harness.spy_benchmark(panel, start=CUT5)
    years = (panel.index[-1] - pd.Timestamp(CUT5)).days / 365.25
    results_dir = HERE / "results5y"
    results_dir.mkdir(exist_ok=True)

    spec_dirs = sorted((HERE / "specs").iterdir()) if not names else \
        [HERE / "specs" / n for n in names]
    rows = []
    for d in spec_dirs:
        if not (d / "spec.py").exists():
            continue
        out_path = results_dir / f"{d.name}.json"
        if out_path.exists():
            rows.append(json.loads(out_path.read_text()))
            print(f"{d.name}: result exists, SKIPPING (one shot)")
            continue
        try:
            r = harness.run(harness.load_spec(d), panel, start=CUT5)
            cagr = (1 + r["total_net"]) ** (1 / years) - 1
            net = r["net_daily"]
            yearly = {}
            nav = (1 + net).cumprod()
            ye = nav.resample("YE").last()
            prev = 1.0
            for k, v in ye.items():
                yearly[str(k.year)] = float(v / prev - 1)
                prev = float(v)
            rec = {"spec": d.name, "blind": (d / ROUND2_MARKER).exists(),
                   "total_net": r["total_net"], "cagr": cagr,
                   "sharpe": r["sharpe"], "ann_vol": r["ann_vol"], "max_dd": r["max_dd"],
                   "avg_gross_exposure": r["avg_gross_exposure"],
                   "avg_daily_turnover": r["avg_daily_turnover"],
                   "cost_drag_ann": r["cost_drag_ann"],
                   "gross_cap_violations": r["gross_cap_violations"],
                   "yearly": yearly,
                   "quarterly": {str(k.date()): float(v) for k, v in r["quarterly"].items()},
                   "pass_18cagr": bool(cagr >= 0.18), "error": None}
        except Exception:
            rec = {"spec": d.name, "total_net": None, "cagr": None,
                   "pass_18cagr": False, "error": traceback.format_exc()}
        out_path.write_text(json.dumps(rec, indent=2))
        rows.append(rec)
        print(f"{d.name}: " + ("ERROR" if rec["cagr"] is None else
              f"CAGR {rec['cagr']:+.2%} total {rec['total_net']:+.1%} DD {rec['max_dd']:+.1%}"))

    spy_cagr = (1 + spy["total_net"]) ** (1 / years) - 1
    ok = sorted([r for r in rows if r.get("cagr") is not None], key=lambda r: -r["cagr"])
    lines = [f"# hunt2026 5-year backdated results — {CUT5} → 2026-07-10 ({years:.1f}y)",
             "",
             f"SPY: total {spy['total_net']:+.1%}, CAGR **{spy_cagr:+.2%}**, "
             f"sharpe {spy['sharpe']:.2f}, maxDD {spy['max_dd']:+.1%}",
             "Round-1 specs are NOT blind on 2021-2025 (fit window overlapped) — stress test only.",
             "Round-2 specs (blind=True) were fit on data <= 2021-07-10 and are fully blind.", "",
             "| spec | blind | CAGR | total | sharpe | maxDD | avg gross | ≥18%/yr |",
             "|---|---|---|---|---|---|---|---|"]
    for r in ok:
        lines.append(f"| {r['spec']} | {'Y' if r.get('blind') else 'n'} | {r['cagr']:+.2%} "
                     f"| {r['total_net']:+.1%} | {r['sharpe']:.2f} | {r['max_dd']:+.1%} "
                     f"| {r['avg_gross_exposure']:.2f} | {'**PASS**' if r['pass_18cagr'] else 'fail'} |")
    for r in rows:
        if r.get("cagr") is None:
            lines.append(f"| {r['spec']} | | ERROR | | | | | fail |")
    (results_dir / "summary.md").write_text("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main(sys.argv[1:])
