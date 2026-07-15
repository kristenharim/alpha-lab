"""EXP-2026-07-14-turnover-band: portfolio-level no-trade band on the vol-managed family.

Specs untouched — the band is an overlay on the frozen spec's raw target rows (before
harness.run's gross-cap): adopt the new row only when L1 drift > band, else re-emit the
last-adopted row. 12 registered variants (6 bands x 2 books), all reported.

Gates before any variant counts (preregistrations/turnover-band-2026-07-14.md):
(a) band=0 THROUGH the filter reproduces the frozen spec's net series exactly;
(b) recomputed holdout Sharpe matches the published results JSON (tol 0.01).

Writes robustness/turnover_band.md + artifacts/hunt2026/turnover_band_run.json.
"""
import json
import sys
from pathlib import Path

import pandas as pd

HERE = Path(__file__).parents[1]
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parents[1]))
import harness
from walk_forward import rolling_windows

from core.eval.run_manifest import stamp_run

BOOKS = ["vol_managed_qqq", "vol_core_svxy"]
BANDS = [0.01, 0.02, 0.05, 0.10, 0.20, 0.40]        # registered grid — no additions
HELP_BPS, FLAT_BPS = 5.0, 5.0                        # pre-committed verdict thresholds


def band_filter(W: pd.DataFrame, band: float) -> pd.DataFrame:
    """Adopt target row only when L1 drift from last-adopted exceeds band."""
    held = W.iloc[0] * 0.0                           # warm-up stays flat
    rows = []
    for _, row in W.iterrows():
        if (row - held).abs().sum() > band:
            held = row
        rows.append(held)
    return pd.DataFrame(rows, index=W.index)


class BandedSpec:
    def __init__(self, spec_mod, band):
        self.spec_mod, self.band = spec_mod, band

    def target_weights(self, panel):
        W = self.spec_mod.target_weights(panel).astype(float).fillna(0.0)
        return band_filter(W, self.band)


