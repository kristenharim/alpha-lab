# Pre-registration — JSE beta-overlay regime map: does factor-1 shrinkage stabilize hedges more on noisier universes?

### EXP-2026-07-14-jse-regime-map

**Stage-0 note.** Kristen's call, 2026-07-14: reframe the single-factor JSE question from a
whole-panel verdict into a REGIME MAP — hold the method fixed (correct only the
theory-covered factor 1, F-027), vary the universe by factor SNR, and locate the boundary
where shrinkage earns its keep. Motivated by F-028 (ψ̂₁≈1 on large-cap ⇒ nothing to
correct): if the effect is real it must appear where the dominant factor is weaker.
Positioned as a beta risk-model overlay (hedge/weight stability), NOT a trading model.

**Hypothesis** (one falsifiable sentence, mechanism included):
JSE correction of the PCA factor-1 direction reduces month-to-month min-var weight
turnover more on lower-factor-SNR universes (small-cap) than on high-SNR universes
(large-cap), because ψ̂₁ falls below 1 only when the market factor is weak relative to
idiosyncratic noise — so on small-caps the shrinkage actually moves h₁ and damps the
sampling wobble that drives weight churn, while on large-caps ψ̂₁≈1 and it does nothing
(F-028).

**Layer touched** (exactly one) + registered baseline:
Layer B — estimator only. Fixed one-factor min-var construction (Σ = (s₁²/n)h₁h₁ᵀ + diag(D),
minvar_weights with the house 5% cap, monthly rebalance, hold one month) — the estimator
lab's existing machinery. Matched pair: jse1 (factor-1 JSE-rotated toward q, k=1, same τ)
vs pca1 (raw h₁), identical everything else. k is fixed at 1 deliberately: factor 1 is the
only factor with a valid JSE target (F-027), so the beta overlay corrects only it.

**Alpha type tag**: estimator (risk-model overlay; stability metric).

**Regime axis (the independent variable):** universe ∈ {large = S&P 500 (~500 names),
mid = S&P 400 (~400), small = S&P 600 (~600)} from the cached composite. Universe varies
factor SNR (small-caps are more idiosyncratic ⇒ weaker dominant factor), which is the lever
name-count alone cannot move. Windows n_est ∈ {63 (decisive), 252 (robustness)} reported
for the p/n cross-check. Data caveat (pre-stated): S&P 400/600 membership in the cache is
CURRENT, not point-in-time — survivorship inflates returns/vol but is near-neutral for the
turnover metric, which is why stability is the registered PRIMARY.

**Primary metric (pre-committed): weight stability.** Per (universe, window): mean monthly
L1 weight turnover ‖wₜ − wₜ₋₁‖₁ of the min-var book, paired jse1 vs pca1 month by month.
Secondary (reported, not decisive): realized next-month annualized vol; mean |Δψ̂₁| (how
far the correction actually moves the eigenvector) as the mechanism gauge.

**Decisive statistic (pre-committed), on n_est=63:** (i) small-cap jse1 median monthly
turnover < pca1 with paired p < 0.05 (shrinkage stabilizes where predicted); AND (ii) the
(jse1 − pca1) median turnover reduction is monotone large ≥ mid ≥ small (larger benefit on
lower-SNR universes) — the regime-dependence claim. Verdict:
- "regime-dependent stabilization" if BOTH hold;
- "universal small effect" if (i) holds on all three universes but the reduction is flat
  across them (no monotone regime gradient);
- "no effect" if (i) fails on small-cap;
- "harmful" if any universe shows jse1 turnover > pca1 at p < 0.05.
Mechanism check (reported): mean ψ̂₁ must be lower on small-cap than large-cap for the
hypothesis's premise to hold; if ψ̂₁≈1 on ALL cached universes, the honest finding is that
this data does not reach the noisy regime and a genuinely thin panel / shorter window is
required — a boundary result, not a null.

**Expected result:** ψ̂₁ decreasing large→small; turnover reduction 0 on large-cap
(F-028), growing on small-cap. Realized-vol effect small either way (JSE is a stability
story, not a return story, per the whole record).

**Alternative result:** ψ̂₁≈1 on all three (the market factor is well-estimated even in
small-cap at these p) ⇒ jse1≈pca1 everywhere, no gradient — meaning accessible S&P
universes never reach the regime where single-factor JSE bites, and the practitioner
value is confined to thinner panels than any S&P index.

**Failure / kill condition (stop-iterating):** one run of the 6 registered configs
(3 universes × 2 windows). No sub-sampled universes, no k > 1, no alternative stability
metrics, no shorter windows after seeing results. Any follow-up (synthetic-SNR panels,
multi-factor overlay) is a new prereg. Result → FAILURES.md (or CONFIDENCE note if the
gradient is found); no live spec touched regardless.

**Trial-ledger row:** same commit. n_trials = 6. **Derived from prior holdout results?**
YES — adaptive loop: reacts to F-028 (ψ̂₁≈1 on large-cap), F-027 (f1 = valid target),
F-021 (benefit scales with p/n). factor_lab read-only; all code in research/estimator_lab/.

---
**Result** (filled after the run, never edited above this line): **HARMFUL** (pre-committed
category: jse1 turnover > pca1 at p<0.05 on every universe). Factor-1 JSE does not stabilize
the min-var hedge — it churns it: monthly weight turnover rises on all three universes
(t=6–12, p≈0) for ≈0 realized-vol payoff, and the harm grows on noisier universes
(small +0.0064 vs large +0.0044 L1/month) — the weight-stability face of F-027/F-028
(perturbing an already-good market eigenvector). Premise only weakly holds: ψ̂₁ ≈ 0.976–0.996
on ALL cached universes incl. small-cap, so accessible S&P panels never reach the noisy
regime; the faint ψ̂₁ gradient (small 0.976 < large 0.979) is real and the churn tracks it.
Boundary statement: single-factor JSE's benefit lives nowhere in S&P large/mid/small-cap —
it needs genuinely thin panels or much shorter windows. Registered mid-cap (S&P 400) data
was not in the cache; fetched fresh (manifest: mid400_px) to run the design as written.
FAILURES.md F-029. Full tables + story: research/estimator_lab/REGIME_MAP.md.
