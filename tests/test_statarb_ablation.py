import numpy as np
import pandas as pd
import pytest


def _idx(n):
    return pd.date_range("2024-01-01", periods=n, freq="B")


# ---- Task 1: rolling dollar-ADV ----

def test_rolling_dollar_adv_median_of_price_times_volume():
    from core.data.prices import rolling_dollar_adv
    idx = _idx(4)
    px = pd.DataFrame({"A": [10.0, 10.0, 10.0, 10.0]}, index=idx)
    vol = pd.DataFrame({"A": [100.0, 300.0, 500.0, 700.0]}, index=idx)
    adv = rolling_dollar_adv(px, vol, window=2)
    assert pd.isna(adv["A"].iloc[0])
    assert adv["A"].iloc[1] == 2000.0
    assert adv["A"].iloc[3] == 6000.0


# ---- Task 2: liquidity + earnings blackout ----

def test_liquidity_filter_zeros_illiquid_positions():
    from tracks.statarb.filters import liquidity_filter
    idx = _idx(3)
    pos = pd.DataFrame({"A": [1, 1, 1], "B": [-1, -1, -1]}, index=idx)
    adv = pd.DataFrame({"A": [9e6, 9e6, 9e6], "B": [1e6, 1e6, 1e6]}, index=idx)
    filtered, removed = liquidity_filter(pos, adv, min_adv=5e6)
    assert filtered["A"].tolist() == [1, 1, 1]
    assert filtered["B"].tolist() == [0, 0, 0]
    assert removed["B"].all() and not removed["A"].any()


def test_earnings_window_mask_marks_window():
    from tracks.statarb.filters import earnings_window_mask
    idx = _idx(6)
    earn = pd.DataFrame({"ticker": ["A"], "date": [pd.Timestamp("2024-01-03")]})
    mask = earnings_window_mask(idx, earn, before=1, after=1, columns=["A", "B"])
    assert mask["A"].tolist() == [False, True, True, True, False, False]
    assert not mask["B"].any()


def test_earnings_blackout_blocks_new_entry_but_holds_existing():
    from tracks.statarb.filters import earnings_blackout
    idx = _idx(4)
    pos = pd.DataFrame({"A": [0, 1, 1, 0], "B": [1, 1, 1, 0]}, index=idx)
    blackout = pd.DataFrame({"A": [False, True, True, False],
                             "B": [False, True, True, False]}, index=idx)
    filtered, removed = earnings_blackout(pos, blackout)
    assert filtered["A"].tolist() == [0, 0, 0, 0]
    assert filtered["B"].tolist() == [1, 1, 1, 0]
    assert removed["A"].iloc[1]


# ---- Task 3: weights + sector cap ----

def test_to_weights_equal_weight_dollar_neutral():
    from tracks.statarb.filters import to_weights
    idx = _idx(1)
    pos = pd.DataFrame({"A": [1], "B": [1], "C": [-1], "D": [0]}, index=idx)
    w = to_weights(pos)
    assert w.iloc[0].abs().sum() == pytest.approx(1.0)
    assert w["A"].iloc[0] == pytest.approx(1 / 3)
    assert w["C"].iloc[0] == pytest.approx(-1 / 3)
    assert w["D"].iloc[0] == 0.0


def test_sector_cap_clips_then_renormalizes():
    from tracks.statarb.filters import to_weights, sector_cap, _apply_caps
    idx = _idx(1)
    pos = pd.DataFrame({"A": [1], "B": [1], "C": [1], "D": [-1]}, index=idx)
    w = to_weights(pos)                       # each +/-0.25
    sectors = {"A": "tech", "B": "tech", "C": "tech", "D": "fin"}
    pre = _apply_caps(w, sectors, name_cap=0.20, sector_cap_=1.0)
    assert (pre.iloc[0].abs() <= 0.20 + 1e-9).all()          # clip happened pre-renorm
    capped = sector_cap(w, sectors, name_cap=0.20, sector_cap_=1.0)
    assert capped.iloc[0].abs().sum() == pytest.approx(1.0)  # gross restored


# ---- Task 4: per-signal log extractor ----

def test_extract_trades_realized_counterfactual_and_stats():
    from tracks.statarb.trades import extract_trades, trade_stats
    idx = _idx(4)
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
    assert by_t["A"]["realized_pnl"] == pytest.approx(0.05)
    assert by_t["A"]["holding_days"] == 2
    assert by_t["A"]["success"] is True
    assert by_t["B"]["entered"] is False
    assert by_t["B"]["counterfactual_pnl"] == pytest.approx(-0.05)
    assert "liquidity" in by_t["B"]["filters_blocked"]
    stats = trade_stats(trades)
    assert stats["n_signals"] == 2 and stats["n_entered"] == 1
    assert stats["win_rate"] == pytest.approx(1.0)


