# Handoff — floor-diagnostic pipeline (solo research project, Kristen)

## Framing (do not drift)
Solo empirical research on finite-sample reliability diagnostics for hybrid factor risk
models. Object = FACTOR EXPOSURE ESTIMATION ERROR and the observable out-of-subspace floor.
NOT a minimum-variance portfolio project (that framing was corrected mid-project; min-var
results exist in this repo's history but are a separate closed line — F-021..F-031).

## The paper this is grounded in
Kercheval–Gunther–Bernstein–Yao–Lan–Lin–Goldberg, "Estimation Error in Latent
High-Dimensional Factor Models" (2026) — Kristen's CDAR/Goldberg lab. Local PDFs:
`14-Lab/reading/papers/Concentration 1 (reference).pdf` + `Concentration 2 (Nick summary).pdf`
(iCloud Obsidian vault). Theorem 1: sin²∠(h_j,b_j) → out-of-subspace floor 1/(1+SNR_j)
[estimable] + weighted in-subspace rotation [provably NOT estimable, Gurdogan–Shkolnik].
Corollary 1: ℓ/θ_j (bulk-mean over j-th top eigenvalue of the dual Gram) is a data-only,
consistent lower-bound estimator of exposure error. Regime: p→∞, n FIXED (not MP).

## Established findings (5 pre-registered phases, all committed/pushed in alpha-lab)
1. **Floor survives residualization** (oracle known-factor removal ≈ no-op vs baseline;
   the rank-deficient-noise/isotropy worry is negligible at k_F/p ≈ 1%).
2. **Finite-sample bias law:** the raw floor UNDER-reports true out-of-subspace error with
   slack ≈ n/(2p). Raw floor trustworthy at ~5% only for p/n ≳ 15.
3. **Corrections:** C3 = floor + 0.5·n/p works for p/n ≳ 7 (≤3%), bends at 4–7, OVERcorrects
   below ~4 (law is first-order only). C4 = MP-edge trust screen (trust iff SNR̂ >
   2√(n/p) + n/p + 0.5) is a clean success everywhere incl. residualized panels. C3 trades
   the bound property for accuracy (coverage 1.0 → 0.7).
4. **Leakage:** with misaligned known factors, leaked strong-factor structure passes the
   screen with low floor 100% of the time (the trap). Full-window detector — D_j = R² of
   residual-factor return series on estimated known-factor returns, F-test — separates
   leaked/genuine at AUC 0.98, FNR ≤ 0.07, FPR ≤ 0.12.
5. **Mechanism adjudicated:** split-sample detector RAISED FPR (0.22) while oracle stays
   0.01 ⇒ the "false positives" are PARTIAL MIXING — sample eigenvectors mix leaked and
   genuine directions (Theorem 1's in-subspace rotation materializing as mixed provenance).
   Leakage is a continuum: use the FULL-WINDOW detector with D_j as a continuous SCORE.

## The validated pipeline (frozen)
Per residual statistical factor: (1) C4 screen → discard if below the MP-edge cut;
(2) floor, + n/(2p) correction only if p/n ≥ 7; (3) full-window leakage score D_j —
low floor is only trustworthy-as-genuine if D_j is near the k_F/n noise level.

## Where everything lives
alpha-lab repo (github.com/kristenharim/alpha-lab), `research/estimator_lab/`:
- Prereg (all 5 phases): `FLOOR_RESIDUAL_MEMO.md` (phases appended, each frozen pre-run)
- Runners: `run_floor_residual.py`, `run_floor_calibration.py`, `run_floor_phase3.py`,
  `run_floor_leakage.py`, `run_floor_split.py`
- Results: `FLOOR_RESIDUAL.md`, `FLOOR_CALIBRATION.md`, `FLOOR_PHASE3.md`,
  `FLOOR_LEAKAGE.md`, `FLOOR_SPLIT.md` (each has a Story section with honest mechanism notes)
- Sim conventions: known-truth MC, Y = B_F f_F + B_R f_R + Z; SNR_j = n·‖β_j‖²/(p·δ²);
  dual-space PCA (h_j = Yv_j/√(npθ_j)); SNR ladder {3,1.5,.8,.4,.15}; k_F=4 strong
  fundamentals; misalignment = qr(u_F + mis·noise); seeds 0–3 used; N_MC=200.

## Process rules that governed this work (keep them)
- Freeze a short prereg (memo addendum) with exact success/fail/ambiguous rules BEFORE code.
- Held-out cells + fresh seeds for evaluation; never evaluate against total eigenvector
  angle when the target is the estimable out-of-subspace component only.
- On failure: diagnose mechanism, never tune thresholds post-hoc. Own rule-drafting bugs
  openly (two were caught and recorded in the artifacts).
- Commit results + story; pull --rebase before push (repo rule; an hourly STATUS publisher
  also pushes to this repo).
- factor_lab (~/projects/factor_lab, the lab's repo) is READ-ONLY; this project is separate
  from Kristen's CDAR deliverable to Alex (her Davis–Kahan rotation-bound notebook) and
  must not be represented as it. Theory derivations (finite-p slack law, MP-edge threshold,
  hybrid Corollary 1) are HERS to take to the lab — sims may motivate, not substitute.

## Phase 6 (real data) — DONE 2026-07-14
FF3+MOM-residualized S&P, 14 primary 63d windows (2021-11→2025-11, p≈460-500, p/n≈7.5).
Prereg + reviewer dispositions: `FLOOR_REALDATA_MEMO.md`; runner `run_floor_realdata.py`;
results `FLOOR_REALDATA.md` (+ story, research log); diagnostics `run_floor_realdata_diag.py`
→ `FLOOR_REALDATA_DIAG.md`; per-slot rows `floor_realdata.csv`. FF pull manifest-logged
(`data/raw/ff_factors_daily.parquet`). Headlines:
6. **C4 does not transfer as calibrated:** on real heteroskedastic heavy-tailed residuals
   (even vol-standardized) the shuffled-panel false-pass rate is ~14% (10-20% across seeds);
   the isotropic 0.5 safety margin is fully consumed. Real-data screening needs an empirical
   per-rank shuffled null; against that null, real PC2-5 pass 14/14 per rank (61/70 total).
7. **Phase-4's trap materializes on real data and the detector catches it:** residual PC1 =
   leakage footprint (high D 0.49 + lowest floors ~0.19 = one mechanical event, corr(D,floor)
   = -0.70; beta drift median 17° between adjacent windows). Low PC1 floors are NOT
   trustworthy-as-genuine. D vs D′ gaps (published-FF vs B̂-implied regressors) expose
   estimated-factor leakage the published series can't see.
8. Bucket shares are qualitative only (27-60% material range under disjoint-beta
   subsampling); low-D factors are NOT "risk beyond standard models" (industry blindness).
## Phase 7 + Stage 2 (attribution program) — DONE 2026-07-14
Kristen chose the FF+industry arm and expanded to a two-stage attribution program.
Phase 7 (`FLOOR_INDUSTRY*`): 11-GICS-dummy arm. Verdict FAIL on a mis-set control bar
(null-relative it passes at 60.6% excess removal); errata section is REQUIRED READING —
a_match headline retracted (mechanical null 0.991), theme-vs-vol-coupling unresolved,
"not sector risk" downgraded to "not annihilated by sector-MEAN projection". Vetted
panel: 5 label-4 slots / 4 windows / 0 recurrent ≈ spot-checks only.
Stage 2 (`FLOOR_ATTRIB*`, final memo `ATTRIB_PROGRAM_MEMO.md`): all 7 hunt2026 books =
known-factor exposure under the frozen ladder (raw +17–42%/y all die at +FF3+MOM);
adversarial review established the windowed design is BLIND to timing alpha (the books'
thesis); static-beta diagnostics: timing channel +9–11%/y point est. unproven; gold
+30.7%/y significant but hindsight-compromised; VRP override was unfireable as frozen
(corrected ρ 0.26). Single best next action (in memo): run the frozen sibling
blind-window attribution + a timing term over 2014→2026.
Process lesson (4 rule-drafting defects this program): every frozen numeric bar ships
with its null value and a reachability check.
C4-recalibration-under-heteroskedasticity remains a THEORY item — hers for the lab.
