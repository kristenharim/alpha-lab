# Setup record — forward alpha-isolation test (EXP-2026-07-14-alpha-forward)

FROZEN 2026-07-14, before the first forward day (2026-07-15). Implements the production
action recommended by memos/js-factor-program-final-2026-07-14.md: measure each live book's
forward return beyond a frozen factor-replication benchmark, after costs and financing.
Measurement/review layer ONLY — no trading weight, capital, or strategy-logic change.
JSE is not deployed anywhere in this layer, per the program verdict.

## Freeze

- **Freeze date 2026-07-14 · forward start 2026-07-15 · reviews: 6m 2027-01-14, 12m 2027-07-14.**
- Exposure source: research/attribution/frozen_betas_2026-07-14.json (write-once; v1
  superseded pre-forward by the review amendments, archived as *_v1_superseded.json).
  Betas from EXP-2026-07-14-factor-attribution blind windows (attribution.csv, SHA in file).
- Panels: corrected post-phantom-row (memos/panel-phantom-row-correction.md). Frozen
  historical results files untouched; corrected data used for all forward accounting.
- Models: **M2** (FF5 + Mom + TSMOM proxy + QQQRES) for five books; **M2g** (M2 + GLD
  excess) for defensive_ensemble and dual_momentum_gold — their gold loadings are KNOWN
  exposures documented in the final memo before the forward test started (factor-model
  review; amended 2026-07-14 with zero forward days elapsed; after 2026-07-15 the
  benchmark may not change for any reason until the 12m review).
- Blind-window betas kept over full-history deliberately: full-history rows would inject
  a one-signed +7-8%/yr benchmark bias on the high-gross books; blind-window noise is
  symmetric and enters the t-stat (factor-model review, quantified).
- QQQRES projection coefficients frozen (fit through 2026-05-29); drift is first-order
  self-hedging, residual exposure ≈ 0.25%/yr worst case. No refit for 12 months.

## Frozen exposures (headline betas; full set in the JSON)

| book | model | Mkt | Mom | TSMOM | QQQRES | GLD | frozen α (t) |
|---|---|---|---|---|---|---|---|
| vol_managed_qqq | M2 | 1.54 | 0.03 | 0.23 | 1.59 | — | +1.4% (0.25) |
| vol_core_svxy | M2 | 1.76 | 0.04 | 0.24 | 1.57 | — | +0.5% (0.10) |
| dual_momentum_gem | M2 | 1.39 | 0.24 | 0.60 | 1.19 | — | +15.8% (1.12) |
| momentum_concentrated | M2 | 0.85 | 0.49 | 0.13 | 0.30 | — | −7.5% (−0.68) |
| trend_vol_qqq | M2 | 0.94 | 0.14 | 0.76 | 0.93 | — | +9.1% (1.50) |
| defensive_ensemble | M2g | 0.65 | 0.05 | 0.65 | 0.53 | 0.22 | +3.9% (1.15) |
| dual_momentum_gold | M2g | 0.53 | 0.16 | 1.12 | 0.62 | 0.79 | +2.5% (0.32) |

(β values as frozen in the JSON; table rounded. M2g α is the frozen refit on the corrected
panel; M2 as-run α retained in the JSON for the record.)

## Benchmark construction (per finalized day)

- replication_t = RF_t + Σⱼ βⱼ·Fⱼ,t (uncosted — biases residuals AGAINST the books by an
  estimated ≤ 50 bps/yr; will not be adjusted at review).
- financing_t = (gross_{t−1} − 1)⁺ × (RF_t + 0.50%/252), gross from the book's own ledger
  (leverage actually held during day t).
- **residual_t = book net return_t − replication_t − financing_t.** Book returns are the
  ledger's `ret_1d` (true daily net, added 2026-07-14; the ledger `nav` is a rolling
  252d-rebased index and is never differenced — integrity-audit blocker B1).
- TSMOM and placebo/GLD closes from a dedicated ~550-day fresh yfinance pull each review
  (single adjustment vintage; no panel seam inside any rolling window — audit finding 2).
- Finalized day = book return exists AND FF factors exist AND the day trails the FF file
  end by ≥ 10 trading days (revision embargo).

## Write-once forward ledger (`ledgers/hunt2026/alpha_forward/<series>.jsonl`)

Exact fields per day: `date, ret_net, repl_ret, fin, resid_net, gross`. Append-only,
strictly-increasing dates; recompute drift vs stored rows warns and never rewrites.
Rows embed the factor vintage at first append (the series of record); mid-run failures
self-heal on later runs; the same date may embed different FF vintages across series —
accepted. At the 12m review the full series is recomputed from the then-current vintage
as a disclosed sensitivity; |Δresid_ann| > 25 bps/yr on any book triggers investigation,
not substitution. Derived at review time: tracking error, residual drawdown, turnover
(from ledger targets), monthly consistency.

