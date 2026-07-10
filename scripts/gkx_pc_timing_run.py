"""PC factor-timing run (HYP-004 revival): PCA-compress the Chen-Zimmermann anomaly panel, time the
top principal components, map the tilt back to a tradable signal book, score it against BOTH
equal-weighting all signals (the 2.10 that killed the rotation) and equal-weighting the PCs (does
timing beat just holding the factors?).

Reuses the GKX track's data loader + OOS timing model + the shared backtest/scorecard. Full firm-level
GKX stays blocked on WRDS; this is the signal-level revival the gkx post-mortem asked for.

Usage: .venv/bin/python scripts/gkx_pc_timing_run.py [--k 5 10] [--start 1980-01-01] [--cost-bps 5]
(first: pip install openassetpricing, or drop the CZ file at data/raw/cz_portfolios.parquet)

Alignment: signal weights at date t use info through t (PC predictions are OOS), and `backtest` lags
weights one period internally, so weight(t) earns the realized signal return at t+1. We feed the raw
signal-return matrix directly (unlike gkx_run, which fed forecast targets and had to shift them).
"""
import argparse
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from core.backtest.engine import backtest
from core.data.registry import register
from core.eval.scorecard import scorecard, to_markdown
from tracks.gkx.cz_data import download_cz_portfolios, load_cz_long_short
from tracks.gkx.models import expanding_window_predict
from tracks.gkx.pc_timing import (
    equal_weight_pc_benchmark,
    rolling_pc_returns,
    signal_weights_from_pc_scores,
    to_wide,
)

MODELS = ["ols", "ridge", "gbrt"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--start", default="1980-01-01")
    ap.add_argument("--k", type=int, nargs="+", default=[5, 10], help="PC counts to try")
    ap.add_argument("--min-train", type=int, default=60, help="PCA warmup months (trailing fit)")
    ap.add_argument("--cost-bps", type=float, default=5.0)
    args = ap.parse_args()

    out = Path("artifacts/gkx")
    out.mkdir(parents=True, exist_ok=True)
    panel_path = Path("data/raw/cz_portfolios.parquet")
    if not panel_path.exists():
        download_cz_portfolios(panel_path)
    panel = load_cz_long_short(panel_path, start=args.start)
    wide = to_wide(panel)
    register(Path("data/manifest.jsonl"), name="cz_portfolios_ls_pc_timing", source="openassetpricing",
             filters={"port": "LS", "start": args.start, "k": args.k}, path=str(panel_path), rows=len(panel))

    results, best_aux = {}, {}
    for k in args.k:
        pc_panel, loadings, cols = rolling_pc_returns(wide, k=k, min_train=args.min_train)
        for model in MODELS:                          # PCA computed once per k, reused across models
            preds = expanding_window_predict(pc_panel, model=model)
            w = signal_weights_from_pc_scores(preds, loadings, cols)
            net = backtest(w, wide, cost_bps=args.cost_bps)["net"].dropna()
            results[f"{model}_k{k}"] = net
            best_aux[f"{model}_k{k}"] = (loadings, cols, net.index)

    best = max(results, key=lambda key: results[key].mean())     # n_trials = every (model, k) tried
    n_trials = len(results)
    loadings, cols, dates = best_aux[best]
    ew_pc = backtest(equal_weight_pc_benchmark(loadings, cols, dates), wide, cost_bps=args.cost_bps)["net"]
    benchmarks = {
        "equal_weight_all_signals": wide.mean(axis=1),   # apples-to-apples on the traded subset
        "equal_weight_pcs": ew_pc,                       # did timing beat holding the factors?
    }
    card = scorecard(results[best], benchmarks, n_trials=n_trials, periods_per_year=12)
    (out / "pc_timing_scorecard.md").write_text(
        to_markdown(card, f"GKX PC factor-timing (best: {best}, of {n_trials} trials)"))
    pd.DataFrame(results).to_parquet(out / "pc_timing_predictions.parquet")
    print(f"best: {best} (net Sharpe over {n_trials} trials); benchmarks "
          f"all={benchmarks['equal_weight_all_signals'].pipe(lambda s: s).mean():.4f}/mo, "
          f"see {out / 'pc_timing_scorecard.md'}")


if __name__ == "__main__":
    main()
