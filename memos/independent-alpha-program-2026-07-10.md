# Independent-Alpha Program — Executive Verdict (2026-07-10)

*Research Director synthesis. Sources: `research/independent_alpha/` (CANONICAL_STATE,
ALPHA_SOURCE_REGISTRY, DATA_GAP_MAP, HYPOTHESIS_DEDUP/QUEUE, EXPERIMENT_QUEUE,
FORECAST_SCOREBOARD, INDEPENDENCE_MATRIX, REPLICATION_SCOREBOARD, INCREMENTAL_VALUE_SCOREBOARD,
prereg/*) and `research/estimator_lab/JSE_BOUNDARY_MAP.md`. Every number is transcribed from a
cited artifact; where a doc contradicted code/ledgers, code/ledgers won. This memo **extends**
those ledgers — it does not restate a single new result. Paper-only throughout.*

Ladder: 0 Hypothesis · 1 predictive (lit/signal) · 2 residual/single-blind · 3 replicated
(walk-forward, in-domain) · 4 incremental/cross-market · 5 forward paper · 6 live capital ·
**falsified** = tested & refuted.

Alpha classes (never conflated): **Market** (independent return forecast — the only real edge) ·
**Estimator** (better covariance/mean — improves a portfolio, forecasts nothing) · **Portfolio**
(sizing/combination of sources already held — Sharpe from diversification) · **Execution** (edge
from how/when orders fill).

---

## 10-line executive summary

1. **15 sources catalogued** (AS-01…15); **12 are genuinely distinct *market* sources**; the rest are 1 Estimator, 1 Portfolio, 0 Execution.
2. **Live distinct independent market forecasts = 1** (AS-01, vol-managed US large-cap equity). 2 if you credit AS-02 trend as a standalone diversifier, 3 if you credit AS-04's VRP sleeve. Everything else promoted is a re-implementation, overlay, or repackage.
3. **3 of the 4 promoted books are ONE source.** vol_managed_qqq / vol_core_svxy / trend_vol_qqq are three implementations of AS-01 (residual corr 0.79, crisis corr 0.77); the 4th (defensive_ensemble) is a Portfolio object. n_eff of the 7 books ≈ **2.8**, ~3 clusters.
4. **Raw predictive evidence:** TS/risk-mgmt lane — 3 books clear the WF-median-excess gate (Level 3). Cross-sectional lane — **0 of 10** price/volume signals clear |t|≥2 rank IC. Event lane — un-scoreable (no PIT data).
5. **Residual evidence:** AS-01 carries a real factor-adjusted α (ensemble t≈2.8), but it survives *only* in US large caps; momentum_concentrated has α≈0 (−0.002).
6. **Replicated (Level 3, in-domain):** the vol/trend cluster + defensive_ensemble. **Cross-market (Level 4): 0** — F-020 ran it and refused (3/7 clusters, p=0.77). Nothing in the repo is above Level 3.
7. **Incremental value:** **0 of 3** watch books improve the frozen ensemble (Level-4 gate); momentum_concentrated is actively harmful (P(ΔSharpe>0)=0.07).
8. **Forward-testing (Level 5, accruing):** 7 live paper books + the Finnhub PIT-earnings collector (8/300 events) + ops-reality execution drag + 10-month news feed. No Level-5 verdict is due yet.
9. **Rejected & why:** cross-sectional stock momentum (dead, 0/10 IC), short-term reversal (turnover), low-vol ranking, VIX-panic, microstructure ranking, breadth timing, overnight tilt (exec-gated); plus vol-mgmt *universality* (F-020), trend+vol *additivity* (F-014, halves excess), JSE unconstrained (F-021), and any month-level ψ̂ timing gate.
10. **Most important next action:** the cross-sectional price/volume lane is **exhausted** — stop mining it and stop bolting correlated sleeves onto AS-01. Reallocate to the only honest *new-information* lane (the already-accruing PIT-earnings track) and the cheapest regime unlock (FRED/VIX/rates ingest). **Operational blocker first:** an uncommitted bug-fix + duplicate-row bug sit on the nightly `--live` paper script — resolve before the next 20:30 run.

---

## Answers to the ten questions (numbers + ladder)

**Q1 — How many distinct alpha sources exist?** 15 catalogued (AS-01…AS-15). By class: **12 distinct Market sources** (AS-01…12), 1 Estimator (AS-13, JSE covariance), 1 Portfolio (AS-14, defensive_ensemble), 0 Execution (AS-15 is a measurement placeholder). Of the 12 market sources, only **3 are alive** (AS-01 promoted, AS-02 overlay/sleeve, AS-04 sleeve-only VRP), 2 are watch (AS-03, AS-06), 7 are falsified/dormant. **Honest count of live, distinct, independent market forecasts: 1** (AS-01) — 2 crediting AS-02, 3 crediting AS-04.

**Q2 — How many are merely implementations of US equity risk-management?** Of the 4 promoted books, **3** (vol_managed_qqq, vol_core_svxy, trend_vol_qqq) are three implementations of the single US large-cap vol/trend cluster (AS-01, ± a VRP or trend leg). Measured: 3-book mean residual pairwise corr 0.79, crisis corr 0.77, n_eff(7 books)=2.80. The 4th promoted book (defensive_ensemble) is a Portfolio wrap of AS-01/02/03, not a 4th forecast. Counting the four promoted books as four alphas overstates independence ~3×.

**Q3 — Which have raw predictive evidence?** Only the TS/risk-management lane: vol_managed_qqq (+13.4pp WF median excess, 78% beat-SPY, DSR 81.5%), vol_core_svxy (+12.4pp, 85%, DSR 81.2%), trend_vol_qqq (+8.0pp, DSR 89.8%) — all Level 3. In signal space, **0 of 10** cross-sectional price/volume signals clear the |t|≥2 rank-IC gate (best t=1.22, the expected max of 10 noise draws). Event lane: 0 scoreable (8 PIT events vs an n≥300 gate).

**Q4 — Which retain residual predictive evidence?** After removing SPY+QQQ, the vol cluster still co-moves at residual corr 0.79 — the shared object is a *vol-timing estimator*, and the frozen 4-book ensemble carries a significant factor-adjusted α (t≈2.8). That α is AS-01's, and it is confirmed US-large-cap-specific (F-020). No other book retains independent residual predictive content: momentum_concentrated's α is −0.002 (≈0), dual_momentum residuals are era-conditional. **Residual-independence finding sits at Level 2** (an Estimator/Portfolio diagnostic — it can only lower, never raise, an independence claim).

**Q5 — Which replicated?** Level 3 (multi-window walk-forward, in-domain): the vol/trend cluster (3 books, one mechanism) and defensive_ensemble (Portfolio/capital-preserver role only). Cross-market Level 4: **none** — F-020 sprayed frozen params on 28 assets/7 clusters and got 3/7 (p=0.77), a coin flip; Level 4 was **refused, not merely unattempted**. Data-vendor replication is UNTESTED for every source (single vendor, EODHD → panel_2005) — the largest un-run replication check remaining.

**Q6 — Which improve the ensemble incrementally?** **None.** Against the frozen 4-book control (Sharpe 1.00, α t≈2.87), block-bootstrap ΔSharpe with treatment re-levered to control vol: dual_momentum_gold +0.003 (P=0.53, insignificant, period-concentrated), dual_momentum_gem −0.010 (P=0.36, corr 0.75, redundant), momentum_concentrated −0.057 (P=0.07, residual-α −2.8%/yr — value-destructive). Level-4 incremental count: **0 of 3**. The apparent max-DD improvement is pure dilution (vanishes at equal vol) — the added-beta trap the gate is built to catch.

**Q7 — Which are collecting forward evidence (Level 5)?** All 7 live paper books accrue NAV nightly (paper-only, scheduler on). The genuinely-new-information forward tracks: Finnhub PIT earnings collector (`earnings_fwd/events.jsonl`, 8 events/2 names vs n≥300 — months away), ops-reality execution-drag measurement, and the Alpaca/Benzinga news feed (~10 months deep). The 3 watch books (dual_momentum_gold/gem, momentum_concentrated) are held **only** for forward evidence under a demote-on-2-quarters-below-SPY kill rule. No Level-5 verdict is due yet.

**Q8 — What new data unlocks the most valuable next experiments?** Ranked (DATA_GAP_MAP §4): (1) **FRED + ^VIX/rates ingest** — cheapest real gap; VIX-conditioning already appears in the vol books yet no VIX/rate series is on disk. Unlocks H-E3 (adjudicates trend-*alpha* vs levered-*beta* — the axis F-020 could not test) and honest regime-conditioning. (2) **PIT S&P 400/600 membership + a −30% delisting bound (iShares dated holdings, free)** — the biggest *truth* gap; decides whether the small-cap reversal sleeve is real or survivorship. (3) **FINRA short interest + Alpaca borrow flags** — converts an unmodeled zero short-cost into a bounded, honest drag. Keep feeding the Finnhub PIT-earnings collector — the only honest new-information track, gating H-E4/A4-03. Deliberately NOT yet worth buying: analyst revisions / options-implied / intraday (WRDS/OptionMetrics-class spend) — wait until a free-data book earns Level-5 forward evidence.

**Q9 — What was rejected and why?** Falsified market sources: AS-05 cross-sectional stock momentum (rank IC −0.001, t=−0.07, 135mo; all variants 0.97-corr — F-015/16, NR-2), AS-07 short-term reversal (real gross, turnover kills it — 4 designs/4 deaths), AS-08 low-vol ranking (IC≈0, negative 2025 — F-018), AS-11 VIX-panic drift (WF worst −62% GFC — F-013), AS-12 microstructure ranking (flat every half-decade — F-019); AS-09 overnight premium dormant (exec-gated, F-006), AS-10 breadth timing retired (levered beta in costume, F-011). Rejected *claims*: vol-mgmt universality (F-020, 3/7), trend+vol additivity (F-014 — combo halves either parent's excess, a priced tail hedge not alpha), JSE unconstrained (F-021 — +18→+49 bps, strictly worse), and any month-level ψ̂/eigengap JSE timing gate (JSE_BOUNDARY_MAP §4 — p/n is the only predictor, and it is a design constant). Rejected as duplicate: H-E2 (= HYP-A4-03).

**Q10 — What should Alpha Lab do next?** (a) **Operational, before the next run:** commit-or-stash the uncommitted held-position pricing fix and add a same-date dedup guard — both sit on the nightly `--live` paper script (CANONICAL_STATE §4a/4b). (b) **Research pivot:** the cross-sectional price/volume lane is closed — stop re-running its funerals and stop adding correlated long-biased sleeves to AS-01 (0/3 add value). (c) **Run the 4 high-bucket testable-now experiments** already pre-registered (H-E1 reversal×liquidity, H-D1 MOC-vs-MOO fill, H-lw-target, H-idio-shrink) — each is a ≤40-line diff that retires or advances a live docket entry, though H-E1's ceiling is Level 1 and the two estimator probes are Estimator-class (no book). (d) **Fund the one honest new-information lane:** ingest FRED/VIX now and keep the PIT-earnings collector accruing toward n=300.

---

## Five-section verdict

### 1. WHAT IS KNOWN (Level 3, replicated in-domain — believe it)
- **AS-01, vol-managed US large-cap equity premium, is a real Market edge in its domain.** vol_managed_qqq beats SPY in 78% of 82 WF windows (+13.4pp median excess), positive across GFC/2011/2015/2018/COVID/2022, confirmed by 1y and non-overlapping 5y blinds. This is levered equity-premium harvesting with a vol-timing kicker (Moreira-Muir) — honest Market alpha of the risk-management kind, **not** a cross-sectional forecast. **Capped at Level 3.**
- **defensive_ensemble works as a capital-preserver (Portfolio alpha), not as a market forecast.** 84% positive WF, worst −18.3%, DSR 95.8%, flat 2022 — but value-vs-naive is only +1.4pp median excess. Its value lives in the drawdown column.
- **The 7 books are ~3 bets, one dominant.** n_eff=2.80 raw; the 3 vol books collapse to one factor (residual corr 0.79) and fail together in crises (corr 0.77) — no mutual crisis diversification.
- **The JSE/dispersion-bias correction is a bounded Estimator win (AS-13, Level 2).** Helps long-only min-var, monotone in p/n (max ~2.6 bps vol at n=42, always p<0.0001); hurts unconstrained (+18→+49 bps). Not worth deploying on a ~470-name book; the publishable object is the boundary, not a return.

### 2. PROVISIONALLY SUPPORTED (Level 2 — watch, forward evidence only)
- **AS-03 dual-momentum** (dual_momentum_gold/gem) — mechanistically a near-duplicate of AS-02; gold's GLD third slot is a confirmed 2024-26 regime artifact (13% of pre-2024 windows); gem is fragile (F-012). The two currently hold an *identical* position — live independence ≈0. Level 2, discounted.
- **AS-06 PEAD proxy** (gap_drift) — 1y blind +5.8% excess but WF worst −53.4% (F-009). The price-only proxy fires ~1/day and catches non-earnings shocks; the *real* earnings-surprise drift has never been tested (no PIT data). Level 2, watch.
- **AS-02 trend momentum** — Level 2-3, but only as a tail hedge inside AS-01 (F-014). A priced hedge (worst window −31%→−22%), not additive alpha.

### 3. CONTRADICTED (tested and refuted — do not re-run)
- **Cross-sectional stock momentum is dead in large caps** (0/10 rank IC, α≈0; F-015/16, NR-2). momentum_concentrated's tolerable windows came from construction, not selection, and it is value-destructive in the ensemble (P=0.07).
- **Vol-management does NOT replicate cross-market** (F-020, 3/7 clusters, p=0.77) — the edge is confirmed US-large-cap-specific; Level 4 refused.
- **Trend + vol is NOT additive** (F-014 — combo halves median excess).
- **Short-term reversal, low-vol ranking, VIX-panic drift, microstructure ranking, breadth timing** — all falsified (turnover/IC/drawdown). Overnight premium is real but execution-gated.
- **No month-level timer for the JSE effect exists** (JSE_BOUNDARY_MAP §4 — ψ̂ is just re-parameterized p/n; every within-n predictor p>0.3).

### 4. UNKNOWN (not yet tested — the honest frontier)
- **Any genuinely new information source.** No PIT earnings surprise, revenue, analyst revisions, coverage/dispersion, options-implied, IPO/lockup, or Russell/small-cap-PIT data exists in the repo. The entire program to date is price/volume + a thin EDGAR fundamentals slice on a single vendor.
- **Data-vendor robustness** — untested for *every* source (single vendor).
- **Trend-alpha vs levered-beta** — F-020 could not run the macro-regime axis (no FRED/VIX on disk). H-E3 is the highest-decision-value experiment on the board and is data-blocked.
- **Small-cap / less-efficient universes** — the one sanctioned momentum reopen (F-005/F-016) is blocked by the survivorship gap.
- **Execution alpha** — not measurable on daily open/close (no intraday/auction/tick). 0 sources.

### 5. CURRENTLY FORWARD-TESTING (Level 5, accruing — no verdict yet)
- **7 live paper books** accruing nightly NAV (paper-only; scheduler on; real-money exposure verified impossible).
- **Finnhub PIT-earnings collector** — 8 events / 2 names vs an n≥300 pre-registered gate; the only honest new-information track; months from testable.
- **ops-reality** execution-drag measurement (≤15 bps stocks / ≤5 bps ETFs targets) — enables the F-001/F-006 reopens if it clears.
- **News/sentiment feed** — ~10 months deep, forward-extendable.
- **4 pre-registered testable-now experiments frozen, not yet executed** (H-E1, H-D1, H-lw-target, H-idio-shrink).

---

## The program succeeded even though it found ~1 new edge

The charter said a decisive negative that kills a low-value lane is a win. This quarter delivered
several: the cross-sectional price/volume lane is **closed** with a measured 0/10; the vol edge is
**bounded** to US large caps (not universal); the watch-tier books are **shown non-incremental**
(0/3); and the JSE program is **correctly bounded** to long-only small-n. That is honest
map-making — it stops the lab from over-deploying capital on an over-counted book (7 names that are
really ~2.8 bets) and redirects scarce effort from an exhausted lane to the only unexploited one
(new-information / PIT data). **This is not a Medallion-like architecture and no such claim is
supported by these backtests** — it is one real, capped, single-market risk-management edge, honestly
measured, plus a clear list of what has not yet been tried.
