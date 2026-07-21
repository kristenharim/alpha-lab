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
    """Minimal broker double for submit_leg: records calls, optionally raises on submit."""
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
    # the gap that matters is against the SETTLED book (last run's targets), which tonight's
    # positions should already reflect; last run wanted 50 sh, the account holds 30
    mc = _mc_row({"AAPL": 5_000})
    prior = {"legs": [{"sym": "AAPL", "target_shares": 50}], "drag_bps_trail": [], "flat_nights": 0}
    row = reconcile_mc_date("2026-07-16", mc, {"AAPL": 30.0}, [], CLOSES, prior)
    assert row["settled_gap_excess_dollars"] == pytest.approx(1_900.0)   # (20 - 1 tolerated) sh * 100
    assert any("MC-POSITION-GAP" in a for a in row["alarms"])


def test_mc_pending_rebalance_is_not_a_position_gap():
    # tonight's orders were submitted a minute ago and fill at the next open, so holding last
    # run's shares is correct, not a gap. This fired every rebalance night before the fix.
    mc = _mc_row({"AAPL": 3_000})                    # tonight wants 30 sh
    prior = {"legs": [{"sym": "AAPL", "target_shares": 50}], "drag_bps_trail": [], "flat_nights": 0}
    row = reconcile_mc_date("2026-07-16", mc, {"AAPL": 50.0}, [], CLOSES, prior)
    assert row["gap_dollars"] == pytest.approx(2_000.0)   # tonight's intended-vs-actual, reported
    assert row["settled_gap_excess_dollars"] == 0.0             # against the settled book: clean
    assert not any("MC-POSITION-GAP" in a for a in row["alarms"])


def test_mc_one_share_rounding_is_not_a_position_gap():
    # runner rounds shares off the live price, the reconcile off the close: a one-share
    # disagreement is the two bases, not drift
    mc = _mc_row({"AAPL": 5_000})
    prior = {"legs": [{"sym": "AAPL", "target_shares": 50}], "drag_bps_trail": [], "flat_nights": 0}
    row = reconcile_mc_date("2026-07-16", mc, {"AAPL": 49.0}, [], CLOSES, prior)
    assert not any("MC-POSITION-GAP" in a for a in row["alarms"])


def test_mc_position_gap_is_not_alarmed_on_a_replay():
    # a --since replay scores old dates against TODAY's positions, so the settled comparison
    # is meaningless there: computed and reported, never alarmed
    mc = _mc_row({"AAPL": 5_000})
    prior = {"legs": [{"sym": "AAPL", "target_shares": 50}], "drag_bps_trail": [], "flat_nights": 0}
    row = reconcile_mc_date("2026-07-16", mc, {"AAPL": 30.0}, [], CLOSES, prior, live_gap=False)
    assert row["settled_gap_excess_dollars"] == pytest.approx(1_900.0)
    assert not any("MC-POSITION-GAP" in a for a in row["alarms"])


def test_intraday_submit_gets_no_split_even_when_it_fills_later():
    """The fill's session being after the run date is not enough. An order placed while that
    session was trading crossed somewhere inside it, so (open - prior close) is a gap it never
    experienced and crediting it as drift overstates the market's share of the cost."""
    mc = _mc_row({"AAPL": 5_000})
    orders = [{"ticker": "AAPL", "side": "buy", "status": "filled", "filled_qty": 50.0,
               "fill_price": 103.5, "client_order_id": "h26mc-AAPL-a",
               "submitted": "2026-07-17", "pre_open": False,      # placed mid-session on the 17th
               "filled_session": "2026-07-17"}]
    row = reconcile_mc_date("2026-07-16", mc, {"AAPL": 50.0}, orders, CLOSES, None,
                            opens={"2026-07-17": {"AAPL": 103.0}})
    assert row["slippage_bps"]["median"] is not None
    assert row["slippage_bps"]["drift_mean"] is None


def test_a_residual_share_of_a_flat_target_is_not_tolerated():
    """The one-share allowance is for a rounding disagreement on a sized leg. A target of zero has
    no rounding basis, so a leftover share of a position that should be flat is a real residual."""
    mc = _mc_row({})
    prior = {"legs": [{"sym": "AAPL", "target_shares": 0}], "drag_bps_trail": [], "flat_nights": 0}
    row = reconcile_mc_date("2026-07-16", mc, {"AAPL": 1.0}, [], CLOSES, prior)
    assert row["settled_gap_excess_dollars"] == pytest.approx(100.0)   # the whole share, untolerated
    assert any("MC-POSITION-GAP" in a for a in row["alarms"])


