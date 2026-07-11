export const meta = {
  name: 'hunt2026-goldberg',
  description: 'Matched-pair PCA min-var specs: raw sample eigenvector vs dispersion-bias (JSE) corrected',
  phases: [{ title: 'Build', detail: 'two builders, identical except the eigenvector correction' }],
}

const BUILD_SCHEMA = {
  type: 'object',
  required: ['spec_name', 'status', 'train_net_2yr', 'train_sharpe_2yr', 'avg_daily_turnover', 'notes'],
  properties: {
    spec_name: { type: 'string' },
    status: { type: 'string', enum: ['built', 'failed'] },
    train_net_2yr: { type: 'number' },
    train_sharpe_2yr: { type: 'number' },
    avg_daily_turnover: { type: 'number' },
    train_full_cagr: { type: 'number' },
    notes: { type: 'string' },
  },
}

const SHARED = `
You are a strategy-spec builder for the hunt2026 alpha hunt in ~/projects/alpha-lab.
READ FIRST: research/hunt2026/specs/SPEC_CONVENTIONS.md and research/hunt2026/harness.py.
Use ~/projects/alpha-lab/.venv/bin/python, run from research/hunt2026 so 'import harness' works.
Train data ONLY (harness.load_train()); holdout.parquet is chmod 000 — never touch it, never
chmod it, no network pulls. Do NOT grid-search params — implement the given defaults, light
sanity-validation only.

SHARED DESIGN (both specs in this pair are identical except one step):
Monthly (first trading day of each month, weights held constant between rebalances):
1. Universe: tickers with member==1 on the rebalance date AND >= 252 non-NaN closes in the
   trailing 252 trading days. Stocks only (exclude the ETF list in sandbox_meta.json and ^VIX).
2. Y = demeaned daily-return matrix of the trailing 252 days, shape (p names x n=252 days).
3. Top-k SVD of Y with k=1: leading left singular vector h (p-vector), singular value sigma1.
4. delta2_hat = ||Y - h h' Y||_F^2 / ((p-k) * n)   [factor-model residual noise variance]
5. [THE ONLY DIFFERING STEP — see your spec below]
6. Covariance model: Sigma = lam1 * v v' + delta2_hat * I, where lam1 = sigma1^2/n and v is
   the (possibly corrected) leading eigenvector. Min-var weights: w_raw = Sigma^{-1} 1 via
   Sherman-Morrison (closed form, no matrix inversion needed for k=1).
7. Long-only: clip negatives to 0; cap each name at 2%; renormalize to sum 1; lever x2.0
   (gross = 2.0 exactly, within the harness cap).
Expected turnover: low (monthly, min-var books are stable). Runtime guard: one SVD per month
on a ~(500 x 252) matrix is trivial; vectorize the monthly loop reasonably.
params.json (<=3): {"window": 252, "k": 1, "leverage": 2.0}.
MECHANISM.md: low-vol/min-var anomaly (leverage-constrained investors overpay for high-beta,
so the low-vol frontier portfolio earns near-market return at ~2/3 the vol; 2x leverage
converts the risk-adjusted edge into raw return) — plus your spec's estimator story below.
State the falsifier: what forward evidence would kill it.

VALIDATE: harness.run on train from 2023-07-10 and from 2015-01-01; no exceptions,
gross_cap_violations == 0, turnover consistent with monthly min-var (~1-3%/day avg incl.
rebalance days). Return the structured result.
`

phase('Build')
const results = await parallel([
  () => agent(`${SHARED}
YOUR SPEC: "pca_minvar_raw" in research/hunt2026/specs/pca_minvar_raw/.
Step 5: NO correction — v = h, the raw sample leading eigenvector. This is the CONTROL leg
of a matched pair testing the dispersion-bias theorem (Goldberg et al.): sample eigenvectors
over-disperse relative to the population one, so raw-PCA min-var books systematically
mis-weight. Implement it straight; its flaws are the point.`,
    { label: 'build:pca_minvar_raw', schema: BUILD_SCHEMA }),

  () => agent(`${SHARED}
YOUR SPEC: "pca_minvar_jse" in research/hunt2026/specs/pca_minvar_jse/.
Step 5: the dispersion-bias / James-Stein correction from Kristen's factor_lab research
(Goldberg-Papanicolaou-Shkolnik line; see ~/projects/factor_lab/bias_correction_demo.py,
READ-ONLY, for the exact estimator):
  psi2_hat = max(tau, 1 - p * delta2_hat / sigma1^2),   tau = 0.01
  Theorem: h = psi * b + orthogonal noise, so h's angle to the equal-weight direction
  q = 1/sqrt(p) is biased: the true cosine is (h'q)/psi_hat, i.e. the TRUE eigenvector is
  closer to equal-weight than the sample one (excess dispersion in h's entries is noise).
  Correction: c_true = min(1.0, (h'q)/psi_hat);  u = (h - (h'q) q) / ||h - (h'q) q||;
  v = c_true * q + sqrt(1 - c_true^2) * u   (rotate h toward q to the corrected angle).
Then proceed with v in step 6. Note in MECHANISM.md that this is the JSE lens applied to
implementation: same anomaly, better-estimated covariance -> better weights; the matched
control is pca_minvar_raw and the holdout delta between them is the measured value of the
theorem. Do not otherwise deviate from the shared design.`,
    { label: 'build:pca_minvar_jse', schema: BUILD_SCHEMA }),
])

return results.filter(Boolean)
