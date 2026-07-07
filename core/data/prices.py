"""Price loading + validation. Network fetch lives here but is called only from scripts/."""
import pandas as pd


def validate_prices(df: pd.DataFrame) -> pd.DataFrame:
    if df is None or df.empty:
        raise ValueError("price frame is empty")
    if df.index.duplicated().any():
        raise ValueError("duplicate dates in price index")
    if not df.index.is_monotonic_increasing:
        raise ValueError("price index not sorted ascending")
    return df


def daily_returns(prices: pd.DataFrame) -> pd.DataFrame:
    return validate_prices(prices).pct_change().dropna(how="all")


def fetch_prices_yf(tickers: list[str], start: str, end: str | None,
                    interval: str = "1d", chunk_size: int = 200) -> pd.DataFrame:
    """Adjusted closes from yfinance. Downloads in chunks so large universes
    (S&P 1500) don't overwhelm a single request. interval: '1d' or '1mo'."""
    import yfinance as yf
    frames = []
    for i in range(0, len(tickers), chunk_size):
        batch = tickers[i:i + chunk_size]
        raw = yf.download(batch, start=start, end=end, interval=interval,
                          auto_adjust=True, progress=False)
        if raw.empty:
            continue
        if isinstance(raw.columns, pd.MultiIndex):
            px = raw["Close"]
        else:
            px = raw[["Close"]].rename(columns={"Close": batch[0]})
        frames.append(px)
    if not frames:
        raise ValueError("no price data returned")
    px = pd.concat(frames, axis=1).dropna(how="all")
    px = px.loc[:, ~px.columns.duplicated()]
    return validate_prices(px)
