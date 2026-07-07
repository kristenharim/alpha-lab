# STATE — Asset-growth contrarian (Cooper-Gulen-Schill)

**Stage:** 1 (run on real data); result is a universe artifact, not a clean anomaly test
**Last session:** 2026-07-07

## Scope
From [[LIT — Does highest YoY growth predict returns]]: YoY total-asset growth is a
CONTRARIAN cross-sectional signal — low-asset-growth firms outperform high-growth (~20%/yr
spread, Cooper-Gulen-Schill 2008). This is the tradeable, free-data version of Kristen's
original "highest YoY growth" question (answer: highest growth predicts *negative* returns).

## Built
- `signal.py` — `asset_growth` (YoY Δ total assets), `growth_score` = −growth (low growth → long)
- `edgar.py` — SEC EDGAR companyfacts fetch for annual `Assets` (free, ~2007+, far more history than yfinance)
- `scripts/asset_growth_run.py` — score → 6-mo availability lag → monthly-held quantile L/S → scorecard
- Reuses the existing `core.backtest` quantile engine (cross-sectional, unlike StatArb). Tests 2/2 green.

## Result (2026-07-07, 60 large caps, EDGAR assets 2007+, monthly 2010–2026)
Net **Sharpe −0.78**, ann. −13.4%, **max DD −93%**, hit rate 40%. Deflated-Sharpe prob 0.08%.
Benchmark equal-weight = 1.35. Strategy strongly NEGATIVE both subperiods.

## The honest read — this is the WRONG universe, not a dead anomaly
The 60-name universe is survivorship-selected mega-caps. Over 2010–2026 the highest-asset-growth
names in that set are exactly the tech winners (NVDA, AAPL, MSFT, AMZN, TSLA) that also had the
highest *returns*. "Short the fast asset-growers" here = short the biggest winners of the decade
→ −93% path. Cooper-Gulen-Schill is a BROAD cross-section (thousands of names, effect strongest
in small caps); 60 mega-caps can't evaluate it fairly. So this run does **not** refute the anomaly
— it shows the anomaly's sign is wrong *within a basket of large-cap growth winners*, which is
almost tautological. It's a clean illustration of why universe choice dominates a cross-sectional test.

## Result — WIDE universe (2026-07-07)
S&P Composite 1500 via `core/data/universe.py` (503 large + 400 mid + 600 small); EDGAR assets
for 1495 names with data, ~1303 in the sort each month; monthly rebalance, 10bps.
**Net Sharpe −0.56, ann. −1.84%, max DD −33%, hit rate 44%.** Benchmark equal-weight 1.01.

Widening 60 mega-caps → 1495 broad names moved the strategy **−0.78 → −0.56**: the mega-cap
"short the decade's winners" artifact largely disappeared, leaving a weak *negative* — i.e. the
low-asset-growth premium is simply **absent in the 2010–2026 growth regime** on this data, not
violently inverted. Not the anomaly working; not the catastrophe either.

Data-quality note (caught + fixed this run): the raw wide run showed a −107% max DD — impossible
for a diversified book. Traced to **CHRD (Chord Energy) Nov-2020, a fake +30,991% monthly return**
(post-bankruptcy reverse split off a near-zero delisted-shell price in yfinance). Fixed by
winsorizing monthly returns to [−90%, +300%]. Free monthly price data has corporate-action landmines.

## Next
1. **Still current-membership → survivorship-biased.** A real verdict needs point-in-time membership
   (WRDS/CRSP). 2010–2026 is also a single growth-favoring regime vs the anomaly's 1968–2003 sample.
2. Neutralize size/sector before sorting (asset growth correlates with size) — feasible now with breadth.
3. Test the low-turnover annual-hold version net of Novy-Marx-Velikov costs explicitly.

## Result — size/sector-NEUTRAL + corrected construction (2026-07-07)
Added `neutralize.py`: each month, residualize the contrarian score against log-size + sector
dummies (score ~ log(assets) + C(sector)), so the L/S is orthogonal to size and sector.

**While wiring it, found + fixed two real bugs** that had inflated the earlier −0.56:
1. `asset_growth` computed YoY on panel-row adjacency, and `pct_change` default `fill_method='pad'`
   densified the sparse multi-fiscal-year-end panel → a fabricated dense score. Fixed: per-company
   YoY on each firm's own consecutive reports (`fill_method` none).
2. `to_monthly` used `reindex(method='ffill')`, which grabs ONE source row per month — on a sparse
   panel that collapsed the size panel to ~13 names/month. Fixed: true per-column as-of ffill.

Corrected wide-universe numbers (2010–2026, ~194–269 names/month, 10bps):
| Variant | Net Sharpe | Ann. | Max DD |
| ------- | ---------- | ---- | ------ |
| Raw (corrected) | **0.01** | 0.13% | −40% |
| **Size/sector-neutral** | **0.01** | 0.06% | −42% |

**The neutralization did its job: the (absent) effect is NOT a hidden size/sector tilt** — raw and
neutral are identical (~0). The contrarian asset-growth premium is simply **flat** on 2010–2026
free data, in either form. The earlier −0.56 was mostly the construction artifact, not signal.

## Verdict for HYP-006
**Flat — no premium, and confirmed not a disguised size/sector bet.** A clean verdict on the
*anomaly itself* still needs point-in-time membership (WRDS, kills survivorship) and ideally a
market-cap size proxy (vs book assets). But size/sector neutralization is done and it changed
nothing → the signal isn't there to neutralize in this era/data. Kristen's Stage-4 call.
