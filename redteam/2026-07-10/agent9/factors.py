"""Agent 9 pass 2: multi-factor attribution, fair vol_core control, dynamic beta, tails."""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
H26 = ROOT / "research" / "hunt2026"
OUT = Path(__file__).parent
sys.path.insert(0, str(H26))
import harness  # noqa: E402

BOOKS = ["vol_managed_qqq", "vol_core_svxy", "trend_vol_qqq", "defensive_ensemble",
         "dual_momentum_gold", "dual_momentum_gem", "momentum_concentrated"]


def multifactor(y, F):
    """OLS y on factors F (DataFrame). Returns betas, ann alpha, R2, ann contribution."""
    df = pd.concat([y.rename("y"), F], axis=1).dropna()
    X = np.column_stack([np.ones(len(df)), df[F.columns].values])
    b, *_ = np.linalg.lstsq(X, df["y"].values, rcond=None)
    yhat = X @ b
    r2 = 1 - ((df["y"] - yhat) ** 2).sum() / ((df["y"] - df["y"].mean()) ** 2).sum()
    out = {"alpha_ann": b[0] * 252, "r2": r2}
    for i, f in enumerate(F.columns):
        out[f"b_{f}"] = b[i + 1]
        out[f"contrib_{f}_ann"] = b[i + 1] * df[f].mean() * 252
    return out


def main():
    for label in ["holdout", "long"]:
        rets = pd.read_csv(OUT / f"net_daily_{label}.csv", index_col=0, parse_dates=True)
        panel = harness.load_full() if label == "holdout" else \
            pd.read_parquet(H26 / "panel_2005.parquet")
        close = panel["close"]
        ar = close.pct_change(fill_method=None).reindex(rets.index)
        F = pd.DataFrame({"SPY": ar["SPY"],
                          "TECH": ar["QQQ"] - ar["SPY"],
                          "DUR": ar["TLT"],
                          "GOLD": ar["GLD"]})
        rows = []
        for b in BOOKS + ["PORT"]:
            y = rets[BOOKS].mean(axis=1) if b == "PORT" else rets[b]
            r = multifactor(y, F)
            r["book"] = b
            r["total_ann"] = y.mean() * 252
            rows.append(r)
        df = pd.DataFrame(rows).set_index("book")
        cols = ["total_ann", "alpha_ann", "r2",
                "b_SPY", "contrib_SPY_ann", "b_TECH", "contrib_TECH_ann",
                "b_DUR", "contrib_DUR_ann", "b_GOLD", "contrib_GOLD_ann"]
        df = df[cols]
        df.to_csv(OUT / f"factor_attrib_{label}.csv")
        print(f"\n===== factor attribution {label} =====")
        print(df.round(3).to_string())

        # rolling 63d beta of portfolio vs SPY
        port = rets[BOOKS].mean(axis=1)
        cov = port.rolling(63).cov(F["SPY"])
        var = F["SPY"].rolling(63).var()
        rb = (cov / var).dropna()
        print(f"rolling 63d PORT beta {label}: min {rb.min():.2f} "
              f"p25 {rb.quantile(.25):.2f} med {rb.median():.2f} "
              f"p75 {rb.quantile(.75):.2f} max {rb.max():.2f}")

        # tail table
        t = pd.read_csv(OUT / f"tail_{label}.csv", index_col=0)
        print(f"--- mean daily ret on worst-decile SPY days ({label}) ---")
        print((t["mean_on_worst10pct_spy_days"] * 100).round(3).to_string())

    # fair control for vol_core_svxy: exposure-matched 60/40 QQQ/SPY blend
    for label, panel, start in [("holdout", harness.load_full(), harness.META["cut"]),
                                ("long", pd.read_parquet(H26 / "panel_2005.parquet"), "2008-01-01")]:
        book = harness.run(harness.load_spec(H26 / "specs" / "vol_core_svxy"), panel, start=start)
        exp = book["avg_gross_exposure"]

        class _Blend:
            @staticmethod
            def target_weights(p):
                c = p["close"]
                W = pd.DataFrame(0.0, index=c.index, columns=c.columns)
                W["QQQ"] = 0.6 * exp
                W["SPY"] = 0.4 * exp
                return W
        ctrl = harness.run(_Blend, panel, start=start)
        bn, cn = book["net_daily"], ctrl["net_daily"]
        yrs = len(bn) / 252
        f = lambda r: ((1 + r).cumprod().iloc[-1]) ** (1 / yrs) - 1
        print(f"\nvol_core_svxy vs exposure-matched 60/40 QQQ/SPY blend ({label}, exp {exp:.2f}):")
        print(f"  book ann {f(bn):+.2%} sharpe {book['sharpe']:.2f} dd {book['max_dd']:+.1%}")
        print(f"  ctrl ann {f(cn):+.2%} sharpe {ctrl['sharpe']:.2f} dd {ctrl['max_dd']:+.1%}")


if __name__ == "__main__":
    main()
