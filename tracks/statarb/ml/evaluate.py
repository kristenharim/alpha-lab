"""The research payload: does gating trades by predicted-success probability beat taking every signal?

Pre-registration (anti-overfitting): the probability threshold is chosen on the EARLIER 60% of trades
by date and reported on the LATER 40% (held-out). The result is reported whichever way it comes out —
if gating does not improve held-out Sharpe, that is itself a finding (signal quality isn't predictable
from entry features alone). No threshold-hunting on the held-out set.

Two views: per-trade stats (honest, from the log directly) and a reconstructed equal-weight daily
series scored via the house scorecard. The daily reconstruction is internally consistent for the
gated-vs-ungated comparison; its absolute level differs from the audited engine net (documented).
"""
import argparse

import numpy as np
import pandas as pd

from core.eval.scorecard import scorecard
from tracks.statarb.ml.dataset import build_features, load_log
from tracks.statarb.ml.train import walk_forward_oof


def per_trade_stats(pnl: pd.Series) -> dict:
    pnl = pnl.dropna()
    if len(pnl) < 2:
        return {"n": len(pnl), "win": float("nan"), "mean": float("nan"), "sharpe": float("nan")}
    sd = pnl.std(ddof=1)
    return {"n": int(len(pnl)), "win": float((pnl > 0).mean()), "mean": float(pnl.mean()),
            "sharpe": float(pnl.mean() / sd) if sd > 0 else 0.0}


def reconstruct_daily(df: pd.DataFrame) -> pd.Series:
    """Equal-weight daily returns from entered trades: each trade's realized_pnl spread uniformly over
    its holding business days; per day, mean across active trades."""
    df = df[df["entered"] & df["realized_pnl"].notna()].copy()
    if df.empty:
        return pd.Series(dtype=float)
    contribs: dict = {}
    for _, t in df.iterrows():
        days = pd.bdate_range(pd.to_datetime(t["entry_date"]), periods=max(1, int(t["holding_days"])))
        per_day = float(t["realized_pnl"]) / len(days)
        for d in days:
            contribs.setdefault(d, []).append(per_day)
    return pd.Series({d: np.mean(v) for d, v in contribs.items()}).sort_index()


def pick_threshold(sel: pd.DataFrame, grid_lo=0.1, grid_hi=0.8, min_trades=10) -> float:
    """Threshold maximizing per-trade Sharpe on the SELECTION set only (>= min_trades kept)."""
    grid = np.quantile(sel["proba"], np.linspace(grid_lo, grid_hi, 15))
    def score(th):
        kept = sel[sel["proba"] > th]["realized_pnl"]
        s = per_trade_stats(kept)
        return s["sharpe"] if s["n"] >= min_trades and not np.isnan(s["sharpe"]) else -np.inf
    return float(max(grid, key=score))


def evaluate(config: str = "all_on") -> dict:
    df = load_log(config)
    X, y, dates = build_features(df)
    oof = walk_forward_oof(X, y, dates, "xgboost")
    df = df.assign(proba=oof.to_numpy(), entry_dt=dates.to_numpy())
    ev = df[df["proba"].notna() & df["entered"] & df["realized_pnl"].notna()].copy()
    if ev.empty:
        raise RuntimeError("no evaluable trades (need entered trades with OOF predictions)")

    cut = ev["entry_dt"].quantile(0.6)
    sel, hold = ev[ev["entry_dt"] <= cut], ev[ev["entry_dt"] > cut]
    threshold = pick_threshold(sel)
    gated = hold[hold["proba"] > threshold]

    ung_daily = reconstruct_daily(hold)
    gat_daily = reconstruct_daily(gated)
    sc = lambda s: scorecard(s, {}, n_trials=1, periods_per_year=252) if len(s) > 2 else None
    return {
        "config": config, "threshold": round(threshold, 4),
        "n_selection": len(sel), "n_holdout": len(hold),
        "per_trade": {"ungated": per_trade_stats(hold["realized_pnl"]),
                      "gated": per_trade_stats(gated["realized_pnl"])},
        "daily": {"ungated": sc(ung_daily), "gated": sc(gat_daily)},
    }


def as_table(res: dict) -> pd.DataFrame:
    pt = res["per_trade"]
    dl = res["daily"]
    def row(name):
        d = dl[name]
        return {"arm": name, "n_trades": pt[name]["n"], "win%": round(pt[name]["win"] * 100, 1),
                "mean_pnl": round(pt[name]["mean"], 4), "per_trade_sharpe": round(pt[name]["sharpe"], 2),
                "daily_sharpe": round(d["sharpe"], 2) if d else float("nan"),
                "max_dd": round(d["max_drawdown"], 3) if d else float("nan")}
    return pd.DataFrame([row("ungated"), row("gated")])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default="all_on")
    args = ap.parse_args()
    res = evaluate(args.config)
    print(f"pre-registered threshold {res['threshold']} (chosen on {res['n_selection']} earlier "
          f"trades) → reported on {res['n_holdout']} held-out trades:\n")
    print(as_table(res).to_string(index=False))
    print("\nReported as-is: a null or negative gated result is a finding, not a failure.")


if __name__ == "__main__":
    main()
