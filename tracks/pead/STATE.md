# STATE — PEAD → PEAD.txt (extends vault HYP-001)

**Stage:** 1 complete (numeric event study run on real data); Phase 2 (text) not started
**Last session:** 2026-07-06

## Built
- `events.py` — SUE proxy = (actual − estimate) / |estimate|, floored; `fetch_earnings_yf`
- `event_study.py` — CAR matrix around events, top-minus-bottom SUE-quintile drift spread
- `universe.py` — 60 large caps (survivorship-biased placeholder)
- `scripts/pead_run.py` — full run → `artifacts/pead/{events,cars}.parquet + drift.md`
- Tests 2/2 green.

## First result (2026-07-06, 539 events, 2024-01 → ~2026-04)
| Horizon | Top−Bottom SUE quintile CAR |
| ------- | --------------------------- |
| +5d  | 4.52% |
| +20d | 5.89% |
| +60d | 8.45% |

Monotone increasing drift — textbook PEAD direction and shape.

## HONEST CAVEATS (do not treat this as validated alpha)
1. **Survivorship bias**: universe = today's large caps. These names disproportionately
   rose over 2024–2025; positive-surprise firms drifting up is partly "winners kept winning."
2. **Risk adjustment is crude**: abnormal return = ret − SPY, no beta, no size/value controls.
   A proper test needs FF factor-adjusted CARs.
3. **No trading costs / no portfolio**: this is an event-study CAR spread, not a net-of-cost
   backtestable strategy yet. Stage 3 must build a calendar-time portfolio through the
   core backtest engine and score it.
4. Small universe (60) → wide quintiles are thin (~5 names each per event bucket).

## Next
1. **HYP-001 upgrade memo** in vault (link this result + caveats).
2. Stage 3: FF-factor-adjusted CARs; calendar-time L/S portfolio → core scorecard (net of cost).
3. Broaden universe / get point-in-time membership (WRDS/CRSP) to kill survivorship bias.
4. Phase 2 (PEAD.txt): earnings-call transcripts (Refinitiv/CapIQ export) → SUE.txt via
   regularized logistic text regression; compare text drift vs numeric drift head-to-head.
