# 15-security vendor diagnostic — Capital IQ Pro & Global Financial Data / Finaeon

*Manual test list (run by Kristen, who holds these platform logins). For EACH security, on EACH
platform, answer only the four questions below. **Do not alter the research panel based on the results
until provenance and completeness are documented.** This diagnoses coverage/quality; it is not itself
a data pull or a panel change.*

## The four questions (per security, per platform)
1. **Complete daily history through the final trading date?** (does the series run to the actual last
   trade, no early truncation, no survivorship drop?)
2. **Stable identifiers?** (a permanent id — CUSIP/CIK/FIGI/vendor-permId — that survives the ticker change?)
3. **Corporate actions present?** (splits, dividends, delisting/merger terms, delisting return?)
4. **Export capability?** (bulk/API/CSV export of the daily series + actions?)

## The 15 securities (span event types and eras)

### 5 continuing ticker changes (same security — continuity expected valid)
| historical | successor | event | ~date |
|---|---|---|---|
| FB | META | rename | 2022-06 |
| ANTM | ELV | rename (Anthem→Elevance) | 2022-06 |
| ABC | COR | rename (AmerisourceBergen→Cencora) | 2023-08 |
| WLTW | WTW | rename (Willis Towers Watson) | 2022-01 |
| BLL | BALL | rename (Ball Corp) | 2022-04 |

### 5 acquired firms (old security terminated — continuity NOT valid)
| historical | acquirer | event | ~date |
|---|---|---|---|
| AGN | ABBV | acquisition (Allergan→AbbVie) | 2020-05 |
| ALXN | AZN | acquisition (Alexion→AstraZeneca) | 2021-07 |
| ATVI | MSFT | acquisition (Activision→Microsoft) | 2023-10 |
| XLNX | AMD | acquisition (Xilinx→AMD) | 2022-02 |
| CERN | ORCL | acquisition (Cerner→Oracle) | 2022-06 |

### 3 bankruptcies / liquidations (Q-suffix; continuity NOT valid)
| historical | company | event | ~date |
|---|---|---|---|
| LEHMQ | Lehman Brothers | bankruptcy (2008 Ch.11, liquidated) | 2008-09 |
| WAMUQ | Washington Mutual | bankruptcy (2008) | 2008-09 |
| AAMRQ | AMR Corp (American Airlines) | bankruptcy 2011 → emerged/merged into AAL 2013 (relisting test) | 2011-11 |

### 2 very old delistings
| historical | company | event | ~date |
|---|---|---|---|
| ABS | Albertson's Inc | acquisition/delisting | 2006-06 |
| GLK | Great Lakes Chemical | merger → Chemtura | 2005-07 |

## Recording template (fill per security, per platform — capture evidence, not just Y/N)
For each cell, record and keep the underlying evidence:
- **screenshot or exported fields** (attach/keep the file);
- **source date** (when you pulled it) and **platform**;
- **identifier used** (ticker vs CUSIP/permId/CIK/FIGI — note which resolved the delisted name);
- **final trading date** the series reaches;
- **price-history availability** (complete-to-last-trade / partial / absent);
- **corporate-action treatment** (splits, dividends, delisting return, merger terms — present? how?);
- **export restrictions** (API / CSV / manual-only / blocked; row/quota caps).

Suggested columns:
`security | platform | source_date | identifier_used | final_trading_date | price_history (complete/partial/absent) | corp_actions | export (API/CSV/none + limits) | screenshot/export ref | notes`

The winner is the platform that reaches the **actual final trading date** with a **stable identifier** and
**corporate actions** for the acquired / bankrupt / old-delisting rows (survivors are easy; the terminated
securities are the real test of survivorship completeness). **Do not alter the research panel based on
these results until provenance and completeness are documented.**
