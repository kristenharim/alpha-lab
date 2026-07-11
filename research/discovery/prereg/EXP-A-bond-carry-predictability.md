# PREREG EXP-A — Bond-carry predictability (measurement, not a portfolio)

*Frozen 2026-07-10 (Discovery Program). Unlocked by DATA_QUALITY_REPORT.md = PASS. Nothing above
the Result line may be edited after the first scoring run. This is a Stage-1 MEASUREMENT test — no
portfolio is constructed and no book is proposed until the predictive + orthogonality gates pass.*

- **Experiment ID:** EXP-2026-07-10-bond-carry-predictability
- **Layer touched (one):** A — economic phenomenon (does a carry MEASURE predict future returns?)
- **Alpha type:** market (carry), low-frequency, small cross-section. NEW information source
  (FRED PIT rates), not a price/volume transform.

**Hypothesis (one falsifiable sentence, mechanism):** A point-in-time bond carry+roll-down measure
— yield minus financing plus roll-down — ranks future returns across the Treasury duration ladder
(SHY 1-3y, IEF 7-10y, TLT 20+y), because carry compensates holders for bearing duration/term risk
that is not arbitraged away at monthly frequency; and this predictability is **economically
orthogonal** to the US-equity/QQQ/trend/vol cluster (low equity beta is the whole point).

**Who pays / why it persists / what kills it:** duration-averse liability holders and rate-hedgers
pay the term premium; it persists because carry is a risk premium, not a free lunch; it disappears
in rate-shock regimes (2022) and when the curve inverts (negative carry). Pre-registered so a 2022
in-sample stress cannot be hidden.

**Data:** `../data/state_aligned.parquet` (PIT, avail-lagged) for yields (DGS2→SHY, DGS10→IEF,
DGS30→TLT mapping), DFF (financing), and the roll-down proxy; `panel_2005.parquet` for ETF returns.
Rates enter at their availability lag (1 BDay) — the decision at close t uses rates dated ≤ t−1.

**Carry measure (fixed, un-tuned):** for bucket i, `carry_i = yield_i − DFF + rolldown_i`, with
`rolldown_i` the layer's transparent slope proxy. Cross-sectional z-score across the 3 buckets each
month. No parameter is fit.

**Control:** unconditional — equal-weight duration ladder (and single-bucket buy-hold), no carry input.
**Treatment:** carry-ranked exposure — long the highest-carry bucket, underweight the lowest (or
carry-z-weighted), monthly.

**Primary statistic:** pooled predictive regression of forward 21d bucket return on carry z-score,
Newey-West t (overlap-robust); AND monthly rank IC of carry vs forward return across the 3 buckets.
**Secondary:** residual return after duration beta; rolling stability; cost-adjusted effect (ETF
spreads, monthly turnover); **equity beta** (regress the carry-sleeve daily return on SPY+QQQ);
**orthogonality** — run the carry-sleeve daily return through
`../orthogonality_benchmark.py` (must read INDEPENDENT: max_corr_to_book < 0.5).

**Universe / sample / holdout:** SHY, IEF, TLT (+ BIL cash), 2005-01-03 → 2026-07. Parameter-free ⇒
primary runs full-sample; **blind holdout = last 24 months (2024-07→2026-06)** — carry coefficient
and IC sign must not flip. Inspect only pre-2024-07 first.

**Forecast + execution timestamps:** carry known at close t (rates dated ≤ t−1); forward return
t+1…t+21. Monthly rebalance at close.

**Expected effect:** carry coefficient > 0 (t > 2); equity beta ≈ 0 (|β_SPY| < 0.1); orthogonality
PASS. Honest prior P(supported) ≈ 0.5 — bond carry is real but decayed and rate-regime-sensitive.
**Alternative:** significant carry predictability but with material equity/duration beta ⇒ NOT
independent, not a discovery.

**Failure / kill condition (decidable, stop-iterating):** carry coefficient |t| < 2 (no
predictability) OR material equity beta OR fails the orthogonality gate → **REJECTED / BLOCKED**;
do NOT build a carry portfolio, and do not test further carry proxies on the Treasury ladder without
a materially different instrument set (FX/commodity carry stays BLOCKED BY DATA per CARRY_FEASIBILITY.md).

