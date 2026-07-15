# Pre-registration — does a portfolio-level no-trade band improve net returns on the vol-managed family?

### EXP-2026-07-14-turnover-band

**Hypothesis** (one falsifiable sentence, mechanism included):
Daily vol-targeting emits many small weight adjustments with near-zero information content,
so holding the last-adopted book until the frozen spec's target drifts more than a band in
L1 weight units cuts turnover costs by more than the tracking loss it introduces, improving
net returns on vol_managed_qqq and vol_core_svxy.

**Layer touched** (exactly one) + registered baseline:
Layer C — portfolio-construction overlay only. The frozen specs are untouched and are the
baselines (vol_managed_qqq keeps its internal per-ticker 0.05 tolerance band; the overlay is
additional and external). Band filter operates on the spec's raw target rows BEFORE
harness.run's gross-cap scaling: adopt the new target row only when
`sum(|target_t − last_adopted|) > band`, else re-emit last_adopted; last_adopted starts at
the zero row so warm-up stays flat.

**Alpha type tag**: portfolio

**Expected result** (numeric, on which evaluator):
Rolling 12m windows / quarterly steps (walk_forward.rolling_windows) on the full
panel_2005 history, plus full-period harness.run stats for context. The ceiling is the
published cost drag — 18 bps/yr (vol_managed_qqq) and 39 bps/yr (vol_core_svxy) — so
expected: small bands (0.02–0.10) cut avg daily turnover 20–60% and lift the median 12m net
delta (banded − baseline) by +2 to +15 bps, with vol_core_svxy gaining roughly 2× 
vol_managed_qqq; large bands (≥0.20) degrade as tracking loss dominates.

**Alternative result** (what the world looks like if the hypothesis is false):
All bands produce median 12m deltas within ±5 bps (at 2 bps/side ETF costs the drag is too
small for banding to matter) — or uniformly negative (the vol-timing signal decays within a
day, so delaying trades costs more than executing them).

**Registered variants** (12, all reported, nothing cherry-picked):
band ∈ {0.01, 0.02, 0.05, 0.10, 0.20, 0.40} L1 × {vol_managed_qqq, vol_core_svxy},
plus the two band=0 baselines. Baseline gates before any variant counts: (a) band=0
reproduces the frozen spec's net series exactly; (b) recomputed blind-window Sharpe matches
the published results JSON (tol 0.01).

**Decisive statistic (pre-committed)**: per (book, band): median across shared 12m windows
of (banded − baseline) window net return; % reduction in avg daily turnover; ann. cost
saved. Verdict rule per book:
- "banding helps" if ≥1 registered band has median delta ≥ +5 bps AND turnover reduction ≥ 20%;
- "flat" if every |median delta| < 5 bps;
- "harmful" if every median delta ≤ 0.
Family verdict = both books agree, else "mixed". 

**Failure / kill condition** (pre-committed; includes the stop-iterating rule):
One run of the 12 registered variants. No finer band grids, no per-book band re-tuning, no
alternative band definitions (per-ticker, %-of-gross, time-based) after seeing results. If
flat or harmful → FAILURES.md entry and the queue item closes. Even if "banding helps",
NO live spec changes from this run — adopting any band value is a separate Stage-4 decision
for Kristen, and the adopted value would carry the selection-over-grid accounting
(n_trials=12) into its own evaluation.

**Trial-ledger row**: TRIAL_LEDGER.md — Robustness experiments table, added in the same
commit.

**Derived from prior holdout results?** YES — adaptive loop: the experiment targets books
promoted by the blind evaluations and its expected-effect sizing uses their published
cost-drag/turnover numbers. Flagged in the ledger row.

---
**Result** (filled after the run, never edited above this line): MIXED per the mechanical
rule (vol_managed_qqq "helps", vol_core_svxy "indeterminate") — but the mechanism is NOT
supported. Cost saved landed inside the pre-registered ceiling (+3 to +13 bps/yr) while the
medians tripping the rule were 5–10x larger and non-monotone across adjacent bands
(vmq −42.5 bps at 0.10 → +57 at 0.40; svxy −251 pp full-period at 0.40) — exposure-path
timing noise, not cost savings. vol_managed_qqq's internal 0.05 band already absorbs the
overlay below 0.10 (0% turnover cut). No adoptable band value; no live change proposed;
queue item closed. Full tables + story: robustness/turnover_band.md. Both baseline gates
passed (band=0 exact reproduction; holdout Sharpe == published).
