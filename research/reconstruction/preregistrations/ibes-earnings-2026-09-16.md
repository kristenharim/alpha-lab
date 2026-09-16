### EXP-2026-09-16-ibes-earnings

Written and committed before any scoring run. Stage 0 delegated by Kristen on 2026-09-16; she asked
for this lane specifically ("I/B/E/S earnings signals ... look more into this").

**Hypotheses (two signals, one mechanism).** Investors underreact to earnings news, so prices keep
drifting after it arrives:
1. **SUE (post-earnings-announcement drift, Bernard and Thomas 1989; analyst version Livnat and
   Mendenhall 2006).** Stocks whose quarterly EPS beat the analyst consensus outperform over the next
   three months.
2. **REV (analyst revision breadth, Chan, Jegadeesh and Lakonishok 1996).** Stocks whose analysts
   have, on net, been raising their current-year EPS estimate outperform.

**Layer touched.** A (economic). Baselines: Fama-French five factors plus UMD; for long-only
variants, the value-weighted return of the same universe.

**Alpha type tag.** market

**Data.**
- I/B/E/S unadjusted quarterly actuals (`ibes.actu_epsus`, `pdicity='QTR'`) and unadjusted summary
  consensus (`ibes.statsumu_epsus`): `fpi='6'` (current fiscal quarter) for SUE, `fpi='1'`
  (current fiscal year) for REV.
- Link I/B/E/S ticker → PERMNO with `wrdsapps.ibcrsphist`, score ≤ 2, date-bounded.
- Returns, prices and market equity from the validated CRSP monthly panel
  (`core/data/crsp.py`, delistings included).
- Factors from `ff.fivefactors_monthly` and `ff.factors_monthly` (UMD).

**Signal construction (no look-ahead).**
- **SUE** = (actual EPS − consensus mean) / |CRSP price| at the month-end before the announcement.
  The consensus is the last I/B/E/S summary dated strictly before the announcement date, for the same
  fiscal period end, and at most 90 days old. Unadjusted estimates, actuals and price share one share
  basis. Winsorized at 1%/99% each month.
- A SUE formed from an announcement in month m is usable for returns in months m+1, m+2 and m+3; each
  month uses the stock's most recent usable SUE.
- **REV** = mean over the last 3 monthly summaries (months t−3..t−1) of (numup − numdown) / numest for
  the current fiscal year. It is a count, so splits cannot contaminate it; requires numest ≥ 3.

**Universes (formed with month t−1 data).**
- **ALL:** CRSP common stocks, price ≥ $5, market equity above the NYSE 20th percentile.
- **LARGE:** the 500 largest by market equity. This is what the paper account can trade.

**Portfolios.** Each month, decile sorts on NYSE breakpoints (ALL) or universe breakpoints (LARGE),
value-weighted by last month's market equity.
- **LS:** top decile minus bottom decile.
- **LONG:** top decile minus the value-weighted universe.

**Costs.** Monthly turnover × per-side cost: 25 bps for ALL, 10 bps for LARGE, charged to every leg.

**Evaluators.**
- **Published era:** 1985-01 → 2004-12. Replication only: the signals should work here.
- **Primary, post-publication:** 2005-01 → 2024-12. This is the decision window.

**Trial count and threshold.** 2 signals × 2 universes × 2 portfolio types = 8 trials. A variant
counts only with a Newey-West t-stat ≥ 2.7 on its FF5 + UMD alpha, net of costs, in the primary
window. 2.7 is roughly a 5% two-sided test with a Bonferroni correction for 8 trials.

**Expected result.**
- Published era: SUE LS alpha 4–8%/yr with t > 3 in ALL; REV similar but smaller.
- Primary window: decay of half or more (McLean and Pontiff 2016); LARGE net alpha near zero;
  **no variant clears t ≥ 2.7 in LARGE.**

**Alternative result (what would change the live book).** A LARGE LONG or LARGE LS variant with net
alpha t ≥ 2.7 and net Sharpe ≥ 0.5 in 2005–2024.

**Decision rule.**
- If a LARGE variant clears the bar, write a frozen live spec for it and paper trade it in a new book
  under a separate pre-registration. It does not auto-deploy.
- If only ALL variants clear, record it as real but not implementable at this account's size and
  cost assumptions.
- If nothing clears, close the lane at this construction. No parameter search follows under this
  experiment.

**Result.** (appended below after the run)
