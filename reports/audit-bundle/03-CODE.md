# CODE — every function behind the audited numbers
Concatenated source. The backtest reuses these exact functions; the paper book (spec) reuses `residual.py` + `bands.py` unchanged.


================================================================================
## `tracks/statarb/residual.py`
================================================================================

```python
"""Residual mean-reversion (Avellaneda & Lee 2010, lite).

Strip systematic risk by regressing each stock's returns on factor returns
(market/sector ETFs here; the paper also uses PCA), then trade the mean-reverting
idiosyncratic residual. The trading signal is the "s-score": a standardized level
of the cumulative residual, modeled as an Ornstein-Uhlenbeck process.
"""
import numpy as np
import pandas as pd


def residual_returns(stock_rets: pd.DataFrame, factor_rets: pd.DataFrame) -> pd.DataFrame:
    """OLS-regress each stock's returns on the factor returns; return residuals.

    Full-sample regression over the passed window (the runner applies it per
    trailing window). Residuals are the idiosyncratic return orthogonal to factors.
    """
    aligned = stock_rets.join(factor_rets, how="inner").dropna()
    F = aligned[factor_rets.columns].to_numpy()
    F = np.column_stack([np.ones(len(F)), F])  # intercept
    out = {}
    for col in stock_rets.columns:
        if col not in aligned:
            continue
        y = aligned[col].to_numpy()
        beta, *_ = np.linalg.lstsq(F, y, rcond=None)
        out[col] = pd.Series(y - F @ beta, index=aligned.index)
    return pd.DataFrame(out)


def rolling_residual(stock_rets: pd.DataFrame, factor_rets: pd.DataFrame,
                     window: int = 60) -> pd.DataFrame:
    """Vectorized single-factor rolling residual across many stocks.

    `factor_rets` has the SAME columns as `stock_rets` — each column is that stock's
    matched factor return (e.g. its sector ETF). Betas are estimated on a trailing
    `window` and LAGGED one day before forming the residual, so no look-ahead.
    Fast enough for a full S&P-500+600 universe (pure DataFrame ops).
    """
    rs, fr = stock_rets.align(factor_rets, join="inner")
    mean_s = rs.rolling(window).mean()
    mean_f = fr.rolling(window).mean()
    cov = (rs * fr).rolling(window).mean() - mean_s * mean_f
    var = (fr * fr).rolling(window).mean() - mean_f ** 2
    beta = cov / var.replace(0, pd.NA)
    alpha = mean_s - beta * mean_f
    resid = rs - alpha.shift(1) - beta.shift(1) * fr
    resid[beta.shift(1).isna()] = pd.NA
    return resid


def s_score(residual: pd.Series, window: int = 60) -> pd.Series:
    """s-score of one stock's residual stream: standardize the cumulative residual
    (the OU level) over a trailing window. Negative s = residual cheap (buy)."""
    cum = residual.cumsum()
    mu = cum.rolling(window).mean()
    sd = cum.rolling(window).std()
    return (cum - mu) / sd.replace(0, np.nan)

```

================================================================================
## `tracks/statarb/bands.py`
================================================================================

```python
"""Shared entry/exit band logic for mean-reversion signals.

Given a standardized series (pair spread z-score, or residual s-score), take a
mean-reversion position: go long (+1) when the series is far BELOW zero (cheap,
expect reversion up), short (-1) when far ABOVE zero, and flatten when it returns
inside the exit band. Positions are stateful — held between crossings.
"""
import pandas as pd


def band_positions(series: pd.Series, entry: float = 2.0, exit_: float = 0.5,
                   long_floor: float | None = None) -> pd.Series:
    """long_floor caps how deep a LONG may go: you may only be long while the series
    is >= -long_floor. Below that (a "falling knife") you never enter, and a held long
    stops out. Default None = no floor (original behavior). Short side unaffected."""
    pos = 0
    out = []
    for v in series:
        if pd.isna(v):
            out.append(pos)
            continue
        too_deep = long_floor is not None and v < -long_floor
        if pos == 0:
            if v <= -entry and not too_deep:
                pos = 1
            elif v >= entry:
                pos = -1
        elif pos == 1 and too_deep:   # knife kept falling — stop out the long
            pos = 0
        elif abs(v) <= exit_:
            pos = 0
        out.append(pos)
    return pd.Series(out, index=series.index)

```

