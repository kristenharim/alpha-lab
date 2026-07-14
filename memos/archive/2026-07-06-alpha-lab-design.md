# alpha-lab — Signal-Generation Research Monorepo (Design)

**Date:** 2026-07-06
**Status:** Approved by Kristen (structure, lifecycle, scorecard, Decision A, Decision B)
**Goal:** Genuine alpha research. Reproduce and extend methodologies from recent signal-generation literature, judged by one honest evaluation standard, feeding the vault trading-lab loop. Not a portfolio piece first; anything showable is a byproduct of research that survives its own audits.

## Context

- Kristen has institutional data access via Berkeley: WRDS (CRSP/Compustat/IBES), Bloomberg terminals, Capital IQ, Refinitiv/LSEG Workspace, FactSet, plus free retail APIs (yfinance, Alpaca, Ken French). Terminal access is on-campus, manual-export, download-capped — usable for building historical datasets, not live pipelines.
- Workflow split: Kristen sets direction, approves hypothesis gates, and makes kill/promote calls. Claude runs pipelines, backtests, and writeups in background sessions.
- The vault trading-lab (`09-Pipeline/trading-lab/`) already defines the quality bar: mechanism first, kill criteria before data, paper trading only. Existing `HYP-001 — Post-earnings announcement drift` seeds the PEAD track.
- Source material: two research syntheses (Downloads) covering LLM news sentiment (Lopez-Lira & Tang), PEAD.txt, Gu-Kelly-Xiu ML cross-section, dynamic factor timing, DeepLOB/TLOB, IPCA, formulaic alphas, DRL execution.

## Decisions Made

1. **Structure: monorepo + vault journal.** New git repo outside iCloud; vault keeps hypothesis notes and memos. (Chosen over vault-native and repo-per-track.)
2. **First tracks (3):** LLM news sentiment, PEAD → PEAD.txt, GKX ML cross-section. Backlog: dynamic factor timing (cheap, later), LOB deep learning (skills exercise only — not deployable alpha for an individual; revisit for learning value, not signal).
3. **Decision A — LLM contamination handling: honest version.** Historical backtests restricted to post-training-cutoff windows; entity-masked robustness check; the live forward paper-trade is the primary evidence. No full-history backtest with a model that has seen the outcomes.
4. **Decision B — GKX data: use Chen-Zimmermann Open Source Asset Pricing panel** (~200 pre-built replicated characteristics) instead of hand-building 94 characteristics from raw CRSP/Compustat. Validate ~5 characteristics against raw Compustat as a spot check. Research effort shifts to modeling and OOS discipline.

## Architecture

Repo: `~/projects/alpha-lab/` (outside iCloud; its own git, independent of the vault repo).

```
alpha-lab/
├── core/                  # shared infrastructure, written once
│   ├── data/              #   loaders: WRDS pulls, terminal-export ingestion, free APIs
│   ├── backtest/          #   portfolio construction, cost model, execution assumptions
│   └── eval/              #   THE scorecard — every track judged by this one rubric
├── tracks/
│   ├── llm_sentiment/     # Lopez-Lira & Tang reproduction + live forward test
│   ├── pead/              # numeric SUE → PEAD.txt (extends vault HYP-001)
│   └── gkx/               # Gu-Kelly-Xiu cross-section on Chen-Zimmermann panel
├── data/                  # gitignored — raw/ interim/ processed/ (parquet)
├── artifacts/             # gitignored — models, backtest outputs
├── memos/                 # short research memos, linked from vault trading-lab
└── docs/
```

Vault side: each track gets a `HYP-XXX` note in `09-Pipeline/trading-lab/` following the existing template (mechanism, persistence argument, kill criteria) and receives stage memos. Heavy artifacts never touch iCloud. Vault notes link to the repo; the repo's `memos/` are mirrored or linked into the vault, not duplicated at length.

## Lifecycle (stage-gate, identical for every track)

- **Stage 0 — Hypothesis.** HYP note in the vault: mechanism, why the edge should persist today, kill criteria, and the OOS evaluation protocol — all written before any data is pulled. **Kristen approves this gate; it is the only gate requiring her.**
- **Stage 1 — Data build.** Point-in-time dataset with a lineage manifest (source, pull date, filters, universe definition).
- **Stage 2 — Replication.** Reproduce the paper's headline result on its original sample period. Validates the pipeline, not the alpha.
- **Stage 3 — OOS + robustness.** Modern sample, net of costs, deflated Sharpe, subperiod/regime splits, decay curve.
- **Stage 4 — Verdict.** Kill-or-promote memo to the vault. Kristen decides.
- **Stage 5 — Paper trading.** Promoted signals run live on Alpaca paper with a nightly job tracking live vs. backtest divergence.

