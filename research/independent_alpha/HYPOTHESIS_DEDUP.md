# HYPOTHESIS_DEDUP.md — 24 candidate hypotheses vs the frozen research record

*Agent 2 (Dedup) · Independent-Alpha program · 2026-07-10*

Method: each candidate checked against `research/hunt2026/FAILURES.md` (F-001..F-021, NR-1..5),
`RESEARCH_OBJECTS.md`, `TRIAL_LEDGER.md`, `robustness/*.md`, `estimator_lab/{RESULTS,CROSSOVER}.md`,
the four live pre-registrations (`exp-ic-earnings-fwd`, `ops-reality`, `est-crossover`, `defensive-asset`),
`ALPHA_SOURCE_REGISTRY.md` (AS-01..15), `research/director/EXPERIMENT_QUEUE.md` (11 ranked + audit),
and against the other 23 candidates. Where a doc contradicted code/ledgers, code/ledgers won.

**Recommendation legend:** APPROVE (new source, register + queue) · REOPEN (a FAILURES reopen
condition is explicitly satisfied) · REJECT_DUPLICATE (same source already registered or another
candidate) · REJECT_PARAM (parameter variant of a settled test) · NEEDS_DIFF (distinct but overlaps
a docketed item; must report the delta vs it).

---

## Master table

