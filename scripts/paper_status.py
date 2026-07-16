"""paper_status.py — STRICTLY READ-ONLY status for the hunt2026 paper system.

One manual command that answers, without reading ten JSON files by hand:
  1. LATEST COMPLETED RUN   — historical proof-of-cycle from the ledgers
  2. LIVE BROKER SNAPSHOT    — current accounts / positions / OPEN orders (as-of now), BOTH the
     shared ETF account and the dedicated momentum_concentrated account
  3. GATE / READINESS STATE  — four-part flatten gate, reconciliation, clean-forward clock

Read-only guarantees (enforced by test_paper_status.py::test_no_write_or_order_paths):
  - never submits / cancels / replaces / modifies any order;
  - never recomputes strategy targets (does NOT import hunt_paper_run);
  - never writes or appends to any file (reads via Path.read_text only);
  - broker access is get_account / get_all_positions / get_orders only (paper=True).

Authority rules (approved 2026-07-11, memos/archive/paper-status-proposal-2026-07-11.md §A):
  - a completed cycle for session D = _account.jsonl LIVE row for D AND _reconcile.jsonl row
    for D. Runner row only => PARTIAL.
  - launchctl / LastExitStatus / plist / nightly.log freshness are CORROBORATING scheduler
    metadata, never the primary completion proof. Before the first scheduled launchd fire, a
    missing log / default exit 0 is NOT a failure (reported PENDING FIRST RUN).
  - the ONLY clean-forward-start authority is DEPLOYMENT_MANIFEST.md. Absent => NOT STARTED.
    Manifest says started but foreign residue remains => INCONSISTENT. No _clean_start.json.

MC leg (added 2026-07-16, after the mc-isolation cutover of 2026-07-15):
  - the dedicated momentum_concentrated account is a SECOND live leg. It is monitored only when a
    live _account_mc row exists (that row IS the cutover proof); pre-cutover / rolled-back trees
    behave exactly as before and can never raise an MC alarm.
  - its _reconcile_mc.jsonl alarms are surfaced verbatim and count toward the exit code, so a broken
    MC leg cannot report a clean exit 0. The shared four-part flatten gate is NOT extended to it:
    that gate is about legacy stat-arb/MC residue in the SHARED account and stays shared-only.

Usage: .venv/bin/python scripts/paper_status.py
Exit:  0 nominal · 1 active operational alarm · 2 essential source unreachable / inconsistent.
"""
from __future__ import annotations

import datetime as dt
import json
import re
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

LEDGER_DIR = ROOT / "ledgers" / "hunt2026"
RECONCILE = LEDGER_DIR / "_reconcile.jsonl"
ACCOUNT = LEDGER_DIR / "_account.jsonl"
# Dedicated momentum_concentrated account (mc-isolation cutover 2026-07-15). Monitored only once
# the cutover has actually produced a live _account_mc row — pre-cutover trees stay unaffected.
RECONCILE_MC = LEDGER_DIR / "_reconcile_mc.jsonl"
ACCOUNT_MC = LEDGER_DIR / "_account_mc.jsonl"
# Duplicated from hunt_paper_run.MC_CRED_NAMES on purpose: the read-only guarantee forbids importing
# the runner (that would pull strategy recomputation into this script).
MC_CRED_NAMES = ("ALPACA_MC_API_KEY_ID", "ALPACA_MC_API_SECRET_KEY")
SHARED_CRED_NAMES = ("ALPACA_API_KEY_ID", "ALPACA_API_SECRET_KEY")
MANIFEST = ROOT / "DEPLOYMENT_MANIFEST.md"
PLIST = Path.home() / "Library" / "LaunchAgents" / "com.rimrim.hunt2026-paper.plist"
NIGHTLY_LOG = ROOT / "artifacts" / "hunt2026" / "paper" / "nightly.log"
LABEL = "com.rimrim.hunt2026-paper"

