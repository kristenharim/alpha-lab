"""Offline unit tests for scripts/paper_status.py — no network, no disk writes.

Covers the approved authority rules: ledger-evidence proof-of-cycle, corroborating-only
scheduler metadata, manifest-only clean clock, historical-vs-live order separation, graceful
degradation, and the read-only guarantee.
"""
import datetime as dt
import re
from pathlib import Path

import scripts.paper_status as ps

H = ps.US_HOLIDAYS_2026


# ---------- old-schema reconcile rows ----------

def test_old_schema_reconcile_maps_inconclusive_not_crash():
    fn, rem = ps._recon_foreign({"date": "2026-07-10", "foreign_positions": {}})  # no n/remaining
    assert fn is None and rem is None
    g = ps.flatten_gate(fn, rem, live_ok=False, live_foreign_n=None, live_failed_flatten=None)
    assert g["g1"] == "INCONCLUSIVE" and g["g2"] == "INCONCLUSIVE"
    assert g["overall"] == "NOT COMPLETE"


def test_missing_reconcile_row_is_none():
    assert ps._recon_foreign(None) == (None, None)


# ---------- ledger loading: account/meta rows are not strategy books ----------

def test_account_mc_ledger_is_not_counted_as_a_book(tmp_path, monkeypatch):
    """Post-cutover there are two account ledgers. Only the seven strategy books may count."""
    import json as _json

    books = ["vol_managed_qqq", "vol_core_svxy", "trend_vol_qqq", "dual_momentum_gem",
             "dual_momentum_gold", "defensive_ensemble", "momentum_concentrated"]
    for b in books:
        (tmp_path / f"{b}.jsonl").write_text(
            _json.dumps({"date": "2026-07-15", "book": b, "mode": "live"}) + "\n")
    (tmp_path / "_account.jsonl").write_text(
        _json.dumps({"date": "2026-07-15", "book": "_account", "mode": "live",
                     "target_dollars": {"QQQ": 1.0}}) + "\n")
    (tmp_path / "_account_mc.jsonl").write_text(
        _json.dumps({"date": "2026-07-15", "book": "_account_mc", "mode": "live"}) + "\n")
    (tmp_path / "_reconcile.jsonl").write_text(_json.dumps({"date": "2026-07-15"}) + "\n")

    monkeypatch.setattr(ps, "LEDGER_DIR", tmp_path)
    monkeypatch.setattr(ps, "RECONCILE", tmp_path / "_reconcile.jsonl")
    monkeypatch.setattr(ps, "ACCOUNT", tmp_path / "_account.jsonl")
    led = ps._load_ledgers()

    assert led["book_counts"]["2026-07-15"] == 7      # was 8: _account_mc counted as a book
    assert led["account_live_dates"] == {"2026-07-15"}


# ---------- dedicated MC account: monitored, and it reaches the exit code ----------

def _clean_ledgers(mc_targets, mc_recon):
    """A fully nominal shared leg, so anything that alarms below comes from the MC leg."""
    return {"account_live_dates": {"2026-07-15"}, "reconcile_dates": {"2026-07-15"},
            "book_counts": {"2026-07-15": 7},
            "latest_recon": {"date": "2026-07-15", "run_at": "2026-07-15T20:31:27",
                             "n_rejects": 0, "alarms": [], "books": {},
                             "foreign_positions": {"n": 0, "flatten_remaining_total": 0}},
            "target_symbols": {"QQQ"},
            "latest_recon_mc": mc_recon, "mc_target_symbols": mc_targets}


def _ok_snapshot(_targets, _since, _creds=None):
    return {"ok": True, "equity": 100.0, "cash": 0.0, "buying_power": 0.0, "gross_x": 0.0,
            "net_x": 0.0, "n_positions": 0, "foreign_n": 0, "open_orders_n": 0,
            "failed_flatten": False}


