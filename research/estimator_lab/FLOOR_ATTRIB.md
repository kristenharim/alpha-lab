# Stage 2 — alpha-book attribution (known / sector-mean / vetted residual)

Prereg: FLOOR_ATTRIB_MEMO.md rev 2 (frozen). 14 primary windows, starts 2022-11-21 → 2026-03-02. Alphas per window, sign-flip permutation (10k joint draws). SELECTION-TAINTED history (n_trials ≥ 18, floor); live OOS excluded; 'industry' = 11-GICS-sector-MEAN controls; residual controls in 4/14 windows — SPOT-CHECKS, not robustness; L4 survival is NOT evidence of absence of residual common risk.

## Verdict (pre-committed): **SUCCESS**
- plumbing (bench beta 1.19, R² 0.94, |t₂| gate): PASS
- SPY null book benign: PASS
- expected false rule-5 count under joint null (upper bound, DSR/stress omitted): 0.33 of 7

## Attribution (annualized window-mean alphas; permutation p)

| book | class | L1 | L2 +FF | L3 +sec | L4 +res | α₄ stress | ρSVXY | DSR18/36 | gross | maxDD |
|---|---|---|---|---|---|---|---|---|---|---|
| defensive_ensemble | known-factor-premium | +20.3% (0.01) | +2.8% (0.61) | +1.6% (0.77) | +1.9% (0.75) | -2.6% | -0.05 | 0.87/0.80 | 1.85 | -26% |
| dual_momentum_gem | known-factor-premium | +30.4% (0.00) | -2.0% (0.79) | -2.5% (0.63) | -2.0% (0.70) | -3.7% | -0.04 | 0.73/0.62 | 1.32 | -41% |
| dual_momentum_gold | known-factor-premium | +42.2% (0.01) | +20.4% (0.21) | +10.1% (0.41) | +10.8% (0.38) | +9.0% | -0.07 | 0.87/0.80 | 1.33 | -41% |
| momentum_concentrated | known-factor-premium | +17.0% (0.03) | -5.3% (0.25) | -5.0% (0.25) | -4.3% (0.35) | -4.3% | +0.01 | 0.52/0.41 | 0.97 | -31% |
| trend_vol_qqq | known-factor-premium | +29.3% (0.01) | -3.4% (0.47) | -5.4% (0.37) | -5.1% (0.40) | -7.0% | +0.00 | 0.78/0.68 | 1.37 | -31% |
| vol_core_svxy | known-factor-premium | +35.1% (0.00) | +1.3% (0.71) | +1.8% (0.60) | +2.3% (0.51) | -1.1% | +0.12 | 0.82/0.74 | 1.65 | -34% |
| vol_managed_qqq | known-factor-premium | +33.0% (0.00) | -1.5% (0.65) | -2.6% (0.60) | -2.3% (0.64) | -4.7% | -0.00 | 0.80/0.71 | 1.46 | -35% |
| bench_qqq_buyhold | known-factor-premium | +24.5% (0.00) | +1.6% (0.54) | +0.3% (0.82) | +0.4% (0.79) | +0.4% | -0.04 | 0.82/0.73 | 1.00 | -35% |
| _spy_null | known-factor-premium | +16.0% (0.00) | -0.4% (0.26) | +0.3% (0.47) | +0.3% (0.41) | +0.3% | -0.01 | 0.76/0.66 | 1.00 | -34% |

## Stability (L4 ann.)

| book | half1 | half2 | hi-vol | lo-vol | sign-frac | suppression |
|---|---|---|---|---|---|---|
| defensive_ensemble | -2.8% | +6.7% | -5.6% | +9.4% | 0.79 | — |
| dual_momentum_gem | -0.0% | -3.9% | -4.0% | +0.1% | 0.71 | — |
| dual_momentum_gold | +1.0% | +20.6% | +4.8% | +16.8% | 0.64 | — |
| momentum_concentrated | -0.9% | -7.6% | -8.7% | +0.2% | 0.57 | — |
| trend_vol_qqq | +1.3% | -11.4% | -10.7% | +0.6% | 0.50 | — |
| vol_core_svxy | +10.5% | -5.9% | +1.9% | +2.8% | 0.57 | — |
| vol_managed_qqq | +3.8% | -8.4% | -5.2% | +0.6% | 0.57 | — |
| bench_qqq_buyhold | +1.6% | -0.8% | +2.1% | -1.3% | 0.57 | — |
| _spy_null | +0.4% | +0.3% | +0.8% | -0.1% | 0.57 | — |

## Provenance

- defensive_ensemble: promoted L3; hunt-2 ADAPTIVE
- dual_momentum_gem: watch; whipsaw-fragile
- dual_momentum_gold: watch; HINDSIGHT-DISCOUNTED (regime artifact)
- momentum_concentrated: sleeve-only; WF-demoted F-015; stock book (survivorship-heavy)
- trend_vol_qqq: promoted L3; hunt-2 ADAPTIVE
- vol_core_svxy: promoted L3; hunt-1; SVXY ETP-menu survivorship
- vol_managed_qqq: promoted L3; hunt-1
- bench_qqq_buyhold: control
- _spy_null: control