# ponytail: weekday-minus-holiday session calendar — pandas_market_calendars isn't installed.
# Upgrade path: swap _trading_day for mcal.get_calendar("XNYS") if that dep ever lands. This set
# only needs to cover the paper program's live window (2026-07 onward) to avoid false MISSING.
US_HOLIDAYS_2026 = {
    "2026-01-01", "2026-01-19", "2026-02-16", "2026-04-03", "2026-05-25",
    "2026-06-19", "2026-07-03", "2026-09-07", "2026-11-26", "2026-12-25",
}
RUN_HOUR, RUN_MIN = 20, 30  # launchd StartCalendarInterval

# Clean-forward-start marker convention in DEPLOYMENT_MANIFEST.md. Both forms are recognized,
# with or without bold, in any section:
#   Clean-forward start: NOT STARTED
#   Clean-forward start: 2026-07-13T13:45:00-07:00
CLEAN_LINE_RE = re.compile(r"clean[-\s]forward\s+start\s*:\s*(.+)", re.I)
ISO_RE = re.compile(
    r"\d{4}-\d{2}-\d{2}(?:[ T]\d{2}:\d{2}(?::\d{2})?(?:[+-]\d{2}:\d{2}|Z)?)?")

# Embedded fallback trading calendar covers ONLY these years (ponytail: hardcoded stopgap until
# pandas_market_calendars lands). Outside this range we do NOT assume weekdays are trading days —
# calendar confidence drops to LIMITED and session-staleness is reported UNKNOWN.
CAL_YEARS = (2026,)


# ============================ pure core (offline-testable) ============================

def _trading_day(d: dt.date, holidays: set[str]) -> bool:
    return d.weekday() < 5 and d.isoformat() not in holidays


def expected_session(now: dt.datetime, holidays: set[str]) -> str:
    """Most recent trading session whose 20:30 run should already have completed."""
    d = now.date()
    if _trading_day(d, holidays) and (now.hour, now.minute) >= (RUN_HOUR, RUN_MIN):
        return d.isoformat()
    d -= dt.timedelta(days=1)
    while not _trading_day(d, holidays):
        d -= dt.timedelta(days=1)
    return d.isoformat()


def first_scheduled_fire(plist_mtime: dt.datetime, holidays: set[str]) -> dt.datetime:
    """The first weekday 20:30 strictly after the plist was installed (when launchd first fires)."""
    d = plist_mtime.date()
    for _ in range(14):
        if _trading_day(d, holidays):
            fire = dt.datetime(d.year, d.month, d.day, RUN_HOUR, RUN_MIN)
            if fire > plist_mtime:
                return fire
        d += dt.timedelta(days=1)
    return plist_mtime  # pathological; treat as already passed


def run_health(session: str, account_live_dates: set[str], reconcile_dates: set[str],
               book_counts: dict[str, int]) -> dict:
    """Proof-of-cycle for `session` from ledger evidence only (the primary authority)."""
    has_runner = session in account_live_dates
    has_reconcile = session in reconcile_dates
    if has_runner and has_reconcile:
        status = "HEALTHY"
    elif has_runner:
        status = "PARTIAL"
    else:
        status = "MISSING"
    return {"session": session, "status": status,
            "runner": has_runner, "reconcile": has_reconcile,
            "books_computed": book_counts.get(session, 0)}


def scheduler_meta(exit_status: int | None, log_exists: bool, log_mtime: dt.datetime | None,
                   session: str, first_fire_passed: bool) -> dict:
    """CORROBORATING metadata only — never the completion proof (see module docstring)."""
    if not first_fire_passed:
        return {"health": "PENDING FIRST RUN",
                "note": "launchd job has not fired yet; missing log / exit 0 are not failures"}
    fresh = bool(log_exists and log_mtime and log_mtime.date().isoformat() >= session)
    if fresh and exit_status == 0:
        return {"health": "OK", "note": f"exit {exit_status}, log fresh"}
    if not log_exists:
        return {"health": "DEGRADED", "note": f"expected {session} 20:30 run left no log"}
    if exit_status not in (0, None):
        return {"health": "DEGRADED", "note": f"last exit {exit_status}"}
    return {"health": "DEGRADED", "note": "log not fresh for expected session"}


