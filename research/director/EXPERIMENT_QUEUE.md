# EXPERIMENT_QUEUE.md

*Research Capital Allocator ranking — generated 2026-07-10. Objective: maximize information gain per unit cost (reduce docket uncertainty), NOT expected return. All 11 designs are decisive in every branch by construction; the ranking is driven by cost (implementation complexity + runtime + research overhead) and by whether the experiment retires a **currently-docketed open question** vs. probes a speculative new axis.*

## Scoring convention
- **P(success)** = probability the *treatment/hypothesis is confirmed* (as each design defines it). Low P is not penalized — a clean kill is full information.
- **score** = relative info-gain / total-cost, 1–10. Pre-registered/sanctioned reopens carry near-zero research overhead and score highest; 3-way clean partitions on cheap runtime beat expensive single-axis probes.
- **Buckets:** 4 high-confidence extensions (36%), 5 medium exploration (45%), 2 moonshots (18%).

## Ranked table

| # | id | bucket | layer | P(success) | score | kill condition | one-line design |
|---|---|---|---|---|---|---|---|
| 1 | **H-jse-weakfactor** | high | B | 0.42 | 9.5 | ψ̂ stays ≈1 at n=63 (regime unreachable) OR ψ̂<1 yet jse3≥pca3 (bridge dead in its own regime) | Rerun min-var at WINDOW=63 (3-line diff), paired jse3−pca3 Δvol + ψ̂ probe — the sanctioned F-021 reopen |
| 2 | **H-overnight-exec** | high | D | 0.60 | 9.0 | intraday gross Sharpe ≥ overnight (mechanism absent) OR overnight net ≥ baseline (promote, don't close) | Re-score frozen vol_managed_qqq weights on close→open vs open→close sessions at 2bps round-trip |
| 3 | **H-xmkt-etf-staleness** | high | A | 0.45 | 8.5 | \|t\|<2 on ≥4/7 ETFs on real SPY (collapse) OR signs miss pre-commitment (reduces to known beta-lag) | Country-ETF lead-lag on real SPY close (not EW proxy) vs pre-committed sign map, NW(5) t-stats |
| 4 | **H-band-turnover-core** | high | C | 0.55 | 7.5 | ETF-core net Δ > 17bps cost drag (band re-times exposure) OR stock-sleeve Δ ≈ ETF Δ (control cheap everywhere) | No-trade-band sweep on vol_managed_qqq (2bps) vs momentum_concentrated (10bps) — the docketed Layer-C exp #3 |
| 5 | **H-ewma-cov** | medium | B | 0.44 | 7.0 | ewma_pca3 − pca3 Δvol t ≥ −2 (n_eff loss swamps recency, F-021 lesson recurs) | Add EMA(hl=60) return-weighting to pca3 min-var, one paired-t on an axis orthogonal to dead corrections |
| 6 | **H-sector-leadlag** | medium | A | 0.43 | 6.5 | treatment 1d IC < +0.005 or \|t\|<2 or sign flips across half-decades | Sector-leader→follower rank IC, sector-common removed both sides — closes ic_screen's open interaction door |
| 7 | **H-max-lottery** | medium | A | 0.22 | 6.0 | orthogonalized MAX5 \|t\|<2 at 21d OR sign flips across the three half-decades | MAX5 skewness signal residualized on ivol/STR through the ic_screen pipeline — anti-mislabel test |
| 8 | **H-asymmetric-voltarget** | medium | C | 0.35 | 5.5 | Δworst-12m sign coin-flip across country cascades OR CAGR give-up ≥ half the median excess | Rate-limit only the re-lever leg of vol_managed; test worst-12m across ~3-4 country-ETF cascade regimes |
| 9 | **H-dispersion-timing** | medium | A | 0.20 | 5.0 | CSD partial \|t\|<2 OR wrong sign OR ΔR²<0.5pp (grounding already shows t=−0.32) | Add aggregate cross-sectional-dispersion regressor to a VIX-only forward-SPY regression; closes the aggregate loophole |
| 10 | **H-obsfactor-cov** | moonshot | B | 0.40 | 4.5 | turnover not sig. below pca5 (loadings don't stabilize weights — core mechanism dead) | Observable market+sector-ETF betas as the min-var factor model; test loading-persistence → turnover → net Sharpe |
| 11 | **H-rie-vs-mp** | moonshot | B | 0.30 | 3.5 | \|nls − mp\| < 5bps or paired p ≥ 0.05 (flat clip already sufficient) | Analytical nonlinear shrinkage vs the MP champion; hardest impl (p>n branch), likely null on strong-factor panel |

---

## Bucket rationale

**High-confidence extensions (1–4).** Three of the four (jse-weakfactor, overnight-exec, band-turnover) are *already pre-registered* — sanctioned reopens named in FAILURES.md F-021 and RESEARCH_OBJECTS open-experiments #2/#3 — so research overhead is ~0 and each is a ≤40-line diff on an in-repo panel running in <1 min. xmkt-etf-staleness is the cheapest way to adjudicate the strongest external claim (the applicant's contaminated EW-proxy lead-lag) and gates whether Layer-D tradability is even worth opening. "High confidence" = high confidence the experiment *resolves the docket*, not that the treatment passes.

**Medium exploration (5–9).** Orthogonal-axis probes and open-door closers. ewma-cov and sector-leadlag each attack a genuinely open question (time-weighting at large p; the ic_screen interaction door) at coin-toss P with modest code. max-lottery and dispersion-timing are cheap anti-mislabel / loophole-closing kills whose modal outcome is a registered negative — low headline P, but that IS the information. asymmetric-voltarget is the most machinery (spec fork) but uniquely multiplies one forbidden-to-tune QQQ-2008 draw into several independent cascade regimes.

**Moonshots (10–11).** Both open *new* Layer-B territory with speculative payoff and no docket backing. obsfactor-cov tests a new axis (observable-loading persistence → turnover → net Sharpe) untouched by the settled realized-vol frontier. rie-vs-mp is the highest-cost item on the board (30–45 min to code the p>n NLS branch) with the lowest prior of beating an already-near-oracle MP champion — worth one shot only because success would open a whole spectrum-shape family.

---

## Top-3 full pre-registration

### 1. H-jse-weakfactor  — *top pick*

- **Hypothesis:** The Goldberg/JSE dispersion-bias eigenvector correction, which was WORSE than raw PCA at n=252 (F-021: +18bps vol at k=3, t≈9.6), *reverses* and helps in its designed regime — short window / weak factors. At WINDOW=63, jse3 realized vol < pca3, paired-t p<0.05.
- **Mechanism:** JSE rotates each PCA eigenvector toward equal-weight q by ψ̂ᵢ² = max(0.01, 1 − p·δ²/σᵢ²). The correction only bites when ψ̂ is meaningfully below 1 (real dispersion bias present). At n=252 with strong S&P factors ψ̂≈0.93–0.997 — bias nearly absent, so the rotation only perturbs good eigenvectors. Shortening to n=63 raises p/n, shrinks σᵢ² estimates, and should drive ψ̂ well below 1 — the falsifiable premise "JSE helps iff ψ̂ ≪ 1."
- **Layer:** B (covariance estimator). The ONLY layer that differs between arms is jse=True vs jse=False rotation of the k=3 eigenvectors. Window, panel, cap (5%), book, universe, hold, cost all identical.
- **Expected:** Sign flip from +18bps (jse worse) to negative if the ψ̂ mechanism carries: order −10 to −50bps annualized vol, with median per-factor ψ̂ dropped to <~0.85 (vs 0.93–0.997 at n=252). Absolute vols will be higher for *every* estimator at n=63 (noisier window) — irrelevant; only the within-month paired jse3−pca3 delta at matched k=3 is the test.
- **Alternative outcomes (each retires a distinct branch):** (a) jse3<pca3 significant AND ψ̂<1 → confirms the bridge's actual falsifiable claim, the n=252 null was a regime artifact, JSE reopens as a live short-window risk estimator. (b) ψ̂ dropped below 1 but jse3≥pca3 → DECISIVE KILL: the noisy n=63 eigenvector / turnover counterparty dominates even in the designed regime; retire the Goldberg program outright. (c) ψ̂ stayed ≈1 at n=63 → the premise itself fails on this universe (S&P factors too strong regardless of window); bounds where the theory can ever apply and kills the "just shorten the window" hope.
- **Failure condition (kill):** Δ(vol)=jse3−pca3 ≥ 0, OR negative but p≥0.05 (native regime, no help). Register the matching negative in FAILURES.md; close F-021 as a hard cross-regime result.
- **Data:** research/hunt2026/panel_2005.parquet (PIT S&P 500, 2005–2026, 5413 rows) — already on disk, no download, free daily only. Same 137-month window set as the n=252 run → paired cross-reference valid. Costs already wired (10bps/side).
- **Minimal impl:** In research/estimator_lab/run_minvar.py change three lines — WINDOW=252→63 and the two output paths → results_n63.csv / summary_n63.csv (preserve the frozen n=252 result). Run `python run_minvar.py` (~20s). Read jse3 vs pca3 unconstrained in summary_n63.csv and recompute the paired-t on that column pair. estimators.py is UNCHANGED (ψ̂ form already implemented + self-checked). Secondary ~20-line psi_probe.py reusing `_pca_parts`: loop the same 63d monthly windows, print median ψ̂ᵢ per factor (i=0..2) — the n=63 analogue of the F-021 figure. Freeze exactly 3 params: WINDOW=63, k=3, CAP=0.05. No grid, no k-sweep, no long-only tuning (collapsed to ~0 at n=252, uninformative). Self-check: reproduce the frozen sample/pca ranking on the first window.

*Why top pick:* lowest cost on the board (3-line diff, existing panel, <1 min), P≈0.42 = maximum uncertainty, it is the explicitly pre-registered next Estimator-Lab experiment (F-021 + PLAN.md), and every one of its three outcomes retires a distinct live entry in RESEARCH_OBJECTS. Best infogain/cost, no branch leaves the docket where it was.

### 2. H-overnight-exec

- **Hypothesis:** The levered-equity-premium book vol_managed_qqq earns its Sharpe disproportionately in the overnight session (close→open); the effect is real but the doubled round-trip turnover cancels it, so overnight-only is not standalone-tradable.
- **Mechanism:** Lou-Polk-Skouras day/night tug-of-war — overnight drift concentrates the equity premium while intraday mean-reverts. Executing the SAME frozen weights close→open captures the premium leg but forces a daily round-trip (turnover = 2·|W|/day) at 2bps/side ETF cost.
- **Layer:** D (execution session) — the ONLY layer that changes. The economic hypothesis (A), 21d-RV estimator (B), and vol-target-0.25/cap-2x/0.05-band portfolio (C) are all frozen from registered vol_managed_qqq. This is RESEARCH_OBJECTS open-experiment #2, verbatim.
- **Expected:** Pre-run on raw 1× QQQ (2005–2026): overnight 11.7%/yr @ 12.5% vol (Sharpe 0.94), intraday 4.8%/yr @ 17.6% vol (Sharpe 0.28) — so gross criterion is very likely met. On the 1.33×-avg book: overnight gross ≈15–16%/yr, overnight cost ≈2·1.33·2bps·252 ≈13.4%/yr, overnight NET ≈+2%/yr (Sharpe 0.1–0.3), far below the 23.3% CAGR / 0.94 baseline. Predicted: both success criteria met, F-006 stays closed as "premium real, not standalone-tradable."
- **Alternative outcomes:** (A predicted) overnight gross Sharpe high, net < baseline → confirms real-but-untradable; permanently caps overnight as a decomposition *feature* (roadmap +0.05–0.15 Sharpe tier), closes the sanctioned reopen. (B surprise) overnight net ≥ baseline → doubled-cost assumption overturned; promote overnight execution to a real book headed for blind holdout — highest-value surprise. (C) intraday gross Sharpe ≥ overnight → falsifies the day/night mechanism in this QQQ/era; the 9%/yr overnight number was a return artifact, not a Sharpe edge.
- **Failure condition (kill / redirect):** intraday gross Sharpe ≥ overnight (mechanism absent) OR overnight net Sharpe ≥ baseline (do NOT close F-006 — promote instead).
- **Data:** research/hunt2026/panel_2005.parquet {open, close} for QQQ, 2005-01-03→2026-07-10, 5413 rows, zero gaps. Verified (1+r_on)(1+r_id)=r_cc to 2e-16 → open/close dividend-consistent, split is clean. Baseline from results5y/vol_managed_qqq.json. No new data.
- **Minimal impl:** ~20-line standalone scorer, NO harness signature change. W = load_spec('vol_managed_qqq').target_weights(panel); r_on = open/close.shift(1)−1; r_id = close/open−1; held = W['QQQ'].shift(1). For {cc, overnight, intraday}: gross = held·ret; cost = turnover·2bps (turnover_cc = W.diff().abs(); turnover_on = turnover_id = 2·W.abs()); net = gross − cost. Report Sharpe, CAGR, cost_drag. Assert cc-mode reproduces results5y Sharpe 0.94 (faithfulness self-check) and the r_on·r_id identity. Zero new params, no grid. Write to overnight_exec.md; update F-006 status + RESEARCH_OBJECTS #2 with the verdict.

### 3. H-xmkt-etf-staleness

- **Hypothesis:** A sign-heterogeneous nonsynchronous US-session lead-lag exists across country ETFs (EWC follows the US positively; Asian ETFs EWA/EWY/EWT/EWH/EWS/FXI reverse negatively via time-zone reversion), and it survives replacing the applicant's contaminated equal-weight US proxy with the real SPY close.
- **Mechanism:** Country ETFs trading on the US session price stale foreign closes. β_lag on lagged SPY captures the nonsynchronous update; the sign splits by session overlap — North-America EWC continues US direction, Asia (closed during the US move) reverses. Adding lagged SPY + own-ETF autocorr as the single registered Layer-A object isolates β_lag from the same-day global-equity beta.
- **Layer:** A (existence). Control = contemporaneous-only regression r_ETF(t+1)=a+b·r_SPY(t+1)+e (asserts zero lead-lag, absorbs same-day beta). Treatment adds exactly the two lagged predictors: +β_lag·r_SPY(t)+γ·r_ETF(t). OLS, no portfolio, no execution — only the predictive coefficient is added, so attribution is clean.
- **Expected:** Applicant's contaminated EW-proxy: β +0.12 (EWC, t=9.1), −0.06..−0.09 Asians (|t| 4.6–6.8), n≈5,400. A clean SPY contemporaneous control absorbs more common variance → predict shrinkage to |β_lag|≈0.03–0.08, |t|≈2–5; EWC-positive most robust, FXI/EWT-negative next. Decisive at n≈5,400 with no tuning.
- **Alternative outcomes:** PASS (signs hold on real SPY, EWC>0 at t≥3, ≥5/7 at |t|≥3) → genuine sign-heterogeneous nonsynchronous-pricing object; eliminates "EW-proxy contamination"; the ONLY branch that justifies opening the Layer-D tradability question (survives 2bps?). FAIL-collapse (|t|<2 on ≥4/7) → edge was contemporaneous stock-level leakage in the EW cross-sectional mean, cheapest highest-certainty kill, register negative. FAIL-wrong-sign (all-positive or EWC flips) → eliminates the novel time-zone-reversion mechanism specifically; collapses to the already-known positive global-beta lag (not novel, dies at 2bps).
- **Failure condition (kill):** signs match the pre-commitment on ≤4/7, OR EWC flips negative, OR all 7 come out same-sign positive, OR |t|<2 on ≥4/7. Register the matching negative result.
- **Data:** SPY close from research/hunt2026/panel_2005.parquet (real US close/close) + 7 country-ETF closes from research/hunt2026/panel_xmarket.parquet (407KB, confirmed on disk). Inner-join on Date, 2005–2026, ~5,400 rows. Close/close only, no open needed. EWU/EWG/EWZ carried as unscored auxiliary sign checks. No external fetch.
- **Minimal impl:** One ~40-line script research/hunt2026/robustness/xmkt_leadlag.py copying the panel-load pattern from robustness/ic_screen.py. Load SPY + 7 ETF closes, pct_change, inner-join. Per ETF fit control M0 and treatment M1 via statsmodels OLS cov_type='HAC', maxlags=5. Emit one table: β_lag, NW t, γ, pre-committed sign, match Y/N, ΔR² (M1−M0). Three frozen params: contemporaneous+own-lag control spec, NW maxlags=5, sign map with |t|≥3 / ≥6-of-7 thresholds. No grid, no portfolio, no cost model. One assert self-check: reproduce EWC β_lag>0 on the raw panel.

---

## Sequencing note
Run 1→3 first: all three are ≤40-line diffs on in-repo panels, each <1 min, and together they retire two pre-registered docket items (F-021 reopen, F-006 reopen) plus the strongest external claim. #4 (band-turnover) chains naturally after — it reuses the same harness. The five medium items are independent and parallelizable; the two moonshots wait until a high-value slot opens, and rie-vs-mp only if obsfactor-cov's new Layer-B axis shows life.
---
## Queue audit — 2026-07-10 (Research Director reconciliation pass)

- #1 H-jse-weakfactor: **EXECUTED** (5562106) — JSE beats PCA at n=63 long-only, worse
  unconstrained. Superseded by EXP-EST-CROSSOVER (full boundary map, pre-registered next).
- #7 H-max-lottery, #9 H-dispersion-timing: **DEPRIORITIZED** — price-only transforms;
  NR-2/F-016-019 argue the marginal IC probe on this universe is low-information. Reopen
  only per the failure-DB reopen rules (new data source or pre-registered conditioning).
- #6 H-sector-leadlag: retained in queue but ranked below the new-information track
  (earnings events) for the same reason.
- #2 H-overnight-exec, #4 H-band-turnover-core, #5 H-ewma-cov: retained as specced
  (pre-registered/sanctioned; next in line after the current trio).
- Moonshots #10/#11: retained.

**Selected next three (info-gain/cost, one per bucket):**
1. EXP-OPS-REALITY (high-confidence, layer D): paper execution reality agreement —
   measurement harness + pre-registered agreement thresholds.
2. EXP-EST-CROSSOVER (estimator, layer B): JSE crossover map — n ∈ {42,63,90,126,189,252},
   paired jse−pca, with ψ̂/eigengap logged per window; question: do observable estimation-
   state variables PREDICT when JSE helps, before portfolio construction.
3. EXP-IC-EARNINGS-FWD (medium exploration, layer A): forward-only earnings-surprise
   point-in-time collector + IC-as-data-accrues (the new-information track; Finnhub
   forward feed, no backfilled history claimed).

---
## Priority update — 2026-07-10 (post-review, Kristen's audit directive)

1. **AUDIT-JSE-RECONCILIATION** (running) — reproducibility investigation, blocks any
   estimator-rule lock. Not an experiment; produces a verdict class (reporting drift /
   method difference / bug) + the first-divergence line.
2. Maintain forward earnings collector (autopilot; no action until n grows).
3. Execution measurement (accrues nightly from Monday; first review ~Aug 7).
4. H-conditional-volmgmt (Priority D: pre-registered conditional form of vol management —
   risk premium × vol clustering × drawdown convexity), after the audit clears.
5. H-overnight-exec / H-band-turnover / H-ewma-cov as previously ranked.
DO NOT START: minute-bar work, new strategy hunts, roster additions (frozen in
DEPLOYMENT_MANIFEST.md until the +3m gate).
