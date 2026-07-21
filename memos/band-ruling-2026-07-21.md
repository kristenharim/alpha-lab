# Ruling — the 30 bps/month book drag band, and what the slippage statistic measures

**From:** Research Director (Kristen Ho), 2026-07-21
**Resolves:** `memos/mc-drag-flag-2026-07-16.md` items 1 and 4
**Scope:** monitoring definitions only. No pre-registered band value was changed.

## 1. The slippage statistic is structurally contaminated by overnight drift

The flag asked whether the MC fills' 332 bps median slippage was real cost or a reference-price
artifact. The mechanism is not in doubt and is structural rather than a bug in any one place: the
runner submits while the market is closed (this deployment fires around 04:00 ET), the order cannot
cross until the opening auction, and the pre-registered statistic scores that fill against the
PREVIOUS session's close. Every fill therefore carries one full overnight gap before execution
begins. The pre-registration anticipated this and budgeted ±50 bps of per-fill drift; the sandbox
tape moves 3 to 5 percent a session, so the drift term runs several times what was assumed.

What is NOT established is the share. Calling the whole 332 bps an artifact was an overclaim, and
this note made it before the decomposition existed to check it.

Rather than amend a frozen definition from inside the experiment, the reconcile now reports the
split alongside the unchanged statistic. Each fill carries `drift_bps` (run-date close to the open
it crossed at) and `exec_bps` (that open to the fill), both on the run-date close basis so the pair
sums to the statistic exactly. Means, not medians, since medians do not add.

| account | date | split fills | slippage | drift | execution |
|---|---|---|---|---|---|
| shared, ETF trailing 20 | as of 07-20 | 20 of 20 | +1.1 | +1.3 | -0.2 |
| momentum_concentrated | 2026-07-16 | 16 of 16 | +291.5 | +238.1 | +53.4 |
| momentum_concentrated | 2026-07-17 | 4 of 4 | -157.1 | -270.0 | +112.9 |
| momentum_concentrated | 2026-07-20 | 5 of 5 | +100.7 | +64.5 | +36.2 |

Two different readings, and they should not be merged. On the shared ETF book the trailing window
is full and the answer is clean: execution costs essentially nothing (-0.2 bps) and the band
breaches are drift. On the dedicated single-name account, drift dominates and flips sign session to
session as expected, but execution does NOT look free: +53, +113, +36 bps on 25 fills across three
sessions. That is 25 fills and no trailing statistic, so it is a flag for attention rather than a
finding, and the obvious candidates (an opening auction print that differs from the vendor's open,
single-name spreads, or the vendor's adjusted open itself) are untested. Someone should test them
before anyone concludes single-name execution is expensive.

## 2. `book_drag_bps_month = 30` stands

The flag was right that the band was inherited unchanged when `momentum_concentrated` moved from
pro-rated attribution in a shared ETF account to exact attribution in a dedicated single-name
account. That mattered mostly because the MC path summed absolute per-fill slippage, which
rectified the overnight noise above into a quantity that only ever grew, so no band was reachable.
With the drag signed as pre-registered, nightly drag now nets across sessions the way a tracking
error should: -3.4 bps on 07-17, +3.9 bps on 07-20.

30 bps per rolling month is a defensible tracking band for either book shape and nothing currently
turns on the difference. Re-deriving it for single names is deferred until a decision actually
depends on it. This is an explicit ruling, not silent inheritance.

## 2b. A pre-existing MC attribution bug fell out of this

Building the split exposed it. The MC reconcile keyed its orders by their raw submit date, while
the shared path attributes each order to the latest run date at or before that submit date. The
20:30 run stamps the NEXT calendar day on its orders, so those never matched an MC run date: they
were dropped from the MC reconcile entirely, and the only fills it had ever measured were same-day
by-hand runs. The 2026-07-20 session read 3 fills and now reads 5. MC now uses the same
`bucket_orders` as the shared account, and a test pins it.

## 3. What is still lit, and why that is correct

`MC-DRAG` reads +106.3 bps and will keep reading roughly that until 2026-07-16 rolls out of the
20-session window in mid-August. That night alone contributed +105.8 bps: it is the initial
build-out of the dedicated account, one full turnover of the sleeve executed into a session the
tape fell about 4 percent. By the split its 16 fills were +238 bps of drift against +53 bps of
execution, so most of that night was the market moving, not the desk. It is one true event rather than a ratchet, so it is being left to age out rather than
suppressed. If it proves noisy enough to train the eye past
it, the follow-up is to exclude the account's first invested session from a statistic that is
supposed to measure tracking, which is a definitional question and belongs in a dated ruling of its
own.
