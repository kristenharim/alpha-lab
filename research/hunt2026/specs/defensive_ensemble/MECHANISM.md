# defensive_ensemble

Three documented premia with low pairwise correlation, combined at inverse-vol (equal-risk)
sleeve weights and vol-targeted to 18%/yr. Sleeve A harvests the equity premium at managed
risk (Moreira-Muir 2017), gated by a 200-day trend filter that has historically sidestepped
deep-drawdown regimes. Sleeve B is cross-asset 12-month time-series momentum
(Moskowitz-Ooi-Pedersen 2012): the other side is investors who under-react to slow-moving
macro information; it is long bonds/gold/dollar in equity bear years, exactly when Sleeve A
is flat. Sleeve C is Antonacci-style dual momentum, a regime switch into the strongest risk
asset or into duration/cash. Because the sleeves earn on different return sources, the
ensemble's Sharpe exceeds any single sleeve's, so an 18%/yr vol target needs less leverage
than a single levered beta and survived the 2022 bear that killed single-beta books. Costs
are ETF-cheap (2 bps/side).

## Exact frozen implementation (this section documents `spec.py` line-for-line; the code is
## frozen and authoritative — if prose and code ever disagree, the code wins)

Universe: the sorted union of the TSMOM menu `[SPY, QQQ, IWM, EFA, EEM, TLT, IEF, GLD, SLV,
DBC, USO, UUP, HYG, LQD, VNQ]`, `RISK = [SPY, QQQ, GLD]`, and `SAFE = [TLT, BIL]`. All
returns are close-to-close `pct_change` (no fill). "Monthly rebalance" = the **first trading
day of each calendar month** (`month != month.shift(1)`); between rebalances the affected
weights are forward-filled.

**Sleeve A — trend + vol-managed QQQ (adjusts daily):**
- Trend gate on QQQ vs its 200-day simple moving average, 1% hysteresis: gate = 1 when
  `close > SMA200 * 1.01`, 0 when `close < SMA200 * 0.99`, else hold the prior gate
  (forward-fill; initial/warmup = 0).
- Exposure = **inverse volatility, not inverse variance**: `lev_q = min(2.0, 0.25 / rv21)`,
  where `rv21` = 21-day rolling std of QQQ close-to-close returns, annualized ×√252.
- `A[QQQ] = gate * lev_q`; `A[BIL] = 1 - gate` (the risk-off leg sits in BIL).

**Sleeve B — 252-day-sign TSMOM, inverse-63d-vol weights (rebalances monthly):**
- `mom = close/close.shift(252) - 1` on the 15-asset TSMOM menu; sign taken.
- Inverse-vol weights: `iv = 1/vol63` (`vol63` = 63-day annualized realized vol), normalized
  across the menu each day, times `sign(mom)` → long-or-short each asset.
- Sampled on the monthly rebalance day and forward-filled; NaN → 0.

**Sleeve C — dual momentum, single asset (rebalances monthly):**
- `r252 = close/close.shift(252) - 1`. Pick `argmax` of RISK 252-day returns if that max
  exceeds BIL's 252-day return; otherwise pick `argmax` of SAFE. One-hot weight 1.0 on the
  pick. Rows where any of RISK+SAFE has a NaN 252-day return are set flat (NaN → ffilled).
- Sampled on the monthly rebalance day and forward-filled; NaN → 0.

**Sleeve combination — inverse-vol sleeve weights (rebalances monthly):**
- Each sleeve's own daily return stream = `(sleeve.shift(1) * rets).sum` (harness lag
  convention). `svol` = 63-day (`sleeve_vol_lookback`) rolling std of each stream.
- Sleeve weights `sw = (1/svol) / Σ(1/svol)`, sampled monthly and forward-filled; warmup
  fallback = 1/3 each. `W_pre = Σ_k sleeve_k * sw_k`.

**Book-level vol target + gross cap (adjusts daily):**
- `bret = (W_pre.shift(1) * rets).sum`; `rv_book` = 63-day annualized realized vol of `bret`.
- `lev = vol_target / rv_book` (= 0.18 / rv_book), then clipped so gross never exceeds
  `gross_cap * 0.999` (= 2.0 × 0.999 = 1.998): `lev = min(lev, 1.998 / gross_pre)`, NaN → 1.0.
- Final book = `W_pre * lev`, NaN → 0.

**Params (`params.json`, ≤3 tunable):** `vol_target = 0.18`, `sleeve_vol_lookback = 63`,
`gross_cap = 2.0`. Every other constant (200d SMA, 1% hysteresis, 0.25 sigma-target, 21d rv,
252d momentum, 63d TSMOM vol, menu membership) is a pre-2021 literature default, not tuned.

**NaN behavior:** every sleeve and the final book `fillna(0.0)`; Sleeve C guards `idxmax`
against all-NaN rows with a −9e9 sentinel then nulls those rows; `lev`/`sw` inverse-vol
divisions replace ±inf with NaN then fill (lev→1.0, sw→1/3).

**Execution convention:** shared harness — weights set at close *t* earn close-to-close
*t→t+1* (`held = W.shift(1)`), costs 10 bps/side stocks / 2 bps/side ETFs on |Δw|, gross ≤2×
enforced. Rebalance cadence is **mixed**: Sleeves B/C and the sleeve-combination weights
change monthly; Sleeve A's exposure and the book-level vol target adjust **daily** (so real
turnover is higher than "monthly" implies — measured ~5%/day one-way, cost drag ~1.3%/yr).

> **Reproducibility note (2026-07-11):** an earlier version of this file said Sleeve A scales
> by "inverse realized *variance*" and did not name the gate asset or rv window; a clean-room
> reimplementation from that text diverged by 277 bps/day (red-team F-RT-07). This section
> now matches the frozen code exactly. The code and historical results are UNCHANGED — this
> was a documentation correction only.

**Falsifier:** realized pairwise sleeve correlations > 0.7 in a stress quarter
(diversification failure — the sleeves have become one levered beta), or 12 months of paper
trading below BIL.
