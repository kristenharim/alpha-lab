"""Walk-forward training of the signal-quality meta-model.

Expanding window by calendar month: train on every trade in months < m, predict month m. Out-of-fold
(OOF) predictions are therefore never in-sample. Three models — logistic regression + random forest
(baselines) and XGBoost (primary). Reports OOF AUC per model; XGBoost's OOF probabilities feed
evaluate.py and the fitted full-data XGBoost feeds explain.py.
"""
import argparse
import warnings

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from xgboost import XGBClassifier

from tracks.statarb.ml.dataset import build_features, load_log


def model_factory(name: str):
    if name == "logistic":
        return make_pipeline(StandardScaler(), LogisticRegression(max_iter=1000))
    if name == "random_forest":
        return RandomForestClassifier(n_estimators=200, max_depth=4, random_state=0, n_jobs=-1)
    if name == "xgboost":
        return XGBClassifier(n_estimators=120, max_depth=3, learning_rate=0.05,
                             subsample=0.8, colsample_bytree=0.8, tree_method="hist",
                             eval_metric="logloss", random_state=0)
    raise ValueError(name)


def walk_forward_oof(X, y, dates, name: str) -> pd.Series:
    """Expanding-window monthly OOF probabilities. A month is scored only if the training set has
    both classes and enough rows."""
    months = dates.dt.to_period("M")
    uniq = sorted(months.unique())
    oof = pd.Series(np.nan, index=X.index)
    for m in uniq[1:]:
        tr = months < m
        te = months == m
        if tr.sum() < 20 or y[tr].nunique() < 2:
            continue
        model = model_factory(name)
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            model.fit(X[tr], y[tr])
            oof[te] = model.predict_proba(X[te])[:, 1]
    return oof


def fit_full(X, y, name: str = "xgboost"):
    model = model_factory(name)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        model.fit(X, y)
    return model


def oof_auc_table(X, y, dates) -> pd.DataFrame:
    rows = []
    for name in ("logistic", "random_forest", "xgboost"):
        oof = walk_forward_oof(X, y, dates, name)
        mask = oof.notna()
        auc = roc_auc_score(y[mask], oof[mask]) if y[mask].nunique() == 2 else float("nan")
        rows.append({"model": name, "oof_auc": round(auc, 4), "scored": int(mask.sum())})
    return pd.DataFrame(rows)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default="all_on")
    args = ap.parse_args()
    X, y, dates = build_features(load_log(args.config))
    print(f"loaded {len(X)} signals, {y.mean():.1%} success, {X.shape[1]} entry-time features")
    print(oof_auc_table(X, y, dates).to_string(index=False))


if __name__ == "__main__":
    main()
