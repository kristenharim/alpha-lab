### EXP-2026-09-16-volfamily-crsp

Written and committed before any scoring run. Stage 0/4 delegated by Kristen on 2026-09-16.

**Hypothesis.** Volatility-managed index exposure (Moreira and Muir 2017), with or without a 200-day
trend gate (Faber 2007), earns a higher Sharpe than a buy-and-hold index position held at the same
average leverage, because volatility is persistent while expected returns do not rise one-for-one
with it. The two frozen live specs that express this, vol_managed_qqq and trend_vol_qqq, are tested
as designs on the longest clean daily index history available.

**Layer touched.** A (economic). Baseline: the same index held at the spec's average gross exposure,
with the unlevered part earning the T-bill rate and the levered part paying it.

**Alpha type tag.** market

**Data and mapping.** CRSP daily S&P 500 value-weighted total return (`crsp.dsp500.vwretd`) stands in
for QQQ; the Fama-French daily T-bill rate stands in for BIL. Specs, parameters and harness are
unchanged (sigma target 25%, 21-day realized vol, 200-day SMA, 2x cap, 2 bps/side as the ETF rate).
Every day's P&L adds rf × (1 − gross held): cash earns the bill rate, leverage pays it.

**Evaluators.**
- **A, primary, never seen:** 1928-01-01 → 2004-12-31. Parameters were fit on QQQ from 2005 onward,
  so this is out of sample in time and in asset.
- **B, secondary:** 2005-01-01 → 2024-12-31, the era the parameters were fit in. Informs only.

**Expected result.** Both specs beat the leverage-matched index on Sharpe in A by 0.1–0.3, with
alpha to the index positive and t near 2 over 77 years; trend_vol_qqq shows the smaller max drawdown.

**Alternative result.** Sharpe no better than the leverage-matched index, alpha t below 2: the live
books are leveraged beta and the vol timing adds nothing after financing.

**Decision rule (one trial each, no tuning):**
1. For each spec in A: "alpha" if the CAPM alpha to the index has Newey-West t ≥ 2 AND net Sharpe
   exceeds the leverage-matched index. Otherwise "beta."
2. The live book keeps **one** representative of this family (the two are identical in live trading).
   It is the spec with the higher net Sharpe in A; the other retires.
3. vol_core_svxy cannot be tested (SVXY and VIX have no pre-2004 history), carries short-volatility
   tail risk, had negative fitted alpha (−6.06%, t −1.05) and correlates 0.96 with trend_vol_qqq in
   live trading. It retires regardless of this experiment.
4. If both specs are "beta," the kept one is labeled a leveraged-beta sleeve in the manifest, sized
   like any other book, and reported against leverage-matched S&P rather than as alpha.

**n_trials.** 2 (one per spec).

**Result.** (appended below after the run)
