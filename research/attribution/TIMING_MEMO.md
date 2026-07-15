# Timing-alpha program — negative-result memo (2026-07-14)

Program: test whether the existing vol/trend/dual-momentum signals add value by
changing exposure to known premia at better times than fixed-exposure benchmarks.
First mandatory action (the mechanism gate) executed per the frozen prereg
`research/hunt2026/preregistrations/timing-tm-2026-07-14.md` on the already-run
frozen attribution machinery. Pre-committed route on a negative gate: STOP broad
timing optimization. This memo is that stop.

## Lead with the measurement limits (mandated)

| book | blind window | n | minimum detectable timing value (t≥2, 80% power) |
|---|---|---|---|
| vol_managed_qqq | 1y | 223 | +12.9%/yr |
| vol_core_svxy | 1y | 223 | +11.5%/yr |
| dual_momentum_gem | 1y | 223 | +11.3%/yr |
| momentum_concentrated | 1y | 223 | +19.0%/yr |
| trend_vol_qqq | 5y | 1,227 | +20.6%/yr |
| defensive_ensemble | 5y | 1,227 | +5.4%/yr |
| dual_momentum_gold | 5y | 1,227 | +11.2%/yr |

A realistic TM-visible timing effect is order +1–3%/yr. The 1-year books were
therefore a foregone non-detection at any plausible effect size (~15% power); the
powered part of the test is the 5-year books — best case defensive_ensemble, where
anything ≥ +5.4%/yr was detectable and nothing appeared. Scope: the gate sees
TM-visible timing only (daily market-return convexity beyond FF5+MOM+TSMOM+QQQRES);
vol-space convexity, discrete regime switching, and horizon-mismatched timing are
invisible to it by design.

## 1. Timing-alpha verdict per book (the three permitted labels)

| book | verdict | key numbers (blind window) |
|---|---|---|
| vol_managed_qqq | no evidence of timing alpha | γ t −2.79 (NEGATIVE convexity), α +14.6%, α+TV stressed −0.7% |
| vol_core_svxy | no evidence of timing alpha | γ t −3.19, α +15.4%, stressed −1.2% |
| dual_momentum_gem | no evidence of timing alpha | γ t +0.72 (noise), MDE 11.3% |
| momentum_concentrated | no evidence of timing alpha | γ t −2.08, stressed −8.1% |
| trend_vol_qqq | no evidence of timing alpha | γ t −1.23, MDE 20.6% (gross 2x inflates SE) |
| defensive_ensemble | no evidence of timing alpha | γ t +0.81 at the best-powered seat (MDE 5.4%) |
| dual_momentum_gold | no evidence of timing alpha | γ t +1.28, TV +5.0% < MDE 11.2% |

No book reaches "promising but unproven"; "robust" was never reachable without
forward confirmation by construction.

## 2–4. Fixed-replication vs strategy, timing tests, parents and placebos

The full tables live in `TIMING_GATE.md` + `timing_gate.csv` (this gate) and
`ATTRIBUTION.md` (levels): fixed-factor replication (M2) leaves blind-window level
alphas of −7.5% to +15.8%/yr, none with t ≥ 2; the TM timing term adds no positive
convexity anywhere; the naive trend parent itself was whipsawed concave in the blind
year (γ −23, t −2.06), so no book failed the parent comparison to a *skilled* parent —
they failed on their own numbers. Placebos/controls: SPY/QQQ clean; the two flagged
control t-stats were adjudicated by the pre-committed bootstrap rule (one NW-size
artifact; one economically-nil cost-drag concavity, TV −0.07%/yr, recorded as a
control model limitation).

## 5. Regime breakdown

Not run beyond the blind/full split — the gate stopped the program before Phase 2's
regime battery, per the pre-committed route. Full-history (in-sample, context only)
γ is ≈ 0 for every book, so there is no in-sample convexity that a regime split
could resurrect.

## 6. Costs, financing, turnover

Harness costs (10/2 bps per side) are inside every number. Financing haircut
max(gross−1,0)·(RF+50bps) turns the two vol books' positive blind-year level alphas
(+14.6%, +15.4%) into ≈ 0 (−0.7%, −1.2%) once their negative timing value is added —
at gross 1.85–1.65 the free-financing illusion is the books' entire apparent edge.

## 7. What mechanism, if any, creates value

The blind-year decomposition is the useful discovery: the vol books earn a POSITIVE
LEVEL (carry-like, +14–15%/yr) and pay for it with NEGATIVE market convexity
(TV −13%/yr) — the signature of harvesting a short-gamma/variance-style premium, not
of timing. What looked like "maybe timing alpha" in the earlier windowed attribution
is, under a design that can see convexity, premium harvesting whose net stressed
value in the claim-bearing year was ≈ 0. Nothing in any book shows the convex
signature timing skill would produce.

## 8. One recommended next action

**Demote / stop the timing-alpha hypothesis for the existing signals.** Do not tune
lookbacks, thresholds, or rebalance frequencies — the mechanism gate says there is
nothing there to refine at any detectable size, and Phase 3 is closed by rule. If
timing remains interesting, it needs a NEW data hypothesis, and the gate's own
blind-spot list says where to look first: vol-space convexity (a variance-swap-like
test of the vol books against realized-vs-implied vol, needs option/VIX-term data) —
that is a new experiment with its own prereg, not a refinement of this one.

Forward paper trading of the books continues regardless (it tests the LEVEL claim,
which the attribution left at "factor exposure + free-financing illusion"); nothing
in this program changes live allocations.

## Process trail

Prereg frozen before code (incl. 9 reviewer dispositions: leverage-normalized parent
leg, MDE table mandated, strong-tier restricted to 5y, size-distortion disclosure,
control-failure adjudicator, PIT-QQQRES robustness — which came back identical to
2 decimals). Statistical + integrity reviews pre-execution; controls adjudicated by
the pre-committed rule; corrected (post-phantom-row) panels used per program
directive, deviation from disposition 9's wording disclosed in TIMING_GATE.md notes.
Stamped via run_manifest (variant `timing_gate`).
