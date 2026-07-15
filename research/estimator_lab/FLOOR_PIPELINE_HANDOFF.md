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

## Declared next step (not started)
Real Fama-French-residualized S&P data: which real residual statistical factors survive the
screen, and what is their leakage-score distribution — are the "ending parts of risk"
genuine, leaked, or noise? Data available in-repo: PIT S&P membership + daily prices
(`data/raw/daily_px_statarb_wide.parquet` etc.); FF factor returns are free (Ken French
library, would need a fresh, manifest-logged pull).
