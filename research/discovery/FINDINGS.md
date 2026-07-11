# Discovery Program — findings (Phase: EXP-A + EXP-B, 2026-07-10)

*Both measurement experiments ran against frozen preregs and the frozen Orthogonality Benchmark v2.
Both are negative — decisive, bug-checked negatives that close lanes. No portfolio, no book, no
parameter search. Success condition for this phase (charter): determine whether bond carry is a
genuinely independent measurable effect and whether vol-management's success is explained by
observable asset characteristics. Both questions are now answered: no, and not transportably.*

---

## EXP-A — Bond-carry predictability → **REJECTED**

| field | result |
|---|---|
| **Preregistered expectation** | carry coef > 0, t > 2; equity beta ≈ 0 (\|β_SPY\|<0.1); orthogonality PASS. Prior P(supported) ≈ 0.5. |
| **Actual signed result** | primary forward-21d carry coef **+0.00143, Newey-West t = 1.53** (< 2); rank IC +0.023 (t 0.43); no horizon (5/21/63d) reaches \|t\|>2. |
| **Uncertainty** | NW(6) t=1.53, 95% CI [−0.0004, +0.0032] straddles 0; rank-IC t=0.43. |
| **Economic materiality** | none as standalone alpha: sleeve 2.4% ret / 5.8% vol / Sharpe 0.41 — and that Sharpe is duration/curve beta (β_TLT 0.33, t 21.9), not carry. After ΔDGS10 control, carry z-coef → t=1.05. |
| **Orthogonality verdict** | **NOT INDEPENDENT** — 7/8 dims pass (corr 0.27, partial 0.22, resid 0.13, downside −0.12, tail 0.09, dd-lift 1.00) but `roll_corr_max_ens`=0.737 > 0.65: the duration ladder's 63d rolling corr to the equity/vol book spikes risk-off. (resid_alpha_t 2.85 but independence fails.) |
| **Belief update** | free-data Treasury-ladder carry is a decayed, rate-regime-driven **duration bet**, not independent alpha. |
| **Supported / narrowed / inconclusive / killed** | **KILLED / REJECTED** (4 frozen kill triggers fire independently). → Failure DB F-022. |
| **Portfolio justified?** | **No.** |
| **Remaining unknown** | FX / commodity term-structure carry (materially different instruments) — **BLOCKED BY DATA** (vendor futures/roll). Free-data Treasury lane closed. |

Runner `experiments/exp_a_bond_carry.py`; carry formula recorded verbatim in the prereg Result.
Bug-checked: coef reproduced without HAC to machine precision; leakage clean (forward ΔDGS10 used
only as in-sample attribution, never in the tradable signal); n=771 pooled obs, 2005–2026.

---

## EXP-B — Conditional vol-management mechanism → **MECHANISM UNSUPPORTED**

| field | result |
|---|---|
| **Preregistered expectation** | ≥3/4 fixed-sign properties hold at cluster level **with joint significance**. Prior P(supported) ≈ 0.55. |
| **Actual signed result** | benefit (vol-managed − buy-hold CAGR, 26 ETFs): risk-premium β +0.0072 (t 1.59), **vol-clustering +0.0116 (t 3.36)**, return-vol asymmetry −0.0103 (t −2.05), drawdown-convexity −0.0095 (t −1.80, wrong sign, collinear w/ clustering). **3/4 signs correct + stable** across all 5 leave-one-cluster-out refits. R²=0.36. |
| **Uncertainty** | decisive frozen test = **cluster-level joint significance → FAILS**: wild-cluster bootstrap p=0.44 (G=5 clusters). Naive iid F p=0.047 forbidden by prereg; raw cluster-robust Wald ill-conditioned, discarded. |
| **Economic materiality** | benefit concentrates in high-premium/high-clustering **US equity + gold** (SPY +7.2%, GLD +5.7%, XLK/XLP ~+6.5%), ~0/negative for broad intl (EEM −0.8%), silver, energy, IWM. |
| **Orthogonality verdict** | n/a (mechanism study, no candidate sleeve). |
| **Belief update** | P(general transportable mechanism) drops ~0.55→~0.25; belief that benefit tracks equity risk premium + vol clustering specifically rises. |
| **Supported / narrowed / inconclusive / killed** | **UNSUPPORTED as a transportable mechanism; NARROWS F-020 descriptively** (vol-management is not universal — it is a US-large-cap/high-premium-equity + gold fact). |
| **Portfolio justified?** | **No** (and it never could be a book — it's a mechanism test). |
| **Remaining unknown** | whether a properly-powered test (more independent markets/instruments, not more features on this ETF panel) would establish the mechanism. Closed on this panel. |

Runner `experiments/EXP-B-conditional-vol-mechanism.py`. Bug-checked: vol-managed weights reproduce
the frozen `vol_managed_qqq` spec exactly; the anomalous F=1632 traced to an ill-conditioned G=5,q=4
Wald and correctly replaced by the wild-cluster bootstrap.

---

## Phase verdict
The Discovery Program's first two measured lanes both close cleanly. **No genuinely independent
new return source was found** in free-data bond carry, and vol-management's success is **not**
explained well enough by observable asset characteristics to call it a transportable mechanism.
This is the intended output: two decisive negatives that stop the lab from over-investing in a
decayed carry proxy and from exporting vol-management on a false generality claim. The next
genuinely-new-information lane remains **earnings** (Lane 1), still accruing toward n≥300 and gated;
the carry reopen is now explicitly vendor-data-gated. Orthogonality Benchmark v2 stands as the
permanent independence gate for every future candidate.
