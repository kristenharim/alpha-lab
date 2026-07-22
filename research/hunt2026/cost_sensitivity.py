"""What the holdout result looks like if single-name execution really costs what we measured.

NOT A RE-SCORING. The blind holdout was spent on 2026-07-10 and results/ is write-once; those
numbers are the result and nothing here replaces them. This re-prices the SAME already-seen return
streams under a different cost assumption, which is a sensitivity analysis and can only ever be
read as one. A spec that survives here has not passed a second test; it has failed to die under a
harsher one.

Why ask. The frozen model charges 10 bps/side on single names (harness.STOCK_BPS) and 2 on ETFs.
EXP-OPS-REALITY then measured live paper execution on the dedicated single-name account at roughly
+58 bps per fill, with a direction-independent floor near +42 (research/hunt2026/exec_side_split.py
and memos/band-ruling-2026-07-21.md). The ETF books measured about zero against their assumed 2, so
the ETF side is left alone: only STOCK_BPS moves.

Caveats that bound every number below. The cost estimate is 25 fills over 4 sessions through
Alpaca's SIMULATED paper fill engine, so it bounds the backtest-versus-paper question and says
nothing about live execution. Turnover here is each spec's own backtested turnover, which is the
right basis, but the measured cost came from one book's turnover pattern and need not transfer.

Usage: .venv/bin/python research/hunt2026/cost_sensitivity.py [spec_name ...]
Writes results_sensitivity/summary.md. Never writes results/.
"""
import json
import sys
from pathlib import Path

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))

import harness   # noqa: E402

# The frozen assumption, the direction-independent floor, and the measured mean.
SCENARIOS = (("frozen", 10.0), ("floor", 42.0), ("measured", 58.0))
PASS_BAR = 0.18          # the pre-registered bar the hunt was scored against


def fmt(x):
    return f"{x:+.2%}"


def score(spec_dir, panel, stock_bps):
    """One spec's holdout run with STOCK_BPS swapped. ETF_BPS is deliberately untouched."""
    original = harness.STOCK_BPS
    harness.STOCK_BPS = stock_bps
    try:
        return harness.run(harness.load_spec(spec_dir), panel, start=harness.META["cut"])
    finally:
        harness.STOCK_BPS = original


def main(names):
    panel = harness.load_full()
    spy = harness.spy_benchmark(panel, start=harness.META["cut"])
    spec_dirs = sorted((HERE / "specs").iterdir()) if not names else \
        [HERE / "specs" / n for n in names]

    rows = []
    for d in spec_dirs:
        if not (d / "spec.py").exists():
            continue
        rec = {"spec": d.name}
        for label, bps in SCENARIOS:
            try:
                r = score(d, panel, bps)
                # beta-matched benchmark per memos/hunt2026-verdict.md: the spec's own average
                # gross exposure times SPY over the same window. Exposure does not move with
                # costs, so the benchmark is fixed per spec and the excess absorbs the full
                # cost increase. Raw net flatters a levered book; this is the honest column.
                bench = r["avg_gross_exposure"] * spy["total_net"]
                rec[label] = {"net": r["total_net"], "sharpe": r["sharpe"],
                              "cost_drag_ann": r["cost_drag_ann"],
                              "turnover": r["avg_daily_turnover"],
                              "gross_exp": r["avg_gross_exposure"],
                              "beta_matched": bench, "excess": r["total_net"] - bench}
            except Exception as e:                     # a broken spec must not stop the sweep
                rec[label] = {"net": None, "error": str(e)}
        rows.append(rec)
        m, f = rec["measured"].get("net"), rec["frozen"].get("net")
        print(f"{d.name:<28} frozen {fmt(f) if f is not None else 'ERROR':>8}   "
              f"measured {fmt(m) if m is not None else 'ERROR':>8}")

    ok = [r for r in rows if r["frozen"].get("net") is not None]
    ok.sort(key=lambda r: r["frozen"]["net"], reverse=True)

    out = HERE / "results_sensitivity"
    out.mkdir(exist_ok=True)
    lines = [
        "# hunt2026 holdout, re-priced at measured execution cost",
        "",
        "**Sensitivity analysis, not a re-scoring.** The blind holdout was spent on 2026-07-10;",
        "`results/` is write-once and untouched. This re-prices the same already-seen return",
        "streams under a harsher single-name cost. Surviving here is not passing a second test.",
        "",
        f"SPY over the same window: **{fmt(spy['total_net'])}**. Pre-registered bar: "
        f"{PASS_BAR:.0%} net.",
        "",
        "`frozen` = 10 bps/side, the pre-registered model. `floor` = 42 bps, the",
        "direction-independent part of measured execution. `measured` = 58 bps, its mean.",
        "ETF costs are unchanged at 2 bps: those books measured about zero against that.",
        "",
        "Raw net first, then the column that matters: excess over a beta-matched SPY, which is",
        "the spec's own average gross exposure times SPY. A 2x book returning 30% while SPY",
        "returns 22% has produced nothing.",
        "",
        "| spec | turnover/d | gross exp | net at 58 | beta-matched | excess frozen | "
        "excess at 58 | alpha survives? |",
        "|---|---|---|---|---|---|---|---|",
    ]
    ok.sort(key=lambda r: r["measured"].get("excess", -9), reverse=True)
    for r in ok:
        fr, me = r["frozen"], r.get("measured", {})
        alive = me.get("excess") is not None and me["excess"] > 0
        lines.append(
            f"| {r['spec']} | {fr['turnover']:.2%} | {fr['gross_exp']:.2f} "
            f"| {fmt(me['net']) if me.get('net') is not None else 'n/a'} "
            f"| {fmt(fr['beta_matched'])} | {fmt(fr['excess'])} "
            f"| {fmt(me['excess']) if me.get('excess') is not None else 'n/a'} "
            f"| {'yes' if alive else 'NO'} |")

    passed_frozen = [r for r in ok if r["frozen"]["net"] >= PASS_BAR]
    passed_measured = [r for r in ok if r.get("measured", {}).get("net") is not None
                       and r["measured"]["net"] >= PASS_BAR]
    alpha_frozen = [r for r in ok if r["frozen"]["excess"] > 0]
    alpha_measured = [r for r in ok if r.get("measured", {}).get("excess") is not None
                      and r["measured"]["excess"] > 0]
    lines += ["",
              f"- cleared the {PASS_BAR:.0%} bar at frozen cost: **{len(passed_frozen)}** "
              f"of {len(ok)}; at 58 bps: **{len(passed_measured)}**",
              f"- POSITIVE beta-matched excess at frozen cost: **{len(alpha_frozen)}**; "
              f"at 58 bps: **{len(alpha_measured)}**",
              "",
              "The second line is the one that decides anything. The bar was 18% while SPY did "
              f"{fmt(spy['total_net'])}, so clearing it never meant much.",
              ]
    (out / "summary.md").write_text("\n".join(lines) + "\n")
    (out / "rows.json").write_text(json.dumps(rows, indent=2))
    print("\n" + "\n".join(lines[-6:]))
    print(f"\nwrote {out}/summary.md")


if __name__ == "__main__":
    main(sys.argv[1:])
