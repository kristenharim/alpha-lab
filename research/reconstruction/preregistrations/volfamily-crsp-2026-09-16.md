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

---

**Result (2026-09-16).** Run: `research/reconstruction/volfamily_crsp.py`, output `volfamily_crsp_results.json`.

| Spec | Evaluator | CAGR | Sharpe | Max DD | Avg index gross | Baseline CAGR | Baseline Sharpe | Baseline max DD | CAPM alpha/yr | NW t | Beta |
|:--|:--|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|
| vol_managed_qqq | A 1928–2004 | 13.2% | 0.65 | −82% | 1.70 | 11.5% | 0.51 | −97% | +3.5% | 2.91 | 1.23 |
| vol_managed_qqq | B 2005–2024 | 16.4% | 0.77 | −52% | 1.65 | 14.3% | 0.58 | −76% | +3.8% | 1.64 | 1.27 |
| trend_vol_qqq | A 1928–2004 | 14.8% | 0.84 | −63% | 1.26 | 10.4% | 0.55 | −92% | +7.9% | 4.20 | 0.69 |
| trend_vol_qqq | B 2005–2024 | 12.5% | 0.69 | −31% | 1.44 | 13.2% | 0.59 | −70% | +4.2% | 1.24 | 0.82 |

**Decision rule applied.** Both specs are "alpha" in A (t ≥ 2 and Sharpe above the leverage-matched
index). trend_vol_qqq has the higher Sharpe in A: **kept**. vol_managed_qqq: **retired**.
vol_core_svxy: **retired** per rule 3.

**Descriptive, not pre-registered** (sub-periods, same construction):

| Spec | Period | Sharpe | Same-leverage index Sharpe | Alpha/yr | t | Max DD | Index max DD |
|:--|:--|--:|--:|--:|--:|--:|--:|
| trend_vol_qqq | 1928–1945 | 0.57 | 0.28 | +9.2% | 1.8 | −63% | −84% |
| trend_vol_qqq | 1946–1974 | 1.05 | 0.71 | +7.4% | 2.9 | −31% | −59% |
| trend_vol_qqq | 1975–2004 | 0.87 | 0.79 | +2.8% | 1.1 | −35% | −61% |
| trend_vol_qqq | 2005–2024 | 0.69 | 0.59 | +4.2% | 1.2 | −31% | −70% |

trend_vol_qqq beat the same-leverage index on Sharpe in every era and roughly halved drawdowns;
its alpha has shrunk since 1975. The durable part is risk control; the return edge is modest.
Caveat: tested on the S&P 500, not the Nasdaq-100 it trades live.