**Cost model:** ETF bid/ask + commission per rebalance; monthly cadence keeps turnover low. No borrow
if long-only ladder; if long/short, model TLT/SHY borrow.

**Leakage / survivorship:** rates lagged 1 BDay; forward returns start t+1; ETF-only (no delisting).
`state_aligned.parquet` passed future-poison + truncation audits (DATA_QUALITY_REPORT.md).

**Parameter count:** 0 fit (fixed carry formula, fixed ladder). **Complexity:** 2/5. **Information
gain:** HIGH — the first non-price/volume *market* source Alpha Lab has measured; a clean PASS is a
genuine independent-candidate, a clean kill closes the free-data carry lane.

**Decision changed by success:** advance to Stage-2 replication (era/instrument) then the
orthogonality/portfolio gates → SHADOW-PAPER CANDIDATE (never funded without Stage-4).
**Decision changed by failure:** bond carry joins the Failure DB; the only remaining carry reopen is
vendor-gated FX/commodity term structure.

**Trial-ledger entry:** TRIAL_LEDGER #23 (Discovery / measurement) at first score.

---
**Result** (filled after the run, never edited above this line):

**Verdict: REJECTED — no predictability at the primary horizon, and what signal exists is
mechanical duration, low-but-nonzero equity beta, and fails the orthogonality gate.**
Four of the frozen kill triggers fire independently. No portfolio built; carry joins the Failure DB.

Runner: `../experiments/exp_a_bond_carry.py` · CSVs: `exp_a_horizon_decay.csv`,
`exp_a_era_stability.csv`, `exp_a_sleeve_perf.csv`, `exp_a_orthogonality.csv`, `exp_a_sleeve_daily.csv`.
Sample 2005-01-03…2026-07-10, 259 decision month-ends, 771 pooled 21d obs. All numbers below are
machine-reproduced from the frozen spec; no parameter fit, no threshold tuned.

**Carry formula used (verbatim, un-tuned).** From `state_aligned.parquet` (already availability-lagged
1 BDay ⇒ row t is decision-usable at close t). Yield pts, % annual, per bucket each day:
- SHY↔DGS2 (2y): `carry_SHY = (DGS2 − DFF) + (DGS2 − DGS3MO)/1.75`
- IEF↔DGS10 (10y proxy; IEF is 7–10y): `carry_IEF = (DGS10 − DFF) + (DGS10 − DGS5)/5`
- TLT↔DGS30 (30y proxy; TLT is 20y+): `carry_TLT = (DGS30 − DFF) + (DGS30 − DGS10)/20`
- Financing DFF (daily effective fed funds). No maturity interpolation beyond this mapping (documented
  approximation). Cross-sectional monthly z across {SHY,IEF,TLT}; monthly rebalance at month-end close;
  forward returns t+1…t+h; costs 2 bps/side on monthly turnover. Carry tail (yield pts) 2026-07-10:
  SHY 0.729 / IEF 0.974 / TLT 1.455 — upward-sloping ⇒ signal is a static long-TLT / short-SHY duration tilt.

**STEP 1 — signal test (predictability).**
- **Primary pooled regression** r_fwd21d ~ carry_z (Newey-West, lag 6): coef = **+0.00143, t = 1.53**,
  95% CI [−0.0004, +0.0032]. **|t| < 2 ⇒ the primary kill fires: no predictability.**
- Horizon decay: 5d coef −0.0004 (t −0.90); 21d +0.00143 (t 1.53); 63d +0.0032 (t 1.34). No horizon reaches |t|>2.
- Monthly cross-sectional rank IC (3 buckets): mean **+0.023, t 0.43** (257 months) — indistinguishable from zero.
- Era stability: t_z = 0.75 / 1.43 / 0.20 / 0.54 for 2005-09 / 2010-14 / 2015-19 / 2020-26; era IC sign
  **flips negative** in 2015-19 (−0.050). Not stable.
- **Blind holdout** (last 24m, 2024-07→2026-06): coef **flips sign** to −0.00089 (t −0.60) vs pre-period
  +0.0017 (t 1.63). Prereg's "sign must not flip" holdout condition is violated.
