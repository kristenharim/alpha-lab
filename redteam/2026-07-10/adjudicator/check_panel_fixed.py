"""Agent 3 data/universe checks on the frozen hunt2026 panels. Read-only."""
import sys
import pandas as pd
import numpy as np
from pathlib import Path

H = Path.home() / "projects/alpha-lab/research/hunt2026"
OUT = Path.home() / "projects/alpha-lab/redteam/2026-07-10/agent3"

train = pd.read_parquet(H / "train.parquet")
hold = pd.read_parquet(H / "holdout.parquet")
panel = pd.concat([train, hold])
p2005 = pd.read_parquet(H / "panel_2005.parquet")
xm = pd.read_parquet(H / "panel_xmarket.parquet")

ETFS = ["SPY","QQQ","IWM","DIA","MDY","EFA","EEM","VGK","EWJ","TLT","IEF","SHY","BIL",
        "LQD","HYG","TIP","GLD","SLV","DBC","USO","UNG","VNQ","UUP","FXE","XLB","XLE",
        "XLF","XLI","XLK","XLP","XLU","XLV","XLY","XLRE","XLC","RSP","SVXY"]

def sec(t): print(f"\n===== {t} =====")

sec("A. calendar integrity (train+holdout)")
idx = panel.index
print("range:", idx[0], "->", idx[-1], "rows:", len(idx))
print("dup dates:", idx.duplicated().sum(), "| monotonic:", idx.is_monotonic_increasing)
print("weekend rows:", (idx.dayofweek >= 5).sum())
print("train last:", train.index[-1], "holdout first:", hold.index[0],
      "overlap:", len(train.index.intersection(hold.index)))
per_year = pd.Series(1, index=idx).groupby(idx.year).sum()
print("rows/year:\n", per_year.to_string())
spy_nan_rows = panel["close"]["SPY"].isna()
print("rows where SPY close is NaN:", spy_nan_rows.sum(),
      list(idx[spy_nan_rows])[:10])
etf_all_nan = panel["close"][ETFS].isna().all(axis=1)
print("rows with ALL ETF closes NaN (phantom days):", etf_all_nan.sum(), list(idx[etf_all_nan])[:10])
# gaps > 4 calendar days (excl normal weekends+holidays)
d = pd.Series(idx).diff().dt.days
print("gaps >5 days:", [(str(idx[i-1].date()), str(idx[i].date())) for i in np.where(d > 5)[0]])

sec("A2. same for panel_2005")
i5 = p2005.index
print("range:", i5[0], "->", i5[-1], "rows:", len(i5), "dups:", i5.duplicated().sum(),
      "weekends:", (i5.dayofweek >= 5).sum())
print("SPY NaN rows in p2005:", p2005["close"]["SPY"].isna().sum())
d5 = pd.Series(i5).diff().dt.days
print("gaps >5 days:", [(str(i5[i-1].date()), str(i5[i].date())) for i in np.where(d5 > 5)[0]])

sec("B. survivorship / membership coverage")
member = panel["member"]
close = panel["close"]
stocks = [t for t in close.columns if t not in ETFS and t != "^VIX"]
print("n stock columns:", len(stocks))
msum = member[stocks].sum(axis=1)
print("daily member count: min", msum.min(), "max", msum.max(),
      "| by year mean:\n", msum.groupby(idx.year).mean().round(1).to_string())
# members flagged 1 but close NaN that day
mem_bool = member[stocks] > 0
nan_while_member = (mem_bool & close[stocks].isna())
frac = nan_while_member.sum(axis=1)
print("members with NaN close, daily count: mean %.1f max %d" % (frac.mean(), frac.max()))
worst = nan_while_member.sum(0).sort_values(ascending=False)
print("worst offenders (days member&NaN):\n", worst[worst > 0].head(20).to_string())

sec("B2. change-log ever-members vs panel columns (missing dead names)")
sys.path.insert(0, str(Path.home() / "projects/alpha-lab"))
pit = pd.read_parquet(Path.home() / "projects/alpha-lab/data/raw/sp500_pit.parquet")
recent = pit[pit["date"] >= "2014-01-01"]
ever = set()
for m in recent["members"]:
    ever |= set(m)
print("ever-members since 2014 in change-log:", len(ever))
have = ever & set(close.columns)
missing = sorted(ever - set(close.columns))
print("present in panel:", len(have), "| MISSING from panel:", len(missing))
print("missing sample:", missing[:60])
# how many missing names were members on a given date each year
for y in [2015, 2017, 2019, 2021, 2023, 2025]:
    snap_rows = recent[recent["date"] <= f"{y}-06-30"]
    if len(snap_rows) == 0: continue
    snap = set(snap_rows.iloc[-1]["members"])
    print(f"members on {y}-06-30: {len(snap)}, missing from panel: {len(snap - set(close.columns))}")

