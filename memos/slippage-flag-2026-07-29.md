# FLAG to the Deployment Coordinator / Research Director — SLIPPAGE-STOCK, SLIPPAGE-ETF, MC-DRAG lit on 2026-07-28

**From:** rimrimOS evening routine (Section 5, read-only book check), escalated at Kristen's request 2026-07-29
**Type:** flag + proposal. **No control-plane file was touched.** Nothing here has been fixed and nothing should be until you rule on it.
**Related:** `memos/mc-drag-flag-2026-07-16.md` (item 5 still open) · `memos/band-ruling-2026-07-21.md` (the standing ruling)

## The alarms

`scripts/paper_status.py` on the 2026-07-28 session (reconcile `2026-07-28T20:31:07`):

```
!! SLIPPAGE-STOCK: trailing mean +228.2 bps outside the [0, 15] bps band for 10 consecutive nights
!! SLIPPAGE-ETF:   trailing mean  +50.5 bps outside the  [0, 5] bps band for 10 consecutive nights
                   — splits into +51.9 bps overnight drift and -1.4 bps execution
!! MC-DRAG:        trailing ~1mo tracking drag -84.1 bps outside the ±30 bps band
```

Everything else is clean: 7/7 books, run HEALTHY, scheduler OK, four-part flatten gate COMPLETE, 0 rejects.

## Headline: none of the three is news about execution quality, and one of them is measuring nothing

The short version is that the 7/21 ruling already predicted all of this, and the "10 consecutive nights" framing is doing real damage to the signal. Details below, each independently checkable from the ledger.

### 1. SLIPPAGE-STOCK is a frozen sample being re-counted, not a 10-night trend

The trailing window is 20 fills. **Every one of them is from 2026-07-14 (4 fills) and 2026-07-15 (16 fills).** There has not been a single stock fill since 07-15, nine sessions ago. The statistic has been literally unchanged since then.

The breach counter nevertheless increments every night, because it re-tests the same stale mean against the band each session with no freshness condition:

| reconcile date | n_fills | breach nights (stock) |
|---|---|---|
| 2026-07-22 | **0** | 6 |
| 2026-07-23 | 3 | 7 |
| 2026-07-24 | 2 | 8 |
| 2026-07-27 | 3 | 9 |
| 2026-07-28 | **0** | 10 |

Two of those ten nights had zero fills of any class. "10 consecutive nights out of band" reads as accumulating evidence; it is one two-day sample counted ten times. The pre-registered trigger is `SLIPPAGE_BREACH_NIGHTS` consecutive nights, and it fired on persistence that does not exist.

### 2. On the stock fills that carry the split, execution is free

The split is withheld from the alarm text only because 4 of the 20 fills predate the `drift_bps` field (the four 07-14 fills), and `trailing_means` reports the split only when every fill in the window carries it. Computed over the 16 fills that do carry it:

| stock, 16 split-carrying fills | bps |
|---|---|
| mean slippage | +251.2 |
| mean overnight drift | +253.5 |
| **mean execution** | **-2.4** |

Execution is **-2.4 bps**, materially identical to the ETF book's -1.4 bps. The entire +251 bps is the overnight gap the fill inherited before it could cross, which is exactly the structural contamination §1 of the 7/21 ruling described. The band is [0, 15] on a statistic that has one full overnight gap baked in by construction.

**Caveat, stated explicitly:** this is the *shared account's* stock class. It does **not** resolve the open question in §1 of the 7/21 ruling, which was about the *dedicated `momentum_concentrated` account's* single-name execution (+53, +113, +36 bps over 25 fills). Those are different books and I did not merge them. MC's own trailing fill window is currently empty (n=0), so that question stays open.

### 3. SLIPPAGE-ETF is the already-ruled case, firing again

ETF window spans 07-17 through 07-27, six sessions, full split coverage, so unlike stock it is a live sample. +50.5 = +51.9 drift and -1.4 execution. That is §1 of the 7/21 ruling restated verbatim: on the shared ETF book execution costs essentially nothing and band breaches are drift. No new decision appears to be required here.

### 4. MC-DRAG is flag item 5 from 07-16, still unaddressed

`drag_bps_trail` currently holds **10 entries, not 20**:

```
[-87.9, -4.2, 1.8, 3.8, -0.7, -1.6, 23.0, 7.5, -25.8, 0.0]   sum = -84.1
```

A single session (-87.9) accounts for more than the whole breach; the other nine net +4. This is the same shape as the 07-16 breach that the 7/21 ruling attributed to one true build-out event and chose to let age out. Item 5 of the original flag asked that the alarm stop calling a partial window "trailing ~1mo"; that item was explicitly left standing and is now producing its second misleading headline.

