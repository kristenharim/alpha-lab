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


# yfinance defaults to threads=True: one worker PER TICKER (~200 per chunk), each holding a
# socket + the cert file + the shared sqlite tz-cache. launchd gives its jobs a 256-FD soft
# limit (an interactive shell gets 1048576), so the nightly runner exhausted FDs and failed as
# "getaddrinfo() thread failed to start" / "unable to open database file" / cert-verify errors
# — while every by-hand run passed. Bound the workers; correctness must not depend on ulimit.
YF_THREADS = 8


def fetch_prices_yf(tickers: list[str], start: str, end: str | None,
                    interval: str = "1d", chunk_size: int = 200,
                    threads: int = YF_THREADS) -> pd.DataFrame:
    """Adjusted closes from yfinance. Downloads in chunks so large universes
    (S&P 1500) don't overwhelm a single request. interval: '1d' or '1mo'."""
    import yfinance as yf
    frames = []
    for i in range(0, len(tickers), chunk_size):
        batch = tickers[i:i + chunk_size]
        raw = yf.download(batch, start=start, end=end, interval=interval,
                          auto_adjust=True, progress=False, threads=threads)
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


def rolling_dollar_adv(prices: pd.DataFrame, volume: pd.DataFrame,
                       window: int = 20) -> pd.DataFrame:
    """Trailing median dollar volume (price x shares) per name — the liquidity gauge."""
    px, vol = prices.align(volume, join="inner")
    return (px * vol).rolling(window).median()


def fetch_volume_yf(tickers: list[str], start: str, end: str | None,
                    chunk_size: int = 200, threads: int = YF_THREADS) -> pd.DataFrame:
    """Share volume from yfinance, same chunking as fetch_prices_yf. Network — script-only."""
    import yfinance as yf
    frames = []
    for i in range(0, len(tickers), chunk_size):
        batch = tickers[i:i + chunk_size]
        raw = yf.download(batch, start=start, end=end, interval="1d",
                          auto_adjust=True, progress=False, threads=threads)
        if raw.empty:
            continue
        vol = raw["Volume"] if isinstance(raw.columns, pd.MultiIndex) else \
            raw[["Volume"]].rename(columns={"Volume": batch[0]})
        frames.append(vol)
    if not frames:
        raise ValueError("no volume data returned")
    v = pd.concat(frames, axis=1).dropna(how="all")
    return v.loc[:, ~v.columns.duplicated()]