sec("B3. delisted-in-sample names (data ends early) — properly dead or silently gone?")
last_valid = close[stocks].apply(lambda s: s.last_valid_index())
ended_early = last_valid[last_valid < pd.Timestamp("2026-06-01")]
print("stock columns whose price history ends before 2026-06:", len(ended_early))
print(ended_early.sort_values().tail(15).to_string())
first_valid = close[stocks].apply(lambda s: s.first_valid_index())
started_late = first_valid[first_valid > pd.Timestamp("2014-06-01")]
print("stock columns starting after 2014-06:", len(started_late))

sec("B4. membership spot-checks (known index events)")
def memb_on(tkr, day):
    day = pd.Timestamp(day)
    if tkr not in member.columns: return f"{tkr}: not in panel"
    loc = member.index.get_indexer([day], method="ffill")[0]
    return f"{tkr} member on {day.date()}: {member[tkr].iloc[loc]}"
for tkr, day in [("TSLA","2020-12-18"),("TSLA","2020-12-21"),("META","2014-06-02"),
                 ("SMCI","2024-03-18"),("SMCI","2024-03-15"),("PLTR","2024-09-23"),
                 ("PLTR","2024-09-20"),("ENPH","2021-01-07"),("ENPH","2021-01-06")]:
    print(memb_on(tkr, day))

sec("C. price availability before membership entry (fine if masked) + after exit")
# for momentum_concentrated eligibility uses member mask; check mask has no member=1 before first price
first_price = close[stocks].apply(lambda s: s.first_valid_index())
bad = []
for t in stocks:
    m = member[t]
    first_mem = m[m > 0].index.min() if (m > 0).any() else None
    if first_mem is not None and first_price[t] is not None and first_mem < first_price[t]:
        bad.append((t, str(first_mem.date()), str(first_price[t].date())))
print("tickers flagged member BEFORE any price exists:", len(bad), bad[:15])

sec("D. ETF inceptions & pre-inception member flags (panel_2005)")
m5 = p2005["member"]; c5 = p2005["close"]
for t in ["SVXY","XLC","XLRE","BIL","HYG","UUP","DBC","USO","TIP","RSP"]:
    fp = c5[t].first_valid_index()
    pre = m5[t][m5.index < fp].sum() if fp is not None else -1
    print(f"{t}: first price {fp.date() if fp is not None else None}, member=1 days before inception: {int(pre)}")

sec("E. stale prices / zero volume / zero prices (ETFs, full panel)")
ec = panel["close"][ETFS]; ev = panel["volume"][ETFS]
for t in ETFS:
    s = ec[t].dropna()
    rep = (s.diff() == 0)
    runs = rep.groupby((~rep).cumsum()).sum().max()
    zv = int((ev[t].reindex(s.index) == 0).sum())
    if (runs and runs >= 3) or zv > 0:
        print(f"{t}: max identical-close run {int(runs)}, zero-volume days {zv}")
print("any nonpositive ETF closes:", int((ec <= 0).sum().sum()))
st = panel["close"][stocks]
print("any nonpositive stock closes:", int((st <= 0).sum().sum()))
# stocks with long flat runs (stale)
flat = {}
for t in stocks:
    s = st[t].dropna()
    if len(s) < 50: continue
    rep = (s.diff() == 0)
    mx = rep.groupby((~rep).cumsum()).sum().max()
    if mx >= 10: flat[t] = int(mx)
print("stocks with >=10-day identical-close runs:", flat)

sec("F. ^VIX sanity & alignment")
vix = panel["close"]["^VIX"]
print("VIX NaN days:", vix.isna().sum(), "range:", vix.min(), vix.max())
print("VIX NaN while SPY present:", int((vix.isna() & panel['close']['SPY'].notna()).sum()))

sec("G. open vs close sanity (adjusted open present?)")
op = panel["open"][ETFS]
print("ETF open NaN frac:", float(op.isna().mean().mean()).__round__(4))
ratio = (op / ec).stack()
print("open/close ratio quantiles:", ratio.quantile([0.0001, 0.5, 0.9999]).round(3).to_string())

sec("H. panel vs panel_2005 consistency on overlap (same tickers, 2014+)")
common = [t for t in ETFS if t in c5.columns]
ov = panel.index.intersection(p2005.index)
diff = (panel["close"][common].loc[ov] - p2005["close"][common].loc[ov]).abs()
rel = diff / panel["close"][common].loc[ov].abs()
print("max relative close diff:", float(rel.max().max()))
print("cols with rel diff > 1e-6:", rel.max()[rel.max() > 1e-6].to_string())

sec("I. SVXY event check")
s = panel["close"]["SVXY"].dropna()
r = s.pct_change()
print("SVXY worst days:", r.nsmallest(3).to_string())
print("SVXY first price:", s.index[0].date())
s5 = p2005["close"]["SVXY"].dropna()
print("p2005 SVXY first price:", s5.index[0].date())

sec("J. xmarket panel checks")
xc = xm["close"]
print("xmarket tickers:", list(xc.columns), "rows:", len(xm), xm.index[0].date(), "->", xm.index[-1].date())
print("first valid:", {t: str(xc[t].first_valid_index().date()) for t in xc.columns})
print("dup dates:", xm.index.duplicated().sum())