def test_unpriceable_prior_target_is_unknown_not_zero():
    """A prior leg the reconcile could not price carries target_shares=None. Reading that as
    "zero shares expected" made every held share unexplained and fired a full-book gap alarm on
    a clean book."""
    mc = _mc_row({"AAPL": 5_000})
    prior = {"legs": [{"sym": "AAPL", "target_shares": None}], "drag_bps_trail": [],
             "flat_nights": 0}
    row = reconcile_mc_date("2026-07-16", mc, {"AAPL": 50.0}, [], CLOSES, prior)
    assert row["settled_gap_excess_dollars"] == 0.0
    assert not any("MC-POSITION-GAP" in a for a in row["alarms"])


def test_corporate_action_scale_slippage_withholds_the_split():
    """The vendor's OHLC is adjusted, the broker's fill price is raw. Across a split the gap is
    the adjustment factor, not execution, so the split is withheld rather than reported."""
    mc = _mc_row({"AAPL": 5_000})
    orders = [{"ticker": "AAPL", "side": "buy", "status": "filled", "filled_qty": 50.0,
               "fill_price": 400.0, "client_order_id": "h26mc-AAPL-a",     # 4x the adjusted close
               "submitted": "2026-07-16", "filled_session": "2026-07-17"}]
    row = reconcile_mc_date("2026-07-16", mc, {"AAPL": 50.0}, orders, CLOSES, None,
                            opens={"2026-07-17": {"AAPL": 103.0}})
    assert row["slippage_bps"]["median"] is not None      # the frozen statistic still sees it
    assert row["slippage_bps"]["drift_mean"] is None      # the reported split does not


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
    assert row["orders"]["rejected"] == 0             # not an h26mc order, not counted here


def test_mc_silent_flat_alarms_after_two_nights():
    mc = _mc_row({"AAPL": 5_000})
    r1 = reconcile_mc_date("2026-07-16", mc, {}, [], CLOSES, None)
    assert r1["flat_nights"] == 1 and not any("SILENT-FLAT" in a for a in r1["alarms"])
    r2 = reconcile_mc_date("2026-07-17", mc, {}, [], CLOSES, r1)
    assert r2["flat_nights"] == 2 and any("MC-SILENT-FLAT" in a for a in r2["alarms"])


def test_drag_trail_refuses_to_inherit_rectified_history():
    """Drag used to be a sum of absolute slippage. A partial replay could splice today's signed
    drag onto those rows and test the band on the hybrid, so an unmarked prior starts over."""
    mc = _mc_row({"AAPL": 5_000})
    legacy = {"drag_bps_trail": [40.0, 40.0], "flat_nights": 0}      # no drag_signed marker
    row = reconcile_mc_date("2026-07-16", mc, {"AAPL": 50.0}, [], CLOSES, legacy)
    assert row["drag_bps_trail"] == [0.0] and row["drag_signed"] is True
    assert not any("MC-DRAG" in a for a in row["alarms"])            # 80 bps of abs() not inherited

    nxt = reconcile_mc_date("2026-07-17", mc, {"AAPL": 50.0}, [], CLOSES, row)
    assert nxt["drag_bps_trail"] == [0.0, 0.0]                       # a marked prior does carry


def test_fill_open_withholds_when_the_crossing_session_lacks_the_symbol():
    """A halt or a data hole must withhold the split, not roll forward to a later session: the
    drift leg would then span two sessions and exec would absorb the extra day."""
    from scripts.hunt_paper_reconcile import _fill_open

    o = {"ticker": "AAPL", "submitted": "2026-07-16", "filled_session": "2026-07-17"}
    opens = {"2026-07-17": {"MSFT": 50.0}, "2026-07-20": {"AAPL": 103.0}}
    assert _fill_open(opens, o, "2026-07-16") is None


def test_mc_monthly_drag_band_trips():
    mc = _mc_row({"AAPL": 5_000})
    # seed a trailing history already near the 30 bps/month band, then add today's drag
    prior = {"drag_bps_trail": [29.0], "flat_nights": 0, "drag_signed": True}
    orders = [{"ticker": "AAPL", "side": "buy", "status": "filled", "filled_qty": 50.0,
               "fill_price": 102.0, "client_order_id": "h26mc-AAPL-abc"}]   # 200 bps slip
    row = reconcile_mc_date("2026-07-16", mc, {"AAPL": 50.0}, orders, CLOSES, prior)
    assert row["drag_month_bps"] > 30.0
    assert any("MC-DRAG" in a for a in row["alarms"])


