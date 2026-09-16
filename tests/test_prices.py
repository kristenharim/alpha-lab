import sys
import types

import numpy as np
import pandas as pd
import pytest
from core.data.prices import validate_prices, daily_returns, fetch_prices_yf, fetch_volume_yf


def _prices():
    idx = pd.date_range("2024-01-01", periods=5, freq="B")
    return pd.DataFrame({"AAA": [100, 101, 102, 101, 103], "BBB": [50, 50, 51, 52, 52]}, index=idx)


def test_validate_ok():
    assert validate_prices(_prices()) is not None


def test_validate_rejects_empty():
    with pytest.raises(ValueError):
        validate_prices(pd.DataFrame())


def test_validate_rejects_duplicate_dates():
    df = _prices()
    df = pd.concat([df, df.iloc[[0]]])
    with pytest.raises(ValueError):
        validate_prices(df)


def test_daily_returns():
    r = daily_returns(_prices())
    assert np.isclose(r.iloc[0]["AAA"], 0.01)
    assert len(r) == 4


def _fake_yf(calls):
    """Stand-in yfinance: records download kwargs, returns a MultiIndex frame. No network."""
    def download(batch, **kw):
        calls.append(kw)
        idx = pd.date_range("2024-01-01", periods=2, freq="B")
        cols = pd.MultiIndex.from_product([["Close", "Volume"], list(batch)])
        return pd.DataFrame(1.0, index=idx, columns=cols)
    return types.SimpleNamespace(download=download)


def test_yf_fetch_bounds_worker_threads(monkeypatch):
    """yfinance's threads=True default spawns a worker PER TICKER; ~200 per chunk exhausts
    launchd's 256-FD soft limit and the nightly runner dies as DNS/sqlite/cert errors while
    every interactive run passes. Both fetchers must bound concurrency, on every chunk."""
    for fetch in (fetch_prices_yf, fetch_volume_yf):
        calls = []
        monkeypatch.setitem(sys.modules, "yfinance", _fake_yf(calls))
        fetch([f"T{i}" for i in range(450)], start="2024-01-01", end=None)
        assert len(calls) == 3, f"{fetch.__name__}: expected 3 chunks of 200"
        for kw in calls:
            t = kw.get("threads")
            assert t is not True and isinstance(t, int) and 1 <= t <= 16, \
                f"{fetch.__name__}: unbounded/absent threads={t!r} — will exhaust FDs under launchd"


def test_yf_fetch_retries_names_that_came_back_empty(monkeypatch):
    """Under launchd ~70 names a night failed on the sqlite tz-cache and kept stale closes.
    Names that come back all-NaN get one serial retry, and the retry's data is used."""
    calls = []

    def download(batch, **kw):
        calls.append((list(batch), kw.get("threads")))
        idx = pd.date_range("2024-01-01", periods=2, freq="B")
        cols = pd.MultiIndex.from_product([["Close", "Volume"], list(batch)])
        df = pd.DataFrame(1.0, index=idx, columns=cols)
        if len(calls) == 1:
            df.loc[:, (slice(None), "B")] = float("nan")   # first pass loses B, every field
        return df
    monkeypatch.setitem(sys.modules, "yfinance", types.SimpleNamespace(download=download))
    px = fetch_prices_yf(["A", "B", "C"], start="2024-01-01", end=None)
    assert calls[1] == (["B"], False)                   # one serial retry, only the lost name
    assert px["B"].notna().all() and list(px.columns).count("B") == 1


def test_yf_fetch_retries_a_wholly_failed_batch(monkeypatch):
    """An empty first response (every name failed) must still get the serial retry."""
    calls = []

    def download(batch, **kw):
        calls.append(kw.get("threads"))
        if len(calls) == 1:
            return pd.DataFrame()
        idx = pd.date_range("2024-01-01", periods=2, freq="B")
        return pd.DataFrame(1.0, index=idx,
                            columns=pd.MultiIndex.from_product([["Close", "Volume"], list(batch)]))
    monkeypatch.setitem(sys.modules, "yfinance", types.SimpleNamespace(download=download))
    v = fetch_volume_yf(["A"], start="2024-01-01", end=None)
    assert calls[1] is False and v["A"].notna().all()
