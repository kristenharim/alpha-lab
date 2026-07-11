# ---
# jupyter:
#   jupytext:
#     text_representation:
#       extension: .py
#       format_name: percent
#   kernelspec:
#     display_name: Python 3
#     name: python3
# ---

# %% [markdown]
# # StatArb residual reversion — research notebook
#
# A market-neutral statistical-arbitrage strategy (Avellaneda–Lee residual reversion) taken through a
# full research workflow: reproduce, **attack** (survivorship audits), quantify which production layers
# matter (ablation), and ask whether a meta-model can predict *which* signals revert.
#
# **This notebook never re-runs the backtest.** It reads the artifacts the audited engine wrote
# (`artifacts/statarb/…`) — the compute/present seam that keeps the headline number honest.
#
# *Paper trading only. Nothing here places real orders.*

# %% [markdown]
# ## ⚠ Superseded — Stage-4 kill (2026-07-10)
#
# The results in this notebook were computed under the pre-fix engine, which scored P&L in
# **residual space** (`held x residual`). The trailing-alpha term that scoring credits is
# unhedgeable, and the implementable book (stock − lagged-beta x sector ETF) earns ~1.3%/yr gross
# against ~5.3%/yr of costs — net Sharpe **−0.88**, and **−1.06** after the pre-registered
# drift-corrected salvage. **Verdict: dead.** This notebook is kept as the historical record the
# post-mortem dissects: see `memos/diagnostics-2026-07-10.md` and the README.

# %%
from pathlib import Path
import warnings; warnings.simplefilter("ignore")
import numpy as np
import pandas as pd
from IPython.display import Image, display

from core.eval.metrics import sharpe, max_drawdown
from tracks.statarb.ml.dataset import build_features, load_log
from tracks.statarb.ml.train import oof_auc_table
from tracks.statarb.ml import evaluate as ev

ROOT = Path.cwd() if (Path.cwd() / "artifacts").exists() else Path.cwd().parents[0]
ABL = ROOT / "artifacts/statarb/ablation"
CONFIG = "costs"   # the equal-weight S&P 500 book behind the headline result

# %% [markdown]
# ## The headline result — does signal *quality* prediction improve the book?
#
# The single most important question in this notebook, up front: if instead of trading **every**
# residual signal we trade only those a meta-model rates likely to revert, does the book improve —
# **out of sample**? The threshold is pre-registered on earlier trades and reported on held-out later
# trades. Reported whichever way it comes out: a null result is itself a finding.

# %%
res = ev.evaluate(CONFIG)
gated_table = ev.as_table(res)
print(f"Ungated full-period Sharpe {res['ungated_full_sharpe']} (audited-path anchor). "
      f"Pre-registered threshold {res['threshold']}: kept {res['n_kept']} of "
      f"{res['n_holdout_trades']} held-out trades.")
gated_table

# %% [markdown]
# `daily_sharpe` here is a daily Sharpe from the audited engine: sub-threshold signals are zeroed
# out of the positions matrix and run through the same `equal_weight_net` path as the headline
# backtest. The ungated held-out Sharpe anchors the comparison. Caveat: this is one
# pre-registered held-out split, not cross-validated, so read the lift as directional. Per-trade win
# rate and mean P&L are the complementary trade-level view.

# %% [markdown]
# ## Which production layers actually matter — the ablation

# %%
def ablation_table():
    rows = []
    for p in sorted(ABL.glob("*_net.parquet")):
        net = pd.read_parquet(p)["net"].dropna()
        rows.append({"config": p.stem.replace("_net", ""), "n_days": len(net),
                     "sharpe": round(sharpe(net, 252), 2), "max_dd": round(max_drawdown(net), 3)})
    return pd.DataFrame(rows)

ablation_table()

# %% [markdown]
# ## Robustness across regimes
#
# A layer's verdict must survive different environments, not one lucky window. Sharpe by calendar year.

# %%
net = pd.read_parquet(ABL / f"{CONFIG}_net.parquet")["net"].dropna()
by_year = net.groupby(net.index.year).apply(lambda s: sharpe(s, 252)).round(2)
by_year.rename("sharpe").to_frame()

# %% [markdown]
# ## QuantStats tearsheet
#
# The field-standard performance report — cumulative returns, drawdown, rolling Sharpe, monthly heatmap.
# Generated to `reports/` and linked here (kept out-of-line so the notebook stays light).

# %%
import quantstats as qs
try:
    m = qs.reports.metrics(net, mode="basic", display=False)
    display(m)
except Exception as e:
    print(f"metrics table skipped ({type(e).__name__})")
print(f"Full tearsheet: reports/statarb_tearsheet_{CONFIG}.html")

# %% [markdown]
# **Honest note.** QuantStats' Sharpe assumes a risk-free rate and its own periodization; the house
# scorecard uses rf=0, ddof=1. The two won't exactly match — a convention difference, not a bug. The
# custom deflated-Sharpe (Bailey–López de Prado) remains the multiple-testing guard QuantStats omits.

# %% [markdown]
# ## The meta-model — walk-forward, leakage-safe
#
# Features are **entry-time only** (an exit-time feature like `holding_days` would leak the label).
# Expanding-window monthly training; out-of-fold AUC below.

# %%
X, y, dates = build_features(load_log(CONFIG))
print(f"{len(X)} signals · {y.mean():.1%} reverted · {X.shape[1]} entry-time features")
oof_auc_table(X, y, dates)

# %% [markdown]
# ### SHAP — what drives the meta-model

# %%
png = ROOT / "reports" / f"shap_beeswarm_{CONFIG}.png"
display(Image(filename=str(png))) if png.exists() else print("run tracks.statarb.ml.explain first")

# %% [markdown]
# ## Limitations (stated, not buried)
#
# - **Survivorship.** The backward log is survivor-biased on deep-dip longs; the meta-model here is a
#   *prototype*. Its clean training set is the forward paper book (survivorship-immune by construction).
# - **Reconstruction.** The gated-vs-ungated `daily_sharpe` is from a sparse trade→daily reconstruction;
#   per-trade win rate / mean P&L are the trustworthy comparison.
# - **Costs & capacity.** Residual reversion is turnover-heavy and cost-sensitive; the ablation charges
#   costs explicitly, but real fills, borrow, and impact are not modeled here.
#
# ## Conclusion
#
# The strategy is real and its limits are named. The differentiator isn't the Sharpe — it's the
# discipline: survivorship audits, an ablation that says which layers earn their keep, and a
# leakage-safe meta-model reported whichever way it comes out.
