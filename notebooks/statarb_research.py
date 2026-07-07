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
CONFIG = "all_on"

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
print(f"Pre-registered threshold {res['threshold']} — chosen on {res['n_selection']} earlier trades, "
      f"reported on {res['n_holdout']} held-out trades")
gated_table

# %% [markdown]
# Per-trade win rate and mean P&L are the honest trade-level view (the per-signal log gives genuine
# discrete-trade stats, unlike period-based Sharpe). The reconstructed `daily_sharpe` is indicative
# only — sparse-trade reconstruction inflates it; trust the per-trade columns.

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
