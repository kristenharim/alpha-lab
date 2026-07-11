export const meta = {
  name: 'hunt2026-build',
  description: 'Build 12 frozen strategy specs from curated research candidates, fit on train only',
  phases: [{ title: 'Build', detail: 'one builder agent per spec' }],
}

const BUILD_SCHEMA = {
  type: 'object',
  required: ['spec_name', 'status', 'train_net_2yr', 'train_sharpe_2yr', 'avg_daily_turnover', 'notes'],
  properties: {
    spec_name: { type: 'string' },
    status: { type: 'string', enum: ['built', 'failed'] },
    train_net_2yr: { type: 'number', description: 'net total return on last 2 train years (2023-07-10 -> 2025-07-10)' },
    train_sharpe_2yr: { type: 'number' },
    avg_daily_turnover: { type: 'number' },
    train_full_cagr: { type: 'number', description: 'approx net CAGR over full train scored from 2015-01-01' },
    notes: { type: 'string', description: 'fitting decisions, param choices, anything the evaluator should know' },
  },
}

// {name, ref: [role, index in research_findings.json candidates], extra guidance}
const BUILDS = [
  { name: 'vol_managed_qqq', ref: ['spx', 0], extra: 'Add the 0.05 tolerance band mentioned in the construction to cut turnover.' },
  { name: 'vol_core_svxy', ref: ['spx', 1], extra: '' },
  { name: 'breadth_gated_leverage', ref: ['spx', 2], extra: 'Known fragile — build exactly as specified, no rescue-tuning.' },
  { name: 'trend_gated_spy_2x', ref: ['firms', 0], extra: 'Also read lit candidate 0 (same design). Use BIL as the risk-off leg (SHY duration risk not wanted); 1% hysteresis band.' },
  { name: 'momentum_concentrated', ref: ['firms', 2], extra: 'Top 20 by 12-1 momentum among member==1 names, inverse-vol weights, monthly refresh in 4 weekly tranches, Barroso-Santa-Clara 20% vol targeting, cap 2x floor 0.5x.' },
  { name: 'dual_momentum_gem', ref: ['lit', 1], extra: 'Menu SPY/QQQ/EFA vs TLT fallback, 12m absolute-momentum gate vs BIL total return, 1.5x on the equity leg, monthly.' },
  { name: 'svxy_vix_carry', ref: ['lit', 2], extra: 'Gate: VIX < 25 AND VIX > 10d realized SPY vol (annualized, x100 to VIX points). ON: 0.5 SVXY + 0.5 SPY. OFF: 1.0 BIL.' },
  { name: 'gap_drift', ref: ['inhouse', 0], extra: 'The repo PEAD prior is the mechanism; z >= 2.5 in 60d sigmas + 3x 20d-median volume, enter close t+1, hold 60d, 5% cap, idle capital in SPY, 1.5x gross. Vectorize — no per-event Python loops over the full panel.' },
  { name: 'ew_levered_vix_gate', ref: ['inhouse', 1], extra: 'Banded rebalance (20% relative drift) is what keeps turnover survivable — implement it.' },
  { name: 'deep_dip_reversion', ref: ['inhouse', 2], extra: 'Reuse tracks/statarb residual code paths where possible (rolling_beta etc). Long-only, entry s<=-2.5, exit s>=-0.5 or 25d, max 15 names, idle in SPY, 1.5x.' },
  { name: 'vix_panic_buyer', ref: ['inhouse', 3], extra: '' },
  { name: 'composite_book', ref: ['inhouse', 4], extra: 'Standalone reimplementation (no imports from sibling specs): 1.2x banded EW core + 0.5x gap-drift sleeve + 0.3x SPY panic sleeve, VIX-40 halving gate, gross <= 2.0.' },
]

phase('Build')
const results = await parallel(BUILDS.map(b => () => agent(`
You are a strategy-spec builder for the hunt2026 alpha hunt in ~/projects/alpha-lab.

YOUR SPEC: "${b.name}". Your full brief is candidate index ${b.ref[1]} of role "${b.ref[0]}"
in ~/projects/alpha-lab/research/hunt2026/research_findings.json — read it (mechanism,
construction, params, evidence). Extra guidance: ${b.extra || 'none'}.

READ FIRST:
- research/hunt2026/specs/SPEC_CONVENTIONS.md (the contract — follow it exactly)
- research/hunt2026/harness.py (the scorer)

BUILD: create research/hunt2026/specs/${b.name}/ with spec.py, params.json (<= 3 tunables),
MECHANISM.md (one-paragraph mechanism + what would falsify it forward). target_weights(panel)
must be pure pandas/numpy, run in under ~2 minutes on the full panel, produce weights only on
tradable tickers (never ^VIX), keep gross <= 2.0 every day itself (do not rely on the harness
clip), and never use future information (no shift(-k), no full-sample statistics).

HARD RULES:
- Train data ONLY: harness.load_train(). holdout.parquet is chmod 000 — do not touch it,
  do not chmod it, do not pull any external/network data. Params are fit/sanity-checked on
  train only. If the brief's default params look reasonable on train, KEEP THEM — do not
  grid-search; light validation only (this protects the deflated statistics).
- Use ~/projects/alpha-lab/.venv/bin/python. Run from repo root so 'import harness' works
  via: cd ~/projects/alpha-lab/research/hunt2026 && ../../.venv/bin/python ...

VALIDATE before returning: score with harness.run(mod, harness.load_train(), start=...) on
(a) last 2 train years (start='2023-07-10') and (b) full train (start='2015-01-01').
Confirm: no exceptions, gross_cap_violations == 0, turnover sane for the design, metrics
roughly consistent with the brief's train claims. If wildly off, debug your implementation
(NOT the params) — the brief's numbers came from real train EDA.

Return the structured result. Your final output is data for the evaluator, not prose.
`, { label: `build:${b.name}`, schema: BUILD_SCHEMA })))

return results.filter(Boolean)
