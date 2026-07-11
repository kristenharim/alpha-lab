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

**F-016 — 12-1 cross-sectional momentum still ranks S&P 500 stocks (post-2015)**
Result: FALSE by IC. Monthly rank IC vs 21d forward returns: −0.001 (t=−0.07, hit rate
50%, 135 months); 63d horizon +0.008 (t=0.45). The signal has NO ranking power in this
universe/era — momentum_concentrated's tolerable windows came from concentration + vol
targeting (construction), not selection skill. Measured BEFORE portfolio construction,
which is why it wasn't visible in return space (robustness/ic.md).
Status: RETIRED as a large-cap ranking signal. Reopen on: a different universe (small
caps), interaction conditioning (momentum × dispersion / × earnings), or an IC that
returns in live regime monitoring. Rule adopted: every future cross-sectional signal
reports rank IC before any portfolio is built.

---

## Negative-result registry

Hypothesis-level records: one row per HYPOTHESIS, aggregating the independent tests
(F-entries above) that bear on it. A hypothesis with 3+ independent kills is stronger
evidence than any single entry — and the first thing to check before proposing a "new"
idea. F-entries keep their numbers; only this section aggregates.

**NR-1 — "Short-term reversal survives costs at daily frequency (large caps)"**
Independent tests: F-001 (decile spread, direct), F-003 (OU half-life screen — the
theory's own quality filter selects the wrong trades), F-004 (Avellaneda-Lee drift
correction — gross up, net worse), F-008 (deep-dip concentration — second construction
angle, same death). Four designs, four mechanisms, one verdict.
Evidence strength: **STRONG against.** Do not run a fifth daily-bar reversal variant at
10 bps/side. Shared reopen condition: measured live slippage ≤ 2-3 bps/side or intraday
execution (per F-001); vol-conditioned entry timing remains the one untested angle
(memos/alpha-roadmap-2026-07.md, Dai et al. NBER w30917).

**NR-2 — "Cross-sectional momentum ranks large caps (post-2015)"**
Independent tests: F-015 (return space — 44-window walk-forward, −4.6pp median excess)
and F-016 (signal space — monthly rank IC ≈ 0, t=−0.07, 135 months, measured before any
construction). Two measurement spaces, same verdict; the tolerable windows were
construction (concentration + vol targeting), not selection skill.
Evidence strength: **STRONG against** in this universe/era. Reopen per F-016 (small caps,
interaction conditioning, or IC returning in live monitoring).

**NR-3 — "Slow gates protect against fast crashes"**
Independent tests: F-007 (daily-close VIX gates ate the Aug-2024/Apr-2025 SVXY gaps),
F-012 (12m dual-momentum gate: COVID −41% in-train, 2022 −25.5% blind), F-013 (VIX-spike
mean-reversion add: −62.1% in the GFC cascade). Three different gate constructions, three
different fast events, zero protection. The gates all work on SLOW bears (2022).
Evidence strength: **STRONG against.** Any spec whose safety argument is a daily-or-slower
gate must state fast-crash exposure explicitly (F-012 rule) and show its worst
walk-forward window includes 2008 (F-013 rule).

**NR-4 — "Static leverage on beta survives a bear window"**
Independent tests: F-011 aggregates three books that died the same way in one window
(trend_gated_spy_2x, ew_levered_vix_gate, composite_book: −40%ish DD, 11-16% CAGR) —
one window, so counted as one test with three expressions — while the state-dependent
versions (vol_managed_qqq, trend_vol_qqq) survived the identical window.
Evidence strength: **MODERATE-STRONG against** (single macro window; mechanism is
arithmetic — volatility drag — which argues it generalizes). Leverage must be
state-dependent; already adopted as a design rule.

**NR-5 — "Sophistication adds median return over the naive expression"**
Independent tests: F-014 (trend+vol combo: +8.0pp median vs +13.4pp for either naive
parent; buys tail relief), F-010 (JSE vs raw PCA: direction right, magnitude ≈ noise at
k=1 long-only). Pattern, not a law: two cases where the sophisticated layer repriced
return into robustness rather than adding return.
Evidence strength: **SUGGESTIVE.** Not a retirement — a reporting rule: every layered
spec reports the delta vs its naive parent (TRIAL_LEDGER.md rule 4), and "better tail,
worse median" is claimed as a hedge, never as alpha.

