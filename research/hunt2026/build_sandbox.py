"""Build the hunt2026 data sandbox: train.parquet (<= T-12m) and holdout.parquet
(the last 12 months, evaluator-only). Builders never load the holdout.

Freeze cut: 2025-07-10 (exactly one year before the hunt date, 2026-07-10).
Universe: point-in-time S&P 500 members at any time since 2014 (fja05680 change-log)
+ macro/sector ETFs + ^VIX (signal-only, untradable).
Fields (MultiIndex columns level 0): open, close, volume, member.
All prices yfinance auto-adjusted.
"""
import datetime
import json
from pathlib import Path

import pandas as pd

from core.data.prices import fetch_prices_yf, validate_prices
from core.data.universe import (fetch_sp500_pit_changes, fetch_sp_composite,
                                membership_mask)

HERE = Path(__file__).parent
CUT = "2025-07-10"
START = "2014-01-01"
END = "2026-07-11"  # exclusive upper bound for yf

ETFS = ["SPY", "QQQ", "IWM", "DIA", "MDY",
        "EFA", "EEM", "VGK", "EWJ",
        "TLT", "IEF", "SHY", "BIL", "LQD", "HYG", "TIP",
        "GLD", "SLV", "DBC", "USO", "UNG",
        "VNQ", "UUP", "FXE",
        "XLB", "XLE", "XLF", "XLI", "XLK", "XLP", "XLU", "XLV", "XLY",
        "XLRE", "XLC", "RSP", "SVXY"]
SIGNAL_ONLY = ["^VIX"]  # in the panel for signals; harness rejects weights on these


def fetch_ohlcv(tickers, start, end, chunk_size=150):
    import yfinance as yf
    out = {"open": [], "close": [], "volume": []}
    for i in range(0, len(tickers), chunk_size):
        batch = tickers[i:i + chunk_size]
        raw = yf.download(batch, start=start, end=end, interval="1d",
                          auto_adjust=True, progress=False, threads=True)
        if raw.empty:
            continue
        if not isinstance(raw.columns, pd.MultiIndex):
            raw.columns = pd.MultiIndex.from_product([raw.columns, [batch[0]]])
        for field, key in [("open", "Open"), ("close", "Close"), ("volume", "Volume")]:
            out[field].append(raw[key])
    return {f: pd.concat(frames, axis=1).dropna(how="all").pipe(
                lambda d: d.loc[:, ~d.columns.duplicated()])
            for f, frames in out.items()}


def main():
    changes = fetch_sp500_pit_changes(cache=HERE.parent.parent / "data/raw/sp500_pit.parquet")
    recent = changes[changes["date"] >= "2014-01-01"]
    stocks = set()
    for m in recent["members"]:
        stocks |= set(m)
    comp = fetch_sp_composite(which=("500",),
                              cache=HERE.parent.parent / "data/raw/sp_composite.parquet")
    stocks |= set(comp["ticker"])
    stocks = sorted(stocks - set(ETFS) - set(SIGNAL_ONLY))
    print(f"universe: {len(stocks)} stocks + {len(ETFS)} ETFs")

    panels = fetch_ohlcv(stocks + ETFS + SIGNAL_ONLY, START, END)
    close = validate_prices(panels["close"])
    cal = close.index

    member = membership_mask(changes, cal, [t for t in close.columns if t in stocks])
    # ETFs and signal tickers are always "members" of the tradable panel
    for t in close.columns:
        if t not in member.columns:
            member[t] = t in ETFS or t in SIGNAL_ONLY
    member = member[close.columns].astype(float)  # float for parquet uniformity

    panel = pd.concat({"open": panels["open"].reindex(cal)[close.columns],
                       "close": close,
                       "volume": panels["volume"].reindex(cal)[close.columns],
                       "member": member}, axis=1)
    panel.columns.names = ["field", "ticker"]

    cut = pd.Timestamp(CUT)
    train, holdout = panel[panel.index <= cut], panel[panel.index > cut]
    train.to_parquet(HERE / "train.parquet")
    holdout.to_parquet(HERE / "holdout.parquet")

    # static metadata both sides may see (current sector map — survivorship-lite, noted)
    comp_all = fetch_sp_composite(cache=HERE.parent.parent / "data/raw/sp_composite_all.parquet")
    comp_all[comp_all["ticker"].isin(close.columns)][["ticker", "sector"]] \
        .to_parquet(HERE / "sectors.parquet")

    meta = {"cut": CUT, "start": START, "end": END,
            "n_stocks": len([t for t in close.columns if t in stocks]),
            "etfs": ETFS, "signal_only": SIGNAL_ONLY,
            "train_rows": len(train), "holdout_rows": len(holdout),
            "built_at": datetime.datetime.now(datetime.timezone.utc).isoformat()}
    (HERE / "sandbox_meta.json").write_text(json.dumps(meta, indent=2))
    with open(HERE.parent.parent / "data/manifest.jsonl", "a") as f:
        f.write(json.dumps({"name": "hunt2026_sandbox", "source": "yfinance+fja05680",
                            "filters": {"cut": CUT, "start": START},
                            "path": "research/hunt2026/train.parquet",
                            "rows": len(train), "pulled_at": meta["built_at"]}) + "\n")
    print(json.dumps(meta, indent=2))


if __name__ == "__main__":
    main()
