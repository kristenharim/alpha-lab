"""Offline tests for the CRSP panel transforms. No WRDS, no network."""
import math

import pandas as pd

from core.data.crsp import (SHUMWAY_DLRET, add_market_equity, apply_delisting, decile_long_short,
                            momentum_signal)


def test_delisting_return_compounds_fills_and_defaults():
    msf = pd.DataFrame({"permno": [1, 2, 3, 4], "date": pd.to_datetime(["2020-01-31"] * 4),
                        "ret": [0.10, None, None, 0.05]})
    delist = pd.DataFrame({"permno": [1, 2, 3], "dlstdt": pd.to_datetime(["2020-01-15"] * 3),
                           "dlret": [-0.50, -0.20, None], "dlstcd": [100, 100, 552]})
    out = apply_delisting(msf, delist).groupby("permno")["ret_adj"].last()
    assert math.isclose(out[1], 1.10 * 0.50 - 1)          # both: compounded
    assert math.isclose(out[2], -0.20)                     # no regular return: dlret alone
    assert math.isclose(out[3], SHUMWAY_DLRET)             # performance delist, no dlret: -30%
    assert math.isclose(out[4], 0.05)                      # never delisted: untouched


def test_momentum_skips_last_month_and_weights_use_last_month_me():
    dates = pd.date_range("2019-01-31", periods=14, freq="ME")
    p = pd.DataFrame({"permno": 1, "date": dates, "ret_adj": [0.01] * 12 + [0.50, 0.0],
                      "prc": -10.0, "shrout": 1000.0})
    p = momentum_signal(add_market_equity(p)).set_index("date")
    assert math.isclose(p["mom"].iloc[12], 1.01 ** 11 - 1)  # month 13: t-12..t-2, ignores t-1
    assert math.isclose(p["mom"].iloc[13], 1.01 ** 11 - 1)   # the +50% month is t-1: skipped
    assert math.isnan(p["me_lag"].iloc[0]) and p["me_lag"].iloc[1] == 10.0   # |prc| x shrout / 1000


def test_decile_long_short_uses_nyse_breakpoints():
    d = pd.Timestamp("2020-01-31")
    rows = [{"permno": i, "date": d, "exchcd": 1, "mom": i, "ret_adj": i / 100, "me_lag": 1.0}
            for i in range(30)]
    rows.append({"permno": 99, "date": d, "exchcd": 3, "mom": 1000, "ret_adj": 0.99, "me_lag": 1.0})
    ls = decile_long_short(pd.DataFrame(rows), "mom")
    top = [0.27, 0.28, 0.29, 0.99]                         # nasdaq name joins the top, not the cutoff
    assert math.isclose(ls[d], sum(top) / 4 - (0.00 + 0.01 + 0.02) / 3)


def test_delisting_the_month_after_the_last_record_gets_its_own_row():
    """87% of CRSP delistings are dated the month after the last monthly record. Merging on month
    alone dropped them all, booking each dead firm's final loss at 0%."""
    msf = pd.DataFrame({"permno": [7, 7], "date": pd.to_datetime(["2020-01-31", "2020-02-29"]),
                        "ret": [0.02, 0.01], "prc": [-5.0, -4.0], "shrout": [100.0, 100.0], "exchcd": 3})
    delist = pd.DataFrame({"permno": [7], "dlstdt": pd.to_datetime(["2020-03-10"]),
                           "dlret": [None], "dlstcd": [560]})
    out = add_market_equity(apply_delisting(msf, delist))
    assert len(out) == 3
    last = out.iloc[-1]
    assert last["date"] == pd.Timestamp("2020-03-31") and last["exchcd"] == 3
    assert math.isclose(last["ret_adj"], SHUMWAY_DLRET)
    assert math.isclose(last["me_lag"], 0.4)               # weighted by February's market equity
    gap = apply_delisting(msf, delist.assign(dlstdt=pd.to_datetime(["2020-06-10"])))
    assert len(gap) == 2                                   # months later: not held, no row
