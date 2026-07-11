# Successor / rename resolution — identifier & corporate-event repair (2026-07-11)

**This is an identifier and corporate-event repair, NOT a price-panel repair.** It produces a NEW
additive candidate file (`rename_candidates.csv`); it does not modify the frozen panel, does not
overwrite the curated `id_map.csv`, does not join predecessor↔successor price series, and does not
assume economic continuity unless a same-security rename is supported. Builder: `resolve_renames.py`.

## Scope & compliance with the authorized restrictions
- Target: the **175** ever-S&P members Polygon left unmatched (identifier gap, not the 207 dated ones).
- **StockAnalysis:** robots checked (`User-agent: * Disallow:` — general access allowed). Not scraped:
  a 3-name probe (AAMRQ, AKS, LEHMQ) returned **404** — its free pages do not serve long-delisted
  names, so it adds nothing here. Left as a documented manual source only.
- Every source kept **separate** in the `sources` column; each inference is labelled.
- Continuity is asserted **only** for same-security renames/share-class; acquisitions, bankruptcies,
  and uncertain cases are `price_continuity_valid = False`/`uncertain` and `manual_review_required = True`.
- SEC has **no delisted-ticker→CIK lookup** (verified: browse-edgar returns an empty page for AKS/ABS/
  AHM), so `old_cik` is generally blank → manual review. `new_cik` is filled only when a curated
  successor ticker is a current SEC ticker.

## Sources (authoritative, local, no scraping)
`curated_id_map` (hand curation, cross-checked not overwritten) · `polygon_reference` (cached delisted
set — name/delisted_utc/composite_figi, matched after conservative normalization: bankruptcy `Q`,
share-class `-A/-B`, warrant `.WS`) · `sec_company_tickers` (current ticker→CIK/name for successors;
ticker-reuse flagged, never assumed).

## Pattern-candidate labeling (classifications from ticker syntax are NOT determinations)
Every event derived primarily from ticker syntax is labeled **`event_basis = pattern_candidate`** and
its `event_type` carries a `?` marker — it is a candidate for manual verification, NOT an authoritative
event determination. Specifically:
- A **`Q` suffix** (`event_type = bankruptcy_proceedings?`) may indicate bankruptcy *proceedings* but does
  **not** by itself prove liquidation or determine successor treatment.
- **Ticker punctuation / class notation** (`share-class?`, `share-class/warrant?`) does **not** by itself
  prove a share-class conversion.
- **SEC identifier / former-name evidence** (CIK, FIGI, curated id_map) is kept in separate columns
  (`old_cik`, `new_cik`, `figi`, `sources`, `identifier_confidence`) and is distinct from the *inferred*
  `event_type`. Identifier evidence never upgrades a pattern-candidate event to a determination.

## Persisted fields (per candidate, in `rename_candidates.csv`)
historical_ticker · proposed_successor_ticker · predecessor_name · successor_name · effective_date ·
event_type (with `?` when pattern-inferred) · **event_basis** (sourced / pattern_candidate / unresolved) ·
old_cik · new_cik · figi · sources · **identifier_confidence** (of the ID evidence, not the event) ·
price_continuity_valid · manual_review_required.

## `price_continuity_valid` = FALSE for every row
No row is assumed continuous. `price_continuity_valid = False` for **all 175** and only flips to True
when the **same continuing security is positively verified with effective dates + supporting evidence**
— which nothing in this free/local set meets. Pattern syntax and identifier presence do not establish
continuity. `manual_review_required = True` for all 175.

## Category counts (of 175) — all buckets are CANDIDATES
| candidate category | count |
|---|---|
| verified rename (same continuing security) | **0** |
| share-class **pattern_candidate** | **9** |
| acquisition (old security terminated) | **0** |
| bankruptcy-proceedings **pattern_candidate** (Q-suffix) | **28** |
| relisting / reorganization | **0** |
| **unresolved** (needs licensed source or manual) | **138** |
| **total** | 175 |

**62 of 175** got authoritative *identifier* data (Polygon-normalized name/date/FIGI); **0** are
authoritative *event* determinations. The 0s for verified-rename / acquisition are honest: those events
cannot be confirmed from a bare delisted ticker without a company name and effective-date evidence, which
the free/local sources do not supply for these old names. **The free automated identifier investigation
is now COMPLETE** — the remaining work is the manual vendor diagnostic; the 138 unresolved names are not
worth further free automated effort until a licensed platform demonstrates adequate inactive-security coverage.

## Next step (does NOT alter the panel)
The 138 unresolved + the nameless subset need a licensed source with delisted coverage — see
`vendor_diagnostic_15.md` (a 15-security manual test for Capital IQ Pro and GFD/Finaeon). No panel
change is made until provenance and completeness are documented per the authorization.
