# alpha-lab

Personal quant signal-research monorepo. Reproduce a published edge, attack it honestly, and keep the
dead ones. One shared, honest scorecard judges every strategy. **Paper trading only. Nothing here
places real orders.**

**[▶ Live dashboard](https://rimrim05.github.io/alpha-lab/dashboard.html)** · **[QuantStats tearsheet](https://rimrim05.github.io/alpha-lab/reports/statarb_tearsheet_costs.html)** · **[research notebook](notebooks/statarb_research.ipynb)**

The flagship track (`tracks/statarb`) carries a full research workflow end to end: a market-neutral
statistical-arbitrage strategy, seven survivorship audits, a production-layer ablation, a per-signal
outcome log, and a leakage-safe meta-model, packaged as a QuantStats tearsheet and a notebook.

---

## Featured result: can you predict which signals mean-revert?

The residual-reversion model *generates* signals. A separate meta-model *scores* them: given a signal
at entry, what is the probability it reverts? If we trade only the highest-confidence signals instead
of every signal, does the book improve out of sample?

The threshold is pre-registered on earlier trades and reported on held-out later trades. Reported as-is.
Everything below is on the equal-weight S&P 500 book whose ungated Sharpe *is* the audited 2.67. The
`daily Sharpe` column is a real engine number: sub-threshold signals are zeroed out of the positions
matrix and run through the exact path that produces the 2.67, not a trade reconstruction.

| arm | trades | win rate | mean P&L | per-trade Sharpe | daily Sharpe (held-out) |
| --- | ------ | -------- | -------- | ---------------- | ----------------------- |
| ungated (trade every signal) | 12,295 | 70.2% | 0.0131 | 0.25 | 2.65 |
| gated (top ~16%, p ≥ 0.75) | 1,959 | **76.3%** | **0.0277** | **0.45** | **4.08** |

The ungated full-period Sharpe reproduces **2.67 exactly**, which proves the gating runs through the
real engine; the ungated held-out Sharpe (2.65) anchors the comparison. Gating the top-confidence
signals lifts the held-out daily Sharpe to 4.08.

The honest read: walk-forward AUC is only **0.54**. Signal quality is largely *unpredictable* from
entry features alone, consistent with an efficient reversion signal, yet a top-confidence cut still
adds real value. Caveat kept in view: this is one pre-registered held-out split, not cross-validated,
so read the lift as directional. The leakage guards (entry-time-only features + walk-forward) are what
keep that AUC honest rather than a suspiciously perfect 0.9 that dies forward.

See the full walk-through in **[`notebooks/statarb_research.ipynb`](notebooks/statarb_research.ipynb)**.

## Which production layers actually matter (ablation)

Each layer is toggled independently; the sweep runs the full S&P 500 over 2018 to present, net of costs.

| config | Sharpe | max DD | note |
| ------ | ------ | ------ | ---- |
| baseline (signal only) | 3.80 | -5.7% | pre-cost, not tradable |
| + transaction costs (10 bps) | **2.67** | -6.3% | the audited headline number |
| + liquidity filter | 2.65 | -6.3% | drops sub-$5M-ADV names |
| + sector / name caps | 2.44 | -6.5% | concentration limits |
| + earnings blackout (all on) | 2.43 | -6.5% | skip entries around earnings |

Costs are the dominant haircut (3.80 to 2.67). The book survives the full production stack at Sharpe
2.43. Every layer's marginal effect is measured, not asserted.

## Why you can trust the 2.67

Avellaneda and Lee (2010) residual reversion: regress each stock on its sector ETF, trade the
mean-reverting idiosyncratic residual via an OU s-score. Net of 10 bps, dollar-neutral, no look-ahead.
It survived seven skeptical audits (skip-a-day, winsorization, large-cap-only, 20-trial deflation,
point-in-time membership, falling-knife stress). The one unresolved risk is delisting survivorship,
which brackets the true Sharpe at roughly **1.7 (robust core) to 2.50 (point-in-time upper bound)**.
The decisive test is forward paper trading (survivorship-immune by construction); it is **now running
live on Alpaca paper** (Stage 5), staged pre-open every weekday by a GitHub Actions cron. The machinery
lives in `tracks/statarb/paper/`, and the live book (NAV, day P&L, positions) is on the
**[dashboard](https://rimrim05.github.io/alpha-lab/dashboard.html)**. Paper only — a forward test, not a
track record; the bracket Sharpe stays noisy until ~12 months accrue.

## Deliverables

- **[`notebooks/statarb_research.ipynb`](notebooks/statarb_research.ipynb)** the research narrative,
  runs top to bottom.
- **[`reports/statarb_tearsheet_costs.html`](https://rimrim05.github.io/alpha-lab/reports/statarb_tearsheet_costs.html)** the QuantStats tearsheet of the *backtest* (curated; re-render when the ablation re-runs).
- **[`reports/statarb_paper_live_tearsheet.html`](https://rimrim05.github.io/alpha-lab/reports/statarb_paper_live_tearsheet.html)** the QuantStats tearsheet of the *live paper book*, regenerated nightly by the cron (placeholder until 20 sessions accrue).
- **`reports/shap_beeswarm_costs.png`** SHAP attribution for the meta-model.
- **`audit-bundle/`** a self-contained reproducibility package (spec, code, recompute steps, return series).
- **[`dashboard.html`](https://rimrim05.github.io/alpha-lab/dashboard.html)** an at-a-glance project overview (the fun extra).

## The research program (one scorecard, honest verdicts)

Dead strategies with clean post-mortems are the portfolio. Every track is judged by the same
`core/eval/scorecard.py` (net-of-cost Sharpe, deflated Sharpe, subperiods).

| track | source of edge | verdict |
| ----- | -------------- | ------- |
| statarb residual reversion | structural (liquidity) | **alive**, survivorship-bracketed — **live on paper (Stage 5)** |
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
.venv/bin/pytest                                   # 69 tests, incl. the parity gate
.venv/bin/python scripts/statarb_ablation_run.py   # the ablation sweep + per-signal logs

# reporting / ML stack (isolated env; keeps the audited env pristine)
python3 -m venv .venv-report && .venv-report/bin/pip install -e ".[report,ml]"
.venv-report/bin/python reports/tearsheet.py --config costs
.venv-report/bin/python -m tracks.statarb.ml.evaluate --config costs
```

The backtest runs in `.venv`; the reporting and ML layer runs in an isolated `.venv-report` and only
reads the artifacts the backtest wrote. The backtest is never re-run inside a notebook, which is what
keeps the headline number honest.