def flatten_gate(recon_foreign_n: int | None, recon_remaining: float | None,
                 live_ok: bool, live_foreign_n: int | None,
                 live_failed_flatten: bool | None) -> dict:
    """Four-part gate (CLEAN_CYCLE_REPORT_TEMPLATE.md §3). Old-schema reconcile rows
    (foreign fields absent) map to INCONCLUSIVE, never a false PASS/FAIL."""
    g1 = "INCONCLUSIVE" if recon_foreign_n is None else ("PASS" if recon_foreign_n == 0 else "FAIL")
    g2 = "INCONCLUSIVE" if recon_remaining is None else ("PASS" if recon_remaining == 0 else "FAIL")
    if not live_ok:
        g3 = g4 = "INCONCLUSIVE"
    else:
        g3 = "INCONCLUSIVE" if live_failed_flatten is None else ("FAIL" if live_failed_flatten else "PASS")
        if recon_foreign_n is None:
            g4 = "INCONCLUSIVE"
        else:
            g4 = "PASS" if live_foreign_n == recon_foreign_n else "FAIL"
    verdicts = (g1, g2, g3, g4)
    complete = all(v == "PASS" for v in verdicts)
    return {"g1": g1, "g2": g2, "g3": g3, "g4": g4,
            "complete": complete, "overall": "COMPLETE" if complete else "NOT COMPLETE"}


def parse_clean_start(manifest_text: str) -> str | None:
    """The clean-forward-start timestamp, or None for `NOT STARTED` / absent / non-timestamp.
    Recognizes both approved forms, bolded or not, in any section."""
    m = CLEAN_LINE_RE.search(manifest_text)
    if not m:
        return None
    val = m.group(1).strip().strip("*").strip()
    if val.upper().startswith("NOT STARTED"):
        return None
    iso = ISO_RE.search(val)
    return iso.group(0) if iso else None


def calendar_confidence(now: dt.datetime) -> str:
    """OK inside the embedded calendar's supported years, else LIMITED (fail conservatively)."""
    return "OK" if now.year in CAL_YEARS else "LIMITED"


def clean_clock(manifest_ts: str | None, residue_present: bool) -> dict:
    """Clean-forward clock from the manifest ONLY. `residue_present` = foreign positions still
    held per the latest evidence (ledger and/or live)."""
    if manifest_ts is None:
        return {"state": "NOT STARTED", "ts": None,
                "note": "no clean-forward start recorded in DEPLOYMENT_MANIFEST.md"}
    if residue_present:
        return {"state": "INCONSISTENT", "ts": manifest_ts,
                "note": "manifest records a clean start but foreign residue is still held"}
    return {"state": "STARTED", "ts": manifest_ts, "note": None}


def next_action(broker_ok: bool, run_status: str, books_ok: bool, rejects: int,
                gate_complete: bool, clock_state: str, first_fire_passed: bool) -> str:
    """Deterministic single next operational action — first matching rule wins."""
    if not broker_ok:
        return "Restore broker connectivity; live snapshot is degraded."
    if run_status in ("MISSING", "PARTIAL") and first_fire_passed:
        return f"Investigate nightly job — last cycle {run_status.lower()}."
    if not books_ok:
        return "One or more books failed to compute; check the nightly cycle."
    if rejects:
        return f"Investigate {rejects} rejected order(s) from the last cycle."
    if not gate_complete:
        return "Wait for market open, re-run reconcile after fills, clear stat-arb/AMAT residue."
    if clock_state == "INCONSISTENT":
        return "Resolve clean-clock inconsistency: manifest says started but residue remains."
    if clock_state == "NOT STARTED":
        return "Populate the clean-cycle report and submit the clean-start edit for approval."
    return "Nominal — no action."


