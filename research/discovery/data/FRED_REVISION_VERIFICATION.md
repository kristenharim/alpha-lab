# FRED ALFRED revision-provenance verification (2026-07-11)

Verifies, with the FRED API key (ALFRED vintages; `~/.config/rimrimos/fred.env`, chmod 600,
not in repo), that the discovery data layer's keyless latest-revised ingest is point-in-time
safe **on the revision axis**. Script: `fred_revision_verification.py` (read-only). This is a
verification addendum to `DATA_QUALITY_REPORT.md`; it does not alter the layer, and it does
**not** touch EXP-A or EXP-B (their frozen specs and evaluation gates are unchanged).

## "First print" defined exactly
The observations endpoint collapses consecutive identical vintages into one row spanning
`[realtime_start .. realtime_end]`. For each sampled observation we record:
- **observation_date** — the calendar date of the data point.
- **earliest_vintage** — the first `realtime_start` at which the observation was *published
  with a real value* (this is also the release date → gives the release lag).
- **first_published_value** — value at the earliest vintage.
- **latest_value** — current value.
- **difference** = latest − first.
- **n_distinct_values** — number of distinct published values (1 ⇒ never revised).
- **backfilled** — whether the observation was first published as `.`/missing and a value
  added later.

## Complete nine-series revision table (all series the layer ingests)
Two sampled observations (2020-06-01 calm, 2023-03-15 SVB week) — identical verdicts; the
2020-06-01 rows are shown, and both samples gave diff 0 / n_distinct 1 / no backfill for all
nine layer series.

| series | earliest_vintage | release lag (bd) | first | latest | diff | n_distinct | backfilled | revision |
|---|---|---|---|---|---|---|---|---|
| DGS3MO | 2020-06-02 | 1 | 0.14 | 0.14 | 0.0 | 1 | no | unrevised |
| DGS2 | 2020-06-02 | 1 | 0.14 | 0.14 | 0.0 | 1 | no | unrevised |
| DGS5 | 2020-06-02 | 1 | 0.31 | 0.31 | 0.0 | 1 | no | unrevised |
| DGS10 | 2020-06-02 | 1 | 0.66 | 0.66 | 0.0 | 1 | no | unrevised |
| DGS30 | 2020-06-02 | 1 | 1.46 | 1.46 | 0.0 | 1 | no | unrevised |
| DFF | 2020-06-02 | 1 | 0.05 | 0.05 | 0.0 | 1 | no | unrevised |
| T10Y2Y | 2020-06-01 | 0 | 0.52 | 0.52 | 0.0 | 1 | no | unrevised |
| VIXCLS | 2020-06-01 | 0 | 28.23 | 28.23 | 0.0 | 1 | no | unrevised |
| VXVCLS | 2020-06-01 | 0 | 30.92 | 30.92 | 0.0 | 1 | no | unrevised |

Excluded macro (control — must be revised for exclusion to be justified):

| series | earliest_vintage | release lag (bd) | first | latest | diff | n_distinct | revision |
|---|---|---|---|---|---|---|---|
| CPIAUCSL | 2020-07-14 | 31 | 257.214 | 257.042 | −0.172 | 6 | REVISED |
| GDP | 2020-07-30 | 43 | 19408.759 | 19958.291 | +549.5 (+2.8%) | 8 | REVISED |

## Revision safety is separate from release timing (two distinct axes)
- **Revision axis (this file):** all nine layer series are unrevised (diff 0, one distinct
  value, no backfill) → latest-revised == point-in-time value, no revision look-ahead.
- **Release-timing axis (frozen rules, unchanged):** the measured `earliest_vintage`
  *confirms* the layer's frozen conventions rather than changing them — DGS*/DFF first publish
  at **obs + 1 business day** (H.15 next-morning release) → the frozen **1-business-day rate
  lag** holds; T10Y2Y/VIXCLS/VXVCLS publish **same day** → the frozen **same-day VIX/state**
  convention holds. An unrevised value is still unusable before its release timestamp; the
  1-bd-rate / same-day-vol lags and market-calendar alignment remain the binding
  point-in-time rules and are **not** relaxed by this result.

## Conclusion
> The tested rate and volatility series show no material vintage revisions, so latest values
> do not introduce revision look-ahead. Their point-in-time validity still depends on the
> frozen release-lag and market-calendar alignment rules. CPI and GDP are revised and require
> ALFRED vintage retrieval before use.

With the full nine-series table and the revision/timing distinction recorded, the data-layer
PASS is **empirically verified**. The FRED key's forward value: if a future (gated)
preregistration ever needs a revised macro series, the key enables true point-in-time vintage
retrieval (`realtime_start` = as-of date) that keyless CSV cannot. Until then the key is used
only for this read-only verification; no strategy is built, nothing is promoted, and EXP-A /
EXP-B are untouched.
