"""Stage 2 diagnostics (read-only; adversarial-review minimum experiment).

(1) Static-beta full-span alpha per book: single OLS on [Mkt-RF,SMB,HML,Mom] over the
    882 window days, intercept CI via 63d circular-block bootstrap (5000 draws).
    The static-vs-windowed-L2 delta is the timing channel the windowed design absorbs.
(2) Corrected VRP statistic: rho of pooled L3 book residuals vs L3-RESIDUALIZED SVXY
    excess (the frozen raw-SVXY version has a mechanical ceiling sqrt(0.219) < 0.5).
Results embedded in FLOOR_ATTRIB.md story; rerun this to reproduce.
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE.parents[1]))
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parents[1] / "research/hunt2026"))
import harness  # noqa: E402
from run_floor_attrib import BOOKS, alphas_for  # noqa: E402
from run_floor_industry import build_windows  # noqa: E402

ROOT = HERE.parents[1]
SEED, N_BOOT, BLOCK = 11, 5000, 63


def main():
    ff = pd.read_parquet(ROOT / "data/raw/ff_factors_daily.parquet")
    px = pd.read_parquet(ROOT / "data/raw/daily_px_statarb_wide.parquet")
    px.index = pd.to_datetime(px.index)
    ret_dates = px.pct_change(fill_method=None).iloc[1:].index.intersection(ff.index)
    wins = build_windows()
    env = []
    for w in wins:
        n0 = list(ret_dates).index(pd.Timestamp(w["d0"]))
        env.append(dict(d0=w["d0"], dates=ret_dates[n0:n0 + 63], fa=w["fa"],
                        sec=w["sec_ret"], vet=np.empty((63, 0)), n_l4=0))
    all_dates = pd.DatetimeIndex(np.concatenate([e["dates"] for e in env]))
    rf = ff["RF"]
    X = np.column_stack([np.ones(len(all_dates)),
                         ff.loc[all_dates, ["Mkt-RF", "SMB", "HML", "Mom"]].values])
    panel = harness.load_full()
    rng = np.random.default_rng(SEED)

    def boot(rex):
        n = len(rex)
        b_full, *_ = np.linalg.lstsq(X, rex, rcond=None)
        a = []
        for _ in range(N_BOOT):
            idx = np.concatenate([(np.arange(BLOCK) + s) % n
                                  for s in rng.integers(0, n, n // BLOCK)])
            b, *_ = np.linalg.lstsq(X[idx], rex[idx], rcond=None)
            a.append(b[0])
        lo, hi = np.quantile(a, [0.025, 0.975])
        return b_full[0], lo, hi

    for name in BOOKS + ["bench_qqq_buyhold"]:
        nd = harness.run(harness.load_spec(
            str(ROOT / "research/hunt2026/specs" / name)), panel)["net_daily"]
        rex = (nd.reindex(all_dates) - rf.reindex(all_dates)).values
        a, lo, hi = boot(rex)
        sig = "SIG" if (lo > 0 or hi < 0) else "ns"
        print(f"{name:24s} static-beta alpha {a * 252:+7.1%} "
              f"[{lo * 252:+7.1%}, {hi * 252:+7.1%}] {sig}")

    svxy = panel["close"]["SVXY"].pct_change()
    svxy_res = []
    for e in env:
        s = (svxy.reindex(e["dates"]) - rf.reindex(e["dates"])).values
        Xw = np.column_stack([np.ones(63), e["fa"], e["sec"]])
        b, *_ = np.linalg.lstsq(Xw, s, rcond=None)
        svxy_res.append(s - Xw @ b)
    svxy_res = np.concatenate(svxy_res)
    for name in ["vol_core_svxy", "vol_managed_qqq", "trend_vol_qqq"]:
        nd = harness.run(harness.load_spec(
            str(ROOT / "research/hunt2026/specs" / name)), panel)["net_daily"]
        _, resid3, _ = alphas_for(nd, rf, env)
        print(f"rho(L3resid, L3res-SVXY) {name}: "
              f"{np.corrcoef(np.concatenate(resid3), svxy_res)[0, 1]:+.3f}")


if __name__ == "__main__":
    main()
