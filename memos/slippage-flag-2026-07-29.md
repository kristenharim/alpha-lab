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
