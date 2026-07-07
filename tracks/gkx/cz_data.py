"""Chen-Zimmermann Open Source Asset Pricing data access (Decision B).

Firm-level CRSP joins are BLOCKED on WRDS; signal-level long-short portfolio returns
are public and are what this track uses for the GKX-lite signal-rotation study.
"""
from pathlib import Path

import pandas as pd

REQUIRED = {"date", "ret"}


def validate_panel(df: pd.DataFrame) -> pd.DataFrame:
    cols = set(df.columns)
    if "signal_id" in cols:
        df = df.rename(columns={"signal_id": "signalname"})
        cols = set(df.columns)
    if not (REQUIRED <= cols and "signalname" in cols):
        raise ValueError(f"panel must have columns {REQUIRED | {'signalname'}}, got {sorted(cols)}")
    df = df.dropna(subset=["ret"]).copy()
    df["date"] = pd.to_datetime(df["date"])
    return df


def load_cz_long_short(path: Path, start: str | None = None) -> pd.DataFrame:
    """Read a CZ portfolio file and reduce to one long-short return per signal per month.

    `dl_port("op")` returns decile portfolios (port = "01".."10") plus the long-short
    (port == "LS") for each signal, with `ret` in PERCENT. We keep only LS and convert
    to decimal so downstream costs and Sharpe annualization are on the right scale.
    """
    df = pd.read_parquet(path)
    if "port" not in df.columns:
        raise ValueError("expected a 'port' column in CZ portfolio file")
    ls = df[df["port"] == "LS"].copy()
    if ls.empty:
        raise ValueError("no long-short (port == 'LS') rows found")
    ls["ret"] = ls["ret"] / 100.0  # percent -> decimal
    ls = ls[["signalname", "date", "ret"]]
    ls["date"] = pd.to_datetime(ls["date"])
    if start:
        ls = ls[ls["date"] >= start]
    return validate_panel(ls)


def download_cz_portfolios(dest: Path) -> Path:
    """Network: pull Chen-Zimmermann long-short portfolio returns. Prefers the
    openassetpricing package; otherwise raises with the manual-download instruction."""
    dest = Path(dest)
    dest.parent.mkdir(parents=True, exist_ok=True)
    try:
        from openassetpricing import OpenAP
    except ImportError as e:
        raise RuntimeError(
            "pip install openassetpricing, or download PredictorLSretWide.csv from "
            "https://www.openassetpricing.com and place it at " + str(dest)
        ) from e
    openap = OpenAP()
    df = openap.dl_port("op", "pandas")  # original-paper long-short portfolios
    df.to_parquet(dest)
    return dest