- **Duration/rate/trend controls (the decisive check):**
  - M1 r21 ~ z: coef 0.00143, t 1.53.
  - M2 r21 ~ z + static_dur: z-coef t 2.09 only because z and duration are collinear (high carry = TLT = long duration); duration itself t −1.37.
  - M3 r21 ~ z + (dur×realized-ΔDGS10) + trend: z-coef collapses to **0.00037, t 1.05**, while the mechanical
    duration term (duration × realized forward ΔDGS10) has **t = −32.9** and trend t 0.73. **Once realized
    rate moves are controlled, carry has no residual predictive power — the return is mechanical duration
    exposure, not carry alpha.** (ΔDGS10 enters only as an in-sample return-attribution control; it is never
    in the tradable signal or the sleeve — no leakage.)
- **Equity beta** of the carry sleeve (regress sleeve daily return on SPY+QQQ): **β_SPY = −0.144 (t −6.6)**,
  β_QQQ +0.043 (t 2.7). |β_SPY| = 0.14 **exceeds the pre-registered ≈0 band (|β_SPY|<0.1)** — a modest risk-off tilt.
- **Rate-duration exposure:** β_TLT = **0.331 (t 21.9)** — the sleeve is dominated by duration; β to daily
  ΔDGS10 +0.0009 (t 0.94, small at daily frequency). Sleeve: ann ret 2.4%, vol 5.8%, Sharpe 0.41, one-way turnover ~1.95×/yr.

**STEP 2 — orthogonality** (carry-z ladder = dollar-neutral weights w_i = z_i / Σ|z_i|, decided at
close t, earned t+1, monthly hold, net of 2bps/side; scored by frozen `orthogonality_benchmark.score_candidate`,
n=5413):

| dim | value | gate | pass? |
|---|---|---|---|
| max_corr_to_book | 0.269 (vol_core_svxy) | <0.50 | ✅ |
| max_partial_corr | 0.215 | <0.35 | ✅ |
| max_resid_corr_mkt | 0.133 | <0.35 | ✅ |
| downside_corr_ens | −0.122 | <0.50 | ✅ |
| tail_dep_ens | 0.094 | <0.40 | ✅ |
| dd_overlap_lift | 1.002 | <1.30 | ✅ |
| **roll_corr_max_ens** | **0.737** | <0.65 | ❌ |
| resid_alpha_t | 2.85 | >2.0 (edge) | (edge yes) |
| incr_ens ΔSharpe / P>0 | +0.121 / 0.77 | P>0.90 | (no) |

**Outcome tag: NOT INDEPENDENT.** Full-period correlation is low (0.27), but the 63d rolling correlation
to the equity/vol ensemble spikes to **0.737 > 0.65** — the duration ladder co-moves with the book cluster
in risk-off windows. Independence fails despite a nominal residual-alpha t of 2.85, so the candidate cannot
be a portfolio candidate.

**Bug-check (strong-result discipline).** (1) Reproduced the primary 21d pooled coefficient a second way
(plain `np.linalg.lstsq`, no HAC) = 0.001430, identical to the NW coefficient 0.001430. (2) Leakage: carry
from availability-lagged `state_aligned.parquet` (row t usable at t); sleeve weights `shift(1)` so decisions
at close t earn t+1; the only future-dated quantity (realized ΔDGS10) is an attribution control, never in the
signal. (3) Sample size real: 259 month-ends, 771 pooled obs, full 22-year span. No result was implausibly
strong — the headline is a near-zero, insignificant coefficient, consistent with a decayed, rate-regime-sensitive
term premium. No macro (GDP/CPI/payrolls) touched; VIX/VIX3M not used (state-only); control plane untouched.

**Frozen kill applied mechanically:** carry coefficient |t| = 1.53 < 2 (no predictability) ✔ fires; equity
beta |β_SPY| = 0.14 above the ≈0 band ✔; predictability is only mechanical duration (M3 z-coef t → 1.05 once
realized rate moves controlled) ✔; fails orthogonality gate (NOT INDEPENDENT) ✔. Any one triggers REJECTED;
all four hold. **→ REJECTED / BLOCKED. No carry portfolio is built.** Per the frozen decision, no further
carry proxies on the Treasury ladder without a materially different instrument set; FX/commodity term-structure
carry remains BLOCKED BY DATA (CARRY_FEASIBILITY.md). Bond carry → Failure DB. TRIAL_LEDGER #23 (measurement).
