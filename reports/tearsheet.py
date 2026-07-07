"""Render a QuantStats HTML tearsheet from an ablation config's net-returns parquet.

Runs in .venv-report. The backtest is NEVER re-run here — this only reads the parquet the audited
.venv wrote (the compute/present seam). QuantStats is the field-standard tearsheet; we feed it our
own daily net series and nothing else.

Usage: .venv-report/bin/python reports/tearsheet.py [--config all_on] [--no-benchmark]
"""
import argparse
from pathlib import Path

import pandas as pd
import quantstats as qs

from core.eval.metrics import sharpe as house_sharpe

ROOT = Path(__file__).resolve().parents[1]


def load_net(config: str) -> pd.Series:
    p = ROOT / "artifacts/statarb/ablation" / f"{config}_net.parquet"
    if not p.exists():
        raise FileNotFoundError(
            f"no net parquet for config '{config}' at {p} — run scripts/statarb_ablation_run.py first")
    return pd.read_parquet(p)["net"].dropna()


def spy_benchmark(index) -> pd.Series | None:
    """Download SPY ourselves and pass a returns Series, rather than trusting QuantStats' internal
    downloader (which has been brittle across yfinance/pandas versions)."""
    try:
        from core.data.prices import daily_returns, fetch_prices_yf
        spy = fetch_prices_yf(["SPY"], str(index[0].date()), str(index[-1].date()))
        return daily_returns(spy)["SPY"].reindex(index).dropna()
    except Exception as e:  # network / vendor hiccup must not kill the deliverable
        print(f"  benchmark skipped ({type(e).__name__}: {e})")
        return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default="all_on")
    ap.add_argument("--no-benchmark", action="store_true")
    args = ap.parse_args()

    net = load_net(args.config)
    out = ROOT / "reports"
    out.mkdir(exist_ok=True)
    bench = None if args.no_benchmark else spy_benchmark(net.index)

    html = out / f"statarb_tearsheet_{args.config}.html"
    qs.reports.html(net, benchmark=bench, output=str(html),
                    title=f"StatArb residual reversion — {args.config}")

    # Honest note (baked into the report per spec): QuantStats Sharpe assumes a rf + its own
    # periodization; the house scorecard Sharpe is rf=0, ddof=1. Show both, state why they differ.
    _s = qs.stats.sharpe(net)
    qs_sh = float(_s.iloc[0] if hasattr(_s, "iloc") else _s)
    ho_sh = house_sharpe(net, 252)
    note = (f"Sharpe — QuantStats {qs_sh:.2f} (assumes risk-free rate + its own periodization) vs "
            f"house scorecard {ho_sh:.2f} (rf=0, ddof=1). The gap is a convention difference, not a "
            f"bug; the custom deflated_sharpe (Bailey-Lopez de Prado) remains the multiple-testing "
            f"guard QuantStats does not provide.")
    (out / f"statarb_tearsheet_{args.config}.note.txt").write_text(note + "\n")
    print(f"wrote {html} ({html.stat().st_size:,} bytes)")
    print(note)


if __name__ == "__main__":
    main()
