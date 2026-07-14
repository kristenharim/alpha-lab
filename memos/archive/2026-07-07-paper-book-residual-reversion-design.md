# Paper Book — Residual Reversion Forward Test (Design)

**Date:** 2026-07-07
**Status:** Approved by Kristen *with redirects* (this revision folds all five in) — pending spec review
**Track:** `tracks/statarb` · HYP-005 · Stage 5 (paper trading)
**Repo:** code in `~/projects/alpha-lab/`; this spec + journal in the vault

**Goal:** Forward-trade the Avellaneda-Lee residual signal on the live S&P 500 via Alpaca paper to
resolve one number: is the true survivorship-free Sharpe **~1.7 (robust core)** or **~2.5 (PIT upper
bound)**? The forward test is survivorship-immune by construction, so it settles what no free-data
backtest can.

---

## Context

- **The bracket (from the backtest audits).** Survivor baseline Sharpe **2.67** → point-in-time
  membership **2.50** (upper bound; 120 of 505 2018 members are delisted with no free price data) →
  **~1.7 robust core** after removing all deep-dip (s < −2) longs. The gap between 1.7 and 2.5 is
  *entirely* the long-side deep-dip premium — the trades most analogous to the missing delisted names.
- **Why forward paper is decisive.** The backtest's blind spot is delisted names' losing longs. Live,
  you hold *current* members forward; if a name you are long halts / craters / is acquired, the broker
  books the real loss — no omission. The live deep-dip bucket therefore contains exactly the "dead-name"
  outcomes the backtest could not see.
- **Why not just fix the backtest.** Point-in-time *prices* (not just membership) need CRSP/WRDS.
  Kristen's WRDS access is on-campus manual export, download-capped — usable for building a historical
  dataset, **not a live pipeline**. The paper book is the practical decisive test and needs no WRDS.
- **Data + workflow.** Alpaca is the sanctioned live-capable retail API (terminal feeds are export-only).
  Runs as a nightly background session; Kristen approves the Stage-5 gate and the final kill/promote call,
  Claude runs the loop and writeups. Consistent with the LLM-sentiment track, where the live forward
  paper-trade is already the primary evidence.

---

## Decisions (folding in the five review redirects)

1. **Resolver = one real order stream + derived floored series.** Submit the *full* signal to Alpaca
   paper; compute a *floored* PnL series from the same fills by zeroing deep-dip long contributions.
   `full − floored` isolates the **long-side deep-dip premium** — named precisely, because it does
   **not** capture short-side survivorship (an acquisition gap against a short lands in *both* books and
   does not difference out). *[redirect 1b]*
2. **Unify on Alpaca market data for BOTH signal and execution.** One price source, one corporate-action
   model. Computing s-scores off yfinance while filling on Alpaca would let cross-vendor split/dividend
   and delisting conventions contaminate the dead-name bookkeeping — the one thing the experiment turns
   on. *[redirect 3]*
3. **Pre-registered resolution anchored to the backtest premium's own CI**, with a fast event-driven
   primary readout and an explicit inconclusive-case timeout. *[redirect 2]* — see next section.
4. **Two non-negotiables:** a source-agnostic **signal-parity harness** *[redirect A]* and explicit
   **terminal-event disambiguation** in reconcile *[redirect B]*. A silent bug in either corrupts the
   answer rather than merely adding noise.
5. **Log the short-side borrow slot now** even though paper won't populate it, so the eventual
   paper-vs-live reconciliation has a baseline. *[redirect 1a]*

---

## The question, quantified, and the resolution rule

**Backtest premium (full − floored daily spread), measured on the artifacts:**

| Universe | Full Sharpe | Floored Sharpe | **Premium spread Sharpe** | 95% CI | Ann. |
| -------- | ----------- | -------------- | ------------------------- | ------ | ---- |
| survivor | 2.67 | 1.86 | **2.98** | [2.28, 3.68] | 4.68% |
| PIT      | 2.50 | 1.69 | **3.27** | [2.56, 3.97] | 4.36% |

