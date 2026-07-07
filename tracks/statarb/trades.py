"""Per-signal outcome log: derive discrete trades (with counterfactuals) from the position matrices.

Schema unions with the paper book's positions.jsonl so backward (here) and forward (paper) logs
concatenate into one training set. Per-trade P&L is the contemporaneous reversion captured over the
hold (Sum sign*resid) — a LABEL for "did it revert", distinct from the engine's cost-and-lag net
series (the performance number). success = pnl > 0.
"""
import pandas as pd


def _runs(col: pd.Series):
    """Yield (start_i, end_i, sign) for each contiguous single-sign nonzero run."""
    vals = col.tolist()
    i, n = 0, len(vals)
    while i < n:
        if vals[i] == 0:
            i += 1
            continue
        j = i
        while j + 1 < n and vals[j + 1] == vals[i]:
            j += 1
        yield i, j, (1 if vals[i] > 0 else -1)
        i = j + 1


def _close_reason(base_col: list, i0: int, i1: int) -> str:
    if i1 == len(base_col) - 1:
        return "window_end"
    return "reversion_exit" if base_col[i1 + 1] == 0 else "band_flip"


def extract_trades(base_positions, final_positions, resid, s_scores,
                   features: dict, sectors: dict, removed_by: dict, lag: int = 0) -> list[dict]:
    """`lag` shifts the P&L window to match the engine's execution lag (held = positions.shift(1+skip)):
    a signal-day-[i0,i1] position earns residuals over [i0+lag, i1+lag]. Pass lag=1+skip for
    engine-consistent P&L; lag=0 sums contemporaneously (used only by the mechanics unit test)."""
    idx = base_positions.index
    rows = []
    for c in base_positions.columns:
        base_col = base_positions[c].tolist()
        for i0, i1, sign in _runs(base_positions[c]):
            entered = final_positions[c].iloc[i0] != 0
            pnl = float(sign * resid[c].iloc[i0 + lag:i1 + 1 + lag].sum())
            blocked = [name for name, mask in removed_by.items()
                       if bool(mask[c].iloc[i0:i1 + 1].any())]
            vr = features["volume_ratio"][c].iloc[i0]
            rows.append({
                "signal_id": f"{c}:{idx[i0].date()}:{i0}",
                "ticker": c,
                "entry_date": str(idx[i0].date()),
                "exit_date": str(idx[i1].date()),
                "holding_days": i1 - i0 + 1,
                "entry_s": float(s_scores[c].iloc[i0]),
                "residual": float(resid[c].iloc[i0]),
                "sector": sectors.get(c),
                "volatility": float(features["volatility"][c].iloc[i0]),
                "volume_ratio": None if pd.isna(vr) else float(vr),
                "close_reason": _close_reason(base_col, i0, i1),
                "entered": bool(entered),
                "filters_blocked": blocked,
                "realized_pnl": pnl if entered else None,
                "counterfactual_pnl": None if entered else pnl,
                "success": bool(pnl > 0),
            })
    return rows


def trade_stats(trades: list[dict]) -> dict:
    entered = [t for t in trades if t["entered"]]
    wins = [t for t in entered if t["success"]]
    hold = [t["holding_days"] for t in entered] or [0]
    return {
        "n_signals": len(trades),
        "n_entered": len(entered),
        "win_rate": (len(wins) / len(entered)) if entered else 0.0,
        "avg_holding_days": sum(hold) / len(hold),
    }
