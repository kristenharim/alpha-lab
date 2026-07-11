# Paper Status Interface — PROPOSAL (docs-only draft, for approval)

**Status:** DOCUMENTATION-ONLY. `scripts/paper_status.py` is **not implemented**. This memo neither changes
launchd, nor wires alerts, nor fixes a monitoring cadence. It records the resolved data sources and the revised
output design for approval **before** any code is written. Read-only sweep only — no file under the control plane
was modified.

Scope guardrail: the eventual tool **writes nothing on any path** (no ledger, no manifest, no clean-start marker).
A new read-only reader script is an additive isolated artifact; recording a clean-forward start remains a
Coordinator action gated on an approved clean-cycle report (`CLEAN_CYCLE_REPORT_TEMPLATE.md` §11).

---

## A. Resolved sources (verified read-only, 2026-07-11)

### 1. launchd plist path
`~/Library/LaunchAgents/com.rimrim.hunt2026-paper.plist` (installed 2026-07-10 23:00).
`ProgramArguments`: `cd .../alpha-lab && .venv/bin/python scripts/hunt_paper_run.py --live; .venv/bin/python scripts/hunt_paper_reconcile.py`.
Schedule: `StartCalendarInterval` weekdays 20:30 local. `RunAtLoad = false`.

### 2. StandardOutPath / StandardErrorPath
Both point to the **same file**: `/Users/kristenho/projects/alpha-lab/artifacts/hunt2026/paper/nightly.log`
(stdout and stderr interleave in one log).

### 3. Real log location — currently ABSENT
`artifacts/hunt2026/paper/` exists but is **empty**; `nightly.log` does not exist. The only `nightly.log` present
is `artifacts/statarb/paper/nightly.log`, a different program. So the launchd job has produced **no stdout yet** —
it has not run under launchd.

### 4. Does LastExitStatus correspond to the most recent scheduled run? — NO
`launchctl list` shows `LastExitStatus = 0`, no PID. But `RunAtLoad = false`, the schedule is weekdays 20:30, the
plist was installed **Sat 2026-07-10 23:00**, today is **Sat 2026-07-11**, and the next fire is **Mon 2026-07-13
20:30**. launchd has therefore **never fired this job**; `0` is the loaded-but-never-run default, not a real run
result. (The `_reconcile.jsonl` rows stamped 2026-07-10 ~22:45 were a **manual** invocation — 22:45 ≠ the 20:30
schedule.) **Consequence:** exit code + log are unreliable run-success signals until the job fires once under
launchd. Run health must be derived from **ledger evidence** (§5), with launchctl/log as secondary corroboration.

### 5. Ledger append that proves a successful nightly cycle
`hunt_paper_run.py` writes the seven book rows first, then writes the **`_account` live row last** (`_write_ledger`
at the end of the live path). That aggregate row — `{date: D, book: "_account", mode: "live"}` — is the runner's
completion marker. The reconcile step then appends one `_reconcile.jsonl` row for `D`. So:

> **A successful nightly cycle for session date D** = `_account.jsonl` has a `mode:"live"` row for `D`
> **AND** `_reconcile.jsonl` has a row for `D`. Runner-only (no reconcile row) = PARTIAL.

### 6. Authoritative clean-forward-start source
There is **no clean-forward-start timestamp anywhere yet** — not in `DEPLOYMENT_MANIFEST.md`, not in
`research/hunt2026/STATUS.md`. Per `CLEAN_CYCLE_REPORT_TEMPLATE.md` §11, the clean start is recorded by a
**Coordinator edit to `DEPLOYMENT_MANIFEST.md`** only after an approved clean-cycle report. Therefore:

> **Authoritative source = `DEPLOYMENT_MANIFEST.md`.** The status tool reads the manifest for a clean-forward-start
> line; absent → **NOT STARTED**. It does **not** create or read `_clean_start.json`.

Do not conflate this with manifest line 50 ("Active books (7) — started 2026-07-10"): that is the book-deployment
date, which still carries stat-arb residue. The clean-forward clock is the post-flatten, contamination-free
incubation start — a future, not-yet-recorded event.

---

## B. Revised output — three separated sections

The prior single block muddled batch-job state, live broker state, and readiness. Split them:

```
ALPHA LAB PAPER STATUS                    generated: 2026-07-13 13:15 PT

── 1. LATEST COMPLETED RUN (from ledgers) ─────────────────────────────
  Expected session:      2026-07-13 (weekdays 20:30)
  Run health:            HEALTHY | PARTIAL | MISSING | UNKNOWN
    runner (_account D):   present 2026-07-13
    reconcile (row D):     present 2026-07-13 22:47
  Seven books computed:  7 / 7 (live rows for D)
  Reconcile timestamp:   2026-07-13 22:47
  Corroboration (weak):  launchctl exit 0 · nightly.log mtime 2026-07-13 20:31
                         (secondary only — untrustworthy until job fires under launchd)

── 2. LIVE BROKER SNAPSHOT (fresh get_*, as-of 13:15 PT) ──────────────
  Broker connection:     HEALTHY
  Equity:                $100,794
  Cash:                  $  8,231
  Buying power:          $ 92,110
  Gross exposure:        1.41x
  Net exposure:         -0.31x
  Positions:             277  (foreign: 271)
  Open orders:           271

── 3. GATE / READINESS STATE (ledger + live) ─────────────────────────
  Position gap:          257%
  Silent-flat books:     6
  Four-part flatten gate: NOT COMPLETE
    g1 foreign=0:          FAIL (271)
    g2 remaining=0:        FAIL
    g3 no failed flatten:  — (needs live snapshot)
    g4 broker==ledger:     — (needs live snapshot)
  Clean forward clock:   NOT STARTED (no clean-start line in DEPLOYMENT_MANIFEST.md)
  Alarms (2):
    !! FOREIGN-POSITIONS: 271 symbols in no book target ($141,672)
    !! SILENT-FLAT: 6 books, no fill/position 4+ nights
  Next action:           Wait for open, re-run reconcile after fills, clear stat-arb/AMAT residue
```

