# 40-name GFD symbol-resolution pilot — coverage & data-quality (2026-07-11)

*Stratified sample from the 382 missing S&P members, chosen to stress the identity problem
(bankruptcies, ticker reuse, acquisitions where the old entity vanished, renames, spin-offs,
share classes). Resolved against GFD/Finaeon (Berkeley). Mapping in `PILOT40_MAPPING.csv`.
No panel/strategy change — evidence only.*

## Resolution gate: PASS
- 40 names → **37 HIGH-confidence (92.5%)** (≥90% threshold met), **3 MEDIUM**, **0 unresolved**, **0 conflations**.
- MEDIUM (excluded from the HIGH download): KATE2 (ex-Liz Claiborne date-window), RD1 (RDS-A ticker vs
  1996-2002 Royal-Dutch-Petroleum era conflict), FTLAQ1 (Fruit of the Loom Cayman vs RI predecessor).
- Suffixes were **verified, not inferred** — non-"1" cases confirmed by evidence: MER3, NYX2, S2, COC1B,
  TCOM1A, KATE2.
- Reused tickers kept separate (AMR/AAL, Delta/DAL, Kodak old/new/KODK, Sprint/SentinelOne); collisions
  avoided (Argentine Nortel NTL2, AMBAC Industries AB1, British Telecom "BT", Pactiv Evergreen).

## Download of the 37 HIGH symbols — data quality: PASS
Batch of 37 (in workbook `rimrim`, split-adjusted daily, Data Fill = None). 287,923 pilot rows.
- **37/37 present**, **37/37 clean**: 0 duplicate dates, 0 blank OHLCV, 0 parse failures.
- **Daily coverage complete through each S&P membership window** — sampled trading-day counts are exact
  (253 in 1997, 252 in 2005). Lower-frequency data (monthly/quarterly/annual) appears **only** in the
  pre-~1970s deep-history extension, outside every membership window.
- **Terminal dates match the actual corporate events** (identity/entity verification), e.g. S2→2020-04-01
  (T-Mobile), AAMRQ1→2013-12-06 (AAL merger), MER3→2008-12-31 (BofA), CPQ1→2002-05-03 (HP),
  TCOM1A→1999-03-09 (AT&T), NYX2→2013-11-12 (ICE), BIGGQ1→2025-05-30 (liquidation).
- **CIK note (ticker-reuse):** where the legal entity survived reorganization the CIK is shared across
  old/new (AAMRQ1 & AAL = CIK 6201; EKDKQ1 & KODK = 31235; DALRQ1 & DAL = 27904), but GFD keeps the
  **securities** separate (distinct symbols, distinct terminal dates, no price bridging) — correct for a
  price panel.

## Implication (no action taken)
GFD resolves and cleanly delivers the hardest missing-member identities at daily frequency for the
membership era. Supports scaling to a 25-50 sample then the full 382 — NOT executed here. Panel,
strategies, schedules, broker state, factor_lab all unchanged.
