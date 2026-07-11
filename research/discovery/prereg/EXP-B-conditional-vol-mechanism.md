# PREREG EXP-B — Conditional volatility-management mechanism (explanation, not a switch)

*Frozen 2026-07-10 (Discovery Program). Unlocked by DATA_QUALITY_REPORT.md = PASS. Nothing above
the Result line may be edited after the first scoring run. This EXPLAINS where vol-management helps;
it does NOT optimize a trading switch and builds no portfolio. Conditions and expected signs are
frozen here BEFORE any evaluation (charter: do not discover the regime after seeing results).*

- **Experiment ID:** EXP-2026-07-10-conditional-vol-mechanism
- **Layer touched (one):** A — mechanism/phenomenon (which observable asset properties explain the
  cross-asset variation in vol-management benefit?)
- **Alpha type:** mechanism test — re-grades the **generality** of the promoted vol family. NOT a
  new market forecast; it cannot itself become a book.

**Hypothesis (one falsifiable sentence, mechanism):** Volatility management improves an asset's
geometric growth in proportion to four **pre-registered, fixed-sign** observable properties —
(1) positive risk premium, (2) volatility clustering, (3) negative return–volatility asymmetry
(leverage effect), (4) volatility-linked drawdown convexity — and does NOT help universally
(F-020); so the cross-asset variation in vol-management benefit is *explained* by these properties
with the signs below, at the cluster level.

**Why this is the sanctioned reopen of F-020:** F-020 rejected *uniform* cross-market vol-management
(3/7 clusters) but could not test *why* — it lacked the macro/vol state now provided by the PASSed
data layer. This asks the mechanism question, not "which ETF performed best."

**Data:** `panel_2005.parquet` ETF returns for the cross-asset set; `../data/state_aligned.parquet`
for VIX/VIX3M and rate/curve state (**STATE variables only** — no vol-carry return is claimed).

**Unit of analysis:** each cross-asset ETF (SPY, QQQ, IWM, EFA, EEM, TLT, IEF, GLD, DBC, USO, VNQ,
plus sector XLK/XLE/XLF/XLU/XLP/XLV/XLY/XLI), from each ETF's inception. **Inference is at the
CLUSTER level** (equities / intl-equity / rates / commodities / sectors-within-equity are correlated
— correlated ETFs count as ONE observation, not N). No per-asset parameter tuning.

**Response (measured, fixed rule):** `benefit_i` = geometric growth of the 21d-realized-vol-targeted
version of asset i (target vol + cap **frozen at the vol_managed_qqq spec** — identical for every
asset) minus buy-hold, net of a fixed turnover cost.

**Predictors (pre-registered, fixed, with EXPECTED SIGNS — no combination search):**
1. risk premium = full-sample mean excess return — **expect +**
2. vol clustering = AR(1) of 21d realized vol (or of squared daily returns) — **expect +**
3. return–vol asymmetry = leverage-effect coef corr(r_t, Δσ_{t+1}) — **expect benefit rises as this is more negative**
4. drawdown convexity = ratio of realized vol in worst-return-decile months to overall vol — **expect +**
5. (context, not scored for sign) funding sensitivity = β to ΔDFF/curve; curve/vol-state exposure — reported for interpretation only.

