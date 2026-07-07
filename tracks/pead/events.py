"""Earnings events + analyst-estimate SUE proxy (WRDS/IBES swaps in later)."""
import pandas as pd


def surprise_score(events: pd.DataFrame) -> pd.DataFrame:
    ev = events.dropna(subset=["eps_actual", "eps_estimate"]).copy()
    if ev.empty:
        raise ValueError("no events with both actual and estimate")
    ev["date"] = pd.to_datetime(ev["date"])
    ev["sue"] = (ev["eps_actual"] - ev["eps_estimate"]) / ev["eps_estimate"].abs().clip(lower=0.01)
    return ev.reset_index(drop=True)


def fetch_earnings_yf(tickers: list[str]) -> pd.DataFrame:
    """Network: pull earnings dates + reported/estimated EPS from yfinance."""
    import yfinance as yf
    frames = []
    for t in tickers:
        try:
            df = yf.Ticker(t).get_earnings_dates(limit=28)
        except Exception:
            continue
        if df is None or df.empty:
            continue
        df = df.reset_index()
        df.columns = [c.lower().replace(" ", "_") for c in df.columns]
        date_col = next((c for c in df.columns if "earnings" in c and "date" in c), None)
        if date_col is None:
            continue
        frames.append(pd.DataFrame({
            "ticker": t,
            "date": pd.to_datetime(df[date_col]).dt.tz_localize(None).dt.normalize(),
            "eps_actual": df.get("reported_eps"),
            "eps_estimate": df.get("eps_estimate"),
        }))
    if not frames:
        raise ValueError("no earnings data returned")
    return pd.concat(frames, ignore_index=True)
