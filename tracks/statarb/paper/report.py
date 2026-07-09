"""Bracket monitor — reads the ledgers, prints the resolver.

Primary readout (fast, event-driven): the dead-name drag — realized PnL on deep-dip
longs closed via halt/delisted/corporate_action/gap_stop. Even a handful is DIRECT
evidence of the survivorship channel the backtest couldn't see.
Secondary (slow, aggregate): the full/floored/premium Sharpe. `premium = full −
floored` is the low-variance long-side deep-dip stream; its CI needs ~12 months, so
it never gates the primary readout. Reuses core.eval.metrics.sharpe.
"""
import pandas as pd

from core.eval.metrics import sharpe
from tracks.statarb.paper.reconcile import DEAD_NAME_REASONS


def bracket_report(nav_rows: list[dict], position_rows: list[dict],
                   periods_per_year: int = 252) -> dict:
    nav = pd.DataFrame(nav_rows)
    if not nav.empty and "date" in nav:
        # intraday reruns append one nav row per run; last mark per date wins (full-day beats partial)
        nav = nav.drop_duplicates("date", keep="last")
    out: dict = {"n_days": len(nav)}
    if not nav.empty and "net" in nav and "floored_net" in nav:
        net = pd.to_numeric(nav["net"], errors="coerce")
        floored = pd.to_numeric(nav["floored_net"], errors="coerce")
        premium = net - floored
        out["full_sharpe"] = sharpe(net, periods_per_year)
        out["floored_sharpe"] = sharpe(floored, periods_per_year)
        out["premium_sharpe"] = sharpe(premium, periods_per_year)
        out["premium_ann"] = float(premium.mean() * periods_per_year)

    dead = [r for r in position_rows if r.get("close_reason") in DEAD_NAME_REASONS]
    out["dead_name_events"] = len(dead)
    out["dead_name_drag"] = float(sum(r.get("realized_pnl") or 0.0 for r in dead))
    out["dead_name_tickers"] = [r.get("ticker") for r in dead]
    return out


def to_markdown(rep: dict) -> str:
    lines = ["# Paper Book — Residual Reversion (Stage 5)", "",
             f"Days marked: **{rep['n_days']}**", ""]
    if "full_sharpe" in rep:
        lines += [
            "## Bracket (secondary — aggregate, ~12mo to resolve)",
            f"- Full Sharpe: **{rep['full_sharpe']:.2f}**  → benign hypothesis lands ~2.5",
            f"- Floored Sharpe (deep-dip longs removed): **{rep['floored_sharpe']:.2f}**  → ~1.7 core",
            f"- Premium (full − floored) Sharpe: **{rep['premium_sharpe']:.2f}** "
            f"(ann. {rep['premium_ann']:.2%})", ""]
    lines += [
        "## Dead-name drag (primary — event-driven, fast)",
        f"- Terminal dead-name closes: **{rep['dead_name_events']}**",
        f"- Realized drag: **{rep['dead_name_drag']:.4f}**",
    ]
    if rep["dead_name_tickers"]:
        lines.append(f"- Names: {', '.join(str(t) for t in rep['dead_name_tickers'])}")
    return "\n".join(lines) + "\n"
