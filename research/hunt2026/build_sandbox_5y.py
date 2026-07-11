"""Re-split the existing hunt2026 panel at the 5-year backdate cut: 2021-07-10.

train5y.parquet  = data <= 2021-07-10 (builders-only view for round 2)
holdout5y.parquet = 2021-07-10 -> 2026-07-10 (evaluator-only, 5 blind years)
No new network pull — the panel already spans 2014 -> 2026-07-10.
"""
import json
from pathlib import Path
import pandas as pd

HERE = Path(__file__).parent
CUT5 = "2021-07-10"

panel = pd.concat([pd.read_parquet(HERE / "train.parquet"),
                   pd.read_parquet(HERE / "holdout.parquet")])
cut = pd.Timestamp(CUT5)
train5, hold5 = panel[panel.index <= cut], panel[panel.index > cut]
train5.to_parquet(HERE / "train5y.parquet")
hold5.to_parquet(HERE / "holdout5y.parquet")
meta = json.loads((HERE / "sandbox_meta.json").read_text())
meta.update({"cut5y": CUT5, "train5y_rows": len(train5), "holdout5y_rows": len(hold5)})
(HERE / "sandbox_meta.json").write_text(json.dumps(meta, indent=2))
print(f"train5y {len(train5)} rows -> {train5.index[-1].date()}, "
      f"holdout5y {len(hold5)} rows {hold5.index[0].date()} -> {hold5.index[-1].date()}")