================================================================================
## `core/data/universe.py`
================================================================================

```python
"""Shared equity universe: current S&P Composite 1500 (large + mid + small cap).

Fetches current index membership from Wikipedia — real breadth across the cap
spectrum, including genuine small caps (S&P 600). IMPORTANT LIMITATION: this is
*current* membership, so it is still survivorship-biased (names dropped after
declining are excluded). It fixes the "too narrow / mega-cap only" problem but NOT
survivorship — only point-in-time membership (WRDS/CRSP) does that.
"""
import io
from pathlib import Path

import pandas as pd
import requests

SP_WIKI = {
    "500": "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies",
    "400": "https://en.wikipedia.org/wiki/List_of_S%26P_400_companies",
    "600": "https://en.wikipedia.org/wiki/List_of_S%26P_600_companies",
}
HEADERS = {"User-Agent": "alpha-lab research (kristen@example.com)"}


def clean_ticker(t: str) -> str:
    """Normalize to yfinance form: uppercase, class dots -> dashes (BRK.B -> BRK-B)."""
    return str(t).strip().upper().replace(".", "-").replace("$", "")


def extract_symbols(tables: list[pd.DataFrame]) -> pd.DataFrame:
    """From the tables on a Wikipedia constituents page, pull the one with a
    symbol/ticker column into a (ticker, sector) frame."""
    for df in tables:
        cols = {str(c).lower(): c for c in df.columns}
        sym = next((cols[k] for k in cols if k in ("symbol", "ticker symbol", "ticker")), None)
        if sym is None:
            continue
        out = pd.DataFrame({"ticker": df[sym].map(clean_ticker)})
        sec = next((cols[k] for k in cols if "sector" in k), None)
        out["sector"] = df[sec].astype(str).values if sec else "Unknown"
        return out
    raise ValueError("no symbol/ticker column found in any table")


def fetch_sp_composite(which=("500", "400", "600"), cache: Path | None = None) -> pd.DataFrame:
    """Return current S&P composite constituents as (ticker, sector, index). Network."""
    if cache and Path(cache).exists():
        return pd.read_parquet(cache)
    frames = []
    for idx in which:
        resp = requests.get(SP_WIKI[idx], headers=HEADERS, timeout=30)
        resp.raise_for_status()
        tables = pd.read_html(io.StringIO(resp.text))
        frames.append(extract_symbols(tables).assign(index=idx))
    df = (pd.concat(frames, ignore_index=True)
          .drop_duplicates("ticker", keep="first")
          .sort_values("ticker")
          .reset_index(drop=True))
    df = df[df["ticker"].str.match(r"^[A-Z][A-Z-]*$")]  # drop malformed rows
    if cache:
        Path(cache).parent.mkdir(parents=True, exist_ok=True)
        df.to_parquet(cache)
    return df


# Point-in-time S&P 500 membership (fja05680, maintained). Full constituent snapshot
# at each change date — forward-filled it reconstructs membership on any past day.
# This is the free-data fix for INCLUSION look-ahead (trading a name before it joined).
# It does NOT fix delisting survivorship: names acquired/failed have no price data in
# yfinance at all, so they can't be re-added. Point-in-time PRICES need CRSP/WRDS.
PIT_SP500_URL = ("https://raw.githubusercontent.com/fja05680/sp500/master/"
                 "S%26P%20500%20Historical%20Components%20%26%20Changes%20(Updated).csv")


def fetch_sp500_pit_changes(cache: Path | None = None) -> pd.DataFrame:
    """S&P 500 membership change-log as [date, members] — members is a sorted list of
    cleaned tickers effective on that date (a full snapshot, not a delta). Network."""
    if cache and Path(cache).exists():
        return pd.read_parquet(cache)
    resp = requests.get(PIT_SP500_URL, headers=HEADERS, timeout=30)
    resp.raise_for_status()
    raw = pd.read_csv(io.StringIO(resp.text))
    raw["date"] = pd.to_datetime(raw["date"])
    raw = raw.sort_values("date").reset_index(drop=True)
    members = [sorted({clean_ticker(t) for t in str(row).split(",")}) for row in raw["tickers"]]
    df = pd.DataFrame({"date": raw["date"], "members": members})
    if cache:
        Path(cache).parent.mkdir(parents=True, exist_ok=True)
        df.to_parquet(cache)
    return df


def membership_mask(changes: pd.DataFrame, dates, tickers) -> pd.DataFrame:
    """Daily boolean frame (dates x tickers): True where the ticker was an S&P 500
    member. Forward-fills each change-date snapshot onto the trading calendar."""
    tickers = list(tickers)
    dates = pd.DatetimeIndex(dates)
    rows = [[t in set(m) for t in tickers] for m in changes["members"]]
    mat = pd.DataFrame(rows, index=pd.to_datetime(changes["date"].values), columns=tickers)
    mat = mat[~mat.index.duplicated(keep="last")].sort_index()
    daily = mat.reindex(mat.index.union(dates)).ffill().reindex(dates)
    return daily.fillna(False).astype(bool)


def ever_members(changes: pd.DataFrame) -> set:
    """Set of tickers that were an S&P 500 member at any point in the change-log."""
    out = set()
    for m in changes["members"]:
        out |= set(m)
    return out

```

