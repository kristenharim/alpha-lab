"""Extend the hunt2026 panel back to 2005 for ETFs + ^VIX only (stocks stay 2014+).

Free-data honesty: pre-2014 stock history for a point-in-time universe would be
survivorship fiction (yfinance has no delisted names), so stock columns are NaN and
member=0 before 2014. ETFs have full real history from inception. Output:
panel_2005.parquet — the walk-forward panel (adds GFC, 2011, 2015-16, 2018Q4 regimes
for every ETF-based spec).
"""
import json
from pathlib import Path

import pandas as pd

import sys
sys.path.insert(0, str(Path(__file__).parents[2]))
from core.data.prices import validate_prices  # noqa: E402

HERE = Path(__file__).parent
META = json.loads((HERE / "sandbox_meta.json").read_text())
TICKERS = META["etfs"] + META["signal_only"]


def fetch(tickers, start="2005-01-01", end="2026-07-11"):
    import yfinance as yf
    raw = yf.download(tickers, start=start, end=end, interval="1d",
                      auto_adjust=True, progress=False, threads=True)
    return {f: raw[k] for f, k in [("open", "Open"), ("close", "Close"), ("volume", "Volume")]}


def main():
    etf = fetch(TICKERS)
    etf_close = validate_prices(etf["close"].dropna(how="all"))
    cal = etf_close.index

    panel = pd.concat([pd.read_parquet(HERE / "train.parquet"),
                       pd.read_parquet(HERE / "holdout.parquet")])
    full_cal = cal.union(panel.index)

    out = {}
    for field in ["open", "close", "volume"]:
        base = panel[field].reindex(full_cal)
        ext = etf[field].reindex(full_cal)
        for t in TICKERS:
            if t in base.columns and t in ext.columns:
                base[t] = base[t].combine_first(ext[t])
        out[field] = base
    member = panel["member"].reindex(full_cal)
    for t in TICKERS:
        if t in member.columns:
            member[t] = 1.0  # ETFs/^VIX tradable-flagged across full history
    member = member.fillna(0.0)  # stocks: not in universe before their data starts
    out["member"] = member

    ext_panel = pd.concat(out, axis=1)
    ext_panel.columns.names = ["field", "ticker"]
    ext_panel.to_parquet(HERE / "panel_2005.parquet")
    print(f"panel_2005: {len(ext_panel)} rows {ext_panel.index[0].date()} -> "
          f"{ext_panel.index[-1].date()}")
    with open(HERE.parents[1] / "data/manifest.jsonl", "a") as f:
        f.write(json.dumps({"name": "hunt2026_panel_2005", "source": "yfinance",
                            "filters": {"etfs_from": "2005-01-01", "stocks_from": "2014-01-01"},
                            "path": "research/hunt2026/panel_2005.parquet",
                            "rows": len(ext_panel),
                            "pulled_at": pd.Timestamp.utcnow().isoformat()}) + "\n")


if __name__ == "__main__":
    main()
