"""Paper-book unit tests. Weighted toward reconcile — the spec flags terminal-event
disambiguation as the unit where a bug BIASES the answer (a false 'delisted'
manufactures the survivorship signal), so it gets the most fixtures."""
import numpy as np
import pandas as pd

from tracks.statarb.paper.reconcile import Reconciler, DEAD_NAME_REASONS
from tracks.statarb.paper.report import bracket_report
from tracks.statarb.paper.signal import _bucket, target_book
from scripts.paper_book_run import dry_run


# ---- signal: bucket boundaries (the -2 / -3 edges that split the floored series) ----
def test_bucket_edges():
    assert _bucket(+1.5, -1) == "short"
    assert _bucket(-1.5, +1) == "long_shallow"
    assert _bucket(-2.0, +1) == "long_shallow"     # spec: -2 <= s is shallow (inclusive edge)
    assert _bucket(-2.01, +1) == "long_deep"       # strictly below -2 is deep
    assert _bucket(-3.01, +1) == "long_verydeep"
    assert _bucket(float("nan"), +1) == "long_shallow"


# ---- reconcile: the disambiguation table, row by row ----
def test_transient_halt_keeps_position():
    r = Reconciler()
    reason, keep = r.classify("AAA", "halted", in_index=True)
    assert (reason, keep) == ("halt", True)        # mark, do NOT book a close


def test_stuck_halt_quarantines_not_delists():
    r = Reconciler()
    for _ in range(6):                              # exceed HALT_MAX_DAYS=5
        reason, keep = r.classify("BBB", "halted", in_index=True)
    assert reason == "quarantine" and keep is True  # never auto-books a dead-name loss


def test_genuine_delisting_books_dead_name():
    r = Reconciler()
    reason, keep = r.classify("CCC", "delisted", in_index=False, successor=None)
    assert (reason, keep) == ("delisted", False)
    assert reason in DEAD_NAME_REASONS


def test_symbol_change_migrates_not_dead():
    r = Reconciler()
    reason, keep = r.classify("DDD", "delisted", in_index=False, successor="DDD2",
                              event={"type": "symbol_change"})
    assert reason == "corporate_action_follow" and keep is False
    assert reason not in DEAD_NAME_REASONS         # a rename is NOT a survivorship loss


def test_delisted_with_successor_quarantines():
    # ambiguous (delisted but a successor exists) → guardrail, never a false dead name
    r = Reconciler()
    reason, keep = r.classify("EEE", "delisted", in_index=False, successor="EEE2")
    assert reason == "quarantine" and keep is True


def test_gap_stop_on_deep_long():
    r = Reconciler()
    reason, keep = r.classify("FFF", "tradable", open_price=5.0, deep_floor=8.0,
                              entry_side="long")
    assert (reason, keep) == ("gap_stop", False)


# ---- report: floored identity + dead-name drag reads the same events ----
def test_report_premium_and_drag():
    nav = [{"date": "d1", "net": 0.03, "floored_net": 0.01},   # premium 0.02/day
           {"date": "d2", "net": 0.04, "floored_net": 0.02}]
    positions = [{"ticker": "CCC", "close_reason": "delisted", "realized_pnl": -0.5},
                 {"ticker": "GGG", "close_reason": "band_flip", "realized_pnl": 0.1}]
    rep = bracket_report(nav, positions)
    assert rep["dead_name_events"] == 1            # band_flip is NOT a dead name
    assert rep["dead_name_drag"] == -0.5
    assert rep["full_sharpe"] > rep["floored_sharpe"]  # premium is positive here


# ---- driver: full nightly loop runs end-to-end with no network ----
def test_dry_run_smoke(tmp_path):
    rep = dry_run(days=20, window=30, out_root=tmp_path)
    assert rep["n_days"] == 20
    assert (tmp_path / "daily_nav.jsonl").exists()
    assert (tmp_path / "scorecard.md").exists()
    assert rep["dead_name_events"] == 0            # survivor panel has no delistings