The premium is a low-return (~4.4%/yr), high-consistency stream — hence the high Sharpe. (The bare
"~0.8" from the first design was the *difference of book Sharpes*, not the premium's own Sharpe — a
different and wrong quantity. This table replaces it.)

**Two hypotheses:**
- **Benign** (survivorship was not inflating the edge) → live premium ≈ backtest, its CI overlaps the
  PIT anchor **[2.56, 3.97]** → true Sharpe ≈ **2.5**.
- **Ate it** (survivorship inflated the edge) → live premium spread Sharpe ≈ **0** → true ≈ **1.7**.

**Power reality (why the aggregate CI alone will not resolve fast).** Premium SE over the 2015-day
backtest is 0.36 (Lo 2002). Scaled to 3 months (~63 trading days) SE ≈ 0.36·√(2015/63) ≈ **2.0**, so a
quarter's live premium CI is ≈ ±4 — it straddles both 0 and 3 and resolves nothing. The aggregate CI
needs **~12 months** to tighten enough to exclude a hypothesis. Therefore the resolver is layered:

- **Primary — dead-name drag ledger (event-driven, fast).** Realized PnL on deep-dip longs closed via
  `halt / delisted / corporate_action / gap_stop`. This is *direct* evidence of the mechanism: even a
  handful of deep-dip longs that delist at a loss demonstrates the survivorship channel the backtest
  omitted. Reported continuously (count + summed drag), not gated on aggregate convergence.
- **Secondary — premium-Sharpe CI (aggregate, slow).** Live `full − floored` spread Sharpe with a
  rolling 95% CI, horizon **12 months**.
- **Pre-registered timeout.** At 12 months, if the premium CI excludes **neither** 0 **nor** the PIT
  backtest anchor's lower bound (~2.56), **adopt the 1.7 core as the planning number and stop.** The
  conservative default is chosen now, while honest, not later. *[redirect 2b]*

**What this resolver does and does not settle.** It settles the *long-side deep-dip* premium — the exact
quantity separating 1.7 and 2.5. It does not, by the floored spread alone, settle short-side survivorship
(borrow drag, short-squeeze/acquisition gaps); those are captured in `positions.jsonl` and the borrow
slot for separate inspection, and are flagged as out of scope for the headline resolver.

---

## Architecture

Five isolated units, each one job, each independently testable. New package `tracks/statarb/paper/`
plus a thin shared broker adapter in `core/`.

```
alpha-lab/
├── core/
│   └── broker/
│       ├── base.py          # Broker interface (submit_targets, positions, fills, asset_status)
│       └── alpaca.py        # alpaca-py paper adapter; paper base-URL hardcoded + assert-not-live
├── tracks/statarb/paper/
│   ├── signal.py            # target book from rolling_residual + band_positions (REUSED, unchanged)
│   ├── ledger.py            # append-only JSONL writers (4 logs)
│   ├── reconcile.py         # intended-vs-actual diff + terminal-event disambiguation  ← highest risk
│   ├── report.py            # bracket monitor: full/floored Sharpe, premium CI, dead-name drag
│   └── parity.py            # signal-parity harness (frozen panel → backtest book, bit-for-bit)
├── scripts/
│   └── paper_book_run.py    # nightly driver; --dry-run uses the fake broker (no network)
└── artifacts/statarb/paper/ # gitignored — the 4 JSONL ledgers + daily scorecard md
```

1. **signal** — given a daily price panel + sector ETFs, computes today's s-scores and target book using
   the *exact* `rolling_residual` + `band_positions` from the backtest. No reimplementation → parity by
   construction (verified by unit 5). Output columns: `ticker, s_score, bucket, beta, residual,
   sector_etf, target_weight`. Buckets: `short` (s ≥ +1.25), `long_shallow` (−2 ≤ s ≤ −1.25),
   `long_deep` (−3 ≤ s < −2), `long_verydeep` (s < −3).
2. **broker** — thin adapter behind `base.Broker` so tests and `--dry-run` use a `FakeBroker`. The
   Alpaca impl hardcodes the paper endpoint and asserts at runtime it is not the live URL.