def test_extract_trades_lag_matches_engine_execution_window():
    # lag shifts the P&L window to the days the engine actually trades (held = positions.shift(1+skip)).
    from tracks.statarb.trades import extract_trades
    idx = _idx(5)
    base = final = pd.DataFrame({"A": [0, 1, 1, 0, 0]}, index=idx)
    resid = pd.DataFrame({"A": [0.0, -0.10, 0.02, 0.03, 0.04]}, index=idx)  # entry drop, reversion after
    s = pd.DataFrame({"A": [0.0, -1.5, -0.9, -0.2, 0.0]}, index=idx)
    feats = {"volatility": pd.DataFrame(0.2, index=idx, columns=["A"]),
             "volume_ratio": pd.DataFrame(1.0, index=idx, columns=["A"])}
    lag0 = extract_trades(base, final, resid, s, feats, {"A": "x"}, {}, lag=0)[0]
    assert lag0["realized_pnl"] == pytest.approx(-0.08)   # [1,2]: -0.10+0.02, captures entry drop
    lag2 = extract_trades(base, final, resid, s, feats, {"A": "x"}, {}, lag=2)[0]
    assert lag2["realized_pnl"] == pytest.approx(0.07)    # [3,4]: 0.03+0.04, the traded reversion


# ---- Task 5: run_residual parity + layers ----

def _toy_market(seed=0, n=120, k=6):
    rng = np.random.default_rng(seed)
    idx = pd.date_range("2022-01-03", periods=n, freq="B")
    cols = [f"S{i}" for i in range(k)]
    fac = pd.DataFrame(rng.normal(0, 0.01, (n, k)), index=idx, columns=cols)
    rets = fac + pd.DataFrame(rng.normal(0, 0.02, (n, k)), index=idx, columns=cols)
    sectors = {c: ("tech" if i % 2 else "fin") for i, c in enumerate(cols)}
    return rets, fac, sectors


def _current_formula_net(rets, factors, window, entry, exit_, skip, cost_bps):
    from tracks.statarb.residual import hedged_returns, rolling_beta, rolling_residual
    from tracks.statarb.bands import band_positions
    from tracks.statarb.book import overlay_cost
    resid = rolling_residual(rets, factors, window=window)
    hedged = hedged_returns(rets, factors, window=window)
    cum = resid.cumsum()
    s = (cum - cum.rolling(window).mean()) / cum.rolling(window).std()
    positions = s.apply(lambda col: band_positions(col, entry=entry, exit_=exit_))
    held = positions.shift(1 + skip)
    n_active = held.abs().sum(axis=1).replace(0, pd.NA)
    gross = (held * hedged).sum(axis=1) / n_active
    turnover = positions.diff().abs()
    cost = (turnover * cost_bps / 1e4 * 2).sum(axis=1) / n_active
    net = (gross - cost).fillna(0)
    net = net[net.ne(0).cumsum() > 0]
    eq_w = positions.div(positions.abs().sum(axis=1).replace(0, pd.NA), axis=0).fillna(0.0)
    oc = overlay_cost(eq_w, rolling_beta(rets, factors, window=window))
    return net - oc.reindex(net.index).fillna(0)


def test_run_residual_parity_all_layers_off():
    from tracks.statarb.book import run_residual
    rets, fac, sectors = _toy_market()
    oracle = _current_formula_net(rets, fac, 40, 1.25, 0.5, 1, 5.0)
    out = run_residual(rets, fac, sectors, window=40, entry=1.25, exit_=0.5, skip=1, cost_bps=5.0)
    pd.testing.assert_series_equal(out["net"], oracle, check_names=False)


def test_run_residual_liquidity_blocks_a_name():
    from tracks.statarb.book import run_residual
    rets, fac, sectors = _toy_market()
    adv = pd.DataFrame(1e9, index=rets.index, columns=rets.columns)
    adv["S0"] = 0.0
    out = run_residual(rets, fac, sectors, window=40, liquidity_adv=1e6, dollar_adv=adv)
    assert all((t["ticker"] != "S0") or (not t["entered"]) for t in out["trades"])


# ---- Task 6: ablation table ----

def test_ablation_table_has_row_per_config():
    from scripts.statarb_ablation_run import ablation_table
    rows = [
        {"config": "baseline", "n_signals": 100, "n_entered": 100, "win_rate": 0.6,
         "avg_holding_days": 8.0, "sharpe": 3.1, "max_drawdown": -0.1,
         "ann_return": 0.12, "deflated_sharpe_prob": 1.0},
        {"config": "costs", "n_signals": 100, "n_entered": 100, "win_rate": 0.58,
         "avg_holding_days": 8.0, "sharpe": 2.67, "max_drawdown": -0.1,
         "ann_return": 0.11, "deflated_sharpe_prob": 1.0},
    ]
    md = ablation_table(rows)
    assert "baseline" in md and "costs" in md and "2.67" in md
    assert md.count("\n") >= 4
