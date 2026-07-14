# StatArb Ablation Harness + Per-Signal Log — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Turn the audited residual-reversion backtest into a toggle-ablation instrument that emits a counterfactual-labeled per-signal outcome log, without changing the headline Sharpe (2.67).

**Architecture:** Keep the vectorized signal/position math byte-for-byte (Approach A). Layers are pure functions that transform the positions matrix (liquidity, earnings blackout) or a derived weights matrix (sector cap). A refactored `run_residual()` is the single code path both the CLI runner and the ablation sweeper call; `extract_trades()` derives the per-signal log from the position matrices. All-layers-off reproduces today's net series bit-for-bit (parity gate).

**Tech Stack:** Python 3.11, pandas, numpy, pytest. No new dependencies. yfinance only at the script boundary (engine + filters are network-free and unit-tested).

## Global Constraints

- **Repo:** `~/projects/alpha-lab/`. Run everything via the venv: `.venv/bin/python`, `.venv/bin/pytest`.
- **Tests never touch the network** — network fetch stays in `scripts/` and in the two `fetch_*_yf` functions (which have no unit tests, matching the existing convention). Engine and filters take pre-built DataFrames and are fully offline-testable.
- **Parity is non-negotiable** — `run_residual` with all layers off must reproduce the current equal-weight P&L formula exactly (Task 5).
- **Positions matrix convention:** `pd.DataFrame`, index = dates (sorted, unique), columns = tickers, values ∈ {−1, 0, +1}. Weights matrix: same shape, float, row-wise dollar-neutral (Σ|w| ≈ 1).
- **Reuse, don't reinvent:** signal via `tracks.statarb.residual.rolling_residual`; positions via `tracks.statarb.bands.band_positions`; scoring via `core.eval.scorecard.scorecard` / `to_markdown`; JSONL via `tracks.statarb.paper.ledger.Ledger`; earnings via `tracks.pead.events.fetch_earnings_yf`.
- **Signal-log JSONL** lives under `artifacts/statarb/signal_log/` (gitignored). Schema is a superset-compatible union with the paper book's `positions.jsonl`.

---

### Task 1: Volume data + rolling dollar-ADV helper

**Files:**
- Modify: `core/data/prices.py` (append two functions)
- Test: `tests/test_prices.py` (append one test)

**Interfaces:**
- Produces: `fetch_volume_yf(tickers: list[str], start: str, end: str | None, chunk_size: int = 200) -> pd.DataFrame` (share volume, network — no test). `rolling_dollar_adv(prices: pd.DataFrame, volume: pd.DataFrame, window: int = 20) -> pd.DataFrame` (trailing median of price×volume; pure — tested).

- [ ] **Step 1: Write the failing test**

```python
def test_rolling_dollar_adv_median_of_price_times_volume():
    from core.data.prices import rolling_dollar_adv
    idx = pd.date_range("2024-01-01", periods=4, freq="B")
    px = pd.DataFrame({"A": [10.0, 10.0, 10.0, 10.0]}, index=idx)
    vol = pd.DataFrame({"A": [100.0, 300.0, 500.0, 700.0]}, index=idx)
    adv = rolling_dollar_adv(px, vol, window=2)
    # window=2 trailing median of (price*volume): [1000, 3000, 5000, 7000]
    assert pd.isna(adv["A"].iloc[0])                 # warm-up
    assert adv["A"].iloc[1] == 2000.0                # median(1000, 3000)
    assert adv["A"].iloc[3] == 6000.0                # median(5000, 7000)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/bin/pytest tests/test_prices.py::test_rolling_dollar_adv_median_of_price_times_volume -v`
Expected: FAIL with `ImportError: cannot import name 'rolling_dollar_adv'`

- [ ] **Step 3: Write minimal implementation**

Append to `core/data/prices.py`:

```python
def rolling_dollar_adv(prices: pd.DataFrame, volume: pd.DataFrame,
                       window: int = 20) -> pd.DataFrame:
    """Trailing median dollar volume (price x shares) per name — the liquidity gauge."""
    px, vol = prices.align(volume, join="inner")
    return (px * vol).rolling(window).median()


def fetch_volume_yf(tickers: list[str], start: str, end: str | None,
                    chunk_size: int = 200) -> pd.DataFrame:
    """Share volume from yfinance, same chunking as fetch_prices_yf. Network — script-only."""
    import yfinance as yf
    frames = []
    for i in range(0, len(tickers), chunk_size):
        batch = tickers[i:i + chunk_size]
        raw = yf.download(batch, start=start, end=end, interval="1d",
                          auto_adjust=True, progress=False)
        if raw.empty:
            continue
        vol = raw["Volume"] if isinstance(raw.columns, pd.MultiIndex) else \
            raw[["Volume"]].rename(columns={"Volume": batch[0]})
        frames.append(vol)
    if not frames:
        raise ValueError("no volume data returned")
    v = pd.concat(frames, axis=1).dropna(how="all")
    return v.loc[:, ~v.columns.duplicated()]
```

- [ ] **Step 4: Run test to verify it passes**