## Story

The SUCCESS verdict is a plumbing verdict; the classifications fired correctly under
the frozen rules. The adversarial review then established that the frozen rules answer
a NARROWER question than the label names suggest, and the prescribed minimum
experiment (run read-only, run_floor_attrib_diag.py) quantified the gap:

1. **The design is structurally blind to timing alpha — the books' main claim.** Per-
   window OLS refits betas every 63 days, so cross-window beta variation (measured:
   vol_managed_qqq 1.31→3.21, dual_momentum_gold −4.09→+2.48) is absorbed into
   "factor exposure." A perfect vol-timer and naive levered QQQ get the same
   signature (L1 significant, L2 ≈ 0). "Known-factor-premium" was the only reachable
   label for timing books, whether or not the timing works. This also dissolves any
   tension with hunt2026's walk-forward +13pp-vs-SPY: different objects; Stage 2
   licenses NO statement about the walk-forward claims.
2. **Static-beta full-span alphas (882 obs, 63d circular-block bootstrap):**
   defensive_ensemble +9.1% [−1.9, +19.2] · dual_momentum_gem +5.3% [−8.6, +21.0] ·
   dual_momentum_gold **+30.7% [+2.5, +57.3] SIGNIFICANT** · momentum_concentrated
   −3.5% [−12.1, +4.6] · trend_vol_qqq +11.3% [−3.0, +23.5] · vol_core_svxy +9.6%
   [−1.9, +19.1] · vol_managed_qqq +9.0% [−2.1, +17.3] · bench QQQ +4.5% [−1.2, +9.8].
   Reading: the static-vs-windowed delta (~+9–11%/yr for the vol/trend books) is the
   timing channel's POINT ESTIMATE, unproven at 3.5 years of one bull regime. Gold's
   significance survives the bootstrap but not its provenance (hindsight-discounted,
   regime artifact per hunt2026 robustness) — unadjudicated, not validated.
3. **The VRP override was unfireable as frozen:** only 21.9% of SVXY's daily variance
   survives the L3 projection, capping the frozen raw-SVXY correlation at √0.219 ≈
   0.47 < the 0.5 threshold — even a 100% static SVXY book could not trip it; the
   prereg's "expected to trip by construction" was wrong under its own definition
   (fourth rule-drafting error; the pattern is bars/rules frozen without a
   reachability check). Corrected statistic (vs L3-residualized SVXY):
   vol_core_svxy +0.261, vol_managed_qqq +0.006, trend_vol_qqq +0.012 — a real but
   non-dominant VRP tilt in vol_core_svxy; the VRP question remains open.
4. **Class-2 label honesty split:** (a) genuinely-no-hint — momentum_concentrated
   (L2 −5.3%/yr, static −3.5%, hi-vol L4 −8.7%, WF-demoted −4.6pp: every arrow
   negative), dual_momentum_gem (≈0 to negative everywhere); (b) point-estimates-
   positive-but-unproven — the four vol/trend books; (c) unadjudicated at this sample
   size — dual_momentum_gold (windowed L2 SE ≈ 15%/yr; 80% power needs ≈ 43%/yr).
5. Permutation caveats (pre-stated + confirmed): contiguous windows share vol regimes
   → independent sign-flips are mildly anti-conservative; affects only L1 gates every
   book clears (sign-fractions 0.71–0.93). CSV gap: L1 sign-fraction column omitted
   (verified out-of-band ≥ 0.60 for all).

**Transferable lesson:** an attribution design must match the strategy class — window-
refit betas measure selection-era intra-window alpha and CANNOT see regime-conditional
beta, which is the entire thesis of vol/trend books. And every frozen threshold needs
a reachability check against its own construction (the VRP ceiling, the a_match null,
the industry-control dof floor: same defect, three appearances).

## Research log (Stage 2)

- Verdict: SUCCESS (plumbing); all 7 books classify known-factor-premium under the
  frozen ladder; no book reaches the residual rungs; expected false rule-5 count 0.33,
  observed 0.
- Supported: raw returns are overwhelmingly factor exposure in-window; intra-window
  FF-alpha ≈ 0 for six books (point estimates −5.3% to +2.8%/yr); momentum_concentrated
  and dual_momentum_gem show no hint of value beyond exposure; controls clean.
- Not supported: any claim about TIMING alpha (design-blind; static-beta point
  estimates +9–11%/yr unproven); any VRP adjudication (rule unfireable as frozen;
  corrected ρ = 0.26 for vol_core_svxy); any statement about hunt2026 walk-forward
  claims; gold's +30.7% static alpha as validated (provenance-compromised).
- Validity: 14 contiguous quarters 2022-11→2026-05, one bull regime; selection-tainted
  history (n_trials ≥ 18 floor); financing haircut applied; survivorship heaviest on
  momentum_concentrated; residual controls were spot-checks (4/14 windows).
- Next: single best action in the final program memo (ATTRIB_PROGRAM_MEMO.md).
