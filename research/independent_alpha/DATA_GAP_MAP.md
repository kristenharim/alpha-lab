# DATA_GAP_MAP.md — Data & Point-in-Time Audit (Agent 3)

Auditor: Agent 3 (Data & PIT), 2026-07-10. Method: inventoried `data/` and `artifacts/`,
read every `core/data/*.py` loader + the collection scripts, opened parquet schemas +
date ranges, and cross-checked against `data/manifest*.jsonl`, `CANONICAL_STATE.md`, and
`memos/alpha-roadmap-2026-07.md`. **Where a loader docstring and the data disagree, the
data wins.** No history was fabricated; every "FORWARD-COLLECTABLE" item is one the repo
can only accrue going forward, not backfill honestly.

Classification legend:
- **TESTABLE NOW** — enough clean history on disk to run an IC/backtest today.
- **FORWARD-COLLECTABLE** — a free feed exists and a collector is (or can be) wired, but
  only forward-in-time; no honest historical backfill.
- **BLOCKED-WITHOUT-VENDOR** — needs a paid/entitled source (WRDS/CRSP, options, estimates).
- **UNSAFE** — present but carries leakage or survivorship that makes naive use misleading.

Credentials on hand: EODHD token (price tier — calendar/fundamentals endpoints 403 at this
plan), Alpaca **paper** keys (news + prices + `easy_to_borrow`/`shortable` flags), Finnhub
free (`~/.config/rimrimos/finnhub.env`, 60/min). **No WRDS/CRSP, no Polygon/Tiingo, no
options or estimate vendor.**

---

## 1. Inventory — what actually exists on disk

### data/raw/ (prices, membership, fundamentals, news)
| file | shape | span | source | what it is |
|---|---|---|---|---|
| `wide_daily_px.parquet` | 4152 × 1503 | 2010-01→2026-07 | yfinance | split/div-adjusted daily **close**, S&P composite 1500 |
| `monthly_px_wide.parquet` | 199 × 1495 | 2010→2026 | yfinance | monthly adj close |
| `daily_px_statarb_wide.parquet` | 2137 × 1103 | 2018→2026 | yfinance | daily adj close, statarb universe |
| `daily_vol_statarb.parquet` | 2138 × 503 | 2018→2026 | yfinance | **share volume** (liquidity input) |
| `sp500_pit.parquet` | 2712 × 2 | 1996→2026 | fja05680 | S&P **500** PIT membership change-log (`date, members[]`) |
| `sp_composite_named.parquet` | 1506 × 4 | current | Wikipedia | current 1500 constituents + sector + name (survivor-biased) |
| `edgar_assets_wide.parquet` | 888 × 1495 | 2006→2026 | EDGAR | total **assets** (asset-growth factor) |
| `value_ni / value_equity / value_shares` | ~1470 names | 1998/99→2026 | EDGAR | net income, book equity, shares outstanding |
| `statarb_earnings.parquet` | 23893 × 4 | 2007→2026 | yfinance | earnings date + `eps_actual` + `eps_estimate` (**current-vintage, not PIT**) |
| `cz_portfolios.parquet` | 1.23M × 7 | 1926→2024 | OpenAssetPricing | Chen-Zimmermann long-short **factor-portfolio returns** (not stock-level) |
| `news.parquet` | 54348 × 4 | **2025-09→2026-07** | Alpaca/Benzinga | headlines (date, ticker, company, headline) |

### research/hunt2026/ (the richest single asset)
| file | shape | span | fields | note |
|---|---|---|---|---|
| `panel_2005.parquet` | 5413 × 6920 | 2005→2026 | `open, close, volume, member` × 1730 names | **has an embedded PIT `member` mask** |
| `train.parquet` | 2897 × 6920 | 2014→**2025-07-10** | same | blind-holdout train cut (frozen) |

### artifacts/ + data/earnings_fwd/ (derived + forward collectors)
| file | span | what it is |
|---|---|---|
| `earnings_fwd/events.jsonl` | started 2026-07-10 (8 rows, 2 names) | Finnhub PIT earnings-surprise, `point_in_time` flag |
| `earnings_fwd/reactions.jsonl` | 1 row | first-session open/close reaction snapshot |
| `artifacts/pead/events.parquet` | 2024→2026 (530) | SUE events for PEAD study |
| `artifacts/gkx/predictions.parquet` | 1982→2024 (504) | GKX ML monthly return predictions (factor-portfolio level) |

