# Agent 8 runner: execute ORIGINAL specs as black boxes (source never read),
# run clean-room replicas, score both with the independent scorer, and emit
# per-book daily difference CSVs + a summary JSON.
import importlib.util
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).parent
HUNT = Path.home() / "projects/alpha-lab/research/hunt2026"
sys.path.insert(0, str(HERE))
import replica  # noqa: E402

BOOKS = list(replica.BOOKS)


def load_orig(name):
    d = HUNT / "specs" / name
    s = importlib.util.spec_from_file_location(name, d / "spec.py")
    mod = importlib.util.module_from_spec(s)
    s.loader.exec_module(mod)
    return mod


def panel_1y():
    return pd.concat([pd.read_parquet(HUNT / "train.parquet"),
                      pd.read_parquet(HUNT / "holdout.parquet")])


def panel_5y():
    return pd.concat([pd.read_parquet(HUNT / "train5y.parquet"),
                      pd.read_parquet(HUNT / "holdout5y.parquet")])


def align(A, B):
    cols = sorted(set(A.columns) | set(B.columns))
    return (A.reindex(columns=cols).fillna(0.0).astype(float),
            B.reindex(columns=cols).fillna(0.0).astype(float))


def compare(name, panel, start, tag, out):
    orig = load_orig(name).target_weights(panel).astype(float).fillna(0.0)
    rep = replica.BOOKS[name](panel).astype(float).fillna(0.0)
    Wo, Wr = align(orig, rep)
    so = replica.score(Wo, panel, start=start)
    sr = replica.score(Wr, panel, start=start)
    dW = (Wo - Wr).abs()
    idx = dW.index[dW.index > pd.Timestamp(start)]
    dWw = dW.reindex(idx)
    first = dWw[(dWw > 1e-6).any(axis=1)].index.min()
    dnet = (so["net_daily"] - sr["net_daily"]).abs()
    df = pd.DataFrame({
        "net_orig": so["net_daily"], "net_rep": sr["net_daily"],
        "net_absdiff": dnet,
        "maxw_absdiff": dWw.max(axis=1),
        "gross_orig": Wo.reindex(idx).abs().sum(axis=1),
        "gross_rep": Wr.reindex(idx).abs().sum(axis=1),
    })
    df.to_csv(HERE / f"diff_{name}_{tag}.csv")
    row = {
        "book": name, "window": tag,
        "orig_total_net": so["total_net"], "rep_total_net": sr["total_net"],
        "orig_sharpe": so["sharpe"], "rep_sharpe": sr["sharpe"],
        "orig_maxdd": so["max_dd"], "rep_maxdd": sr["max_dd"],
        "orig_gross": so["avg_gross_exposure"], "rep_gross": sr["avg_gross_exposure"],
        "orig_turn": so["avg_daily_turnover"], "rep_turn": sr["avg_daily_turnover"],
        "orig_cost": so["cost_drag_ann"], "rep_cost": sr["cost_drag_ann"],
        "first_weight_diff": str(first) if first is not pd.NaT else None,
        "days_net_diff_gt_1bp": int((dnet > 1e-4).sum()),
        "days_net_diff_gt_10bp": int((dnet > 1e-3).sum()),
        "mean_abs_net_diff_bp": float(dnet.mean() * 1e4),
        "corr_net": float(so["net_daily"].corr(sr["net_daily"])),
    }
    out.append(row)
    print(json.dumps(row, indent=None, default=str))


def main(which=None, tags=("1y", "5y")):
    out = []
    books = [which] if which else BOOKS
    if "1y" in tags:
        p1 = panel_1y()
        for b in books:
            if b in ("trend_vol_qqq", "defensive_ensemble", "dual_momentum_gold") and which is None:
                pass  # round-2 books have no stored 1y json but still comparable
            compare(b, p1, "2025-07-10", "1y", out)
    if "5y" in tags:
        p5 = panel_5y()
        for b in books:
            compare(b, p5, "2021-07-10", "5y", out)
    old = []
    f = HERE / "compare_summary.json"
    if f.exists():
        old = json.loads(f.read_text())
        old = [r for r in old if not any(r["book"] == n["book"] and r["window"] == n["window"] for n in out)]
    f.write_text(json.dumps(old + out, indent=2, default=str))


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else None,
         tuple(sys.argv[2].split(",")) if len(sys.argv) > 2 else ("1y", "5y"))