3. **ledger** — the four append-only JSONL logs below.
4. **reconcile** — diffs the target book against Alpaca's actual positions/fills and books terminal
   events. The disambiguation rules are specified separately (highest-risk unit).
5. **report** — reads the ledgers and computes, via the identical `core/eval/scorecard.py`: live full
   Sharpe, derived floored Sharpe, `premium = full − floored` with rolling CI, and the dead-name drag.

---

## The four ledgers (the logging spec)

Append-only JSONL, one directory under `artifacts/statarb/paper/`, following the `registry.register`
ethos (one immutable row per event). Every unit of the answer reconstructs from these.

| Ledger | One row per | Fields |
| ------ | ----------- | ------ |
| **`targets.jsonl`** | (date, ticker) in the intended book | `date, ticker, s_score, bucket, beta, residual, sector_etf, target_weight` |
| **`fills.jsonl`** | Alpaca fill | `ts, ticker, side, qty, target_price, fill_price, slippage_bps, commission, `**`borrow_bps, locate_status`** |
| **`positions.jsonl`** | position **open** and **close** | open: `open_date, ticker, side, qty, entry_price, entry_s, entry_bucket` · close: `close_date, close_price, `**`close_reason`**`, realized_pnl, holding_days` |
| **`daily_nav.jsonl`** | day | `date, gross, cost, net, nav, n_pos, net_by_bucket{short,long_shallow,long_deep,long_verydeep}, `**`floored_net`** |

- **`close_reason` ∈ `{reversion_exit, band_flip, halt, delisted, corporate_action, gap_stop,
  quarantine, still_open}`** — the survivorship sensor. `halt/delisted/corporate_action/gap_stop` are
  the live dead-name events; `quarantine` is the safeguard state (below).
- **`borrow_bps` / `locate_status`** — null under Alpaca paper, but the slot exists so the paper-vs-live
  baseline is there when it matters; short-side borrow drag is a top reason a 1.7 backtest compresses
  live.
- **`floored_net`** (derived, unambiguous) = `net − net_by_bucket[long_deep] − net_by_bucket[long_verydeep]`
  — i.e. the same day's book with the two deep-dip long buckets removed, using the per-bucket marks
  already in this row. Same fills, same shocks → `net − floored_net` is the low-variance long-side
  deep-dip premium. A deep-dip long that delists at a loss lowers `net` (and thus the live premium)
  directly, so the dead-name ledger and the premium series are two views of one underlying signal —
  event-level (fast, interpretable) and aggregate (slow, statistical) — not independent tests.

---

## Reconcile — terminal-event disambiguation (highest-risk unit)  *[redirect B]*

This unit is the sensor for the effect under study. A false `delisted` close injects a fake dead-name
loss and *manufactures* the survivorship signal — biasing the answer toward the outcome we predisposed
to believe. Rules are explicit and conservative:

| Situation | Detection | Action |
| --------- | --------- | ------ |
| Transient halt, resumes | non-tradable, still an index member, resumes ≤ **K=5** trading days | **halt** — mark-to-last, do **not** book a close; keep the position |
| Genuine delisting | non-tradable + removed from index + no successor security | **delisted** — book close at official delist / last valid mark |
| Symbol change / spinoff w/ successor | corporate-action feed gives successor symbol | **corporate_action (follow)** — migrate the position to the new symbol; **not** a dead-name event |
| Cash acquisition / merger | corporate-action feed, cash terms | **corporate_action (close)** — book close at deal price |
| Overnight gap beyond stop | held long, open gaps below the deep-dip floor | **gap_stop** — book close at open |
| Non-tradable, cause unknown | none of the above resolves within the run | **quarantine** — mark-to-last, do **not** book as delisted, flag for manual review, re-evaluate next run |

`quarantine` is the guardrail: ambiguity never auto-books a dead-name loss. Every `delisted` and
`corporate_action(close)` row is also written to a human-readable review line so mis-bookings are
caught before they enter the resolver.

---

## Signal-parity harness (non-negotiable)  *[redirect A]*

