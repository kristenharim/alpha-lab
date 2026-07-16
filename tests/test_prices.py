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