def _stub_env(tmp_path, monkeypatch, ledgers):
    manifest = tmp_path / "DEPLOYMENT_MANIFEST.md"
    manifest.write_text("Clean-forward start: 2026-07-15T20:31:00-07:00\n")
    monkeypatch.setattr(ps, "MANIFEST", manifest)
    monkeypatch.setattr(ps, "PLIST", tmp_path / "absent.plist")
    monkeypatch.setattr(ps, "NIGHTLY_LOG", tmp_path / "absent.log")
    monkeypatch.setattr(ps, "_launchctl_exit", lambda: 0)
    monkeypatch.setattr(ps, "_load_ledgers", lambda: ledgers)
    monkeypatch.setattr(ps, "_broker_snapshot", _ok_snapshot)


def test_mc_reconcile_alarm_surfaces_and_drives_exit_code(tmp_path, monkeypatch):
    """A broken MC leg must not be able to report a clean exit 0 (mc-isolation cutover)."""
    _stub_env(tmp_path, monkeypatch, _clean_ledgers(
        {"AMD"}, {"date": "2026-07-15", "alarms": ["MC-POSITION-GAP: $6,119 broker-vs-model gap"]}))
    status, code = ps.build_status(dt.datetime(2026, 7, 16, 13, 0))
    assert status["mc"]["active"]
    assert any("MC-POSITION-GAP" in a for a in status["alarms"])
    assert code == 1                       # was 0: MC alarms never reached the exit code
    assert "MC equity:" in ps.render(status)


def test_mc_inactive_pre_cutover_cannot_alarm(tmp_path, monkeypatch):
    """No live _account_mc row (pre-cutover / rolled back) => MC leg is not monitored at all."""
    _stub_env(tmp_path, monkeypatch, _clean_ledgers(set(), None))
    status, code = ps.build_status(dt.datetime(2026, 7, 16, 13, 0))
    assert not status["mc"]["active"]
    assert [a for a in status["alarms"] if a.startswith("MC-")] == []
    assert code == 0
    assert "dedicated momentum_concentrated account" not in ps.render(status)


def test_mc_broker_unreachable_alarms(tmp_path, monkeypatch):
    _stub_env(tmp_path, monkeypatch, _clean_ledgers({"AMD"}, None))
    monkeypatch.setattr(ps, "_broker_snapshot",
                        lambda t, s, c=None: _ok_snapshot(t, s) if c is None
                        else {"ok": False, "error": "APIError"})
    status, code = ps.build_status(dt.datetime(2026, 7, 16, 13, 0))
    assert any(a.startswith("MC-BROKER-UNREACHABLE") for a in status["alarms"])
    assert code == 1


def test_broker_snapshot_names_the_missing_cred_vars(monkeypatch):
    """Offline: with no keys in env, the error must say WHICH account's keys are missing."""
    monkeypatch.setattr(ps, "load_dotenv", lambda *a, **k: None, raising=False)
    for name in (*ps.SHARED_CRED_NAMES, *ps.MC_CRED_NAMES):
        monkeypatch.delenv(name, raising=False)
    monkeypatch.setattr("core.env.load_dotenv", lambda *a, **k: None)
    out = ps._broker_snapshot(set(), "2026-07-08", ps.MC_CRED_NAMES)
    assert out["ok"] is False and "ALPACA_MC_API_KEY_ID" in out["error"]


def test_latest_live_targets_uses_latest_live_row(tmp_path):
    import json as _json
    p = tmp_path / "_account_mc.jsonl"
    p.write_text("\n".join([
        _json.dumps({"date": "2026-07-14", "mode": "dry", "target_dollars": {"NEVER": 1}}),
        _json.dumps({"date": "2026-07-14", "mode": "live", "target_dollars": {"OLD": 1}}),
        _json.dumps({"date": "2026-07-15", "mode": "live", "target_dollars": {"AMD": 1, "WDC": 2}}),
    ]) + "\n")
    assert ps._latest_live_targets(p) == {"AMD", "WDC"}
    assert ps._latest_live_targets(tmp_path / "absent.jsonl") == set()


# ---------- completed vs partial cycle detection ----------

def test_completed_cycle_detected():
    rh = ps.run_health("2026-07-10", {"2026-07-10"}, {"2026-07-10"}, {"2026-07-10": 7})
    assert rh["status"] == "HEALTHY" and rh["books_computed"] == 7