Run: `.venv/bin/pytest tests/test_prices.py::test_rolling_dollar_adv_median_of_price_times_volume -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add core/data/prices.py tests/test_prices.py
git commit -m "feat(statarb): rolling dollar-ADV helper + yfinance volume fetch"
```

---

### Task 2: Liquidity + earnings-blackout filters

**Files:**
- Create: `tracks/statarb/filters.py`
- Test: `tests/test_statarb_ablation.py`

**Interfaces:**
- Consumes: positions matrix ({−1,0,+1}); `dollar_adv` from Task 1.
- Produces:
  - `liquidity_filter(positions, dollar_adv, min_adv) -> tuple[pd.DataFrame, pd.DataFrame]` → (filtered positions, removed-mask). Zeros a position on days its trailing dollar-ADV < `min_adv`.
  - `earnings_window_mask(index, earnings, before, after, columns) -> pd.DataFrame` → bool mask, True within [−before, +after] trading days of any earnings date for that ticker.
  - `earnings_blackout(positions, blackout) -> tuple[pd.DataFrame, pd.DataFrame]` → (filtered, removed-mask). Blocks NEW entries during blackout; holds existing positions normally.

- [ ] **Step 1: Write the failing tests**

Create `tests/test_statarb_ablation.py`:

```python
import numpy as np
import pandas as pd
import pytest


def _idx(n):
    return pd.date_range("2024-01-01", periods=n, freq="B")


def test_liquidity_filter_zeros_illiquid_positions():
    from tracks.statarb.filters import liquidity_filter
    idx = _idx(3)
    pos = pd.DataFrame({"A": [1, 1, 1], "B": [-1, -1, -1]}, index=idx)
    adv = pd.DataFrame({"A": [9e6, 9e6, 9e6], "B": [1e6, 1e6, 1e6]}, index=idx)
    filtered, removed = liquidity_filter(pos, adv, min_adv=5e6)
    assert filtered["A"].tolist() == [1, 1, 1]       # liquid, kept
    assert filtered["B"].tolist() == [0, 0, 0]       # illiquid, zeroed
    assert removed["B"].all() and not removed["A"].any()


def test_earnings_window_mask_marks_window():
    from tracks.statarb.filters import earnings_window_mask
    idx = _idx(6)   # 2024-01-01 .. 2024-01-08 (business days)
    earn = pd.DataFrame({"ticker": ["A"], "date": [pd.Timestamp("2024-01-03")]})
    mask = earnings_window_mask(idx, earn, before=1, after=1, columns=["A", "B"])
    # earnings on idx[2]; window [idx[1], idx[3]] True for A, never for B
    assert mask["A"].tolist() == [False, True, True, True, False, False]
    assert not mask["B"].any()


def test_earnings_blackout_blocks_new_entry_but_holds_existing():
    from tracks.statarb.filters import earnings_blackout
    idx = _idx(4)
    # A tries to ENTER (0->1) during blackout on day1 -> blocked
    # B already HELD (1) entering blackout -> kept
    pos = pd.DataFrame({"A": [0, 1, 1, 0], "B": [1, 1, 1, 0]}, index=idx)
    blackout = pd.DataFrame({"A": [False, True, True, False],
                             "B": [False, True, True, False]}, index=idx)
    filtered, removed = earnings_blackout(pos, blackout)
    assert filtered["A"].tolist() == [0, 0, 0, 0]    # entry suppressed through window
    assert filtered["B"].tolist() == [1, 1, 1, 0]    # held position untouched
    assert removed["A"].iloc[1]
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `.venv/bin/pytest tests/test_statarb_ablation.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'tracks.statarb.filters'`

- [ ] **Step 3: Write minimal implementation**

Create `tracks/statarb/filters.py`:

```python
"""Composable production layers for the residual-reversion book.

Each filter is a pure function of the positions matrix plus pre-built context
(no network). Filters that gate entries return (filtered_positions, removed_mask)
so the signal log can attribute why a candidate was skipped. Sector-cap operates
on a weights matrix (see to_weights) because it reshapes exposure, not membership.
"""
import pandas as pd


def liquidity_filter(positions: pd.DataFrame, dollar_adv: pd.DataFrame,
                     min_adv: float) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Force flat any name whose trailing dollar-ADV is below min_adv that day."""
    adv = dollar_adv.reindex_like(positions)
    illiquid = adv < min_adv
    removed = (positions != 0) & illiquid
    return positions.mask(illiquid, 0), removed


def earnings_window_mask(index: pd.DatetimeIndex, earnings: pd.DataFrame,
                         before: int, after: int, columns: list[str]) -> pd.DataFrame:
    """Bool mask: True on trading days within [-before, +after] of a ticker's earnings."""
    mask = pd.DataFrame(False, index=index, columns=columns)
    pos_of = {d: i for i, d in enumerate(index)}
    for t, d in zip(earnings["ticker"], pd.to_datetime(earnings["date"])):
        if t not in mask.columns:
            continue
        # snap earnings date to the next trading day at/after it
        loc = index.searchsorted(d)
        for j in range(loc - before, loc + after + 1):
            if 0 <= j < len(index):
                mask.iat[j, mask.columns.get_loc(t)] = True
    return mask


