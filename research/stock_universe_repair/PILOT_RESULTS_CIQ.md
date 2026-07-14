# Pilot results — Capital IQ Pro (driven live 2026-07-11)

*Gathered by driving Kristen's logged-in CIQ Pro session (Chrome extension). Screenshots captured
per security. This is actual entitlement evidence; the panel stays UNCHANGED per the standing rule.*

## Access + platform capabilities (confirmed live)
- **Access: LIVE** — logged in as Kristen Ho, full CIQ Pro.
- **Permanent identifiers exposed:** CIQ **MI KEY** + **SPCIQ KEY** (company-level), **CUSIP** + **ISIN**
  (security-level). Multiple identifier types available.
- **Export formats:** **Excel** (structured), PNG, PDF, Word (from the Stock Chart "Export" menu).
- **Search resolution for inactive names:** by **company name** works cleanly; results are tagged
  PUBLIC/PRIVATE and status (Operating / Operating Subsidiary / Out of Business / Inactive).
- **Historical pricing:** each delisted profile shows "This security was last traded on <date>" and a
  "Click to access historical pricing data" link → Stock Chart with a data-table + Export.

## Per-security (identity-continuity is the acid test)
| security | resolved by | entity found | last trade | identity kept separate? | permanent ID | verdict |
|---|---|---|---|---|---|---|
| **WAMUQ** | name "Washington Mutual" | Washington Mutual, Inc. (PRIVATE/delisted) | **3/19/2012** | yes — own entity | MI KEY 102028; SPCIQ 1787986284 | **PASS** |
| **CELG** | name "Celgene" | Celgene Corporation (Operating Subsidiary of BMY) | **11/20/2019** | **yes — price series ENDS at acquisition, Ultimate Parent = Bristol-Myers Squibb, NOT appended to BMY** | MI KEY 4151669; SPCIQ 258769 | **PASS** |
| **GM/MTLQQ** | name "Motors Liquidation" | **Motors Liquidation Company** (PUBLIC, "Out of Business" as of 3/31/2011) | (out of business 2011) | **yes — old GM is a SEPARATE "Motors Liquidation" entity; old NYSE:GM common + MTLQ.Q both Inactive; NOT joined to post-2010 General Motors Company** | old GM common CUSIP 370442501 / ISIN US3704425012; MTLQ.Q CUSIP 62010A105 | **PASS** |
| **XLNX** | name "Xilinx" | Xilinx, Inc. (Operating Subsidiary of AMD, PRIVATE) | (acq. 2022-02) | **yes — own entity, not merged into AMD** | MI KEY (Xilinx) | **PASS** |
| **KD** | name "Kyndryl" | Kyndryl Holdings, Inc. (NYSE:KD, PUBLIC, Operating; IT Consulting) | (operating; series 10/29/2021→07/10/2026) | **yes — price series STARTS 10/29/2021 (spinoff/when-issued window), does NOT inherit IBM's multi-decade history; own entity, not IBM** | MI KEY 29724772; SPCIQ 691274020 | **PASS** |
| **HTZ** | name "Hertz Global Holdings" | Hertz Global Holdings, Inc. (NASDAQGS:HTZ, PUBLIC, Operating; CUSIP 42806J700) | (operating; **series STARTS 07/30/2021**→07/10/2026) | **yes — current HTZ price series starts 07/30/2021 (post 6/30/2021 emergence); does NOT bridge back to pre-2020 pre-bankruptcy Hertz common (cancelled, crashed to ~$0.40 in 2020). Old→new NOT joined.** | MI KEY 4993855; SPCIQ 30396158; CUSIP 42806J700 / ISIN US42806J7000 | **PASS** |

