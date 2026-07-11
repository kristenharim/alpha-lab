"""Agent 6 perturbation runner. Executes EXACTLY the grid in predeclaration.md.

Read-only vs the repo: loads frozen specs/panels, writes only under agent6/.
P&L convention is a literal copy of research/hunt2026/harness.py::run, verified
against the published summaries at baseline before any perturbation is trusted.
"""
import importlib.util
import json
import shutil
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

LAB = Path.home() / "projects/alpha-lab"
H26 = LAB / "research/hunt2026"
AG6 = LAB / "redteam/2026-07-10/agent6"
SCRATCH = AG6 / "scratch"
CSV = AG6 / "csv"
META = json.loads((H26 / "sandbox_meta.json").read_text())
STOCK_BPS, ETF_BPS, MAX_GROSS = 10.0, 2.0, 2.0
ETFS = set(META["etfs"])

CUT1 = "2025-07-10"
CUT5 = "2021-07-10"

BOOKS = {
    # book: (window_start, bench)
    "vol_managed_qqq": (CUT1, "QQQ"),
    "vol_core_svxy": (CUT1, "QQQ"),
    "dual_momentum_gem": (CUT1, "SPY"),
    "momentum_concentrated": (CUT1, "SPY"),
    "trend_vol_qqq": (CUT5, "QQQ"),
    "defensive_ensemble": (CUT5, "6040"),
    "dual_momentum_gold": (CUT5, "SPY"),
}
PUBLISHED = {  # total_net from results/summary.md and results5y/summary.md
    "vol_managed_qqq": 0.4251, "vol_core_svxy": 0.3610, "dual_momentum_gem": 0.5856,
    "momentum_concentrated": 0.3544, "trend_vol_qqq": 2.011,
    "defensive_ensemble": 1.476, "dual_momentum_gold": 2.585,
}


def load_spec_from(path):
    path = Path(path)
    s = importlib.util.spec_from_file_location(f"{path.parent.name}_{time.time_ns()}",
                                               path)
    mod = importlib.util.module_from_spec(s)
    s.loader.exec_module(mod)
    return mod


def fresh_mod(book):
    return load_spec_from(H26 / "specs" / book / "spec.py")


def per_side_bps(cols, mult=1.0, add=0.0):
    return pd.Series([(ETF_BPS if t in ETFS else STOCK_BPS) * mult + add for t in cols],
                     index=cols)


def cap_gross(W):
    gross = W.abs().sum(axis=1)
    return W.mul((MAX_GROSS / gross).clip(upper=1.0).fillna(1.0), axis=0)


def score(W, panel_, start, cost_mult=1.0, cost_add=0.0, exec_open=False):
    """Literal harness.run P&L on precomputed executed weights W (already capped)."""
    close = panel_["close"][W.columns]
    rets = close.pct_change(fill_method=None)
    if exec_open:
        op = panel_["open"][W.columns]
        op = op.where(op.notna(), close)  # missing open -> fall back to close
        r_on = op / close.shift(1) - 1.0
        r_id = close / op - 1.0
        gross = (W.shift(2) * r_on + W.shift(1) * r_id).sum(axis=1, min_count=1).fillna(0.0)
    else:
        gross = (W.shift(1) * rets).sum(axis=1, min_count=1).fillna(0.0)
    bps = per_side_bps(W.columns, cost_mult, cost_add)
    cost = (W.diff().abs().fillna(W.abs()) * (bps / 1e4)).sum(axis=1)
    net = gross - cost
    idx = net.index[net.index > pd.Timestamp(start)]
    net = net.reindex(idx)
    nav = (1 + net).cumprod()
    return {"total_net": float(nav.iloc[-1] - 1),
            "sharpe": float(net.mean() / net.std() * np.sqrt(252)) if net.std() > 0 else 0.0,
            "max_dd": float((nav / nav.cummax() - 1).min())}


def bench_total(panel_, kind, start):
    idx, cols = panel_.index, panel_["close"].columns
    W = pd.DataFrame(0.0, index=idx, columns=["SPY", "QQQ", "BIL"])
    if kind == "6040":
        W["SPY"], W["BIL"] = 0.6, 0.4
    else:
        W[kind] = 1.0
    return score(cap_gross(W), panel_, start)["total_net"]


