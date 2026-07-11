"""Offline check for the dashboard's live-paper reducer: NAV compounding, day P&L, holdings.
No network, no ledgers on disk — writes a tiny synthetic ledger to a tmp dir."""
import json
from pathlib import Path

from scripts import build_dashboard as bd


def _write(tmp, nav_rows, tgt_rows):
    (tmp / "daily_nav.jsonl").write_text("\n".join(json.dumps(r) for r in nav_rows))
    (tmp / "targets.jsonl").write_text("\n".join(json.dumps(r) for r in tgt_rows))


def test_no_book_returns_none(tmp_path):
    assert bd.paper_stats(tmp_path) is None          # empty dir -> panel omitted, page still builds


def test_nav_compounds_and_ranks_holdings(tmp_path):
    _write(
        tmp_path,
        [{"date": "2026-07-08", "net": 0.10, "n_pos": 2},
         {"date": "2026-07-09", "net": -0.05, "n_pos": 3}],
        [{"date": "2026-07-09", "ticker": "AAA", "target_weight": 0.02},
         {"date": "2026-07-09", "ticker": "BBB", "target_weight": -0.05},   # largest |w| -> first, short
         {"date": "2026-07-08", "ticker": "OLD", "target_weight": 0.9}],    # stale date, must be ignored
    )
    s = bd.paper_stats(tmp_path)
    assert s["days"] == 2
    assert abs(s["day_pnl"] - (-0.05)) < 1e-12
    assert abs(s["cum_return"] - (1.10 * 0.95 - 1.0)) < 1e-12               # compounded, not summed
    assert s["n_pos"] == 3
    assert s["holdings"][0] == ("BBB", "short")                            # ranked by |weight|, signed
    assert "OLD" not in [t for t, _ in s["holdings"]]                       # only the latest date


def test_duplicate_nav_date_is_deduped(tmp_path):
    # append-only ledger re-ran the same day: the later row must win, not double-count.
    _write(
        tmp_path,
        [{"date": "2026-07-08", "net": 0.10, "n_pos": 2},
         {"date": "2026-07-08", "net": 0.20, "n_pos": 9}],   # same date, re-run
        [],
    )
    s = bd.paper_stats(tmp_path)
    assert s["days"] == 1                                     # one session, not two
    assert s["n_pos"] == 9                                    # last row wins
    assert abs(s["cum_return"] - 0.20) < 1e-12               # 0.20 only, not 1.10*1.20-1


if __name__ == "__main__":
    import tempfile
    with tempfile.TemporaryDirectory() as d:
        test_no_book_returns_none(Path(d))
    with tempfile.TemporaryDirectory() as d:
        test_nav_compounds_and_ranks_holdings(Path(d))
    with tempfile.TemporaryDirectory() as d:
        test_duplicate_nav_date_is_deduped(Path(d))
    print("paper_panel self-check OK")
