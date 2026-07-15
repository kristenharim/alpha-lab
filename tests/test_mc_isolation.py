"""Offline tests for the momentum_concentrated account-isolation cutover (2026-07-15).

No network, no broker, no creds. Covers: the pure routing split + its no-cross-leak invariant, the
unchanged sizing divisor, the dedicated MC reconcile's alarm logic, exclusion of MC from the shared
reconcile, and the broker factory's second-account cred wiring.
"""
import pytest

from scripts.hunt_paper_run import (BOOKS, MC_BOOK, N_BOOKS_TOTAL, SHARED_BOOKS, route_targets,
                                    submit_leg)
from scripts.hunt_paper_reconcile import reconcile_date, reconcile_mc_date


class _FakeBroker:
    """Minimal broker double for submit_leg — records calls, optionally raises on submit."""
    def __init__(self, raise_on_submit=False, fills=None):
        self.raise_on_submit = raise_on_submit
        self._fills = fills or []
        self.cancelled = False
        self.submitted = None

    def cancel_all_orders(self):
        self.cancelled = True

    def submit_targets(self, targets, *, tag=None):
        if self.raise_on_submit:
            raise ConnectionError("simulated network blip")
        self.submitted = (dict(targets), tag)

    def fills(self):
        return list(self._fills)

    def order_errors(self):
        return []


def _row(dollars):
    return {"target_dollars": dict(dollars)}


# ---------- sizing invariant: divisor stays 7, MC split out ----------

def test_sizing_divisor_unchanged():
    assert N_BOOKS_TOTAL == 7 == len(BOOKS)          # notional = equity/7, never len(SHARED_BOOKS)
    assert MC_BOOK in BOOKS and MC_BOOK not in SHARED_BOOKS
    assert len(SHARED_BOOKS) == 6 and set(SHARED_BOOKS) == set(BOOKS) - {MC_BOOK}


# ---------- routing split + no cross-account leak ----------

def test_route_splits_mc_from_etf_books():
    rows = {"vol_managed_qqq": _row({"QQQ": 10_000}),
            "trend_vol_qqq": _row({"QQQ": 5_000}),
            MC_BOOK: _row({"AAPL": 3_000, "MSFT": 2_000})}
    shared, mc = route_targets(rows)
    assert shared == {"QQQ": 15_000}                 # ETF books aggregate together
    assert mc == {"AAPL": 3_000, "MSFT": 2_000}      # MC alone in its account
    assert not (set(shared) & set(mc))               # disjoint


def test_route_fails_closed_on_shared_symbol():
    # an ETF book and MC both wanting the same symbol must abort, never silently co-route
    rows = {"defensive_ensemble": _row({"SPY": 8_000}),
            MC_BOOK: _row({"SPY": 1_000})}
    with pytest.raises(RuntimeError, match="route to BOTH"):
        route_targets(rows)


def test_route_empty_mc_is_fine():
    rows = {"vol_core_svxy": _row({"SVXY": 4_000}), MC_BOOK: _row({})}
    shared, mc = route_targets(rows)
    assert shared == {"SVXY": 4_000} and mc == {}


# ---------- shared reconcile excludes MC ----------

def test_shared_reconcile_drops_mc_and_account_mc():
    day = {"_account": {"target_dollars": {"QQQ": 10_000}, "notional": 70_000, "fills": []},
           "vol_managed_qqq": {"target_dollars": {"QQQ": 10_000}, "notional": 10_000, "nav": 1.0},
           MC_BOOK: {"target_dollars": {"AAPL": 5_000}, "notional": 10_000, "nav": 1.0},
           "_account_mc": {"target_dollars": {"AAPL": 5_000}, "notional": 70_000, "fills": []}}
    shared_books = {k: v for k, v in day.items() if k not in (MC_BOOK, "_account_mc")}
    row = reconcile_date("2026-07-16", shared_books, [], {"QQQ": 100.0}, {"QQQ": 100.0}, {})
    assert MC_BOOK not in row["books"]                # MC not judged against the shared account
    assert "vol_managed_qqq" in row["books"]


# ---------- dedicated MC reconcile alarm logic ----------

def _mc_row(dollars, notional=10_000):
    return {"target_dollars": dict(dollars), "notional": notional}

CLOSES = {"AAPL": 100.0, "MSFT": 50.0}


def test_mc_clean_match_no_alarms():
    mc = _mc_row({"AAPL": 5_000})                    # target 50 sh @ 100
    row = reconcile_mc_date("2026-07-16", mc, {"AAPL": 50.0}, [], CLOSES, None)
    assert row["book"] == MC_BOOK
    assert row["gap_dollars"] == 0.0
    assert row["alarms"] == []