## Cadence

- `scripts/hunt_alpha_review.py` runs monthly via the evening routine (wired 2026-07-15:
  first weekday evening each month, self-healing trigger = no report file for the current
  month; the routine commits only `ledgers/hunt2026/alpha_forward/` + `reports/alpha_forward/`
  and may never act on results). Also runnable on demand; it is idempotent.
  Monthly output = descriptive statistics only; the report carries a
  standing line that no parameter, hedge, or model-selection action may be taken from it.
- `--selfcheck` (offline) validates the replication chain against frozen alphas at any time.
- The nightly paper job must run after 16:00 ET (it runs 20:30 local); a pre-close mark
  would be permanently embedded.

## Placebos (same framework, pre-registered bands — judged on bands, NEVER on t-stats)

| series | expected resid/yr | band | note |
|---|---|---|---|
| CTRL_spy_buyhold | +0.2% | ±0.5% | the true ≈0 calibration control |
| CTRL_qqq_buyhold (M2) | +3.2% | ±0.5%, TE < 0.5% | deterministic tautology (QQQRES built from QQQ); plumbing control only |
| CTRL_qqq_buyhold_M1 | +3.4% | ±2·4.9%/√(n/252) | the informative control: tests the frozen projection forward |
| CTRL_qqq_1.5x_static | +6.4% | ±0.7% | as-run α minus the externally-charged 50bps spread leg |

A band miss is a pipeline stop, not a result.

## Decision rules (pre-committed; no threshold may be revised after 2026-07-15)

- **No alpha call before the 12m review.** The 6m review is descriptive.
- Clusters for multiplicity (m=3): QQQ vol/trend {vol_managed_qqq, vol_core_svxy,
  trend_vol_qqq} · momentum {dual_momentum_gem, dual_momentum_gold, momentum_concentrated}
  · defensive/TSMOM {defensive_ensemble}.
- At 12m: **"promising but unproven residual alpha"** requires NW-lag-5 t ≥ 2.4 AND
  positive cumulative residual in both the 0–6m and 6–12m halves AND all placebo bands
  passing AND residual surviving the financing/cost stress — then schedule an independent
  replication. 2.0 ≤ t < 2.4 = "suggestive — extend 12 months, no allocation change."
  Below 2.0 or negative = **factor-premium harvesting confirmed**; factor-adjusted
  kill/demote rules replace raw-vs-SPY going forward (manifest edit, Kristen's approval).
- No allocation changes automatically; any proposed deployment change is surfaced to
  Kristen with this ledger as evidence.

## Disclosures (carry into every review)

1. **Forward NAV is model-marked, not broker-marked** (books are virtual; nav recomputed
   from the frozen spec on the yfinance panel). momentum_concentrated's forward residual
   therefore retains unquantified FAVORABLE survivorship bias (a delisting books 0, not
   the loss); its 12m verdict must be caveated. Reality tripwire: the standing
   EXP-OPS-REALITY reconciliation (per-book tracking drag < 30 bps/month vs broker) is the
   alarm; a persistent breach voids the affected book's forward series.
2. Constant frozen betas leave factor-TIMING P&L in the residual by design — consistent
   with the program's classification (timing known premia = premium-timing, not alpha
   until it clears the bar above). vol_managed_qqq's regime beta range (0.80–1.47 around
   frozen 1.54) means large residual swings; read the NW t, not the point estimate.
3. Cash drag: the harness credits no RF on uninvested cash (momentum_concentrated gross
   ≈ 0.85), matching the freeze-time convention — the forward test measures the same
   quantity; do not over-read a negative residual by ~1–2%/yr of RF drag.
4. Adjusted-close vintage: a date recomputed later may not bit-match its write-once row;
   first-append vintage is the record (see ledger section).
5. TSMOM proxy under-spans monthly cross-sectional switching (gem/gold) and SMA200
   mechanisms (trend_vol_qqq); leaked trend premium in residual is classified per
   disclosure 2, and building bespoke proxies now would fit the benchmark to the books.

## Review dispositions (all recommendations adopted except)

- Data-integrity M4's "judge 1.5x placebo at +4.7%" — adopted in mechanism but centered
  at the as-run regression alpha (+6.4% after the financing-leg adjustment) rather than
  the const-leakage arithmetic; the frozen betas came from that exact regression, so the
  empirical anchor is the consistent one. Band unchanged (±0.7%).
- Everything else: adopted verbatim (B1 ret_1d, B2 disclosures+tripwire, M3 single
  financing charge, M2g amendment, M1-QQQ control, embargo, drift warning, mode-scoped
  ledger idempotency, blind-window betas kept).

## Trial accounting

One registered forward experiment, no variants; thresholds frozen above. Adaptive-loop
flag: yes (implements the completed program's recommendation). Run stamp:
artifacts/attribution/alpha_forward_setup_run.json.
