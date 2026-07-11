# Experiment 4 — Carry data feasibility audit

*A data & measurement audit, NOT a trading strategy (charter § 10). Question: can Alpha Lab
build a point-in-time, implementable carry dataset with valid financing and roll assumptions?*
*Verdict per source below; overall: **bond-carry slice feasible now (free); rest BLOCKED BY DATA**.*

Carry = expected return from holding, absent price change (roll-down + yield/financing spread).
Its appeal for this program is **low equity beta** — a real carry source would be orthogonal to
the entire QQQ/trend/vol cluster (the diversifying prize). The risk is that the only carry
instruments already on disk (SVXY/VXX) are *already inside* the vol cluster, so a naive vol-carry
book would fail the orthogonality gate.

| carry type | data needed | availability | PIT / leakage | implementable | verdict |
|---|---|---|---|---|---|
| **Bond / rates carry** (curve slope + roll-down) | constant-maturity yields (DGS3MO, DGS2, DGS10), fed funds for financing | **FREE — FRED**, deep history, daily | FRED daily CMT revised minimally; use ALFRED vintages for a strict PIT check | **yes** — IEF/TLT/SHY (on disk) or Treasury futures | **FEASIBLE NOW** (needs FRED ingest) |
| **Vol carry** (VIX vs VIX3M term structure, roll) | ^VIX, ^VIX3M, VXX/SVXY | ^VIX/^VIX3M free (not on disk); SVXY/VXX **on disk** | daily, clean | SVXY/VXX (decay IS the carry) | **NOT-INDEPENDENT RISK** — already captured by `vol_core_svxy`'s SVXY sleeve; must clear the orthogonality gate vs the vol cluster before counting |
| **FX carry** (short-rate differential / forward points) | FX spot + forward points or foreign short rates | rates partly FRED; forward points need a vendor | forward points vendor-gated | UUP/FXE (ETF decay) or FX futures | **BLOCKED BY DATA** (clean forward points) |
| **Commodity carry** (futures term structure, front vs next) | futures curve (front/next contract) | **not on disk**; ETFs (USO/DBC) have roll decay that *contaminates* the signal | needs contract-level PIT | commodity futures or curve-aware ETFs | **BLOCKED BY DATA** (vendor term structure) |

## Mandatory modeling (charter § Lane 3) — what any carry book must include
financing (fed funds / repo), roll mechanics (constant-maturity approximation vs actual contract
roll), ETF decay (USO/VXX are not buy-and-hold), borrow (short legs), instrument inception
(no synthetic pre-inception history), liquidity, transaction costs. Absent these, carry backtests
are fiction.

## Recommendation
1. **Build the bond-carry slice first** — it is the only carry source that is free, PIT-clean,
   implementable with instruments already on disk, and plausibly low-equity-beta. Concretely:
   ingest FRED (DGS3MO/DGS2/DGS10 + DFF), construct curve-slope + roll-down signals, map to a
   long/short IEF-TLT-SHY (or BIL) sleeve, model financing + roll, then **run it through
   [orthogonality_benchmark.py](orthogonality_benchmark.py)** before any portfolio claim. This is
   the same FRED ingest that unblocks Exp 3 — one data task, two experiments.
2. **Defer FX & commodity carry** — BLOCKED BY DATA until a term-structure/forward-points vendor
   is justified (don't fabricate from decaying ETFs).
3. **Treat vol carry with suspicion** — pre-check orthogonality vs `vol_core_svxy`; if
   `max_corr_to_book` > 0.5 it is NOT INDEPENDENT and not a discovery.

**Status: BLOCKED BY DATA for FX/commodity/vol; the bond-carry slice is unblocked by the single
FRED ingest already ranked #1 in DATA_GAP_MAP §4.** No strategy built — audit only, as mandated.
