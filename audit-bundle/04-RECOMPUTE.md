# RECOMPUTE — every headline number, re-derived from the raw return series

All figures below were recomputed directly from `05-residual-return-series.csv` (the daily net-of-cost
PnL series each backtest wrote), using the functions in `03-CODE.md`. If you want to re-derive them
yourself, that CSV + these formulas are sufficient — you do not need to trust the stated numbers.

## Definitions / formulas
- **Sharpe (annualized):** `mean(net) / std(net, ddof=1) * sqrt(252)`.
- **Ann. return:** `mean(net) * 252` (net is a daily simple return on the notional book).
- **Max drawdown:** on `cumprod(1+net)`.
- **Deflated-Sharpe prob:** Bailey & López de Prado (2014); `n_trials=20`, adjusts for skew/kurtosis and
  the expected max Sharpe of 20 zero-skill trials. Code in `metrics.py::deflated_sharpe`.
- **Premium spread:** `full_net − floored_net`, aligned on common dates; its own Sharpe.
- **Sharpe SE (Lo 2002, iid):** `sqrt((1 + 0.5*SR_pp^2)/n) * sqrt(252)`, `SR_pp = SR_ann/sqrt(252)`.
  95% CI = `SR_ann ± 1.96*SE`. (iid SE — see caveat below.)

## Headline stats (recomputed)

| series | Sharpe | Ann.ret | MaxDD | Hit | Deflated p (n=20) | n | Lo-SE |
| ------ | ------ | ------- | ----- | --- | ----------------- | - | ----- |
| full_survivor  | 2.666 | 12.50% | −6.30% | 60.10% | 1.0000 | 2015 | 0.356 |
| floor3.0_surv  | 2.567 | 11.46% | −5.12% | 59.65% | 1.0000 | 2015 | 0.356 |
| floor2.5_surv  | 2.311 | 10.07% | −4.51% | 58.76% | 1.0000 | 2015 | 0.356 |
| floor2.0_surv  | 1.857 |  7.83% | −4.30% | 57.62% | 0.9995 | 2015 | 0.355 |
| floor1.75_surv | 1.708 |  7.12% | −4.33% | 57.12% | 0.9981 | 2015 | 0.355 |
| full_pit       | 2.500 | 11.51% | −5.49% | 58.36% | 1.0000 | 2015 | 0.356 |
| floor2.0_pit   | 1.686 |  7.15% | −5.04% | 56.77% | 0.9976 | 2015 | 0.355 |

Subperiods (each full book split in half):
- `full_survivor`: 2018-06-27→2022-06-27 **2.91** | 2022-06-28→2026-07-06 **2.40**
- `full_pit`:      2018-06-27→2022-06-27 **2.67** | 2022-06-28→2026-07-06 **2.31**

## Premium spread (full − floored @ floor 2.0) — Sharpe + 95% CI

| universe | premium Sharpe | Lo-SE | 95% CI | ann. |
| -------- | -------------- | ----- | ------ | ---- |
| survivor | **2.980** | 0.357 | **[2.281, 3.680]** | 4.678% |
| PIT      | **3.265** | 0.357 | **[2.565, 3.966]** | 4.363% |

## Adjudication of the two flagged findings

### Finding 1 (premium-CI attribution) — RESOLVED, no error in the committed spec
The spec (`02-design-spec.md`) assigns survivor premium CI = **[2.28, 3.68]** and PIT = **[2.56, 3.97]**,
and anchors the 12-month timeout to the PIT lower bound **~2.56**. The recomputation above reproduces
exactly those numbers. The committed spec is internally correct. The transcription slip existed only in
an earlier chat message that printed the PIT CI without labeling it — it never entered the spec or the
decision rule.

### Finding 2 (is 1.7 a lower bound?) — CONCEDED: 1.7 is NOT a clean floor
This is the substantive one and the concern is correct. The floored Sharpe (1.71 survivor / 1.69 PIT)
was measured on a universe that still **omits the 120 delisted names** (no free price data). Flooring
removes deep-dip (s<−2) longs — the *primary* survivorship channel — but the floored book still carries
two residual survivorship-exposed channels that the survivor data cannot penalize:
1. **Short leg** — a dead name acquired at a premium gaps UP against a short; that loss is absent.
2. **Shallow longs that deepen** — a long entered at −1.25≤s≤−2 that then craters toward delisting is
   stopped out at −2 at a *clean* survivor price; a real dead name would gap/halt through the stop.

Therefore the honest bracket is **not** `1.7 ≤ true ≤ 2.5`. It is:
- **2.50** = loose upper bound (PIT membership, survivor prices).
- **1.71** = *tighter* upper bound (main channel removed) — **not** a proven lower bound.
- **true ≤ 1.71**, and possibly below it; the residual gap = short-side + shallow-long survivorship
  channels (smaller than the deep-dip channel, but nonzero and unquantifiable on free data).

Implication: the spec's "robust core / lower bound / adopt 1.7 as the planning number" framing is
optimistic and should be softened. The forward paper test remains the only construct that establishes a
*real* floor (it experiences every dead-name loss across all channels). **This finding is conceded pre-
audit; an independent model should still stress-test the magnitude reasoning.**

## Known caveats an auditor should weigh (not errors, but soft spots)
- **iid Sharpe SE.** The Lo (2002) SE assumes iid returns. Mean-reversion PnL is mildly autocorrelated,
  so the true SE is likely a bit wider than 0.357 → the premium CIs are slightly optimistic (tighter
  than reality). Does not change the qualitative conclusion but worth noting.
- **Deflated-Sharpe n_trials=20 is a declared count, not audited.** The real search space (mega vs wide
  vs PIT × entry/exit/window/floor params) is larger; the true deflation is harsher than n=20 implies.
- **Premium Sharpe ~3.0 is an in-sample difference of two thresholded strategies on the same data** —
  structurally prone to looking cleaner in-sample than it will live. That is the whole reason for the
  forward test.
