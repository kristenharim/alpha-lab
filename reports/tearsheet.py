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


# minimum live sessions before QuantStats' annualized stats mean anything — below this the
# tearsheet would print a confident Sharpe off ~a week of noise, so we render a placeholder instead.
MIN_LIVE_ROWS = 20


def load_paper_live() -> pd.Series:
    """Daily net returns of the live paper book, from the ledger the nightly cron commits."""
    import json
    p = ROOT / "artifacts/statarb/paper/live/daily_nav.jsonl"
    if not p.exists():
        raise FileNotFoundError(f"no live paper ledger at {p} — run scripts/paper_book_run.py --live first")
    rows = [json.loads(l) for l in p.read_text().splitlines() if l.strip()]
    s = pd.Series({pd.Timestamp(r["date"]): float(r.get("net", 0.0)) for r in rows}).sort_index()
    s.index.name = "date"
    return s.dropna()


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


def _placeholder(out_html: Path, n: int) -> None:
    """Honest stand-in while the live book is too short for annualized stats to mean anything."""
    out_html.write_text(
        f"<!doctype html><meta charset='utf-8'><title>StatArb — live paper book</title>"
        f"<div style='font:15px -apple-system,sans-serif;max-width:600px;margin:3rem auto;"
        f"color:#444;line-height:1.6'><h2 style='font-weight:500'>Live paper tearsheet — accruing</h2>"
        f"<p>The book has <b>{n}</b> trading session(s). A QuantStats tearsheet needs "
        f"<b>{MIN_LIVE_ROWS}</b> before its annualized Sharpe/drawdown stop being noise, so this "
        f"renders as a placeholder until then. The live NAV, day P&amp;L, and positions are on the "
        f"<a href='dashboard.html'>dashboard</a> in the meantime.</p></div>")
    print(f"placeholder written ({n}/{MIN_LIVE_ROWS} sessions) -> {out_html}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--source", choices=["ablation", "live"], default="ablation",
                    help="ablation = backtest net parquet (curated); live = paper-book NAV returns (nightly)")
    ap.add_argument("--config", default="all_on")
    ap.add_argument("--no-benchmark", action="store_true")
    args = ap.parse_args()

    out = ROOT / "reports"
    out.mkdir(exist_ok=True)

    if args.source == "live":
        net = load_paper_live()
        html = out / "statarb_paper_live_tearsheet.html"
        if len(net) < MIN_LIVE_ROWS:
            _placeholder(html, len(net))
            return
        qs.reports.html(net, benchmark=None, output=str(html),
                        title="StatArb residual reversion — live paper book")
        print(f"wrote {html} ({html.stat().st_size:,} bytes)")
        return

    net = load_net(args.config)
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