def test_runner_only_is_partial():
    rh = ps.run_health("2026-07-10", {"2026-07-10"}, set(), {"2026-07-10": 7})
    assert rh["status"] == "PARTIAL" and rh["runner"] and not rh["reconcile"]


def test_no_evidence_is_missing():
    rh = ps.run_health("2026-07-10", set(), set(), {})
    assert rh["status"] == "MISSING" and rh["books_computed"] == 0


# ---------- scheduler metadata: never the primary proof ----------

def test_missing_log_before_first_fire_is_not_failure():
    # plist installed Fri 2026-07-10 23:00; now Sat 2026-07-11 -> Monday's fire hasn't happened
    plist_mtime = dt.datetime(2026, 7, 10, 23, 0)
    now = dt.datetime(2026, 7, 11, 10, 14)
    ffp = now >= ps.first_scheduled_fire(plist_mtime, H)
    assert ffp is False
    sm = ps.scheduler_meta(exit_status=0, log_exists=False, log_mtime=None,
                           session="2026-07-10", first_fire_passed=ffp)
    assert sm["health"] == "PENDING FIRST RUN"


def test_first_fire_is_monday_after_friday_night_install():
    fire = ps.first_scheduled_fire(dt.datetime(2026, 7, 10, 23, 0), H)
    assert fire == dt.datetime(2026, 7, 13, 20, 30)  # skips Fri (already past) + weekend


def test_missed_expected_run_after_first_fire_degrades():
    sm = ps.scheduler_meta(exit_status=0, log_exists=False, log_mtime=None,
                           session="2026-07-14", first_fire_passed=True)
    assert sm["health"] == "DEGRADED"


def test_fresh_log_and_clean_exit_is_ok():
    sm = ps.scheduler_meta(exit_status=0, log_exists=True,
                           log_mtime=dt.datetime(2026, 7, 14, 20, 31),
                           session="2026-07-14", first_fire_passed=True)
    assert sm["health"] == "OK"


# ---------- expected session boundary ----------

def test_expected_session_saturday_rolls_to_friday():
    assert ps.expected_session(dt.datetime(2026, 7, 11, 10, 14), H) == "2026-07-10"


def test_expected_session_weekday_before_close_is_prior_day():
    # Tue 2026-07-14 09:00 (before the 20:30 run) -> Monday 2026-07-13
    assert ps.expected_session(dt.datetime(2026, 7, 14, 9, 0), H) == "2026-07-13"


# ---------- historical vs live order separation ----------

def test_historical_and_live_order_counts_are_separate():
    recon = {"date": "2026-07-10", "run_at": "2026-07-10T22:45", "n_orders": 40, "n_fills": 0,
             "n_partial": 0, "n_rejects": 0, "position_gap_frac": 2.5684, "books": {},
             "foreign_positions": {"n": 271, "flatten_remaining_total": 5.0}, "alarms": []}
    broker = {"ok": True, "equity": 100794.0, "cash": 8000.0, "buying_power": 90000.0,
              "gross_x": 1.41, "net_x": -0.31, "n_positions": 277, "foreign_n": 271,
              "open_orders_n": 271, "failed_flatten": False}
    out = ps.render({
        "generated": "2026-07-13 13:15", "run_health": ps.run_health(
            "2026-07-10", {"2026-07-10"}, {"2026-07-10"}, {"2026-07-10": 7}),
        "sched": {"health": "PENDING FIRST RUN", "note": "x"}, "reconcile_ts": recon["run_at"],
        "hist_orders": {"n_orders": 40, "n_fills": 0, "n_partial": 0, "n_rejects": 0},
        "broker": broker, "gate": ps.flatten_gate(271, 5.0, True, 271, False),
        "clock": ps.clean_clock(None, True), "gap_str": "256.84%", "silent_flat": 6,
        "alarms": [], "next_action": "x"})
    assert "submitted 40" in out and "(historical)" in out
    assert "Open orders (now):     271" in out and "not historical" in out


