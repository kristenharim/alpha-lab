"""Offline tests for the two pre-go-live bricks: the signal-parity gate and the Alpaca adapter.

The adapter is tested with a MOCK trading client (injected) — no network, no keys — matching the repo
rule. The live data path itself is validated only by the first real --live run (smoke test with keys).
"""
import numpy as np
import pandas as pd
import pytest

from core.data.prices import daily_returns


# ---- signal-parity harness ----

def _panel(n=140, k=30, seed=1):
    rng = np.random.default_rng(seed)
    dates = pd.bdate_range("2024-01-01", periods=n)
    px = pd.DataFrame(100 * np.exp(np.cumsum(rng.normal(0, 0.02, (n, k)), axis=0)),
                      index=dates, columns=[f"T{i:02d}" for i in range(k)])
    rets = daily_returns(px)
    mkt = rets.mean(axis=1)
    factors = pd.DataFrame({c: mkt for c in px.columns}).reindex(rets.index)
    return px, factors, rets


def test_parity_frozen_panel_matches_full_panel():
    from tracks.statarb.paper.parity import parity_mismatches
    px, factors, rets = _panel()
    sample = list(rets.index[-6:])
    bad = parity_mismatches(px, factors, sample, window=60)
    assert bad == [], f"signal parity broke on {bad} — live book != backtest book"


# ---- Alpaca adapter (mock client) ----

class _Asset:
    def __init__(self, tradable, status="ACTIVE"):
        self.tradable, self.status = tradable, status


class _Pos:
    def __init__(self, symbol, qty, avg):
        self.symbol, self.qty, self.avg_entry_price = symbol, str(qty), str(avg)
        self.side = "long" if qty > 0 else "short"


class _Order:
    def __init__(self, oid, symbol, side, qty, price):
        self.id, self.symbol, self.side = oid, symbol, side
        self.filled_qty, self.filled_avg_price = str(qty), str(price)


class _TC:
    def __init__(self, positions=None, assets=None, orders=None):
        self._pos = positions or []
        self._assets = assets or {}
        self._orders = orders or []
        self.submitted = []

    def get_all_positions(self):
        return self._pos

    def get_asset(self, sym):
        if sym not in self._assets:
            raise ValueError("asset not found")
        return self._assets[sym]

    def submit_order(self, req):
        self.submitted.append(req)

    def get_orders(self, filter=None):
        return self._orders


def test_asset_status_maps_tradable_halted_delisted():
    from core.broker.alpaca import AlpacaBroker
    tc = _TC(assets={"AAPL": _Asset(True), "HALT": _Asset(False, "ACTIVE")})
    b = AlpacaBroker(tc, price_fn=lambda t: 100.0)
    assert b.asset_status("AAPL") == "tradable"
    assert b.asset_status("HALT") == "halted"        # untradable but active
    assert b.asset_status("GONE") == "delisted"      # not found


def test_submit_targets_places_share_delta_and_skips_untradable():
    from core.broker.alpaca import AlpacaBroker
    tc = _TC(positions=[_Pos("MSFT", 10, 200.0)],
             assets={"AAPL": _Asset(True), "MSFT": _Asset(True), "HALT": _Asset(False, "ACTIVE")})
    b = AlpacaBroker(tc, price_fn=lambda t: {"AAPL": 100.0, "MSFT": 200.0, "HALT": 50.0}[t])
    b.submit_targets({"AAPL": 5000.0, "MSFT": 0.0, "HALT": 5000.0})
    orders = {o.symbol: o for o in tc.submitted}
    assert orders["AAPL"].qty == 50 and str(orders["AAPL"].side).endswith("BUY")   # 5000/100 new long
    assert orders["MSFT"].qty == 10 and str(orders["MSFT"].side).endswith("SELL")  # exit the 10 held
    assert "HALT" not in orders                                                    # untradable -> skipped


def test_fills_drains_and_positions_map():
    from core.broker.alpaca import AlpacaBroker
    tc = _TC(positions=[_Pos("AAPL", 50, 100.0)],
             orders=[_Order("o1", "AAPL", "buy", 50, 100.0)])
    b = AlpacaBroker(tc, price_fn=lambda t: 100.0)
    assert b.positions()["AAPL"]["qty"] == 50.0
    first = b.fills()
    assert len(first) == 1 and first[0]["ticker"] == "AAPL" and first[0]["qty"] == 50.0
    assert b.fills() == []       # drained — same order not reported twice


def test_factory_requires_env_keys(monkeypatch):
    from core.broker.alpaca import alpaca_paper_broker
    monkeypatch.delenv("ALPACA_API_KEY_ID", raising=False)
    monkeypatch.delenv("ALPACA_API_SECRET_KEY", raising=False)
    with pytest.raises(RuntimeError, match="ALPACA_API_KEY_ID"):
        alpaca_paper_broker(price_fn=lambda t: 100.0)
