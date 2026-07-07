"""Distance-based pairs trading (Gatev, Goetzmann & Rouwenhorst 2006).

Form pairs by minimum sum-of-squared-deviation between normalized price paths in
a formation window; trade divergences of the normalized spread in the next window.
Runs on daily EOD closes — the most free-data-replicable StatArb strategy.
"""
import pandas as pd
from tracks.statarb.bands import band_positions


def normalize_prices(prices: pd.DataFrame) -> pd.DataFrame:
    """Normalize each price series to start at 1 (a cumulative-return index)."""
    first = prices.ffill().bfill().iloc[0]
    return prices.divide(first, axis=1)


def select_pairs(prices: pd.DataFrame, n_pairs: int = 20) -> list[tuple[str, str]]:
    """Pick the n_pairs tickers with the smallest sum-of-squared normalized-price gap."""
    norm = normalize_prices(prices.dropna(axis=1, how="any"))
    cols = list(norm.columns)
    dists = []
    for i in range(len(cols)):
        for j in range(i + 1, len(cols)):
            ssd = float(((norm[cols[i]] - norm[cols[j]]) ** 2).sum())
            dists.append((ssd, cols[i], cols[j]))
    dists.sort(key=lambda t: t[0])
    return [(a, b) for _, a, b in dists[:n_pairs]]


def select_pairs_sectored(prices: pd.DataFrame, sectors: dict[str, str],
                          n_pairs: int = 20) -> list[tuple[str, str]]:
    """Like select_pairs but only forms pairs WITHIN the same sector, then keeps the
    globally closest n_pairs. Restricting to same-sector pairs is both economically
    sensible (they share fundamentals) and keeps the O(N^2) search tractable on a wide
    universe."""
    norm = normalize_prices(prices.dropna(axis=1, how="any"))
    cols = list(norm.columns)
    by_sector: dict[str, list[str]] = {}
    for c in cols:
        by_sector.setdefault(sectors.get(c, "Unknown"), []).append(c)
    dists = []
    for members in by_sector.values():
        for i in range(len(members)):
            for j in range(i + 1, len(members)):
                ssd = float(((norm[members[i]] - norm[members[j]]) ** 2).sum())
                dists.append((ssd, members[i], members[j]))
    dists.sort(key=lambda t: t[0])
    return [(a, b) for _, a, b in dists[:n_pairs]]


def spread_zscore(a: pd.Series, b: pd.Series, window: int | None = None) -> pd.Series:
    """Z-score of the normalized-price spread between two series."""
    pair = pd.concat([a, b], axis=1).dropna()
    norm = normalize_prices(pair)
    spread = norm.iloc[:, 0] - norm.iloc[:, 1]
    if window:
        mu = spread.rolling(window).mean()
        sd = spread.rolling(window).std().replace(0, pd.NA)
    else:
        mu = spread.mean()
        sd = spread.std()
        sd = pd.NA if sd == 0 else sd
    return (spread - mu) / sd


def pair_zscore_oos(form_a: pd.Series, form_b: pd.Series,
                    trade_a: pd.Series, trade_b: pd.Series) -> pd.Series:
    """Out-of-sample spread z-score for the TRADING window, standardized by the
    FORMATION window's spread mean/std (Gatev-Goetzmann-Rouwenhorst). No look-ahead:
    the bands are fixed from formation data before the trading period starts.
    """
    a_all = pd.concat([form_a, trade_a])
    b_all = pd.concat([form_b, trade_b])
    a_all = a_all[~a_all.index.duplicated()]
    b_all = b_all[~b_all.index.duplicated()]
    base_a = form_a.dropna().iloc[0]
    base_b = form_b.dropna().iloc[0]
    spread_all = a_all / base_a - b_all / base_b
    form_spread = spread_all.loc[form_a.index]
    mu, sd = form_spread.mean(), form_spread.std()
    if sd == 0 or pd.isna(sd):
        return pd.Series(pd.NA, index=trade_a.index)
    return (spread_all.loc[trade_a.index] - mu) / sd


def pair_pnl(positions: pd.Series, ret_a: pd.Series, ret_b: pd.Series) -> pd.Series:
    """Daily P&L of a pair. position +1 = long A / short B. Position lagged one day
    (formed on yesterday's close, earns today's spread return) — no look-ahead."""
    df = pd.concat([positions.rename("pos"), ret_a.rename("a"), ret_b.rename("b")], axis=1).dropna()
    held = df["pos"].shift(1).fillna(0)
    return held * (df["a"] - df["b"])