def test_public_transition_keeps_healthy_cycle_distinct_from_readiness():
    from scripts.paper_publish import sanitize

    rows = dict(sanitize({
        "run_health": {"status": "HEALTHY"},
        "sched": {"health": "PENDING FIRST RUN"},
        "broker": {"ok": True},
        "gate": {"overall": "NOT COMPLETE", "g4": "FAIL"},
        "clock": {"state": "NOT STARTED"},
    }, code=1))
    assert rows == {
        "System": "🟡 TRANSITION",
        "Trader scheduler": "PENDING FIRST RUN",
        "Latest cycle": "Healthy",
        "Broker connection": "Healthy",
        "Legacy flatten gate": "In progress",
        "Target reconciliation": "Mismatch",
        "Clean-forward clock": "Not started",
        "Manual intervention": "Recommended",
    }


# ---------- broker-unreachable degradation ----------

def test_broker_unreachable_renders_without_crash():
    out = ps.render({
        "generated": "t", "run_health": ps.run_health("2026-07-10", set(), set(), {}),
        "sched": {"health": "PENDING FIRST RUN", "note": "x"}, "reconcile_ts": None,
        "hist_orders": None, "broker": {"ok": False, "error": "ConnectionError"},
        "gate": ps.flatten_gate(None, None, False, None, None), "clock": ps.clean_clock(None, False),
        "gap_str": "NO DATA", "silent_flat": "NO DATA", "alarms": [], "next_action": "x"})
    assert "UNHEALTHY" in out and "ConnectionError" in out


def test_broker_down_gate_inconclusive():
    g = ps.flatten_gate(0, 0.0, live_ok=False, live_foreign_n=None, live_failed_flatten=None)
    assert g["g3"] == "INCONCLUSIVE" and g["g4"] == "INCONCLUSIVE"


# ---------- four-part flatten-gate mapping ----------

def test_gate_all_pass_is_complete():
    g = ps.flatten_gate(0, 0.0, True, 0, False)
    assert g == {"g1": "PASS", "g2": "PASS", "g3": "PASS", "g4": "PASS",
                 "complete": True, "overall": "COMPLETE"}


def test_gate_foreign_present_fails_g1():
    g = ps.flatten_gate(271, 5.0, True, 271, False)
    assert g["g1"] == "FAIL" and g["g2"] == "FAIL" and g["g4"] == "PASS" and not g["complete"]


def test_gate_broker_ledger_disagree_fails_g4():
    g = ps.flatten_gate(0, 0.0, True, 3, False)  # ledger says 0 foreign, broker shows 3
    assert g["g4"] == "FAIL"


def test_gate_failed_flatten_fails_g3():
    g = ps.flatten_gate(1, 1.0, True, 1, True)
    assert g["g3"] == "FAIL"


# ---------- clean-clock manifest states ----------

def test_clean_clock_not_started_when_absent():
    assert ps.parse_clean_start("no marker here") is None
    assert ps.clean_clock(None, False)["state"] == "NOT STARTED"


def test_clean_clock_started_when_marker_and_no_residue():
    txt = "## Account\n**Clean-forward start: 2026-07-15T20:30 PT**\n"
    ts = ps.parse_clean_start(txt)
    assert ts == "2026-07-15T20:30"
    assert ps.clean_clock(ts, residue_present=False)["state"] == "STARTED"


def test_clean_clock_inconsistent_when_started_but_residue():
    cc = ps.clean_clock("2026-07-15T20:30", residue_present=True)
    assert cc["state"] == "INCONSISTENT"


def test_book_started_line_is_not_a_clean_start():
    # the real manifest's "Active books (7) — started 2026-07-10" must NOT match
    assert ps.parse_clean_start("## Active books (7) — started 2026-07-10, equal capital") is None


def test_clean_start_not_started_form():
    assert ps.parse_clean_start("Clean-forward start: NOT STARTED") is None
    assert ps.parse_clean_start("**Clean-forward start: NOT STARTED**") is None
    assert ps.clean_clock(ps.parse_clean_start("Clean-forward start: NOT STARTED"), False)["state"] \
        == "NOT STARTED"


def test_clean_start_iso_with_timezone_offset():
    ts = ps.parse_clean_start("Clean-forward start: 2026-07-13T13:45:00-07:00")
    assert ts == "2026-07-13T13:45:00-07:00"
    assert ps.clean_clock(ts, residue_present=False)["state"] == "STARTED"