# ---------------- perturbation helpers (weight level) ----------------

def missed_trades(W, p, seed):
    rng = np.random.default_rng(seed)
    miss = rng.random(len(W)) < p
    V = W.to_numpy().copy()
    for i in range(1, len(V)):
        if miss[i]:
            V[i] = V[i - 1]
    return pd.DataFrame(V, index=W.index, columns=W.columns)


def random_lag(W, p, seed):
    rng = np.random.default_rng(seed)
    flag = rng.random(len(W)) < p
    V = W.to_numpy().copy()
    V[1:][flag[1:]] = W.to_numpy()[:-1][flag[1:]]
    return pd.DataFrame(V, index=W.index, columns=W.columns)


# ---------------- panel-level perturbations ----------------

def mask_close(panel_, p, seed):
    rng = np.random.default_rng(seed)
    pm = panel_.copy()
    cm = pm["close"].to_numpy().copy()
    cm[rng.random(cm.shape) < p] = np.nan
    pm.loc[:, "close"] = cm
    return pm


def swap_qqq_spy(panel_):
    pm = panel_.copy()
    for f in ["open", "close", "volume"]:
        q = pm[(f, "QQQ")].copy()
        pm[(f, "QQQ")] = pm[(f, "SPY")]
        pm[(f, "SPY")] = q
    return pm


# ---------------- rebalance-shift patched copies ----------------

RSHIFT_PATCHES = {
    "dual_momentum_gold": (
        "    month_end = idx[:-1][idx[1:].month != idx[:-1].month]",
        "    month_end = idx[:-1][idx[1:].month != idx[:-1].month]\n"
        "    _pos = idx.get_indexer(month_end) + RSHIFT\n"
        "    month_end = idx[_pos[_pos < len(idx)]]"),
    "dual_momentum_gem": (
        "    month_end = idx[:-1][idx[1:].month != idx[:-1].month]",
        "    month_end = idx[:-1][idx[1:].month != idx[:-1].month]\n"
        "    _pos = idx.get_indexer(month_end) + RSHIFT\n"
        "    month_end = idx[_pos[_pos < len(idx)]]"),
    "defensive_ensemble": (
        "    reb = (month != month.shift(1)).values  # first trading day of each month",
        "    reb = np.roll((month != month.shift(1)).values, RSHIFT)\n"
        "    reb[:RSHIFT] = False"),
    "momentum_concentrated": (
        '    rebal_days = pd.Series(idx, index=idx).groupby(idx.to_period("W")).last().values',
        '    _rd = pd.Series(idx, index=idx).groupby(idx.to_period("W")).last()\n'
        "    _pos = idx.get_indexer(pd.DatetimeIndex(_rd.values)) + RSHIFT\n"
        "    rebal_days = idx[_pos[_pos < len(idx)]].values"),
}


def rshift_mod(book, k):
    src = (H26 / "specs" / book / "spec.py").read_text()
    old, new = RSHIFT_PATCHES[book]
    assert src.count(old) == 1, (book, "patch anchor not unique")
    dst = SCRATCH / f"{book}_rshift{k}"
    dst.mkdir(parents=True, exist_ok=True)
    (dst / "spec.py").write_text(f"RSHIFT = {k}\n" + src.replace(old, new))
    shutil.copy(H26 / "specs" / book / "params.json", dst / "params.json")
    return load_spec_from(dst / "spec.py")


# ---------------- param / universe mutation ----------------

def params_attr(mod):
    for name in ("P", "PARAMS"):
        if hasattr(mod, name):
            return getattr(mod, name)
    raise AttributeError("no params dict")


