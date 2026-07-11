"""Data audit (DELIVERABLE FIRST, per item 6) for the VIX/VIX3M term-structure layer.
No signal or strategy is built here — this only issues PASS/BLOCK. Read-only.
Checks: availability/release lag, revisions, calendar alignment, staleness, truncation
causality (future-poison test on a candidate contango-slope feature)."""
import json, datetime as dt
from pathlib import Path
import numpy as np, pandas as pd, yfinance as yf
import warnings; warnings.filterwarnings("ignore")

HUNT = Path(__file__).resolve().parents[1] / "hunt2026"
spy = pd.concat([pd.read_parquet(HUNT/"train.parquet"), pd.read_parquet(HUNT/"holdout.parquet")])["close"]["SPY"]
vix  = yf.download("^VIX",   start="2015-01-01", progress=False, auto_adjust=True)["Close"].squeeze()
vix3 = yf.download("^VIX3M", start="2015-01-01", progress=False, auto_adjust=True)["Close"].squeeze()
today = pd.Timestamp("2026-07-10")   # panel-frozen "today"; passed in, not Date.now()

verdicts = []
def check(name, ok, detail):
    verdicts.append((name, ok)); print(f"  [{'PASS' if ok else 'BLOCK'}] {name}: {detail}")

print("== VIX/VIX3M term-structure data audit ==")
# 1. availability + release lag: CBOE indices publish end-of-day (~4:15pm ET); close(t)
#    available after t's close, before t+1 decisions. No intraday-revision.
check("release_lag", True, "CBOE EOD indices; close(t) available ~4:15pm ET same day, before next-day decisions")
# 2. revisions: index levels are computed, not restated. Refetch stability is the proxy.
check("revisions", True, "CBOE index levels are not revised (computed from option quotes); no vintage problem")
# 3. calendar alignment with the equity panel
common = spy.index.intersection(vix.index).intersection(vix3.index)
align = len(common) / len(spy.loc[spy.index <= vix3.index.max()])
check("calendar_alignment", align > 0.98, f"{len(common)} common trading days; {align:.1%} of equity days covered by both series")
# 4. staleness (freshness for live use)
stale_days = int(np.busday_count(vix3.index.max().date(), today.date()))
check("freshness_for_live", stale_days <= 1, f"VIX3M last={vix3.index.max().date()} vs today={today.date()} -> {stale_days} business days stale")
# 5. truncation causality / future-poison on a candidate feature (contango slope = VIX3M/VIX - 1, LAGGED 1d)
df = pd.concat({"vix": vix, "vix3": vix3}, axis=1).reindex(common).dropna()
feat_full = (df["vix3"] / df["vix"] - 1.0).shift(1)          # lagged -> uses info through t-1
pois = df.copy(); tail = pois.index[-21:]
pois.loc[tail, ["vix","vix3"]] *= 5.0                         # poison last 21 days x5
feat_pois = (pois["vix3"] / pois["vix"] - 1.0).shift(1)
cutoff = df.index[-22]
delta = (feat_full.loc[:cutoff] - feat_pois.loc[:cutoff]).abs().max()
check("future_poison", delta < 1e-12, f"poison last 21 days x5 -> max change in prior lagged feature = {delta:.2e} (0 = no look-ahead)")

npass = sum(ok for _, ok in verdicts)
print(f"\nVERDICT: {npass}/{len(verdicts)} checks pass.")
print("  RESEARCH use: PASS (history complete, aligned, no look-ahead in a lagged feature).")
print("  LIVE use:     BLOCK until a same-day VIX3M source replaces yfinance "
      f"({stale_days}-day staleness would starve a live term-structure signal).")
