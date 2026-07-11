# Pre-registration — forward-only earnings-surprise IC (EXP-IC-EARNINGS-FWD)

### EXP-2026-07-10-ic-earnings-fwd

**Hypothesis** (one falsifiable sentence, mechanism included):
Positive standardized earnings surprise (SUE = (actual − estimate) / scale, scale =
trailing std of the symbol's last up-to-4 surprises when ≥2 are available, else |estimate|)
predicts positive 5/20/60-day forward returns cross-sectionally among S&P 500 members,
because post-earnings-announcement drift (underreaction to fundamental news) has not been
fully arbitraged at the large-cap horizon.

**Layer touched** (exactly one) + registered baseline:
Layer A — economic / market: a NEW information source (verified point-in-time earnings
surprises from Finnhub, collected forward from 2026-07-10). Baseline = zero-IC null on the
same event panel. No estimator, portfolio, or execution layer is touched; the output is a
rank IC, not a strategy.

**Alpha type tag**: market

**Data honesty constraints (pre-committed)**:
- Forward-only. The Finnhub free tier has no usable calendar history and only 4 quarters
  of surprise history; those historical surprise rows MAY be stored but are flagged
  `point_in_time: false` (stale-knowledge risk: estimates/actuals as known today, not as
  known then) and are EXCLUDED from the primary IC test. No historical backfill is ever
  claimed as evidence.
- Events enter the panel only when pulled on/after their report date with
  `point_in_time: true`. Dedupe on (symbol, period).
- Universe = S&P 500 membership per the last row of panel_2005.parquet's `member` field
  at collection time.

**Primary test (pre-committed, runs as data accrues via earnings_collect.py --report)**:
Spearman rank IC of SUE vs forward total return over 5, 20, and 60 trading days
(entry = first close on/after report_date reaction is observable, i.e. next session close),
pooled across events, with a Newey-West-free simple t-stat on per-event contribution
(t = IC · sqrt(n−2) / sqrt(1−IC²)). Decision horizon = 20d.

**Secondary hypothesis (pre-committed now)**:
Day+1 confirmation — close ≥ open in the first session after a positive surprise —
strengthens the signal: the confirmed-positive-SUE subset has higher 20d rank IC than the
unconfirmed subset.

**Conditioning rules (pre-registered NOW, not discovered later — the only slices that may
ever be reported)**:
1. Sector-relative SUE: demean SUE within GICS sector (sectors.parquet) before ranking.
2. High-dispersion regime: events split by whether the cross-sectional std of trailing
   20d returns among members on the report date is above/below its expanding median.
No other conditioning, winsorizing scheme, or subsample may be introduced post hoc.

**Expected result** (numeric, on which evaluator):
Once n ≥ 300 point-in-time events: 20d rank IC ≥ 0.03 with t ≥ 2 (evaluator =
earnings_collect.py --report, the pre-registered pooled Spearman IC). 5d IC expected same
sign, smaller n-adjusted t; 60d IC expected positive but weaker per-day.

**Alternative result** (what the null produces):
Large-cap PEAD is fully arbitraged post-2010s: 20d IC ≈ 0.00 ± 2/sqrt(n), confirmation adds
nothing, and the sector-relative variant is indistinguishable from raw.

**Failure / kill condition** (pre-committed; decidable from --report output):
KILL if, at n ≥ 600 point-in-time events, 20d rank IC < 0.01 OR t < 1. Stop-iterating
rule: no new scaling definitions, horizons, or conditioning slices may be added to rescue
the result; if killed, the dataset keeps accruing as infrastructure but the hypothesis
goes to FAILURES.md and no earnings-surprise spec is proposed from this data.

**Trial-ledger row**: TRIAL_LEDGER.md — robustness/experiment table row added in the same
commit (1 hypothesis + 1 pre-registered secondary + 2 pre-registered conditioners).

**Derived from prior holdout results?** No — the PEAD hypothesis predates this hunt (it is
a literature prior; the repo's separate pead track is WRDS-blocked and shares no data with
this forward panel). Not an adaptive loop on hunt2026 holdout results.

---
**Result** (filled after the run, never edited above this line): ACCUMULATING — collection
started 2026-07-10; 0 point-in-time events scoreable tonight by construction. --report
prints the honest accumulating state until n ≥ 300.
