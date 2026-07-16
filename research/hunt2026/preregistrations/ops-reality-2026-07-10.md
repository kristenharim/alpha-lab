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
**Result** (filled after the run, never edited above this line): Night-1 run
(--since 2026-07-10) executed 2026-07-10 late evening: 0 h26 fills, 0 rejects — as
pre-registered, "no fills yet — nothing to measure" (304 open orders queued for Monday's
open, incl. the statarb flatten). 68 closed orders were all self-cancels from the day's
3 live re-runs (cancel_all_orders idempotency); the harness classifies these separately
from rejects — a measurement-harness fix made on night 1 before any fill existed, bands
untouched. Position gap 257% of notional is the expected pre-fill state (legacy statarb
book ~$150k gross still on until Monday). Harness + 8 offline tests green; row appended
to ledgers/hunt2026/_reconcile.jsonl. Bands untested until fills accrue; ACCUMULATING
nightly. Recommended wiring (Director to apply, one line in the plist): run
scripts/hunt_paper_reconcile.py right after hunt_paper_run.py --live in
com.rimrim.hunt2026-paper — an evening reconcile measures the previous run-date's fills.

**2026-07-16 — bands were never wired to alarms; now enforced. Thresholds unchanged.**
Discovered while investigating the 2026-07-15 cycle: the reconcile computed, stored and
PRINTED every band ("rate 100.0%, band < 2%") but only SILENT-FLAT and FOREIGN-POSITIONS
could ever raise an alarm. The registered bands were decorative for the life of the
experiment to date. Consequence: on 2026-07-15 all 19 h26 orders closed unfilled (Alpaca
expired the whole queued batch; account healthy, next session's identical code path filled
3 min after the open) — reject rate 100% against a 2% band, and nothing alarmed. That
night's non-zero exit came from an unrelated FOREIGN-POSITIONS alarm; had the flatten been
complete, a session that lost every order would have reported clean.
Now enforced exactly as registered above — no band, statistic, or threshold altered:
- Slippage: trigger is the trailing-mean statistic (>=20 fills/class) outside its band for
  10 consecutive nights (§Failure/kill). Per-night breaches remain logged-only. A negative
  streak reports the §Alternative-result reading (reference-close convention biased ->
  suspect the measurement, not an execution win). The alarm carries the registered remedy:
  flag the Director; never tune specs or the frozen cost model from inside this experiment.
- Reject rate: alarms the SAME night at >= 2% (the band above is "< 2% ... per night", so
  exactly 2% is a breach; the harness had used strict >).
DEVIATION, approved by Kristen 2026-07-16, recorded here rather than applied above:
read strictly, "per-night breach of any band is logged, not acted on" covers reject rate
too. It alarms same-night regardless. Rationale: that clause's stated reason is "overnight
noise is expected", which describes slippage's overnight drift and does not apply to a
night on which nothing traded; reject rate >= 2% is itself a listed Alternative Result
(sizing/tradability bugs); and silent-flat — the sibling operational failure — already
alarms immediately by registration. This changes WHEN an operational failure is surfaced,
not what is measured or any decision threshold.
Evidence the slippage wiring does not cry wolf: replaying all 4 sessions to date fires 0
slippage alarms. Trailing means sit at +5.8 bps stock / +2.3 bps ETF — both inside their
bands, i.e. the null holds so far. 2026-07-13 breached both bands on a single night
(streak 1, correctly silent) and reset to 0 on 2026-07-14; a per-night check would have
raised a false alarm there. Per-fill stdev is ~250 bps against a 15 bps band, as the
overnight-drift note above anticipated. Bands remain ACCUMULATING; no verdict claimed.