Misses and killed hypotheses are logged with root causes (mirrors the lock-in error-log discipline).

## Evaluation Harness (core/eval — the honest scorecard)

Non-negotiable for all tracks:

- Net-of-cost returns with an explicit per-horizon cost model (daily-rebalance tracks pay realistic spread + impact assumptions; monthly tracks pay less but still pay).
- Deflated Sharpe ratio / multiple-testing haircut (Harvey-Liu-Zhu t>3 logic applied to our own trials, not just the literature's).
- OOS protocol declared in the Stage-0 HYP note before any data is touched; no protocol changes after seeing results.
- Naive benchmarks reported alongside every result (buy-and-hold, equal-weight, the numeric version of any text signal).
- Subperiod and regime robustness; capacity/liquidity sanity check (does the signal live only in microcaps we couldn't trade?).
- A signal cannot survive by being graded on a friendlier rubric; the harness is shared code, unit-tested, and changes to it require a note in every affected track's state.

## Track Plans

### LLM news sentiment (fastest to live signal)
- Data: Refinitiv/LSEG news archive exports for history; Alpaca news API (or equivalent free feed) for the live loop. Scoring with Claude (cheap tier, e.g. Haiku) using the paper's YES/NO/UNKNOWN prompt structure as the baseline, then prompt variants.
- Contamination protocol (Decision A): historical evaluation only on windows after the scoring model's training cutoff; entity-masked robustness check (does the signal survive when tickers/companies are anonymized?); primary evidence is the live forward test: daily headline scoring → daily-rebalanced long-short paper portfolio.
- Known risk: this alpha is decaying as LLM adoption spreads — the decay rate is itself a documented, testable sub-hypothesis.

### PEAD → PEAD.txt (extends HYP-001)
- Phase 1 (numeric): SUE from Compustat + IBES via WRDS; event-study + calendar-time portfolio on the full panel; upgrades vault HYP-001 from sketch to full study.
- Phase 2 (text): SUE.txt from earnings-call transcripts (Refinitiv/CapIQ exports); regularized logistic text regression per the paper; report text drift vs. numeric drift head-to-head.
- Mechanism: underreaction + limits to arbitrage; kill criteria to include "drift gone or confined to untradeable names in the post-2015 sample."

### GKX ML cross-section (long build, background-friendly)
- Data (Decision B): Chen-Zimmermann open-source characteristics panel joined to CRSP returns; spot-check ~5 characteristics against raw Compustat.
- Models in ascending complexity: OLS-Huber baseline → elastic net → gradient-boosted trees → shallow NNs. Expanding-window train/validate/test exactly as in the paper.
- Deliverables: OOS R², decile long-short performance net of costs, variable-importance stability. This track is a research benchmark and signal source for later combination, not a nimble standalone alpha.

### Backlog
- Dynamic factor timing (Ken French + macro predictors; cheapest data; add when a slot frees).
- LOB / DeepLOB (FI-2010): learning exercise only; explicitly not deployable alpha at retail latency.
- Signal combination layer: only after ≥2 tracks produce surviving signals; combining three unvalidated signals is not a step.

## Workflow, Testing, Failure Handling

- Kristen: Stage-0 approvals, Stage-4 verdicts, memo review. Claude: everything else, run in background sessions.
- Every session ends by rewriting a per-track `STATE.md` (what ran, results, next step, open questions) so gaps or context loss are survivable. No session leaves the repo in an undocumented state.
- Code standards: validate data at ingestion boundaries; deterministic seeds; unit tests on loaders and on the eval harness (a harness bug corrupts every verdict); files under 500 lines; no secrets in the repo (WRDS/Alpaca/Anthropic credentials in env or `~/.config`, gitignored).
- Terminal exports: manual on-campus act by Kristen; ingestion is "drop file in `data/raw/`, loader validates schema and registers it in the lineage manifest."
- Paper trading only, per trading-lab rules. Nothing in this project places real orders.

## Success Criteria

- Each active track reaches Stage 4 with an honest verdict — a well-documented kill is a success.
- At least one signal survives to Stage 5 and its live paper performance is tracked against backtest expectations.
- The vault trading-lab contains the full reasoning trail: hypothesis → protocol → verdict → (if promoted) live divergence log.
