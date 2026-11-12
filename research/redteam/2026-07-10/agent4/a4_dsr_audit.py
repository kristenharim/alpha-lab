"""Agent4: audit of robustness/deflated.md.
1. Reproduce the repo DSR table exactly (same formula).
2. Run the SAME formula on SPY/QQQ buy-and-hold (no-skill controls).
3. Check IID assumptions: lag autocorrelation of daily nets; NW-adjusted DSR.
4. Dependence: pairwise corr of the 18 nets; Monte-Carlo expected max Sharpe
   under a zero-mean null PRESERVING the empirical covariance (vs the repo sr0).
"""
from pathlib import Path
from statistics import NormalDist

import numpy as np
import pandas as pd

OUT = Path(__file__).parent
ND = NormalDist()
EM = 0.5772156649

df = pd.read_parquet(OUT / "nets5y.parquet")
specs = [c for c in df.columns if not c.startswith("_")]
N = len(specs)

sr = {c: df[c].mean() / df[c].std() for c in df.columns}
sr_arr = np.array([sr[c] for c in specs])
sr0 = sr_arr.std(ddof=1) * ((1 - EM) * ND.inv_cdf(1 - 1 / N)
                            + EM * ND.inv_cdf(1 - 1 / (N * np.e)))
print(f"repro sr0 = {sr0:.4f} (ann {sr0*np.sqrt(252):.2f})   [repo: 0.0334 / 0.53]")


def dsr_row(net, sr0):
    s = net.mean() / net.std()
    T = len(net)
    g3, g4 = float(net.skew()), float(net.kurt()) + 3
    denom = np.sqrt(max(1e-12, 1 - g3 * s + (g4 - 1) / 4 * s ** 2))
    return (s * np.sqrt(252), ND.cdf((s - sr0) * np.sqrt(T - 1) / denom),
            ND.cdf(s * np.sqrt(T - 1) / denom))


print("\n-- reproduction of deflated.md (spec, annSR, DSR, P(SR>0)) --")
rows = {}
for c in specs:
    rows[c] = dsr_row(df[c], sr0)
for c, (a, d, p) in sorted(rows.items(), key=lambda kv: -kv[1][1]):
    print(f"{c:26s} {a:5.2f}  {d:6.1%}  {p:6.1%}")

print("\n-- SAME formula applied to no-skill benchmarks --")
for c in ["_SPY_BH", "_QQQ_BH"]:
    a, d, p = dsr_row(df[c], sr0)
    print(f"{c:26s} {a:5.2f}  DSR {d:6.1%}  P(SR>0) {p:6.1%}")

print("\n-- IID check: lag-1..5 autocorrelation of daily nets --")
for c in specs + ["_SPY_BH"]:
    ac = [df[c].autocorr(l) for l in range(1, 6)]
    print(f"{c:26s} " + " ".join(f"{x:+.3f}" for x in ac))

# NW-style variance inflation factor for the mean: 1 + 2*sum((1-l/L)*rho_l), L=10
print("\n-- DSR with Newey-West(10) inflated SE (per spec) --")
L = 10
for c in specs:
    net = df[c]
    rho = np.array([net.autocorr(l) for l in range(1, L + 1)])
    infl = max(1e-6, 1 + 2 * np.sum((1 - np.arange(1, L + 1) / (L + 1)) * rho))
    s = net.mean() / net.std()
    T = len(net)
    g3, g4 = float(net.skew()), float(net.kurt()) + 3
    denom = np.sqrt(max(1e-12, 1 - g3 * s + (g4 - 1) / 4 * s ** 2) * infl)
    d = ND.cdf((s - sr0) * np.sqrt(T - 1) / denom)
    print(f"{c:26s} infl {infl:5.2f}  DSR_iid {rows[c][1]:6.1%} -> DSR_nw {d:6.1%}")

print("\n-- dependence among the 18 trials --")
C = df[specs].corr()
off = C.values[np.triu_indices(N, 1)]
print(f"pairwise corr: mean {off.mean():+.2f}, median {np.median(off):+.2f}, "
      f"min {off.min():+.2f}, max {off.max():+.2f}")
ev = np.linalg.eigvalsh(C.values)[::-1]
print("effective # independent trials (eigen, (sum l)^2/sum l^2):",
      f"{ev.sum()**2 / (ev**2).sum():.1f}")

# MC expected-max under zero-true-SR null with empirical covariance
rng = np.random.default_rng(0)
T = len(df)
cov = df[specs].cov().values
Lc = np.linalg.cholesky(cov + 1e-12 * np.eye(N))
mx = []
for _ in range(2000):
    z = rng.standard_normal((T, N)) @ Lc.T
    m = z.mean(0) / z.std(0, ddof=1)
    mx.append(m.max())
mx = np.array(mx)
print(f"MC E[max SR | true SR=0, empirical cov, N=18]: {mx.mean():.4f} daily "
      f"(ann {mx.mean()*np.sqrt(252):.2f}); 95th pct {np.quantile(mx,0.95)*np.sqrt(252):.2f} ann")
print(f"repo sr0 threshold: 0.0334 daily / 0.53 ann")
