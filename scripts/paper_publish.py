"""paper_publish.py: publish a SANITIZED paper status to GitHub; keep the full report local.

Option A (local): a launchd job runs this on a schedule. It reuses paper_status.build_status()
(the SAME read-only reconciliation / gate / broker picture) and produces two outputs:

  • PUBLIC  → STATUS.md, pushed to GitHub. SANITIZED: aggregate health + verdicts only. No equity,
    cash, buying power, symbols, quantities, exposures, order IDs, allocations, or run schedule.
  • PRIVATE → artifacts/hunt2026/paper/STATUS_full.md (gitignored). The full detailed render(),
    for your eyes only. Email (paper_monitor) already carries the full report too.

Isolation: ALL git operations happen in a DEDICATED CLONE (~/projects/alpha-lab-status-publisher),
never in the active development tree. The publisher fetches + hard-resets that clone to origin/main,
writes STATUS.md, commits, and pushes from there, so it can never collide with your uncommitted
research, a branch switch, another agent, or a failed autostash. build_status() still runs in the
main tree (it needs the code + .env), but that is read-only and touches no git.

Keys stay on this Mac: build_status() loads them from .env (gitignored). The published STATUS.md
carries no numbers that could identify positions or size.

Usage:
  .venv/bin/python scripts/paper_publish.py            # write both reports, commit+push on change
  .venv/bin/python scripts/paper_publish.py --dry-run  # write both reports, no git (public → stdout dir)
  .venv/bin/python scripts/paper_publish.py --selfcheck # offline assert on the sanitizer, no IO
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

PUBLISHER_DIR = Path.home() / "projects" / "alpha-lab-status-publisher"
# The PC cannot reach Alpaca or this repo, so the vault is the only place it can read
# hunt2026's health from. MACHINES.md standing ask #1(c), 2026-09-09. Aggregate only —
# the same sanitized rows the public status carries, never positions or equity.
VAULT_STATUS = Path.home() / "Obrimrim" / "rimrimOS" / "runtime" / "hunt2026-status.json"
FULL_LOCAL = ROOT / "artifacts" / "hunt2026" / "paper" / "STATUS_full.md"  # gitignored (artifacts/*)
PAGES_DASHBOARD = "https://kristenharim.github.io/alpha-lab/dashboard.html"
ALPACA_LIVE = "https://app.alpaca.markets/paper/dashboard/overview"

_VERDICT = {0: "🟢 NOMINAL", 1: "🟡 TRANSITION", 2: "🔴 ACTION"}


def sanitize(status: dict, code: int) -> list[tuple[str, str]]:
    """Coarse, aggregate-only rows for the PUBLIC status. Deliberately drops every quantity:
    no equity/cash/buying power, no symbols/positions/counts, no order IDs, no sub-gate detail,
    no schedule times, no raw alarm text (alarms embed dollar figures)."""
    rh = status.get("run_health", {})
    sched_health = status.get("sched", {}).get("health", "?")
    broker_ok = status.get("broker", {}).get("ok", False)
    gate_overall = status.get("gate", {}).get("overall", "?")
    g4 = status.get("gate", {}).get("g4", "?")  # live == ledger target: coarse recon verdict only
    clock_state = status.get("clock", {}).get("state", "?")

    latest_cycle = {"HEALTHY": "Healthy", "PARTIAL": "Partial", "MISSING": "Pending"}.get(
        rh.get("status", "?"), rh.get("status", "?").title())
    gate_public = {"COMPLETE": "Complete", "NOT COMPLETE": "In progress"}.get(gate_overall, gate_overall)
    recon_public = {"PASS": "Complete", "FAIL": "Mismatch", "INCONCLUSIVE": "Pending"}.get(g4, "Pending")
    clock_public = {"NOT STARTED": "Not started", "STARTED": "Started",
                    "INCONSISTENT": "Inconsistent"}.get(clock_state, clock_state.title())
    manual = {2: "Required", 1: "Recommended", 0: "Not currently required"}.get(code, "Unknown")

    return [
        ("System", _VERDICT.get(code, "⚪ UNKNOWN")),
        ("Trader scheduler", "Loaded" if sched_health == "OK" else sched_health),
        ("Latest cycle", latest_cycle),
        ("Broker connection", "Healthy" if broker_ok else "Unreachable"),
        ("Legacy flatten gate", gate_public),
        ("Target reconciliation", recon_public),
        ("Clean-forward clock", clock_public),
        ("Manual intervention", manual),
    ]


def render_public(status: dict, code: int) -> str:
    """The committed STATUS.md, sanitized. GitHub renders it as the public insights surface."""
    rows = sanitize(status, code)
    w = max(len(k) for k, _ in rows)
    block = "\n".join(f"{(k + ':').ljust(w + 1)}  {v}" for k, v in rows)
    return (
        "# Paper status — Alpha Lab hunt2026\n\n"
        f"**{_VERDICT.get(code, '⚪ UNKNOWN')}** · refreshed `{status['generated']}`\n\n"
        "Aggregate operational health only — detailed positions, equity, and reconciliation are "
        f"kept private. Live trading view → [Alpaca paper]({ALPACA_LIVE}) · "
        f"project overview → [dashboard.html]({PAGES_DASHBOARD}).\n\n"
        "```text\n"
        f"{block}\n"
        "```\n"
    )


def _git(args: list[str], cwd: Path, timeout: int = 90) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["git", *args], cwd=cwd, capture_output=True, text=True, timeout=timeout,
        env={"GIT_TERMINAL_PROMPT": "0", "PATH": "/usr/bin:/bin:/usr/local/bin"},
    )


def _ensure_clone() -> bool:
    """Make sure the dedicated publisher clone exists. Returns False if it can't be created."""
    if (PUBLISHER_DIR / ".git").exists():
        return True
    url = _git(["remote", "get-url", "origin"], cwd=ROOT).stdout.strip()
    if not url:
        return False
    PUBLISHER_DIR.parent.mkdir(parents=True, exist_ok=True)
    return _git(["clone", "--single-branch", "--branch", "main", url, str(PUBLISHER_DIR)],
                cwd=PUBLISHER_DIR.parent, timeout=180).returncode == 0


