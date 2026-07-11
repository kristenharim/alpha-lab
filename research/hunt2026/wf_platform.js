export const meta = {
  name: 'hunt2026-platform-fleet',
  description: 'Engineer the next platform tier: paper book, cross-market replication, IC screen, Estimator Lab, docs',
  phases: [{ title: 'Engineer', detail: '5 parallel engineering agents' }],
}

const RESULT = {
  type: 'object',
  required: ['task', 'status', 'summary', 'artifacts'],
  properties: {
    task: { type: 'string' },
    status: { type: 'string', enum: ['done', 'partial', 'blocked'] },
    summary: { type: 'string', description: 'key findings/decisions, written for the evaluator' },
    artifacts: { type: 'array', items: { type: 'string' }, description: 'paths created/modified' },
    key_numbers: { type: 'string', description: 'the numbers that matter, compact' },
  },
}

const COMMON = `
You are an engineering agent for alpha-lab (~/projects/alpha-lab), a paper-trading research
platform. House rules (CLAUDE.md): assume a great result is a bug until proven otherwise;
smallest change that works; tests never touch the network; never edit frozen specs under
research/hunt2026/specs/. Use ~/projects/alpha-lab/.venv/bin/python. The shared harness and
panels live in research/hunt2026/ (harness.py; panel_2005.parquet = 2005->2026 ETF+2014+
stock MultiIndex panel [field, ticker]; ^VIX signal-only). Costs 10bps/side stocks, 2bps
ETFs. Your final structured output is data for the orchestrator, not prose.`

