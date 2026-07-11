"""Agent4: cache 5y daily net series for all 18 non-benchmark specs + SPY/QQQ benchmarks.
Read-only vs production; writes only into agent4/."""
import sys
from pathlib import Path

import pandas as pd

HUNT = Path.home() / "projects/alpha-lab/research/hunt2026"
OUT = Path(__file__).parent
sys.path.insert(0, str(HUNT))
import harness  # noqa: E402

CUT5 = "2021-07-10"
panel = pd.read_parquet(HUNT / "panel_2005.parquet")

nets = {}
for d in sorted((HUNT / "specs").iterdir()):
    if not (d / "spec.py").exists() or (d / "benchmark").exists():
        continue
    r = harness.run(harness.load_spec(d), panel, start=CUT5)
    nets[d.name] = r["net_daily"]
    print(d.name, "ok", len(r["net_daily"]))

# no-skill controls through the identical harness
nets["_SPY_BH"] = harness.spy_benchmark(panel, start=CUT5)["net_daily"]


class _Qqq:
    @staticmethod
    def target_weights(p):
        c = p["close"]
        return pd.DataFrame(0.0, index=c.index, columns=c.columns).assign(QQQ=1.0)


nets["_QQQ_BH"] = harness.run(_Qqq, panel, start=CUT5)["net_daily"]

df = pd.DataFrame(nets)
df.to_parquet(OUT / "nets5y.parquet")
print("saved", df.shape)
