import pandas as pd

import core.data.earnings as earnings_mod
from core.data.earnings import earnings_blackout, fetch_earnings_calendar


def _fake_fetch_day(payload_by_date):
    return lambda date: payload_by_date.get(date, [])


def test_fetch_normalizes_tickers_and_dates(monkeypatch):
    monkeypatch.setattr(earnings_mod, "_fetch_day", _fake_fetch_day({
        "2026-07-09": [{"symbol": "PEP", "name": "PepsiCo"},
                       {"symbol": "BRK.B", "name": "Berkshire"}],
        "2026-07-10": [{"symbol": "WDFC", "name": "WD-40"}],
    }))
    monkeypatch.setattr(earnings_mod.time, "sleep", lambda s: None)
    df = fetch_earnings_calendar("2026-07-09", "2026-07-11")
    assert set(df["ticker"]) == {"PEP", "BRK-B", "WDFC"}
    assert df.loc[df["ticker"] == "BRK-B", "report_date"].iloc[0] == pd.Timestamp("2026-07-09")


def test_fetch_empty_range_returns_empty_frame(monkeypatch):
    monkeypatch.setattr(earnings_mod, "_fetch_day", _fake_fetch_day({}))
    monkeypatch.setattr(earnings_mod.time, "sleep", lambda s: None)
    df = fetch_earnings_calendar("2026-07-11", "2026-07-12")  # weekend
    assert df.empty and list(df.columns) == ["ticker", "report_date"]


def test_blackout_window():
    cal = pd.DataFrame({
        "ticker": ["SOON", "LATER"],
        "report_date": [pd.Timestamp("2026-07-10"), pd.Timestamp("2026-07-19")],
    })
    # reporting tomorrow -> in the blackout; reporting in 10 days -> out
    assert earnings_blackout(cal, "2026-07-09", window=2) == {"SOON"}
    # window straddles a weekend: Friday check catches a Monday report
    assert earnings_blackout(cal, "2026-07-17", window=2) == {"LATER"}
