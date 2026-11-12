# alpha-lab — history & negative-result registry

The forward-looking front page is [`README.md`](README.md). This file is the record of everything
that came before the current forward test — kept in full, because **dead strategies with clean
post-mortems are the portfolio**. Nothing here is a live claim.

---

## The featured post-mortem — a Sharpe-3.8 backtest, retired

A market-neutral stat-arb strategy backtested at **3.80 gross Sharpe** and survived seven robustness
checks before the accounting flaw was found: P&L was scored in *residual space*, crediting each
position with its own trailing drift, which no hedge can earn. Decomposing identical positions on
identical data (an exact accounting identity) split the headline:

| book | gross Sharpe | ann. return |
| ---- | :----------: | :---------: |
| residual book (what the old engine scored) | **3.80** | +17.9% |
| raw stock book (implementable baseline) | 0.30 | +2.0% |
| beta-hedged book (implementable) | 0.42 | +2.0% |

The engine was corrected to book only implementable returns, a pre-registered salvage failed, and the
strategy was retired. **Full write-up → [`CASE_STUDY.md`](CASE_STUDY.md).** The house rule it produced:
*an audit suite must test the P&L definition, not just the signal and the data.*

## The original five tracks — one scorecard, honest verdicts

Every track judged by the same [`core/eval/scorecard.py`](core/eval/scorecard.py), one yardstick, no
per-strategy goalposts.

| track | source of edge | verdict |
| ----- | -------------- | ------- |
| statarb residual reversion | structural (liquidity) | **dead** (Stage 4): P&L was residual-space; implementable edge ~4× below costs |
| GKX signal rotation | behavioral (factor momentum) | **dead** (Stage 4): rotation & PC-timing both lose to equal-weight |
| PEAD drift | behavioral (underreaction) | promising, +8.45% 60-day drift, caveated |
| asset-growth contrarian | behavioral (glamour) | flat, no premium this era |
| LLM headline sentiment | informational | specified, data-blocked |

## hunt2026 — blind-holdout tournament

Discovery under a frozen protocol: 18 total specs, kill criteria written before the data, post-cut
files chmod-000 during building, specs frozen in git before unlock.

- **Round 1 (1-year blind):** 14 specs; 11 beat +18% but SPY did +21%; beta-matched excess is the
  real number. Survivors: momentum_concentrated, dual_momentum, gap_drift.
- **Round 2 (5-year backdated, fully blind through the 2022 bear):** 4 ETF specs, literature-default
  params fit ≤ 2021. **3 of 4 passed, and the pass spanned a bear year.** Headline:
  **defensive_ensemble +19.9% CAGR, Sharpe 1.32, −13.4% maxDD, flat through 2022.**

Verdicts: [`memos/hunt2026-verdict.md`](memos/hunt2026-verdict.md),
[`memos/hunt2026-5y-verdict.md`](memos/hunt2026-5y-verdict.md).

## James-Stein / factor-risk program (2026-07-14)

An autonomous program with pre-frozen preregs answering two questions on the live book:

- **Q1, real residual alpha?** No. **Factor-premium harvesting**: no book clears blind-window t ≥ 2
  alpha; the four best-looking cells each decompose into gold beta, financing, one 2022 regime, or an
  empty cell. The books are competent implementations of published premia, not idiosyncratic alpha.
- **Q2, does James-Stein shrinkage help?** No deployment-material value anywhere. The one real effect
  (long-only min-var vol reduction) is capped at ~2.6 bps/yr and shrinks with p/n; harmful with shorts;
  10 preregistered experiments null or harmful. It's a **structural null**: ψ̂₁ ≈ 0.98–1.00 at S&P
  scale, so there's nothing for the correction to correct. MP eigenvalue clipping won wherever
  risk-model quality mattered.

Final memo: [`memos/js-factor-program-final-2026-07-14.md`](memos/js-factor-program-final-2026-07-14.md).
This program is what set the current forward test's benchmark and label.

---

*Reproducibility package for the retired statarb work → [`reports/audit-bundle/`](reports/audit-bundle/).
All verdict memos live in [`memos/`](memos/).*