**Control:** universal vol-management applied to all assets (F-020's rejected uniform rule — the null
that properties don't matter). **Treatment:** regress `benefit` on the 4 fixed-sign properties;
test sign + joint significance at cluster level.

**Primary statistic:** cross-asset (cluster-level) regression of `benefit` on the 4 pre-registered
properties — do the coefficient **signs match the predictions** and is the model **jointly
significant** with n = number of clusters? **Secondary:** leave-one-cluster-out sign stability; a
walk-forward variant (properties from an expanding window predict next-period benefit) as the only
tradability-relevant check. Report R² but NEVER select predictors on it.

**Sample / holdout:** full history per asset. The primary is a descriptive cross-sectional
*explanation* (properties are stable asset characteristics); the walk-forward secondary is the
look-ahead-safe version. Freeze the property list + signs now (done, above).

**Expected effect:** ≥3 of 4 signs hold at cluster level with joint significance. Honest prior
P(supported) ≈ 0.55. **Alternative:** benefit is explained but by risk-premium/beta ALONE (properties
2-4 add nothing) ⇒ narrows the claim to "vol-management helps high-premium equity beta," not a
general mechanism.

**Failure / kill condition (decidable, stop-iterating):** properties do not explain cross-asset
benefit (joint insignificant at cluster level OR the majority of signs wrong) → **MECHANISM
UNSUPPORTED**; vol-management stays an empirical US-large-cap fact, not a mechanistically
generalizable rule. This CLOSES the conditional-vol reopen — do not test further property sets on
this ETF panel (the reopen is then new markets/instruments, not new features here).

**Cost model:** benefit computed net of a fixed per-rebalance turnover cost so the ranking is
implementable-relevant; no live trading (mechanism study).

**Leakage / survivorship:** VIX/rates STATE only, availability-lagged in the PASSed data layer;
the primary is descriptive (stable characteristics), the secondary is walk-forward. ETF-only, from
real inception (no synthetic pre-inception history).

**Parameter count:** 0 fit (vol-target frozen from the live spec; property list frozen).
**Complexity:** 3/5. **Information gain:** HIGH — adjudicates the trend-alpha-vs-levered-beta
generality question F-020 could not, and tells the lab whether the promoted family's edge is a
transportable mechanism or a single-market fact.

**Decision changed by success:** a validated property model tells us WHERE to look for the next
vol-management application (and whether the promoted family generalizes) — a research-direction
result, not a book. **Decision changed by failure:** stop trying to export vol-management; treat it
as US-large-cap-specific (consistent with F-020), and the promoted family's generality is capped.

**Trial-ledger entry:** TRIAL_LEDGER #24 (Discovery / mechanism) at first score.

---
**Result** (filled after the run, never edited above this line):

**Run:** 2026-07-11 · runner `research/discovery/experiments/EXP-B-conditional-vol-mechanism.py`
· outputs `EXP-B-per-asset.csv`, `EXP-B-cluster-means.csv`, `EXP-B-results.json`. Vol-target spec
FROZEN at the live `vol_managed_qqq` (σ_target=0.25, 21d realized-vol lookback, 0.05 no-trade band,
2.0 cap), applied identically to every asset; costs = harness convention (2 bps/side ETF on |Δw|).
n = 26 ETFs across 5 clusters, each from its first available panel bar (2005-01 for most; XLC 2018,
XLRE 2015). VIX/rates used as STATE only (risk-free = DFF for the excess-return property).

**VERDICT: MECHANISM UNSUPPORTED** (frozen kill applied mechanically: the 4-property model is NOT
jointly significant at the cluster level). Vol-management stays an empirical US-large-cap /
high-premium-equity-beta fact, not a validated transportable 4-property mechanism. This CLOSES the
conditional-vol reopen on this ETF panel (next reopen = new markets/instruments, not new features here).

**Cross-asset benefit (CAGR of vol-managed − buy-hold, net of cost), by cluster mean:** US-equity
+3.98%, real-estate +5.08% (VNQ, n=1), rates +1.70%, commodities +1.67%, intl-equity +0.59%. Benefit
is positive and largest in US equity + gold (GLD +5.7%, SPY +7.2%, QQQ/XLK/XLP ~+6.5%), ~0 or
negative for broad intl (EEM −0.8%), silver (−0.23), energy (XLE −1.2%), IWM (−0.1%). So the raw
cross-asset pattern already **NARROWS F-020 descriptively** — vol-management is NOT universal; it
concentrates in high-premium, high-vol-clustering equity beta.

**Standardized cluster-robust regression (benefit on the 4 z-scored properties, n=26, G=5):**
| property | expected | β (std) | cluster-robust t | sign OK? |
|---|---|---|---|---|
| risk premium | + | +0.0072 | +1.59 (p=.19) | yes |
| vol clustering (AR1 of r²) | + | +0.0116 | +3.36 (p=.03) | yes |
| return–vol asymmetry corr(rₜ,Δσₜ₊₁) | − | −0.0103 | −2.05 (p=.11) | yes |
| drawdown convexity | + | −0.0095 | −1.80 (p=.15) | **no** |

R² = 0.36. **Signs: 3/4 correct.** Drawdown convexity flips to the wrong sign in the multivariate fit
(collinear with clustering; within-cluster its β is +0.003, t=0.3 — it carries no independent signal).

**Joint significance at the cluster level (the decisive test):** the raw cluster-robust Wald is
numerically degenerate with G=5 and q=4 restrictions (F=1632, p≈0, cond(M)≈4.4e3) — **discarded as
an artifact, not signal** (bug-check below). The credible few-cluster test is a Rademacher WILD
CLUSTER BOOTSTRAP (null imposed, all 2⁵=32 draws): **joint p = 0.44 → NOT jointly significant.** A
naive iid F treating the 26 ETFs as independent gives F=2.90, p=0.047, but the prereg explicitly
forbids that inference (correlated markets ≠ independent confirmations), so it does not count. With
only 5 clusters and 4 predictors the cluster-mean regression is saturated (0 residual df) — the
design is **underpowered to establish cluster-level joint significance**, which is why the kill fires.

**Sign consistency (the part that DOES hold):** leave-one-cluster-out — risk premium (+), vol
clustering (+), asymmetry (−) keep the predicted sign in all 5 refits; only convexity is unstable
(+ expected, − realized in every refit). Cluster-mean univariate corr with benefit: risk premium
+0.65, vol clustering **+0.85**, asymmetry −0.46, convexity +0.24 (weak). Vol clustering is the
strongest and most robust predictor at every level (cluster-mean, pooled, within-cluster t=2.26,
p=0.04) — so this is NOT the "risk-premium/beta alone" alternative; the clustering channel does carry
signal, it simply cannot clear a joint test with G=5.

**Independent value after asset-class dummies (within-cluster, R²=0.50):** risk premium (t=2.0),
vol clustering (t=2.3), asymmetry (t=−2.1) retain the right sign with borderline within-cluster
significance; convexity adds nothing (t=0.3). So within the US-equity sector cross-section the three
surviving properties do track benefit — but that is a single-cluster fact, not cross-cluster proof.

**Bug-check (mandatory):** (1) Replication — my vol-managed weights reproduce the FROZEN
`vol_managed_qqq` spec exactly on QQQ (max |w_mine − w_spec| = 0.0), and the P&L convention is copied
verbatim from `harness.run`. (2) Second-method — QQQ buy-hold CAGR 0.1571 (compounded daily net) vs
0.1577 (raw price-ratio over the identical window), agree to <0.1pt. (3) Leakage — weights use only
info through t and are held shifted to t+1; corr(wₜ, rₜ) = 0.007 ≈ 0 (weights not contemporaneously
predictive). (4) The one "too-strong" number — joint F=1632/p≈0 — was traced to the G=5, q=4
cluster-robust Wald being ill-conditioned, replaced with the wild-cluster-bootstrap p=0.44. Sample
sizes ≥ 2003 daily obs per asset. No number survived as anomalously strong.

**Bottom line / decision changed:** stop trying to export vol-management as a general mechanism from
this panel. The four properties do NOT jointly explain cross-asset benefit at the cluster level
(WCB p=0.44), so the promoted vol family's generality is **capped** — treat it as US-large-cap /
high-premium-equity-beta specific (consistent with F-020, which this narrows but does not overturn).
The mechanism is *directionally* right (3/4 signs, clustering strongest and stable) but the ETF panel
has too few independent clusters to prove it; further property mining on this panel is closed —
any reopen is new markets/instruments. **No portfolio built, no book proposed, nothing promoted;
this is a measurement/research-direction result only.** TRIAL_LEDGER #24 (Discovery / mechanism).