================================================================================
## `scripts/statarb_residual_run.py`
================================================================================

```python
"""StatArb residual mean-reversion (Avellaneda & Lee 2010, ETF variant), wide universe.

For each stock: rolling single-factor regression on its SECTOR ETF (betas lagged, no
look-ahead) -> idiosyncratic residual -> s-score of the cumulative residual. Trade the
mean-reversion: long when s <= -1.25 (residual cheap), short when s >= +1.25, flat inside
+/-0.5. Dollar-neutral, equal-weight across active names, net of costs -> shared scorecard.

Reuses the daily prices cached by scripts/statarb_run.py --universe wide.
Usage: .venv/bin/python scripts/statarb_residual_run.py [--window 60 --entry 1.25 --exit 0.5]
"""
import argparse
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from core.data.prices import daily_returns, fetch_prices_yf
from core.data.registry import register
from core.data.universe import (fetch_sp_composite, fetch_sp500_pit_changes,
                                 membership_mask, ever_members)
from core.eval.scorecard import scorecard, to_markdown
from tracks.statarb.bands import band_positions
from tracks.statarb.residual import rolling_residual

SECTOR_ETF = {
    "Information Technology": "XLK", "Financials": "XLF", "Health Care": "XLV",
    "Consumer Discretionary": "XLY", "Consumer Staples": "XLP", "Energy": "XLE",
    "Industrials": "XLI", "Materials": "XLB", "Utilities": "XLU",
    "Real Estate": "XLRE", "Communication Services": "XLC",
}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--window", type=int, default=60)
    ap.add_argument("--entry", type=float, default=1.25)
    ap.add_argument("--exit", type=float, default=0.5, dest="exit_")
    ap.add_argument("--cost-bps", type=float, default=5.0)
    ap.add_argument("--long-floor", type=float, default=None, dest="long_floor",
                    help="falling-knife stress test: forbid longs while s < -long_floor "
                         "(skip deep-dip entries + stop out held longs that keep falling). "
                         "Tests whether the edge is concentrated in the trades most analogous "
                         "to the missing delisted names. Off by default.")
    ap.add_argument("--n-trials", type=int, default=20,
                    help="declared # of strategy variants tried, for the deflated-Sharpe haircut")
    ap.add_argument("--skip", type=int, default=1,
                    help="days between signal close and execution — defends against "
                         "bid-ask bounce / same-close reversal (0 reproduces the naive run)")
    ap.add_argument("--cap", choices=["all", "large", "small"], default="all",
                    help="large = S&P 500 only, small = S&P 600 only")
    ap.add_argument("--start", default="2018-01-01")
    ap.add_argument("--pit", action="store_true",
                    help="point-in-time S&P 500: trade each name only on its actual index-"
                         "membership days (removes inclusion look-ahead). Universe = names "
                         "EVER in the S&P 500; forces --cap large semantics. NOTE: cannot fix "
                         "delisting survivorship (dead names have no free price data) — the "
                         "resulting Sharpe is an UPPER BOUND on the true point-in-time Sharpe.")
    args = ap.parse_args()

    out = Path("artifacts/statarb")
    out.mkdir(parents=True, exist_ok=True)

    comp = fetch_sp_composite(cache=Path("data/raw/sp_composite.parquet"))
    pit_changes = None
    if args.pit:
        pit_changes = fetch_sp500_pit_changes(cache=Path("data/raw/sp500_pit_changes.parquet"))
        keep_set = ever_members(pit_changes)          # every ticker ever in the S&P 500
        sector = dict(zip(comp["ticker"], comp["sector"]))  # sectors from full composite
    else:
        keep = {"large": ["500"], "small": ["600"], "all": ["500", "600"]}[args.cap]
        comp = comp[comp["index"].isin(keep)]
        sector = dict(zip(comp["ticker"], comp["sector"]))
        keep_set = set(comp["ticker"])

    px_cache = Path("data/raw/daily_px_statarb_wide.parquet")
    prices = pd.read_parquet(px_cache) if px_cache.exists() else fetch_prices_yf(
        sorted(keep_set), args.start, None)
    prices = prices[[c for c in prices.columns if c in keep_set]]
    # winsorize daily returns against bad ticks / halts (a delisted small-cap's price
    # glitch can fake a huge residual + a fake reversion profit). Real daily moves rarely
    # exceed -50% / +100%.
    rets = daily_returns(prices).clip(lower=-0.5, upper=1.0)

    etf_px = fetch_prices_yf(["SPY"] + sorted(set(SECTOR_ETF.values())), args.start, None)
    etf_ret = daily_returns(etf_px).reindex(rets.index)

    # each stock's factor = its sector ETF return (fallback SPY where sector/ETF missing)
    factor = {}
    for t in rets.columns:
        etf = SECTOR_ETF.get(sector.get(t, ""), "SPY")
        s = etf_ret[etf] if etf in etf_ret else etf_ret["SPY"]
        factor[t] = s.fillna(etf_ret["SPY"])
    factors = pd.DataFrame(factor).reindex(rets.index)

    resid = rolling_residual(rets, factors, window=args.window)
    # s-score = standardized cumulative residual (same logic as residual.s_score, vectorized)
    cum = resid.cumsum()
    s = (cum - cum.rolling(args.window).mean()) / cum.rolling(args.window).std()

    positions = s.apply(lambda col: band_positions(col, entry=args.entry, exit_=args.exit_,
                                                    long_floor=args.long_floor))
    if args.pit:
        # gate trading to actual index-membership days: a name is forced flat when it was
        # not in the S&P 500 (turnover on entry/exit is charged realistically via .diff()).
        mask = membership_mask(pit_changes, positions.index, positions.columns)
        positions = positions.where(mask, 0)
    # execute `skip` days after the signal close (skip>=1 breaks the bid-ask-bounce channel:
    # you can't both measure the signal on and trade at the same close)
    held = positions.shift(1 + args.skip)
    active = held.abs()
    n_active = active.sum(axis=1).replace(0, pd.NA)
    gross = (held * resid).sum(axis=1) / n_active
    turnover = positions.diff().abs()
    cost = (turnover * args.cost_bps / 1e4 * 2).sum(axis=1) / n_active  # stock + ETF leg
    net = (gross - cost).fillna(0)
    net = net[net.ne(0).cumsum() > 0]  # drop leading warm-up

    med_active = int(active.sum(axis=1).replace(0, pd.NA).dropna().median())
    tag = "point-in-time membership" if args.pit else f"{args.cap} cap"
    floor_tag = f", long-floor {args.long_floor}" if args.long_floor is not None else ""
    title = (f"StatArb residual reversion (Avellaneda-Lee) — {tag}{floor_tag}, {rets.shape[1]} names, "
             f"~{med_active} pos/day, skip={args.skip}, {args.cost_bps}bps")
    bench = {"equal_weight_universe": rets.mean(axis=1)}
    card = scorecard(net, bench, n_trials=args.n_trials, periods_per_year=252)
    stem = "residual_pit" if args.pit else "residual"
    if args.long_floor is not None:
        stem += f"_floor{args.long_floor}"
    (out / f"{stem}_scorecard.md").write_text(to_markdown(card, title))
    net.to_frame("net").to_parquet(out / f"{stem}_pnl.parquet")
    register(Path("data/manifest.jsonl"), name="statarb_" + stem, source="yfinance",
             filters={"window": args.window, "entry": args.entry, "names": int(rets.shape[1]),
                      "pit": bool(args.pit)},
             path=str(out / f"{stem}_pnl.parquet"), rows=int(net.ne(0).sum()))
    print(to_markdown(card, title))


if __name__ == "__main__":
    main()

```

