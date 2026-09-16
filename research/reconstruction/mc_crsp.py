"""EXP-2026-09-16-mc-crsp: the frozen momentum_concentrated spec on CRSP, through the unchanged
hunt2026 harness. Pre-registration: research/reconstruction/preregistrations/mc-crsp-2026-09-16.md.

Run: .venv/bin/python research/reconstruction/mc_crsp.py
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "research" / "hunt2026"))
import harness  # noqa: E402
from core.data.registry import register  # noqa: E402

CACHE = ROOT / "data" / "crsp"
START, END = "1990-01-01", "2024-12-31"
SPEC = ROOT / "research" / "hunt2026" / "specs" / "momentum_concentrated"
A = ("1992-01-01", "2004-12-31")
B = ("2005-01-01", "2024-12-31")


def pull(db):
    files = {k: CACHE / f"sp500_daily_{k}.parquet" for k in ("dsf", "members", "delist", "index", "ff")}
    if all(f.exists() for f in files.values()):
        return {k: pd.read_parquet(f) for k, f in files.items()}
    CACHE.mkdir(parents=True, exist_ok=True)
    members = db.raw_sql(f"select permno, start, ending from crsp.dsp500list where ending >= '{START}'",
                         date_cols=["start", "ending"])
    perms = ",".join(str(int(p)) for p in members["permno"].unique())
    chunks = []
    for y in range(int(START[:4]), int(END[:4]) + 1):
        chunks.append(db.raw_sql(f"select permno, date, ret from crsp.dsf where permno in ({perms}) "
                                 f"and date between '{y}-01-01' and '{y}-12-31'", date_cols=["date"]))
    dsf = pd.concat(chunks, ignore_index=True)
    delist = db.raw_sql(f"select permno, dlstdt, dlret, dlstcd from crsp.dsedelist where permno in ({perms}) "
                        f"and dlstcd <> 100", date_cols=["dlstdt"])
    index = db.raw_sql(f"select caldt, vwretd from crsp.dsp500 where caldt between '{START}' and '{END}'",
                       date_cols=["caldt"])
    ff = db.raw_sql(f"select date, rf from ff.factors_daily where date between '{START}' and '{END}'",
                    date_cols=["date"])
    out = {"dsf": dsf, "members": members, "delist": delist, "index": index, "ff": ff}
    for k, df in out.items():
        df.to_parquet(files[k])
        register(ROOT / "data" / "manifest.jsonl", f"crsp_sp500_daily_{k}", "WRDS CRSP",
                 {"start": START, "end": END, "universe": "dsp500list members"},
                 str(files[k].relative_to(ROOT)), len(df))
    return out


def daily_returns_with_delisting(dsf, delist):
    """permno x date matrix of daily returns. A delisting return lands on the first trading day after
    the last traded date (compounded if CRSP dates it on a traded day); Shumway -30% for a
    performance delisting with no recorded return."""
    R = dsf.pivot_table(index="date", columns="permno", values="ret")
    days = R.index
    d = delist.copy()
    d.loc[d["dlret"].isna() & d["dlstcd"].between(500, 599), "dlret"] = -0.30
    d = d.dropna(subset=["dlret"])
    for _, row in d.iterrows():
        p = int(row["permno"])
        if p not in R.columns:
            continue
        last = R[p].last_valid_index()
        if last is None:
            continue
        after = days[days > last]
        if row["dlstdt"] <= last:
            R.at[last, p] = (1 + R.at[last, p]) * (1 + row["dlret"]) - 1
        elif len(after):
            R.at[after[0], p] = row["dlret"]
    return R


def build_panel(data, survivors_only=False):
    dsf = data["dsf"].copy()
    dsf["permno"] = dsf["permno"].astype(int)
    delist = data["delist"].copy()
    delist["permno"] = delist["permno"].astype(int)
    if survivors_only:
        last = dsf.groupby("permno")["date"].max()
        keep = set(last[last >= pd.Timestamp("2024-12-31")].index)
        dsf = dsf[dsf["permno"].isin(keep)]
        R = dsf.pivot_table(index="date", columns="permno", values="ret")
    else:
        R = daily_returns_with_delisting(dsf, delist)
    idx = R.index
    # total-return "close": starts at 1 on each security's first return; NaN before and after life
    close = (1 + R.fillna(0)).cumprod()
    alive = R.notna().cumsum() > 0
    dead = R[::-1].notna().cumsum()[::-1] == 0
    close = close.where(alive & ~dead)
    close.columns = [str(c) for c in close.columns]

    m = data["members"].copy()
    member = pd.DataFrame(0.0, index=idx, columns=close.columns)
    for _, row in m.iterrows():
        c = str(int(row["permno"]))
        if c in member.columns:
            member.loc[(idx >= row["start"]) & (idx <= row["ending"]), c] = 1.0

    spx = data["index"].set_index("caldt")["vwretd"].reindex(idx).fillna(0)
    close["SPY"] = (1 + spx).cumprod()
    member["SPY"] = 1.0
    return pd.concat({"close": close, "member": member}, axis=1)




def evaluate(panel, rf, window, spec):
    res = harness.run(spec, panel, *window)
    W = spec.target_weights(panel).astype(float).fillna(0.0)
    g = W.abs().sum(axis=1)
    W = W.mul((harness.MAX_GROSS / g).clip(upper=1.0).fillna(1.0), axis=0)
    held_gross = W.abs().sum(axis=1).shift(1).reindex(res["net_daily"].index).fillna(0)
    r = res["net_daily"] + rf.reindex(res["net_daily"].index).fillna(0) * (1 - held_gross)
    return res, r, held_gross


def ann(r):
    nav = (1 + r).cumprod()
    yrs = len(r) / 252
    return {"cagr": nav.iloc[-1] ** (1 / yrs) - 1, "vol": r.std() * np.sqrt(252),
            "sharpe": r.mean() / r.std() * np.sqrt(252), "maxdd": (nav / nav.cummax() - 1).min()}


def nw_alpha(monthly_ex, factors, lags=3):
    """OLS alpha with a Newey-West (Bartlett) t-stat, numpy only. Returns annualized alpha, t,
    factor loadings, months."""
    j = pd.concat([monthly_ex.rename("y"), factors], axis=1).astype(float).dropna()
    y = j["y"].to_numpy()
    X = np.column_stack([np.ones(len(j)), j.drop(columns="y").to_numpy()])
    beta, *_ = np.linalg.lstsq(X, y, rcond=None)
    u = y - X @ beta
    Xu = X * u[:, None]
    S = Xu.T @ Xu
    for k in range(1, lags + 1):
        w = 1 - k / (lags + 1)
        G = Xu[k:].T @ Xu[:-k]
        S += w * (G + G.T)
    XtX_inv = np.linalg.inv(X.T @ X)
    se = np.sqrt(np.diag(XtX_inv @ S @ XtX_inv))
    loads = dict(zip(j.drop(columns="y").columns, np.round(beta[1:], 2)))
    return beta[0] * 12, beta[0] / se[0], loads, len(j)


def main():
    import wrds
    db = wrds.Connection(wrds_username="kris10harim")
    data = pull(db)
    fm = db.raw_sql("select date, mktrf, smb, hml, umd, rf from ff.factors_monthly "
                    f"where date between '{START}' and '{END}'", date_cols=["date"])
    db.close()
    fm["ym"] = fm["date"].dt.to_period("M")
    fm = fm.set_index("ym")
    rf = data["ff"].set_index("date")["rf"]
    spec = harness.load_spec(SPEC)

    rows = []
    for label, surv, window in [("A 1992-2004, with delistings", False, A),
                                ("B 2005-2024, with delistings", False, B),
                                ("B 2005-2024, survivors only", True, B)]:
        panel = build_panel(data, survivors_only=surv)
        res, r, hg = evaluate(panel, rf, window, spec)
        s = ann(r)
        avg_g = hg.mean()
        idx_r = panel["close"]["SPY"].pct_change().reindex(r.index).fillna(0)
        base = avg_g * idx_r + rf.reindex(r.index).fillna(0) * (1 - avg_g)
        b = ann(base)
        mex = (1 + r).resample("ME").prod() - 1
        mex.index = mex.index.to_period("M")
        mex = mex - fm["rf"].reindex(mex.index)
        a, t, loads, n = nw_alpha(mex, fm[["mktrf", "smb", "hml", "umd"]])
        rows.append({"label": label, **s, "avg_gross": avg_g, "turnover": res["avg_daily_turnover"],
                     "cost_drag": res["cost_drag_ann"], "base_cagr": b["cagr"], "base_sharpe": b["sharpe"],
                     "alpha": a, "alpha_t": t, "loads": loads, "months": n})
        print(label, {k: (round(v, 4) if isinstance(v, float) else v) for k, v in rows[-1].items()})
    pd.DataFrame(rows).to_json(ROOT / "research" / "reconstruction" / "mc_crsp_results.json", orient="records", indent=2)


if __name__ == "__main__":
    main()