PARAM_GRID = {  # book -> list of (label, key, value)
    "vol_managed_qqq": [("sigma-20", "sigma_target", 0.20), ("sigma+20", "sigma_target", 0.30),
                        ("lb-20", "vol_lookback", 17), ("lb+20", "vol_lookback", 25),
                        ("band-20", "tolerance_band", 0.04), ("band+20", "tolerance_band", 0.06)],
    "vol_core_svxy": [("sigma-20", "sigma_target", 0.20), ("sigma+20", "sigma_target", 0.30),
                      ("svxyw-20", "svxy_weight", 0.24), ("svxyw+20", "svxy_weight", 0.36),
                      ("gate-20", "vix_gate_window", 50), ("gate+20", "vix_gate_window", 76)],
    "trend_vol_qqq": [("sma-20", "sma_window", 160), ("sma+20", "sma_window", 240),
                      ("sigma-20", "sigma_target", 0.20), ("sigma+20", "sigma_target", 0.30),
                      ("rvlb-20", "rv_lookback", 17), ("rvlb+20", "rv_lookback", 25)],
    "defensive_ensemble": [("vt-20", "vol_target", 0.144), ("vt+20", "vol_target", 0.216),
                           ("slb-20", "sleeve_vol_lookback", 50), ("slb+20", "sleeve_vol_lookback", 76),
                           ("cap-20", "gross_cap", 1.6), ("cap+20", "gross_cap", 2.4)],
    "dual_momentum_gold": [("lb-20", "lookback", 202), ("lb+20", "lookback", 302),
                           ("rlev-20", "risk_leverage", 1.2), ("rlev+20", "risk_leverage", 1.8),
                           ("dlev-20", "defensive_leverage", 0.8), ("dlev+20", "defensive_leverage", 1.2)],
    "dual_momentum_gem": [("lb-20", "lookback_days", 202), ("lb+20", "lookback_days", 302),
                          ("skip5", "skip_days", 5), ("skip21", "skip_days", 21),
                          ("elev-20", "equity_leverage", 1.2), ("elev+20", "equity_leverage", 1.8)],
    "momentum_concentrated": [("n-20", "n_names", 16), ("n+20", "n_names", 24),
                              ("vt-20", "vol_target_ann", 0.16), ("vt+20", "vol_target_ann", 0.24),
                              ("vlb-20", "vol_lookback", 50), ("vlb+20", "vol_lookback", 74)],
}


def universe_variants(book, panel_):
    """Yield (label, mod_or_None, panel) — mod=None means use fresh baseline mod."""
    if book in ("vol_managed_qqq", "trend_vol_qqq"):
        yield "U1-spy", fresh_mod(book), swap_qqq_spy(panel_)
    elif book == "vol_core_svxy":
        m = fresh_mod(book)
        m.CORE_SPLIT = {"SPY": 1.0}
        yield "U1-spycore", m, panel_
    elif book == "defensive_ensemble":
        m = fresh_mod(book)
        m.TSMOM_MENU = [t for t in m.TSMOM_MENU if t not in ("USO", "SLV", "HYG")]
        yield "U1-menu12", m, panel_
        m2 = fresh_mod(book)
        m2.RISK = ["SPY", "QQQ"]
        yield "U2-nogold", m2, panel_
    elif book == "dual_momentum_gold":
        m = fresh_mod(book)
        m.RISK_MENU = ["SPY", "QQQ", "GLD", "EFA"]
        yield "U1-addefa", m, panel_
        m2 = fresh_mod(book)
        m2.DEFENSIVE_MENU = ["IEF", "BIL"]
        yield "U2-ief", m2, panel_
    elif book == "dual_momentum_gem":
        m = fresh_mod(book)
        m.EQUITY_MENU = ["SPY", "QQQ", "EFA", "EEM"]
        yield "U1-addeem", m, panel_
        m2 = fresh_mod(book)
        m2.DEFENSIVE = "IEF"
        yield "U2-ief", m2, panel_
    elif book == "momentum_concentrated":
        pm = panel_.copy()
        mem = pm["member"].rolling(21).min()
        pm.loc[:, "member"] = mem.to_numpy()
        yield "U1-strictmem", fresh_mod(book), pm
        pm2 = panel_.copy()
        pm2.loc[:, "member"] = pm2["member"].shift(21).to_numpy()
        yield "U2-lagmem", fresh_mod(book), pm2


# ---------------- main ----------------