def exit_code(essential_bad: bool, clock_inconsistent: bool, alarms_active: bool) -> int:
    if essential_bad or clock_inconsistent:
        return 2
    if alarms_active:
        return 1
    return 0


def render(s: dict) -> str:
    """Format the assembled status dict into the three-section block."""
    L: list[str] = []
    L.append(f"ALPHA LAB PAPER STATUS                    generated: {s['generated']}")
    rh, sm = s["run_health"], s["sched"]
    L.append("\n── 1. LATEST COMPLETED RUN (ledger evidence) ─────")
    if s.get("calendar_confidence", "OK") != "OK":
        yrs = "/".join(str(y) for y in CAL_YEARS)
        L.append(f"  Calendar confidence:   {s['calendar_confidence']} "
                 f"(outside embedded {yrs} calendar — staleness UNKNOWN)")
        L.append(f"  Expected session:      {rh['session']}  [UNKNOWN — verify manually]")
    else:
        L.append(f"  Expected session:      {rh['session']}")
    L.append(f"  Run health:            {rh['status']}")
    L.append(f"    runner (_account):     {'present' if rh['runner'] else 'MISSING'}")
    L.append(f"    reconcile row:         {'present' if rh['reconcile'] else 'MISSING'}")
    L.append(f"  Seven books computed:  {rh['books_computed']} / 7")
    L.append(f"  Reconcile timestamp:   {s.get('reconcile_ts') or 'NO DATA'}")
    h = s.get("hist_orders")
    if h:
        L.append(f"  Orders that cycle:     submitted {h['n_orders']}  filled {h['n_fills']}  "
                 f"partial {h['n_partial']}  rejected {h['n_rejects']}  (historical)")
    else:
        L.append("  Orders that cycle:     NO DATA")
    L.append(f"  Scheduler (corrob.):   {sm['health']} — {sm['note']}")

    b = s["broker"]
    L.append("\n── 2. LIVE BROKER SNAPSHOT (fresh get_*, as-of now) ───")
    if not b["ok"]:
        L.append(f"  Broker connection:     UNHEALTHY — {b.get('error', 'unreachable')}")
    else:
        L.append("  Broker connection:     HEALTHY")
        L.append(f"  Equity:                ${b['equity']:,.0f}")
        L.append(f"  Cash:                  ${b['cash']:,.0f}")
        L.append(f"  Buying power:          ${b['buying_power']:,.0f}")
        L.append(f"  Gross exposure:        {b['gross_x']:.2f}x")
        L.append(f"  Net exposure:          {b['net_x']:+.2f}x")
        L.append(f"  Positions:             {b['n_positions']}  (foreign: {b['foreign_n']})")
        L.append(f"  Open orders (now):     {b['open_orders_n']}  (currently open, not historical)")

    mc = s.get("mc") or {"active": False}
    if mc["active"]:
        L.append("\n  -- dedicated momentum_concentrated account --")
        if not mc["ok"]:
            L.append(f"  MC broker connection:  UNHEALTHY — {mc.get('error', 'unreachable')}")
        else:
            L.append(f"  MC equity:             ${mc['equity']:,.0f}")
            L.append(f"  MC positions:          {mc['n_positions']}  (foreign: {mc['foreign_n']})")
            L.append(f"  MC open orders (now):  {mc['open_orders_n']}")
            L.append(f"  MC reconcile row:      {s.get('recon_mc_ts') or 'NONE'}")

    g, cc = s["gate"], s["clock"]
    L.append("\n── 3. GATE / READINESS STATE ───────────")
    L.append(f"  Position gap:          {s.get('gap_str', 'NO DATA')}")
    L.append(f"  Silent-flat books:     {s.get('silent_flat', 'NO DATA')}")
    L.append(f"  Four-part flatten gate: {g['overall']}")
    L.append(f"    g1 foreign=0:          {g['g1']}")
    L.append(f"    g2 remaining=0:        {g['g2']}")
    L.append(f"    g3 no failed flatten:  {g['g3']}")
    L.append(f"    g4 broker==ledger:     {g['g4']}")
    clk = cc["state"] + (f" ({cc['ts']})" if cc.get("ts") else "")
    L.append(f"  Clean forward clock:   {clk}")
    if cc.get("note"):
        L.append(f"                         {cc['note']}")
    alarms = s.get("alarms", [])
    L.append(f"  Alarms ({len(alarms)}):" + ("" if alarms else " none"))
    for a in alarms:
        L.append(f"    !! {a}")
    if alarms and s.get("reconcile_ts"):
        L.append(f"    (reconcile-derived alarms are as of {s['reconcile_ts']}, "
                 f"not the live broker snapshot in section 2 above)")
    L.append(f"  Next action:           {s['next_action']}")
    return "\n".join(L)


