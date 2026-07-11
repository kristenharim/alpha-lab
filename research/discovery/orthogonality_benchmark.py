"""Experiment 5 — the PERMANENT Orthogonality Benchmark for the Additional Discovery Program.

Every discovery candidate must pass through here BEFORE it can be called independent. It
answers one question with numbers, not opinion: does a candidate daily return series add
information the existing Alpha Lab portfolio does not already own?

Method (reuses the frozen independence harness so the control set is identical to the
7-book reconstruction the runner would P&L):
  control set X = [1, SPY, QQQ, <the 7 live books>]   # trend/vol/leverage/momentum ARE the books
  regress candidate on X  -> residual alpha (ann) + t, residual Sharpe, residual series
  report: max |return corr| to any book, max |residual corr|, crisis contribution
          (worst-decile SPY days), incremental ensemble Sharpe (equal-risk, block-bootstrap)

Gate is reported component-by-component (charter 3C: never one opaque score). The reviewer
assigns the final verdict from the charter vocabulary; this file only supplies evidence.

Run: .venv/bin/python research/discovery/orthogonality_benchmark.py   (runs the self-check)
Import: from orthogonality_benchmark import score_candidate
"""
from __future__ import annotations
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
IND = ROOT / "research" / "independent_alpha" / "independence"
HUNT = ROOT / "research" / "hunt2026"
sys.path.insert(0, str(IND))
from compute_independence import book_returns, factor_returns, BOOKS  # noqa: E402

PROMOTED = ["vol_managed_qqq", "vol_core_svxy", "trend_vol_qqq", "defensive_ensemble"]
INDEP_CORR_MAX = 0.50   # max return corr to any single book to call it independent
INDEP_RESID_MAX = 0.35  # max residual corr after removing SPY+QQQ
ALPHA_T_MIN = 2.0       # residual-alpha t to claim a residual edge
INCR_P_MIN = 0.90       # P(incremental ensemble ΔSharpe > 0) to claim portfolio value


def _load_panel_frames() -> tuple[pd.DataFrame, pd.DataFrame]:
    """The 7 books + SPY/QQQ factor series on the runner's exact P&L convention."""
    panel = pd.read_parquet(HUNT / "panel_2005.parquet")
    books = book_returns(panel)
    factors = factor_returns(panel)
    df = books.join(factors, how="inner").dropna()
    active = (books.reindex(df.index).abs().sum(axis=1) > 0)
    df = df.loc[active[active].index.min():]
    return df[list(BOOKS)], df[["SPY", "QQQ"]]


def _ann_sharpe(r: pd.Series) -> float:
    s = r.std()
    return float(r.mean() / s * np.sqrt(252)) if s > 0 else 0.0


def _block_bootstrap_incr_sharpe(ens: pd.Series, cand: pd.Series, block=21, reps=2000, seed=0):
    """P(ΔSharpe > 0) for adding cand to the equal-risk ensemble, treatment re-scaled to
    control vol each replicate (skill not leverage). Fixed seed -> reproducible."""
    # equal-risk add: weight candidate by inverse-vol vs the ensemble, then rescale to ens vol
    w = ens.std() / cand.std() if cand.std() > 0 else 0.0
    treat = ens + w * cand
    treat = treat * (ens.std() / treat.std()) if treat.std() > 0 else treat
    diff0 = _ann_sharpe(treat) - _ann_sharpe(ens)
    rng = np.random.default_rng(seed)
    n = len(ens)
    nb = int(np.ceil(n / block))
    e, t = ens.values, treat.values
    wins = 0
    for _ in range(reps):
        idx = (rng.integers(0, n - block, nb)[:, None] + np.arange(block)).ravel()[:n]
        if _ann_sharpe(pd.Series(t[idx])) - _ann_sharpe(pd.Series(e[idx])) > 0:
            wins += 1
    return diff0, wins / reps


