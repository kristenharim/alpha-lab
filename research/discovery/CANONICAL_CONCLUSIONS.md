# Discovery Program — Canonical Conclusions (2026-07-11)

Canonical record of the two measurement experiments, refining the framing in the frozen
prereg Result sections (which remain frozen and unedited). Both were independently
reproduced from the frozen scripts (persisted outputs byte-identical); these verdicts are
not reporting artifacts. No strategy, threshold, portfolio, or deployment follows from either.

## EXP-A — REJECTED for the frozen free-data Treasury ETF implementation

The **primary ex-ante prediction test fails**: forward-21d return on carry z-score gives
coef = **+0.00143, t = 1.53** (below the registered |t|>2); rank IC is weak (+0.023, t=0.43);
**no tested horizon** (5/21/63d) reaches the threshold; and the **final 24-month holdout
reverses sign** (+0.0017 pre → −0.00089 holdout). These are the falsification gates, and they
fail on their own.

The forward-ΔDGS10 regression (M3, where the z-coef collapses to t=1.05 while duration×realized-
rate-move has t=−32.9) is **ex-post attribution only, not the primary falsification test**. It
supports the reading that realized returns were dominated by duration and rate moves, but the
hypothesis is already falsified by the ex-ante prediction and holdout gates above.

The nominal residual-alpha **t = 2.85 does not rescue** the hypothesis: the underlying signal
lacks stable predictive evidence, and the frozen Orthogonality Benchmark classifies the sleeve
**NOT INDEPENDENT**.

**Rolling-correlation failure, with context** (63d |corr| of the carry sleeve to the promoted
ensemble; threshold 0.65; n=5351 windows):

| field | value |
|---|---|
| median rolling correlation | **−0.219** (risk-off most of the time) |
| windows above threshold | **128 of 5351 (2.4%)** |
| longest continuous breach | **63 trading days** (2011-11-01 → 2012-02-01) |
| worst breach | \|corr\| **0.737**, window **2011-09-29 → 2011-12-28** (euro-crisis risk-off) |
| responsible book / factor | **long-duration Treasury (TLT) exposure** — co-moves 0.999 with dual_momentum_gem's TLT leg in risk-off; the promoted-ensemble breach is driven by defensive_ensemble's bond sleeve |

The breach is temporary and rare, but **the verdict is unchanged even if the breach were
ignored** — the primary prediction and holdout gates already fail. Bond carry (free-data
Treasury ladder) → Failure DB.

## EXP-B — MECHANISM UNSUPPORTED ON THE CURRENT PANEL

The four-property model (risk premium, vol clustering, return-vol asymmetry, drawdown
convexity) **does not pass the pre-registered cluster-level joint test**: Rademacher wild
cluster bootstrap, G=5, **joint p = 0.44**. (The naive iid-across-26-ETFs F, p=0.047, is
forbidden by the prereg — correlated markets are not independent confirmations.)

Three expected signs hold and the benefit concentrates descriptively in US equities and gold
(US-equity +4.0%, gold +5.7%, broad-intl/energy ~0-to-negative), which **narrows F-020**
(vol-management is not universal). But this does **not establish a transportable mechanism**.
**Volatility clustering is the strongest _descriptive_ predictor in this panel** (cluster-mean
corr +0.85, within-cluster t=2.26) — recorded as a descriptive fact on this ETF panel, **not**
as a generally proven robust predictor. No regime switch, strategy, or portfolio follows.

## FRED data-layer conclusion (scope preserved)
Sampled-vintage verification, not a universal all-date proof: the nine ingested rate/vol
series show no material vintage revisions at the tested observations (2020-06-01, 2023-03-15)
→ latest values carry no revision look-ahead; point-in-time validity still rests on the frozen
release-lag / market-calendar rules (measured lags confirm 1-bd rates, same-day vol). CPI/GDP
are revised and remain BLOCKED absent ALFRED point-in-time retrieval.

## Discovery Program → MAINTENANCE MODE
1. Continue prospective earnings-event collection (com.rimrim.earnings-collect, read-only).
2. Maintain the data layer and the Orthogonality Benchmark.
3. **Close the free-data Treasury carry lane.**
4. Reopening carry requires **materially better futures / term-structure data** — not more
   proxies on the same ladder (CARRY_FEASIBILITY.md).
5. **Do not reopen conditional vol-management** with nearby variables, thresholds, or ETF
   permutations on this panel — next reopen needs new markets/instruments.
6. All discovery work stays **outside the funded seven-book roster**.

## Canonical project state
- Existing strategy implementations are **mechanically credible** (red-team A–D).
- **Forward performance evidence remains near zero** (fills pending Monday's open).
- **No new independent alpha source has been validated.**
- **Free-data bond carry is rejected** in the tested form.
- Volatility management **remains useful in selected markets** but **lacks a validated
  transportable cross-asset mechanism**.
- **Point-in-time earnings and revisions remain the highest-value unresolved discovery lane.**

No additional broad hunt is authorized. The next meaningful evidence should come from **real
fills** and **prospective earnings data**.