phase('Engineer')
const results = await parallel([
  () => agent(`${COMMON}

TASK: paper-book runner for the promoted hunt2026 books. Study scripts/paper_book_run.py
and core/broker/ first (the statarb paper runner + Alpaca wiring — find how credentials
are loaded; the nightly statarb workflow was disabled, its plumbing remains).
Build scripts/hunt_paper_run.py:
- Books (fixed registry in the script): vol_managed_qqq (core), vol_core_svxy, trend_vol_qqq,
  defensive_ensemble — loaded via harness.load_spec from research/hunt2026/specs/, weights
  from target_weights on a fresh panel built from live/latest daily data (reuse the repo's
  price-fetch path for current quotes; lookback history from panel_2005.parquet extended
  with recent yfinance bars is fine for signal computation).
- Equal capital split across the 4 books initially; per-book tag in client_order_id;
  ledger JSONL per book (date, targets, fills, nav, benchmark nav) under ledgers/hunt2026/.
- Benchmarks logged alongside each book nightly: exposure-matched SPY AND the book's naive
  benchmark (bench_qqq_buyhold for QQQ books; 60/40 SPY/BIL for the ensemble).
- DEFAULT IS --dry-run (compute + print orders, write ledger row marked dry, submit
  NOTHING). A --live flag submits to the ALPACA PAPER account only — never add real-money
  paths. Do NOT run --live yourself; run --dry-run once and report its output.
- Also write audit-bundle/com.rimrim.hunt2026-paper.plist (launchd, nightly 20:30 local,
  --live) but leave it in audit-bundle/ DISABLED (.disabled suffix) — the orchestrator
  enables it after review.
- One offline test: tests/test_hunt_paper.py — registry loads, weights produced on a
  fixture panel, ledger row schema. Keep the suite green (run pytest tests/ -q).`,
    { label: 'eng:paper-book', schema: RESULT, effort: 'high' }),

  () => agent(`${COMMON}

TASK: cross-market replication study — does the vol-managed-leverage mechanism (and the
trend gate) exist OUTSIDE US large-cap equities? This is replication evidence, not a new
trial (record it that way).
Universe: every non-US-equity and non-equity ETF already in panel_2005.parquet (EFA, EEM,
VGK, EWJ, TLT, IEF, GLD, SLV, DBC, USO, UNG, UUP, FXE, HYG, LQD, VNQ, IWM, MDY) PLUS pull
~10 more country/asset ETFs from yfinance 2005->2026-07-10 into research/hunt2026/
panel_xmarket.parquet (e.g. EWU EWG EWA EWC EWY EWT EWZ FXI EWH EWS; append to
data/manifest.jsonl). Free choice of liquid additions; document.
For EACH asset, full available history, compute:
(a) buy-and-hold: CAGR, Sharpe, worst rolling 12m;
(b) vol-managed at sigma_target=0.25/lookback 21d (the FROZEN registered params — no
    per-asset tuning), cap 2x, 2bps costs;
(c) 200d-SMA trend gate (1% hysteresis) at 1x, risk-off cash;
(d) combo (gate x vol-target).
Deliverable: research/hunt2026/robustness/xmarket.md — per-asset table of Sharpe deltas
(managed minus buy-hold), a mechanism verdict per asset class (equities/bonds/commodities/
FX), and the honest aggregate: in how many of N independent assets does vol management
improve Sharpe? Does the trend gate? Use sign-test logic, not cherry-picks. State clearly
that assets sharing the US equity factor (IWM, MDY, VGK...) are NOT independent draws —
group by correlation cluster and count clusters, not tickers.`,
    { label: 'eng:xmarket-replication', schema: RESULT, effort: 'high' }),

  () => agent(`${COMMON}

TASK: IC-first signal screen — what actually ranks S&P 500 stocks? Follow-up to the
momentum-IC kill (read research/hunt2026/robustness/ic.md and FAILURES.md F-016 first;
replicate its methodology exactly: monthly, PIT members via panel field 'member', rank IC
vs 21d and 63d forward returns, 2015->2026, report mean IC / t-stat / hit rate / by-year).
Signals to screen (all computable from open/close/volume + sector map in sectors.parquet):
1. short-term reversal (21d return, sign-flipped)
2. sector-relative 12-1 momentum (momentum minus sector-ETF momentum)
3. residual momentum (12-1 on rolling-beta residuals vs sector ETF — reuse
   tracks/statarb/residual.py rolling_beta)
4. idiosyncratic volatility (60d residual vol, low-minus-high)
5. dispersion residual (deviation of 21d return from sector median, sign-flipped)
6. volume shock (21d avg volume / 252d avg volume)
7. overnight-vs-intraday share (126d overnight return share)
8. gap persistence (count of >2-sigma up-gaps held, 63d)
9. low-vol (60d total vol, low-minus-high)
10. 52-week-high proximity (close / 252d max close)
Deliverable: research/hunt2026/robustness/ic_screen.md — one table (signal x {mean IC,
t, hit rate, IC by half-decade}), flag |t|>=2 as candidates, and add hypothesis-level
entries for the clear zeros. NO portfolio construction, NO strategy building — measurement
only. Fit-free formulas only; do not tune any signal's window to improve its IC.`,
    { label: 'eng:ic-screen', schema: RESULT, effort: 'high' }),

  () => agent(`${COMMON}

TASK: found Estimator Lab — estimation research judged on realized RISK, not returns.
Create research/estimator_lab/ with:
1. PLAN.md — pre-registration: question ("which covariance estimator produces minimum-
   variance portfolios with the lowest realized out-of-sample volatility on S&P 500
   daily returns?"), estimators, metric, windows, and expected results WRITTEN BEFORE
   RUNNING (include an 'expected' column you fill in first, then run).
2. estimators.py — implementations, each cov(returns_window) -> Sigma:
   (a) sample covariance;
   (b) k-factor PCA (k in {1,3,5}) + diagonal idio;
   (c) same with JSE/psi-hat correction per factor (the hunt2026 pca_minvar_jse
       correction, generalized to k>1: correct each h_i toward the equal-weight direction
       using psi_i^2 = max(tau, 1 - p*delta2/sigma_i^2); read
       research/hunt2026/specs/pca_minvar_jse/spec.py and, READ-ONLY,
       ~/projects/factor_lab/bias_correction_demo.py);
   (d) Ledoit-Wolf shrinkage to scaled identity (implement the closed form, no sklearn
       dependency if absent — check what's installed first);
   (e) Marchenko-Pastur eigenvalue clipping.
3. run_minvar.py — walk-forward: monthly 2015->2026 on PIT S&P 500 members (>=252d
   history; panel research/hunt2026/panel_2005.parquet), estimate Sigma on trailing 252d,
   build UNCONSTRAINED min-var (sum w = 1, shorts allowed, per-name |w| cap 5% to keep it
   sane) AND long-only variant; hold one month; metric = realized ann. vol next month,
   plus realized Sharpe and turnover as secondary. Paired comparison per month, report
   mean realized vol per estimator with a paired t-test vs sample covariance.
4. RESULTS.md — the table + verdict vs the pre-registered expectations.
This is the Goldberg research bridge: the k>1 JSE test that the muted k=1 result
pre-registered. Keep runtime sane (~500 names x 135 months; vectorize; Sherman-Morrison
or Woodbury for factor-model inverses).`,
    { label: 'eng:estimator-lab', schema: RESULT, effort: 'high' }),

  () => agent(`${COMMON}

TASK: platform documentation layer. Create/update in research/hunt2026/:
1. CONFIDENCE_LADDER.md — levels 0-6 (0 untested idea, 1 literature-replicated, 2 single
   blind pass, 3 multiple walk-forward passes, 4 cross-market replication, 5 live paper
   success, 6 live capital) + current placement of every spec in TRIAL_LEDGER.md with a
   one-line justification each (read TRIAL_LEDGER.md, FAILURES.md, walkforward/summary.md,
   robustness/*.md for evidence). Separate ROBUSTNESS from ECONOMIC VALUE: add a second
   axis (value vs naive benchmark, capacity, complexity, uniqueness) scored 1-5 per
   promoted book.
2. PREREGISTRATION.md — the template every future experiment fills BEFORE running:
   hypothesis, layer touched (A-D), expected result, alternative result, failure/kill
   condition, trial-ledger row, alpha type tag (market/estimator/portfolio/execution).
3. FAILURES.md — append a '## Negative-result registry' section: hypothesis-level records
   aggregating multiple tests (e.g. 'short-term reversal survives costs' now has F-001,
   F-004, F-008 as independent tests -> strong evidence against; 'cross-sectional
   momentum ranks large caps' has F-015+F-016). Do not renumber existing entries.
4. STATUS.md — one-page decision dashboard: experiments run/alive/killed, hypothesis
   confidence stars per family (trend/vol-management/momentum/reversal/carry/estimator),
   promoted books with confidence-ladder level, paper-book state, next pre-registered
   experiments. Plain markdown tables, terse.
Read-only everywhere else; keep every claim traceable to a file in the repo.`,
    { label: 'eng:docs-ladder', schema: RESULT }),
])

return results.filter(Boolean)
