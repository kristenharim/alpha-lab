# From Sharpe 3.8 to Retirement: Auditing an Untradeable Stat-Arb Backtest

A single-strategy walkthrough of how a strong-looking backtest was traced to an accounting artifact,
corrected at the engine level, given one pre-registered rescue attempt, and retired, with the
post-mortem kept as the deliverable. **Paper-account orders only; no live capital.**

---

## The research question

Does the published residual-reversion strategy of Avellaneda and Lee (2010) produce an *implementable*
edge on liquid S&P 500 large caps? The method: regress each stock on its sector ETF, and trade the
mean-reverting idiosyncratic residual via an Ornstein-Uhlenbeck s-score. Dollar-neutral, lagged betas,
skip-a-day execution. The question was never "can a backtest look good"; it was "can a real portfolio
hold this."

## The initial result

The strategy backtested at **2.67 net Sharpe / 3.80 gross Sharpe** and survived a seven-audit
robustness gauntlet: look-ahead checks, winsorization sensitivity, large-cap-only restriction,
20-trial deflated Sharpe, point-in-time index membership, and falling-knife stress. Each audit passed.
On that basis the strategy was promoted to live Alpaca paper trading.

## The validation protocol

Every track in the repo moves through the same stage gate, and this one was no exception:

| stage | gate |
| ----- | ---- |
| 0 Hypothesis | mechanism, kill criteria, and OOS protocol written *before* data |
| 1 Data build | point-in-time dataset + lineage manifest |
| 2 Replication | reproduce the paper's headline (validates the pipeline, not alpha) |
| 3 OOS + robustness | net of costs, deflated Sharpe, subperiods, decay |
| 4 Verdict | kill-or-promote memo |
| 5 Paper trading | forward, point-in-time controlled |

The discipline was real. Deflated Sharpe used honest trial counts; membership was as-of date, not
back-filled from today's index. The audits were not the problem. What they shared was the blind spot.

## The bug

While the strategy was live on paper, a diagnostic decomposition asked a question none of the seven
audits had: *is this P&L earnable by a portfolio?* The engine scored profit in **residual space** —
`held × residual` — where the residual subtracts each name's trailing alpha. That trailing-alpha term
is the stock's own drift. It is **not a factor exposure**, so no hedge can remove it, and no book can
actually capture it.

Decomposing identical positions on identical data (an exact accounting identity, not a re-simulation)
splits the headline number into what is real and what is not:

| book | gross Sharpe | annualized return |
| ---- | ------------ | ----------------- |
| residual book (what the old engine scored) | 3.80 | +17.9% |
| raw stock book (what a live book actually holds) | 0.30 | +2.0% |
| beta-hedged book (stock − beta·ETF, implementable) | 0.42 | +2.0% |

The gap between 3.80 and 0.42 was the unhedgeable trailing-alpha term, roughly 6 bps/day of accounting
profit booked per position whether or not the stock reverted. The audits passed because they all
interrogated the *signal and the data*; the flaw lived in the *P&L definition*.

## The correction

The engine was rebuilt to score only implementable returns: hedged returns (stock − lagged-beta ×
sector ETF) plus the turnover cost of the hedge overlay itself. Re-running the production-layer
ablation under the corrected engine tells the honest story:

| config | Sharpe | max DD | note |
| ------ | ------ | ------ | ---- |
| baseline (signal only, no costs) | 0.28 | -10.6% | the real gross edge: ~1.3%/yr |
| + transaction costs (10 bps) | **-0.88** | -30.4% | costs ~4× the gross edge |
| + liquidity filter | -0.89 | -30.4% | drops sub-$5M-ADV names |
| + sector / name caps | -1.10 | -35.0% | concentration limits |
| + earnings blackout (all on) | -1.12 | -35.0% | skip entries around earnings |

Under the old residual-space engine the same rows read 3.80 / 2.67 / 2.65 / 2.44 / 2.43. The distance
between the two tables *is* the accounting artifact. Every layer's marginal effect is now measured, not
asserted.

## The salvage

One theoretically-motivated rescue was warranted before calling it: Avellaneda-Lee's drift-corrected
s-score, which explicitly accounts for the trailing-drift term. It was **pre-registered as a single
trial with zero tuned parameters** — no search, no second bite. Gross improved (0.28 → 0.35), but the
added churn made net *worse* (−0.88 → −1.06). The rescue was a real hypothesis with a real prior, and
it failed cleanly.

## The verdict

**Dead.** The real reversion edge on daily large caps is ~1.3–1.6%/yr gross against ~5.3%/yr of
turnover costs, a roughly 4× gap. That is not a tuning distance; no parameter sweep closes a hole that
size. The strategy was retired at Stage 4, before the forward paper test had to be the thing that
caught it. The paper-trading machinery in `tracks/statarb/paper/` remains as infrastructure with its
nightly cron disabled.

## The lesson

The seven audits all tested the signal and the data, and all passed. The failure was one layer beneath
them, in how profit was defined. That is now a house rule for every track in the platform:

> **An audit suite must include the question "is this P&L earnable by a portfolio?" — not only "is the
> signal real and the data clean?"**

An implementable-P&L gate now sits in the shared engine, so the same class of error cannot recur
silently in the next strategy.

## What I would do next

The value of this result is not the dead strategy; it is the reusable check. The implementable-P&L
accounting, the exact-parity gate, and the negative-result registry are strategy-agnostic, and the
research program applies them uniformly across its tracks. The next steps are to carry the same
hedged-return standard into the behavioral tracks (PEAD drift, in particular) and to keep the estimator
experiments (PCA / JSE) benchmarked against the same scorecard, so no track can post a number the
platform's own accounting would reject.

## Engineering notes

- **Exact C++/Python parity:** the C++ band state machine must reproduce the pure-Python positions
  bit-for-bit (`tests/test_fastbands_parity.py`); positions are discrete state, so parity is exact,
  not approximate.
- **Isolated environments:** the backtest runs in `.venv`; the reporting and ML layer runs in a
  separate `.venv-report` that only *reads* the artifacts the backtest wrote. The headline number is
  never re-run inside a notebook.
- **Reproducibility:** `reports/audit-bundle/` is a self-contained package (spec, code, recompute steps,
  return series). The full post-mortem lives in `memos/diagnostics-2026-07-10.md`.

## My role and use of AI

I defined the research questions, validation protocol, architecture, and final verdicts. AI coding
agents assisted with implementation and documentation under repository tests and explicit governance
controls.