---

## 2. Source-by-source audit

### 2.1 Price / volume — **TESTABLE NOW**
- **Availability:** daily adj close for ~1500 names (2010→), volume for 503 (2018→), a
  2005→2026 OHLCV panel (`panel_2005`).
- **Depth:** 20yr on the panel; 16yr on the wide close matrix.
- **PIT quality:** GOOD for prices (a close is a close). Adjusted with `auto_adjust=True`
  so dividends/splits are baked in — see corporate actions below.
- **Survivorship:** the **wide/statarb close matrices are survivor-biased** (Wikipedia
  current members). The `panel_2005.member` mask fixes *inclusion* look-ahead but not
  *delisting* — dead tickers have no yfinance history to include (see §2.4).
- **Leakage:** low. Engine applies a one-day lag; opens are same-day-tradeable.
- **Free.** Acquisition value: n/a (have it). Unlocks: everything price-based (momentum,
  reversal, vol-management — all already built on this).

### 2.2 Opens / closes (intraday proxy) — **TESTABLE NOW (with caveats)**
- `panel_2005` and `train` carry **open + close**; `reactions.jsonl` snaps earnings-session
  open/close. Enables open-to-close vs close-to-close split, overnight-gap studies, and
  execution-at-open assumptions.
- **PIT/quality caveat:** yfinance opens are the weak link — occasionally the prior-close
  echo or an unadjusted print. Fine for signal research, **not** for execution-alpha claims.
- Free. Unlocks: gap-reversal, overnight-return factor, PEAD reaction timing.

### 2.3 Corporate actions — **UNSAFE (implicit only)**
- No explicit split/dividend/spinoff table exists. Adjustment is **baked into** yfinance
  `auto_adjust`. That silently *back-adjusts* the whole history on every new split, so a
  cached matrix pulled at different times can disagree; and total-return vs price-return is
  not separable.
- **Leakage risk:** none for point-in-time signals, but dividend-yield / total-return
  factors cannot be built cleanly, and any study needing the *unadjusted* print (e.g. price
  level filters, penny-stock screens) is contaminated.
- Fix requires a corporate-actions feed (EODHD has one at a higher tier; Alpaca corporate
  actions API is free-ish). Classify the *clean-CA-table* need as BLOCKED-WITHOUT-VENDOR
  at the current EODHD plan.

### 2.4 Survivorship / delisting — **UNSAFE (known, unfixed) → biggest TRUTH gap**
- **State:** `universe.py` is explicit — current-membership universes are survivor-biased;
  `sp500_pit.parquet` + `panel_2005.member` fix S&P 500 *inclusion* only. Delisted/acquired/
  failed names are simply **absent** (no yfinance prices), so reversal/momentum backtests
  on the 400/600 sleeves over-state returns by an unknown, positive amount.
- **PIT quality:** membership PIT is good for **S&P 500 only**. S&P 400/600 membership is
  **current-only** (Wikipedia) — not PIT at all.
- **Fix path (free, in roadmap):** iShares dated-holdings download (IJH/IJR) reconstructs
  400/600 membership back to ~2007; a −30% delisting-return penalty (Shumway 1997) bounds
  the bias. True fix = CRSP delisting returns (BLOCKED-WITHOUT-VENDOR / WRDS).
- Acquisition value: **HIGH** — it doesn't add alpha, it tells you which existing alpha is
  real. Gates whether the small-cap reversal edge in the roadmap is deployable.

### 2.5 Point-in-time S&P membership — **TESTABLE NOW (500) / partial**
- `sp500_pit.parquet` (fja05680, 1996→2026, 2712 snapshots) + `membership_mask()` in
  `universe.py` give clean daily PIT 500 membership. `panel_2005` bakes it into a `member`
  column already consumed by `earnings_collect.sp500_members()`.
- **Gap:** 400/600 have no PIT layer (see §2.4). Free.

### 2.6 Earnings timestamps — **mixed: statarb file UNSAFE, fwd collector FORWARD-COLLECTABLE**
- `statarb_earnings.parquet` (2007→2026, 23.9k rows) has report dates + actual/estimate,
  **but the estimate is the current yfinance vintage** — revised after the fact. Using its
  `eps_estimate` as an as-of-date consensus is **look-ahead**. Report *dates* are usable;
  the surprise is not PIT.
