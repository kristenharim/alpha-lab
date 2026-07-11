# pca_minvar_jse

The edge is the low-vol / min-var anomaly: leverage-constrained investors (mutual funds,
retail, benchmark-tied institutions) reach for beta instead of leverage, overpaying for
high-vol names and leaving the low-vol frontier portfolio earning near-market return at
roughly two-thirds the vol (Frazzini-Pedersen betting-against-beta; Baker-Bradley-Wurgler);
the 2x leverage this book runs converts that risk-adjusted edge into raw return — the
counterparty is anyone who cannot lever and so bids up lottery-beta instead. The estimator
layer is the JSE/dispersion-bias correction (Goldberg-Papanicolaou-Shkolnik): the sample
leading eigenvector h of the trailing return matrix satisfies h = psi*b + orthogonal noise,
so its angle to the equal-weight direction q is biased wide — the excess dispersion in h's
entries is noise, and the true market factor sits closer to q. We estimate psi from the
residual noise variance (psi^2 = max(0.01, 1 - p*delta2/sigma1^2)) and rotate h toward q to
the corrected angle before building Sigma = lam1*v*v' + delta2*I and the min-var weights.
Same anomaly, better-estimated covariance, better weights: the matched control is
pca_minvar_raw (identical pipeline, uncorrected h), and the holdout delta between the two
is the measured value of the theorem in implementation. Falsifier: a sustained forward
stretch where this book's Sharpe fails to beat SPY's (the low-vol premium arbitraged away
or crowded out), or the JSE leg persistently underperforming the raw control out of sample
— which would say the dispersion-bias correction does not survive contact with real
non-spherical residuals and membership churn.
