# Diagnostic results — 2026-07-10 (the three free tests from alpha-roadmap-2026-07)

All three run on the committed `costs`-config artifacts (positions, residuals, 31,008-trade
signal log, 2018–present, S&P 500).

## 1. Half-life monotonicity test → the OU/kappa screen is KILLED

Pre-registered rule: build the screen only if per-trade P&L declines with estimated AR(1)
half-life and the slowest quintile is ~zero/negative. Measured: the OPPOSITE.

| half-life quintile | median hl (d) | mean per-trade P&L | win rate |
|---|---|---|---|
| Q1 fast | 2.3 | 0.0104 | 70.4% |
| Q3 | 5.2 | 0.0130 | 71.2% |
| Q5 slow | 12.2 | 0.0195 | 73.9% |

Slow-reverting entries earn MORE (also per-day, not just per-hold). The A&L hl≤30d screen
keeps 99% of trades anyway, and the 1% it drops had HIGHER mean P&L (0.031). Verdict: do not
build. (Caveat noted in the roadmap stands: survivorship hides the blowups the screen targets,
but on measurable data the pre-registered test kills it.)

## 2. Book beta regression → found a P&L-definition problem that dominates everything

The engine scores `held × residual` (tracks/statarb/pnl.py). Decomposing on identical
positions and data (identity: raw = resid + alpha_lag + beta_lag·f):

| book | gross Sharpe | ann. return | ann. vol |
|---|---|---|---|
| residual book (what the backtest scores) | **3.80** | +17.9% | 4.7% |
| raw stock book (what the live paper book holds) | **0.30** | +2.0% | 6.5% |
| beta-hedged book (stock − beta·ETF, implementable) | **0.42** | +2.0% | 4.6% |
| trailing-alpha drift term alone | −29.9 | −15.9% | 0.5% |

The gap is the `alpha_lag` term: the trailing 60d drift estimate, subtracted inside
`rolling_residual`, is booked as P&L by the engine but is NOT hedgeable (it is each name's own
drift, not a factor exposure — the ETF hedge fixes vol, not return). Mechanically: the same
dislocation that triggers an entry drags the 60d alpha estimate against the position, so
subtracting it credits the trade ~6 bps/day of accounting P&L regardless of what the stock
does. The headline 2.67 is substantially this term. The implementable book grosses ~2%/yr
against a measured cost drag of 5.3%/yr → negative net. All residual-space results inherit
this: the ablation table, the robust-core 1.7, the gated 4.08, the per-trade labels.

The live paper book marks NAV with RAW returns, so the forward test would have surfaced this
within months; the decomposition surfaces it now.

## 3. Turnover cost decomposition

Daily one-way turnover 5.3% of book, median hold 15d. At 10 bps/side the cost drag is
5.34%/yr — 29.9% of residual-space gross (3.80 → 2.67), and > 100% of implementable gross.

## Consequences (pending Kristen's call — this is a verdict-level event)

1. Fix the engine to score implementable P&L: `held × (raw − beta_lag·f)` plus the ETF
   overlay cost, then re-run the ablation. Expect the headline to collapse; that is the point.
2. The salvage path is Avellaneda-Lee's own drift-corrected (modified) s-score: enter only
   where expected reversion EXCEEDS the expected drift drag, i.e. select trades on
   implementable expected P&L. Whether anything survives net of costs is an open question.
3. Kappa screen: dead per its own kill criterion. GP sizing / MOC / cost-model items: only
   relevant if step 2 leaves a live edge.
4. README / dashboard / STATE claims keep the 2.67 language until the re-run, then update to
   the implementable numbers.

## Post-fix ablation re-run (same day)

Engine fixed: P&L scored on hedged returns (stock − lagged-beta × sector ETF) + overlay cost
at 1 bp/side; trade labels now implementable; `hedged.parquet` persisted; parity gate updated;
86 tests green. Full-history S&P 500 re-run:

| config | Sharpe (was) | Sharpe (now) | ann. return | win rate |
|---|---|---|---|---|
| baseline (no costs) | 3.80 | **0.28** | +1% | 63% |
| + costs 10 bps | 2.67 | **−0.88** | −4% | 63% |
| + liquidity | 2.65 | −0.89 | −4% | 63% |
| + sector caps | 2.44 | −1.10 | −5% | 63% |
| all on | 2.43 | **−1.12** | −5% | 64% |

The strategy as specified does not survive implementable accounting: ~1%/yr gross against
~5%/yr of costs. Deflated-Sharpe prob of the cost-charged book: 0.00. This matches the
decomposition's prediction exactly.

Open decisions (Kristen gates verdicts):
1. Salvage attempt: A&L drift-corrected s-score (select on expected reversion NET of drift).
2. The live Alpaca paper cron is still trading this book nightly.
3. README / dashboard / STATE / notebook / tearsheets all still carry the residual-space
   numbers and need a one-pass rewrite once the verdict is called.

## Salvage attempt: A&L drift-corrected (modified) s-score — FAILED (same day)

Pre-registered before running: one trial, formula straight from Avellaneda-Lee (s_mod =
s − α/(κσ), lagged α, AR(1) κ, zero tuned parameters), same bands/window/universe/engine;
success = costs-config implementable net Sharpe > 0.

| variant | gross Sharpe | net Sharpe (10 bps) | ann. gross | win | hold |
|---|---|---|---|---|---|
| plain s-score | 0.28 | −0.88 | +1.28% | 63.3% | 18.9d |
| drift-corrected | 0.35 | **−1.06** | +1.56% | 57.6% | 16.0d |

The correction does what the theory says (gross up slightly, drift-explained entries
suppressed) but shortens holds and adds churn, so net gets WORSE. Killed by its own criterion.

## The strategy, figured out (final picture)

1. The headline 2.67 was an accounting artifact: the engine credited the unhedgeable
   trailing-alpha term (−15.9%/yr of pure drift drag was being booked as profit).
2. The real, implementable reversion edge on daily S&P 500 with a sector-ETF hedge is
   ~1.3–1.6%/yr gross (Sharpe ~0.3). It exists — 63% win rate — but it is tiny.
3. Turnover costs 5.3%/yr at 10 bps/side. Even at 2 bps/side (best institutional case)
   cost ≈ gross → net ≈ 0. The gap is ~4x, not a parameter-tuning distance.
4. The A&L drift correction, the one change aimed at the failure mode, fails pre-registered.

Recommended verdict (Stage 4, Kristen gates): DEAD at daily frequency on large caps.
The post-mortem is the deliverable: a Sharpe-3.8 backtest killed by implementability
accounting, caught before the forward test had to catch it. Remaining on her call:
mark verdict, stop the nightly paper cron, one-pass rewrite of README/dashboard/STATE/notebook.

---
**VERDICT CALLED: DEAD (Kristen, 2026-07-10).** Wrap-up executed: nightly paper-trading workflow
disabled on GitHub (`gh workflow disable paper-trading`, ledger frozen), STATE.md set to Stage 4
dead with the kill story, README rewritten around the post-mortem, dashboard rebuilt, notebook
banner added. Paper positions left open on the Alpaca paper account (flatten with
`scripts/paper_book_run.py --flatten` if desired).
