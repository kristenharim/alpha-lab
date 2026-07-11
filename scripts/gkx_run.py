"""GKX-lite: download Chen-Zimmermann signal portfolios, run the model ladder, score a
signal-rotation strategy. Full firm-level GKX replication is blocked on WRDS.

Usage: .venv/bin/python scripts/gkx_run.py
(first: pip install openassetpricing, or drop the CZ file at data/raw/cz_portfolios.parquet)

Alignment note (verified with a toy check, see STATE): expanding_window_predict returns
y_true[t] = the forward (t->t+1) return that score[t] forecasts, so scores and y_true are
contemporaneously aligned at date t. core.backtest lags weights by one period internally
(held = weights.shift(1)), so we feed it `actual.shift(1)` — pairing weight(t) with
y_true(t), realization dated t+1. Feeding `actual` unshifted would credit each month's
return to the prior month's position (misaligned).
"""
import argparse
from pathlib import Path

import pandas as pd

from core.backtest.engine import backtest
from core.backtest.portfolio import quantile_weights
from core.data.registry import register
from core.eval.scorecard import scorecard, to_markdown
from tracks.gkx.cz_data import download_cz_portfolios, load_cz_long_short
from tracks.gkx.models import expanding_window_predict


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--start", default="1980-01-01", help="first month of the study window")
    ap.add_argument("--cost-bps", type=float, default=5.0)
    args = ap.parse_args()

    out = Path("artifacts/gkx")
    out.mkdir(parents=True, exist_ok=True)
    panel_path = Path("data/raw/cz_portfolios.parquet")
    if not panel_path.exists():
        download_cz_portfolios(panel_path)

    panel = load_cz_long_short(panel_path, start=args.start)
    register(Path("data/manifest.jsonl"), name="cz_portfolios_ls", source="openassetpricing",
             filters={"port": "LS", "start": args.start}, path=str(panel_path), rows=len(panel))

    results = {}
    for model in ["ols", "ridge", "gbrt"]:
        preds = expanding_window_predict(panel, model=model)
        scores = preds.pivot_table(index="date", columns="signal", values="y_pred")
        actual = preds.pivot_table(index="date", columns="signal", values="y_true")
        # see alignment note in module docstring
        res = backtest(quantile_weights(scores), actual.shift(1), cost_bps=args.cost_bps).dropna()
        results[model] = res["net"]

    best = max(results, key=lambda k: results[k].mean())
    bench = {"equal_weight_all_signals": panel.groupby("date")["ret"].mean()}
    card = scorecard(results[best], bench, n_trials=3, periods_per_year=12)
    (out / "scorecard.md").write_text(to_markdown(card, f"GKX-lite signal rotation ({best})"))
    pd.DataFrame(results).to_parquet(out / "predictions.parquet")
    print(f"best model: {best}; see {out / 'scorecard.md'}")


if __name__ == "__main__":
    main()
