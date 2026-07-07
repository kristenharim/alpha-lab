# alpha-lab

Personal signal-generation research monorepo. Reproduces and extends methodologies from
recent quant literature (LLM news sentiment, PEAD/PEAD.txt, Gu-Kelly-Xiu ML cross-section),
judged by one shared, honest evaluation scorecard. **Paper trading only — nothing here
places real orders.**

Design spec and research journal live in the Obsidian vault:
`quant.rim/docs/superpowers/specs/2026-07-06-alpha-lab-design.md` and
`09-Pipeline/trading-lab/` (hypothesis notes, verdict memos).

## Lifecycle (stage-gate, every track)

| Stage | Gate |
| ----- | ---- |
| 0 — Hypothesis | HYP note in vault: mechanism, kill criteria, OOS protocol. **Kristen approves.** |
| 1 — Data build | Point-in-time dataset + lineage manifest (`data/manifest.jsonl`) |
| 2 — Replication | Reproduce the paper's headline result (validates pipeline, not alpha) |
| 3 — OOS + robustness | Net of costs, deflated Sharpe, subperiods, decay |
| 4 — Verdict | Kill-or-promote memo. **Kristen decides.** |
| 5 — Paper trading | Alpaca paper, nightly live-vs-backtest tracking |

## Layout

- `core/` — shared data loaders, backtest engine, evaluation scorecard
- `tracks/` — one package per research track, each with `STATE.md`
- `scripts/` — network/data pulls and runners (tests never touch the network)
- `data/`, `artifacts/` — gitignored heavy files