# ============================ thin I/O layer ============================

def _load_ledgers() -> dict:
    """Read book + account ledgers. Returns account_live_dates, reconcile_dates, book_counts,
    latest reconcile row, latest _account target symbols. Raises on unreadable ledger dir."""
    from collections import defaultdict
    account_live_dates: set[str] = set()
    book_dates: dict[str, set[str]] = defaultdict(set)  # distinct book names per date (re-runs dup rows)
    for path in LEDGER_DIR.glob("*.jsonl"):
        if path.name in (RECONCILE.name, RECONCILE_MC.name):
            continue
        for line in path.read_text().splitlines():
            row = json.loads(line)
            if row.get("mode") != "live":
                continue
            d = row["date"]
            book = str(row.get("book") or "")
            if book == "_account":
                account_live_dates.add(d)
            elif not book.startswith("_"):
                # `_`-prefixed rows are account/meta ledgers (_account_mc, _reconcile_mc), never
                # strategy books — counting them inflates books_computed past 7 (mc cutover 2026-07-15).
                book_dates[d].add(book)
    book_counts = {d: len(s) for d, s in book_dates.items()}
    recon_rows = ([json.loads(x) for x in RECONCILE.read_text().splitlines()]
                  if RECONCILE.exists() else [])
    reconcile_dates = {r["date"] for r in recon_rows}
    latest_recon = recon_rows[-1] if recon_rows else None
    target_symbols = _latest_live_targets(ACCOUNT)
    recon_mc_rows = ([json.loads(x) for x in RECONCILE_MC.read_text().splitlines()]
                     if RECONCILE_MC.exists() else [])
    return {"account_live_dates": account_live_dates, "reconcile_dates": reconcile_dates,
            "book_counts": book_counts, "latest_recon": latest_recon,
            "target_symbols": target_symbols,
            "latest_recon_mc": recon_mc_rows[-1] if recon_mc_rows else None,
            "mc_target_symbols": _latest_live_targets(ACCOUNT_MC)}


def _latest_live_targets(path: Path) -> set[str]:
    """Target symbols of the most recent LIVE row in an account ledger; empty set if absent."""
    if not path.exists():
        return set()
    rows = [json.loads(x) for x in path.read_text().splitlines()
            if json.loads(x).get("mode") == "live"]
    return set(rows[-1].get("target_dollars", {})) if rows else set()


def _broker_snapshot(target_symbols: set[str], since: str,
                     cred_names: tuple[str, str] = SHARED_CRED_NAMES) -> dict:
    """Read-only broker snapshot: get_account + get_all_positions + get_orders(OPEN/ALL).
    Reuses orders_from_client from hunt_paper_reconcile (read-only). Returns ok=False on any
    failure so the caller degrades section 2 instead of crashing.
    `cred_names` selects the account: SHARED_CRED_NAMES (six ETF books) or MC_CRED_NAMES."""
    import os

    from core.env import load_dotenv
    load_dotenv()
    key, secret = os.environ.get(cred_names[0]), os.environ.get(cred_names[1])
    if not (key and secret):
        return {"ok": False, "error": f"{cred_names[0]} / {cred_names[1]} not in env/.env"}
    # ponytail: retry the live snapshot — a single transient APIError (Alpaca blip/rate-limit)
    # otherwise fires a false BROKER-UNREACHABLE alarm. 3 tries, 2s/4s backoff.
    last_err = None
    for attempt in range(3):
        if attempt:
            time.sleep(2 * attempt)
        try:
            return _broker_snapshot_once(key, secret, target_symbols, since)
        except Exception as e:  # broker down / SDK / network — retry, then degrade
            last_err = e
    return {"ok": False, "error": type(last_err).__name__}


