# StatArb Ablation Harness + Per-Signal Outcome Log (Design)

**Date:** 2026-07-07
**Status:** Design approved by Kristen — pending spec review
**Track:** `tracks/statarb` · HYP-005 · backtest-side (complements the Stage-5 paper book)
**Repo:** code in `~/projects/alpha-lab/`; this spec + journal in the vault

**Goal:** Turn the residual-reversion backtest from a single-number producer (Sharpe 2.67) into a
research instrument that answers *which production layers actually improve the strategy* (an ablation
study) and *emits a per-signal outcome log* that later feeds a signal-quality meta-model. The log is
the shared substrate for both, and is schema-compatible with the forward paper book so backward and
forward data concatenate into one training set.

---

## Context

**What already exists** (verified against the repo, 2026-07-07):
- `scripts/statarb_residual_run.py` — the audited backtest: vectorized signal (`rolling_residual` →
  cumulative s-score → `band_positions`), no look-ahead, already toggling **transaction costs**
  (`--cost-bps`) and one **risk filter** (`--long-floor`), plus `--pit`, `--skip`, `--cap`.
- `core/broker/base.py` + `tracks/statarb/paper/{signal,ledger,reconcile,report}.py` — the forward
  paper-book scaffold (separate, already-approved spec: `2026-07-07-paper-book-residual-reversion-design.md`).
- `tracks/pead/events.py::fetch_earnings_yf` — free earnings dates (reused here).
- `core/eval/scorecard.py` — the shared net-of-cost / deflated-Sharpe / subperiods scorecard.

**What is missing — the only real gap:** a **per-signal outcome log**. The backtest emits a daily
net-P&L series and a scorecard; it has no per-trade record (entry features → realized outcome). Both
the ablation table's per-experiment stats (`n_signals`, `win_rate`, `avg_holding`) and any future ML
meta-model are *derived from* this log. So the log is built first.

**Why two windows, not one** (the resolved fork):
- **Ablation → full history (2018→today).** "Does layer X help?" earns trust from many trades across
  regimes (COVID, 2022 selloff, calm 2024). A 2–3-month window is too few trades — a single bad week
  could flip a layer's verdict.
- **ML prototype → recent slice + forward.** The meta-model needs *unbiased labels*, not volume.
  Over a short recent window almost no S&P 500 name delists, so it is ~survivorship-clean; the forward
  paper book extends it with truly survivorship-immune data.
- Same log feeds both — the log is date-tagged, sliced differently per purpose. Conflating the windows
  is the subtle mistake this split avoids.

---

## Decisions

1. **Approach A — extend the vectorized core, do not rewrite it.** Signal + position math stays
   byte-for-byte unchanged (the path that produced the audited 2.67). Layers become pure functions that
   transform the positions matrix; a single `extract_trades()` derives the log from that matrix. The
   rejected alternative (an event-driven day-by-day loop) would reimplement the audited trading loop —
   exactly the parity risk the paper-book spec built a harness to prevent.
2. **Parity gate protects 2.67.** Acceptance criterion: `run_residual(config)` with **all layers off**
   reproduces today's net-P&L series bit-for-bit. A refactor that changes the audited number fails.
3. **Label the road not taken (counterfactual outcomes).** In a backtest the future prices are known,
   so the log records *every* candidate signal (each s-score band-cross) with `entered: true/false`, the
   filters that blocked it, **and the P&L it would have realized if taken.** This lets the ablation say
   "the liquidity filter skipped 40 trades averaging −1.2%" (earned its keep) vs "+0.9%" (hurt). Forward
   paper trading cannot observe this — it only sees trades taken. Backward log = richer counterfactuals;
   forward log = cleaner dead-name labels. Complementary by construction.
4. **Unionable schema.** The per-signal log is a superset-compatible union of the paper book's
   `positions.jsonl` fields (`entry_s`, `entry_bucket`, `close_reason`, `realized_pnl`, `holding_days`)
   plus backtest-only extras. Backward + forward logs concatenate into one training set.
5. **Earnings-only news layer for v1.** No free structured M&A/headline feed exists; the news layer is
   an earnings-blackout. General news/M&A is deferred and documented, not silently assumed.

