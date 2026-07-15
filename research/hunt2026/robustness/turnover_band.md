# Turnover-band sweep — vol-managed family (EXP-2026-07-14-turnover-band)

Portfolio-level L1 no-trade band overlaid on the frozen specs; 12 registered variants, all reported. Deltas are vs each book's own band=0 baseline on shared rolling 12m windows (quarterly steps, full panel). Prereg: preregistrations/turnover-band-2026-07-14.md.

## vol_managed_qqq — baseline turnover/d 0.0301, cost drag 15 bps/yr

| band | med 12m Δ (bps) | windows | turnover cut | cost saved (bps/yr) | full-period Δnet (pp) |
|---|---|---|---|---|---|
| 0.01 | +0.0 | 46 | 0% | +0.0 | +0.00 |
| 0.02 | +0.0 | 46 | 0% | +0.0 | +0.00 |
| 0.05 | +0.0 | 46 | 0% | +0.0 | +0.00 |
| 0.10 | -42.5 | 46 | 18% | +2.8 | -66.96 |
| 0.20 | +15.5 | 46 | 35% | +5.3 | +43.11 |
| 0.40 | +57.0 | 46 | 58% | +8.9 | +7.29 |

**vol_managed_qqq verdict (per prereg rule): helps**

## vol_core_svxy — baseline turnover/d 0.0741, cost drag 37 bps/yr

| band | med 12m Δ (bps) | windows | turnover cut | cost saved (bps/yr) | full-period Δnet (pp) |
|---|---|---|---|---|---|
| 0.01 | +0.8 | 46 | 1% | +0.4 | +3.12 |
| 0.02 | -3.8 | 46 | 3% | +1.0 | -17.19 |
| 0.05 | +24.5 | 46 | 7% | +2.8 | +64.34 |
| 0.10 | +29.3 | 46 | 11% | +4.2 | +49.94 |
| 0.20 | +32.0 | 46 | 17% | +6.3 | +49.92 |
| 0.40 | +2.3 | 46 | 34% | +12.7 | -251.43 |

**vol_core_svxy verdict (per prereg rule): indeterminate**

## Family verdict: **mixed** (vol_managed_qqq: helps, vol_core_svxy: indeterminate)

Per the prereg kill condition this is one run of the registered grid — no finer grids, no re-tuned band definitions. Any adoption of a band value is a separate Stage-4 decision for Kristen carrying n_trials=12 selection accounting.

## Story (why the mechanical verdict overstates the result)

- **The deltas are NOT the hypothesized mechanism.** The prereg bounded the cost-savings effect at the published cost drag (≤ 15/37 bps/yr), and the measured cost saved lands exactly there (+3 to +13 bps/yr). But the median 12m deltas that trip the verdict rule are 5–10x larger than the cost saved — they come from exposure-path divergence (a delayed rebalance is accidentally *different vol timing*), not from trading less. Same-sign evidence: the response is non-monotone (vol_managed_qqq: −42.5 bps at 0.10 → +57 at 0.40; vol_core_svxy: +32 at 0.20 → −251 pp full-period at 0.40). A real cost effect would be small, smooth, and plateau-shaped; timing luck swings sign between adjacent grid points.
- **vol_managed_qqq's internal 0.05 per-ticker band already absorbs the overlay below 0.10** — 0% turnover cut, identical series. The frozen spec already banks the genuinely available cost saving; there was little left to harvest.
- **Bottom line: the real, mechanism-attributable effect is ≈ the cost saved — worth at most ~+13 bps/yr on vol_core_svxy — and no band value is stable enough to adopt.** The 'helps'/'indeterminate' verdicts are the rule firing on timing noise. Recommendation: no live change, queue item closed as run; the cheap net-return improvement this experiment hunted does not exist at 2 bps/side ETF costs beyond what the specs already do.
