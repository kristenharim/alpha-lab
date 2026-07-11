"""Earnings calendar + blackout helper. Network fetch lives here, called only from scripts/.

Source is Nasdaq's public calendar endpoint (free, no key). EODHD's calendar API needs a
higher plan tier than the price subscription (403), so it's not used.
If Nasdaq changes the payload, swap _fetch_day for a keyed provider (e.g. Finnhub)
without touching callers.
"""
import json
import time
import urllib.request

import pandas as pd

from core.data.universe import clean_ticker

NASDAQ_URL = "https://api.nasdaq.com/api/calendar/earnings?date={date}"
HEADERS = {"User-Agent": "Mozilla/5.0", "Accept": "application/json"}


def _fetch_day(date: str) -> list[dict]:
    """Raw earnings rows for one YYYY-MM-DD date (empty on weekends/holidays)."""
    req = urllib.request.Request(NASDAQ_URL.format(date=date), headers=HEADERS)
    data = json.load(urllib.request.urlopen(req, timeout=30))
    return (data.get("data") or {}).get("rows") or []


def fetch_earnings_calendar(start: str, end: str,
                            cache: "pd.io.common.FilePath | None" = None) -> pd.DataFrame:
    """Earnings report dates in [start, end] as (ticker, report_date). Network.

    One request per calendar day; tickers normalized to the universe convention
    (BRK.B -> BRK-B). Parquet cache hit skips the network entirely.
    """
    from pathlib import Path
    if cache and Path(cache).exists():
        return pd.read_parquet(cache)
    frames = []
    for d in pd.date_range(start, end, freq="D"):
        rows = _fetch_day(d.strftime("%Y-%m-%d"))
        if rows:
            frames.append(pd.DataFrame({
                "ticker": [clean_ticker(r["symbol"]) for r in rows],
                "report_date": d.normalize(),
            }))
        time.sleep(0.5)  # be polite to the unauthenticated endpoint
    df = (pd.concat(frames, ignore_index=True).drop_duplicates()
          if frames else pd.DataFrame(columns=["ticker", "report_date"]))
    if cache:
        Path(cache).parent.mkdir(parents=True, exist_ok=True)
        df.to_parquet(cache)
    return df


def earnings_blackout(earnings: pd.DataFrame, on_date, window: int = 2) -> set[str]:
    """Tickers whose report_date falls within +/- `window` CALENDAR days of `on_date`.

    Calendar days (not business days) on purpose: a Monday report should already be
    in Friday's blackout, and the simplicity is worth the extra weekend day of caution.
    """
    on_date = pd.Timestamp(on_date).normalize()
    lo, hi = on_date - pd.Timedelta(days=window), on_date + pd.Timedelta(days=window)
    hit = earnings[(earnings["report_date"] >= lo) & (earnings["report_date"] <= hi)]
    return set(hit["ticker"])
