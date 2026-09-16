"""EXP-2026-09-16-volfamily-crsp: frozen vol_managed_qqq and trend_vol_qqq on the CRSP S&P 500 daily
index, 1928-2024. Pre-registration: research/reconstruction/preregistrations/volfamily-crsp-2026-09-16.md.

Run: .venv/bin/python research/reconstruction/volfamily_crsp.py
"""
import json
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "research" / "hunt2026"))
import harness  # noqa: E402
from core.data.registry import register  # noqa: E402
from mc_crsp import ann, nw_alpha  # noqa: E402

CACHE = ROOT / "data" / "crsp" / "sp500_index_rf_1926_2024.parquet"
WINDOWS = {"A 1928-2004": ("1928-01-01", "2004-12-31"), "B 2005-2024": ("2005-01-01", "2024-12-31")}
SPECS = ["vol_managed_qqq", "trend_vol_qqq"]


def load():
    if CACHE.exists():
        return pd.read_parquet(CACHE)
    import wrds
    db = wrds.Connection(wrds_username="kris10harim")
    idx = db.raw_sql("select caldt as date, vwretd from crsp.dsp500 where caldt <= '2024-12-31'",
                     date_cols=["date"]).set_index("date")
    rf = db.raw_sql("select date, rf from ff.factors_daily where date <= '2024-12-31'",
                    date_cols=["date"]).set_index("date")
    db.close()
    df = idx.join(rf, how="inner").dropna()
    CACHE.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(CACHE)
    register(ROOT / "data" / "manifest.jsonl", "crsp_sp500_index_rf_daily", "WRDS crsp.dsp500 + ff.factors_daily",
             {}, str(CACHE.relative_to(ROOT)), len(df))
    return df


def main():
    df = load()
    close = pd.DataFrame({"QQQ": (1 + df["vwretd"]).cumprod(), "BIL": (1 + df["rf"]).cumprod()})
    panel = pd.concat({"close": close}, axis=1)
    rf = df["rf"]
    rows = []
    for name in SPECS:
        spec = harness.load_spec(ROOT / "research" / "hunt2026" / "specs" / name)
        W = spec.target_weights(panel).astype(float).fillna(0.0)
        for label, (s, e) in WINDOWS.items():
            res = harness.run(spec, panel, s, e)
            r_idx = res["net_daily"].index
            # BIL weight already earns the bill rate through its price; only uninvested cash and
            # leverage need the rf adjustment, so gross here counts the index leg only
            eq_gross = W["QQQ"].abs().shift(1).reindex(r_idx).fillna(0)
            bil = W["BIL"].abs().shift(1).reindex(r_idx).fillna(0) if "BIL" in W else 0
            r = res["net_daily"] + rf.reindex(r_idx) * (1 - eq_gross - bil)
            g = eq_gross.mean()
            ir = df["vwretd"].reindex(r_idx)
            base = g * ir + rf.reindex(r_idx) * (1 - g)
            a_s, b_s = ann(r), ann(base)
            m = lambda x: ((1 + x).resample("ME").prod() - 1)
            mex = m(r) - m(rf.reindex(r_idx))
            mkt = (m(ir) - m(rf.reindex(r_idx))).rename("mkt")
            alpha, t, loads, n = nw_alpha(mex, mkt.to_frame())
            rows.append({"spec": name, "window": label, "cagr": a_s["cagr"], "vol": a_s["vol"],
                         "sharpe": a_s["sharpe"], "maxdd": a_s["maxdd"], "avg_index_gross": g,
                         "base_cagr": b_s["cagr"], "base_sharpe": b_s["sharpe"], "base_maxdd": b_s["maxdd"],
                         "capm_alpha": alpha, "alpha_t": t, "beta": float(loads["mkt"]), "months": n,
                         "cost_drag": res["cost_drag_ann"]})
            print({k: (round(v, 3) if isinstance(v, float) else v) for k, v in rows[-1].items()})
    out = ROOT / "research" / "reconstruction" / "volfamily_crsp_results.json"
    out.write_text(json.dumps(rows, indent=2, default=float))


if __name__ == "__main__":
    main()
