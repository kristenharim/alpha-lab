# Failure database — why ideas died, so nobody re-runs the same funeral

Structured records of every falsified hypothesis in this repo. A hypothesis lands here
when evidence retires it; it leaves only if NEW data (not new enthusiasm) reopens it.
Format: hypothesis / result / evidence / status / what would reopen it.

---

**F-001 — Short-term reversal survives retail costs at daily frequency (large caps)**
Result: FALSE. Gross is real (5d sector-relative decile spread +15.8%/yr, t=2.41 on
2014-2025 train), turnover eats it: best smoothed long-only version nets 12.3% CAGR
(below SPY); market-neutral versions net negative. Sister evidence: the statarb book —
implementable gross ~1.3-1.6%/yr vs 5.3%/yr cost drag (memos/diagnostics-2026-07-10.md).
Status: RETIRED at 10 bps/side, daily bars. Reopen if: measured live slippage on the paper
book comes in ≤ 2-3 bps/side, or intraday execution becomes available.

**F-002 — Residual-space P&L approximates implementable P&L**
Result: FALSE, catastrophically. Booking held×residual credited the unhedgeable
trailing-alpha term: headline Sharpe 3.80 → 0.28 implementable. The costliest accounting
bug this repo has produced; engine fixed 2026-07-10 (commit 92cbfad).
Status: RETIRED as a scoring convention, permanently. Harness scores real returns only.

**F-003 — OU half-life (kappa) screen improves reversion entry quality**
Result: FALSE by its own pre-registered criterion — per-trade P&L INCREASES with
half-life (slow quintile 0.0195 vs fast 0.0104). The screen would drop the best trades.
Status: RETIRED. Reopen if: survivorship-free data shows the fast-reversion edge the
theory predicts (the blowups the screen targets are invisible in yfinance data).

**F-004 — Avellaneda-Lee drift-corrected s-score rescues daily reversion net of costs**
Result: FALSE. Gross up slightly (0.28→0.35 Sharpe) exactly as theory says, but shorter
holds add churn: net WORSENS (−0.88 → −1.06). Killed by pre-registered criterion, one trial.
Status: RETIRED.

**F-005 — Index add/drop effect is tradable in the current S&P 500**
Result: FALSE on 2014-2025 train: post-add excess −0.5%/21d (t=−0.79), deletion reversal
+0.27% (t=0.10). The classic effect is arbitraged away, consistent with post-2010 literature.
Status: RETIRED for large caps. Reopen if: tested on S&P 600 adds (small-cap version may
retain the effect; needs survivorship-safe data).

**F-006 — The overnight premium is exploitable at one close-to-close trade per day**
Result: FALSE as a tilt: overnight carries ~9%/yr of the 13.1% equity return, but a
126d overnight-share tilt has zero cross-sectional predictive power (t=−0.15) close-to-close.
Status: RETIRED under the daily convention. EXPLICITLY REOPENED by design when the harness
gains open+close execution — the effect itself is real; the constraint was the convention.

**F-007 — VIX-gated SVXY carry clears the bar as a standalone book**
Result: FALSE. 1y blind +5.9%; 5y +3.1%; Aug-2024 and Apr-2025 gap events landed inside
daily-close gates exactly as the spec's own brief warned (pre-registered ~40-45% pass odds).
Post-2018 SVXY at −0.5x halves the carry.
Status: RETIRED standalone. Small sleeve inside a vol-managed core (vol_core_svxy) remains
the only sanctioned expression.

**F-008 — Deep-dip concentrated reversion (long-only) escapes the reversal cost trap**
Result: FALSE. 5y CAGR +2.1%, Sharpe 0.22, −44% DD; the concentration raised per-trade
variance without raising net edge. Confirms F-001 from a second angle.
Status: RETIRED.

**F-009 — Gap+volume drift (PEAD proxy) generalizes beyond the 2025-26 window**
Result: PARTIAL. 1y blind +5.8% beta-matched excess, but 5y CAGR only +12.3% — the proxy
decayed/was regime-dependent. The proxy fires ~1/day and catches non-earnings shocks.
Status: WATCH (not retired). Reopen properly when a real earnings calendar with surprises
exists (Finnhub free tier is forward-only, 4 quarters deep) — the hypothesis "drift after
REAL earnings surprises" was never actually tested.

**F-010 — Raw sample PCA eigenvector ≥ JSE-corrected eigenvector for min-var construction**
Result: FALSE (direction), weakly (magnitude). JSE beat raw in both eval windows
(+15bps/1y, +10bps CAGR/5y) with never a loss. k=1 + long-only clip + 2% cap mutes the
delta to noise level.
Status: raw is RETIRED as a default — use JSE everywhere PCA is used; the open research
question (k=3-5, unconstrained, walk-forward) is pre-registered as the estimator program's
next experiment. Never test "raw vs JSE at k=1 long-only" again — answered.

**F-011 — Static leverage on beta survives a 5-year window containing a bear**
Result: FALSE. Every static-levered book (trend_gated_spy_2x, ew_levered, composite_book)
posted −40%ish drawdowns and 11-16% CAGR through 2021-2026. Conditional leverage
(vol-managed) survived.
Status: RETIRED as a design pattern. Leverage must be state-dependent.

**F-012 — 12-month dual momentum's gate protects against fast crashes**
Result: FALSE for fast crashes (COVID Mar-2020 in-train −41% DD at 1.5x; 2022 −25.5%
blind for the gold variant). The 12m gate protects against SLOW bears only.
Status: KNOWN LIMITATION recorded, not full retirement — the strategy passed its 5y blind
bar anyway. Any future dual-momentum variant must state fast-crash exposure in MECHANISM.md.

**F-013 — vix_panic_buyer's panic-add is safe because spikes mean-revert**
Result: FALSE across full history. Walk-forward on the 2005 panel: worst 12m window
−62.1% (GFC — adding leverage into 2008's serial VIX spikes was catastrophic). The 5y and
1y blind windows simply contained no sustained crash regime. The 2022-style slow bear it
survived; the 2008-style cascade it did not.
Status: RETIRED as an unconditional overlay. Reopen only with a regime guard whose worst
walk-forward window is > −30% (pre-register the guard; do not tune it on the GFC window
that killed it).

**F-014 — Combining trend gate and vol targeting adds alpha over either alone**
Result: FALSE in median, TRUE in tail. 80-window attribution (bench_qqq_sma200_2x vs
vol_managed_qqq vs trend_vol_qqq): each component alone +13.4pp median excess vs SPY;
combined +8.0pp — but worst window improves −31% → −22%. The combo is a priced tail hedge.
Status: RECORDED. Choose per book objective: max compounding → single component;
capital preservation → combo. Never claim the combo as additive alpha.

**F-015 — momentum_concentrated's 1-year excess generalizes across regimes**
Result: WEAK. 44-window walk-forward (2015+): median +6.5%, −4.6% median excess, beats
SPY 41% — the 2015-2020 momentum winter dominates. The +16.6% 1y-blind excess was a
favorable draw of a regime-dependent sleeve.
Status: DEMOTED to sleeve-only (diversifier in ensembles; its windows are near-uncorrelated
with the vol-managed family's). Not a standalone.
