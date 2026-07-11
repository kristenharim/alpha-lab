# HYPOTHESIS_QUEUE.md — surviving candidate alpha sources (post-dedup)

*Agent 12 (Rank) · Independent-Alpha program · 2026-07-10 · dedup: `HYPOTHESIS_DEDUP.md`*

23 survivors (H-E2 rejected as a duplicate of HYP-A4-03-lowcov). Each card is an alpha SOURCE
`(information · mechanism · who-pays)` triple, not a spec. **Class** distinguishes Market (independent
forecast) from Estimator / Portfolio / Execution (not independent forecasts — never counted as an edge).
All are evidence-ladder **level 0 (Hypothesis)** until tested. `data_now` gates the experiment ranking:
false ⇒ forward-collect / data-build first, heavily discounted.

Registry cross-ref: these are candidate *additions*; the live registry is `ALPHA_SOURCE_REGISTRY.md`
(AS-01..15). None duplicates a live AS source (checked in dedup).

---

## Lane A — Earnings & analyst information (all Market, all data_now=false, forward-collect)

**HYP-A4-01-estrev — Post-report analyst estimate-revision drift.** *Class: Market.*
Info: signed daily change in forward-consensus EPS for the next fiscal period, snapshotted ~30d
post-report (the revision path, not the realized backward SUE). Mechanism: sticky-consensus /
anchoring — analysts revise gradually, so the revision stream is fresh slowly-diffusing fundamental
info the surprise headline doesn't contain (Chan-Jegadeesh-Lakonishok, additive to PEAD). Who-pays:
headline-surprise + passive flows that reprice on the beat number but never re-trade the multi-week
revision stream. Target/horizon: rank IC of net-revision vs 5/20/40d forward return, partialled on
contemporaneous SUE; 20d. Distinct: new data field (not in events.jsonl), analyst-behavior driver
(orthogonal to dead price momentum, F-016). Kill: 20d IC<0.01 or t<1 at n≥400 PIT revisions, or IC→0
once SUE partialled out. Data: nightly forward-estimate snapshot → new `revisions.jsonl` (extend
`scripts/earnings_collect.py`); no PIT history exists. Pre-test: low-moderate.

**HYP-A4-02-revqual — Revenue-confirmed beats drift, EPS-only beats fade.** *Class: Market.*
Info: revenue actual vs consensus revenue, paired with EPS surprise (the second axis single-EPS SUE
collapses). Mechanism: top-line beats are more persistent than buyback/tax/cost-cut EPS-only beats;
market underreacts to double-beats, over-rewards low-quality EPS-only beats that revert
(Jegadeesh-Livnat revenue-surprise drift). Who-pays: headline-EPS reaction algos that don't decompose
the beat. Target/horizon: double-beat minus EPS-only-beat forward spread + composite quality IC; 20-40d.
Distinct: revenue dimension unused anywhere in repo; orthogonal to the two prereg conditioners. Kill:
double-minus-EPS-only 20d spread not >0 at t≥1.5, n≥200/cohort, or no incremental IC over SUE. Data:
revenue_actual/estimate/surprise per event (free source unproven — premium Finnhub or scrape),
forward-only. Pre-test: moderate mechanism, feasibility-gated.

**HYP-A4-03-lowcov — Low-coverage gradual-diffusion PEAD (absorbs H-E2).** *Class: Market.*
Info: analyst coverage count per name (rec-trend count sum) × SUE, PIT on report date. Mechanism:
Hong-Lim-Stein gradual diffusion — drift larger/longer where fewer analysts monitor; even in the S&P
500 mid-cap members (~6-12) vs mega-caps (40+) give real coverage dispersion. Who-pays: slow price
discovery in under-monitored names. Target/horizon: SUE→return IC in low- vs high-coverage tercile
(low-minus-high the pre-committed stat); 20-60d. Distinct: coverage-conditioned diffusion, new
conditioner (F-016 reopen door), NOT a prereg-conditioner slice. Kill: low-minus-high IC diff ≤0 or
|t|<1.5 at n≥300. Data: `stock/recommendation` count-sum (**FREE**, snapshot nightly) — cheapest new
feed in the batch. Pre-test: low (large-cap coverage range compressed) — high-value as a clean
registered negative that closes the F-016 momentum×earnings door.

