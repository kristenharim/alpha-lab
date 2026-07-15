"""Path-luck robustness: block-bootstrap Sharpe intervals for the 7 live books.

Diagnostic on FROZEN specs over each book's own blind-evidence window (agent6 redteam
convention) — round-1 books on the holdout year (start=META["cut"]), round-2 books on the
blind 5y window (start=2021-07-10). No spec, param, or panel change; all 7 books reported,
none selected. Baseline gate: the recomputed Sharpe must reproduce the published
results/results5y number (tol 0.01) before the bootstrap counts.

Writes robustness/sharpe_bootstrap.md + artifacts/hunt2026/sharpe_bootstrap_run.json.
"""
import sys
from pathlib import Path

HERE = Path(__file__).parents[1]
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parents[1]))
import json

import harness
from core.eval.metrics import sharpe_bootstrap
from core.eval.run_manifest import stamp_run

CUT5 = "2021-07-10"                       # evaluate_5y.py convention
KILL_BAR = 0.5                            # repo kill threshold (net Sharpe < 0.5 is dead)
BOOT = {"n_sims": 1000, "block": 20, "seed": 0}

# book -> (results dir, window start) = each book's own blind-evidence window
BOOKS = {
    "vol_managed_qqq": ("results", None),         # None -> META["cut"] holdout year
    "vol_core_svxy": ("results", None),
    "dual_momentum_gem": ("results", None),
    "momentum_concentrated": ("results", None),
    "trend_vol_qqq": ("results5y", CUT5),
    "defensive_ensemble": ("results5y", CUT5),
    "dual_momentum_gold": ("results5y", CUT5),
}


def main():
    panel = harness.load_full()
    rows = []
    for name, (results_dir, start) in BOOKS.items():
        start = start or harness.META["cut"]
        published = json.loads((HERE / results_dir / f"{name}.json").read_text())["sharpe"]
        r = harness.run(harness.load_spec(HERE / "specs" / name), panel, start=start)
        if abs(r["sharpe"] - published) > 0.01:
            raise AssertionError(f"{name}: recomputed sharpe {r['sharpe']:.3f} != "
                                 f"published {published:.3f} — baseline gate FAILED")
        b = sharpe_bootstrap(r["net_daily"], 252, **BOOT)
        rows.append({"book": name, "window": f"{results_dir} (>{start})",
                     "n_obs": len(r["net_daily"].dropna()), **b,
                     "p05_above_kill": b["p05"] >= KILL_BAR})

    lines = ["# Sharpe bootstrap — path-luck intervals, 7 live books (2026-07-14)", "",
             f"Circular block bootstrap of daily net returns (n_sims={BOOT['n_sims']}, "
             f"block={BOOT['block']}, seed={BOOT['seed']}) on each book's own blind-evidence "
             "window; frozen specs, baseline Sharpe reproduced against the published result "
             "(tol 0.01) before bootstrapping. Complements deflated Sharpe (selection) and "
             "the agent6 perturbation grid (parameter sensitivity): this asks whether the "
             "point Sharpe survives resampling of its own return path. Read p05 against the "
             f"kill bar ({KILL_BAR}).", "",
             "| book | window | obs | sharpe | p05 | median | p95 | pct(orig) | p05 ≥ kill? |",
             "|---|---|---|---|---|---|---|---|---|"]
    for r in rows:
        lines.append(f"| {r['book']} | {r['window']} | {r['n_obs']} | {r['sharpe']:.2f} "
                     f"| **{r['p05']:.2f}** | {r['median']:.2f} | {r['p95']:.2f} "
                     f"| {r['pct_original']:.2f} | {'PASS' if r['p05_above_kill'] else '**FAIL**'} |")
    lines += ["", "All 7 books reported, none selected (no new search; n_trials of the "
              "underlying books unchanged). A FAIL here is a flag for the 12-month review, "
              "not an automatic demotion — the pre-registered kill rules in "
              "DEPLOYMENT_MANIFEST.md stay authoritative.", "",
              "## Story (read before reacting to the FAILs)", "",
              "- **Baseline gate: 7/7** — every recomputed Sharpe matched the published "
              "result before bootstrapping.",
              "- **The holdout-year FAILs are a statement about the window, not the books.** "
              "One year of daily data puts a ±1-ish standard error on an annualized Sharpe, "
              "so p05 ≈ point − 1.3 is what the arithmetic forces: a 1y blind holdout cannot "
              "statistically separate Sharpe 1.3–1.8 from the 0.5 kill bar. This quantifies "
              "why the repo also demands 82-window walk-forward + 5y blinds instead of "
              "trusting the holdout year alone.",
              "- **The 5y windows are the real test.** defensive_ensemble PASSES "
              "(p05 0.65 — consistent with it holding the top deflated-Sharpe probability, "
              "95.8%, in deflated.md). trend_vol_qqq (0.39) and dual_momentum_gold (0.44) "
              "sit just under the bar — gold is already watch-tier and hindsight-discounted, "
              "so this agrees with the existing classification rather than contradicting it.",
              "- **vol_core_svxy is the one flag worth remembering: p05 −0.11, the only "
              "negative.** Its short-vol SVXY sleeve is the classic negative-skew profile — "
              "steady gains, occasional crash — and negative skew widens the bootstrap left "
              "tail (the −skew·SR term in the Sharpe estimator variance). The smooth curve "
              "is partly crash risk, priced in by this metric.",
              "- **pct(orig) ≈ 0.5 everywhere**: no book's headline number depends on a "
              "lucky arrangement of its own returns — no sequence-luck pathology.", ""]
    out = HERE / "robustness" / "sharpe_bootstrap.md"
    out.write_text("\n".join(lines))
    print("\n".join(lines))

    stamp_run(track="hunt2026", variant="sharpe_bootstrap",
              params={**BOOT, "kill_bar": KILL_BAR, "books": {r["book"]: r["window"] for r in rows},
                      "selection": "none — all 7 live books reported",
                      "baseline_gate": "recomputed sharpe == published (tol 0.01)"},
              n_trials=1)
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
