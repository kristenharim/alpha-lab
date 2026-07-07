"""Load the per-signal log and build a LEAKAGE-SAFE feature matrix.

The model predicts, AT ENTRY, whether a signal will mean-revert. So a feature is legitimate only if
its value is known at entry. `holding_days`, `close_reason`, `exit_date`, and the realized/counterfactual
P&L are known only at EXIT — using them as inputs is within-trade leakage (a suspiciously-high AUC that
collapses forward). The walk-forward split guards *cross-month* leakage; this partition guards
*within-trade* leakage. Both are required. `build_features` selects ONLY entry-time columns and asserts
no exit-only column leaks in.
"""
from pathlib import Path

import pandas as pd

from tracks.statarb.paper.ledger import Ledger

ROOT = Path(__file__).resolve().parents[3]

ENTRY_NUMERIC = ["entry_s", "abs_entry_s", "residual", "volatility", "volume_ratio"]
ENTRY_CATEGORICAL = ["sector"]
EXIT_ONLY = {"holding_days", "close_reason", "exit_date", "realized_pnl", "counterfactual_pnl"}
LABEL = "success"


def load_log(config: str = "all_on") -> pd.DataFrame:
    root = ROOT / "artifacts/statarb/signal_log" / config
    rows = Ledger(root).read("signal_log")
    if not rows:
        raise FileNotFoundError(f"empty/missing signal log for config '{config}' under {root}")
    return pd.DataFrame(rows)


def build_features(df: pd.DataFrame):
    """Return (X, y, entry_dates). X contains ONLY entry-time features (numeric imputed by median,
    sector one-hot). Raises if any exit-only column reaches the feature matrix."""
    df = df.copy()
    df["abs_entry_s"] = df["entry_s"].abs()

    num = df[ENTRY_NUMERIC].apply(pd.to_numeric, errors="coerce")
    num = num.fillna(num.median(numeric_only=True))          # handles null volume_ratio
    cat = pd.get_dummies(df["sector"].astype(str), prefix="sector")
    X = pd.concat([num, cat], axis=1)

    leaked = set(X.columns) & EXIT_ONLY
    assert not leaked, f"leakage: exit-only columns in feature matrix: {leaked}"

    y = df[LABEL].astype(int)
    entry_dates = pd.to_datetime(df["entry_date"])
    return X, y, entry_dates
