# Polygon source — entitlement + contribution to the repair (2026-07-11)

*Additive to this project. Does not edit id_map.csv / PLAN.md / continuity_audit.py. Supplies the
Polygon-source layer that PLAN Track 1 (identifier/delisting map) and Track 3 (survivorship source)
were "BLOCKED on key" for — but only partially, per the provisioned plan's entitlements.*

## Provisioned Polygon plan = REFERENCE DATA ONLY (probed live)
| endpoint | status |
|---|---|
| `/v3/reference/tickers` (incl. `active=false` → delisted, `delisted_utc`, `composite_figi`) | ✅ 200 |
| `/v3/reference/splits`, `/v3/reference/dividends` | ✅ 200 |
| `/v2/aggs/...` daily price bars (any name, even recent AAPL 2024) | ❌ **403 NOT_AUTHORIZED** |

**Consequence:** Polygon on this plan unblocks the **identifier / delisting / corporate-action** half
of the repair. It does **NOT** supply prices for the ~150 dead names (repair Track 3's core need) —
that still requires a Polygon **price-tier upgrade** (Stocks Starter = 2y aggregates; Developer/
Advanced = 15y+) or **FactSet / Tiingo / CRSP**.

## What this layer produced
`polygon_reference.py` paginates all delisted US stocks (24 pages, cached in `polygon_raw/`,
**gitignored** — 6.8 MB, reproducible) and joins them to the ever-S&P members missing from the panel.
Result → `delisting_map.csv`:

- ever-S&P members missing from `panel_2005`: **382**
- matched in Polygon's delisted set: **207 (54%)**; with delist date: **205**; with FIGI permanent id: 54
- **not matched: 175 (46%)** — older delistings outside Polygon's reference window, rename-successors
  (e.g. ABX→GOLD, a rename not a delist), or share-class ticker forms (AFS-A) needing normalization.

This auto-completes ~205 of the hand-seeded `id_map.csv` delist dates. The 175 unmatched need the
existing hand-curated rename mapping (successor tickers) or a deeper vendor.

## Bottom line for the repair
- **Identifier/delisting track: materially advanced** (205 auto-dated delistings + FIGIs).
- **Price track: still BLOCKED** — this plan serves no OHLCV. The survivorship-complete *price* panel
  (`panel_stocks_v2`) needs a price source. FactSet is the highest-value one (prices **and** PIT
  earnings for the Discovery earnings lane); its MCP setup is interactive-OAuth (owner must run it),
  and its REST API needs the FactSet username-serial (the API key is only the password half).
