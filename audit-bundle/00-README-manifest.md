# Audit bundle — residual-reversion backtest + paper-book design (HYP-005)

Upload these files to a second (ideally different-family) LLM to independently verify the data and
reasoning. The point is **recomputation**, not re-reading: the raw return series are included so the
auditor can redo the arithmetic rather than trust stated numbers.

## What each file is

| File | What it is | Use it to audit |
| ---- | ---------- | --------------- |
| `00-README-manifest.md` | this file | orientation + claim map |
| `01-STATE-statarb.md` | the research journal / results of record (pairs, residual, PIT, falling-knife) | every stated Sharpe/claim — the source of truth for what was concluded |
| `02-design-spec.md` | the Stage-5 paper-book design (the forward test that resolves the bracket) | internal logic of the design + the resolution rule |
| `03-CODE.md` | concatenated source of every function behind the numbers | methodology: look-ahead, cost model, s-score, PIT mask, floor logic, Sharpe/deflated-Sharpe |
| `04-RECOMPUTE.md` | every headline number re-derived from the CSV + formulas + my adjudication of the two flagged findings | check the arithmetic; see which findings are already conceded |
| `05-residual-return-series.csv` | daily net PnL, 2015 rows × 7 books (full/floored×4/pit/pit-floored) | recompute Sharpe, subperiods, premium spread + CI from scratch |
| `05b-pairs-return-series.csv` | daily net PnL for the (dead) pairs strategy | the pairs numbers in STATE, if audited |

## The claims most worth an independent recompute
1. **The 2.67 baseline** and its collapse under corrections (2.67 → 2.50 PIT → 1.71 floored). Recompute
   from `05-...csv`.
2. **The premium spread CI** ([2.28,3.68] survivor / [2.56,3.97] PIT) — the anchor of the 12-month
   resolution timeout. Recompute; check the Lo-2002 SE and the iid assumption.
3. **Deflated-Sharpe / multiple-testing** honesty (n_trials=20 declared vs the true search space).

## Two findings already adjudicated (stated so the auditor can confirm or refute, not to pre-empt)
- **Finding 1 — premium-CI attribution:** RESOLVED. Recomputation confirms the committed spec is
  correct ([2.28,3.68] survivor, [2.56,3.97] PIT). The slip was in chat narration only. (`04-RECOMPUTE.md`)
- **Finding 2 — is 1.7 a lower bound?:** CONCEDED. It is not a clean floor — the floored book still omits
  the dead names via the short leg and shallow-long stop-outs, so `true ≤ 1.71` (possibly lower), not
  `1.7 ≤ true`. This weakens the "defensible 1.7 core" language in the spec. An independent model should
  still stress-test the magnitude argument. (`04-RECOMPUTE.md`)

## Notes for whoever runs the audit
- **Two audit levels are supported by this bundle:** (a) *full* — with all files, most claims become
  "redo the arithmetic"; (b) *design-only* — hand over just `02-design-spec.md` (+ optionally this
  manifest) to a reviewer with no artifacts, to audit the spec's internal logic in isolation.
- **The implementation plan does not exist yet.** Work paused at the approved-spec stage; the
  `writing-plans` step has not run. If the audit prompt references an "implementation plan / task list,"
  that is not in this bundle because it hasn't been written. Ask if you want it generated and audited too.
- Expect false positives — a cold model will object to some deliberate choices (equal-weight, EOD-only,
  iid SE). The output is a list of suspicions to adjudicate, not a verdict.