## What I am asking for

Not a band change. Widening a threshold to quiet a statistic that is behaving as designed would be the wrong move, and §2 of the 7/21 ruling already declined to re-derive the band absent a decision that depends on it.

1. **Rule on whether the breach-night counter should require a fresh sample.** The candidate condition is that a night with no new fills in the class neither increments nor resets the streak. As written, an idle book manufactures a decision trigger. This is the one I would actually change, and it is Coordinator-owned.
2. **Decide whether the split should be reported on a partial window.** Withholding it when 4 of 20 fills are legacy rows hid the -2.4 bps execution figure, which is the single most decision-relevant number in the stock alarm. A `split_n` disclosure alongside a partial mean would have surfaced it without mixing samples.
3. **Consider whether the stock band [0, 15] is meaningful on a drift-contaminated statistic**, given the frozen definition scores every fill against the prior close and the pre-registration budgeted ±50 bps of drift against a tape moving 3 to 5 percent a session. An explicit ruling, as in §2 of the 7/21 note, beats silent re-breaching.
4. **MC-DRAG: rule on the "trailing ~1mo" label for a 10-entry window** (flag 07-16 item 5, still open).
5. **Separately worth knowing:** there have been no stock fills in nine sessions. I did not investigate why and it may be entirely intended by the roster, but it is the kind of thing that should be deliberate rather than discovered through a stale alarm.

## Provenance

- Read-only throughout: `scripts/paper_status.py`, plus direct reads of `ledgers/hunt2026/_reconcile.jsonl`, `ledgers/hunt2026/_reconcile_mc.jsonl`, and `scripts/hunt_paper_reconcile.py`.
- No writes to `scripts/hunt_paper_run.py`, `DEPLOYMENT_MANIFEST.md`, `research/hunt2026/STATUS.md`, `ledgers/hunt2026/*.jsonl`, or any scheduler plist. No trading script was executed.
- All figures recomputed from the ledger rather than taken from the alarm strings; the stock split was computed by hand over the 16 qualifying fills because the reconcile withholds it.

---

# RESOLUTION — 2026-07-30, after an LLM-council ruling

Four rounds of the cross-model gate produced four blockers/majors, **every one of them a
false-alarm suppressor that deleted a true alarm**, and every one inside the retirement machinery
rather than the original counter fix. The council was asked to rule on the open threshold question
and on scope, and rejected the framing:

> The four rounds indict *inferring alarm-relevant state from live data inside the subsystem that
> reports pass/fail* — not retirement as a concept.

## What was actually shipped

Branch `slippage-freshness-minimal`, cut fresh from `main`. **89 lines of source** (previous
branch: 262, plus 9 in `paper_status.py`).

1. **The counter fix.** A window is under test only when `FRESH_MIN_FILLS` of its fills come from
   the last `STALE_WINDOW_SESSIONS` sessions. Otherwise the streak counts **zero** — not a held
   value, not a banked one. A frozen window produces no nights of evidence, and every attempt to
   carry a count across the gap ended up spending pre-freeze nights as though they were fresh.
2. **`SLIPPAGE-<CLS>-UNTESTED`, a coverage alarm in the `alarms` list.** Not a breach: it says the
   band is not being measured. It lives in `alarms` because that is the only channel
   `paper_status.exit_code` reads — a "standing state" line that renders without touching the exit
   code reports green on an untested band, which is exactly how round 3 shipped a live breach as
   green. This also closes the open threshold question: below ~2 fills/session the pre-registered
   trigger is undefined, and now says so out loud instead of failing silently.
3. **`RETIRED_CLASSES`, a hand-declared set.** Currently `{"stock"}`, with the cutover memo cited
   in the comment. A human edits it when a book actually moves, and that edit IS the
   acknowledgement that silences the coverage alarm. **Retirement suppresses the coverage alarm
   only** — fills in a retired class are band-tested in full, because liquidation and wind-down
   trades are where execution quality is worst.
4. Kept from the original ruling: the partial split reported with `split_n` and named as its own
   average rather than a decomposition of a mean over a different sample; both halves required for
   selection (the `KeyError`); the MC-DRAG window label; `abs(gap) >= 0.5` on MC-POSITION-GAP.

**Correction to an earlier draft of this section.** It claimed retired classes stay band-tested
and that ETF alarms at 12 nights. The first was false as written — the coverage gate was branching
past the breach check, so a retired *or* under-watched class could not report a breach at all, at
any fill rate. The gate caught it; both are fixed and the guarantee is now asserted at 1
fill/session, the rate that actually breaks it, rather than at 10.