## Formal gate — Capital IQ Pro (closed 2026-07-11, all 6 driven)
- **Identity integrity: PASS — 6/6.** Zero identity-continuity errors across all six traps: bankruptcy-
  terminal (WAMUQ), acquisition-with-CVR (CELG), old/new-GM split (GM/MTLQQ), acquisition-subsidiary
  (XLNX), IBM spinoff (KD, series starts 10/29/2021), post-bankruptcy relisting (HTZ, series starts
  07/30/2021). CIQ never joins a predecessor series to its successor; acquired/bankrupt/spun securities
  are kept as own terminal-/start-dated trading items with permanent IDs (MI KEY + SPCIQ KEY + CUSIP/ISIN).
- **Terminal/bound coverage: 6/6** have documented series bounds. Live-verified *this session* via the
  Max-range "From X To Y" chart label: KD (10/29/2021→07/10/2026), HTZ (07/30/2021→07/10/2026). The other
  four verified earlier same day (WAMUQ last trade 3/19/2012; CELG ends 11/20/2019; GM out-of-business 2011;
  XLNX acq. 2022-02). *Caveat:* exact first-price-date + last-nonblank-price for the four delisted names
  rest on earlier-in-day screenshots, not re-driven now.
- **Corporate-action treatment: PASS.** Status (Operating / Operating Subsidiary / Out of Business /
  Inactive), ultimate parent, and event type (acquisition / spinoff / bankruptcy / relisting) documented
  per name.
