"""EXP-2026-07-14-vol-timing — VIX term-structure gate on SVXY carry.

Frozen prereg: research/vol_timing/PREREG.md (incl. dispositions). Signal
s_t = 1{VIX_t/VIX3M_t < 1}; strategy W_t = [SVXY: s_{t-1}, BIL: 1-s_{t-1}];
harness convention adds one more day (held = W.shift(1)) -> exactly one full day
of delay. Benchmarks B1 (const SVXY), B2 (0.9216 SVXY / 0.0784 BIL). Primary:
mean daily log diff vs B2, stationary-block-bootstrap CI. Placebos P1/P2/P4/P5.
Local 2-asset engine asserted against harness.run before any placebo loop.

Run from repo root: .venv/bin/python research/vol_timing/run_voltiming.py
"""
import hashlib
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "research/hunt2026"))
sys.path.insert(0, str(REPO))
import harness  # noqa: E402
from core.eval.run_manifest import stamp_run  # noqa: E402

OUT = REPO / "research/vol_timing"
WBAR = 0.9216
ETF_BPS = 2.0
HOLDOUT_START = pd.Timestamp("2025-07-10")   # holdout = dates > this (hunt convention)
REGIME_SPLIT = pd.Timestamp("2018-02-28")
SEED_BOOT, SEED_P1, SEED_P4 = 3, 5, 7
N_BOOT, N_PLACEBO, BLOCK = 2000, 1000, 21
OFF_RUN_MEAN, ON_FRAC = 2.98, 0.9234
CRASH = [("Volmageddon", "2018-02-01", "2018-02-15"),
         ("COVID", "2020-02-19", "2020-03-23"),
         ("2022 bear", "2022-01-03", "2022-10-14"),
         ("yen-carry", "2024-07-15", "2024-08-09"),
         ("2025-04 gaps", "2025-04-01", "2025-04-30")]


def engine(weights, rets):
    """Local 2-asset accounting identical to harness.run: held = W.shift(1),
    cost = 2 bps x |dW| (full entry first day)."""
    held = weights.shift(1)
    gross = (held * rets).sum(axis=1, min_count=1).fillna(0.0)
    cost = (weights.diff().abs().fillna(weights.abs()) * (ETF_BPS / 1e4)).sum(axis=1)
    return gross - cost


def stats_block(net, label):
    nav = (1 + net).cumprod()
    return {"series": label, "cagr": float(nav.iloc[-1] ** (252 / len(net)) - 1),
            "ann_vol": float(net.std() * np.sqrt(252)),
            "max_dd": float((nav / nav.cummax() - 1).min()),
            "turnover_ann": np.nan}


def crash_returns(net):
    nav = (1 + net).cumprod()
    out = {}
    for name, a, b in CRASH:
        w = nav.loc[a:b]
        out[name] = float(w.iloc[-1] / w.iloc[0] - 1) if len(w) > 1 else np.nan
    return out


def gated_net(sig, rets, index):
    W = pd.DataFrame({"SVXY": sig.shift(1).reindex(index).fillna(0.0)}, index=index)
    W["BIL"] = 1.0 - W["SVXY"]
    return engine(W, rets)


def boot_ci(x, seed=SEED_BOOT, n_boot=N_BOOT):
    rng = np.random.default_rng(seed)
    n = len(x)
    means = []
    for _ in range(n_boot):
        idx, pos = [], rng.integers(0, n)
        while len(idx) < n:
            idx.append(pos)
            pos = rng.integers(0, n) if rng.random() < 1 / BLOCK else (pos + 1) % n
        means.append(x[np.array(idx)].mean())
    lo, hi = np.quantile(means, [0.025, 0.975])
    return float(lo), float(hi)


