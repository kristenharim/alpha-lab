# Stock-Universe Repair — versioned data project (started 2026-07-11)

Separate, versioned project. It does **not** rewrite the frozen hunt2026 panels or the
frozen momentum_concentrated trial (both stay as-is; the original **BLOCKED** verdict for
momentum_concentrated is preserved as institutional knowledge). Output is a NEW dataset
(`panel_stocks_v2`) that a NEW frozen trial will use.

## Root cause (measured, not assumed — continuity_audit.py)
Of **777** ever-S&P-500-member stocks since 2014 in the frozen panel:
- **168 (22%) have ZERO prices** while flagged as members;
- 595 (77%) are clean (≥99% coverage);
- **average daily member coverage 87.2%** (≈13% of the index unpriceable on a typical day).

The 168 zero-coverage names are dominated by **genuine delistings / mergers / renames** that
yfinance cannot serve: AABA (ex-Yahoo/Altaba), ABC (AmerisourceBergen→Cencora/COR), AGN
(Allergan→AbbVie), ALXN (Alexion→AstraZeneca), ANTM (Anthem→Elevance/ELV), APC
(Anadarko→Occidental), ATVI (Activision→Microsoft), BCR, BRCM (→AVGO), BXLT, CA (→AVGO),
CAM, ABMD (→J&J), ADS, ARNC, plus a few current tickers that appear fetch-dropped (BK, MMC,
BLL→BALL). yfinance returns nothing for an acquired/delisted symbol, so the frozen panel
could only ever hold **survivors** → a survivorship-biased selection universe.

**Direction of bias:** momentum_concentrated ranked over ~595 survivor names, tilting away
from names that were later acquired/delisted. Magnitude is bounded: momentum's rank IC on
this universe is already ≈0 (F-016), so the bias did not manufacture a false edge — it made
the universe incomplete, not the result falsely positive.

## Why yfinance is structurally insufficient
Free yfinance has no delisted-security history. A survivorship-complete daily equities
panel requires **Polygon.io, Tiingo, or CRSP/WRDS**. This project is therefore **BLOCKED on a
survivorship-complete data source** for the ~150 genuinely-dead names; the ~15 fetch-dropped
current names (BK, MMC, BLL/BALL) are recoverable now via robust per-ticker re-fetch.

## Repair tracks
1. **Permanent identifier map** (`id_map.csv`, human-curated, versioned): old ticker →
   {successor ticker, corporate-action type (rename/merge/acquire/delist/spinoff), effective
   date, permanent_id}. Starter rows for the identifiable actions are seeded (below).
2. **Robust re-fetch** of current-but-dropped tickers (per-ticker, not batch — the batch
   download silently dropped names) → recovers BK/MMC/BLL-as-BALL etc.
3. **Survivorship-complete acquisition** (gated on a Polygon/Tiingo/CRSP key) for the dead
   names — the only real fix for the 150.
4. **Continuity audit** (this dir) re-run on v2: missing-member-day stats, coverage
   distribution, affected ranks/selections, estimated bias direction — the deliverable that
   certifies v2 before any trial.

## After repair (NEW trials, original results preserved)
- Re-run the IC screen on v2 as a **new** trial (new ledger row; F-016 stays).
- Re-run momentum_concentrated as a **new frozen version** (v2) — new spec dir, new blind
  eval; the original v1 book stays frozen on the paper roster with its BLOCKED verdict.
- Only if v2 IC clears the pre-registered bar does anything advance — and then through the
  Orthogonality Benchmark + Stage-4 gate, never directly to the funded roster.

## Status
- continuity_audit.py + coverage table: **done** (v1 characterized).
- id_map.csv starter: **seeded** (identifiable corporate actions).
- Per-ticker re-fetch of dropped current names: **TODO** (recoverable now).
- Survivorship-complete source: **BLOCKED on key** (Polygon/Tiingo/CRSP).