---

## Architecture

New/changed files (≈5, each one focused job):

```
alpha-lab/
├── tracks/statarb/
│   ├── filters.py     # NEW — composable layers, pure (positions, ctx) -> positions
│   └── trades.py      # NEW — extract_trades() (round-trip + counterfactual log) + trade_stats()
├── scripts/
│   ├── statarb_residual_run.py   # REFACTOR — body -> importable run_residual(config)
│   └── statarb_ablation_run.py   # NEW — sweep named configs, write the comparison table
└── core/data/prices.py           # EXTEND — also fetch volume (dollar-ADV + volume_ratio feature)
```

- **`run_residual(config) -> (net_series, trades_log)`** — the single audited code path. `statarb_residual_run.py`
  becomes a thin CLI over it; `statarb_ablation_run.py` calls it once per config. Signal/position math
  unchanged; layers applied as post-signal position transforms; log extracted from the final matrix.
- **`filters.py`** — one pure function per layer (below). Each takes the positions matrix + a context
  bundle (returns, volume, sector map, earnings dates) and returns a transformed matrix. Order is fixed
  and explicit in `run_residual`. Pure functions → independently unit-testable, no hidden state.
- **`trades.py`** — `extract_trades()` scans each ticker column of the positions matrix for entry→exit
  runs, computes entry features + realized (and counterfactual) P&L + `close_reason`, and emits log rows.
  `trade_stats()` rolls a log up to per-experiment summary stats.

---

## The layers (concrete definitions + defaults; all tunable)

| Layer | Definition | Default | Toggle |
| ----- | ---------- | ------- | ------ |
| **costs** | Per-side bps charged on turnover (stock + ETF leg), as today. | `--cost-bps` (baseline run uses 0; "on" = 5 wide / 10 large-cap) | already exists |
| **liquidity** | Drop names whose trailing 20-day **median dollar volume** < threshold at entry (illiquid → not practically executable). | `$5M` ADV floor | `--liquidity-adv` (0 = off) |
| **sector_cap** | Cap **net exposure per sector** and **single-name weight**, then renormalize to stay dollar-neutral. Prevents a "12 regional banks" concentrated bet the equal-weight book would otherwise take. | sector net ≤ 20% of gross; single name ≤ 2% of gross | `--sector-cap` / `--name-cap` (0 = off) |
| **earnings_blackout** | Block **new** entries within a window around a name's earnings date (event risk ≠ mean-reversion). Existing positions held normally in v1. | window `[-2, +1]` trading days | `--earnings-blackout` (off by default) |

Features recorded per signal for later ML (cheap to compute here): `residual`, `s_score`, `sector`,
`volatility` (rolling std of returns), `volume_ratio` (entry volume / 20-day avg), `earnings_next`
(bool, earnings within lookahead). Costs/liquidity/sector/earnings each independently on/off, so the
ablation runner can sweep the cumulative stack **or** any combination.

---

## Per-signal outcome log (the substrate)

One row per candidate signal (band-cross), written as date-tagged JSONL under
`artifacts/statarb/signal_log/` (gitignored). Union-compatible with the paper book's `positions.jsonl`.

| Field | Meaning |
| ----- | ------- |
| `signal_id`, `ticker`, `entry_date` | identity |
| `entry_s`, `entry_bucket`, `residual` | signal at entry (`bucket` ∈ short / long_shallow / long_deep / long_verydeep — same boundaries as the paper book) |
| `sector`, `sector_etf`, `volatility`, `volume_ratio`, `earnings_next` | features |
| `entered` (bool), `filters_blocked` (list) | decision + *why* skipped (empty if entered) |
| `exit_date`, `holding_days`, `close_reason` | exit; `close_reason` ∈ `{reversion_exit, band_flip, floor_stop, window_end}` |
| `realized_pnl`, `return` | outcome **if entered** |
| `counterfactual_pnl`, `counterfactual_return` | outcome the trade **would** have had if taken (populated for skipped signals too) |
| `success` (bool) | label = realized (or counterfactual) net return > 0 over the hold |

