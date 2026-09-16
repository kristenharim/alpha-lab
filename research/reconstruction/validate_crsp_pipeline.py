"""Stage 2 pipeline validation: rebuild two published series from raw CRSP and compare.

Not a hypothesis and not a claim of alpha. If a value-weighted CRSP market and a momentum decile
spread built here do not track Ken French's MKT and UMD, every result built on this panel is suspect.
Run: .venv/bin/python research/reconstruction/validate_crsp_pipeline.py
"""
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from core.data.crsp import decile_long_short, fetch_crsp_monthly, momentum_signal, value_weighted_market  # noqa: E402
from core.data.registry import register  # noqa: E402

PANEL = ROOT / "data" / "crsp" / "crsp_monthly_1963_2024.parquet"
OUT = ROOT / "research" / "reconstruction" / "crsp_validation.md"


def main():
    import wrds
    db = wrds.Connection(wrds_username="kris10harim")
    if PANEL.exists():
        panel = pd.read_parquet(PANEL)
    else:
        panel = fetch_crsp_monthly(db)
        PANEL.parent.mkdir(parents=True, exist_ok=True)
        panel.to_parquet(PANEL)
        register(ROOT / "data" / "manifest.jsonl", "crsp_monthly_1963_2024", "WRDS crsp.msf+msenames+msedelist",
                 {"shrcd": [10, 11], "exchcd": [1, 2, 3], "delisting": "Shumway -30% for 5xx"},
                 str(PANEL.relative_to(ROOT)), len(panel))
    ff = db.raw_sql("select date, mktrf, rf, umd from ff.factors_monthly where date >= '1963-01-01'",
                    date_cols=["date"])
    db.close()
    ff["ym"] = ff["date"].dt.to_period("M")
    ff = ff.set_index("ym")

    mkt = value_weighted_market(panel)
    mom = decile_long_short(momentum_signal(panel), "mom")
    # the same momentum spread with delisting losses ignored: the size of the survivorship bias
    # every pre-CRSP stock result in this repo carried
    nodl = panel[panel["ret"].notna()].assign(ret_adj=lambda x: x["ret"])
    mom_nodl = decile_long_short(momentum_signal(nodl), "mom")
    mine = pd.DataFrame({"mkt": mkt, "mom": mom, "mom_nodl": mom_nodl})
    mine.index = pd.to_datetime(mine.index).to_period("M")
    j = mine.join(ff, how="inner").dropna()
    j["mkt_ex"] = j["mkt"] - j["rf"]

    def row(a, b, label):
        x = j[[a, b]].dropna()
        return (f"| {label} | {x.index[0]}–{x.index[-1]} | {len(x)} | {x[a].corr(x[b]):.3f} | "
                f"{x[a].mean()*1200:.2f} | {x[b].mean()*1200:.2f} | {(x[a]-x[b]).std()*100:.2f} |")
    n_perm = panel["permno"].nunique()
    n_dead = panel.loc[panel["dlret"].notna(), "permno"].nunique()   # securities whose death is booked
    lines = [
        "# CRSP pipeline validation",
        "",
        "**Question:** does a panel built from raw CRSP reproduce two published return series closely enough to trust results built on it?",
        "",
        "**Method, step by step.** (1) Every monthly CRSP record for common shares (share code 10/11) on NYSE, AMEX and Nasdaq, 1963–2024. "
        "(2) Delisting returns folded into the delisting month; a performance delisting with no recorded return is booked at −30% (Shumway 1997). "
        "(3) Market equity = |price| × shares outstanding; each month's weights use the *previous* month's market equity. "
        "(4) Market: value-weighted average return of all stocks, minus the T-bill rate. "
        "(5) Momentum: return from 12 months ago to 2 months ago (skipping last month); each month, stocks above the 90th and below the 10th percentile of NYSE stocks; value-weighted top minus bottom. "
        "(6) Compare with Ken French's MKT−RF and UMD from WRDS. French's UMD uses a 2×3 size/momentum sort, so a correlation near but below 1 is expected for the decile spread; the market series should match almost exactly.",
        "",
        f"Panel: {len(panel):,} stock-months, {n_perm:,} distinct securities, {n_dead:,} of which carry a delisting return.",
        "",
        "| Series (mine vs French) | Months | n | Correlation | My mean, %/yr | French mean, %/yr | Tracking error, %/month |",
        "|:--|:--|--:|--:|--:|--:|--:|",
        row("mkt_ex", "mktrf", "Market excess return vs MKT−RF"),
        row("mom", "umd", "Momentum decile spread vs UMD"),
        row("mom_nodl", "umd", "Same spread, delisting returns ignored, vs UMD"),
        "",
        "One row = one series compared month by month over the full overlap.",
    ]
    OUT.write_text("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