"Same function" does not guarantee "same numbers" once the signal is fed a live, growing panel instead
of the cached backtest panel. Look-ahead can enter through *when* today's close is available, timezone /
session boundaries, and the rolling window's warm-up on a growing panel.

- **Test:** on any historical date `d`, `paper/signal.py` fed a panel frozen at `d` must reproduce the
  backtest's target book for `d` **bit-for-bit** (same tickers, same positions, same buckets).
- **Source-agnostic:** the harness feeds *one frozen panel* to both the backtest position logic and the
  live signal module. It tests the code path (plumbing, timing, warm-up), independent of whether live
  ultimately runs on Alpaca data and the historical backtest ran on yfinance — that vendor boundary is a
  separate, acknowledged axis, and the forward live-vs-backtest comparison is distributional (against
  the pre-registered Sharpe/premium expectations), not path-wise.
- **Gate:** the parity test must pass in CI before any live run is permitted. A silent parity break makes
  every live-vs-backtest comparison meaningless.

---

## Data flow (one nightly run)

1. **Fetch** today's Alpaca daily bars for the current S&P 500 members + sector ETFs.
2. **Reconcile first:** for every held name, resolve tradability via the disambiguation table; book any
   terminal event (`positions.jsonl` close + `daily_nav` mark) **before** placing new orders.
3. **Compute** target book (`signal.py`); write `targets.jsonl`.
4. **Submit** the diff (target − current) to Alpaca paper; write `fills.jsonl`.
5. **Mark** NAV, per-bucket net, and the derived `floored_net`; write `daily_nav.jsonl`.
6. **Report:** update the bracket monitor (dead-name drag primary; premium CI secondary); write the
   scorecard md.

---

## Config & safety

- Alpaca **paper** endpoint hardcoded + runtime assert it is not the live URL. Keys via env
  (`ALPACA_API_KEY_ID`, `ALPACA_API_SECRET_KEY`); never committed.
- $1M notional paper book, dollar-neutral, equal-weight across active names (matches backtest weighting).
- **Idempotent / run-stamped:** re-running the same date places no duplicate orders.
- `--dry-run` uses `FakeBroker` — network-free, honoring the repo rule that tests never touch the network.
- **Feed caveat:** Alpaca free data is IEX (thin) vs paid SIP; for EOD daily bars this is acceptable, and
  unifying signal+execution on it is worth more than the marginal consolidated-close accuracy. Documented,
  not silently assumed.
- New optional dependency: `alpaca-py`.

---

## Testing

- **Parity harness** (the critical one): frozen panel → backtest book, bit-for-bit, on sampled dates.
- **Bucketing:** s-score → bucket boundaries, including the −2 and −3 edges.
- **Derived floored identity:** on a synthetic `daily_nav`, `floored_net` == `net` minus deep-bucket
  contributions (assert).
- **Fake-broker dry-run:** full nightly loop submits + reconciles with no network.
- **Terminal-event disambiguation fixtures:** halt-resumes (no close), delist (close booked),
  symbol-change (position migrated, no dead-name event), unknown (quarantine, no close). This is where a
  bug biases the answer, so it gets the most fixtures.
- **Borrow slot null-safe:** `fills.jsonl` writes with `borrow_bps=null` under paper without error.

---

## Scope / YAGNI (explicitly cut)

- No real-money path, ever.
- EOD daily only — no intraday.
- Equal-weight book — no Ledoit-Wolf / portfolio optimizer (separate track item).
- No dashboard — the monitor prints and writes a scorecard md the vault can consume later.
- Residual signal only — not a multi-strategy harness.
- No intraday borrow modeling — just log the slot for the future paper-vs-live baseline.

---

## Open item most worth review

The **power/horizon reframe** in the resolution section: the aggregate premium CI needs ~12 months, so
the primary readout is the event-driven dead-name drag ledger and the pre-registered fallback is "adopt
1.7 and stop at 12 months if still inconclusive." That is the load-bearing honesty choice — confirm it
reads as *decisive enough to be worth running* rather than a hedge.
