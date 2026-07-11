# hunt2026 spec conventions (frozen — builders read this, then never touch holdout)

Each spec is a directory `specs/<name>/` containing:

- `spec.py` — standalone module exposing `target_weights(panel) -> pd.DataFrame`.
  Loads its own `params.json` from `Path(__file__).parent`. No imports from other
  specs. May import from `tracks/` / `core/` if genuinely shared.
- `params.json` — ALL tunable parameters, **≤ 3**, fit on train data only.
- `MECHANISM.md` — one paragraph: the economic mechanism (who is on the other side,
  why the edge persists), plus the falsifier: what forward evidence would kill it.

## Interface contract

- `panel`: MultiIndex-column DataFrame, level 0 field ∈ {open, close, volume, member},
  level 1 ticker. `panel["close"]` etc. Adjusted prices. `member` is the point-in-time
  S&P 500 mask (floats 0/1; ETFs always 1). `^VIX` is signal-only — weight must be 0.
- Return daily target weights (fraction of NAV) set at each date's close using info
  through that close. The harness lags one day and scores close-to-close — do NOT lag
  yourself, do NOT peek (no `.shift(-k)`, no full-sample fits, no using the panel's
  last date as "today").
- Gross exposure ≤ 2.0 every day (harness clips and counts violations — a violation
  means your spec is broken).
- Costs charged by the harness: 10 bps/side stocks, 2 bps/side ETFs, on |Δweight|.
  Turnover is YOUR enemy; 100%/day one-way at 10 bps = 25%/yr drag.
- P&L must be implementable — weights on real tickers only, no residual-space
  accounting (see memos/diagnostics-2026-07-10.md for the corpse that rule is named
  after).

## Fitting rules

- Fit/validate on `harness.load_train()` ONLY. `load_full()` / `holdout.parquet` are
  evaluator-only; loading them disqualifies the spec.
- Suggested in-train validation: score on the last 1-2 train years
  (`harness.run(mod, train_panel, start="2023-07-10")`) — but the number that counts
  is the one blind year you never saw.
- Freeze means freeze: after submission, no edits. One shot.