**HYP-A4-04-disagree — Analyst forecast disagreement modulates the surprise reaction.** *Class: Market.*
Info: per-name analyst EPS-estimate dispersion (std, or free rec-count spread), a firm-level
fundamental-uncertainty axis — NOT the panel-wide return dispersion the prereg conditioner uses.
Mechanism: Diether-Malloy-Scherbina — high disagreement + short constraints ⇒ price reflects optimists
⇒ overpricing + muddied post-surprise signal; clean positive-SUE drift concentrates in low-dispersion
names. Who-pays: constrained shorts + optimism-biased holders in high-disagreement names.
Target/horizon: SUE→return IC by dispersion tercile + standalone dispersion→return IC (DMS main effect);
20-60d. Distinct: per-name analyst dispersion ≠ prereg's cross-sectional return dispersion; own prereg.
Kill: low-minus-high IC diff ≤0 or |t|<1.5 at n≥300 AND standalone dispersion IC ≈0. Data: estimate
std/high-low (premium) or free rec-spread proxy, forward-only. Pre-test: low-moderate (free proxy noisy).

## Lane B — Forced flows & small-cap events (all Market, all data_now=false, data-build)

**H-FF-01 — S&P 600/400 index-addition forced demand (F-005 REOPEN, less-efficient universe).**
Info: committee add announced ~1-5d pre-effective; IJR/IJH must buy a large float fraction over a
compressed window; tradable = announce-to-effective calendar × passive-AUM/float. Mechanism:
downward-sloping short-run demand curve — in the S&P 500 deep liquidity arbitrages it away (F-005:
-0.5%/21d, t=-0.79); in small caps the same forced demand hits a thin book ⇒ larger, slower impact,
then partial reversal. Who-pays: 600/400 funds forced to buy at inflated prices; premium → pre-positioned
arbs. Horizon: entry at announcement → effective (~1-10d) → reversal (~20-40d). Distinct: calendar-event
demand shock in a *different universe* than the entire vol/trend library; distinct from H-FF-04 (Russell
= rules-based, weeks-ahead). Kill: announce-to-effective abnormal <+0.5% or |t|<2 at n≥100 survivorship-
complete events, no reversal, or negative net of small-cap spreads. Data (absent): PIT 600/400 membership
w/ announce+effective dates incl. deletions, survivorship-complete small-cap prices incl. delisted,
per-name float + passive-AUM, small-cap spread model. Pre-test: moderate gross, low net.

**H-FF-02 — IPO lockup-expiration supply shock in low-float small/mid caps.** *Class: Market (short-biased).*
Info: lockup expiry date (90-180d, fixed in S-1/424B) × unlocked-overhang/float. Mechanism: anticipated
discrete supply increase meets downward demand curve; insiders/VCs sell for diversification ⇒ negative
drift into/around expiry, larger for low-float/low-coverage. Who-pays: holders who can't absorb the
supply; edge → pre-positioned shorts/liquidity providers. Horizon: short ~5-10d pre-expiry, hold to
~5-15d post. Distinct: supply-side corporate-calendar event on recent IPOs — asset class + event type
absent from the library; distinct from H-FF-03 (calendar-certain, no new info). Kill: expiry-window
abnormal not significantly negative (|t|<2, n≥100), not monotone in overhang/float, fully anticipated,
or borrow cost eats the short net. Data (absent): EDGAR S-1/424B lockup terms, survivorship-complete
post-IPO prices, float/shares series, small-cap borrow. Pre-test: moderate gross, low net.

**H-FF-03 — Follow-on / secondary offering pressure + post-placement reversal.** *Class: Market.*
Info: SEO/shelf-takedown announced via 8-K/424B5, priced at a discount; deal-size/ADV + placement
discount. Mechanism: (1) announcement dilution + adverse-selection signal + supply ⇒ negative reaction,
deeper in thin small caps; (2) once the block clears, temporary underpricing reverts over weeks.
Who-pays: diluted holders at announcement; reversal premium → liquidity providers who buy the discounted
block. Horizon: announce→~5d (pressure), then ~10-30d reversal. Distinct: discretionary
information-bearing issuance event, no library book models issuance; distinct from H-FF-01/04 (mechanical
demand) and H-FF-02 (no new info). Kill: post-placement reversal not significantly positive (|t|<2,
n≥100), smaller than round-trip cost, or fully explained by concurrent negative signal. Data (absent):
EDGAR deal terms, survivorship prices, shares/ADV, spread model. Pre-test: moderate on the drop, uncertain
net reversal.

