# HANDOFF — Alpha Lab orientation

One-read orientation for a new session. This file holds **stable** orientation and governance only.
It deliberately does **not** restate live numbers (book counts, allocations, NAVs, entitlement/pilot
state) — those drift, and duplicating them here creates a second source of truth that goes stale.
For anything dynamic, read the authoritative file linked below.

**DEPLOYMENT_MANIFEST.md is the single authority on live/deployment state; where anything disagrees,
the manifest wins.**

## Governance (read first)
- **Single-writer control plane** (DEPLOYMENT_MANIFEST.md § Governance): one Coordinator owns
  `scripts/hunt_paper_run.py`, `DEPLOYMENT_MANIFEST.md`, `research/hunt2026/STATUS.md`, `ledgers/**`,
  and scheduler config. Other sessions write **isolated research artifacts only** and must not touch
  the control plane.
- **Multiple sessions may run concurrently** in this repo. Prefer additive new files; don't edit
  another session's in-flight files.
- **Paper-only throughout. No real-money path. Never `--live` by hand.** Keys live in gitignored `.env`.
- **Sole scheduled order-submitter:** the launchd job `com.rimrim.hunt2026-paper`
  (`hunt_paper_run.py --live` + `hunt_paper_reconcile.py`, weekdays 20:30 PT). No other scheduler
  trades the book. (The old GitHub Actions `paper-trading` cron was disabled 2026-07-11 and is now a
  manual read-only auth check.)

## Where current state actually lives (read these, don't cache them here)
- **Live/deployment state, book classification, allocations, gates:** `DEPLOYMENT_MANIFEST.md`
- **Hunt2026 program status / ledgers / failures:** `research/hunt2026/{STATUS,TRIAL_LEDGER,FAILURES}.md`
- **Paper book status at a glance:** `scripts/paper_status.py` (reader) · `scripts/paper_monitor.py` (monitor)
- **Independent-Alpha program:** `research/independent_alpha/CANONICAL_STATE.md` + `INDEPENDENCE_MATRIX.md`
- **Discovery program:** `research/discovery/CHARTER.md` + `FINDINGS.md`
- **Stock-universe repair (survivorship / entitlement pilots):**
  `research/stock_universe_repair/PILOT_6_SECURITY.md` + `PILOT_RESULTS_CIQ.md`
- **Data-source entitlement state (Polygon / FactSet / FRED / Capital IQ / Finaeon):** the per-source
  status files under `research/**/data/` and `research/stock_universe_repair/*ENTITLEMENT*` — canonical
  there, not restated here.
- **Latest operational transition / flatten gate:** newest memo in `memos/`.

## Entry-point files
`DEPLOYMENT_MANIFEST.md` · `research/hunt2026/STATUS.md` · `research/independent_alpha/CANONICAL_STATE.md`
· `research/discovery/CHARTER.md` · `research/stock_universe_repair/PILOT_6_SECURITY.md` · `memos/`