def _publish_to_clone(md: str, generated: str) -> str:
    """Fetch + hard-reset the isolated clone to origin/main, write STATUS.md, commit, push.
    Content is deterministic, so a rejected push (race with the cloud paper-bot) is retried once."""
    for _ in range(2):
        _git(["fetch", "origin", "main"], cwd=PUBLISHER_DIR)
        _git(["reset", "--hard", "origin/main"], cwd=PUBLISHER_DIR)  # clone is machine-only, safe
        (PUBLISHER_DIR / "STATUS.md").write_text(md, encoding="utf-8")
        _git(["add", "STATUS.md"], cwd=PUBLISHER_DIR)
        if _git(["diff", "--cached", "--quiet"], cwd=PUBLISHER_DIR).returncode == 0:
            return "unchanged"
        _git(["commit", "-m", f"status: {generated}"], cwd=PUBLISHER_DIR)
        if _git(["push", "origin", "main"], cwd=PUBLISHER_DIR).returncode == 0:
            return "pushed"
    return "push deferred (will retry next run)"


def publish(now: dt.datetime, dry_run: bool = False) -> int:
    from scripts.paper_status import build_status, render  # read-only status assembly

    status, code = build_status(now)

    FULL_LOCAL.parent.mkdir(parents=True, exist_ok=True)
    FULL_LOCAL.write_text(render(status) + "\n", encoding="utf-8")  # private, gitignored
    md = render_public(status, code)

    if not dry_run and VAULT_STATUS.parent.is_dir():
        VAULT_STATUS.write_text(json.dumps({
            "generated": status["generated"],
            "verdict": _VERDICT.get(code, "UNKNOWN"),
            # status_code is the TRADING verdict (0 nominal / 1 transition / 2 action).
            # It is deliberately NOT called exit_code: check_producer_ownership.py reads
            # exit_code as "did this job fail", and a healthy 🟡 TRANSITION was being
            # reported as a broken producer (2026-09-11).
            "status_code": code,
            "status": "ok",
            "exit_code": 0,
            "rows": dict(sanitize(status, code)),
            "source": "alpha-lab/scripts/paper_publish.py (Mac, hourly)",
        }, indent=2) + "\n", encoding="utf-8")

    if dry_run:
        print(f"[publish] full → {FULL_LOCAL}\n[publish] public (dry-run, no git):\n\n{md}")
        return 0

    if not _ensure_clone():
        print(f"[publish] full report written; publisher clone unavailable — public push skipped  code={code}")
        return 0
    note = _publish_to_clone(md, status["generated"])
    print(f"[publish] full → {FULL_LOCAL.name} (private) · public STATUS.md {note}  exit_code={code}")
    return 0


def _selfcheck() -> int:
    status = {"generated": "2026-07-11 12:00", "run_health": {"status": "PARTIAL"},
              "sched": {"health": "OK"}, "broker": {"ok": True, "equity": 6969, "foreign_n": 3},
              "gate": {"overall": "NOT COMPLETE", "g4": "INCONCLUSIVE"},
              "clock": {"state": "NOT STARTED"},
              "alarms": ["CASH-LOW: buying power $123.45 below floor"]}
    md = render_public(status, 1)
    assert "🟡 TRANSITION" in md and "Broker connection:" in md, "missing verdict/rows"
    # no quantity/identifier may leak into the DATA BLOCK (the disclaimer prose may name fields)
    block = md.split("```text", 1)[1]
    for leak in ("6969", "$", "foreign", "123.45", "AMAT", "0.", "1.", "2."):
        assert leak not in block, f"LEAK: {leak!r} present in public data block"
    assert "app.alpaca.markets" in md, "missing live-view pointer"
    print("[publish] selfcheck OK — no sensitive fields in public output")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true", help="write both reports, skip all git")
    ap.add_argument("--selfcheck", action="store_true", help="offline assert on the sanitizer, no IO")
    args = ap.parse_args()
    if args.selfcheck:
        return _selfcheck()
    return publish(dt.datetime.now(), dry_run=args.dry_run)


if __name__ == "__main__":
    sys.exit(main())