**H-FF-04 — Russell 2000/1000 reconstitution migration-band forced flow.** *Class: Market.*
Info: rules-based, pre-computable — FTSE Russell reconstitutes on a May market-cap rank, effective late
June; adds/migrations predictable weeks ahead. Mechanism: the largest single-day forced US rebalance;
predicted adds face concentrated forced buying into the effective close, huge vs small-cap float ⇒ run-up
then reversal. Who-pays: Russell funds executing at the reconstitution price; premium → arbs replicating
the rank rule. Horizon: post-rank-day → June effective (~3-5wk) → ~10-20d reversal. Distinct: once-a-year
rules-based mega-flow; concretely distinct from H-FF-01 (committee, days-ahead) in information structure,
flow magnitude, counterparty-date predictability. Kill: rank-to-effective abnormal <+0.5% or |t|<2 at
n≥100, fully arbitraged, no reversal, or spreads eat net. Data (absent): survivorship-complete Russell
membership + effective dates, small-cap prices incl. delisted, PIT market-cap/float, spread model.
Pre-test: low-moderate — most-competed edge in the lane (heavy post-2007 decay); F-005 is the cautionary
prior.

## Lane C — Cross-asset macro / trend / carry

**H-C-carry — Cross-asset carry (yield/roll spread).** *Class: Market. data_now=false (bond slice free/FRED).*
Info: current forward-minus-spot / yield spreads across classes (curve slope+roll, FX forward points,
commodity basis, equity div yield) — explicitly NOT past prices. Mechanism: KMPV — a collateralized
futures return = carry + price move; carry is a mechanically observable expected-return component,
hedgers accept negative carry. Who-pays: hedgers/rebalancers on the low/negative-carry side.
Target/horizon: cross-sectional + TS ranking of class returns by current carry; 1-3mo. Distinct:
current basis, orthogonal to the whole trend/momentum/vol library; NOT AS-04 (US-equity VRP on one
instrument) — this is rates/FX/commodity/equity carry. Kill: carry-sorted spread t<2 or wrong sign net,
or loads >0.6 on tsmom/dual_momentum (trend in disguise). Data: Treasury CMT yields (FRED, free, not
ingested) for the bond slice; full x-asset needs licensed futures/forwards. Pre-test: medium (~40-45%);
post-2018 decay, short-vol crash risk.

**H-C-sbcorr — Stock-bond correlation regime forecasts the defensive leg (NEEDS_DIFF).**
*Class: Portfolio/Estimator — NOT market alpha. data_now=TRUE.*
Info: trailing realized SPY-TLT/IEF correlation (+sign), optionally × inflation-vol proxy — a slow
cross-asset second moment. Mechanism: correlation sign is set by dominant macro shock (growth ⇒ negative,
bonds hedge; inflation ⇒ positive, duration fails); regime is persistent/autocorrelated so trailing corr
predicts forward hedge value (Campbell-Sunderam-Viceira). Who-pays: 60/40 & risk-parity rebalancers
holding fixed duration regardless of regime (2022). Target/horizon: forward hedge-value/sign to select
TLT/BIL/GLD defensive leg; 1-3mo. Distinct: cross-asset second moment (not price/trend/vol); attacks the
F-012/F-020 weakness that the dual-momentum TLT/BIL leg blindly assumes bonds hedge. **Must beat** the
frozen fixed-hedge leg AND the momentum-picked leg dual_momentum_gold already runs — else it reproduces
an existing capture. Kill: forward corr sign not forecastable OOS (hit ≤50%), no worst-window improvement
over fixed-TLT, or reproduces the momentum-picked leg. Data: SPY/TLT/IEF/GLD/BIL in panel_2005 (present).
Pre-test: high the sign is forecastable; low-medium net portfolio improvement. Report as a hedge (NR-5),
never additive alpha.

