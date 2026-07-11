export const meta = {
  name: 'hunt2026-research',
  description: 'Parallel alpha-hunt research: S&P structure, firm practice, literature, in-house synthesis',
  phases: [{ title: 'Research', detail: '4 parallel researchers -> candidate strategy proposals' }],
}

const CANDIDATE_SCHEMA = {
  type: 'object',
  required: ['summary', 'candidates'],
  properties: {
    summary: { type: 'string', description: 'markdown research summary with key evidence' },
    candidates: {
      type: 'array',
      items: {
        type: 'object',
        required: ['name', 'mechanism', 'construction', 'params', 'why_18pct'],
        properties: {
          name: { type: 'string' },
          mechanism: { type: 'string', description: 'one-paragraph economic mechanism: who is on the other side and why the edge persists' },
          construction: { type: 'string', description: 'precise signal + portfolio construction using ONLY fields open/close/volume/member on the sandbox universe (S&P500 stocks + listed ETFs + ^VIX signal-only), daily close-to-close rebalance' },
          params: { type: 'array', items: { type: 'string' }, description: 'the <=3 tunable parameters and sensible default values' },
          why_18pct: { type: 'string', description: 'honest arithmetic for how this clears +18%/yr NET (costs 10bps/side stocks 2bps ETFs, leverage <=2x allowed, long-bias allowed)' },
          evidence: { type: 'string', description: 'citations / prior results backing it' },
        },
      },
    },
  },
}

const COMMON = `
CONTEXT: alpha-hunt in ~/projects/alpha-lab (paper research only). Goal: strategies on FREE
DAILY data that would return >= +18% NET over the 12 months ending 2026-07-10, discovered and
parameterized WITHOUT seeing those 12 months. Data cut: nothing after 2025-07-10 may inform
design. Costs 10 bps/side stocks, 2 bps/side ETFs. Leverage <= 2x gross. Long-bias fine.
Execution convention: daily target weights at the close, earning next-day close-to-close
returns. Available panel fields: open, close (adjusted), volume, S&P500 point-in-time
membership mask, ~35 macro/sector ETFs, ^VIX (signal only, untradable). NO options, NO
intraday bars, NO fundamentals except what is freely derivable.
Unlevered market-neutral strategies essentially never hit 18%/yr — favor long-biased,
levered, or concentrated/timed designs. Propose 3-6 candidates. Be brutally honest in
why_18pct: most proposals fail this bar; say which of yours are stretches.
Your final structured output is the deliverable.`

phase('Research')
const [spx, firms, lit, inhouse] = await parallel([
  () => agent(`${COMMON}

ROLE: S&P structure specialist. Study ONLY the training sandbox:
~/projects/alpha-lab/research/hunt2026/train.parquet (pandas MultiIndex columns
(field, ticker), fields open/close/volume/member; sectors.parquet and sandbox_meta.json
sit beside it). You are FORBIDDEN from reading holdout.parquet or pulling any data after
2025-07-10 — doing so invalidates the whole hunt.
Use ~/projects/alpha-lab/.venv/bin/python for analysis. Investigate on train data:
(1) index add/drop effects — the member mask flips give you event dates; measure pre/post
    inclusion-drift and deletion-reversal;
(2) overnight vs intraday return split (close->open vs open->close) by name, by sector,
    by vol regime — is the overnight premium exploitable at our costs given the convention
    is close-to-close (a tilt TOWARD high-overnight-share names is; holding only overnight
    is not);
(3) seasonality: turn-of-month, month-of-quarter rebalance flows, Sep weakness, FOMC drift
    proxies (we have no event calendar — calendar-day proxies only);
(4) dispersion / vol regimes: cross-sectional vol as a timing signal for reversal vs
    momentum; ^VIX term signals from the level alone;
(5) ETF flow proxies: RSP/SPY ratio, sector volume surges, SVXY behavior.
Report measured effect sizes (ann. return spread, t-stats) from train, not folklore.
Turn the strongest effects into candidates.`,
    { label: 'research:spx-specialist', schema: CANDIDATE_SCHEMA, effort: 'high' }),

  () => agent(`${COMMON}

ROLE: firm-alpha researcher. Web research: how real shops — especially small/mid quant
firms and sophisticated solo PMs — actually source alpha that is implementable on daily
bars. Sources: practitioner interviews (podcasts/transcripts), investor letters, 13F
patterns, quant blogs (Quantocracy sphere), prop-firm writing, AQR/Man/academic-practitioner
crossover pieces. Focus on what is REPEATEDLY documented as working after costs at small
scale: e.g. index-rebalance front-running, ETF primary-market frictions, post-earnings
drift at small size, vol-selling with tail hedges, trend at moderate leverage, factor
timing. Discard anything requiring intraday execution, options books, or paid data.
Cite sources in evidence.`,
    { label: 'research:firm-alpha', schema: CANDIDATE_SCHEMA, effort: 'high' }),

  () => agent(`${COMMON}

ROLE: literature researcher. Web research on PUBLISHED strategies with credible 15%+/yr
net (or Sharpe high enough that <=2x leverage on daily data gets there): time-series
momentum (Moskowitz-Ooi-Pedersen), cross-sectional momentum, PEAD, vol-risk-premium
harvesting implementable with SVXY/VIX-signal rules, betting-against-beta, sector
rotation/dual momentum (Antonacci), trend+carry blends, low-vol anomaly with leverage,
turn-of-month and overnight anomalies. For each: the published net return, the
out-of-sample decay evidence (post-publication returns typically halve — cite McLean &
Pontiff), and the honest levered arithmetic to 18%. Prefer strategies with documented
post-publication survival. Cite papers with years in evidence.`,
    { label: 'research:literature', schema: CANDIDATE_SCHEMA, effort: 'high' }),

  () => agent(`${COMMON}

ROLE: in-house synthesizer. Work ONLY from this repo's own prior findings — read
~/projects/alpha-lab/memos/ (especially diagnostics-2026-07-10.md and
alpha-roadmap-2026-07.md), tracks/*/STATE.md, README.md, and any scorecards. Do NOT web
search. Key priors: PEAD showed +8.45% drift on ~530 events; statarb reversal is DEAD at
daily frequency on large caps (implementable gross ~1.3-1.6%/yr vs 5.3%/yr costs — the
post-mortem explains why residual-space accounting lied); dispersion results are in the
statarb ablation. Propose ORIGINAL candidates that build on what survived and invert what
failed: e.g. if slow-reverting entries earned MORE (the killed kappa screen's finding),
what does that imply? If costs killed reversal at 5.3% daily turnover, what
low-turnover expressions of the same information survive? PEAD at concentrated size?
Honest arithmetic to 18% required.`,
    { label: 'research:in-house', schema: CANDIDATE_SCHEMA, effort: 'high' }),
])

return { spx, firms, lit, inhouse }
