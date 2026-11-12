import pandas as pd
from pathlib import Path

H = Path.home() / "projects/alpha-lab/research/hunt2026"
train = pd.read_parquet(H / "train.parquet")
hold = pd.read_parquet(H / "holdout.parquet")
panel = pd.concat([train, hold])
close = panel["close"]; member = panel["member"]

ETFS = {"SPY","QQQ","IWM","DIA","MDY","EFA","EEM","VGK","EWJ","TLT","IEF","SHY","BIL",
        "LQD","HYG","TIP","GLD","SLV","DBC","USO","UNG","VNQ","UUP","FXE","XLB","XLE",
        "XLF","XLI","XLK","XLP","XLU","XLV","XLY","XLRE","XLC","RSP","SVXY","^VIX"}
stocks = [t for t in close.columns if t not in ETFS]

print("=== specific live names ===")
for t in ["BK","MMC","K","IPG","HES","CMA","HOLX","SEE","AAPL","MSFT","JPM"]:
    s = close[t]
    print(f"{t}: n_valid={s.notna().sum()}, first={s.first_valid_index()}, last={s.last_valid_index()}")

print("\n=== entirely-NaN stock columns ===")
nn = close[stocks].notna().sum()
allnan = nn[nn == 0]
print("count:", len(allnan))
print(sorted(allnan.index)[:80])

print("\n=== columns with <100 valid days ===")
few = nn[(nn > 0) & (nn < 100)]
print(len(few)); print(few.to_string())

print("\n=== member-days lost to all-NaN columns vs partial ===")
mem = member[stocks] > 0
nan_while_mem = (mem & close[stocks].isna()).sum()
tot = nan_while_mem[nan_while_mem > 0].sort_values(ascending=False)
allnan_set = set(allnan.index)
print("total member-day-NaN:", int(nan_while_mem.sum()))
print("from all-NaN columns:", int(nan_while_mem[nan_while_mem.index.isin(allnan_set)].sum()))
print("n tickers with any member&NaN:", (nan_while_mem > 0).sum())

print("\n=== 2026-05-25 phantom row: which columns have data? ===")
row = panel.loc[pd.Timestamp("2026-05-25")]
c = row["close"].dropna()
print("non-NaN closes:", len(c), list(c.index)[:20], c.head().to_string())
v = row["volume"].dropna()
print("non-NaN volumes:", len(v))

print("\n=== ticker-reuse overlap: member=1 AND price present but price starts after membership ended? ===")
# suspicious: tickers whose first price is > 2015 and whose membership window ended before first price
import numpy as np
sus = []
for t in stocks:
    s = close[t]
    fp = s.first_valid_index()
    if fp is None: continue
    m = member[t] > 0
    if not m.any(): continue
    last_mem = m[m].index.max()
    first_mem = m[m].index.min()
    if fp > first_mem:  # price starts after membership began
        overlap = int((m & s.notna()).sum())
        sus.append((t, str(first_mem.date()), str(last_mem.date()), str(fp.date()), overlap))
sus = [x for x in sus if x[4] > 0 and pd.Timestamp(x[3]) > pd.Timestamp(x[1]) + pd.Timedelta(days=400)]
print("tickers member long before their first price, yet overlapping member&price days:")
for x in sorted(sus, key=lambda r: -r[4])[:25]:
    print(x)

print("\n=== how many stock cols not in ever-members(2014+) ===")
pit = pd.read_parquet(Path.home() / "projects/alpha-lab/data/raw/sp500_pit.parquet")
recent = pit[pit["date"] >= "2014-01-01"]
ever = set()
for m in recent["members"]:
    ever |= set(m)
extra = [t for t in stocks if t not in ever]
print("stock cols:", len(stocks), "ever-members:", len(ever), "extra (never S&P500 since 2014):", len(extra))
print("extra sample:", sorted(extra)[:30])
comp = pd.read_parquet(Path.home() / "projects/alpha-lab/data/raw/sp_composite.parquet")
print("sp_composite cache rows:", len(comp), "index col values:", comp["index"].value_counts().to_dict() if "index" in comp else "n/a")
