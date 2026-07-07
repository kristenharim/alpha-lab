# STATE — GKX signal rotation (Gu-Kelly-Xiu, lite)

**Stage:** 1 (data + model ladder run on public CZ data); firm-level GKX blocked on WRDS
**Last session:** 2026-07-07

## Scope decision (Decision B in spec)
Full GKX predicts the firm-level cross-section from ~94 characteristics — that needs
CRSP/Compustat (WRDS), which isn't available yet. Instead this track runs GKX-lite: the
same expanding-window ML method applied at the SIGNAL level, using the Chen-Zimmermann
Open Source Asset Pricing published long-short portfolios (212 signals). It's a factor-
timing study (predict next month's signal returns, rotate), not the firm-level replication.

## Built
- `cz_data.py` — `download_cz_portfolios` (openassetpricing `dl_port('op')`),
  `load_cz_long_short` (filters port=='LS', converts percent→decimal), `validate_panel`
- `models.py` — features (12m factor momentum, 12m vol) → next-month return;
  expanding window, **annual refit** (`refit_every=12`), models OLS/Ridge/GBRT
- `scripts/gkx_run.py` — download → ladder → signal-rotation L/S → scorecard
- Tests 4/4 green.

## Data notes (learned this session)
- `dl_port('op')` returns DECILE portfolios (port "01".."10") + long-short ("LS") per
  signal, `ret` in PERCENT. Use LS only, /100. (First run mis-fed all deciles as one
  series — fixed.)
- Monthly GBRT refit measured at **886s** (~15 min) — impractical and not what GKX does.
  GKX retrains ANNUALLY on an expanding window; `refit_every=12` matches the paper and
  cuts runtime ~12×. 212 signals × 540 months (1980+ default window).

## Alignment (verified with a toy check, in-session)
`expanding_window_predict` returns y_true[t] = forward (t→t+1) return that score[t]
forecasts. `core.backtest` lags weights internally, so the runner feeds `actual.shift(1)`
— pairing weight(t) with y_true(t), realization dated t+1. No look-ahead.

## Result
*Run in progress (annual refit). Paste scorecard here + into HYP-004 when done.*

## Next
1. Read scorecard: net Sharpe per model, deflated-Sharpe prob (3-model haircut), subperiods.
2. Verdict vs HYP-004 kill criteria (net Sharpe < 0.3 or deflated prob < 50% → dead).
3. If alive: add more features (factor value/BM spread, macro), widen model ladder.
4. Full firm-level GKX remains gated on WRDS — the real replication, deferred.