**A real finding fell out of the honest counting.** Replaying the full ledger with quiet nights
holding instead of incrementing puts the ETF streak at **9, not 12**. Three of the twelve
"consecutive nights" were sessions with no ETF fill at all. The ETF breach is real and still out of
band at +31.1 bps, but it has **not** legitimately reached the pre-registered trigger — it is one
genuine breach night away. The escalation that has been showing in the nightly status was partly
inflated by the same bug this change removes.

So on the live ledger today there are **no slippage alarms**: stock is hand-acknowledged as
retired, and ETF is at 9/10 honest nights. The round-3 repro — two quiet ETF sessions — yields
`SLIPPAGE-ETF-UNTESTED` in `alarms` rather than green. 275 passed, 1 skipped.

**One review finding was declined, not missed.** The gate flagged that an unknown-only
`MC-POSITION-GAP` night skips the alarm block. `test_unpriceable_prior_target_is_unknown_not_zero`
pins the opposite deliberately: a leg the PRIOR row could not price is unknown, not a gap, and
counting it fired a full-book alarm on a clean book. Overturning that is a ruling, not a cleanup,
so it stands and is recorded here for Kristen.

## What was dropped, and why it is recorded rather than deleted

`fix-stale-slippage-window` is left intact, unmerged, as the record of what inference cost. Its
retirement machinery derived liveness from rosters, book counts, fill presence and fill pricing;
each derivation was individually reasonable and collectively produced four blockers. The lesson is
narrower than "don't model retirement": **do not infer, from live data, a fact that decides
whether an alarm fires — declare it.**

---

# OPEN DECISION FOR KRISTEN — the pre-registration says "consecutive", the book does not fill daily

Five review rounds have converged on one irreducible problem. The pre-registered trigger is
*"the band breached on the trailing statistic for `SLIPPAGE_BREACH_NIGHTS` **consecutive nights**"*.
Every possible implementation of that sentence breaks something, because the pre-registration
assumed a book that fills every session and none of these books do:

| On a night with no fill | Consequence |
|:--|:--|
| **increment** | one frozen sample counted as eleven nights — the original 2026-07-28 bug |
| **reset to 0** | a bursty class never reaches 10 and its real breach disappears — a regression against `main`, verified at 60 sessions producing 0 alarms |
| **hold** (current) | ten breach observations separated by arbitrary gaps satisfy a trigger whose text says *consecutive* — the count is honest, the **word** is not |

There is no fourth option. This is not an implementation defect left to fix; it is the
pre-registration meeting a fill pattern it did not anticipate. **Amending it is Kristen's call**,
and §Stop-iterating forbids the harness from re-tuning its own spec.

Two candidate amendments, both cheap once ruled:

1. **Re-word to what is actually counted** — "N breach nights among sessions this class filled".
   Keeps every existing number valid, admits gaps, requires editing the pre-registration text.
2. **Add a gap bound** — consecutive *filling* sessions, with the streak reset if the class goes
   more than K sessions without filling. Preserves the spirit of "consecutive", discards evidence
   across long gaps, needs K chosen.

## RULED 2026-07-30 (Kristen): option 1

Amendment appended to `research/hunt2026/preregistrations/ops-reality-2026-07-10.md`, following
the same record-don't-rewrite convention as the 2026-07-16 deviation. "10 consecutive trading
nights" becomes "10 breach nights among sessions in which that class filled". **Threshold, bands
and trailing statistic unchanged — only the word.** It counts exactly the nights that carry
evidence and none of the nights that do not, so no decision becomes easier or harder to reach on
real evidence.

Effect on the record, stated because it changes a number that has been on the status board: the
ETF streak is **9, not 12**. Three of those nights had no ETF fill. The breach is real, still out
of band at +31.1 bps, and one filling breach night from the trigger.

**Shipped alongside, so nothing asserts something false:** the alarm no longer claims
"consecutive nights". It says "breach nights", states that these are nights the class filled, and
names the pre-registration mismatch in its own text. A breach whose window is not currently being
measured is additionally marked `[PROVISIONAL]` with the fresh/total fill counts, which is the
review's own suggested alternative to gating the streak on freshness.

## Also resolved this round

- **Disputed finding verified from source.** The nightly path runs `dates[-2:]` and calls
  `drop_reprocessed_dates` on them before recomputing, so yesterday is always re-scored from a
  banked value three rows back. Late fills DO propagate into the streak. Codex was right, the
  Claude seat's finding drops.
- **Declined, recorded:** gating `MC-POSITION-GAP` on `unknown_gap`.
  `test_unpriceable_prior_target_is_unknown_not_zero` pins the opposite deliberately.
- **Not closed:** MC-DRAG still compares a partial window to a per-month band. The relabel made the
  mismatch legible without normalising it, so flag 2026-07-16 item 5 stays open by design.

275 passed, 1 skipped.
