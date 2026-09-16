"""CRSP monthly stock panel: the survivorship-free universe every stock result gets rebuilt on.

Network (WRDS) lives in `fetch_crsp_monthly`, called only from research scripts. Everything else is
pure and tested offline. Conventions follow the literature so results are comparable to published
numbers: common shares (shrcd 10/11) on NYSE/AMEX/Nasdaq (exchcd 1/2/3), delisting returns folded in,
market equity = |prc| x shrout (CRSP marks bid/ask midpoints with a negative price).

CRSP here ends 2024-12-31 (annual vintage). It is a research source, never a live feed.
"""
import pandas as pd

# Shumway (1997): a performance delisting (codes 500-599) with no recorded delisting return lost
# about 30% on average. Leaving it missing silently books those firms at 0%, which is the
# survivorship bias this panel exists to remove.
SHUMWAY_DLRET = -0.30

MSF_SQL = """
select a.permno, a.date, a.ret, a.prc, a.shrout, b.shrcd, b.exchcd, b.siccd, b.ticker
from crsp.msf a
join crsp.msenames b
  on a.permno = b.permno and b.namedt <= a.date and a.date <= b.nameendt
where a.date between '{start}' and '{end}'
  and b.shrcd in (10, 11) and b.exchcd in (1, 2, 3)
"""
DELIST_SQL = "select permno, dlstdt, dlret, dlstcd from crsp.msedelist"


def apply_delisting(msf: pd.DataFrame, delist: pd.DataFrame) -> pd.DataFrame:
    """Add `ret_adj`: the month's return including the delisting return. (1+ret)(1+dlret)-1 when both
    exist; dlret alone when the month has no regular return; Shumway's -30% for a performance
    delisting with no dlret.

    87% of CRSP delistings are dated the month AFTER the security's last monthly record, so a plain
    (permno, month) merge drops them and books every one at 0%. Those get their own row in the
    delisting month: no price, identifiers carried from the last record, so me_lag (computed later)
    is the weight the stock actually had going into the month it died."""
    out = msf.copy()
    out["ym"] = pd.to_datetime(out["date"]).dt.to_period("M")
    d = delist.copy()
    d["ym"] = pd.to_datetime(d["dlstdt"]).dt.to_period("M")
    missing_perf = d["dlret"].isna() & d["dlstcd"].between(500, 599)
    d.loc[missing_perf, "dlret"] = SHUMWAY_DLRET
    d = d.dropna(subset=["dlret"])[["permno", "ym", "dlret"]]

    last = out.sort_values("date").groupby("permno").tail(1)
    nxt = d.merge(last, on="permno", suffixes=("", "_last"))
    nxt = nxt[nxt["ym"] == nxt["ym_last"] + 1]
    if len(nxt):
        extra = nxt.drop(columns=["ym_last", "date"]).copy()
        extra["date"] = extra["ym"].dt.to_timestamp(how="end").dt.normalize()
        for c in ("ret", "prc", "shrout"):
            if c in extra:
                extra[c] = float("nan")
        extra = extra.drop(columns=["dlret"])
        out = pd.concat([out, extra[[c for c in out.columns if c in extra.columns]]], ignore_index=True)

    out = out.merge(d, on=["permno", "ym"], how="left")
    r, dl = out["ret"], out["dlret"]
    out["ret_adj"] = ((1 + r.fillna(0)) * (1 + dl.fillna(0)) - 1).where(r.notna() | dl.notna())
    return out.drop(columns=["ym"]).sort_values(["permno", "date"], ignore_index=True)


def add_market_equity(panel: pd.DataFrame) -> pd.DataFrame:
    """me in $ millions (shrout is thousands), plus me_lag: last month's me, the only weight a
    portfolio formed at the start of the month could have used."""
    p = panel.sort_values(["permno", "date"]).copy()
    p["me"] = p["prc"].abs() * p["shrout"] / 1000.0
    p["me_lag"] = p.groupby("permno")["me"].shift(1)
    return p


def momentum_signal(panel: pd.DataFrame) -> pd.DataFrame:
    """12-2 momentum: cumulative ret_adj over months t-12..t-2, skipping t-1 (short-term reversal).
    Requires all 11 returns, the standard filter. Uses only data dated before month t."""
    p = panel.sort_values(["permno", "date"]).copy()
    lr = (1 + p["ret_adj"]).where(p["ret_adj"].notna())
    g = lr.groupby(p["permno"])
    p["mom"] = g.transform(lambda s: s.shift(2).rolling(11, min_periods=11).apply(lambda x: x.prod(), raw=True)) - 1
    return p


def decile_long_short(panel: pd.DataFrame, signal: str) -> pd.Series:
    """Monthly value-weighted top-minus-bottom decile return, NYSE breakpoints (exchcd 1), weights
    from me_lag. The standard construction, so the result can be checked against published series."""
    p = panel.dropna(subset=[signal, "ret_adj", "me_lag"])
    p = p[p["me_lag"] > 0]

    def one_month(m: pd.DataFrame) -> float:
        nyse = m.loc[m["exchcd"] == 1, signal]
        if len(nyse) < 20:
            return float("nan")
        lo, hi = nyse.quantile(0.1), nyse.quantile(0.9)

        def vw(x):
            return (x["ret_adj"] * x["me_lag"]).sum() / x["me_lag"].sum() if len(x) else float("nan")
        return vw(m[m[signal] >= hi]) - vw(m[m[signal] <= lo])
    return p.groupby("date").apply(one_month)


def value_weighted_market(panel: pd.DataFrame) -> pd.Series:
    p = panel.dropna(subset=["ret_adj", "me_lag"])
    p = p[p["me_lag"] > 0]
    return p.groupby("date").apply(lambda m: (m["ret_adj"] * m["me_lag"]).sum() / m["me_lag"].sum())


def fetch_crsp_monthly(db, start: str = "1963-01-01", end: str = "2024-12-31") -> pd.DataFrame:
    """NETWORK. `db` is an open wrds.Connection. Returns the delisting-adjusted panel with me/me_lag."""
    msf = db.raw_sql(MSF_SQL.format(start=start, end=end), date_cols=["date"])
    delist = db.raw_sql(DELIST_SQL, date_cols=["dlstdt"])
    for c in ("permno", "shrcd", "exchcd"):
        msf[c] = msf[c].astype(int)
    delist["permno"] = delist["permno"].astype(int)
    return add_market_equity(apply_delisting(msf, delist))
