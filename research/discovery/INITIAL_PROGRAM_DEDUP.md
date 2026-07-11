# Initial Program (Experiments 1–5) — deduplication & status

*Mandated first step (charter § 6, Failure/Dedup Reviewer): reconcile the 5 required
experiments against the Trial Ledger, Failure DB, Research Objects, Red-Team findings, and the
already-completed prereg batch BEFORE new work. Verdicts use the charter vocabulary.*

**Headline:** the Discovery Program is **data-gated, not idea-gated.** Two of the five are
buildable now (Exp 5 done, Exp 4 audit); the three highest-value market lanes (Exp 1, 2, 3) are
**BLOCKED BY DATA** with a single cheap unblock — FRED/VIX ingest, then let the PIT-earnings
collector accrue. This matches [../independent_alpha/DATA_GAP_MAP.md](../independent_alpha/DATA_GAP_MAP.md) §4.

| Exp | title | dedup verdict | status | evidence / pointer |
|---|---|---|---|---|
| **1** | Forward earnings-surprise IC | APPROVE (highest-priority lane) | **BLOCKED BY DATA** | Finnhub PIT collector live + read-only, ~8 events vs registered n≥300 gate. Historical backfills are revised-vintage (look-ahead) and excluded from the primary prospective test per charter. Docketed: EXP-IC-EARNINGS-FWD (accruing) + HYP-A4-01/03/04. **Action: accrue to n≥300, then run the pre-registered IC test. Do NOT build a portfolio first.** |
| **2** | Open/close event implementation | NEEDS DIFFERENTIATION → resolved | **harness BUILT; event application BLOCKED BY DATA** | The open-vs-close *harness* exists — `../independent_alpha/experiments/hd1_moc_vs_moo.py` reprices books at `open.shift(-1)` vs `close.shift(-1)`. Its generic test on the vol books (H-D1) = **KILL** (fill directionless, net t=0.17, gap t=1.25). Event-signal entry needs Exp-1 PIT events → blocked. Charter caution ("overnight premium ≠ profitable after 2 executions") already confirmed (F-006/F-019, H-D2). |
| **3** | Conditional volatility management | APPROVE (sanctioned conditional reopen of F-020) | **pre-registerable now; BLOCKED BY DATA (FRED/VIX)** | = **H-E3** (EXPERIMENT_QUEUE #13, highest decision value). F-020 already rejected *universal* vol-management (3/7 cross-market); this tests *which observable asset properties* (positive risk premium, vol clustering, negative return-vol asymmetry, vol-linked drawdowns) explain where it helps — a mechanism test, NOT ranking ETFs by performance. **Conditions must be pre-registered before evaluation; needs FRED rates + a real ^VIX/VIX3M series (not on disk).** |
| **4** | Carry data feasibility | APPROVE (new, actionable — a data audit, not a strategy) | **DONE (audit)** | [CARRY_FEASIBILITY.md](CARRY_FEASIBILITY.md): bond-carry slice is feasible now (FRED, free, PIT-clean, tradable via IEF/TLT/SHY, low equity beta = the diversifying prize); FX/commodity/full x-asset carry BLOCKED BY DATA (vendor term-structure); vol-carry flagged NOT-INDEPENDENT-risk vs the existing vol cluster. |
| **5** | Orthogonality benchmark | APPROVE (new, foundational) | **DONE — permanent gate live** | [orthogonality_benchmark.py](orthogonality_benchmark.py) + [ORTHOGONALITY_BENCHMARK.md](ORTHOGONALITY_BENCHMARK.md). Scores any candidate vs SPY+QQQ+the 7 books; reports max corr, residual-α t, residual Sharpe, crisis contribution, incremental ensemble Sharpe (block-bootstrap). Self-check passes. Every Stage-4 candidate must clear it. |

## What this means for sequencing
1. **The one action that unblocks the most:** ingest & validate FRED (rates/curve) + a real
   ^VIX/VIX3M series (timestamp + leakage checks). Unblocks Exp 3 **and** the bond-carry slice of
   Exp 4 — the cheapest real gap (DATA_GAP_MAP §4 #1).
2. **Keep the PIT-earnings collector accruing** toward n≥300 (Exp 1 / Lane 1, the highest-priority
   lane). Enabled + read-only, gated for deployment (DEPLOYMENT_MANIFEST).
3. **Everything measurable on in-repo price/volume is exhausted** — the just-run batch killed the
   last daily-bar reversal reopen (H-E1) and the fill-point question (H-D1). Do not open more
   price/volume probes; the reopen condition is new data (charter § 5).
4. **Nothing here promotes to funded paper.** Any survivor exits via Research Director → Red Team
   → Stage-4 only.
