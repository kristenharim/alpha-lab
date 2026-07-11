"""Offline tests for the EXP-OPS-REALITY reconcile harness: fixture ledger rows + a mock
trading client. No network, no keys, no broker mutation (the mock has no submit method at all)."""
from scripts.hunt_paper_reconcile import (bucket_orders, orders_from_client, reconcile_date,
                                          trailing_means)

D = "2026-07-10"


def _books():
    return {
        "_account": {"date": D, "book": "_account", "gross": 1.0, "notional": 100_000.0,
                     "target_dollars": {"QQQ": 80_000.0, "AMD": 300.0}},
        "vol_managed_qqq": {"date": D, "book": "vol_managed_qqq", "gross": 0.8,
                            "notional": 50_000.0, "nav": 1.4,
                            "target_dollars": {"QQQ": 50_000.0}},
        "momentum_concentrated": {"date": D, "book": "momentum_concentrated", "gross": 0.9,
                                  "notional": 50_000.0, "nav": 1.1,
                                  "target_dollars": {"QQQ": 30_000.0, "AMD": 300.0}},
    }


def _order(sym="QQQ", side="buy", qty=100.0, price=500.5, status="filled", coid="h26-x-1"):
    return {"ticker": sym, "side": side, "status": status, "filled_qty": qty,
            "fill_price": price if qty else None, "client_order_id": coid, "submitted": D}


def test_slippage_sign_and_class():
    closes = {"QQQ": 500.0, "AMD": 100.0}
    orders = [_order("QQQ", "buy", 100, 500.5),          # etf, paid 10 bps above ref
              _order("AMD", "sell", 3, 99.8, coid="h26-x-2")]  # stock, sold 20 bps below ref
    row = reconcile_date(D, _books(), orders, {"QQQ": 100.0, "AMD": 3.0}, closes)
    assert row["n_fills"] == 2 and row["n_rejects"] == 0
    assert abs(row["slippage"]["etf"]["mean_bps"] - 10.0) < 0.1
    assert abs(row["slippage"]["stock"]["mean_bps"] - 20.0) < 0.1


def test_rejects_counted_and_rate():
    closes = {"QQQ": 500.0}
    orders = [_order(), _order("AMD", qty=0.0, status="rejected", coid="h26-x-2")]
    row = reconcile_date(D, _books(), orders, {}, closes)
    assert row["n_rejects"] == 1 and row["reject_rate"] == 0.5
    assert row["rejects"][0]["ticker"] == "AMD"


def test_self_cancels_are_not_rejects():
    orders = [_order("QQQ", qty=0.0, status="canceled")]  # our own cancel_all on a re-run
    row = reconcile_date(D, _books(), orders, {}, {"QQQ": 500.0})
    assert row["n_rejects"] == 0 and row["n_canceled"] == 1 and row["n_orders"] == 0


def test_book_drag_prorated_by_target_share():
    closes = {"QQQ": 500.0}
    row = reconcile_date(D, _books(), [_order()], {"QQQ": 100.0}, closes)
    # 10 bps on a $50,050 fill = $50.05 cost, split 5/8 vs 3/8 by target share
    drag_vm = row["books"]["vol_managed_qqq"]["drag_bps"]      # 50.05*(5/8)/50k*1e4
    drag_mc = row["books"]["momentum_concentrated"]["drag_bps"]
    assert abs(drag_vm - 6.256) < 0.05
    assert abs(drag_mc - 3.754) < 0.05


def test_silent_flat_alarm_needs_two_nights():
    closes = {"QQQ": 500.0, "AMD": 100.0}
    # QQQ filled + held, AMD book never trades and holds nothing
    pos = {"QQQ": 100.0}
    n1 = reconcile_date(D, _books(), [_order()], pos, closes)
    assert n1["books"]["momentum_concentrated"]["flat_nights"] == 0  # QQQ overlaps -> not flat
    books = _books()
    books["momentum_concentrated"]["target_dollars"] = {"AMD": 300.0}  # AMD-only book
    n1 = reconcile_date(D, books, [_order()], pos, closes)
    assert n1["books"]["momentum_concentrated"]["flat_nights"] == 1 and n1["alarms"] == []
    n2 = reconcile_date("2026-07-13", books, [], pos, closes,
                        prior_flat={b: r["flat_nights"] for b, r in n1["books"].items()})
    assert n2["books"]["momentum_concentrated"]["flat_nights"] == 2
    assert any("SILENT-FLAT" in a and "momentum_concentrated" in a for a in n2["alarms"])


def test_no_fills_is_honest_and_trailing_needs_20():
    row = reconcile_date(D, _books(), [], {}, {"QQQ": 500.0})
    assert row["n_orders"] == 0 and row["reject_rate"] is None
    assert row["slippage"]["etf"]["n"] == 0
    trail = trailing_means([row])
    assert trail["etf"]["mean_bps"] is None  # n < 20 -> no trailing verdict yet


def test_bucket_orders_attributes_to_latest_run_date_and_filters_tag():
    orders = [_order(),                                       # submitted on D
              {**_order(coid="h26-y-2"), "submitted": "2026-07-13"},
              {**_order(coid="other-1"), "submitted": D}]     # not h26 -> ignored
    b = bucket_orders(orders, [D, "2026-07-13"])
    assert len(b[D]) == 1 and len(b["2026-07-13"]) == 1


def test_orders_from_client_read_only_extraction():
    class _O:
        def __init__(self):
            self.symbol, self.side, self.status = "QQQ", "buy", "filled"
            self.filled_qty, self.filled_avg_price = "100", "500.5"
            self.client_order_id, self.submitted_at = "h26-QQQ-ab", "2026-07-10T21:00:00Z"

    class _TC:  # read-only mock: get_orders only, no submit/cancel methods exist
        def get_orders(self, filter=None):
            return [_O()]

    out = orders_from_client(_TC(), since=D)
    o = out[0]
    assert o == {"ticker": "QQQ", "side": "buy", "status": "filled", "filled_qty": 100.0,
                 "fill_price": 500.5, "client_order_id": "h26-QQQ-ab", "submitted": "2026-07-10"}


def test_foreign_positions_flag_statarb_residue():
    # AAPL is held but in no book target -> foreign (stat-arb/AMAT residue); QQQ is known
    closes = {"QQQ": 500.0, "AAPL": 200.0}
    row = reconcile_date(D, _books(), [], {"QQQ": 160.0, "AAPL": 5.0}, closes)
    fp = row["foreign_positions"]
    assert fp["n"] == 1 and fp["symbols"] == ["AAPL"] and abs(fp["dollars"] - 1000.0) < 1e-6
    assert any("FOREIGN-POSITIONS" in a for a in row["alarms"])
    # clean account -> no foreign, no alarm
    row2 = reconcile_date(D, _books(), [], {"QQQ": 160.0}, closes)
    assert row2["foreign_positions"]["n"] == 0
    assert not any("FOREIGN" in a for a in row2["alarms"])


def test_partial_and_replaced_classified():
    closes = {"QQQ": 500.0}
    orders = [_order(),                                              # full fill
              _order(qty=40.0, status="canceled", coid="h26-x-2"),  # partial (filled 40, rest canceled)
              _order(qty=0.0, status="replaced", coid="h26-x-3")]   # replacement, not a reject
    row = reconcile_date(D, _books(), orders, {"QQQ": 140.0}, closes)
    assert row["n_fills"] == 2 and row["n_partial"] == 1 and row["n_replaced"] == 1
    assert row["n_rejects"] == 0  # replaced is not a reject