**H-C-value — Cross-asset value (5y reversal) diversifier.** *Class: Market. data_now=TRUE.*
Info: ~5y past return / price-vs-own-history at asset-class level (SPY/QQQ/EFA/EEM/TLT/GLD/DBC/VNQ +
country ETFs), value = negative 5y return. Mechanism: Asness-Moskowitz-Pedersen "Value & Momentum
Everywhere" — classes cheap vs own long-run level earn higher returns (multi-year overreaction/reversion),
negatively correlated with 12m momentum. Who-pays: multi-year trend-extrapolators + performance-chasers.
Target/horizon: cross-sectional class-return IC by 5y-reversal score; 3-12mo, quarterly-annual rebalance.
Distinct: opposite sign + 5y horizon nothing in the library uses (dual_momentum/tsmom = 12m same sign, so
value is by construction diversifying); distinct from dead short-horizon reversal (F-001/F-017 — daily,
single-stock). Kill: class 5y-value rank IC ≤0 or t<2, or value stream corr >0.6 with inverted 12m-mom, or
too few independent 5y windows. Data: panel_2005 (~21y, present) — but only ~4 non-overlapping 5y windows
⇒ low power. Pre-test: low-medium (~30-35%), measurement-risk-dominated.

**H-C-breakeven — Breakeven-inflation trend rotates real-asset menu vs nominal duration.** *Class: Market.
data_now=false (FRED).*
Info: market breakeven inflation (nominal minus TIPS yield, FRED T10YIE) and its trend — forward-looking
macro expectation. Mechanism: rising breakeven ⇒ real assets (DBC/GLD/USO/TIP) earn the inflation premium
while nominal duration + long-duration growth lose; slow-repricing counterparty (2021-22). Who-pays:
nominal-duration + long-duration-growth holders slow to reprice inflation shifts. Target/horizon: real
assets vs TLT/IEF/QQQ conditioned on rising/falling breakeven; 1-3mo. Distinct: macro fundamental (not
price/trend/vol), different menu; distinct from H-C-carry (carry = yield earned; breakeven = inflation
forecast). Kill: breakeven-conditioned real-vs-nominal spread t<2 or wrong sign OOS, explained by rate
level / duration short, or loads >0.6 on tsmom commodity legs. Data: FRED breakeven (free, not ingested);
TIP-vs-IEF is a crude contaminated proxy. Pre-test: medium (~35-40%) but **one inflation up-cycle in
2005-2026 ⇒ single-regime trap (F-020 lesson)**; pre-register a pre/post-window split.

## Lane D — Execution & microstructure

