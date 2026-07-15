# Final memo — two-stage attribution program (2026-07-14)

Program: (Stage 1) FF+industry residual-risk model → vetted residual-factor panel;
(Stage 2) nested attribution of the 7 live hunt2026 books. Every experiment
preregistered, 3-reviewer-checked, adversarially reviewed; full trail:
FLOOR_INDUSTRY_MEMO/FLOOR_INDUSTRY (+ errata) · FLOOR_ATTRIB_MEMO/FLOOR_ATTRIB
(+ story) · diagnostics runners. Nothing here is a proven-alpha claim.

## 1. Bottom-line classification per book

Frozen-ladder label first; honest reading (post-adversarial) second — the ladder's
per-window design measures INTRA-window alpha and is structurally blind to
cross-window beta TIMING, which is these books' actual thesis.

| book | frozen label | honest reading |
|---|---|---|
| vol_managed_qqq | known-factor premium | Factor exposure; intra-window alpha ≈ 0; timing channel +9.0%/y point est., UNPROVEN (CI −2.1 to +17.3) |
| vol_core_svxy | known-factor premium | Same (+9.6%/y ns) + real but non-dominant VRP tilt (corrected ρ 0.26); VRP question open — the frozen override was unfireable |
| trend_vol_qqq | known-factor premium | Factor exposure; timing +11.3%/y ns |
| defensive_ensemble | known-factor premium | Factor exposure; timing +9.1%/y ns |
| dual_momentum_gem | known-factor premium | Factor exposure, NO HINT of value beyond it (≈0 to negative everywhere) |
| momentum_concentrated | known-factor premium | Factor exposure with NEGATIVE selection-era alpha (L2 −5.3%/y, static −3.5%/y, hi-vol −8.7%/y; consistent w/ its WF demotion) |
| dual_momentum_gold | known-factor premium | UNADJUDICATED: windowed test powerless (needs ≈43%/y for 80% power); static-beta alpha +30.7%/y [+2.5, +57.3] IS significant but provenance-compromised (hindsight-designed gold menu, regime artifact) — the one book where more data could change the answer |

In her requested vocabulary: no book earns "promising but unproven residual alpha";
none shows "hidden residual-risk exposure" (the residual rungs were never reached);
gold is best described as "insufficient evidence" with an asterisk.

## 2. Factor-control table (Stage-1 status of the risk model)

| control layer | status |
|---|---|
| FF3+MOM (known) | Working as designed. Residual PC1 = leakage footprint (high D 0.49, lowest floors) — the detector's Phase-4 job, confirmed on real data. Low PC1 floors are never trustworthy-as-genuine. |
| Industry (11 GICS sector dummies, cross-sectional) | Removes sector-MEAN risk (null-relative: 60.6% of excess sector association — passes its control's spirit; the recorded FAIL isolates to a raw-ratio metric bug). NOT finer than sector means: sub-sector/theme vs vol-regime coupling UNRESOLVED. Non-PIT sector map (2023-03 GICS restructure backfilled pre-2023 windows). |
| Residual statistical factors (label-4 vetted panel) | 5 slots / 4 of 14 windows / 0 recurrent / exact-permutation p 0.21–0.51: spot-checks only, ≈ nil evidential value as controls; the gate is exclusion-biased by design. Rule "hidden residual-risk" was unreachable with this panel. |
| Detectability & leakage machinery | Closed-form C4 is NOT production-valid on real residuals (false-pass ~14%; isotropic margin consumed) — use the empirical per-rank shuffled null (as both arms did). Leakage D_j stays a CONTINUOUS score; provenance is never claimed. |

## 3. Before/after attribution (annualized window-mean alpha; permutation p; 14 windows 2022-11→2026-05)

| book | L1 raw | L2 +FF | L3 +sector | L4 +residual | α₄ stressed | static-beta α (context) |
|---|---|---|---|---|---|---|
| vol_managed_qqq | +33.0% (.00) | −1.5% (.65) | −2.6% (.60) | −2.3% (.64) | −4.7% | +9.0% ns |
| vol_core_svxy | +35.1% (.00) | +1.3% (.71) | +1.8% (.60) | +2.3% (.51) | −1.1% | +9.6% ns |
| trend_vol_qqq | +29.3% (.01) | −3.4% (.47) | −5.4% (.37) | −5.1% (.40) | −7.0% | +11.3% ns |
| defensive_ensemble | +20.3% (.01) | +2.8% (.61) | +1.6% (.77) | +1.9% (.75) | −2.6% | +9.1% ns |
| dual_momentum_gem | +30.4% (.00) | −2.0% (.79) | −2.5% (.63) | −2.0% (.70) | −3.7% | +5.3% ns |
| momentum_concentrated | +17.0% (.03) | −5.3% (.25) | −5.0% (.25) | −4.3% (.35) | −4.3% | −3.5% ns |
| dual_momentum_gold | +42.2% (.01) | +20.4% (.21) | +10.1% (.41) | +10.8% (.38) | +9.0% | +30.7% SIG* |
| bench QQQ (control) | +24.5% (.00) | +1.6% (.54) | +0.3% (.82) | +0.4% (.79) | +0.4% | +4.5% ns |

L4 column = residual controls in only 4/14 windows (spot-checks). α₄ stressed =
financing haircut max(gross−1,0)×(RF+50bps). *significant in-sample, provenance-
compromised. Expected false "promising" count under the joint null: 0.33; observed 0.

## 4. Supported · not supported · next action

**Supported.** The books' raw returns (+17–42%/y over the span) are overwhelmingly
known-factor exposure; intra-window FF-alpha is ≈ 0 for six of seven; two books
(momentum_concentrated, dual_momentum_gem) show no hint of value beyond exposure, with
momentum_concentrated's point estimates uniformly negative. The risk-model pipeline
itself behaved: controls passed, leakage detector caught PC1 exactly as the sims
predicted, sector-mean removal did its job.

**Not supported.** Any timing-alpha verdict (the design is blind to it; +9–11%/y
point estimates, all CIs span zero); any VRP adjudication (frozen rule unfireable;
corrected ρ 0.26); gold's static +30.7% as validated alpha (hindsight provenance,
one regime, selection-tainted era); any statement about hunt2026's walk-forward
+13pp-vs-SPY claims (different object, different span); "not industry risk" for the
residual factors (only "not annihilated by sector-MEAN projection"); any
genuine/leaked provenance claim about residual factors.

**Single best next action.** Run the already-frozen sibling blind-window attribution
(research/hunt2026/preregistrations/factor-attribution-2026-07-14.md) EXTENDED with
one market-timing term (Treynor–Mazuy quadratic or signal-conditioned beta) on the
full 2014→2026 span with its claim-bearing holdout — it directly adjudicates the
timing channel this program proved its own design cannot see, at zero new-data cost,
and its claim-bearing windows dodge most of the selection taint. (Research-side
runner-up, hers to take to the lab as theory: C4's edge under heteroskedastic noise —
the empirical-null replacement is now validated practice in two phases.)

**Process notes for the record.** Four rule-drafting defects surfaced this program
(industry-control raw-ratio bar, a_match null, VRP ceiling, plus Phase 6's span
mislabel); the shared root is freezing thresholds without a reachability/null check
against their own construction — worth one standing line in the estimator_lab process
rules: "every frozen numeric bar ships with its null value and a reachability check."
Stage-1's FAIL verdict was honored as recorded (diagnosis only, no re-verdict); the
proceed decision was documented as a consequence-override and survived adversarial
scrutiny on content.