- `earnings_collect.py` (Finnhub) is the **honest** path: it flags `point_in_time=True`
  only for events it watched go actual inside the pull window, and pre-registration
  (`exp-ic-earnings-fwd-2026-07-10.md`) *excludes* the stale backfill from scoring. Today:
  8 events, 2 names — **accumulating, n≫threshold(300) is months away**.

### 2.7 EPS / revenue surprise — **EPS FORWARD-COLLECTABLE, revenue BLOCKED**
- EPS surprise: forward via Finnhub (`surprise`, `surprise_pct` already in `events.jsonl`).
  Historical PIT EPS surprise = BLOCKED (no vintage-dated consensus source free).
- **Revenue surprise: none, no free PIT source.** BLOCKED-WITHOUT-VENDOR.

### 2.8 Analyst estimates / revisions — **BLOCKED-WITHOUT-VENDOR**
- Nothing on disk. Only a single-vintage consensus point (yfinance/Finnhub); **no revision
  history, no as-of-date consensus, no up/down-grade events.** The revisions factor (one of
  the most robust in the literature) is un-testable without I/B/E/S (WRDS) or a paid feed.
- Forward-collectable in principle (snapshot consensus nightly) but that's a multi-quarter
  build with no backfill.

### 2.9 Coverage / dispersion — **BLOCKED-WITHOUT-VENDOR**
- Requires per-analyst estimates to compute # covering + dispersion. None available free.

### 2.10 Fundamentals — **TESTABLE NOW but thin**
- EDGAR-sourced: **assets, net income, book equity, shares** only (2006/1998→2026).
  Timestamped by filing so reasonably PIT-safe at monthly granularity (the loaders lag 6mo).
- **Gap:** no margins, cash flow, debt, capex, R&D — so quality/profitability factors
  (gross-profitability, accruals, F-score) can't be built. Extending EDGAR pulls to more
  XBRL tags is free work, not a vendor purchase → the *richer-fundamentals* need is
  FORWARD/BUILDABLE, not blocked.

### 2.11 Short interest / borrow — **historical BLOCKED-free-partial, live FORWARD-COLLECTABLE**
- **None on disk.** FINRA publishes bi-monthly short interest **free** (historical,
  downloadable) — that's TESTABLE-NOW-after-a-pull, not blocked. Borrow fee / rebate is
  vendor-only (S3, Markit) = BLOCKED. Alpaca `easy_to_borrow`/`shortable` flags are free but
  **live-only** (no history) = FORWARD-COLLECTABLE.
- Value: the long-short books currently charge **zero** short cost — modeling it converts an
  unknown into a bounded drag and removes a live dollar-neutrality failure mode (roadmap
  proposal). Honesty > alpha.

### 2.12 Options-implied — **BLOCKED-WITHOUT-VENDOR**
- No IV, no put/call, no skew, no surface. yfinance option chains are current-snapshot only
  (no history, unreliable). Any vol-risk-premium refinement beyond the SVXY/VIX ETF proxies
  already in the books needs a paid options vendor (ORATS, OptionMetrics).

### 2.13 Macro / rates — **UNSAFE-by-absence → FORWARD/BUILDABLE (free)**
- **No VIX file, no treasury curve, no CPI/FF on disk** despite VIX-conditioning appearing
  in the roadmap and vol-books. Currently proxied by ETF prices in the panel (SVXY, GLD).
- FRED (rates, CPI, FF) and `^VIX` via yfinance are **free and deep** (VIX to 1990) — this
  is the cheapest real gap to close. Classify: TESTABLE-NOW-after-a-pull.

### 2.14 Borrow / liquidity — **liquidity TESTABLE NOW, borrow see §2.11**
- Liquidity: `rolling_dollar_adv()` (price×volume) already computes trailing dollar ADV
  from data on hand. Sufficient for turnover/impact gating.

### 2.15 Auction / intraday / tick — **BLOCKED-WITHOUT-VENDOR**
- Daily open/close only. No minute bars, no auction (open/close cross) prices, no tick.
  Execution-alpha claims (the 4th alpha type) are **not measurable** with current data —
  important guardrail: no book here can claim execution alpha on this data.

