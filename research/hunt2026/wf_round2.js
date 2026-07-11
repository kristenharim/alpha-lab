export const meta = {
  name: 'hunt2026-round2',
  description: 'Round-2 specs for the 5-year backdated hunt: fit on data <= 2021-07-10 only',
  phases: [{ title: 'Build', detail: '4 builders, params from pre-2021 data + literature defaults' }],
}

const BUILD_SCHEMA = {
  type: 'object',
  required: ['spec_name', 'status', 'train_net_3yr', 'train_sharpe_3yr', 'avg_daily_turnover', 'notes'],
  properties: {
    spec_name: { type: 'string' },
    status: { type: 'string', enum: ['built', 'failed'] },
    train_net_3yr: { type: 'number', description: 'net total return on 2018-07-10 -> 2021-07-09 (last 3 train5y years)' },
    train_sharpe_3yr: { type: 'number' },
    avg_daily_turnover: { type: 'number' },
    train_full_cagr: { type: 'number', description: 'net CAGR scored from 2015-01-01 on train5y' },
    notes: { type: 'string' },
  },
}

const SHARED = `
You are a round-2 strategy-spec builder for the hunt2026 5-year backdated alpha hunt in
~/projects/alpha-lab. The blind window is 2021-07-10 -> 2026-07-10 (5 years). You must
behave as if today were 2021-07-10.

READ FIRST: research/hunt2026/specs/SPEC_CONVENTIONS.md and research/hunt2026/harness.py.

DATA: ONLY research/hunt2026/train5y.parquet (2014-01 -> 2021-07-09; same MultiIndex panel
format). train.parquet / holdout.parquet / holdout5y.parquet are chmod 000 — do not touch or
chmod them; no network data. harness.load_train()/load_full() read locked files — do NOT call
them; load train5y directly: panel = pd.read_parquet('train5y.parquet').
Validate with harness.run(mod, panel, start='2018-07-10') and start='2015-01-01'.

RULES: <= 3 tunables in params.json, chosen from literature defaults or pre-2021 evidence
only — NO grid searches (this protects the deflated statistics). Keep gross <= 2.0 yourself.
No ^VIX weights. Vectorized, < 2 min runtime. Create spec.py, params.json, MECHANISM.md
(mechanism + forward falsifier) AND an empty marker file named 'round2' in your spec dir
(evaluate_5y.py uses it to tag the result as blind).

CONTEXT you may use (all knowable at 2021-07-10): costs 10bps/side stocks 2bps ETFs; the
+18%/yr CAGR bar over 5 years; unlevered market-neutral won't reach it; leverage <= 2x;
diversification across return sources beats a single levered beta for surviving bear years.
Return the structured result; it is data for the evaluator, not prose.
`