- **Structured export: PASS** (single-file test complete 2026-07-11). Kristen ran Export→Excel herself
  (browser-automation clicks can't complete the download — no user gesture — so the file must be triggered
  by a real click). File inspected:
  - **File:** `Kyndryl Holdings, Inc._StockChart_07_11_2026.xlsx` (96 KB; sheets `Stock Chart` [metadata] +
    `Data`).
  - **753 daily rows**, **2023-07-11 → 2026-07-10 (3.00 yr)**, descending. Daily frequency confirmed
    (gap histogram 1d×585 / weekend 3d×136 / holiday 4d×20,2d×11; 0 dup dates; 0 blank price/vol).
  - **Columns:** `Pricing Date` · `KD | Share Price (Daily)($)` · `KD | Volume (Daily)`. Price + volume.
  - **Identifier preserved:** metadata sheet = `NYSE:KD (MI KEY: 29724772; SPCIQ KEY: 691274020)`.
  - **⚠️ Adjusted/unadjusted NOT distinguished** — one price column, no adj/unadj flag in this export path.
  - **⚠️ Date cap:** daily granularity capped at **3-year windows** (tooltip: "shorten your range to ≤ 3
    years to enable daily data"). Max range silently downsamples to Monthly. Full KD history at daily =
    2 stitched windows. No row-cap hit within a 3Y window.
  - The Stock-Chart Excel export is **single-security** — the KD file carried zero columns for the 5
    comparison tickers loaded on the chart. So this path is one-name-at-a-time.
- **Overall CIQ price gate: PASS** (identity 6/6, coverage 6/6, corporate actions documented, structured
  export complete + usable). *Scale caveat below — a single-name PASS is NOT a full-panel PASS.*

## Bulk-export limit test (Companies screener, 2026-07-11)
Ran a minimal screen `Market Capitalization [Current] ($M) > 0` → **79,681 companies** matched (full global
universe is screenable — discovery is NOT the constraint). Findings:
- **Grid display** paginates at **250 rows/page** max (50/100/250 options; 319 pages for 79,681).
- **Rows carry a permanent Entity ID** (e.g., 4984797) alongside name + ticker — IDs survive bulk output.
- **Export modes:** Results As **Table Function** / **Single Cell Functions** / **Values** / **List** /
  **PDF** / Criteria to Maps.
- **Structural limit — the decisive point:** the screener output is **cross-sectional** (one snapshot row
  per company, e.g., current market cap), **NOT a daily time-series panel**. The Table-Function / Single-
  Cell modes export **live CIQ Excel-plugin formulas**, i.e., a daily/historical bulk pull is handed off to
  the **CIQ Excel Plugin (Office add-in)** — a separate desktop tool + entitlement that is **UNTESTED**.
- **Net:** there is **no web-UI path that emits a multi-name daily-price panel**. Two real routes for
  panel_stocks_v2, both with open questions:
  1. **Per-name Stock-Chart exports** — proven working + ID-preserving, but **1 name × ≤3-yr daily window
     per file**. For the ~382 missing delisted members that's roughly **382 names × ~2 windows ≈ 760 manual
     exports** (each needs a real Save click — automation can't complete the download). Laborious but
     mechanically sound.
  2. **CIQ Excel Plugin** (what Table-Function export feeds) — the actual bulk mechanism; **not installed/
     tested**, per-request cell/row caps + delisted-security time-series coverage unknown. This is the next
     thing to test before declaring CIQ can build the full panel.
- **Do NOT yet conclude CIQ can support panel_stocks_v2 at scale.** Single-name daily export: PASS. Bulk
  daily-panel export: **UNPROVEN** — gated on the Excel Plugin test.

## Estimates PIT test (Recent Changes / Revisions / Detailed Estimates) — **INCONCLUSIVE (leans FAIL)**
- **Fields found:** "Recent Changes" exposes an **Estimate Date Range (from/to)** filter over dated
  estimate changes — the one dated-revision primitive that *could* support PIT reconstruction. No explicit
  **As Of Date / Snapshot Date / Point-in-Time / Estimates Snapshot** labeled field found on any surface.
- **Archived vs restated:** The populated surfaces — Detailed Estimates (current consensus by fiscal
  period), Consensus, Revisions (trailing up/down *counts* for Last 1/2/3 Months, anchored to today) — are
  all **current-anchored / restated**, not as-was snapshots.
- **Blocker:** the only dated-revision surface (Recent Changes) is **entitlement-gated on this Berkeley
  login** — banner: *"Your default broker entitlements are currently being validated… request entitlements"*
  — so broker names + dated estimates are **not populated**. Cannot retrieve dated broker revisions to
  reconstruct pre-announcement consensus.
- **Result: INCONCLUSIVE.** No labeled PIT/snapshot consensus field; the dated-revision path exists in the
  UI but is not entitled on this login, so as-was consensus cannot be reconstructed today. Treat CIQ
  estimates as **restated, not PIT**, for this entitlement *until* the two verification gates below clear.

### Addendum 2026-07-13 — support-email caveat split (Kristen)

S&P support (Reva) noted two caveats. They land on **different** tracks; do not conflate.

1. **"Only current index members, not point-in-time"** → **NON-ISSUE for stock-universe-repair.**
   This track already has S&P membership history from the existing frozen panel. CIQ/GFD's job here
   was only ever to **price the already-identified ~382 missing names**. The 6/6 identity pilot
   already proved CIQ does that correctly. Membership PIT is not CIQ's problem on this track.

2. **"Historical consensus estimates, but limited to analysts your university subscribes to"** →
   **this is the one that matters for the EPS-revisions lane.** Promising, **not** a confirmed
   unblock. `DATA-BLOCKED` stands until both are verified live:
   - **PIT vs restated:** is "historical" a frozen as-of-that-day snapshot, or a restated view of
     the past? The in-app probe already found the one dated-revision surface (Recent Changes)
     entitlement-gated pending broker validation — Reva may be describing that same surface once
     validation clears, or something different. Do not assume.
   - **Analyst count under Berkeley:** prereg requires `analyst_count ≥ 3` at **both** ends of the
     60-day revision window. If "analysts your university subscribes to" means 1–2 visible
     brokers, the lane fails that bar regardless of PIT status.

Do **not** flip EPS-revisions off DATA-BLOCKED, freeze EXP-IC-REVISIONS-FWD, or purchase anything
on the strength of the email alone.

## Not yet tested
Finaeon / GFD (Berkeley institutional login previously resisted the automated click — deferred to a manual
Kristen click per the "stop and ask" rule). Panel unchanged.