def _broker_snapshot_once(key: str, secret: str, target_symbols: set[str], since: str) -> dict:
    """One live read-only broker read. Raises on any failure so _broker_snapshot can retry."""
    from alpaca.trading.client import TradingClient
    from scripts.hunt_paper_reconcile import orders_from_client
    tc = TradingClient(key, secret, paper=True)  # read-only usage only

    acct = tc.get_account()
    positions = tc.get_all_positions()
    gross = sum(abs(float(p.market_value)) for p in positions)
    net = sum(float(p.market_value) for p in positions)
    equity = float(acct.equity)
    foreign_syms = [p.symbol for p in positions
                    if p.symbol not in target_symbols and abs(float(p.qty)) > 1e-9]
    open_orders = orders_from_client(tc, since=since, statuses="open")
    # g3: a foreign position whose latest OPPOSING order failed terminally (rejected/expired)
    # while the position is still held. canceled = our own re-run cancel, not a failure.
    failed_flatten = None
    try:
        all_orders = orders_from_client(tc, since=since, statuses="all")
        held = {p.symbol: float(p.qty) for p in positions}
        failed_flatten = False
        for sym in foreign_syms:
            want = "sell" if held.get(sym, 0) > 0 else "buy"
            opp = [o for o in all_orders if o["ticker"] == sym and o["side"] == want]
            if opp and opp[-1]["status"] in ("rejected", "expired"):
                failed_flatten = True
                break
    except Exception:
        failed_flatten = None  # leave g3 INCONCLUSIVE
    return {"ok": True, "equity": equity, "cash": float(acct.cash),
            "buying_power": float(acct.buying_power),
            "gross_x": gross / equity if equity else 0.0,
            "net_x": net / equity if equity else 0.0,
            "n_positions": len(positions), "foreign_n": len(foreign_syms),
            "open_orders_n": len(open_orders), "failed_flatten": failed_flatten}


def _launchctl_exit() -> int | None:
    try:
        out = subprocess.run(["launchctl", "list", LABEL], capture_output=True, text=True, timeout=5)
        m = re.search(r'"LastExitStatus"\s*=\s*(-?\d+)', out.stdout)
        return int(m.group(1)) if m else None
    except Exception:
        return None


def _recon_foreign(row: dict | None) -> tuple[int | None, float | None]:
    """(foreign_n, flatten_remaining_total) from a reconcile row, tolerating old-schema rows."""
    if not row:
        return None, None
    fp = row.get("foreign_positions")
    if not fp:
        return None, None
    return fp.get("n"), fp.get("flatten_remaining_total")