Why the split matters here: section 1 answers "did the batch job run?", section 2 answers "what does the broker
show right now?", section 3 answers "are we allowed to start the clean clock?". These have different clocks,
different trust levels, and different failure modes.

Post-transition, section 3 collapses to `foreign 0 / gap <1% / gate COMPLETE / clock STARTED <ts> / Alarms: NONE`.
Plain text, pipeable, no HTML.

---

## C. Source table (per field)

| Section | Field | Source | Trust |
|---|---|---|---|
| 1 | Expected session | exchange calendar (weekday−holiday) | derived |
| 1 | Run health, 7/7 | `_account.jsonl` live row for D + `_reconcile.jsonl` row for D | **primary** |
| 1 | Reconcile timestamp | `_reconcile.jsonl` last `run_at` | primary |
| 1 | launchctl exit / log mtime | `launchctl list`, `nightly.log` stat | **secondary/weak** |
| 2 | Equity, cash, buying power | fresh `get_account()` | live |
| 2 | Positions, gross/net, foreign | `get_all_positions()` → reuse `foreign_decomposition` | live |
| 2 | Open orders | `get_orders(status=OPEN)` | live |
| 3 | Gap, silent-flat, g1, g2 | last `_reconcile.jsonl` row | file |
| 3 | g3, g4 | live snapshot vs ledger diff | live+file |
| 3 | Clean forward clock | `DEPLOYMENT_MANIFEST.md` clean-start line (absent → NOT STARTED) | authoritative |
| 3 | Alarms | `_reconcile.jsonl` `alarms[]` + live threshold checks | file+live |

Broker reads reuse `orders_from_client` / `positions_from_client` from `hunt_paper_reconcile.py` (already
read-only, `paper=True`). The tool imports them; it does not re-open a broker path of its own.

---

## D. Staleness rules
- **Run MISSING** if no `_account` live row for the expected session date; **PARTIAL** if runner row present but no
  reconcile row.
- **Ledger stale** if latest ledger `date` is behind the most recent completed session.
- Live broker snapshot is always "as-of now" (labelled).
- **Old-schema reconcile rows** (`flatten_complete` absent) degrade to `n == 0` fallback, as `print_report`
  already does — the current 4 rows are old-schema.

## E. Next action (deterministic precedence, first match wins)
1. Broker unreachable → "Restore broker connectivity; status degraded."
2. Run MISSING/PARTIAL or ledger stale → "Investigate nightly job for <D>."
3. <7/7 books → "N books failed to compute."
4. Rejected orders in last reconcile → "Investigate N rejected orders."
5. Flatten gate not complete → "Wait for open, re-run reconcile after fills, clear residue."
6. Gate complete but clock not started → "Populate clean-cycle report; submit clean-start for approval."
7. All clean → "Nominal — no action."

## F. Tests (one runnable check)
Split pure derivation (run-health from two ledger sets, gate verdicts, staleness, next-action) from I/O.
`tests/test_paper_status.py` asserts: old-schema reconcile row degrades without crashing; run-health returns
PARTIAL when reconcile row absent; MISSING when `_account` row absent; missing `nightly.log` never yields HEALTHY;
next-action precedence picks one line. No network in tests (mirrors reconcile's pure-core pattern).

## G. Failure behavior
Broker down → section 2 `UNHEALTHY`, g3/g4 `INCONCLUSIVE`, sections 1 and 3-from-file still print. Missing/empty
`_reconcile.jsonl` → those fields `NO DATA`. Never crash. Exit `0` nominal / `1` alarm active / `2` a source
unreachable. **No writes on any path, including error paths.**

## H. Cadence — recommendation only, NOT to be wired yet
Trading stays frozen (one after-close target calc, one submission, no intraday recompute). For monitoring, do
**not** hard-code 30-minute polling. First operational days: temporary read-only checks near the open and after
close to observe real order/fill behavior. Once stable, a light **open / midday / close** cadence is likely
sufficient for a slow daily paper book; tighten only if alerts or broker behavior justify it. Alert *delivery*
stays a separate thin wrapper, unbuilt until this reader is approved and proven.

---

*Docs-only draft. Nothing implemented. Approve the sources (§A) and output (§B) before any code, launchd, cadence,
or alert work.*