================================================================================
## `core/eval/scorecard.py`
================================================================================

```python
"""One scorecard for every track. A signal cannot pick a friendlier rubric."""
import pandas as pd
from core.eval.metrics import sharpe, deflated_sharpe, max_drawdown, hit_rate


def scorecard(net: pd.Series, benchmarks: dict, n_trials: int, periods_per_year: int) -> dict:
    net = net.dropna()
    halves = [net.iloc[: len(net) // 2], net.iloc[len(net) // 2:]]
    return {
        "sharpe": sharpe(net, periods_per_year),
        "deflated_sharpe_prob": deflated_sharpe(net, n_trials, periods_per_year),
        "max_drawdown": max_drawdown(net),
        "hit_rate": hit_rate(net),
        "ann_return": float(net.mean() * periods_per_year),
        "n_obs": len(net),
        "n_trials_declared": n_trials,
        "subperiods": [{"start": str(h.index[0].date()), "end": str(h.index[-1].date()),
                        "sharpe": sharpe(h, periods_per_year)} for h in halves if len(h) > 1],
        "benchmarks": {k: sharpe(v.dropna(), periods_per_year) for k, v in benchmarks.items()},
    }


def to_markdown(result: dict, title: str) -> str:
    lines = [f"# Scorecard — {title}", "",
             f"- Net Sharpe (ann.): **{result['sharpe']:.2f}**",
             f"- Deflated Sharpe prob (n_trials={result['n_trials_declared']}): **{result['deflated_sharpe_prob']:.2%}**",
             f"- Ann. return: {result['ann_return']:.2%} | Max DD: {result['max_drawdown']:.2%} "
             f"| Hit rate: {result['hit_rate']:.2%} | Obs: {result['n_obs']}",
             "", "## Subperiods"]
    lines += [f"- {s['start']} → {s['end']}: Sharpe {s['sharpe']:.2f}" for s in result["subperiods"]]
    lines += ["", "## Benchmarks (Sharpe)"]
    lines += [f"- {k}: {v:.2f}" for k, v in result["benchmarks"].items()]
    return "\n".join(lines) + "\n"

```