**Honest schema boundary:** backtest `close_reason` lacks `halt / delisted / corporate_action /
gap_stop` — those are forward-only (dead names have no free price history). That gap is *precisely* why
forward data is needed for deep-dip labels; the shared schema means the two logs concatenate cleanly,
the forward one simply carrying close reasons the backward one cannot.

---

## Ablation output

One table per sweep, cumulative stack by default (each row adds one layer), written as markdown +
a parquet of the raw rows under `artifacts/statarb/ablation/`. Stats come from `trade_stats()` over the
log; risk metrics from the shared `scorecard`.

| config | n_signals | win % | avg hold | ann. | Sharpe | max DD | deflated |
| ------ | --------- | ----- | -------- | ---- | ------ | ------ | -------- |
| baseline (signal only, costs off) | … | … | … | … | > 2.67 | … | … |
| + costs | … | … | … | … | ~2.67 | … | … |
| + liquidity | | | | | | | |
| + sector cap | | | | | | | |
| + earnings blackout | | | | | | | |

Cells are runtime output (format shown, not fixed values). **Second parity anchor:** the ablation runs
on the canonical universe (S&P 500, `skip=1`), so the `+costs` row at 10 bps must reproduce the audited
~2.67 — if it doesn't, the harness has drifted from the run that produced the headline number. The
costs-*off* baseline is therefore *above* 2.67 by construction.

Each layer's row also reports the **counterfactual delta** — how the trades it removed *would* have
done — so "helped" vs "hurt" is evidenced, not asserted.

---

## Data flow (one ablation run)

1. Load cached wide price panel + sector ETFs (reuse existing cache); fetch/attach **volume**.
2. Compute residuals, s-scores, base positions once (audited path, unchanged).
3. For each named config: apply the config's layer transforms to the positions matrix → `run_residual`
   → `(net_series, trades_log)`.
4. `extract_trades` → per-signal log (with counterfactuals for skipped signals); write JSONL.
5. `trade_stats` + `scorecard` → one row; assemble the table (markdown + parquet).

---

## Testing

- **Parity gate (load-bearing):** `run_residual` all-off reproduces the current `statarb_residual_run.py`
  net series bit-for-bit. This is the "didn't break 2.67" test.
- **Filters (pure, one each):** `liquidity` drops exactly the sub-threshold names; `sector_cap` enforces
  the bound and preserves dollar-neutrality; `earnings_blackout` blocks entries inside the window and
  only there.
- **`extract_trades`:** synthetic positions matrix with known round-trips → asserts entry/exit dates,
  `holding_days`, `realized_pnl` sign, and `close_reason` classification; a skipped-signal fixture
  asserts `counterfactual_pnl` is populated and `realized_pnl` is null.
- **Ablation smoke test:** tiny universe, short window → table assembles, columns present, rows ordered.

---

## Scope / YAGNI (explicitly cut)

- **No ML in this build.** The log is built and validated here; the meta-model (logistic → random forest
  → XGBoost, walk-forward) is Phase 3, on the recent-clean slice + forward data.
- **Earnings-only** news layer — general news / M&A deferred (no free structured feed).
- **Equal-weight book preserved** — sector/name caps constrain it, but no Ledoit-Wolf / optimizer (that
  is a separate track item, as in the paper-book spec).
- **No new dependencies** — yfinance volume + existing pead earnings + stdlib.
- **Backtest only** — the forward paper book is its own spec; this one just guarantees schema union.

---

## Phasing (confirmed)

1. **This build:** per-signal outcome log substrate + ablation harness.
2. Full-history ablation table (the research artifact: which layers matter).
3. Recent-window ML prototype (signal-quality meta-model) on the date-sliced log.
4. Forward paper book continuously grows the training set (survivorship-immune labels).

---

## Open item most worth review

The **counterfactual labeling** (Decision 3). It is what makes the backtest log uniquely valuable
(forward can't see skipped-trade outcomes) and what turns the ablation from "Sharpe went up" into
"here are the specific trades each layer removed and what they would have done." Confirm this is worth
the extra bookkeeping in `extract_trades` — it is the one place this design does more than the minimum,
and deliberately so.
