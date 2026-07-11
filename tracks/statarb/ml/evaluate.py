"""The research payload: does gating trades by predicted-success probability beat taking every signal?

The gated book's Sharpe is a daily Sharpe from the audited engine: positions of sub-threshold
signals are zeroed out and run through the same `equal_weight_net` path as the headline backtest,
not a reconstruction, so the gated-vs-ungated comparison uses identical machinery.

Pre-registration (anti-overfitting): the probability threshold is a fixed rule (top 30% of predicted
probability) fit on the EARLIER 60% of trades by date, then applied to the LATER 40% (held-out). The
result is reported whichever way it comes out — a null gated result is a finding, not a failure.

Runs on the `costs` config (the equal-weight S&P 500 book behind the headline result).
"""
import argparse
from pathlib import Path

import numpy as np
import pandas as pd

from core.eval.scorecard import scorecard
from tracks.statarb.pnl import equal_weight_net
from tracks.statarb.ml.dataset import build_features, load_log
from tracks.statarb.ml.train import walk_forward_oof
from tracks.statarb.trades import _runs

ROOT = Path(__file__).resolve().parents[3]
ABL = ROOT / "artifacts/statarb/ablation"
KEEP_QUANTILE = 0.70          # pre-registered rule: keep signals above the 70th pct of selection proba


def per_trade_stats(pnl: pd.Series) -> dict:
    pnl = pnl.dropna()
    if len(pnl) < 2:
        return {"n": len(pnl), "win": float("nan"), "mean": float("nan"), "sharpe": float("nan")}
    sd = pnl.std(ddof=1)
    return {"n": int(len(pnl)), "win": float((pnl > 0).mean()), "mean": float(pnl.mean()),
            "sharpe": float(pnl.mean() / sd) if sd > 0 else 0.0}


def evaluate(config: str = "costs", skip: int = 1, cost_bps: float = 10.0) -> dict:
    positions = pd.read_parquet(ABL / f"{config}_positions.parquet")
    hedged = pd.read_parquet(ABL / "hedged.parquet")   # implementable P&L space (engine fix 2026-07-10)
    idx = positions.index

    df = load_log(config)
    X, y, dates = build_features(df)
    oof = walk_forward_oof(X, y, dates, "xgboost")
    df = df.assign(proba=oof.to_numpy(), entry_dt=dates.to_numpy())
    proba_by_id = dict(zip(df["signal_id"], df["proba"]))

    # pre-register threshold on the earlier 60% of PREDICTED trades; apply to the later 40% (held-out)
    pred = df[df["proba"].notna()]
    cut = pred["entry_dt"].quantile(0.6)
    sel = pred[pred["entry_dt"] <= cut]
    threshold = float(np.nanquantile(sel["proba"], KEEP_QUANTILE))

    # gate: zero the position run of any signal whose proba is below threshold (keep NaN/unpredicted)
    gated = positions.copy()
    col_loc = {c: gated.columns.get_loc(c) for c in gated.columns}
    for c in positions.columns:
        for i0, i1, _sign in _runs(positions[c]):
            p = proba_by_id.get(f"{c}:{idx[i0].date()}:{i0}", np.nan)
            if not np.isnan(p) and p < threshold:
                gated.iloc[i0:i1 + 1, col_loc[c]] = 0

    # REAL daily net from the audited path; report the held-out window (dates after the cut).
    # Coerce to float: equal_weight_net's internal pd.NA yields object dtype under pandas 3.0 (this
    # venv), which scipy's skew/kurtosis rejects. The audited .venv (pandas 2.2) is unaffected, so the
    # parity-proven formula stays untouched — we just clean its output at this boundary.
    net_ung = equal_weight_net(positions, hedged, skip, cost_bps).astype(float)
    net_gat = equal_weight_net(gated, hedged, skip, cost_bps).astype(float)
    oos = lambda s: s[s.index > cut]
    sc = lambda s: scorecard(s, {}, n_trials=1, periods_per_year=252) if len(s) > 2 else None

    hold = df[df["proba"].notna() & (df["entry_dt"] > cut) & df["entered"]]
    kept = hold[hold["proba"] >= threshold]
    return {
        "config": config, "threshold": round(threshold, 4),
        "ungated_full_sharpe": round(float(scorecard(net_ung, {}, 1, 252)["sharpe"]), 2),  # full-period anchor
        "n_holdout_trades": len(hold), "n_kept": len(kept),
        "per_trade": {"ungated": per_trade_stats(hold["realized_pnl"]),
                      "gated": per_trade_stats(kept["realized_pnl"])},
        "daily": {"ungated": sc(oos(net_ung)), "gated": sc(oos(net_gat))},
    }


def as_table(res: dict) -> pd.DataFrame:
    pt, dl = res["per_trade"], res["daily"]
    def row(name):
        d = dl[name]
        return {"arm": name, "n_trades": pt[name]["n"], "win%": round(pt[name]["win"] * 100, 1),
                "mean_pnl": round(pt[name]["mean"], 4), "per_trade_sharpe": round(pt[name]["sharpe"], 2),
                "daily_sharpe": round(d["sharpe"], 2) if d else float("nan"),
                "max_dd": round(d["max_drawdown"], 3) if d else float("nan")}
    return pd.DataFrame([row("ungated"), row("gated")])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default="costs")
    args = ap.parse_args()
    res = evaluate(args.config)
    print(f"ungated full-period Sharpe {res['ungated_full_sharpe']} (audited-path anchor)")
    print(f"pre-registered threshold {res['threshold']} → held-out: {res['n_kept']}/"
          f"{res['n_holdout_trades']} trades kept\n")
    print(as_table(res).to_string(index=False))
    print("\ndaily_sharpe comes from the audited engine (gated positions, same P&L path). "
          "Reported as-is: a null gated result is a finding.")


if __name__ == "__main__":
    main()
