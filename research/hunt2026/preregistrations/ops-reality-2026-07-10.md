# Pre-registration — EXP-OPS-REALITY: do paper fills agree with the frozen cost model?

### EXP-2026-07-10-ops-reality

**Hypothesis** (one falsifiable sentence, mechanism included):
The frozen backtest execution model (10 bps/side stocks, 2 bps/side ETFs, next-day fills
at reference close, zero rejects — harness.py per_side_bps) is an adequate description of
the real Alpaca-paper execution of the 7-book aggregate: measured costs, reject rates, and
per-book NAV drift will sit inside the agreement bands below, because the book is small
(~$100k notional), liquid (large-cap ETFs + S&P members), and traded once daily as market
orders.

**Layer touched** (exactly one — D execution) + registered baseline:
Layer D. Baseline = the frozen harness cost model itself (10/2 bps per side, next-day
close fills, no rejects). No spec, weight, or deployment is changed by this experiment;
it only measures the gap between model and broker. Measurement harness:
scripts/hunt_paper_reconcile.py, strictly read-only against the broker (it never submits
or cancels anything).

**Alpha type tag**: execution

**Expected result** (numeric, on which evaluator — the reconcile harness's own output,
one JSONL row per night in ledgers/hunt2026/_reconcile.jsonl):
1. Slippage per fill = side-adjusted (fill_price − run-date ledger reference close)/close,
   in bps; positive = paid more than model. Because fills happen at the next open, single
   fills embed overnight drift (±50 bps noise is normal); the model-agreement statistic is
   therefore the trailing mean over the last ≥20 fills per class. Agreement bands:
   trailing-mean slippage in [0, 15] bps for stocks, [0, 5] bps for ETFs.
2. Rejected-order rate < 2% of h26-tagged orders per night.
3. Per-book tracking error — cumulative slippage drag allocated to each book by its share
   of the aggregate target in each symbol — < 30 bps of book notional per rolling month.
4. Silent-flat alarm: any book with nonzero ledger targets whose symbols show zero fills
   AND zero held position for 2+ consecutive reconcile nights fires an alarm. Expected
   count: 0.
Night 1 (2026-07-10, orders queued for Monday's open): expected honest output is
"no fills yet — nothing to measure". The harness existing, tested, and running is this
experiment's deliverable; measurements accrue nightly.

**Alternative result** (what the world looks like if the hypothesis is false):
Trailing-mean slippage persistently outside the bands (e.g. ETFs > 5 bps or negative
beyond −5 bps, meaning the reference-close convention itself is biased), reject rate ≥ 2%
(sizing/tradability bugs), a book drifting > 30 bps/month from its model NAV (pro-ration
or aggregation bug, or cost model materially wrong), or a silent-flat book (submission
path silently dropping a book). Any of these means the frozen backtest numbers overstate
what the paper account actually earns.

**Failure / kill condition** (pre-committed; decidable from _reconcile.jsonl):
- Per-night breach of any band is logged, not acted on (overnight noise is expected).
- DECISION TRIGGER: any band breached on the trailing statistic for 10 consecutive trading
  nights, or any silent-flat alarm → flag to Research Director. The remedy is NEVER to
  tune specs or edit the frozen cost model from inside this experiment; the Director
  decides whether to re-price the cost model repo-wide.
- Stop-iterating rule: this harness gets no parameters to sweep. One measurement
  convention (registered above), fixed forever; if the convention itself proves wrong,
  that is a new pre-registered experiment, not an edit to this one.

**Trial-ledger row**: TRIAL_LEDGER.md — robustness/operational-experiment row added in the
same commit (1 experiment, 0 spec variants, thresholds fixed before any fill existed).

**Derived from prior holdout results?** No — purely operational; it reacts to the books
going live (Kristen's 2026-07-10 gate), not to any out-of-sample performance number.

---
**Result** (filled after the run, never edited above this line): pending.
