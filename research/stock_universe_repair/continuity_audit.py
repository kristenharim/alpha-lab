"""Continuity audit for the frozen stock universe. Read-only; characterizes the v1 coverage
gap so v2 can be certified against it. Writes coverage.csv."""
import json
from pathlib import Path
import pandas as pd

HUNT = Path(__file__).resolve().parents[1] / "hunt2026"
meta = json.loads((HUNT / "sandbox_meta.json").read_text())
panel = pd.concat([pd.read_parquet(HUNT / "train.parquet"),
                   pd.read_parquet(HUNT / "holdout.parquet")])
close, member = panel["close"], panel["member"]
etf = set(meta["etfs"]) | set(meta["signal_only"])
stocks = [c for c in close.columns if c not in etf]

rows = []
for t in stocks:
    m = member[t] if t in member.columns else None
    md = int((m > 0).sum()) if m is not None else 0
    if md == 0:
        continue
    pm = int((close[t].notna() & (m > 0)).sum())
    rows.append({"ticker": t, "member_days": md, "priced_member_days": pm,
                 "coverage": round(pm / md, 4)})
df = pd.DataFrame(rows).sort_values("coverage")
out = Path(__file__).parent / "coverage.csv"
df.to_csv(out, index=False)
print(f"ever-members {len(df)} | zero-coverage {(df.coverage==0).sum()} "
      f"| <0.9 {(df.coverage<0.9).sum()} | clean(>=0.99) {(df.coverage>=0.99).sum()} "
      f"| mean {df.coverage.mean():.3f}")
daily = (close[stocks].notna() & (member[stocks] > 0)).sum(axis=1) / (member[stocks] > 0).sum(axis=1)
print(f"avg daily member coverage {daily.mean():.1%}  -> {out}")
