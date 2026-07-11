# Berkeley entitlement + survivorship + PIT-estimates verification protocol (2026-07-11)

**Why this is a protocol, not a confirmed answer.** Entitlements are account/tier-specific. I cannot
access Berkeley's Capital IQ Pro (S&P Global MCP = interactive OAuth, unavailable headless) or GFD/
Finaeon (Berkeley libproxy, browser-login). Only your logged-in session or the Berkeley library / S&P /
GFD support can confirm the actual entitlement. Below: **vendor general capability (sourced)** vs **what
to verify for Berkeley**, plus the exact steps. Do NOT change the research panel until provenance and
completeness are documented.

---

## Part 1 — Capital IQ Pro

### 1a. Entitlement checklist — vendor capability vs verify-for-Berkeley
| your requirement | CIQ general capability (sourced) | how to verify in your session |
|---|---|---|
| delisted daily price history to last trade | 109,000+ companies incl. inactive | open a delisted name → Charting/Pricing → confirm series reaches the actual final trade |
| adjusted & unadjusted prices | yes (split/div-adjusted toggle) | toggle adjustment on the pricing export |
| splits/div/M&A/spinoff/bankruptcy/ticker change | Transactions + Key Developments + corp-action history | check a merger + a bankruptcy name |
| stable identifiers | CUSIP, ISIN, SEDOL + CIQ permanent IDs (companyId / tradingItemId / capitalIQId) | confirm a permanent ID survives the ticker change |
| S&P 500 membership / constituent-change history | index constituents + as-of-date membership in the screener | screen index membership as-of a past date |
| structured export | CIQ Pro Office Excel plug-in, screener export, Xpressfeed / API | note the row/export cap you hit |
| non-commercial academic use | governed by Berkeley's S&P license | confirm terms with the library (do not assume) |

### 1b. Retrieval method (your CIQ-specific question)
- **Screening** (CIQ Pro screener): bulk/universe — filter `company status = inactive/delisted`, export. Best for bulk inactive retrieval.
- **Excel plug-in** (`CIQ(id, item, date)` formulas via CIQ Pro Office): programmatic per-field pulls; has a data/row cap — record it.
- **Downloadable report / tearsheet**: single-company.
- **Inactive securities are best searched by COMPANY NAME or CUSIP or CIQ permanent ID** — the *old ticker* frequently fails after delisting/reuse. Bulk inactive = screener (or Xpressfeed for true bulk feed).

### 1c. Point-in-time estimates (the decisive distinction)
- Base CIQ Pro "Estimates" view can be **restated** (a current DB view of historical fiscal periods).
- The archived product is **"S&P Capital IQ Estimates — Point-in-Time"** — a snapshot of every estimate
  change with its associated date/timestamp. **VERIFY Berkeley has the PIT snapshot entitlement** (often
  separate from base CIQ Pro; may require Xpressfeed or the PIT dataset specifically).
- **Test:** pick a historical earnings date; retrieve the consensus *as of the day before* the release;
  confirm it equals the then-current (as-was) consensus via the revision timestamps — NOT today's restated number.

---

## Part 2 — GFD / Finaeon

- Finaeon has **US Stocks** + **US Delisted Equities** databases: individual current & delisted US stocks
  from every exchange, **25,000+ delisted names**, survivorship-free, with corporate actions + fundamentals
  (sourced). So individual delisted US common stocks **are** covered — it is NOT index-only.
- **VERIFY Berkeley licenses the US Stocks / US Delisted Equities modules** (vs only the GFDatabase
  indices/macro series — a common narrower campus subscription). This is your GFD-specific question.
- Identifiers: GFD permanent symbol/code, often with CUSIP — verify.
- S&P 500 membership history: GFD carries index constituent series — verify as-of-date availability.
- Export: Excel export; bulk via the database download interface — record row/download caps.
- **Estimates: GFD does NOT provide analyst estimates** → the earnings-estimates lane is Capital IQ (or
  I/B/E/S, unavailable to you), never GFD.

---

## Part 3 — The 15-security test grid
Run each through the 4 questions + full recording fields in
[../../stock_universe_repair/vendor_diagnostic_15.md](../../stock_universe_repair/vendor_diagnostic_15.md):
FB→META, ANTM→ELV, ABC→COR, BLL→BALL, WLTW→WTW (renames); AGN, ALXN, ATVI, XLNX, CERN (acquisitions);
LEHMQ, WAMUQ, AAMRQ (bankruptcies); ABS, GLK (old delistings). Per security/platform record: **source
date, platform, identifier used, final trading date, price-history availability, corporate-action
treatment, export restrictions**, + a screenshot/export reference.

The real test is the acquired / bankrupt / old-delisting rows: does the series reach the **actual final
trading date** with a **stable identifier** and **corporate actions**? (Survivors like FB→META are easy.)

---

## Part 4 — Historical PIT analyst-estimates protocol (Capital IQ)
Capture per (company/security id, fiscal period, measure e.g. EPS): consensus value · number of analysts ·
**estimate/revision timestamp** · actual reported value · earnings announcement date & time · whether
inactive/acquired companies are covered · structured export.

**Decisive acceptance test:** can the platform *reconstruct the consensus available immediately before a
historical earnings release*, and is that value **archived point-in-time** (revision-timestamped as-was)
rather than **retrospectively restated**? Only the PIT snapshot dataset passes. If Berkeley has only the
base estimates view, this lane stays BLOCKED for PIT research and the Finnhub forward collector remains
the correct approach (its prereg forbids restated backfill anyway).

---

## Fastest way to actually get the answers
Either (a) **I drive your real Chrome** (claude-in-chrome) while you're logged into CIQ Pro / Finaeon — I
run each lookup and fill the grid; or (b) you run it and paste/screenshot the results. Sources:
[S&P Capital IQ Estimates](https://www.spglobal.com/market-intelligence/en/solutions/capital-iq-estimates)
· [S&P Capital IQ Pro](https://www.spglobal.com/market-intelligence/en/solutions/products/sp-capital-iq-pro)
· [Finaeon US Delisted Equities](https://finaeon.com/product/us-delisted-equities/)