### 2.16 News / sentiment — **FORWARD-COLLECTABLE (short history now)**
- `news.parquet`: Alpaca/Benzinga headlines, 54k rows, **only 2025-09→2026-07 (~10 months)**.
  The loader docstring claims history to ~2015; only ~10 months was actually pulled. Free to
  extend backward via Alpaca, but Benzinga depth/quality pre-2020 is thin.

---

## 3. Classification summary

| source | class | free? | PIT quality | survivorship |
|---|---|---|---|---|
| price/volume | TESTABLE NOW | yes | good | biased (panel `member` partial fix) |
| opens/closes | TESTABLE NOW | yes | fair (yfinance opens) | as above |
| corporate actions | UNSAFE (implicit) | tier-gated | n/a | n/a |
| delisting/survivorship | UNSAFE (unfixed) | free-partial (iShares) / CRSP paid | — | **the core gap** |
| PIT S&P 500 membership | TESTABLE NOW | yes | good | fixes inclusion only |
| PIT S&P 400/600 membership | BLOCKED (free-partial) | iShares free | none today | none |
| earnings dates | TESTABLE NOW | yes | dates ok | — |
| EPS surprise (PIT) | FORWARD-COLLECTABLE | Finnhub free | forward-only | — |
| revenue surprise | BLOCKED-WITHOUT-VENDOR | no | — | — |
| analyst estimates/revisions | BLOCKED-WITHOUT-VENDOR | no | — | — |
| coverage/dispersion | BLOCKED-WITHOUT-VENDOR | no | — | — |
| fundamentals (assets/NI/eq/shares) | TESTABLE NOW (thin) | yes (EDGAR) | filing-timestamped | — |
| richer fundamentals | FORWARD/BUILDABLE | yes (EDGAR XBRL) | ok | — |
| short interest (FINRA) | TESTABLE NOW after pull | yes | bi-monthly lag | — |
| borrow fee | BLOCKED-WITHOUT-VENDOR | no | — | — |
| borrow flags (live) | FORWARD-COLLECTABLE | yes (Alpaca) | live-only | — |
| options-implied | BLOCKED-WITHOUT-VENDOR | no | — | — |
| macro/rates/VIX | TESTABLE NOW after pull | yes (FRED/yfinance) | good | — |
| liquidity (dollar ADV) | TESTABLE NOW | yes | good | — |
| auction/intraday/tick | BLOCKED-WITHOUT-VENDOR | no | — | — |
| news/sentiment | FORWARD-COLLECTABLE | yes (Alpaca) | 10mo history now | — |

**Leakage watchlist (do not ship on these naively):** `statarb_earnings.eps_estimate`
(revised vintage), yfinance opens (echo prints), any 400/600 backtest (survivorship),
corporate-action-adjusted matrices re-pulled at different dates (silent re-adjustment).

---

## 4. Top-3 highest-value data acquisitions

1. **PIT S&P 400/600 membership + a delisting bound (iShares dated holdings, FREE).**
   The single biggest *truth* gap: it decides whether the small-cap reversal edge the
   roadmap prizes is real or a survivorship artifact. Reconstruct IJH/IJR holdings back to
   ~2007, add a −30% delisting-return penalty (Shumway 1997). Zero alpha added, but it
   validates or kills a whole deployable sleeve and quotes a bound on every deflated-Sharpe
   claim. Cost: engineering only.

2. **FINRA bi-monthly short interest (historical, FREE) + Alpaca borrow flags (live).**
   The long-short books currently charge **zero** short cost — an unmodeled drag *and* a
   live dollar-neutrality failure mode. FINRA gives testable history now; Alpaca flags close
   the live loop. Converts an unknown into a bounded, honest cost. Cost: one pull + a PnL line.

3. **Macro/VIX/rates from FRED + `^VIX` (FREE, deep) — then keep feeding the Finnhub PIT
   earnings collector.** VIX-conditioning already appears in the vol-books yet **no VIX/rate
   series is on disk** — the cheapest real gap to close (VIX to 1990, rates via FRED),
   unlocking honest regime-conditioning tests instead of ETF proxies. Pair with continuing
   `earnings_collect.py` (the only honest PIT new-information track — but months from n=300).

**Deliberately NOT recommended to buy yet:** analyst revisions / options-implied / intraday
(all BLOCKED-WITHOUT-VENDOR) — real edges live there, but they need WRDS/OptionMetrics-class
spend and should wait until a free-data book earns Level-5 forward evidence first.