================================================================================
## `core/eval/metrics.py`
================================================================================

```python
"""Performance metrics. deflated_sharpe follows Bailey & Lopez de Prado (2014)."""
import numpy as np
import pandas as pd
from scipy import stats

EULER_GAMMA = 0.5772156649015329


def sharpe(returns: pd.Series, periods_per_year: int) -> float:
    r = returns.dropna()
    if len(r) < 2 or r.std(ddof=1) == 0:
        return 0.0
    return float(r.mean() / r.std(ddof=1) * np.sqrt(periods_per_year))


def max_drawdown(returns: pd.Series) -> float:
    curve = (1 + returns.fillna(0)).cumprod()
    return float((curve / curve.cummax() - 1).min())


def hit_rate(returns: pd.Series) -> float:
    r = returns.dropna()
    return float((r > 0).mean()) if len(r) else 0.0


def deflated_sharpe(returns: pd.Series, n_trials: int, periods_per_year: int) -> float:
    """Probability the true Sharpe exceeds zero, deflating for n_trials searches."""
    r = returns.dropna()
    T = len(r)
    if T < 10:
        return 0.0
    sr = float(r.mean() / r.std(ddof=1))  # per-period SR
    sk = float(stats.skew(r))
    ku = float(stats.kurtosis(r, fisher=False))
    if n_trials <= 1:
        sr0 = 0.0
    else:
        # expected max SR of n_trials zero-skill strategies (per-period units)
        z1 = stats.norm.ppf(1 - 1.0 / n_trials)
        z2 = stats.norm.ppf(1 - 1.0 / (n_trials * np.e))
        sr0 = np.sqrt(1.0 / (T - 1)) * ((1 - EULER_GAMMA) * z1 + EULER_GAMMA * z2)
    denom = np.sqrt(max(1e-12, 1 - sk * sr + (ku - 1) / 4.0 * sr**2))
    z = (sr - sr0) * np.sqrt(T - 1) / denom
    return float(stats.norm.cdf(z))

```