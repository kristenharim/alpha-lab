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

## Next
1. **Right test needs breadth + small caps + point-in-time membership → WRDS/Compustat.** Until then
   this track can't fairly evaluate the anomaly. Flag as blocked for a real verdict.
2. Interim free-data option: widen to a few hundred names via a broader EDGAR pull (Russell-1000-ish
   ticker list) — still survivorship-biased but enough breadth to see the small-cap tilt.
3. Neutralize size/sector before sorting (the anomaly is partly a size story) — needs more names first.

## Verdict for HYP-006
**Inconclusive — wrong test bed.** Not evidence against Cooper-Gulen-Schill; evidence that you
can't test a broad cross-sectional anomaly on 60 mega-caps. Real verdict gated on a wider universe.