def score_candidate(candidate: pd.Series, label: str = "candidate") -> dict:
    """Score one daily return series. Returns a dict of evidence + component gate flags."""
    books, factors = _load_panel_frames()
    df = pd.concat([candidate.rename("cand"), books, factors], axis=1, join="inner").dropna()
    if len(df) < 252:
        raise ValueError(f"{label}: only {len(df)} overlapping days — need >=252")
    cand = df["cand"]

    # (1) plain return correlation to each existing book
    corr_to_books = df[list(BOOKS)].apply(lambda c: cand.corr(c))
    max_corr = corr_to_books.abs().max()

    # (2) residual alpha after [1, SPY, QQQ, 7 books]
    Xcols = ["SPY", "QQQ"] + list(BOOKS)
    X = np.column_stack([np.ones(len(df)), df[Xcols].values])
    coef, *_ = np.linalg.lstsq(X, cand.values, rcond=None)
    resid = cand.values - X @ coef
    dof = len(df) - X.shape[1]
    sigma2 = (resid @ resid) / dof
    se_alpha = np.sqrt(sigma2 * np.linalg.inv(X.T @ X)[0, 0])
    alpha_ann = coef[0] * 252
    alpha_t = coef[0] / se_alpha if se_alpha > 0 else 0.0
    resid_s = pd.Series(resid, index=df.index)
    resid_sharpe = _ann_sharpe(resid_s)

    # residual corr to each book's SPY+QQQ residual (shared-info-after-market check)
    fX = np.column_stack([np.ones(len(df)), df[["SPY", "QQQ"]].values])
    def _resid_on_mkt(y):
        c, *_ = np.linalg.lstsq(fX, y, rcond=None)
        return y - fX @ c
    cand_rm = _resid_on_mkt(cand.values)
    max_resid_corr = max(abs(np.corrcoef(cand_rm, _resid_on_mkt(df[b].values))[0, 1]) for b in BOOKS)

    # (3) crisis contribution: mean candidate return on worst-decile SPY days (bps/day)
    crisis = df[df["SPY"] <= df["SPY"].quantile(0.10)]
    crisis_bps = float(crisis["cand"].mean() * 1e4)

    # (4) incremental ensemble value (equal-risk ensemble of the 4 promoted books)
    ens = df[PROMOTED].mean(axis=1)  # equal-weight; each book already vol-shaped
    d_sharpe, p_incr = _block_bootstrap_incr_sharpe(ens, cand)

    flags = {
        "independent_by_corr": bool(max_corr < INDEP_CORR_MAX and max_resid_corr < INDEP_RESID_MAX),
        "has_residual_edge": bool(alpha_t > ALPHA_T_MIN),
        "incremental": bool(p_incr > INCR_P_MIN),
    }
    if not flags["independent_by_corr"]:
        tag = "NOT INDEPENDENT"
    elif flags["has_residual_edge"] and flags["incremental"]:
        tag = "PORTFOLIO CANDIDATE"
    elif flags["has_residual_edge"]:
        tag = "MEASUREMENT SUPPORTED (independent, edge not yet portfolio-incremental)"
    else:
        tag = "INDEPENDENT BUT NO EDGE (diversifier only — judge on crisis/DD contribution)"

    return {
        "label": label, "n_days": len(df),
        "window": f"{df.index[0].date()}..{df.index[-1].date()}",
        "max_corr_to_book": round(float(max_corr), 3),
        "argmax_corr_book": corr_to_books.abs().idxmax(),
        "max_residual_corr": round(float(max_resid_corr), 3),
        "resid_alpha_ann": round(float(alpha_ann), 4),
        "resid_alpha_t": round(float(alpha_t), 2),
        "resid_sharpe": round(float(resid_sharpe), 2),
        "crisis_bps_per_day": round(crisis_bps, 2),
        "incr_ens_dSharpe": round(float(d_sharpe), 3),
        "incr_ens_P_gt0": round(float(p_incr), 3),
        "flags": flags, "suggested_tag": tag,
    }


def _selfcheck():
    """Runnable check: an existing book must FAIL independence; orthogonal noise must read
    independent-with-no-edge; orthogonal noise + real drift must clear the residual-edge gate."""
    books, factors = _load_panel_frames()
    idx = books.join(factors, how="inner").dropna().index

    # 1) an existing book fed as a candidate -> NOT INDEPENDENT (max corr ~1 with itself)
    dup = score_candidate(books["vol_core_svxy"].reindex(idx), "dup:vol_core_svxy")
    assert dup["suggested_tag"] == "NOT INDEPENDENT", dup
    assert dup["max_corr_to_book"] > 0.95, dup

    rng = np.random.default_rng(7)
    # 2) orthogonal zero-mean noise -> independent, but no residual edge
    noise = pd.Series(rng.normal(0, 0.01, len(idx)), index=idx)
    n = score_candidate(noise, "noise")
    assert n["flags"]["independent_by_corr"] and not n["flags"]["has_residual_edge"], n

    # 3) orthogonal noise + steady drift -> independent AND residual edge (t>2)
    edge = pd.Series(rng.normal(0.0006, 0.008, len(idx)), index=idx)
    e = score_candidate(edge, "noise+drift")
    assert e["flags"]["independent_by_corr"] and e["flags"]["has_residual_edge"], e

    print("SELF-CHECK PASSED")
    for r in (dup, n, e):
        print(f"  {r['label']:22s} tag={r['suggested_tag']:30s} "
              f"maxcorr={r['max_corr_to_book']:.2f} residα_t={r['resid_alpha_t']:.1f} "
              f"P(incr>0)={r['incr_ens_P_gt0']:.2f}")


if __name__ == "__main__":
    _selfcheck()
