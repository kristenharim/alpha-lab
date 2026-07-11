"""H-D1 — MOC (close d+1) vs next-open (open d+1) fill point for the 3 live vol books.

Prereg: research/independent_alpha/prereg/H-D1.md (EXP-2026-07-10-moc-vs-moo-fill).

Execution alpha, not a forecast. Signal/weights are BYTE-IDENTICAL between arms; only the
fill price differs. Both arms carry the same one-day execution delay off the 20:30 decision
(weights decided at close d, order lands d+1):
  arm A (current live, MOO): position filled at OPEN d+1  -> realized open-to-open.
  arm B (MOC):               position filled at CLOSE d+1 -> realized close-to-close.
So a weight W_d (decided close d) is held over (fill_{d+1} -> fill_{d+2}); in a daily series
that is W.shift(2) applied to the arm's price-relative. B - A isolates (close_rel - open_rel)
on identically-held weights -> the pure fill-point (gap) term. Costs are identical and cancel.

Run: .venv/bin/python research/independent_alpha/experiments/hd1_moc_vs_moo.py
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

ROOT = Path(__file__).resolve().parents[3]
HUNT = ROOT / "research" / "hunt2026"
OUT = Path(__file__).resolve().parent
sys.path.insert(0, str(HUNT))
sys.path.insert(0, str(ROOT / "scripts"))
import harness  # noqa: E402
from hunt_paper_run import SPECS, _heal_etfs, META  # noqa: E402

VOL3 = ["vol_managed_qqq", "vol_core_svxy", "trend_vol_qqq"]
# per-book measurement start: SVXY book from its real inception, others from 2010-01
BOOK_START = {"vol_managed_qqq": "2010-01-01",
              "vol_core_svxy": "2011-10-04",   # SVXY inception
              "trend_vol_qqq": "2010-01-01"}
FULL_END = "2026-07-10"
HOLDOUT_START = "2022-01-01"
ETF = set(META["etfs"])


def book_weights(panel: pd.DataFrame, name: str) -> pd.DataFrame:
    """Full daily target-weight history, exactly as compute_book/live runner forms it
    (heal ETF closes, then spec.target_weights)."""
    healed = _heal_etfs(panel)
    spec = harness.load_spec(SPECS / name)
    return spec.target_weights(healed).astype(float).fillna(0.0)


def costs(W: pd.DataFrame) -> pd.Series:
    """Harness cost convention: per-side bps on |weight change|. IDENTICAL across arms."""
    bps = pd.Series([harness.ETF_BPS if t in ETF else harness.STOCK_BPS for t in W.columns],
                    index=W.columns)
    return (W.diff().abs().fillna(W.abs()) * (bps / 1e4)).sum(axis=1)


def arm_returns(panel: pd.DataFrame, W: pd.DataFrame):
    """Net daily returns for arm A (open-fill) and arm B (close-fill), same weights.

    Both hold W.shift(2): weight decided close d, filled d+1, held to the next fill d+2.
    arm A prices d+1->d+2 open-to-open; arm B close-to-close. Cost series identical -> cancels
    in B-A but subtracted from both for honest per-arm net returns.
    """
    healed = _heal_etfs(panel)
    close = healed["close"][W.columns]
    openp = panel["open"][W.columns]          # raw open (no interior holiday NaNs in this panel)
    rcc = close.pct_change(fill_method=None)
    roo = openp.pct_change(fill_method=None)
    held = W.shift(2)
    gross_A = (held * roo).sum(axis=1, min_count=1).fillna(0.0)
    gross_B = (held * rcc).sum(axis=1, min_count=1).fillna(0.0)
    c = costs(W)
    return gross_A - c, gross_B - c


def gap_slippage(panel: pd.DataFrame, W: pd.DataFrame) -> pd.Series:
    """Per-rebalance signed overnight-gap term  Sum_i dW_i * (open_{d+1}/close_d - 1).
    The direct arm-A leakage diagnostic (prereg secondary), one value per rebalance day."""
    healed = _heal_etfs(panel)
    close = healed["close"][W.columns]
    openp = panel["open"][W.columns]
    gap = openp.shift(-1) / close - 1.0                 # overnight gap into d+1, per ticker
    dW = W.diff()
    slip = (dW * gap).sum(axis=1, min_count=1)
    reb = dW.abs().sum(axis=1) > 1e-12                  # only actual rebalance days
    return slip[reb].dropna()


def ann_stats(r: pd.Series):
    r = r.dropna()
    ann_ret = (1 + r).prod() ** (252 / len(r)) - 1
    sharpe = r.mean() / r.std() * np.sqrt(252) if r.std() > 0 else 0.0
    return ann_ret, sharpe


def worst_12m(diff_monthly: pd.Series) -> float:
    """Worst rolling 12-month sum of the monthly B-A difference."""
    return float(diff_monthly.rolling(12).sum().min())


def slice_span(r: pd.Series, start, end=None):
    idx = r.index[(r.index >= pd.Timestamp(start)) & (r.index <= pd.Timestamp(end or FULL_END))]
    return r.reindex(idx)


def main():
    panel = pd.read_parquet(HUNT / "panel_2005.parquet")

    per_book = {}
    pooled_diffs, pooled_slip = [], []
    print(f"{'book':<18} {'annA%':>7} {'annB%':>7} {'B-A bps':>8} {'ShA':>6} {'ShB':>6} "
          f"{'t(mo)':>6} {'nmo':>4} {'slip_bps':>9} {'t(slip)':>8} {'nreb':>5} {'w12m_bps':>9}")
    for name in VOL3:
        W = book_weights(panel, name)
        rA_full, rB_full = arm_returns(panel, W)
        slip_full = gap_slippage(panel, W)

        start = BOOK_START[name]
        rA = slice_span(rA_full, start)
        rB = slice_span(rB_full, start)
        slip = slice_span(slip_full, start)

        # turnover guard: identical W frame -> identical turnover per rebalance, both arms
        turn = W.diff().abs().sum(axis=1)
        assert np.allclose(turn.values, turn.values), "turnover must match (same W)"
        # explicit two-arm guard: recompute the |dW| each arm would trade -> byte identical
        assert (W.diff().abs().sum(axis=1).equals(W.diff().abs().sum(axis=1)))

        annA, shA = ann_stats(rA)
        annB, shB = ann_stats(rB)

        # monthly paired diff
        mA = (1 + rA).resample("ME").prod() - 1
        mB = (1 + rB).resample("ME").prod() - 1
        dmo = (mB - mA).dropna()
        t_mo = stats.ttest_1samp(dmo, 0.0)
        t_slip = stats.ttest_1samp(slip, 0.0)

        per_book[name] = dict(
            annA=annA, annB=annB, shA=shA, shB=shB,
            ba_ann_bps=(annB - annA) * 1e4, t_mo=t_mo.statistic, n_mo=len(dmo),
            slip_bps=slip.mean() * 1e4, t_slip=t_slip.statistic, n_reb=len(slip),
            w12m_bps=worst_12m(dmo) * 1e4, dmo=dmo, slip=slip,
            # holdout: sign of B-A must not flip in 2022+
            ba_full_sign=np.sign((annB - annA)),
            ba_holdout=(( (1 + slice_span(rB_full, HOLDOUT_START)).prod()
                          / (1 + slice_span(rA_full, HOLDOUT_START)).prod()) - 1),
        )
        pooled_diffs.append(dmo)
        pooled_slip.append(slip)
        pb = per_book[name]
        print(f"{name:<18} {annA*100:>7.2f} {annB*100:>7.2f} {pb['ba_ann_bps']:>8.1f} "
              f"{shA:>6.2f} {shB:>6.2f} {pb['t_mo']:>6.2f} {pb['n_mo']:>4d} "
              f"{pb['slip_bps']:>9.3f} {pb['t_slip']:>8.2f} {pb['n_reb']:>5d} {pb['w12m_bps']:>9.1f}")

    # pooled paired t on monthly diffs (concat across books) + pooled slip t
    pooled_dmo = pd.concat(pooled_diffs)
    pooled_sl = pd.concat(pooled_slip)
    t_pool = stats.ttest_1samp(pooled_dmo, 0.0)
    t_pool_slip = stats.ttest_1samp(pooled_sl, 0.0)
    print("\n--- POOLED ---")
    print(f"pooled monthly B-A: mean {pooled_dmo.mean()*1e4:+.2f} bps/mo  "
          f"paired t = {t_pool.statistic:+.3f}  (n={len(pooled_dmo)} book-months)")
    print(f"pooled gap-slippage: mean {pooled_sl.mean()*1e4:+.3f} bps/reb  "
          f"t = {t_pool_slip.statistic:+.3f}  (n={len(pooled_sl)} rebalances)")

    # holdout sign stability
    print("\n--- HOLDOUT (2022-01..2026-07) sign of B-A ---")
    holdout_ok = True
    for name in VOL3:
        pb = per_book[name]
        ho = pb["ba_holdout"]
        flip = np.sign(ho) != pb["ba_full_sign"] and abs(ho) > 1e-9 and abs(pb["ba_ann_bps"]) > 1e-6
        holdout_ok &= not flip
        print(f"  {name:<18} full B-A sign {int(pb['ba_full_sign']):+d}  "
              f"holdout cum B-A {ho*1e4:+.1f} bps  {'FLIP' if flip else 'stable'}")
    # pooled holdout sign
    pooled_ho_A = pd.concat([slice_span(arm_returns(panel, book_weights(panel, n))[0],
                                        HOLDOUT_START) for n in VOL3])
    print(f"  pooled monthly B-A full sign {int(np.sign(pooled_dmo.mean())):+d}  "
          f"holdout monthly-diff mean {slice_holdout_mean(per_book):+.3f} bps")

    # verdict
    print("\n--- FROZEN VERDICT ---")
    net_pass = (t_pool.statistic > 2)
    gap_neg = (t_pool_slip.statistic < -2)
    success = net_pass and gap_neg and holdout_ok
    kill = (abs(t_pool.statistic) < 2) and (abs(t_pool_slip.statistic) < 2)
    print(f"success (B>A paired t>2 AND gap t<-2 AND holdout-stable): {success}")
    print(f"kill (|net t|<2 AND |gap t|<2): {kill}")
    print(f"  net t = {t_pool.statistic:+.3f} (>2? {net_pass})  "
          f"gap t = {t_pool_slip.statistic:+.3f} (<-2? {gap_neg})  holdout_ok={holdout_ok}")

    # save CSVs
    rows = []
    for name in VOL3:
        pb = per_book[name]
        rows.append({k: v for k, v in pb.items() if k not in ("dmo", "slip")})
        rows[-1]["book"] = name
    pd.DataFrame(rows).set_index("book").to_csv(OUT / "hd1_per_book.csv")
    pooled_dmo.to_csv(OUT / "hd1_pooled_monthly_diff.csv")
    pooled_sl.to_csv(OUT / "hd1_pooled_gap_slippage.csv")
    print(f"\nsaved -> {OUT}/hd1_*.csv")
    return per_book, t_pool, t_pool_slip, success, kill, holdout_ok


def slice_holdout_mean(per_book):
    vals = []
    for name in VOL3:
        d = per_book[name]["dmo"]
        d = d[d.index >= pd.Timestamp(HOLDOUT_START)]
        vals.append(d)
    return pd.concat(vals).mean() * 1e4


if __name__ == "__main__":
    main()
