# TM timing gate — EXP-2026-07-14-timing-tm

Prereg: timing-tm-2026-07-14.md (frozen incl. dispositions 1–9). M2T = M2 + γ·(Mkt−RF)². Blind windows claim-bearing; as-frozen panel (F1 defect inherited, disclosed). NW lag 5 primary; lag-21 and stationary-bootstrap columns are disclosure.

## Gate verdict: **CONTROL-FAIL (see adjudication)**
- timing-positive books: 0/7 (strong tier, 5y books only: 0)
- control adjudications: [('CTRL_qqq_1.5x_static', 'blind_1y', np.float64(-2.8970620225510664), 1.0)]

## MDE (house rule — read NOT SUPPORTED against this)

| book | window | n | MDE TV ann (t≥2, 80% power) |
|---|---|---|---|
| vol_managed_qqq | blind_1y | 223 | +12.9% |
| vol_core_svxy | blind_1y | 223 | +11.5% |
| dual_momentum_gem | blind_1y | 223 | +11.3% |
| momentum_concentrated | blind_1y | 223 | +19.0% |
| trend_vol_qqq | blind_5y | 1227 | +20.6% |
| defensive_ensemble | blind_5y | 1227 | +5.4% |
| dual_momentum_gold | blind_5y | 1227 | +11.2% |

## Controls + parent

| series | window | γ | t_γ | t_γ lag21 | TV ann |
|---|---|---|---|---|---|
| CTRL_spy_buyhold | blind_1y | -0.04 | -0.14 | -0.16 | -0.07% |
| CTRL_qqq_buyhold | blind_1y | +0.00 | +0.00 | +0.00 | +0.00% |
| CTRL_qqq_1.5x_static | blind_1y | -0.04 | -2.90 | -3.03 | -0.07% |
| PARENT_qqq_sma200_2x | blind_1y | -23.09 | -2.06 | -2.29 | -36.95% |
| CTRL_spy_buyhold | blind_5y | +0.48 | +3.13 | +3.59 | +1.52% |
| CTRL_qqq_buyhold | blind_5y | +0.00 | +0.02 | +0.02 | +0.00% |
| CTRL_qqq_1.5x_static | blind_5y | -0.01 | -1.47 | -1.27 | -0.05% |
| PARENT_qqq_sma200_2x | blind_5y | -3.84 | -1.19 | -1.70 | -12.10% |

## Books (blind windows; leg 3 leverage-normalized vs parent)

| book | win | γ | t_γ | lag21 | TV | α | α+TV stress | MDE TV | leg3 | dist? | PIT-QQQRES t_γ | pass |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| vol_managed_qqq | 1y | -7.90 | -2.79 | -3.20 | -12.65% | +14.56% | -0.66% | +12.9% | F | y | -2.79 | — |
| vol_core_svxy | 1y | -8.10 | -3.19 | -3.83 | -12.96% | +15.39% | -1.23% | +11.5% | F | y | -3.19 | — |
| dual_momentum_gem | 1y | +1.78 | +0.72 | +0.87 | +2.85% | +14.00% | +14.43% | +11.3% | P | y | +0.72 | — |
| momentum_concentrated | 1y | -8.69 | -2.08 | -1.74 | -13.91% | +5.81% | -8.09% | +19.0% | F | y | -2.08 | — |
| trend_vol_qqq | 5y | -2.82 | -1.23 | -1.82 | -8.90% | +18.53% | +8.00% | +20.6% | F | NO | -1.23 | — |
| defensive_ensemble | 5y | +0.49 | +0.81 | +0.78 | +1.53% | +5.38% | +3.01% | +5.4% | P | y | +0.81 | — |
| dual_momentum_gold | 5y | +1.60 | +1.28 | +1.41 | +5.03% | +8.29% | +11.56% | +11.2% | P | y | +1.28 | — |

## Full-history M2T (IN-SAMPLE context — no claim may cite this)

| book | γ | t_γ | TV ann |
|---|---|---|---|
| vol_managed_qqq | -0.33 | -0.21 | -1.10% |
| vol_core_svxy | -0.52 | -0.25 | -1.75% |
| dual_momentum_gem | -0.02 | -0.04 | -0.07% |
| momentum_concentrated | +0.26 | +0.30 | +0.87% |
| trend_vol_qqq | -0.84 | -0.46 | -2.85% |
| defensive_ensemble | -0.24 | -0.59 | -0.81% |
| dual_momentum_gold | -0.21 | -0.18 | -0.71% |

## Notes (story, post-run)

**Verdict NOT SUPPORTED, overdetermined.** Two independent routes give the same answer:
(a) 0/7 books pass the timing-positive conjunction; (b) the pre-committed control
adjudication (disposition 6) fired — CTRL_qqq_1.5x_static blind-1y has t_γ = −2.90
with stationary-bootstrap p ≈ 1.0, i.e. a genuinely nonzero NEGATIVE γ on a static
book. Diagnosis: not pipeline plumbing and not beta asymmetry — the control's own
daily-rebalance cost term (cost ∝ |r|) is a concave drag, TM-visible at TV ≈ −0.07%/yr
(economically nil, statistically resolvable). Model limitation recorded; gate defaults
to NOT SUPPORTED, which the book results independently confirm.

Mechanism finding worth keeping: in the blind year the three flagged books show
SIGNIFICANTLY NEGATIVE market convexity beyond M2 (vol_managed_qqq γ t −2.79,
vol_core_svxy −3.19, momentum_concentrated −2.08) offset by positive level α
(+14–15%/yr), netting to ≈ 0 after the financing haircut (−0.7%, −1.2%, −8.1%).
That is the short-gamma / premium-harvesting signature — the OPPOSITE of timing
convexity. The naive trend parent was itself whipsawed concave in the blind year
(γ −23, t −2.06). Books with positive γ (gem +0.72, defensive +0.81, gold +1.28)
are all deep inside noise.

Panel-state note (transparent deviation from disposition 9's wording): the gate ran on
the CORRECTED panel (post Memorial-Day phantom-row fix; n = 223/1,227, four more FF
days than the parent attribution's 219/1,223). Disposition 9 was drafted against the
audit's as-frozen assumption; the correction of record (TRIAL_LEDGER.md,
memos/panel-phantom-row-correction.md) and Kristen's program directive ("use corrected
panels for new analysis") supersede it. The books' frozen results were themselves
regenerated post-fix, so integrity is consistent.

Disclosure per disposition 5/6: CTRL_spy_buyhold blind-5y shows t_γ = +3.13 but its
stationary-bootstrap p fell inside (0.05, 0.95) → adjudicated as NW-size noise per the
pre-committed rule (the reviewer's Monte Carlo predicted exactly this ~2–3× size
distortion on squared regressors); γ = +0.48, TV +1.5%/yr, consistent with a small
SPY-vs-CRSP-market composition artifact. PIT-QQQRES robustness (disposition 8):
identical t_γ to two decimals for every book — the F2 look-ahead does not move γ.

Read the verdict against the MDE table: hunt-1 books could only have shown TV ≥
+11–19%/yr (implausibly large); the powered test is the 5y books, where TV ≥ +5.4%/yr
(defensive_ensemble) was detectable and nothing appeared. Scope: TM-visible timing
only — vol-space convexity, discrete Henriksson–Merton switching, and horizon-
mismatched timing are invisible to a single daily (Mkt−RF)² term by design.