def build_status(now: dt.datetime | None = None) -> tuple[dict, int]:
    """Assemble the full status dict and its exit code. Pure-ish: all writes are absent; the
    only side effects are read-only broker/file/launchctl reads. Reused by the monitor."""
    now = now or dt.datetime.now()
    holidays = US_HOLIDAYS_2026
    session = expected_session(now, holidays)

    # essential file sources: ledgers + manifest. Unreadable => exit 2.
    essential_bad = False
    try:
        led = _load_ledgers()
    except Exception:
        led = {"account_live_dates": set(), "reconcile_dates": set(), "book_counts": {},
               "latest_recon": None, "target_symbols": set()}
        essential_bad = True
    try:
        manifest_text = MANIFEST.read_text()
    except Exception:
        manifest_text = ""
        essential_bad = True

    recon = led["latest_recon"]
    recon_foreign_n, recon_remaining = _recon_foreign(recon)

    rh = run_health(session, led["account_live_dates"], led["reconcile_dates"], led["book_counts"])

    try:
        plist_mtime = dt.datetime.fromtimestamp(PLIST.stat().st_mtime)
    except Exception:
        plist_mtime = now
    ffp = now >= first_scheduled_fire(plist_mtime, holidays)
    log_exists = NIGHTLY_LOG.exists()
    log_mtime = dt.datetime.fromtimestamp(NIGHTLY_LOG.stat().st_mtime) if log_exists else None
    sched = scheduler_meta(_launchctl_exit(), log_exists, log_mtime, session, ffp)

    since = (dt.date.fromisoformat(session) - dt.timedelta(days=7)).isoformat()
    broker = _broker_snapshot(led["target_symbols"], since)
    # The dedicated MC account is a second live leg post-cutover. A live _account_mc row is the
    # cutover proof: absent (pre-cutover / rolled back) => inactive, and nothing here can alarm.
    mc = {"active": bool(led["mc_target_symbols"])}
    if mc["active"]:
        mc.update(_broker_snapshot(led["mc_target_symbols"], since, MC_CRED_NAMES))
        mc["active"] = True

    gate = flatten_gate(recon_foreign_n, recon_remaining, broker["ok"],
                        broker.get("foreign_n"), broker.get("failed_flatten"))

    residue = bool((recon_foreign_n or 0) > 0 or (broker["ok"] and broker.get("foreign_n", 0) > 0))
    clock = clean_clock(parse_clean_start(manifest_text), residue)

    rejects = recon.get("n_rejects", 0) if recon else 0
    silent_flat = sum(1 for b in (recon.get("books", {}).values() if recon else [])
                      if b.get("flat_nights", 0) >= 2)
    alarms = list(recon.get("alarms", [])) if recon else []
    if not broker["ok"]:
        alarms.append(f"BROKER-UNREACHABLE: {broker.get('error', 'unknown')}")
    if rh["status"] in ("MISSING", "PARTIAL") and ffp:
        alarms.append(f"CYCLE-{rh['status']}: no complete cycle for {session}")
    # MC leg: its reconcile already emits MC-prefixed alarms; surfacing them here is what rolls the
    # dedicated account into the exit code, so a broken MC leg can no longer report HEALTHY.
    recon_mc = led["latest_recon_mc"]
    if mc["active"]:
        alarms += list(recon_mc.get("alarms", [])) if recon_mc else []
        if not mc["ok"]:
            alarms.append(f"MC-BROKER-UNREACHABLE: {mc.get('error', 'unknown')}")

    na = next_action(broker["ok"] and (mc["ok"] if mc["active"] else True),
                     rh["status"], rh["books_computed"] >= 7, rejects,
                     gate["complete"], clock["state"], ffp)

    status = {
        "generated": now.strftime("%Y-%m-%d %H:%M %Z").rstrip(),
        "calendar_confidence": calendar_confidence(now),
        "run_health": rh, "sched": sched,
        "reconcile_ts": recon.get("run_at") if recon else None,
        "hist_orders": ({"n_orders": recon.get("n_orders", 0), "n_fills": recon.get("n_fills", 0),
                         "n_partial": recon.get("n_partial", 0), "n_rejects": rejects}
                        if recon else None),
        "broker": broker, "mc": mc, "gate": gate, "clock": clock,
        "recon_mc_ts": recon_mc.get("date") if recon_mc else None,
        "gap_str": (f"{recon['position_gap_frac']:.2%}" if recon and recon.get("position_gap_frac") is not None
                    else "NO DATA"),
        "silent_flat": silent_flat if recon else "NO DATA",
        "alarms": alarms, "next_action": na,
    }
    return status, exit_code(essential_bad, clock["state"] == "INCONSISTENT", bool(alarms))


def main() -> int:
    status, code = build_status()
    print(render(status))
    return code


if __name__ == "__main__":
    sys.exit(main())
