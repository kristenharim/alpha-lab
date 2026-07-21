# Ruling — the 30 bps/month book drag band, and what the slippage statistic measures

**From:** Research Director (Kristen Ho), 2026-07-21
**Resolves:** `memos/mc-drag-flag-2026-07-16.md` items 1 and 4
**Scope:** monitoring definitions only. No pre-registered band value was changed.

## 1. The 332 bps median was a measurement artifact, and it is now decomposed

The flag asked whether the MC fills' 332 bps median slippage was real cost or a reference-price
artifact. It is the artifact, and the mechanism is structural rather than a bug in any one place:
the run submits after the close, the fill lands at the next open, and the pre-registered statistic
scores that fill against the close it was submitted after. Every fill therefore carries one full
overnight gap before execution begins.

The pre-registration anticipated this and budgeted for it, calling ±50 bps of per-fill drift normal
and prescribing the trailing mean over 20 fills as the agreement statistic. The sandbox tape moves
3 to 5 percent a session, so the drift term is running roughly six times what the pre-registration
assumed, which is enough to dominate the statistic outright.

Rather than amend a frozen definition from inside the experiment, the reconcile now reports the
split alongside the unchanged statistic. Each fill carries `drift_bps` (run-date close to the open
of the session it actually filled in) and `exec_bps` (that open to the fill), the trailing window
reports both, and `SLIPPAGE-*` names which half moved when it escalates.

The split is only computed for orders submitted after the run date, which is the 20:30 case whose
orders queue overnight and fill at the next open. A by-hand daytime run submits after its own
session's open, so that open is not the boundary between market drift and execution and the split
would read backwards. Most fills in the current window came from by-hand runs, so the evidence
available today is one session:

| date | eligible fills | slippage | drift | execution |
|---|---|---|---|---|
| 2026-07-20 | 4 of 9 | +68.9 | +60.2 | +3.5 |

That is a single session and four fills. It is consistent with the reading that the band breaches
are drift and that execution is running inside the 15 bps stock and 5 bps ETF bands, and it is
nowhere near enough to assert it. The trailing window withholds the split entirely until every
fill in it carries one, which will take about 20 sessions of scheduled runs. Treat the mechanism
as established by construction (the reference close precedes the fill by a session, unavoidably)
and the magnitudes as unmeasured until that window fills.

## 2. `book_drag_bps_month = 30` stands

The flag was right that the band was inherited unchanged when `momentum_concentrated` moved from
pro-rated attribution in a shared ETF account to exact attribution in a dedicated single-name
account. That mattered mostly because the MC path summed absolute per-fill slippage, which
rectified the overnight noise above into a quantity that only ever grew, so no band was reachable.
With the drag signed as pre-registered, nightly drag now nets across sessions the way a tracking
error should: -3.4 bps on 07-17, +0.1 bps on 07-20.

30 bps per rolling month is a defensible tracking band for either book shape and nothing currently
turns on the difference. Re-deriving it for single names is deferred until a decision actually
depends on it. This is an explicit ruling, not silent inheritance.

## 3. What is still lit, and why that is correct

`MC-DRAG` reads +102.5 bps and will keep reading roughly that until 2026-07-16 rolls out of the
20-session window in mid-August. That night alone contributed +105.8 bps: it is the initial
build-out of the dedicated account, one full turnover of the sleeve executed into a session the
tape fell about 4 percent. Its fills were submitted intraday by hand, so the drift/exec split is
withheld for it and how much of that 105.8 was market movement rather than execution is not
measured. It is one true event rather than a ratchet, so it is being left to age out rather than
suppressed. If it proves noisy enough to train the eye past
it, the follow-up is to exclude the account's first invested session from a statistic that is
supposed to measure tracking, which is a definitional question and belongs in a dated ruling of its
own.
