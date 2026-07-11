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

**F-021 RESOLVED (partial reopen confirmed) — JSE helps in its designed regime (n=63, long-only)**
The pre-registered weak-factor reopen (H-jse-weakfactor, EXPERIMENT_QUEUE.md #1) ran at
WINDOW=63. Paired jse−pca realized-vol delta (verified, my run):
- long-only: −0.013 / −0.020 / −0.016 vol%pts at k=1/3/5, t = −2.2 / −6.0 / −6.5, p ≤ 0.03
  → JSE SIGNIFICANTLY IMPROVES. The n=252 long-only null (~0) was a regime artifact; shorten
  the window and the dispersion-bias correction bites, exactly as the theorem claims.
- unconstrained: +0.72 / +0.37 / +0.25, t > 6 → JSE still WORSE; short-window eigenvector
  noise / turnover dominates the correction when shorts are allowed.
Proof of mechanism is by construction: JSE differs from PCA only by the ψ̂ rotation, so a
significant delta requires ψ̂ < 1 — the premise "JSE helps iff ψ̂ ≪ 1" is confirmed.
Status: the Goldberg program is LIVE in the small-n / constrained regime. Scope now bounded
on BOTH sides: dead at n=252 (F-021) and unconstrained; alive at n=63 long-only. The
publishable claim is the boundary itself, not a headline return. Effect is small (1-2 bps
vol) but robust; next: log ψ̂ per month to plot benefit vs ψ̂, and test n∈{42,90,126} to map
the crossover. Artifacts: research/estimator_lab/{results_w63,summary_w63}.csv.

**F-021 FINAL — the crossover mapped (EXP-EST-CROSSOVER, 2026-07-10): there is no crossover**
Pre-registered n-sweep (42/63/90/126/189/252, k=3, same 138 months, prereg
preregistrations/est-crossover-2026-07-10.md). Two corrections to the record above:
1. "Dead at n=252" was wrong in sign-language for the long-only book: long-only JSE helps
   at EVERY n, monotone −2.6 bps (n=42) → −0.5 bps (n=252), always p<0.0001. It never turns
   harmful; it just decays. Unconstrained JSE hurts at every n (+18 to +49 bps), worst at
   small n. The correct scope statement is by BOOK, not by window: long-only always-on,
   unconstrained never. Benefit ≈ −0.24 bps realized vol per unit p/n (in-sample fit).
2. The hoped-for ψ̂ month-level gate is dead: pooled Spearman(Δ, median ψ̂) = +0.18
   (p=3e-07) but WITHIN each fixed n, ρ ≈ 0 (all p>0.3, 6/6) — ψ̂ is an observable
   re-parameterization of p/n, not a timing signal. Pre-committed cuts both rejected:
   ψ̂<0.90 bucket (N=26, nearly all n=42, calm months) insignificant at −0.4 bps;
   ψ̂≥0.95 still −1.0 bps at t=−11. Eigengap: no content (p=0.32).
Status: F-021 CLOSED. Goldberg program final form: a real but tiny long-only estimator
edge that scales with p/n; not worth a deployment on ~470-name S&P books (max ~2.6 bps
vol/yr at n=42), but the mechanism is confirmed and correctly bounded on all sides. No
month-level timing signal exists in the estimation-state observables tested. Artifacts:
research/estimator_lab/{CROSSOVER.md,crossover.csv,run_crossover.py}.

**F-020 — Gold is structurally the right third asset in the dual-momentum risk menu**
Result: FALSE — regime artifact, by pre-registered rule. GLD beats the two-asset {SPY,QQQ}
menu in only 21% of 70 rolling windows (2009-2026) and 13% of pre-2024 windows (median
delta −0.61%); its entire edge sits in the 10 windows ending 2024-2026 (+18.6% median).
Stronger finding: the third slot is a net drag no matter what fills it — NONE has the best
median SPY-excess (+11.3%) of all ten variants; the defensive TLT/BIL leg already supplies
the crisis protection. Windows where GLD was actually held: 60% positive / +4.6% median vs
96% / +31.0% when not held. (robustness/defensive_asset.md, prereg
preregistrations/defensive-asset-2026-07-10.md)
Status: hypothesis RETIRED. The live dual_momentum_gold book stays frozen mid-forward-test;
whether to retire its gold slot at the next legitimate re-freeze is a Stage-4 call. Any
replacement asset picked from this experiment's table would itself be hindsight — the only
clean fix on current evidence is the two-asset menu.


**F-021 status amendment (2026-07-10, Director): PROVISIONAL, not closed.**
The crossover sweep (69f5489) indicates a small long-only JSE benefit at EVERY n
(−2.6bps@42 → −0.5bps@252) and persistent unconstrained harm — but this conflicts with
earlier narrative reports ("long-only identical at n=252", "sign flipped at n=63") and
with a month-set discrepancy (137 months 2015-02→ vs 138 months 2015-01→). A matched-run
reproducibility audit (AUDIT_JSE_RECONCILIATION.md) must identify the first divergence
(reporting language vs pipeline difference vs bug) before any operational rule is locked.
Until then the operational rule is UNLOCKED and the three conclusions stay separate:
scientific (directionally useful long-only), operational (0.5-2.6bps/yr is below
deployment materiality regardless), paper (constraint-dependent sign + p/n monotonicity
is the publishable shape, pending audit).

**F-021 audit verdict (2026-07-10, reproducibility audit): REPORTING DRIFT — pipelines agree, F-021 may re-close.**
Full audit: research/estimator_lab/AUDIT_JSE_RECONCILIATION.md. Findings: (a) no method
difference, no bug — run_minvar and run_crossover produce IDENTICAL monthly delta series
(max 2.7e-16; crossover imports run_minvar's universe/cap/vol code and asserts estimator
equivalence), and both committed CSVs are byte-reproducible on the current panel.
(b) The paired t on long-only WAS run and reported in the original RESULTS.md table
(-0.6 bps, t=-8.2); the "economically zero" narrative two paragraphs later rounded a
small significant negative to zero — that prose line is the first divergence, and the
n=63 "sign flip" framing inherited it (nothing flipped; the effect grew 4x).
(c) The 137-vs-138 / 2015-02-vs-2015-01 month-set scare is labeling: RESULTS.md described
hold-END months, CROSSOVER.md rebalance dates; the head never differed. The one real
change is the panel regeneration (phantom 2026-05-25 fix): 136/137 overlapping months
identical, only 2026-05-01 moved (<=0.8 vol-bps), plus a new 2026-06 tail month
(-0.56 t=-8.2 -> -0.53 t=-7.4). Corrected numbers (current panel, 138m, k=3, paired t):
n=252 long-only -0.53 bps t=-7.39; n=63 long-only -1.98 bps t=-5.99; unconstrained
+18.4 t=+9.7 (252) / +36.9 t=+8.1 (63). The crossover "no crossover, monotone decay"
conclusion STANDS without re-running. Operational rule can re-lock as stated in 238cf37;
materiality unchanged (below deployment threshold on ~470-name S&P books).

**F-021 final closure (2026-07-10, Director, post-audit c072ceb):** the reproducibility
audit returned verdict (a) REPORTING DRIFT — both pipelines byte-identical (max per-month
delta 2.7e-16); the divergence was PROSE (RESULTS.md:59 "economically zero" contradicting
its own table's −0.6bps t=−8.2), inherited by the later "sign flip" narrative. Month-set
discrepancy = labeling convention (hold-end vs rebalance dates) + one tail month from the
panel regeneration (1 of 137 overlapping months changed, ≤0.8 vol-bps). Corrected final
numbers: long-only k=3 −0.53bps t=−7.39 (n=252), −1.98bps t=−5.99 (n=63); unconstrained
+18.4bps t=+9.69 (n=252). Crossover conclusion STANDS. Operational rule locked: JSE
always-on for long-only min-var, never unconstrained; below deployment materiality.
Process lesson recorded: prose summaries must quote the table, not paraphrase it.

---

### F-022 — Bond-carry (Treasury-ladder, free data) does not predict; it is mechanical duration

**Registered:** EXP-A (research/discovery/prereg/EXP-A-bond-carry-predictability.md), Discovery
Program, 2026-07-10. Trial #23. First non-price/volume *market* source tested.

**Result — REJECTED (four frozen kill triggers fire independently).** A frozen carry+roll-down
measure `carry_i = (yield_i − DFF) + rolldown_i` over the SHY/IEF/TLT ladder (PIT rates from the
PASSed FRED state layer):
- Primary pooled forward-21d regression on carry z: coef +0.00143, **Newey-West t = 1.53 < 2** (no
  predictability); 95% CI [−0.0004, +0.0032]. No horizon (5/21/63d) reaches |t|>2. Rank IC +0.023 (t 0.43).
- **Mechanical-duration control is decisive:** adding a duration×realized-ΔDGS10 term (t = −32.9)
  collapses the carry z-coef to **t = 1.05**. The apparent signal is a static long-TLT/short-SHY
  duration tilt when the curve is upward-sloping, not carry timing.
- Equity beta β_SPY = −0.144 (t −6.6, exceeds the ≈0 band); duration beta β_TLT 0.33 (t 21.9).
- **Orthogonality v2: NOT INDEPENDENT** — 7/8 dims pass but `roll_corr_max_ens` = 0.737 > 0.65
  (63d rolling corr to the equity/vol ensemble spikes risk-off). resid_alpha_t 2.85 but independence fails.
- Blind holdout (last 24m) sign flips; era IC sign flips negative 2015-19.

**Belief update:** free-data Treasury-ladder carry is a decayed, rate-regime-driven duration bet,
not independent alpha. **The free-data carry lane is closed.** Reopen only with a materially
different instrument set (FX / commodity term structure) — BLOCKED BY DATA (vendor futures/roll,
CARRY_FEASIBILITY.md). Bug-checked: primary coef reproduced byte-identically without HAC; leakage
clean (forward ΔDGS10 used only as in-sample attribution control, never in the tradable signal);
n = 771 pooled obs over 2005–2026.

### F-020 addendum — conditional vol-management is not a validated transportable mechanism

**Registered:** EXP-B (research/discovery/prereg/EXP-B-conditional-vol-mechanism.md), Discovery
Program, 2026-07-10. Trial #24. The sanctioned mechanism-level reopen of F-020.

**Result — MECHANISM UNSUPPORTED (narrows F-020, does not overturn it).** Regressing the cross-asset
vol-management benefit (frozen vol_managed_qqq spec applied to 26 ETFs, minus buy-hold, net of cost)
on the four pre-registered fixed-sign properties: **3/4 signs correct and stable** across all
leave-one-cluster-out refits — risk premium +, volatility clustering + (strongest, t 3.36),
return-vol asymmetry − ; drawdown convexity flips (collinear with clustering, no independent value).
But the decisive frozen test — **joint significance at the cluster level — FAILS**: wild-cluster
bootstrap p = 0.44 with only G = 5 clusters (the naive iid F p=0.047 is forbidden by prereg; the
raw cluster-robust Wald was ill-conditioned and discarded). So vol-management stays a US-large-cap /
high-premium-equity + gold empirical fact, not a transportable 4-property mechanism. This **narrows
F-020 descriptively** (benefit concentrates in high-premium, high-vol-clustering equity beta; ~0 or
negative for broad intl, silver, energy, IWM) but the mechanism is not established. **Closes the
conditional-vol reopen on this ETF panel** — next reopen is new markets/instruments, not new features.
Bug-checked: vol-managed weights reproduce the frozen spec exactly; the anomalous F=1632 traced to an
ill-conditioned G=5,q=4 Wald and correctly replaced with the wild-cluster bootstrap.