def _blackout_col(pos_col: list, blackout_col: list) -> list:
    prev, out = 0, []
    for p, b in zip(pos_col, blackout_col):
        if b and prev == 0 and p != 0:   # would be a NEW entry inside the window -> block
            p = 0
        out.append(p)
        prev = p
    return out


def earnings_blackout(positions: pd.DataFrame,
                      blackout: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Block new entries during each name's blackout window; hold existing normally."""
    bo = blackout.reindex_like(positions).fillna(False)
    out = {c: _blackout_col(positions[c].tolist(), bo[c].tolist()) for c in positions.columns}
    filtered = pd.DataFrame(out, index=positions.index)
    removed = (positions != 0) & (filtered == 0)
    return filtered, removed
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `.venv/bin/pytest tests/test_statarb_ablation.py -v`
Expected: PASS (3 tests)

- [ ] **Step 5: Commit**

```bash
git add tracks/statarb/filters.py tests/test_statarb_ablation.py
git commit -m "feat(statarb): liquidity + earnings-blackout filters"
```

---

### Task 3: Weights + sector-cap filter

**Files:**
- Modify: `tracks/statarb/filters.py` (append two functions)
- Test: `tests/test_statarb_ablation.py` (append two tests)

**Interfaces:**
- Produces:
  - `to_weights(positions) -> pd.DataFrame` — equal-weight dollar-neutral: each row `positions / row.abs().sum()` (all-zero rows → 0).
  - `sector_cap(weights, sectors, name_cap, sector_cap_) -> pd.DataFrame` — clip |w| ≤ `name_cap`; scale each sector's day down if |net sector weight| > `sector_cap_`; renormalize each row back to gross 1.

- [ ] **Step 1: Write the failing tests**

Append to `tests/test_statarb_ablation.py`:

```python
def test_to_weights_equal_weight_dollar_neutral():
    from tracks.statarb.filters import to_weights
    idx = _idx(1)
    pos = pd.DataFrame({"A": [1], "B": [1], "C": [-1], "D": [0]}, index=idx)
    w = to_weights(pos)
    assert w.iloc[0].abs().sum() == pytest.approx(1.0)   # gross 1
    assert w["A"].iloc[0] == pytest.approx(1 / 3)
    assert w["C"].iloc[0] == pytest.approx(-1 / 3)
    assert w["D"].iloc[0] == 0.0


def test_sector_cap_limits_single_name_then_renormalizes():
    from tracks.statarb.filters import to_weights, sector_cap
    idx = _idx(1)
    pos = pd.DataFrame({"A": [1], "B": [1], "C": [1], "D": [-1]}, index=idx)
    w = to_weights(pos)                                   # each 0.25 / -0.25
    sectors = {"A": "tech", "B": "tech", "C": "tech", "D": "fin"}
    capped = sector_cap(w, sectors, name_cap=0.20, sector_cap_=1.0)
    # each name clipped to 0.20, then row renormalized to gross 1
    assert capped.iloc[0].abs().sum() == pytest.approx(1.0)
    assert (capped.iloc[0].abs() <= 0.20 + 1e-9).all() is np.bool_(False) or True  # post-renorm may exceed; see note
```

Note: the last assertion is intentionally loose — after renormalization a clipped weight can rise again; the meaningful invariant is gross = 1 and that the *pre-renorm* clip happened. Replace the loose line with the precise check below.

Replace that last assertion line with:

```python
    # pre-renorm clip is what we assert precisely: no name exceeds cap BEFORE renorm
    from tracks.statarb.filters import _apply_caps
    pre = _apply_caps(w, sectors, name_cap=0.20, sector_cap_=1.0)
    assert (pre.iloc[0].abs() <= 0.20 + 1e-9).all()
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `.venv/bin/pytest tests/test_statarb_ablation.py -k "weights or sector_cap" -v`
Expected: FAIL with `ImportError: cannot import name 'to_weights'`

- [ ] **Step 3: Write minimal implementation**

Append to `tracks/statarb/filters.py`:

```python
def to_weights(positions: pd.DataFrame) -> pd.DataFrame:
    """Equal-weight, dollar-neutral: row-normalize positions to gross exposure 1."""
    gross = positions.abs().sum(axis=1).replace(0, pd.NA)
    return positions.div(gross, axis=0).fillna(0.0)


def _apply_caps(weights: pd.DataFrame, sectors: dict,
                name_cap: float, sector_cap_: float) -> pd.DataFrame:
    w = weights.clip(lower=-name_cap, upper=name_cap)
    sec = pd.Series(sectors).reindex(w.columns)
    for s in sec.dropna().unique():
        cols = sec[sec == s].index
        net = w[cols].sum(axis=1)
        scale = (sector_cap_ / net.abs()).clip(upper=1.0).where(net.abs() > sector_cap_, 1.0)
        w[cols] = w[cols].mul(scale, axis=0)
    return w


def sector_cap(weights: pd.DataFrame, sectors: dict,
               name_cap: float, sector_cap_: float) -> pd.DataFrame:
    """Clip single-name and per-sector net exposure, then renormalize each row to gross 1."""
    w = _apply_caps(weights, sectors, name_cap, sector_cap_)
    gross = w.abs().sum(axis=1).replace(0, pd.NA)
    return w.div(gross, axis=0).fillna(0.0)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `.venv/bin/pytest tests/test_statarb_ablation.py -k "weights or sector_cap" -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add tracks/statarb/filters.py tests/test_statarb_ablation.py
git commit -m "feat(statarb): weights + sector/name exposure cap"
```

---

### Task 4: Per-signal outcome log extractor

**Files:**
- Create: `tracks/statarb/trades.py`
- Test: `tests/test_statarb_ablation.py` (append)

**Interfaces:**
- Consumes: `base_positions` (no filters), `final_positions` (after filters), `resid` (from `rolling_residual`), `s_scores`, feature DataFrames, `removed_by` (dict name→mask from Tasks 2–3).
- Produces:
  - `extract_trades(base_positions, final_positions, resid, s_scores, features, removed_by) -> list[dict]` — one row per candidate trade (a contiguous single-sign run in `base_positions`), with realized P&L if it survived filters, counterfactual P&L if it was skipped.
  - `trade_stats(trades) -> dict` → `{n_signals, n_entered, win_rate, avg_holding_days}`.
- **P&L convention (label-oriented):** trade P&L = Σ over the held run of `sign * resid[ticker]` (contemporaneous reversion captured). This is the *label* for "did this signal revert", distinct from the engine's cost-and-lag-adjusted headline net series. `success = pnl > 0`.

- [ ] **Step 1: Write the failing test**

Append to `tests/test_statarb_ablation.py`:

```python
def test_extract_trades_realized_counterfactual_and_stats():
    from tracks.statarb.trades import extract_trades, trade_stats
    idx = _idx(4)
    # A: one long run days1-2 (survives). B: one long run day1 (removed by a filter -> skipped)
    base = pd.DataFrame({"A": [0, 1, 1, 0], "B": [0, 1, 0, 0]}, index=idx)
    final = pd.DataFrame({"A": [0, 1, 1, 0], "B": [0, 0, 0, 0]}, index=idx)
    resid = pd.DataFrame({"A": [0.0, 0.02, 0.03, 0.0], "B": [0.0, -0.05, 0.0, 0.0]}, index=idx)
    s = pd.DataFrame({"A": [0.0, -1.4, -0.9, -0.2], "B": [0.0, -1.6, -0.2, 0.0]}, index=idx)
    feats = {"volatility": pd.DataFrame(0.2, index=idx, columns=["A", "B"]),
             "volume_ratio": pd.DataFrame(1.0, index=idx, columns=["A", "B"])}
    sectors = {"A": "tech", "B": "tech"}
    trades = extract_trades(base, final, resid, s, feats, sectors,
                            removed_by={"liquidity": (base != 0) & (final == 0)})
    by_t = {r["ticker"]: r for r in trades}
    assert by_t["A"]["entered"] is True
    assert by_t["A"]["realized_pnl"] == pytest.approx(0.05)     # +1*(0.02+0.03)
    assert by_t["A"]["holding_days"] == 2
    assert by_t["A"]["success"] is True
    assert by_t["B"]["entered"] is False
    assert by_t["B"]["counterfactual_pnl"] == pytest.approx(-0.05)  # would have lost
    assert "liquidity" in by_t["B"]["filters_blocked"]
    stats = trade_stats(trades)
    assert stats["n_signals"] == 2 and stats["n_entered"] == 1
    assert stats["win_rate"] == pytest.approx(1.0)             # 1 of 1 entered won
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/bin/pytest tests/test_statarb_ablation.py::test_extract_trades_realized_counterfactual_and_stats -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'tracks.statarb.trades'`

- [ ] **Step 3: Write minimal implementation**

Create `tracks/statarb/trades.py`:

```python
"""Per-signal outcome log: derive discrete trades (with counterfactuals) from the
position matrices. Schema unions with the paper book's positions.jsonl so backward
(here) and forward (paper) logs concatenate into one training set.
"""
import pandas as pd


def _runs(col: pd.Series):
    """Yield (start_i, end_i, sign) for each contiguous single-sign nonzero run."""
    vals = col.tolist()
    i, n = 0, len(vals)
    while i < n:
        if vals[i] == 0:
            i += 1
            continue
        sign = 1 if vals[i] > 0 else -1
        j = i
        while j + 1 < n and vals[j + 1] == vals[i]:
            j += 1
        yield i, j, sign
        i = j + 1


def _close_reason(base_col, i0, i1):
    n = len(base_col)
    if i1 == n - 1:
        return "window_end"
    nxt = base_col[i1 + 1]
    if nxt == 0:
        return "reversion_exit"
    return "band_flip"


def extract_trades(base_positions, final_positions, resid, s_scores,
                   features: dict, sectors: dict, removed_by: dict) -> list[dict]:
    idx = base_positions.index
    rows = []
    for c in base_positions.columns:
        base_col = base_positions[c].tolist()
        for i0, i1, sign in _runs(base_positions[c]):
            entered = final_positions[c].iloc[i0] != 0
            pnl = float(sign * resid[c].iloc[i0:i1 + 1].sum())
            blocked = [name for name, mask in removed_by.items()
                       if bool(mask[c].iloc[i0:i1 + 1].any())]
            row = {
                "signal_id": f"{c}:{idx[i0].date()}",
                "ticker": c,
                "entry_date": str(idx[i0].date()),
                "exit_date": str(idx[i1].date()),
                "holding_days": i1 - i0 + 1,
                "entry_s": float(s_scores[c].iloc[i0]),
                "residual": float(resid[c].iloc[i0]),
                "sector": sectors.get(c),
                "volatility": float(features["volatility"][c].iloc[i0]),
                "volume_ratio": float(features["volume_ratio"][c].iloc[i0]),
                "close_reason": _close_reason(base_col, i0, i1),
                "entered": bool(entered),
                "filters_blocked": blocked,
                "realized_pnl": pnl if entered else None,
                "counterfactual_pnl": None if entered else pnl,
                "success": bool(pnl > 0),
            }
            rows.append(row)
    return rows


def trade_stats(trades: list[dict]) -> dict:
    entered = [t for t in trades if t["entered"]]
    wins = [t for t in entered if t["success"]]
    hold = [t["holding_days"] for t in entered] or [0]
    return {
        "n_signals": len(trades),
        "n_entered": len(entered),
        "win_rate": (len(wins) / len(entered)) if entered else 0.0,
        "avg_holding_days": sum(hold) / len(hold),
    }
```

- [ ] **Step 4: Run test to verify it passes**

Run: `.venv/bin/pytest tests/test_statarb_ablation.py::test_extract_trades_realized_counterfactual_and_stats -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add tracks/statarb/trades.py tests/test_statarb_ablation.py
git commit -m "feat(statarb): per-signal outcome log extractor + trade stats"
```

---

### Task 5: Refactor runner into `run_residual()` with the parity gate

**Files:**
- Modify: `scripts/statarb_residual_run.py` (extract body into `run_residual`, keep CLI)
- Test: `tests/test_statarb_ablation.py` (append parity + layer-integration tests)

**Interfaces:**
- Produces: `run_residual(rets, factors, sectors, *, window=60, entry=1.25, exit_=0.5, skip=1, long_floor=None, cost_bps=5.0, n_trials=20, liquidity_adv=0.0, dollar_adv=None, sector_cap_=0.0, name_cap=0.0, blackout=None, features=None) -> dict` returning `{"net": pd.Series, "trades": list[dict], "base_positions": pd.DataFrame, "final_positions": pd.DataFrame}`.
- **Parity rule:** with `liquidity_adv=0, sector_cap_=0, name_cap=0, blackout=None`, the P&L path is the *exact current formula* (`gross=(held*resid).sum/n_active`, `cost=(turnover*bps/1e4*2).sum/n_active`). The weights path is entered ONLY when `sector_cap_>0 or name_cap>0`.

- [ ] **Step 1: Write the failing tests**

Append to `tests/test_statarb_ablation.py`:

```python
def _toy_market(seed=0, n=120, k=6):
    rng = np.random.default_rng(seed)
    idx = pd.date_range("2022-01-03", periods=n, freq="B")
    cols = [f"S{i}" for i in range(k)]
    fac = pd.DataFrame(rng.normal(0, 0.01, (n, k)), index=idx, columns=cols)
    rets = fac + pd.DataFrame(rng.normal(0, 0.02, (n, k)), index=idx, columns=cols)
    sectors = {c: ("tech" if i % 2 else "fin") for i, c in enumerate(cols)}
    return rets, fac, sectors


def _current_formula_net(rets, factors, window, entry, exit_, skip, cost_bps):
    from tracks.statarb.residual import rolling_residual
    from tracks.statarb.bands import band_positions
    resid = rolling_residual(rets, factors, window=window)
    cum = resid.cumsum()
    s = (cum - cum.rolling(window).mean()) / cum.rolling(window).std()
    positions = s.apply(lambda col: band_positions(col, entry=entry, exit_=exit_))
    held = positions.shift(1 + skip)
    active = held.abs()
    n_active = active.sum(axis=1).replace(0, pd.NA)
    gross = (held * resid).sum(axis=1) / n_active
    turnover = positions.diff().abs()
    cost = (turnover * cost_bps / 1e4 * 2).sum(axis=1) / n_active
    net = (gross - cost).fillna(0)
    return net[net.ne(0).cumsum() > 0]


def test_run_residual_parity_all_layers_off():
    from scripts.statarb_residual_run import run_residual
    rets, fac, sectors = _toy_market()
    oracle = _current_formula_net(rets, fac, 40, 1.25, 0.5, 1, 5.0)
    out = run_residual(rets, fac, sectors, window=40, entry=1.25, exit_=0.5,
                       skip=1, cost_bps=5.0)
    pd.testing.assert_series_equal(out["net"], oracle, check_names=False)


def test_run_residual_liquidity_changes_result_and_logs():
    from scripts.statarb_residual_run import run_residual
    rets, fac, sectors = _toy_market()
    adv = pd.DataFrame(1e9, index=rets.index, columns=rets.columns)
    adv["S0"] = 0.0                                   # force S0 illiquid
    out = run_residual(rets, fac, sectors, window=40, liquidity_adv=1e6, dollar_adv=adv)
    assert all(t["ticker"] != "S0" or not t["entered"] for t in out["trades"])
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `.venv/bin/pytest tests/test_statarb_ablation.py -k run_residual -v`
Expected: FAIL with `ImportError: cannot import name 'run_residual'`

- [ ] **Step 3: Write minimal implementation**

Refactor `scripts/statarb_residual_run.py`. Add `run_residual` above `main()`, and change `main()` to build the panel (existing code) then call `run_residual`. The core function:

```python
def run_residual(rets, factors, sectors, *, window=60, entry=1.25, exit_=0.5, skip=1,
                 long_floor=None, cost_bps=5.0, n_trials=20, liquidity_adv=0.0,
                 dollar_adv=None, sector_cap_=0.0, name_cap=0.0, blackout=None,
                 features=None):
    """Single audited code path. All-layers-off reproduces the current equal-weight
    P&L exactly (parity gate); weights path is used only when a cap is active."""
    import pandas as pd
    from tracks.statarb.bands import band_positions
    from tracks.statarb.residual import rolling_residual
    from tracks.statarb import filters as F
    from tracks.statarb.trades import extract_trades

    resid = rolling_residual(rets, factors, window=window)
    cum = resid.cumsum()
    s = (cum - cum.rolling(window).mean()) / cum.rolling(window).std()
    base_positions = s.apply(lambda col: band_positions(col, entry=entry, exit_=exit_,
                                                        long_floor=long_floor))

    positions = base_positions
    removed_by = {}
    if liquidity_adv and dollar_adv is not None:
        positions, rem = F.liquidity_filter(positions, dollar_adv, liquidity_adv)
        removed_by["liquidity"] = rem
    if blackout is not None:
        positions, rem = F.earnings_blackout(positions, blackout)
        removed_by["earnings"] = rem

    use_weights = sector_cap_ > 0 or name_cap > 0
    if use_weights:
        w = F.sector_cap(F.to_weights(positions), sectors, name_cap or 1.0, sector_cap_ or 1.0)
        held = w.shift(1 + skip)
        gross = (held * resid).sum(axis=1)
        turnover = w.diff().abs()
        cost = (turnover * cost_bps / 1e4 * 2).sum(axis=1)
        net = (gross - cost).fillna(0)
    else:
        held = positions.shift(1 + skip)
        n_active = held.abs().sum(axis=1).replace(0, pd.NA)
        gross = (held * resid).sum(axis=1) / n_active
        turnover = positions.diff().abs()
        cost = (turnover * cost_bps / 1e4 * 2).sum(axis=1) / n_active
        net = (gross - cost).fillna(0)
    net = net[net.ne(0).cumsum() > 0]

    if features is None:
        vol = rets.rolling(window).std()
        features = {"volatility": vol, "volume_ratio": pd.DataFrame(
            1.0, index=rets.index, columns=rets.columns)}
    trades = extract_trades(base_positions, positions, resid, s, features, sectors, removed_by)
    return {"net": net, "trades": trades,
            "base_positions": base_positions, "final_positions": positions}
```

Then in `main()`, after the panel/factor/etc. are built (unchanged), replace the inline P&L block (current lines ~96–130) with:

```python
    out = run_residual(rets, factors, sector_map_series_or_dict, window=args.window,
                       entry=args.entry, exit_=args.exit_, skip=args.skip,
                       long_floor=args.long_floor, cost_bps=args.cost_bps,
                       n_trials=args.n_trials)
    net = out["net"]
```

Keep the existing `sector` dict as `sectors`; keep the scorecard/markdown/register/print block below unchanged (it consumes `net`). The `--pit` membership masking stays in `main()` applied to `base_positions` before scoring is out of scope for this task — leave `--pit` behavior exactly as today by keeping its branch in `main()` operating on the pre-`run_residual` positions **only if already present**; if wiring `--pit` through `run_residual` is non-trivial, keep the current `main()` pit path and pass its masked positions in a follow-up (documented, not blocking the ablation).

- [ ] **Step 4: Run tests to verify they pass**

Run: `.venv/bin/pytest tests/test_statarb_ablation.py -k run_residual -v`
Expected: PASS

Then the full existing suite (nothing regressed):

Run: `.venv/bin/pytest tests/test_statarb.py -v`
Expected: PASS

- [ ] **Step 5: Real-data parity check (manual, one-time)**

Run: `.venv/bin/python scripts/statarb_residual_run.py --cap large --cost-bps 10`
Expected: prints net Sharpe **~2.67** (matches the pre-refactor headline). If it differs, the refactor broke parity — stop and fix before proceeding.

- [ ] **Step 6: Commit**

```bash
git add scripts/statarb_residual_run.py tests/test_statarb_ablation.py
git commit -m "refactor(statarb): extract run_residual() + wire filters, parity-gated"
```

---

### Task 6: Ablation sweep runner + comparison table

**Files:**
- Create: `scripts/statarb_ablation_run.py`
- Test: `tests/test_statarb_ablation.py` (append smoke test of the table assembler)

**Interfaces:**
- Consumes: `run_residual` (Task 5), `trade_stats` (Task 4), `scorecard`/`to_markdown` (existing).
- Produces: `ablation_table(rows) -> str` (markdown) and a `main()` that builds the panel once, runs the cumulative config stack, writes `artifacts/statarb/ablation/table.md` + `table.parquet`.

- [ ] **Step 1: Write the failing test**

Append to `tests/test_statarb_ablation.py`:

```python
def test_ablation_table_has_row_per_config():
    from scripts.statarb_ablation_run import ablation_table
    rows = [
        {"config": "baseline", "n_signals": 100, "n_entered": 100, "win_rate": 0.6,
         "avg_holding_days": 8.0, "sharpe": 3.1, "max_drawdown": -0.1,
         "ann_return": 0.12, "deflated_sharpe_prob": 1.0},
        {"config": "+ costs", "n_signals": 100, "n_entered": 100, "win_rate": 0.58,
         "avg_holding_days": 8.0, "sharpe": 2.67, "max_drawdown": -0.1,
         "ann_return": 0.11, "deflated_sharpe_prob": 1.0},
    ]
    md = ablation_table(rows)
    assert "baseline" in md and "+ costs" in md
    assert "2.67" in md
    assert md.count("\n") >= 4          # header + separator + 2 rows
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/bin/pytest tests/test_statarb_ablation.py::test_ablation_table_has_row_per_config -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'scripts.statarb_ablation_run'`

- [ ] **Step 3: Write minimal implementation**

Create `scripts/statarb_ablation_run.py`:

```python
"""Ablation sweep: run the residual book under a cumulative stack of production layers,
one comparison table. Emits the per-signal log per config for later ML. Full history.

Usage: .venv/bin/python scripts/statarb_ablation_run.py --cap large --cost-bps 10
"""
import argparse
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from core.data.prices import daily_returns, fetch_prices_yf, fetch_volume_yf, rolling_dollar_adv
from core.data.universe import fetch_sp_composite
from core.eval.scorecard import scorecard
from tracks.pead.events import fetch_earnings_yf
from tracks.statarb import filters as F
from tracks.statarb.paper.ledger import Ledger
from tracks.statarb.trades import trade_stats
from scripts.statarb_residual_run import SECTOR_ETF, run_residual

COLS = ["config", "n_signals", "n_entered", "win_rate", "avg_holding_days",
        "ann_return", "sharpe", "max_drawdown", "deflated_sharpe_prob"]


def ablation_table(rows: list[dict]) -> str:
    head = "| " + " | ".join(COLS) + " |"
    sep = "| " + " | ".join("---" for _ in COLS) + " |"
    def fmt(v):
        return f"{v:.2f}" if isinstance(v, float) else str(v)
    body = ["| " + " | ".join(fmt(r.get(c, "")) for c in COLS) + " |" for r in rows]
    return "\n".join([head, sep, *body]) + "\n"


def _row(name, out):
    card = scorecard(out["net"], {}, n_trials=20, periods_per_year=252)
    stats = trade_stats(out["trades"])
    return {"config": name, **stats, "sharpe": card["sharpe"],
            "ann_return": card["ann_return"], "max_drawdown": card["max_drawdown"],
            "deflated_sharpe_prob": card["deflated_sharpe_prob"]}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cost-bps", type=float, default=10.0)
    ap.add_argument("--start", default="2018-01-01")
    ap.add_argument("--liquidity-adv", type=float, default=5e6)
    ap.add_argument("--sector-cap", type=float, default=0.20)
    ap.add_argument("--name-cap", type=float, default=0.02)
    args = ap.parse_args()

    out_dir = Path("artifacts/statarb/ablation")
    out_dir.mkdir(parents=True, exist_ok=True)
    log_root = Path("artifacts/statarb/signal_log")

    comp = fetch_sp_composite(cache=Path("data/raw/sp_composite.parquet"))
    comp = comp[comp["index"] == "500"]
    sectors = dict(zip(comp["ticker"], comp["sector"]))
    tickers = sorted(sectors)

    px = fetch_prices_yf(tickers, args.start, None)
    px = px[[c for c in px.columns if c in sectors]]
    rets = daily_returns(px).clip(lower=-0.5, upper=1.0)
    etf = daily_returns(fetch_prices_yf(["SPY"] + sorted(set(SECTOR_ETF.values())),
                                        args.start, None)).reindex(rets.index)
    factors = pd.DataFrame({t: etf.get(SECTOR_ETF.get(sectors.get(t, ""), "SPY"),
                                       etf["SPY"]).fillna(etf["SPY"])
                            for t in rets.columns}).reindex(rets.index)

    vol = fetch_volume_yf(tickers, args.start, None).reindex(rets.index)
    adv = rolling_dollar_adv(px.reindex(rets.index), vol, window=20)
    earn = fetch_earnings_yf(tickers)
    blackout = F.earnings_window_mask(rets.index, earn, before=2, after=1,
                                      columns=list(rets.columns))

    configs = [
        ("baseline", dict(cost_bps=0.0)),
        ("+ costs", dict(cost_bps=args.cost_bps)),
        ("+ liquidity", dict(cost_bps=args.cost_bps, liquidity_adv=args.liquidity_adv, dollar_adv=adv)),
        ("+ sector cap", dict(cost_bps=args.cost_bps, liquidity_adv=args.liquidity_adv,
                              dollar_adv=adv, sector_cap_=args.sector_cap, name_cap=args.name_cap)),
        ("+ earnings blackout", dict(cost_bps=args.cost_bps, liquidity_adv=args.liquidity_adv,
                                     dollar_adv=adv, sector_cap_=args.sector_cap,
                                     name_cap=args.name_cap, blackout=blackout)),
    ]
    rows = []
    for name, kw in configs:
        out = run_residual(rets, factors, sectors, window=60, entry=1.25, exit_=0.5,
                           skip=1, n_trials=20, **kw)
        rows.append(_row(name, out))
        led = Ledger(log_root / name.replace(" ", "_").replace("+", "plus"))
        for t in out["trades"]:
            led.append("signal_log", t)

    md = ablation_table(rows)
    (out_dir / "table.md").write_text("# StatArb ablation — S&P 500, full history\n\n" + md)
    pd.DataFrame(rows).to_parquet(out_dir / "table.parquet")
    print(md)


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Run test to verify it passes**

Run: `.venv/bin/pytest tests/test_statarb_ablation.py::test_ablation_table_has_row_per_config -v`
Expected: PASS

- [ ] **Step 5: Full suite + real run**

Run: `.venv/bin/pytest tests/ -q`
Expected: PASS (all)

Run: `.venv/bin/python scripts/statarb_ablation_run.py`
Expected: prints a 5-row table; `+ costs` row Sharpe ≈ 2.67; writes `artifacts/statarb/ablation/table.md` and per-config logs under `artifacts/statarb/signal_log/`.

- [ ] **Step 6: Commit**

```bash
git add scripts/statarb_ablation_run.py tests/test_statarb_ablation.py
git commit -m "feat(statarb): ablation sweep runner + comparison table"
```

---

## Self-Review

**Spec coverage:**
- Per-signal log substrate → Task 4 (+ emitted per config in Task 6). ✓
- Four layers (costs/liquidity/sector-cap/earnings) → costs exist; Tasks 2–3 add the rest; wired in Task 5. ✓
- Counterfactual labeling → Task 4 (`counterfactual_pnl` for skipped signals). ✓
- Unionable schema (entry_s, entry_bucket, close_reason, realized_pnl, holding_days) → Task 4 rows. Note: `entry_bucket` is derivable from `entry_s` (short/long_shallow/long_deep/long_verydeep); add it in Task 4's row dict if the ML phase needs it pre-computed — deferred as YAGNI since it's a pure function of `entry_s` already logged.
- Parity gate (both anchors) → Task 5 Step 1 (synthetic bit-for-bit) + Step 5 (real-data ~2.67) + Task 6 (`+costs` ≈ 2.67). ✓
- Full-history ablation, date-tagged log → Task 6 (`--start 2018`, `entry_date` on every row). ✓
- Ablation table with n_signals/win%/avg-hold/Sharpe/DD → Task 6. ✓

**Placeholder scan:** No TBD/TODO. The one soft spot is Task 5's `--pit` note (explicitly deferred, not blocking) — acceptable, ablation runs on the non-pit large-cap universe where 2.67 is defined.

**Type consistency:** `run_residual` returns `net`/`trades`/`base_positions`/`final_positions` (Task 5) consumed as `out["net"]`/`out["trades"]` (Task 6). `extract_trades(base, final, resid, s, features, sectors, removed_by)` signature matches its call in Task 5. `sector_cap_`/`name_cap` naming consistent Tasks 3→5→6. `trade_stats` keys (`n_signals`,`n_entered`,`win_rate`,`avg_holding_days`) match `_row`/`ablation_table` COLS.

---

## Deviations from spec (intentional, minimal)

- **Per-trade P&L is contemporaneous reversion** (`Σ sign*resid` over the hold), a *label* for "did it revert" — deliberately distinct from the engine's cost-and-lag net series (the performance number). Documented in Task 4.
- **`return`/`counterfactual_return`** fields folded into `*_pnl` (resid-space) for v1 — addable later without schema break.
- **`--pit` not threaded through `run_residual`** yet — ablation uses the standard large-cap universe where the 2.67 anchor is defined.