def test_clean_start_recognized_without_bold_or_section():
    txt = "random preamble\nClean-forward start: 2026-07-13T13:45:00-07:00\ntrailer\n"
    assert ps.parse_clean_start(txt) == "2026-07-13T13:45:00-07:00"


# ---------- fallback calendar confidence ----------

def test_calendar_confidence_ok_inside_supported_years():
    assert ps.calendar_confidence(dt.datetime(2026, 7, 11, 10, 0)) == "OK"


def test_calendar_confidence_limited_outside_supported_years():
    assert ps.calendar_confidence(dt.datetime(2027, 1, 4, 10, 0)) == "LIMITED"
    assert ps.calendar_confidence(dt.datetime(2025, 12, 1, 10, 0)) == "LIMITED"


def test_limited_calendar_renders_unknown_session():
    out = ps.render({
        "generated": "t", "calendar_confidence": "LIMITED",
        "run_health": ps.run_health("2027-01-01", set(), set(), {}),
        "sched": {"health": "PENDING FIRST RUN", "note": "x"}, "reconcile_ts": None,
        "hist_orders": None, "broker": {"ok": False, "error": "x"},
        "gate": ps.flatten_gate(None, None, False, None, None), "clock": ps.clean_clock(None, False),
        "gap_str": "NO DATA", "silent_flat": "NO DATA", "alarms": [], "next_action": "x"})
    assert "Calendar confidence:   LIMITED" in out and "UNKNOWN" in out


# ---------- deterministic single next-action precedence ----------

def test_next_action_broker_first():
    assert "broker" in ps.next_action(False, "HEALTHY", True, 0, True, "STARTED", True).lower()


def test_next_action_residue_before_clock():
    a = ps.next_action(True, "HEALTHY", True, 0, gate_complete=False, clock_state="NOT STARTED",
                       first_fire_passed=True)
    assert "residue" in a.lower()


def test_next_action_clock_not_started_when_gate_complete():
    a = ps.next_action(True, "HEALTHY", True, 0, gate_complete=True, clock_state="NOT STARTED",
                       first_fire_passed=True)
    assert "clean-start" in a.lower()


def test_next_action_nominal():
    a = ps.next_action(True, "HEALTHY", True, 0, True, "STARTED", True)
    assert a.startswith("Nominal")


def test_partial_cycle_not_flagged_before_first_fire():
    # PARTIAL/MISSING should not drive the action until launchd has actually fired once
    a = ps.next_action(True, "PARTIAL", True, 0, True, "STARTED", first_fire_passed=False)
    assert a.startswith("Nominal")


# ---------- exit-code precedence ----------

def test_exit_codes():
    assert ps.exit_code(False, False, False) == 0
    assert ps.exit_code(False, False, True) == 1
    assert ps.exit_code(True, False, False) == 2      # essential source unreachable
    assert ps.exit_code(False, True, False) == 2      # clock inconsistent
    assert ps.exit_code(False, True, True) == 2       # inconsistency outranks alarm


# ---------- read-only guarantee (no write / no order path) ----------

def _code_only(path: Path) -> str:
    """Module source with the docstring and all comments stripped — the guarantee is about
    executable code, not documentation (the docstring legitimately names what it does NOT do)."""
    import ast
    src = path.read_text()
    doc = ast.get_docstring(ast.parse(src), clean=False)
    if doc:
        src = src.replace(doc, "")            # drop the module docstring body
    return re.sub(r"#.*", "", src)            # drop comments


def test_no_write_or_order_paths():
    code = _code_only(Path(ps.__file__))
    forbidden = ["submit_order", "cancel_order", "replace_order", "cancel_all_orders",
                 ".write_text(", "_write_ledger", "hunt_paper_run", "open("]
    hits = [tok for tok in forbidden if tok in code]
    assert hits == [], f"read-only violation: forbidden tokens present: {hits}"


def test_module_does_not_import_runner():
    code = _code_only(Path(ps.__file__))
    assert not re.search(r"import\s+.*hunt_paper_run", code)
    # the reconcile import it DOES use is read-only (get_orders/get_all_positions only)
    assert "hunt_paper_reconcile" in code