| id | related prior tests | same-info? | same-mech? | same-horizon? | same-failure-mode? | reopen satisfied? | recommendation |
|---|---|---|---|---|---|---|---|
| HYP-A4-01-estrev | exp-ic-earnings-fwd (backward SUE), AS-06/F-009 | **no** (fwd consensus revision path, new field) | related PEAD, distinct driver (analyst anchoring, CJL) | yes (20d) | yes (large-cap arb, NR-2 prior) | n/a (new source) | **APPROVE** — forward-collect |
| HYP-A4-02-revqual | exp-ic-earnings-fwd (SUE only), gap_drift | **no** (revenue axis, new field) | PEAD quality/composition interaction | overlaps (20-40d) | yes (large-cap arb, thin cohorts) | n/a (new source) | **APPROVE** — forward-collect; free revenue feed unproven |
| HYP-A4-03-lowcov | exp-ic-earnings-fwd, F-016 reopen (momxearn), Hong-Lim-Stein | **no** (PIT coverage count, new field) | slow-diffusion PEAD conditioner | yes (20-60d) | yes (S&P coverage range compressed) | F-016 reopen (interaction conditioning) | **APPROVE** — canonical coverage-PEAD (absorbs H-E2); cheapest feed (free rec-count) |
| HYP-A4-04-disagree | exp-ic-earnings-fwd conditioner #2 (RETURN dispersion), DMS | **no** (per-name analyst dispersion ≠ panel return dispersion) | distinct (DMS overpricing + disagreement×surprise) | yes (20-60d) | yes (large-cap arb; noisy free proxy) | n/a (new conditioner, own prereg) | **APPROVE** — forward-collect; needs own prereg |
| H-FF-01 | **F-005** (index effect killed large-cap S&P 500) | same mech, **different universe** (600/400) | index-add forced demand | event-window | yes (passive-arb has grown in small caps too) | **YES — F-005 names this exact reopen** (S&P 600, survivorship-safe data) | **REOPEN** — data-blocked (no PIT 600/400 membership + delisted prices) |
| H-FF-02 | none in repo (no IPO/lockup data) | new source | supply shock, downward demand curve | event-window | borrow-cost / decay | n/a | **APPROVE** — data-build (EDGAR S-1 + survivorship post-IPO + borrow) |
| H-FF-03 | none in repo | new source | issuance pressure + placement reversal | event-window | info-vs-liquidity not separable in repo | n/a | **APPROVE** — data-build (EDGAR 424B5/8-K + survivorship + borrow) |
| H-FF-04 | **F-005** (large-cap index null = cautionary prior) | new source (Russell membership) | rules-based reconstitution flow | event-window | yes (most-arbitraged; heavy post-2007 decay) | not a direct F-005 reopen (adjacent) | **APPROVE** — data-build (Russell membership history absent); lowest prior in lane |
| H-C-carry | AS-04 VRP (US-equity variance carry — different), tsmom/AS-03, F-020 | **no** (basis/yield level, not past return, not US VRP) | carry premium (KMPV) | 1-3mo | short-vol crash; F-020 x-market non-replication | n/a (new source) | **APPROVE** — bond-carry slice free (FRED, not ingested); full x-asset licensed |
| H-C-sbcorr | F-012, F-020 (TLT/BIL leg does crisis work), dual_momentum_gold (momentum-picks TLT/BIL), AS-14 | new (corr second moment) | regime hedge-value (CSV) | 1-3mo | overlaps momentum-picked defensive leg | n/a | **NEEDS_DIFF** — data available; must beat frozen fixed-hedge AND momentum-picked leg; self-classed Portfolio/Estimator, not market |
| H-C-value | F-001/F-017/NR-1 (STR dead — different horizon/universe), AMP | new (5y asset-class reversal) | multi-year overreaction | 3-12mo | thin sample (~4 indep 5y windows) | n/a | **APPROVE** — data available; low power caveat |
| H-C-breakeven | F-020 (single-regime artifact caution) | new (breakeven spread) | inflation-expectation real-vs-nominal | 1-3mo | one inflation up-cycle → regime-count risk | n/a | **APPROVE** — FRED not ingested; severe single-regime power risk |
| H-D1-moc-vs-moo | **queue #2 H-overnight-exec** (session attribution — different Q), F-006, ops-reality prereg | fill-point of frozen target (no new predictor) | fill-timing cost, not a signal | per-rebalance | inside cost noise | RESEARCH_OBJECTS open-exp #2 adjacent | **APPROVE** — data available; actionable on LIVE books; distinct from #2 |
| H-D2-calendar-overnight | queue #2 (uniform overnight), F-006, F-019 (overnight-share flat) | calendar × overnight return | calendar-concentrated overnight premium | overnight | turn-of-month publication decay | n/a (time-series, not the cross-sectional tests killed) | **APPROVE** — data available; distinct from uniform overnight |
| H-D3-gap-defer | **NR-1/F-001** (reversal dead daily — direct headwind), D1 complement | signed gap on rebalance morning | conditional participation (urgent-flow avoidance) | per-rebalance | gaps may CONTINUE not revert (NR-1) | n/a | **APPROVE** — data available; honest low prior |
| H-D4-auction-imbalance | **F-019** (retired microstructure; "reopen only w/ higher-freq harness") | auction imbalance (NOT in repo) | auction reversion + exec quality | overnight | HFT-competed | F-019 reopen requires the data it lacks | **APPROVE→PARK** — hard data gap (no bid/ask/auction/tick anywhere); honest data marker |
| H-E1-reversal-x-liquidity-shock | F-001/F-017/**NR-1** ("vol-conditioned entry = the one untested angle"), ic_screen verdict | in-repo price+volume as STATE conditioner | liquidity-provision premium (Nagel/ACG) | 5-21d | electronic-MM compression post-2015 | **YES — NR-1 names it; ic_screen sanctions mechanism-based interaction** | **REOPEN** — data available; signal-space only (level-1, tradability still gated by NR-1 cost wall) |
| H-E2-earnings-surprise-x-coverage | **= HYP-A4-03-lowcov** (identical Hong-Lim-Stein PEAD×coverage) | same as A4-03 | same as A4-03 | same | same | F-016 reopen | **REJECT_DUPLICATE** of HYP-A4-03-lowcov (merge; A4-03 has the cheaper free-proxy path) |
| H-E3-trend-x-funding-inflation-regime | **F-020** (x-market universality — but NOT the macro-regime axis), F-014, F-011, ledger tsmom 2022 | macro regime conditioner (FRED, absent; VIX ≠ funding/infl) | trend crisis-alpha vs levered beta | regime (months-yrs) | few macro regimes; 2022-artifact risk | n/a — the axis F-020 could not run | **APPROVE** — FRED not ingested; re-grades the promoted family (high decision value, low power) |
| H-E4-momentum-x-earnings-confirmation | **F-016 reopen (momentum × earnings — sanctioned)**, NR-2, F-015, Novy-Marx | PIT earnings-surprise sign (earnings-fwd accruing) | fundamental momentum (earnings, not price) | 21-63d | post-2015 large-cap momentum winter | **YES — F-016 names momentum×earnings** | **REOPEN** — forward-collect (earnings-fwd pipeline already live) |
| H-lw-target | **estimator_lab RESULTS.md** ("LW-identity = blunt target", lost to MP), F-021 | LW shrinkage TARGET (only identity tested) | shrinkage-target, not spectrum | monthly | MP near-oracle (ψ̂~0.98) may dominate | n/a — flagged-open in RESULTS.md | **APPROVE** — data available; Estimator (not market); low prior vs MP |
| H-robust-cov | estimator_lab (all use Gaussian np.cov), F-021 | robust 2nd-moment estimate | moment estimator vs spectrum | monthly | n=252 moment already well-estimated (F-021) | n/a | **APPROVE** — data available; Estimator; coin-flip, bites in tails only |
| H-idio-shrink | estimator_lab _pca_parts (JSE leaves D untouched), Michaud | residual diagonal D | error-maximization at idio block | monthly | 5% cap may already blunt low-D names | n/a | **APPROVE** — data available; Estimator; only lever on the diagonal |
| H-cov-temporal-smooth | **queue #4 H-band-turnover-core** (weight band — different), **queue #5 H-ewma-cov** (within-window recency — opposite), NR-3 | sequence of Σ estimates (smooth path) | across-window stability for turnover | monthly | staleness at regime turns (NR-3) | n/a | **NEEDS_DIFF** — data available; distinct lever but adjacent to docketed #4/#5; must report delta vs both |

---

## Non-trivial calls (justification)

**H-E2 REJECT_DUPLICATE.** H-E2 and HYP-A4-03-lowcov are the *same* Hong-Lim-Stein hypothesis
(PEAD strengthens as analyst coverage falls), same information (PIT earnings surprise × per-name
coverage count), same 20d horizon, same failure condition (low-minus-high coverage IC diff, interaction
t≥2, n≥600). They differ only in framing lane. Kept HYP-A4-03 as canonical because it names the
**free** coverage feed (Finnhub `stock/recommendation` count-sum), making it testable a quarter sooner
than H-E2's I/B/E/S / premium-endpoint path. One pre-registration, not two.

**Two sanctioned FAILURES reopens (near-zero research overhead — the F-021/F-006 pattern).**
- **H-E1** satisfies NR-1 verbatim: *"vol-conditioned entry timing remains the one untested angle"*
  (Dai et al. NBER w30917), and `ic_screen.md`'s verdict explicitly sanctions *"an interaction
  hypothesis with a mechanism"* as the one open door. All data on disk. This is the cheapest,
  highest-info reopen in the whole batch. Caveat carried forward: even a confirmed conditional IC is
  **level-1 predictive only** — tradability stays gated behind NR-1's cost wall (≤2-3 bps/side or
  intraday), so it is a signal-space object, never promoted straight to a book.
- **H-E4** satisfies F-016's named reopen ("interaction conditioning (momentum × … earnings)"). Needs
  PIT earnings-surprise sign; the `earnings-fwd` collector is already accruing, so the data pipeline
  exists — only depth is missing. Forward-collect, do not backfill (yfinance cache is survivorship-biased).
- **H-FF-01** satisfies F-005's named reopen ("tested on S&P 600 adds … needs survivorship-safe data").
  Reopen is legitimate but **data-blocked** — the repo has no PIT 600/400 membership and no
  delisted-inclusive small-cap price panel. Reopen ≠ testable now.

**H-C-sbcorr / H-cov-temporal-smooth NEEDS_DIFF (distinct but adjacent).**
- H-C-sbcorr's correlation signal is genuinely new, but `dual_momentum_gold` *already* momentum-picks
  TLT vs BIL and so partially captures bond-hedge failure in rising-rate regimes (its own MECHANISM
  cites 2013/2018). Its own failure condition already says it must beat that leg. Honest classification
  stands: **Portfolio/Estimator**, not an independent market forecast — score it as a hedge (NR-5), never
  as additive alpha.
- H-cov-temporal-smooth is distinct from queue #4 (post-optimization no-trade *band* clips weights off
  the frontier) and #5 (EWMA reweights *within* a window for recency — opposite objective). But all three
  attack turnover on the same min-var harness; it must be run reporting the paired delta vs #4 and #5,
  or it re-measures a docketed lever.

**Nothing else is a duplicate or parameter variant.** The four Lane-F estimator hypotheses are four
distinct levers (shrinkage-target / moment-robustness / residual-diagonal / temporal-path) — none
touches the same layer as another, and none re-runs the settled JSE/MP/PCA eigenspectrum question
(F-010/F-021 closed). The three Lane-D execution hypotheses are three distinct fill-time levers, all
distinct from queue #2's session-attribution question. The Lane-A/-B new-information and forced-flow
sources have **no** prior test in the repo (no PIT earnings-revision, revenue, coverage, dispersion,
IPO, SEO, Russell, or small-cap index data exists — confirmed against DATA_GAP_MAP.md and the panels).

## Disposition summary

- **APPROVE (new source): 12** — A4-01, A4-02, A4-03, A4-04, FF-02, FF-03, FF-04, C-carry, C-value,
  C-breakeven, D1, D2, D3, D4(park), E3. *(15 including the two NEEDS_DIFF and the park.)*
- **REOPEN (sanctioned): 3** — H-FF-01 (F-005, data-blocked), H-E1 (NR-1, testable now), H-E4 (F-016, forward-collect).
- **NEEDS_DIFF: 2** — H-C-sbcorr, H-cov-temporal-smooth.
- **REJECT_DUPLICATE: 1** — H-E2 (→ HYP-A4-03-lowcov).
- **REJECT_PARAM: 0.**

**Survivors carried to HYPOTHESIS_QUEUE.md: 23** (all but H-E2). Of these, **10 are testable now**
(data_available_now=true): H-C-sbcorr, H-C-value, H-D1, H-D2, H-D3, H-E1, H-lw-target, H-robust-cov,
H-idio-shrink, H-cov-temporal-smooth. The other 13 require forward-collection or a data build and are
heavily discounted in the experiment ranking.