def test_slippage_splits_into_overnight_drift_and_execution():
    # close 100, next open 103, fill 103.5: 300 bps of that fill was the market gapping open
    # before we could trade, 50 was execution. Both legs are on the close basis, so the pair
    # sums to the banded statistic exactly rather than nearly.
    mc = _mc_row({"AAPL": 5_000})
    orders = [{"ticker": "AAPL", "side": "buy", "status": "filled", "filled_qty": 50.0,
               "fill_price": 103.5, "client_order_id": "h26mc-AAPL-a",
               "submitted": "2026-07-16", "filled_session": "2026-07-17"}]   # crossed the 17th
    row = reconcile_mc_date("2026-07-16", mc, {"AAPL": 50.0}, orders, CLOSES, None,
                            opens={"2026-07-17": {"AAPL": 103.0}})
    s = row["slippage_bps"]
    assert s["median"] == pytest.approx(350.0, abs=0.5)
    assert s["split_n"] == 1
    assert s["drift_mean"] == pytest.approx(300.0, abs=0.5)
    assert s["exec_mean"] == pytest.approx(50.0, abs=0.5)
    assert s["drift_mean"] + s["exec_mean"] == pytest.approx(350.0)   # exact on means


def test_submit_stamp_reads_the_exchange_session_not_the_utc_date():
    """The 20:30 PT run submits at 03:30 UTC the NEXT calendar day. In exchange time that is
    23:30 on the session that placed it, after the close, so it rests until the next open."""
    from scripts.hunt_paper_reconcile import submit_stamp

    evening = submit_stamp("2026-07-21T03:30:00Z")          # 23:30 ET on the 20th, after the close
    assert evening["submitted"] == "2026-07-20" and evening["pre_open"] is False

    premarket = submit_stamp("2026-07-21T08:00:55Z")        # 04:00 ET, what this deployment does
    assert premarket["submitted"] == "2026-07-21" and premarket["pre_open"] is True

    intraday = submit_stamp("2026-07-20T17:05:00Z")         # 13:05 ET, market open
    assert intraday["submitted"] == "2026-07-20" and intraday["pre_open"] is False

    assert submit_stamp("")["submitted"] is None            # unusable stamp withholds, never guesses


def test_pre_open_orders_belong_to_the_previous_run():
    """A run builds its book from the last complete session and stamps its row with that session.
    Submitting before the open puts its orders on the NEXT calendar date, so filing them by date
    alone hands them to the following run: the fills land on a row whose close they never traded
    against, and the drift leg stops being an overnight gap."""
    from scripts.hunt_paper_reconcile import bucket_orders, submit_stamp

    orders = [{"client_order_id": "h26-AAPL-a", **submit_stamp("2026-07-21T08:00:55Z")}]  # 04:00 ET
    got = bucket_orders(orders, ["2026-07-20", "2026-07-21"])
    assert got["2026-07-20"] and not got["2026-07-21"]     # the run that placed it, not the next


def test_evening_orders_stay_with_their_own_run_on_consecutive_days():
    """The case the previous test missed: with runs on BOTH days, a raw UTC date pushed the
    evening order onto the next day's run and scored it against the wrong close."""
    from scripts.hunt_paper_reconcile import bucket_orders, submit_stamp

    orders = [{"client_order_id": "h26mc-AAPL-a", **submit_stamp("2026-07-21T03:30:00Z")},
              {"client_order_id": "h26mc-MSFT-b", **submit_stamp("2026-07-21T17:05:00Z")}]
    got = bucket_orders(orders, ["2026-07-20", "2026-07-21"])      # consecutive run days
    assert [o["client_order_id"] for o in got["2026-07-20"]] == ["h26mc-AAPL-a"]
    assert [o["client_order_id"] for o in got["2026-07-21"]] == ["h26mc-MSFT-b"]