def main():
    panel = harness.load_full()
    close = panel["close"][["SVXY", "BIL"]]
    rets = close.pct_change(fill_method=None)
    vix = panel["close"]["^VIX"]
    v3 = pd.read_parquet(REPO / "data/raw/vix3m_daily.parquet")["VIX3M"]
    v3 = v3.reindex(vix.index)
    sig = (vix / v3 < 1.0).astype(float)
    idx = rets.dropna().index                            # both assets live (2014->)
    idx = idx[idx <= pd.Timestamp("2026-07-10")]

    # real strategy net, local engine
    net_s = gated_net(sig, rets, idx).reindex(idx)
    # parity assert vs harness.run on a dynamic spec
    class _Spec:
        @staticmethod
        def target_weights(p):
            c = p["close"]
            W = pd.DataFrame(0.0, index=c.index, columns=c.columns)
            s1 = sig.shift(1).reindex(c.index).fillna(0.0)
            W["SVXY"] = s1
            W["BIL"] = 1.0 - s1
            return W
    hr = harness.run(_Spec, panel)["net_daily"].reindex(idx)
    # parity: identical on all days except idx[0] — harness charges the full entry
    # cost at PANEL start (2005, outside the window), the local engine at window
    # start. Local treatment applies equally to strategy and both benchmarks (fair).
    assert np.allclose(net_s.values[1:], hr.values[1:], atol=1e-12), "engine parity FAIL"

    W1 = pd.DataFrame({"SVXY": 1.0, "BIL": 0.0}, index=idx)
    W2 = pd.DataFrame({"SVXY": WBAR, "BIL": 1 - WBAR}, index=idx)
    net_b1 = engine(W1, rets.reindex(idx))
    net_b2 = engine(W2, rets.reindex(idx))

    logd = np.log1p(net_s) - np.log1p(net_b2)
    arith = net_s - net_b2
    full, hold = logd, logd[logd.index > HOLDOUT_START]
    dF, dH = float(full.mean() * 252), float(hold.mean() * 252)
    ci_log = tuple(c * 252 for c in boot_ci(full.values))
    ci_arith = tuple(c * 252 for c in boot_ci(arith.values, seed=SEED_BOOT + 1))
    dA = float(arith.mean() * 252)
    # MDE: 2.84 x bootstrap SE of the mean (annualized)
    rng_se = np.std([full.values[np.random.default_rng(SEED_BOOT + 2 + i).integers(
        0, len(full), len(full))].mean() for i in range(200)])
    mde = float(2.84 * rng_se * 252)

    # secondary/tail
    row_s = stats_block(net_s, "strategy")
    row_b1 = stats_block(net_b1, "B1_const_SVXY")
    row_b2 = stats_block(net_b2, "B2_exposure_matched")
    cr_s, cr_b1, cr_b2 = crash_returns(net_s), crash_returns(net_b1), crash_returns(net_b2)

    # holdout mechanism check
    off_hold = sig.reindex(idx).shift(2)[
        (idx > HOLDOUT_START)] == 0.0
    svxy_hold = rets["SVXY"].reindex(idx)[idx > HOLDOUT_START]
    off_mean_svxy = float(svxy_hold[off_hold.values].mean())

    # regime splits + one-regime checks
    pre = float(logd[logd.index <= REGIME_SPLIT].mean() * 252)
    post = float(logd[logd.index > REGIME_SPLIT].mean() * 252)
    contrib = logd.groupby(logd.index.year).sum()
    best_year = int(contrib.idxmax())
    ex_best = float(logd[logd.index.year != best_year].mean() * 252)

    # episode diagnostics
    s2 = sig.reindex(idx).shift(2).fillna(1.0)           # effective position lag
    off = s2 == 0.0
    ep_id = (off != off.shift()).cumsum()[off]
    ep_len = ep_id.map(ep_id.value_counts())
    dec = {}
    for lab, lo, hi in [("len1", 1, 1), ("len2-5", 2, 5), ("len>5", 6, 10 ** 9)]:
        days = ep_len[(ep_len >= lo) & (ep_len <= hi)].index
        dec[lab] = float(logd.reindex(days).sum())
    # event-time profile: SVXY mean return on day k from episode start (signal-time)
    raw_off = sig.reindex(idx) == 0.0
    starts = idx[(raw_off & ~raw_off.shift(1, fill_value=False))]
    prof = {}
    svxy_r = rets["SVXY"].reindex(idx)
    uncond = float(svxy_r.mean())
    for k in range(1, 6):
        vals = [svxy_r.iloc[i + k] for i in [idx.get_loc(s) for s in starts]
                if i + k < len(idx)]
        prof[k] = float(np.mean(vals))

    # placebos
    def excess_of(sig_x):
        return float((np.log1p(gated_net(sig_x, rets, idx).reindex(idx))
                      - np.log1p(net_b2)).mean() * 252)

    rng1 = np.random.default_rng(SEED_P1)
    s_arr = sig.reindex(idx).values
    n = len(s_arr)
    p1 = []
    for _ in range(N_PLACEBO):
        shift0 = rng1.integers(0, n)
        blocks = [np.roll(s_arr, shift0)[i:i + 63] for i in range(0, n, 63)]
        rng1.shuffle(blocks)
        p1.append(excess_of(pd.Series(np.concatenate(blocks)[:n], index=idx)))
    p1_95 = float(np.quantile(p1, 0.95))

    rng4 = np.random.default_rng(SEED_P4)
    on_run_mean = OFF_RUN_MEAN * ON_FRAC / (1 - ON_FRAC)
    p4, p4_dd_gain, p4_crash_gain = [], [], []
    b2_dd = row_b2["max_dd"]
    for _ in range(N_PLACEBO):
        s_p, state = [], 1.0
        while len(s_p) < n:
            run = 1 + rng4.geometric(1 / (on_run_mean if state else OFF_RUN_MEAN)) - 1
            s_p.extend([state] * max(run, 1))
            state = 1.0 - state
        sp = pd.Series(np.array(s_p[:n], float), index=idx)
        net_p = gated_net(sp, rets, idx).reindex(idx)
        p4.append(float((np.log1p(net_p) - np.log1p(net_b2)).mean() * 252))
        nav_p = (1 + net_p).cumprod()
        p4_dd_gain.append(float((nav_p / nav_p.cummax() - 1).min()) - b2_dd)
        p4_crash_gain.append([crash_returns(net_p)[c[0]] - cr_b2[c[0]] for c in CRASH])
    p4_95 = float(np.quantile(p4, 0.95))
    p4_dd_95 = float(np.quantile(p4_dd_gain, 0.95))
    p4_crash_95 = np.quantile(np.array(p4_crash_gain), 0.95, axis=0)

    p2 = excess_of(sig.shift(5))
    # P5: info-free stress gate
    spy_r = panel["close"]["SPY"].pct_change(fill_method=None).reindex(idx)
    rv = spy_r.rolling(21).std()
    q = rv[rv.index <= HOLDOUT_START].quantile(1 - 0.0784)
    s5 = (rv < q).astype(float).fillna(1.0)
    net_p5 = gated_net(s5, rets, idx).reindex(idx)
    cr_p5 = crash_returns(net_p5)
    dd_p5 = stats_block(net_p5, "P5")["max_dd"]
    p5_excess = float((np.log1p(net_p5) - np.log1p(net_b2)).mean() * 252)

    # rule evaluation
    ci_excl0 = ci_log[0] > 0 or ci_log[1] < 0
    dd_gain = row_s["max_dd"] - b2_dd                     # positive = shallower DD
    crash_gain = {c[0]: cr_s[c[0]] - cr_b2[c[0]] for c in CRASH}
    crash_beats_p4 = sum(crash_gain[c[0]] > p4_crash_95[i] for i, c in enumerate(CRASH))
    beats_p5_dd = row_s["max_dd"] > dd_p5
    beats_p5_crash = sum(cr_s[c[0]] > cr_p5[c[0]] for c in CRASH)
    p4_rule2_rate = float(np.mean([
        (p4_dd_gain[i] > p4_dd_95) and
        (sum(p4_crash_gain[i][j] > p4_crash_95[j] for j in range(5)) >= 3)
        for i in range(N_PLACEBO)]))
    rule2 = ((not ci_excl0 or dF <= 0) and dd_gain > p4_dd_95
             and crash_beats_p4 >= 3 and beats_p5_dd and beats_p5_crash >= 3)
    p2_decay = (1 - p2 / dF) > 0.5 if dF > 0 else True
    rule3 = (dF > 0 and ci_excl0 and dH > 0 and off_mean_svxy < 0
             and dF > p1_95 and dF > p4_95 and p2_decay
             and ex_best > 0 and pre > 0 and post > 0)
    if rule3:
        verdict = "PROMISING BUT UNPROVEN VOLATILITY TIMING ALPHA"
    elif rule2:
        verdict = "RISK-MANAGEMENT IMPROVEMENT, NOT ALPHA"
    elif dF <= 0:
        verdict = "NO EVIDENCE OF TIMING ALPHA"
    else:
        verdict = "AMBIGUOUS"

    pd.DataFrame([row_s, row_b1, row_b2]).to_csv(OUT / "voltiming.csv", index=False)
    L = ["# Vol-timing — VIX term-structure gate on SVXY (EXP-2026-07-14-vol-timing)", "",
         "Prereg: PREREG.md (frozen incl. dispositions). Full 2014-01→2026-07-10; "
         "holdout 2025-07-11→. Costs 2 bps/side; churn null ≈ 0.5%/yr pre-stated.", "",
         f"## Verdict (pre-committed ladder): **{verdict}**", "",
         "## Primary (vs B2, exposure-matched; annualized mean daily log diff)",
         f"- ΔF = {dF:+.2%}  [boot 95% CI {ci_log[0]:+.2%}, {ci_log[1]:+.2%}]  "
         f"(MDE ≈ {mde:.1%})",
         f"- arithmetic secondary: {dA:+.2%}  [CI {ci_arith[0]:+.2%}, {ci_arith[1]:+.2%}]",
         f"- holdout ΔH = {dH:+.2%} (directional only; ~14 OFF days); "
         f"holdout OFF-day mean SVXY return {off_mean_svxy:+.3%}/day",
         f"- one-regime: best contribution year {best_year}; excluding it "
         f"{ex_best:+.2%}; pre-2018 {pre:+.2%}, post-2018 {post:+.2%}", "",
         "## Levels & tails", "",
         "| series | CAGR | vol | maxDD | " + " | ".join(c[0] for c in CRASH) + " |",
         "|---|---|---|---|---|---|---|---|---|"]
    for row, cr in [(row_s, cr_s), (row_b1, cr_b1), (row_b2, cr_b2)]:
        L.append(f"| {row['series']} | {row['cagr']:+.1%} | {row['ann_vol']:.1%} "
                 f"| {row['max_dd']:.1%} | "
                 + " | ".join(f"{cr[c[0]]:+.1%}" for c in CRASH) + " |")
    L += ["", "## Placebos",
          f"- P1 shuffled: 95th pct {p1_95:+.2%} vs ΔF {dF:+.2%} → "
          f"{'PASS' if dF > p1_95 else 'fail'}",
          f"- P2 delayed 5d: excess {p2:+.2%} (decay "
          f"{(1 - p2 / dF) if dF > 0 else float('nan'):.0%})",
          f"- P4 random episodes: 95th pct {p4_95:+.2%} → "
          f"{'PASS' if dF > p4_95 else 'fail'}; rule-2-as-written null rate "
          f"{p4_rule2_rate:.1%} (bar < 5%)",
          f"- P5 info-free stress gate: excess {p5_excess:+.2%}, maxDD {dd_p5:.1%}; "
          f"real beats P5 on maxDD: {'yes' if beats_p5_dd else 'NO'}, on crash windows "
          f"{beats_p5_crash}/5", "",
          "## Latency diagnostics (pre-stated readings in PREREG.md)",
          f"- episode-length decomposition of Σ log-diff: {dec}",
          f"- event-time SVXY mean return day k=1..5 after inversion start: "
          f"{[f'{prof[k]:+.3%}' for k in range(1, 6)]} vs unconditional "
          f"{uncond:+.3%}/day", "",
          "## Story", "", "(appended post-run)", ""]
    (OUT / "VOLTIMING.md").write_text("\n".join(L))
    print("\n".join(L))
    stamp_run(track="vol_timing", variant="ts_gate_svxy",
              params={"wbar": WBAR, "seeds": [SEED_BOOT, SEED_P1, SEED_P4],
                      "n_boot": N_BOOT, "n_placebo": N_PLACEBO,
                      "numpy": np.__version__, "pandas": pd.__version__,
                      "holdout_n": int((idx > HOLDOUT_START).sum()),
                      "verdict": verdict,
                      "input_sha256": {f: hashlib.sha256(
                          (REPO / f).read_bytes()).hexdigest()[:16]
                          for f in ["data/raw/vix3m_daily.parquet"]},
                      "prereg": "research/vol_timing/PREREG.md"},
              n_trials=1)


if __name__ == "__main__":
    main()
