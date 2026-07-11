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
| **KD** | — | not yet driven (spinoff from IBM 2021 — low continuity risk; expected own entity) | — | pending | — | pending |
| **HTZ** | name "Hertz Global Holdings" | current Hertz Global Holdings, Inc. (NASDAQ:HTZ, Operating; CUSIP 42806J700) found | — | **pending** — needs a pricing-continuity check across the 2020 Ch.11 / 2021 relisting (does the price series join old pre-bankruptcy Hertz to the relisted security?) | CUSIP 42806J700 / ISIN US42806J7000 | pending |

## Interim verdict — Capital IQ Pro: **PASSING**
- **Zero identity-continuity errors** in the four hardest traps driven (bankruptcy-terminal, acquisition-
  with-CVR, old/new-GM split, acquisition-subsidiary). CIQ consistently keeps the acquired/bankrupt
  security as its **own terminal-dated entity** with permanent IDs, correctly linking parent/subsidiary
  **without merging price series**.
- Meets the pilot PASS bar on: identity separation (4/4 so far), terminal histories reach the actual last
  trade, corporate action documented (status + ultimate parent), structured **Excel** export available.
- **Remaining to fully close CIQ:** KD (spinoff — expected pass), HTZ pricing-continuity across the
  relisting (the one genuinely ambiguous case), and per-security first-price-date + adjusted/unadjusted +
  export row-limit (secondary — the chart's data-table + Excel export cover these but need the date-window
  set past the stray default comparison).

## Not yet tested
Finaeon (institutional anonymous login resisted the automated click earlier) + the CIQ estimates PIT
snapshot test. Panel unchanged.