def test_mc_orders_bucket_to_the_run_that_submitted_them():
    """The 20:30 run stamps the NEXT day on its orders. Keying MC's orders by their raw submit
    date matched no run date at all, so those fills were dropped from the MC reconcile entirely
    and the only ones it ever saw were same-day by-hand runs. That is also why the drift/exec
    split could never fire in the MC path: it is defined only for overnight submits."""
    from scripts.hunt_paper_reconcile import bucket_orders

    orders = [{"client_order_id": "h26mc-AAPL-a", "submitted": "2026-07-21"},   # 07-20's 20:30 run
              {"client_order_id": "h26mc-MSFT-b", "submitted": "2026-07-20"}]   # by-hand, same day
    got = bucket_orders(orders, ["2026-07-17", "2026-07-20"])
    assert [o["client_order_id"] for o in got["2026-07-20"]] == ["h26mc-AAPL-a", "h26mc-MSFT-b"]


def test_split_is_withheld_for_a_same_session_fill():
    # a fill that crossed in the run date's OWN session has no overnight gap to measure: that
    # session's open minus its own close is a reversed intraday move, not drift
    mc = _mc_row({"AAPL": 5_000})
    orders = [{"ticker": "AAPL", "side": "buy", "status": "filled", "filled_qty": 50.0,
               "fill_price": 103.5, "client_order_id": "h26mc-AAPL-a",
               "submitted": "2026-07-16", "filled_session": "2026-07-16"}]   # crossed same session
    row = reconcile_mc_date("2026-07-16", mc, {"AAPL": 50.0}, orders, CLOSES, None,
                            opens={"2026-07-16": {"AAPL": 103.0}})
    assert row["slippage_bps"]["median"] is not None
    assert row["slippage_bps"]["drift_mean"] is None and row["slippage_bps"]["split_n"] == 0


def test_slippage_split_is_absent_without_opens():
    # the next session may not have happened yet; that leaves the split unreported, never wrong
    mc = _mc_row({"AAPL": 5_000})
    orders = [{"ticker": "AAPL", "side": "buy", "status": "filled", "filled_qty": 50.0,
               "fill_price": 103.5, "client_order_id": "h26mc-AAPL-a",
               "submitted": "2026-07-17"}]
    row = reconcile_mc_date("2026-07-16", mc, {"AAPL": 50.0}, orders, CLOSES, None)
    assert row["slippage_bps"]["median"] is not None
    assert row["slippage_bps"]["drift_mean"] is None and row["slippage_bps"]["split_n"] == 0


def test_mc_drag_is_signed_so_overnight_noise_cancels():
    # fills land at the next open and are scored against the run-date close, so each night carries
    # an overnight gap of either sign. Summing absolute values ratcheted the band; signed nets out.
    mc = _mc_row({"AAPL": 5_000})
    buy_high = [{"ticker": "AAPL", "side": "buy", "status": "filled", "filled_qty": 50.0,
                 "fill_price": 102.0, "client_order_id": "h26mc-AAPL-a"}]      # +200 bps
    buy_low = [{"ticker": "AAPL", "side": "buy", "status": "filled", "filled_qty": 50.0,
                "fill_price": 98.0, "client_order_id": "h26mc-AAPL-b"}]        # -200 bps
    r1 = reconcile_mc_date("2026-07-16", mc, {"AAPL": 50.0}, buy_high, CLOSES, None)
    r2 = reconcile_mc_date("2026-07-17", mc, {"AAPL": 50.0}, buy_low, CLOSES, r1)
    assert r1["drag_bps"] > 0 and r2["drag_bps"] < 0
    # +102 bps and -98 bps of notional (dollar cost scales with the fill price), so the pair nets
    # to 4 bps instead of the 200 bps an absolute sum would have booked
    assert r2["drag_month_bps"] == pytest.approx(4.0, abs=0.1)
    assert not any("MC-DRAG" in a for a in r2["alarms"])


# ---------- per-leg submit is fail-safe (no partial-night data loss) ----------

def test_submit_leg_success_returns_fills_and_ok():
    fills = [{"client_order_id": "h26-QQQ-abc", "ticker": "QQQ"},
             {"client_order_id": "h26mc-AAPL-xyz", "ticker": "AAPL"}]   # foreign tag must be filtered
    brk = _FakeBroker(fills=fills)
    got, ok = submit_leg("shared", brk, {"QQQ": 10_000}, "h26")
    assert ok is True and brk.cancelled and brk.submitted[1] == "h26"
    assert [f["ticker"] for f in got] == ["QQQ"]        # only the h26- fill, not the h26mc- one


def test_submit_leg_failure_is_caught_and_flagged():
    # a raising broker (e.g. network error) must NOT propagate; it returns ([], False) so the
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