def test_mc_position_gap_alarms():
    mc = _mc_row({"AAPL": 5_000})                    # want 50 sh, hold only 30
    row = reconcile_mc_date("2026-07-16", mc, {"AAPL": 30.0}, [], CLOSES, None)
    assert row["gap_dollars"] == pytest.approx(2_000.0)   # 20 sh * 100
    assert any("MC-POSITION-GAP" in a for a in row["alarms"])


def test_mc_rejected_order_alarms():
    mc = _mc_row({"AAPL": 5_000})
    orders = [{"ticker": "AAPL", "side": "buy", "status": "rejected", "filled_qty": 0.0,
               "fill_price": None, "client_order_id": "h26mc-AAPL-abc"}]
    row = reconcile_mc_date("2026-07-16", mc, {"AAPL": 50.0}, orders, CLOSES, None)
    assert row["orders"]["rejected"] == 1
    assert any("MC-REJECTS" in a for a in row["alarms"])


def test_mc_ignores_foreign_tagged_orders():
    mc = _mc_row({"AAPL": 5_000})
    orders = [{"ticker": "AAPL", "side": "buy", "status": "rejected", "filled_qty": 0.0,
               "fill_price": None, "client_order_id": "h26-AAPL-xyz"}]   # shared-account tag
    row = reconcile_mc_date("2026-07-16", mc, {"AAPL": 50.0}, orders, CLOSES, None)
    assert row["orders"]["rejected"] == 0             # not an h26mc order — not counted here


def test_mc_silent_flat_alarms_after_two_nights():
    mc = _mc_row({"AAPL": 5_000})
    r1 = reconcile_mc_date("2026-07-16", mc, {}, [], CLOSES, None)
    assert r1["flat_nights"] == 1 and not any("SILENT-FLAT" in a for a in r1["alarms"])
    r2 = reconcile_mc_date("2026-07-17", mc, {}, [], CLOSES, r1)
    assert r2["flat_nights"] == 2 and any("MC-SILENT-FLAT" in a for a in r2["alarms"])


def test_mc_monthly_drag_band_trips():
    mc = _mc_row({"AAPL": 5_000})
    # seed a trailing history already near the 30 bps/month band, then add today's drag
    prior = {"drag_bps_trail": [29.0], "flat_nights": 0}
    orders = [{"ticker": "AAPL", "side": "buy", "status": "filled", "filled_qty": 50.0,
               "fill_price": 102.0, "client_order_id": "h26mc-AAPL-abc"}]   # 200 bps slip
    row = reconcile_mc_date("2026-07-16", mc, {"AAPL": 50.0}, orders, CLOSES, prior)
    assert row["drag_month_bps"] > 30.0
    assert any("MC-DRAG" in a for a in row["alarms"])


# ---------- per-leg submit is fail-safe (no partial-night data loss) ----------

def test_submit_leg_success_returns_fills_and_ok():
    fills = [{"client_order_id": "h26-QQQ-abc", "ticker": "QQQ"},
             {"client_order_id": "h26mc-AAPL-xyz", "ticker": "AAPL"}]   # foreign tag must be filtered
    brk = _FakeBroker(fills=fills)
    got, ok = submit_leg("shared", brk, {"QQQ": 10_000}, "h26")
    assert ok is True and brk.cancelled and brk.submitted[1] == "h26"
    assert [f["ticker"] for f in got] == ["QQQ"]        # only the h26- fill, not the h26mc- one


def test_submit_leg_failure_is_caught_and_flagged():
    # a raising broker (e.g. network error) must NOT propagate — it returns ([], False) so the
    # caller still writes the ledger row and the other account's leg proceeds
    brk = _FakeBroker(raise_on_submit=True)
    got, ok = submit_leg("dedicated momentum_concentrated", brk, {"AAPL": 5_000}, "h26mc")
    assert got == [] and ok is False


# ---------- broker factory: second-account creds ----------

def test_factory_missing_mc_creds_names_them(monkeypatch):
    from core.broker.alpaca import alpaca_paper_broker
    monkeypatch.delenv("ALPACA_MC_API_KEY_ID", raising=False)
    monkeypatch.delenv("ALPACA_MC_API_SECRET_KEY", raising=False)
    with pytest.raises(RuntimeError, match="ALPACA_MC_API_KEY_ID"):
        alpaca_paper_broker(lambda t: 100.0,
                            cred_names=("ALPACA_MC_API_KEY_ID", "ALPACA_MC_API_SECRET_KEY"))