**F-016 addendum — momentum variants (sector-relative, residual, 52w-high) die with it**
Result: FALSE by IC (robustness/ic_screen.md). Sector-hedged 12-1 (t=0.03/0.59 at
21d/63d), residual 12-1 on 60d-beta sector residuals (t=0.27/1.22), and 52-week-high
proximity (t=−0.02/0.32) all fail; each variant's by-year IC is ~0.97-correlated with raw
momentum's — same signal, lower amplitude. Residual mom's 63d t=1.22 is the best of ten
screened signals, i.e. the expected max of ten noise draws.
Status: RETIRED with F-016. Reopen conditions unchanged.

**F-017 — short-horizon reversal ranks S&P 500 stocks (post-2015)**
Result: FALSE by IC. 21d reversal: mean IC +0.005 (t=0.34); sector-dispersion residual
(21d return vs sector median, flipped): −0.001 (t=−0.09). Mildly positive 2015-19
(+0.036), negative since 2020 (−0.011, −0.052 in 2025-26) — the documented large-cap STR
decay, not a harvestable signal (robustness/ic_screen.md).
Status: RETIRED at monthly rebalance. Reopen on: intraday/weekly horizons with a cost
model, or small caps.

**F-018 — low-vol / low-ivol ranks S&P 500 stocks (post-2015)**
Result: FALSE by IC. 60d total vol (low-minus-high): mean IC −0.006 (t=−0.29); 60d
sector-residual ivol: +0.002 (t=0.16). Both were strongly negative in 2025 (−0.05 to
−0.10) — no defensive ranking power in this universe/era (robustness/ic_screen.md).
Status: RETIRED as a large-cap ranking signal. Reopen on: vol-anomaly conditioning
(post-drawdown regimes) or a universe with a real vol spread.

**F-019 — price/volume microstructure (volume shock, overnight share, gap persistence)
ranks S&P 500 stocks**
Result: FALSE by IC. Volume shock 21d/252d (t=0.13/−0.43), 126d overnight-minus-intraday
cum log return (t=−0.21/−0.48), 63d count of held >2σ up-gaps (t=0.25/0.52). Flat in
every half-decade (robustness/ic_screen.md).
Status: RETIRED at monthly horizon. These are plausibly intraday/weekly effects; monthly
sampling was the honest first test and it found nothing. Reopen only with a
higher-frequency harness.

**F-020 — the vol-managed-leverage mechanism (and trend gate) is universal across markets**
Result: FALSE. Frozen registered params (σ=0.25/rv21/cap2x; SMA200/1% hysteresis) applied
UNCHANGED to 28 assets grouped into 7 correlation clusters (sign-test on cluster-median
Sharpe delta, not tickers — 14 intl-equity funds + IWM/MDY/VNQ/HYG collapse to ONE global-
equity draw). Vol management improves Sharpe in 3/7 clusters (p=0.77), trend gate 4/7
(p=0.50), combo 4/7 (p=0.50) — indistinguishable from a coin flip. Class-median ΔSharpe tiny
and mixed-sign (intl-eq −0.01, bonds +0.03, commod +0.02, fx +0.01). Isolated wins (VNQ,
UNG, DBC) are cherry-picks (robustness/xmarket.md).
Status: the edge is CONFIRMED US-large-cap-equity-specific — it is levered equity-premium
harvesting, which is why it lives where the premium is richest and does not travel. Caps the
vol-managed family at confidence level 3. Reopen only per-asset-class with class-specific
mechanism justification (not the same knob sprayed everywhere).

**F-021 — the Goldberg/JSE dispersion-bias correction improves min-var at k>1, n=252 (S&P 500)**
Result: FALSE, and significantly so. Estimator Lab walk-forward (research/estimator_lab/,
137 months, ~450 names, verified by independent re-run): unconstrained min-var, JSE is WORSE
than raw PCA at every k (+31/+18/+14 bps realized vol at k=1/3/5, t≈8-12); long-only the gap
is ~0. Mechanism (verified, not assumed): per-factor ψ̂ ≈ 0.93-0.997 at n=252 with strong
S&P factors, so the dispersion bias the correction targets is nearly absent and the rotation
only perturbs good eigenvectors. Winners on realized risk: MP-eigenvalue-clipping
(unconstrained, 11.3% vol) and PCA k=1 (long-only, 11.7%); sample covariance is unusable.
Status: JSE RETIRED for the large-n / strong-factor regime. EXPLICITLY REOPENED for the
theory's actual live regime — small n (60-90d windows) / weak factors, which is where
factor_lab's own demo (n=60) operates. That is the pre-registered next Estimator-Lab
experiment, and it is the scientifically correct home for the Goldberg program: not "does
JSE help everywhere" (answered: no) but "JSE helps iff ψ̂ is meaningfully below 1."
