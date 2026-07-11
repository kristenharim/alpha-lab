# alpha-lab

Personal quant signal-research monorepo. Reproduce a published edge, attack it honestly, and keep the
dead ones. One shared, honest scorecard judges every strategy. **Paper trading only. Nothing here
places real orders.**

**[▶ Live dashboard](https://rimrim05.github.io/alpha-lab/dashboard.html)** · **[QuantStats tearsheet](https://rimrim05.github.io/alpha-lab/reports/statarb_tearsheet_costs.html)** · **[research notebook](notebooks/statarb_research.ipynb)**

The flagship track (`tracks/statarb`) carries a full research lifecycle end to end — a market-neutral
statistical-arbitrage strategy taken through seven robustness audits, a production-layer ablation, a
per-signal outcome log, a meta-model, live paper trading, and finally a **Stage-4 kill**: the headline
result was traced to a subtle implementability bug, the fix was applied to the engine, a pre-registered
salvage was attempted, and the strategy was retired. The post-mortem is the deliverable.

---

## Featured result: a Sharpe-3.8 backtest, killed by implementability accounting

The strategy (Avellaneda-Lee residual reversion on the S&P 500) originally backtested at **2.67 net
Sharpe** and survived seven robustness audits — look-ahead, winsorization, point-in-time membership,
deflated Sharpe, falling-knife stress. It was live on Alpaca paper when a diagnostic decomposition
found the real problem: the engine scored P&L in **residual space** (`held x residual`), and the
trailing-alpha term the residual subtracts is each name's own drift — **not a factor exposure, so no
hedge can remove it**. Decomposing identical positions on identical data (an exact accounting
identity):

| book | gross Sharpe | ann. return |
| ---- | ------------ | ----------- |
| residual book (what the old engine scored) | 3.80 | +17.9% |
| raw stock book (what a live book holds) | 0.30 | +2.0% |
| beta-hedged book (stock − beta·ETF, implementable) | 0.42 | +2.0% |

The engine was fixed to score hedged returns plus the hedge overlay's own costs, and the one
theoretically-motivated rescue — Avellaneda-Lee's drift-corrected s-score, pre-registered as a single
trial with zero tuned parameters — was attempted: gross improved (0.28 → 0.35) but the added churn
made net worse (−0.88 → −1.06). **Verdict: dead.** The real reversion edge on daily large caps is
~1.3–1.6%/yr gross against ~5.3%/yr of turnover costs — a 4x gap, not a tuning distance. Full
post-mortem: [`memos/diagnostics-2026-07-10.md`](memos/diagnostics-2026-07-10.md).

## Which production layers actually matter (ablation)

Each layer is toggled independently; the sweep runs the full S&P 500 over 2018 to present, net of costs.

Post-fix (implementable P&L: hedged returns + overlay costs):

| config | Sharpe | max DD | note |
| ------ | ------ | ------ | ---- |
| baseline (signal only, no costs) | 0.28 | -10.6% | the real gross edge: ~1.3%/yr |
| + transaction costs (10 bps) | **-0.88** | -30.4% | costs ~4x the gross edge |
| + liquidity filter | -0.89 | -30.4% | drops sub-$5M-ADV names |
| + sector / name caps | -1.10 | -35.0% | concentration limits |
| + earnings blackout (all on) | -1.12 | -35.0% | skip entries around earnings |

(The same table under the old residual-space engine read 3.80 / 2.67 / 2.65 / 2.44 / 2.43 — the gap
between the two tables is the unhedgeable trailing-alpha term.) Every layer's marginal effect is
measured, not asserted.

## Methodology, and how the bug survived seven audits

Avellaneda and Lee (2010) residual reversion: regress each stock on its sector ETF, trade the
mean-reverting idiosyncratic residual via an OU s-score. Dollar-neutral, lagged betas, skip-a-day
execution, deflated Sharpe with honest trial counts — the discipline was real, and seven robustness
audits (look-ahead, winsorization, large-cap-only, 20-trial deflation, point-in-time membership,
falling-knife stress) all passed. They passed because they all tested the *signal and the data*; none
tested the *P&L definition*. Scoring `held x residual` implicitly credits the book with each name's
trailing drift — the same dislocation that triggers an entry drags the drift estimate against the
position, so subtracting it books ~6 bps/day of accounting profit per position whether or not the
stock reverts. The lesson, now a house rule: **an audit suite must include "is this P&L earnable by a
portfolio?"** The engine now scores hedged returns (stock − lagged-beta x sector ETF) and charges the
hedge overlay's turnover; the paper-trading machinery in `tracks/statarb/paper/` remains as
infrastructure (the nightly cron is disabled — verdict called before the forward test had to catch
it).

## Deliverables

- **[`notebooks/statarb_research.ipynb`](notebooks/statarb_research.ipynb)** the research narrative
  (pre-fix numbers; superseded by the post-mortem, kept for the record).
- **[`memos/diagnostics-2026-07-10.md`](memos/diagnostics-2026-07-10.md)** the post-mortem: the
  decomposition, the engine fix, the pre-registered salvage, the verdict.
- **[`reports/statarb_tearsheet_costs.html`](https://rimrim05.github.io/alpha-lab/reports/statarb_tearsheet_costs.html)** the QuantStats tearsheet of the *pre-fix* backtest (kept as the historical artifact the post-mortem dissects).
- **[`reports/statarb_paper_live_tearsheet.html`](https://rimrim05.github.io/alpha-lab/reports/statarb_paper_live_tearsheet.html)** the live-paper tearsheet (cron disabled at verdict; frozen).
- **`reports/shap_beeswarm_costs.png`** SHAP attribution for the meta-model.
- **`audit-bundle/`** a self-contained reproducibility package (spec, code, recompute steps, return series).
- **[`dashboard.html`](https://rimrim05.github.io/alpha-lab/dashboard.html)** an at-a-glance project overview.

## The research program (one scorecard, honest verdicts)

Dead strategies with clean post-mortems are the portfolio. Every track is judged by the same
`core/eval/scorecard.py` (net-of-cost Sharpe, deflated Sharpe, subperiods).

| track | source of edge | verdict |
| ----- | -------------- | ------- |
| statarb residual reversion | structural (liquidity) | **dead** (Stage 4) — P&L was residual-space; implementable edge 4x below costs |
| PEAD drift | behavioral (underreaction) | promising, +8.45% 60-day drift, caveated |
| asset-growth contrarian | behavioral (glamour) | flat, no premium this era |
| GKX signal rotation | behavioral (factor momentum) | **dead** (Stage 4) — rotation & PC-timing both lose to equal-weight |
| LLM headline sentiment | informational | specified, awaiting data |

## Lifecycle (stage-gate, every track)

| stage | gate |
| ----- | ---- |
| 0 Hypothesis | mechanism, kill criteria, OOS protocol written before data |
| 1 Data build | point-in-time dataset + lineage manifest |
| 2 Replication | reproduce the paper's headline (validates pipeline, not alpha) |
| 3 OOS + robustness | net of costs, deflated Sharpe, subperiods, decay |
| 4 Verdict | kill-or-promote memo |
| 5 Paper trading | forward, survivorship-immune |

## Layout

- `core/` shared data loaders, backtest engine, evaluation scorecard, broker adapter.
- `tracks/` one package per research track; `tracks/statarb/` holds the signal, filters, per-signal
  log, ML meta-model, and paper-book scaffold.
- `scripts/` network pulls and runners (`statarb_ablation_run.py` is the main sweep).
- `reports/`, `notebooks/` committed deliverables.
- `data/`, `artifacts/` gitignored heavy files; scorecards and the manifest are the durable record.

## Reproduce

```bash
python3 -m venv .venv && .venv/bin/pip install -e ".[dev]"
.venv/bin/pytest                                   # full suite, incl. the parity gate
.venv/bin/python scripts/statarb_ablation_run.py   # the ablation sweep + per-signal logs

# reporting / ML stack (isolated env; keeps the audited env pristine)
python3 -m venv .venv-report && .venv-report/bin/pip install -e ".[report,ml]"
.venv-report/bin/python reports/tearsheet.py --config costs
.venv-report/bin/python -m tracks.statarb.ml.evaluate --config costs
```

The backtest runs in `.venv`; the reporting and ML layer runs in an isolated `.venv-report` and only
reads the artifacts the backtest wrote. The backtest is never re-run inside a notebook, which keeps the
headline number reproducible.