phase('Build')
const results = await parallel([
  () => agent(`${SHARED}
YOUR SPEC: "tsmom_multi_asset" at research/hunt2026/specs/tsmom_multi_asset/.
Design (Moskowitz-Ooi-Pedersen 2012 time-series momentum, ETF implementation, fit-free):
Menu (liquid, data from 2014 in panel): SPY, QQQ, IWM, EFA, EEM, TLT, IEF, GLD, SLV, DBC,
USO, UUP, HYG, LQD, VNQ. Monthly on first trading day: sign_i = sign(252d total return of i);
raw weight w_i = sign_i * (1/sigma_i) / sum_j (1/sigma_j) where sigma_i = 63d realized vol
(annualized, floored at 5%). Scale the whole book so trailing 63d realized PORTFOLIO vol
(computed from the weighted return stream, no lookahead: use weights held constant over the
trailing window as an approximation) targets 15% annualized, cap gross at 2.0.
params.json: {"lookback": 252, "vol_target": 0.15, "gross_cap": 2.0}.
MOP 2012 shows this on futures at Sharpe ~1 across 25 years pre-2012 — fully out-of-sample
relative to our design date. Long AND short signs allowed (short TLT in a downtrend is the
point). MECHANISM.md: slow-moving capital + investor under/overreaction sustains multi-month
autocorrelation across asset classes; the strategy is long that autocorrelation, and its
crisis-alpha profile (shorts what grinds down) is the diversifier levered equity lacks.`,
    { label: 'build:tsmom_multi_asset', schema: BUILD_SCHEMA }),

  () => agent(`${SHARED}
YOUR SPEC: "trend_vol_qqq" at research/hunt2026/specs/trend_vol_qqq/.
Design (composition of two pre-2012 literature mechanisms, fit-free):
Daily: risk-on iff QQQ close > 200d SMA of QQQ close (1% hysteresis band: cross above
SMA*1.01 to turn on, below SMA*0.99 to turn off, hold state inside).
Risk-on weight on QQQ = min(2.0, 0.25 / rv21) where rv21 = 21d realized vol annualized;
risk-off: 1.0 BIL. 0.05 tolerance band on weight changes to cut turnover.
params.json: {"sma_window": 200, "sigma_target": 0.25, "rv_lookback": 21}.
MECHANISM.md: vol-targeting harvests the equity premium at constant risk (Moreira-Muir 2017);
the trend gate removes the regime vol-targeting handles worst (a slow grind-down where vol
stays moderate but drift is negative — vol-managed books stay ~1x long through those;
Faber 2007 timing evidence). Falsifier: a V-shaped crash-recovery year where the gate
whipsaws twice for >5% each vs the ungated book.`,
    { label: 'build:trend_vol_qqq', schema: BUILD_SCHEMA }),

  () => agent(`${SHARED}
YOUR SPEC: "dual_momentum_gold" at research/hunt2026/specs/dual_momentum_gold/.
Design (Antonacci dual momentum, defensive leg generalized, fit-free):
Monthly on last trading day: risk menu {SPY, QQQ, GLD}; defensive menu {TLT, BIL}.
Compute 252d total return for all. If best risk asset's 252d return > BIL's 252d return:
hold that single risk asset at 1.5x. Else: hold the better of {TLT, BIL} by 252d return
at 1.0x (defensive momentum — do NOT hardcode TLT: in a rising-rate regime bonds fail as
the safe leg, a fact visible in 2013/2018 train data).
params.json: {"lookback": 252, "risk_leverage": 1.5, "defensive_leverage": 1.0}.
GLD in the risk menu is the non-equity absolute-momentum leg (Antonacci's own extensions);
its 2019-2021 momentum is visible in train5y. MECHANISM.md: relative momentum picks the
strongest trend, absolute momentum steps aside in bears; the other side is investors who
rebalance against 12m trends. Falsifier: two consecutive switch months each costing >5% vs
buy-and-hold (whipsaw regime).`,
    { label: 'build:dual_momentum_gold', schema: BUILD_SCHEMA }),

  () => agent(`${SHARED}
YOUR SPEC: "defensive_ensemble" at research/hunt2026/specs/defensive_ensemble/.
Design (equal-risk ensemble of three uncorrelated sleeves, standalone reimplementation —
do NOT import sibling specs):
Sleeve A: trend+vol QQQ (200d SMA gate w/ 1% hysteresis; on: min(2, 0.25/rv21) QQQ; off: BIL).
Sleeve B: multi-asset 252d-sign TSMOM (menu SPY,QQQ,IWM,EFA,EEM,TLT,IEF,GLD,SLV,DBC,USO,UUP,
HYG,LQD,VNQ; inverse-63d-vol weights, monthly).
Sleeve C: dual momentum {SPY,QQQ,GLD} vs {TLT,BIL} by 252d return, single asset.
Combine monthly with inverse-realized-vol sleeve weights (63d vol of each sleeve's trailing
return stream), then scale the total book to an 18% annualized 63d realized-vol target,
gross capped at 2.0.
params.json: {"vol_target": 0.18, "sleeve_vol_lookback": 63, "gross_cap": 2.0}.
MECHANISM.md: three documented premia (equity premium at managed risk, cross-asset trend,
regime-switching momentum) with low pairwise correlation; the ensemble's Sharpe exceeds any
sleeve's, so a vol target calibrated to hit ~18%/yr needs less leverage and survives the
bear year that kills single-beta books. Falsifier: realized sleeve correlations > 0.7 in a
stress quarter (diversification failure) or 12m paper below BIL.`,
    { label: 'build:defensive_ensemble', schema: BUILD_SCHEMA }),
])

return results.filter(Boolean)
