"""SHAP feature attribution for the signal-quality meta-model — the standard 'which features drove
the prediction' beeswarm every ML-signal paper ships. TreeExplainer on the full-data XGBoost model.
Saves a beeswarm PNG under reports/ (committed).
"""
import argparse
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import shap

from tracks.statarb.ml.dataset import build_features, load_log
from tracks.statarb.ml.train import fit_full

ROOT = Path(__file__).resolve().parents[3]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default="all_on")
    args = ap.parse_args()

    X, y, _ = build_features(load_log(args.config))
    model = fit_full(X, y, "xgboost")
    explainer = shap.TreeExplainer(model)
    sv = explainer(X)

    out = ROOT / "reports"
    out.mkdir(exist_ok=True)
    png = out / f"shap_beeswarm_{args.config}.png"
    plt.figure()
    shap.summary_plot(sv, X, show=False, plot_size=(9, 6))
    plt.tight_layout()
    plt.savefig(png, dpi=130, bbox_inches="tight")
    plt.close()
    print(f"wrote {png}")


if __name__ == "__main__":
    main()