**H-D1-moc-vs-moo — Close (MOC) vs next-open (MOO) fill point for the live vol books.** *Class: Execution.
data_now=TRUE.*
Info: signed overnight gap (open_t/close_{t-1} − 1) relative to each book's intended rebalance direction —
fill point of the frozen target, no new predictor. Mechanism: vol/trend books rebalance in the direction
of recent drift; the live 20:30 runner fills at next open, paying an overnight gap positively correlated
with its own trade sign (adverse-selection leakage). MOC books one session earlier and skips the correlated
gap. Who-pays: the book itself — MOC recovers donated slippage (no external alpha). Target/horizon: Δ net
return/Sharpe of vol_managed_qqq (+2 QQQ siblings) under MOC vs MOO, same weights, 2bps/side; per-rebalance,
2005-2026 + live ledger. Distinct: not a vol/trend signal; distinct from queue #2 H-overnight-exec (which
asks if overnight is standalone-tradable) — this asks which fill point the LIVE book should use, directly
actionable. Kill: MOC−MOO net Δ ≤0 over the sample AND forward ledger (gap not adversely correlated). Data:
panel open/close + frozen target_weights + live fill prices in ledgers/hunt2026/*.jsonl. Pre-test: ~55%.

**H-D2-calendar-overnight — Calendar-selective overnight premium harvest (turn-of-month + pre-holiday).**
*Class: Market/Execution. data_now=TRUE.*
Info: deterministic calendar (month-end first/last, pre-holiday) × QQQ/SPY close→open return. Mechanism:
overnight premium isn't uniform — turn-of-month settlement/rebalance/reinvestment demand + pre-holiday
drift carry a disproportionate share; harvest ONLY the ~30-40 flagged nights/yr, cutting the every-night
turnover that kills the uniform book ~6-8x. Who-pays: month-end/reinvestment + pre-holiday price-insensitive
buyers. Target/horizon: flagged-vs-unflagged overnight mean + net Sharpe of the flagged-only book after
2bps; overnight, ~30-40x/yr. Distinct: calendar-conditioned time-series harvest — distinct from queue #2's
uniform overnight book (dies on turnover) and from F-006/F-019 cross-sectional tests; trigger is a public
calendar, not price. Kill: flagged mean ≤ unflagged (t<2) or flagged-only net Sharpe ≤ uniform net Sharpe.
Data: QQQ/SPY open/close (present) + pandas market calendar (no download). Pre-test: ~40% (turn-of-month
well-published/decayed; pre-holiday less so).

**H-D3-gap-defer — Adverse-gap execution deferral on forced open fills.** *Class: Execution. data_now=TRUE.*
Info: realized overnight gap on each rebalance morning, signed by trade direction. Mechanism: runner fires
post-close so MOC is unreachable; worst fills are mornings that already gapped hard in the trade's
direction; defer one session when the signed gap exceeds a threshold — a persistent trend target recovers
most of the missed move while skipping the gap-day slippage. Who-pays: urgent overnight-flow gap-chasers the
naive book paid for immediacy. Target/horizon: Δ net return/tracking-drag of defer-on-adverse-gap vs
always-open-fill, 2bps/side; per-rebalance, ~10-20% of days. Distinct: complement of D1 (D1 = change venue;
D3 = conditional participation when venue is fixed at open). Kill: deferred net < always-fill beyond cost
saved (gaps continued not reverted), or threshold param-fragile across pre/post-2015. Data: panel open/close
+ frozen targets (no intraday needed). Pre-test: **~35% — NR-1 headwind** (reversal dead daily; if gaps
continue, deferral loses); the narrow adverse-gap-tail reversion is exactly the bet under test.

**H-D4-auction-imbalance — Closing-auction order-imbalance signal (DATA-GAPPED → PARK).** *Class:
Execution/Market. data_now=false.*
Info: exchange closing-auction imbalance feeds + auction prints (NOT in repo — grep confirms no bid/ask,
spread, auction, imbalance, VWAP, tick or minute data anywhere). Mechanism: auction concentrates volume;
published imbalance predicts close→open and partially reverts; a book could time rebalances into the
auction (best liquidity) and/or lean on the imbalance sign. Who-pays: forced auction participants demanding
close prints. Target/horizon: close→open conditioned on imbalance + auction-vs-open effective spread;
overnight. Distinct: only lane hypothesis touching true intraday microstructure; the honest F-019 "reopen
with a higher-frequency harness" marker — it *is* that harness, gated on data the repo lacks. Kill (once
data exists): imbalance→overnight |t|<2 AND auction spread ≥ open spread. Data: NYSE/Nasdaq Order-Imbalance
+ auction prints — acquisition is the blocker. Pre-test: unquantifiable without data. **PARK** until data.

## Lane E — Conditional interaction effects

**H-E1-reversal-x-liquidity-shock — Reversal ranking is conditional on liquidity-demand intensity (NR-1
REOPEN).** *Class: Market (signal-space, level-1 ceiling). data_now=TRUE.*
Info: in-repo price+volume as a STATE conditioner (21d volume-shock z + Amihud illiquidity spike), not a
standalone signal — the one axis NR-1 names untested. Mechanism: Nagel "Evaporating Liquidity" /
Avramov-Chordia-Goyal — reversal is a liquidity-provision premium whose price spikes with demand intensity;
21d reversal has real IC only in names/periods with a liquidity shock, ~0 elsewhere (the interaction the
unconditional IC averages away). Who-pays: impatient demanders during shocks (reconstitution, forced
deleveraging, capitulation, hedging cascades). Target/horizon: 5/21d forward IC within the top
liquidity-shock tercile, sector-neutral; 5-21d. Distinct: market-neutral cross-sectional, resurrects a dead
signal via a state variable (not leverage-on-beta); if confirmed it is a conditional-IC estimator object,
not a book. Kill: interaction |t|<2 or top-tercile 21d IC<0.02 at n≥120 monthly formations — no post-hoc
shock/horizon/winsor rescue. Data: panel close+volume + sectors (all on disk). Pre-test: 0.35. **Ceiling:
even if confirmed, level-1 PREDICTIVE only — tradability stays gated by NR-1's cost wall (≤2-3 bps or
intraday); a signal-space hypothesis, not a strategy.**

**H-E3-trend-x-funding-inflation-regime — Is the promoted family's excess trend-alpha or levered beta?**
*Class: Market (re-grades a live source). data_now=false (FRED).*
Info: macro regime conditioner absent from every panel — PIT funding (fed funds / 2y / term spread) +
inflation (CPI surprise / breakeven), aligned to the FROZEN weights of vol_managed_qqq / trend_vol_qqq —
the axis F-020 could not run. Mechanism: managed-futures crisis alpha (Moskowitz-Ooi-Pedersen) pays most in
sustained macro trends (2022, tsmom +13.7%); hypothesis: the family's SPY-excess loads on the funding/
inflation regime; in easy-money mean-reverting regimes the gate whipsaws and excess vanishes. Who-pays:
institutions forced to de-risk/re-hedge on regime shifts. Target/horizon: rolling-12m SPY-excess of the
frozen weights vs contemporaneous regime; regime-length (few independent draws). Distinct: the ONLY
hypothesis interrogating the promoted books themselves, on the exact axis F-020 lacked; adjudicates trend
ALPHA vs levered BETA and **re-grades the family's confidence level**. Kill: regime interaction |t|<2 across
≥3 episodes OR realized-equity-vol explains the excess better (higher partial R²) — then confirmed as
beta/vol-timing (supports F-020). Data: frozen weights (present) + PIT FRED (absent; VIX ≠ funding/infl).
Pre-test: 0.25 — few macro regimes, 2022-artifact risk, beta-null well-evidenced (F-020/F-014/F-011).

**H-E4-momentum-x-post-earnings-confirmation — Fundamental momentum (F-016 momentum×earnings REOPEN).**
*Class: Market. data_now=false (earnings-fwd accruing).*
Info: PIT earnings-surprise confirmation (sign of most-recent SUE within the formation window) conditioning
12-1 price momentum. Mechanism: Novy-Marx "Fundamental Momentum" / CJL — price momentum is a noisy proxy
for earnings momentum; a trend predicts continuation only when backed by a real earnings surprise;
unconfirmed trends are noise/about-to-reverse, so pooling dilutes IC to the ~0 F-016 measured. Who-pays:
underreactors to earnings news (same PEAD rent as A4-03 via the price-trend lens). Target/horizon: 21/63d
forward IC of 12-1 momentum within the earnings-confirmed subset, sector-neutral; 21-63d. Distinct:
separates price momentum (DEAD, F-016/NR-2) from fundamental momentum — the one F-016-sanctioned reopen not
yet tested; NOT momentum_concentrated (construction, F-015); distinct from A4-03 (conditioner is
trend-confirmation, not attention). Kill: confirmed-subset 21d IC<0.02 or not exceeding unconfirmed by t≥2
at n≥600 PIT-confirmed formations — momentum stays dead across a second measurement space. Data: panel
close (present) + PIT surprise sign (earnings-fwd, accruing; yfinance cache is survivorship-biased,
unusable). Pre-test: 0.25.

## Lane F — Estimator improvements (all Estimator alpha — NOT market forecasts; all data_now=TRUE)

**H-lw-target — Ledoit-Wolf shrinkage TARGET upgrade (constant-correlation / single-index vs identity).**
Info: the estimation window's average pairwise correlation the scaled-identity target discards — 2nd-moment
only. Mechanism: the lab's `lw` shrinks toward σ̄²·I (zero-avg-corr prior, wrong for one-factor equities);
RESULTS.md flags it "a blunt target" (highest turnover 3.23, lost to MP 11.64% vs 11.27%). Ledoit-Wolf's
own constant-correlation (or single-index) target keeps the dominant common correlation ⇒ shrunk matrix
closer to truth, min-var weights churn less. Who-pays: nobody — recovers the mis-specified-prior drag
(Estimator, level-2, not a forecast). Target: realized next-month vol + net Sharpe of unconstrained &
long-only min-var, paired per month vs `lw` and vs `mp`, 137 months. Distinct: only ONE LW variant (identity)
was tested; MP/JSE/PCA regularize the eigen-SPECTRUM — this is the shrinkage-TARGET, the specific "blunt
target" RESULTS.md left open. Kill: LW-CC minus LW-identity vol Δ ≥0 (paired p≥0.05) in both books. Data:
panel_2005 + sklearn ledoit_wolf + ~15-line closed-form CC shrinkage. Pre-test: moderate it beats
LW-identity, low it beats MP (F-021: MP near-oracle).

**H-robust-cov — Tail-robust covariance (Gaussian-rank / winsorized correlation) → MP clipping.**
Info: same window, 2nd-moment estimated robustly to fat tails (crash-day leverage removed). Mechanism: every
lab estimator is built on np.cov (Gaussian MLE); min-var w∝Σ⁻¹·1 is exquisitely sensitive to outlier-day
entries; a Gaussian-rank (Spearman→Pearson) or winsorized correlation before MP clipping should lower OOS
vol, concentrated in high-dispersion/post-shock months. Who-pays: nobody — tail-contamination drag
(Estimator, level-2). Target: realized vol + net Sharpe of robust-then-MP min-var, paired vs MP champion,
split by dispersion/VIX regime; 137 months. Distinct: changes the ESTIMATOR of the moment itself, orthogonal
to all eigen-spectrum regularizers and to JSE's eigenvector rotation. Kill: robust-MP minus MP vol Δ ≥0
(p≥0.05) overall AND no significant negative Δ in the top-dispersion tercile. Data: panel_2005 + scipy
rankdata. Pre-test: coin-flip (F-021: n=252 moment already well-estimated; likely bites only at short
windows / tails).

**H-idio-shrink — Idiosyncratic-variance shrinkage inside the PCA/JSE factor model.**
Info: the factor-model residual diagonal D (per-name idio variance), the noisiest block at n~252 — no return
signal. Mechanism: in pca_cov Σ=VΛV'+diag(D); min-var puts its largest weights on smallest-D names, whose low
D is often a downward estimation error (Michaud error-maximization); James-Stein shrinkage of D toward its
cross-sectional (or sector) mean cuts that error-loading and lowers OOS vol without touching factor
structure. Who-pays: nobody — the optimizer's own error-max drag (Estimator, level-2). Target: realized vol +
net Sharpe of idio-shrunk pca3/pca5 (and jse), paired vs unshrunk, both books; 137 months. Distinct: the ONLY
lever on the residual DIAGONAL — JSE rotates eigenvectors (leaves D untouched, verified in estimators.py
_pca_parts), LW/MP act on the spectrum, EWMA reweights returns. Kill: idio-shrunk minus unshrunk vol Δ ≥0
(p≥0.05) in both books — name the frozen 5% cap as the confound. Data: panel_2005 + _pca_parts + ~10-line
diagonal shrink. Pre-test: moderate unconstrained, low long-only.

**H-cov-temporal-smooth — Turnover-aware temporal covariance smoothing, judged on NET Sharpe (NEEDS_DIFF).**
Info: the SEQUENCE of monthly Σ estimates — smoothing the estimator's PATH; no new market data. Mechanism:
turnover is what separates NET Sharpe (LW 0.35@3.23 vs MP 0.71@1.10); a convex blend
Σ̃_t=(1−α)Σ̂_t+αΣ̃_{t−1} smooths the risk-model path ⇒ consecutive min-var weights move less ⇒ lower
round-trip cost ⇒ higher net Sharpe at ~equal gross vol, provided smoothing doesn't stale through a regime
turn. Who-pays: nobody — the churn's round-trip cost (Execution/Estimator, level-2). Target: full-period net
Sharpe (10bps/side, wired) + turnover at a small pre-registered α grid vs α=0, on MP & pca3; gross vol as
guardrail; 137 months. Distinct: distinct from queue #4 (post-optimization no-trade BAND clips weights off
the frontier) and queue #5 H-ewma-cov (within-window recency, opposite objective) — this smooths the risk
MODEL across windows. **Must report the paired delta vs #4 and #5** or it re-measures a docketed lever. Kill:
no α>0 improves net Sharpe vs α=0 at equal-or-lower gross vol. Data: panel_2005, costs wired. Pre-test:
moderate net-Sharpe by construction, low it survives the gross-vol guardrail (NR-3 staleness at 2022-turns).