def weights_of(mod, panel_):
    W = mod.target_weights(panel_).astype(float).fillna(0.0)
    return cap_gross(W)


def main(books):
    panel = pd.concat([pd.read_parquet(H26 / "train.parquet"),
                       pd.read_parquet(H26 / "holdout.parquet")])
    print("panel", panel.shape, panel.index[0], "->", panel.index[-1], flush=True)

    for book in books:
        t0 = time.time()
        start, bkind = BOOKS[book]
        rows = []
        mod = fresh_mod(book)
        Wb = weights_of(mod, panel)
        base = score(Wb, panel, start)
        bench = bench_total(panel, bkind, start)
        base_ex = base["total_net"] - bench
        pub = PUBLISHED[book]
        print(f"== {book}: baseline {base['total_net']:+.2%} (published {pub:+.2%}) "
              f"bench {bench:+.2%} excess {base_ex:+.2%}", flush=True)
        assert abs(base["total_net"] - pub) < 0.005, (book, base["total_net"], pub)

        def add(label, family, r, bench_=None):
            b = bench if bench_ is None else bench_
            ex = r["total_net"] - b
            rows.append({"variant": label, "family": family, **r,
                         "bench": b, "excess": ex, "d_excess": ex - base_ex})

        add("baseline", "baseline", base)

        # 1 costs
        for m in (0.5, 2.0, 4.0):
            add(f"cost_x{m}", "costs", score(Wb, panel, start, cost_mult=m))
        add("cost_+10bps", "costs", score(Wb, panel, start, cost_add=10.0))

        # 2 params +-20%
        for label, key, val in PARAM_GRID[book]:
            m = fresh_mod(book)
            params_attr(m)[key] = val
            add(f"param_{label}", "params", score(weights_of(m, panel), panel, start))

        # 3 signal delay
        for k in (1, 2, 5):
            add(f"delay_{k}d", "signal_delay",
                score(Wb.shift(k).fillna(0.0), panel, start))

        # 4 rebalance-date shift
        if book in RSHIFT_PATCHES:
            for k in (1, 3):
                m = rshift_mod(book, k)
                add(f"rshift_{k}d", "rebal_shift", score(weights_of(m, panel), panel, start))

        # 5 next-open execution
        add("exec_open", "exec_timestamp", score(Wb, panel, start, exec_open=True))

        # 6 missed trades
        for p in (0.05, 0.10):
            for s in (0, 1, 2, 4, 7):
                add(f"miss_{int(p*100)}pct_s{s}", "missed_trades",
                    score(missed_trades(Wb, p, s), panel, start))

        # 7 random one-bar lag
        for s in (0, 1, 2, 4, 7):
            add(f"lag_10pct_s{s}", "random_lag", score(random_lag(Wb, 0.10, s), panel, start))

        # 8 missing observations (recompute on degraded panel)
        for p in (0.005, 0.02):
            for s in (0, 1, 2):
                pm = mask_close(panel, p, s)
                m = fresh_mod(book)
                add(f"missobs_{p*100:g}pct_s{s}", "missing_obs",
                    score(weights_of(m, pm), pm, start))

        # 9 alternate start dates
        after = panel.index[panel.index > pd.Timestamp(start)]
        for k in ((21, 42, 63) if start == CUT1 else (63, 126, 252)):
            s2 = after[k - 1]
            add(f"start_+{k}d", "alt_start", score(Wb, panel, s2),
                bench_=bench_total(panel, bkind, s2))

        # 10 alternate universe
        for label, m, pm in universe_variants(book, panel):
            add(f"univ_{label}", "alt_universe", score(weights_of(m, pm), pm, start))

        # 11 leverage reduction
        for f in (0.75, 0.5):
            add(f"lev_x{f}", "leverage", score(Wb * f, panel, start))

        df = pd.DataFrame(rows)
        df.to_csv(CSV / f"{book}.csv", index=False)
        print(df.to_string(index=False), flush=True)
        print(f"{book} done in {time.time()-t0:.0f}s, {len(df)} rows", flush=True)


if __name__ == "__main__":
    main(sys.argv[1:] or list(BOOKS))
