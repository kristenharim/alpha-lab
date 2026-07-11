# PREREG H-D1 — MOC vs next-open fill point for the live vol-managed books

*Frozen 2026-07-10 (Agent 5, Experiment Engineer). Format extends
`research/hunt2026/PREREGISTRATION.md`. Nothing above the Result line may be edited
after the first scoring run.*

- **Experiment ID:** EXP-2026-07-10-moc-vs-moo-fill
- **Hypothesis ID:** H-D1-moc-vs-moo
- **Ranked:** EXPERIMENT_QUEUE.md #2 (high) · highest decision value on the board ·
  adjacent to director #2 (open+close execution) but **distinct** (measures the realized
  fill-point of the 3 LIVE books, not the F-006 overnight-premium book)

**Hypothesis** (one falsifiable sentence, mechanism included): The live 20:30 run computes
each book's weights from data through **close day d** and fills at the **next open**
(open d+1, `MarketOrder`/`TimeInForce.DAY`), so the mandatory overnight hold
(close d → open d+1) is a signed slippage correlated with the trade direction — when the vol
signal cuts exposure into a falling tape, the overnight gap systematically works against the
book — and a next-**close** (MOC, close d+1) fill of the same order removes that leak.

**Layer touched** (exactly one): **D — execution** (fill point only; the signal, estimator,
and portfolio weights are byte-identical between arms). Registered baseline: the **current
live fill policy** — weights from close d, filled at open d+1 — as run by
`scripts/hunt_paper_run.py --live` (20:30 weekdays, `paper=True`).

**Alpha type tag:** execution. This is **Execution alpha, not a market forecast** — a win
means we stop leaking a known gap, not that we predict anything new.

**Control (arm A, current live):** order submitted 20:30 day d → fills at **open d+1**.
Backtest realization: weights set on close d earn the book's return with the rebalance priced
at `open.shift(-1)` (open d+1).

**Treatment (arm B):** identical order (same close-d weights, same 20:30 submission) held for
the **next closing auction** → fills at **close d+1** (MOC). Backtest realization: rebalance
priced at `close.shift(-1)`. Both arms are fully realizable from a 20:30 run — neither peeks at
any d+1 data to form the weight.

**Universe:** the 3 promoted vol-management books and only their traded instruments —
`vol_managed_qqq`, `vol_core_svxy`, `trend_vol_qqq` (QQQ / SVXY / core-satellite ETFs + BIL),
from `BOOKS` in `scripts/hunt_paper_run.py`. Prices from `panel_2005.parquet` `open`/`close`
(both present, 2005-01-03 → 2026-07-10), ETF closes refreshed as the live runner does.

**Sample / train / eval (non-overlapping, holdout fixed BEFORE running):**
- Full backtest: 2010-01 → 2026-07 (post-ETF-liquidity era for QQQ/SVXY; SVXY starts 2011-10,
  its book measured from inception).
- Parameter-free (no fit — a fixed fill-point swap), so the primary paired-t runs on the full
  span. **Blind live-regime holdout:** 2022-01 → 2026-07 (the promoted family's live/eval era,
  includes the 2022 drawdown) — the sign of the fill-point delta must not flip there.
  Inspect/develop only on the pre-2022 span.

**Forecast + execution timestamps:** weight/forecast timestamp = **close d (16:00 ET)**, signal
data through close d, computed at the 20:30 ET run. Execution: arm A = **open d+1 (09:30 ET)**;
arm B = **close d+1 (16:00 ET MOC auction)**.

**Expected effect size:** the signed overnight-gap term
`Σ_i Δw_i · (open_{d+1}/close_d − 1)` averaged over rebalances. Prior: a few bps per rebalance,
directionally *against* arm A on the exposure-cutting trades (vol books de-lever into weakness).
Expected annualized net-return delta (B − A) ≈ +0 to +20 bps. Honest prior P(material) ≈ 0.4 —
overnight gaps are close to a random walk in liquid ETFs; the bet is the small trade-sign
correlation.

**Primary statistic:** annualized net return **and** net Sharpe of arm B minus arm A, per book,
with a **paired t-test on monthly return differences** (same weights, only fill price differs ⇒
naturally paired). **Secondary:** mean signed overnight-gap slippage per rebalance (bps) and its
t-stat vs zero (the direct leakage diagnostic); worst-12m delta; turnover unchanged check
(must be identical across arms — a guard that only the fill layer moved).

**Success condition:** arm B beats arm A on net return by a paired t > 2 in the pooled 3-book
test **and** the signed overnight-gap slippage of arm A is significantly negative (t < −2),
sign stable in the 2022+ holdout → the open fill leaks; **recommend the live books switch the
fill policy to next-close MOC** (paper-only change, routed through Kristen's Stage-4 gate — this
prereg does NOT modify any live spec).

**Failure / kill condition** (decidable, includes stop-iterating rule): |paired t| < 2 on net
return **and** |overnight-gap t| < 2 → **kill.** The open fill is unbiased; keep MOO, and
**also close H-D3** (adverse-gap deferral) — if the pooled gap is directionless, the tail-gap
variant has no base to stand on. Do not iterate further fill-point variants without intraday
data.

**Cost model:** spread + commission are **identical** across arms (same order, same instrument),
so they cancel in the B−A difference — the measured delta is purely the fill-point (gap) term.
Report the delta in bps/rebalance and annualized. No borrow (long ETFs). The live paper broker's
own fills provide a forward, real check via the ops-reality reconcile harness.

**Leakage checks:** the weight uses data only through close d in BOTH arms; arm B's close-d+1
fill price is a *future* price used only to fill, never to decide (no look-ahead in the signal).
Explicitly assert `turnover_A == turnover_B` per rebalance (identical target weights) — any
difference means the arms diverged in more than the fill layer.

**Survivorship checks:** ETF-only books (QQQ, SVXY, BIL) — no delisting/survivorship exposure;
SVXY measured from its real inception (no backfill before 2011-10). `panel` ETF closes are
ffilled across holidays exactly as the live runner does (no synthetic pre-inception history).

**Runtime estimate:** ~15 s (two NAV passes over 3 books, reusing `_nav`). **Complexity score:**
2/5 (~40-line offline harness that re-prices each book at `open.shift(-1)` vs `close.shift(-1)`;
no change to `hunt_paper_run.py`, no `--live`).

**Information-gain estimate:** HIGH decision value — directly actionable on 3 live paper books;
chains onto the ops-reality reconcile harness which confirms the same gap forward from real
paper fills. Either branch is decisive.

**Trial count:** adds **TRIAL_LEDGER.md #20** (execution measurement on live books; tag =
execution / measurement) in the same commit. Adaptive-loop flag: informed by the live
deployment state (CANONICAL_STATE §2–3) ⇒ **yes** — note in the hunt-level ledger.

**Derived from prior holdout results?** No backtest-holdout ancestry; motivated by the live
fill mechanics (open-fill from a 20:30 run) documented in CANONICAL_STATE. Not an adaptive loop
over a prior OOS score.

---
**Result** (filled after the run, never edited above this line):
