"""Offline test for the hunt2026 paper runner: registry loads, weights produced on a fixture
panel, ledger row schema. No network, no broker."""
import json

import numpy as np
import pandas as pd

from scripts.hunt_paper_run import BOOKS, compute_book


def _fixture_panel():
    """Synthetic ETF-only panel covering every ticker the four books touch. Deterministic RW
    so specs run end-to-end without the frozen parquet (tests never touch the network/big files)."""
    etfs = ["SPY", "QQQ", "IWM", "EFA", "EEM", "TLT", "IEF", "GLD", "SLV",
            "DBC", "USO", "UUP", "HYG", "LQD", "VNQ", "BIL", "SVXY", "^VIX"]
    stocks = [f"STK{i}" for i in range(30)]  # momentum_concentrated needs member stocks
    tickers = etfs + stocks
    dates = pd.bdate_range("2019-01-01", periods=600)
    rng = np.random.default_rng(0)
    steps = rng.normal(0.0003, 0.01, size=(len(dates), len(tickers)))
    close = pd.DataFrame(100 * np.exp(np.cumsum(steps, axis=0)), index=dates, columns=tickers)
    close["BIL"] = 100.0  # cash-like
    close["^VIX"] = 15 + 5 * rng.random(len(dates))
    fields = {f: close.copy() for f in ("open", "close", "volume", "member")}
    member = pd.DataFrame(0.0, index=dates, columns=tickers)
    member[etfs] = 1.0
    member[stocks] = 1.0
    fields["member"] = member
    panel = pd.concat(fields, axis=1)
    panel.columns.names = ["field", "ticker"]
    return panel


def test_registry_loads():
    assert set(BOOKS) == {"trend_vol_qqq", "defensive_ensemble", "dual_momentum_gold",
                          "momentum_concentrated"}
    assert set(BOOKS.values()) <= {"qqq", "6040", "spy"}


def test_weights_produced_on_fixture():
    panel = _fixture_panel()
    for name in BOOKS:
        row = compute_book(panel, name, notional=25_000.0)
        assert row["targets"], f"{name} produced an empty book"
        for t, w in row["targets"].items():
            assert np.isfinite(w) and t != "^VIX"          # signal-only is never a target
            assert abs(row["target_dollars"][t] - round(w * 25_000.0, 2)) < 1e-6
        assert row["gross"] <= 2.0 + 1e-9                  # harness gross cap


def test_ledger_row_schema(tmp_path, monkeypatch):
    panel = _fixture_panel()
    row = compute_book(panel, "trend_vol_qqq", notional=25_000.0)
    row["mode"], row["fills"] = "dry", []
    assert set(row) >= {"date", "book", "targets", "target_dollars", "gross", "notional",
                        "nav", "bench_spy_nav", "bench_naive_nav", "mode", "fills"}

    monkeypatch.setattr("scripts.hunt_paper_run.LEDGER_DIR", tmp_path)
    from scripts import hunt_paper_run
    path = hunt_paper_run._write_ledger(row)
    back = json.loads(path.read_text().splitlines()[-1])
    assert back["book"] == "trend_vol_qqq" and back["mode"] == "dry"


def test_account_aggregation_sums_across_books():
    # books are virtual: the account submits the SUM of per-book dollar targets
    rows = [{"target_dollars": {"QQQ": 100.0, "SPY": 50.0}},
            {"target_dollars": {"QQQ": 25.0, "BIL": 10.0}}]
    agg = {}
    for row in rows:
        for t, d in row["target_dollars"].items():
            agg[t] = agg.get(t, 0.0) + d
    assert agg == {"QQQ": 125.0, "SPY": 50.0, "BIL": 10.0}