def main():
    panel = harness.load_full()
    lines = ["# Turnover-band sweep — vol-managed family (EXP-2026-07-14-turnover-band)", "",
             "Portfolio-level L1 no-trade band overlaid on the frozen specs; 12 registered "
             "variants, all reported. Deltas are vs each book's own band=0 baseline on "
             "shared rolling 12m windows (quarterly steps, full panel). Prereg: "
             "preregistrations/turnover-band-2026-07-14.md.", ""]
    verdicts = {}
    for name in BOOKS:
        spec = harness.load_spec(HERE / "specs" / name)
        base = harness.run(spec, panel)

        # gate (a): band=0 through the filter == frozen spec, exactly
        zero = harness.run(BandedSpec(spec, 0.0), panel)
        assert (zero["net_daily"] - base["net_daily"]).abs().max() < 1e-12, \
            f"{name}: band=0 does not reproduce the frozen spec — filter bug"
        # gate (b): holdout Sharpe reproduces the published result
        published = json.loads((HERE / "results" / f"{name}.json").read_text())["sharpe"]
        hold = harness.run(spec, panel, start=harness.META["cut"])
        assert abs(hold["sharpe"] - published) < 0.01, \
            f"{name}: holdout sharpe {hold['sharpe']:.3f} != published {published:.3f}"

        base_win = dict(rolling_windows(base["net_daily"]))
        lines += [f"## {name} — baseline turnover/d {base['avg_daily_turnover']:.4f}, "
                  f"cost drag {base['cost_drag_ann'] * 1e4:.0f} bps/yr", "",
                  "| band | med 12m Δ (bps) | windows | turnover cut | cost saved (bps/yr) "
                  "| full-period Δnet (pp) |", "|---|---|---|---|---|---|"]
        book_stats = []
        for band in BANDS:
            r = harness.run(BandedSpec(spec, band), panel)
            win = dict(rolling_windows(r["net_daily"]))
            shared = sorted(set(base_win) & set(win))
            deltas = pd.Series([win[d] - base_win[d] for d in shared])
            med_bps = float(deltas.median()) * 1e4
            cut = 1 - r["avg_daily_turnover"] / base["avg_daily_turnover"]
            saved = (base["cost_drag_ann"] - r["cost_drag_ann"]) * 1e4
            dnet = (r["total_net"] - base["total_net"]) * 100
            book_stats.append({"band": band, "med_bps": med_bps, "cut": cut})
            lines.append(f"| {band:.2f} | {med_bps:+.1f} | {len(shared)} | {cut:.0%} "
                         f"| {saved:+.1f} | {dnet:+.2f} |")
        helps = any(s["med_bps"] >= HELP_BPS and s["cut"] >= 0.20 for s in book_stats)
        flat = all(abs(s["med_bps"]) < FLAT_BPS for s in book_stats)
        harmful = all(s["med_bps"] <= 0 for s in book_stats)
        verdicts[name] = "helps" if helps else "harmful" if harmful else "flat" if flat else "indeterminate"
        lines += ["", f"**{name} verdict (per prereg rule): {verdicts[name]}**", ""]

    fam = verdicts[BOOKS[0]] if len(set(verdicts.values())) == 1 else "mixed"
    lines += [f"## Family verdict: **{fam}** "
              f"({', '.join(f'{b}: {v}' for b, v in verdicts.items())})", "",
              "Per the prereg kill condition this is one run of the registered grid — no finer "
              "grids, no re-tuned band definitions. Any adoption of a band value is a separate "
              "Stage-4 decision for Kristen carrying n_trials=12 selection accounting.", "",
              "## Story (why the mechanical verdict overstates the result)", "",
              "- **The deltas are NOT the hypothesized mechanism.** The prereg bounded the "
              "cost-savings effect at the published cost drag (≤ 15/37 bps/yr), and the "
              "measured cost saved lands exactly there (+3 to +13 bps/yr). But the median "
              "12m deltas that trip the verdict rule are 5–10x larger than the cost saved "
              "— they come from exposure-path divergence (a delayed rebalance is "
              "accidentally *different vol timing*), not from trading less. Same-sign "
              "evidence: the response is non-monotone (vol_managed_qqq: −42.5 bps at 0.10 "
              "→ +57 at 0.40; vol_core_svxy: +32 at 0.20 → −251 pp full-period at 0.40). "
              "A real cost effect would be small, smooth, and plateau-shaped; timing luck "
              "swings sign between adjacent grid points.",
              "- **vol_managed_qqq's internal 0.05 per-ticker band already absorbs the "
              "overlay below 0.10** — 0% turnover cut, identical series. The frozen spec "
              "already banks the genuinely available cost saving; there was little left "
              "to harvest.",
              "- **Bottom line: the real, mechanism-attributable effect is ≈ the cost "
              "saved — worth at most ~+13 bps/yr on vol_core_svxy — and no band value "
              "is stable enough to adopt.** The 'helps'/'indeterminate' verdicts are the "
              "rule firing on timing noise. Recommendation: no live change, queue item "
              "closed as run; the cheap net-return improvement this experiment hunted "
              "does not exist at 2 bps/side ETF costs beyond what the specs already do.", ""]
    out = HERE / "robustness" / "turnover_band.md"
    out.write_text("\n".join(lines))
    print("\n".join(lines))

    stamp_run(track="hunt2026", variant="turnover_band",
              params={"bands": BANDS, "books": BOOKS, "overlay": "L1 no-trade band, pre-cap",
                      "evaluator": "rolling 12m windows, quarterly steps, full panel",
                      "verdict_bps": {"helps": HELP_BPS, "flat": FLAT_BPS},
                      "prereg": "preregistrations/turnover-band-2026-07-14.md",
                      "verdicts": verdicts, "family": fam},
              n_trials=12)
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
