# pca_minvar_raw

Low-vol / min-var anomaly, levered: leverage-constrained investors (mutual funds,
benchmark-tied institutions) who want beta can only reach it by overweighting
high-beta names, bidding those up and leaving the low-vol frontier portfolio
earning near-market return at roughly two-thirds the volatility (Frazzini-Pedersen
BAB, Baker-Bradley-Wurgler); 2x leverage converts that risk-adjusted edge into raw
return, which the counterparties structurally cannot do. Estimator story: this is
the CONTROL leg of a matched pair testing the dispersion-bias theorem (Goldberg,
Papanicolaou, Shkolnik) — the covariance model uses the RAW sample leading
eigenvector from a 252-day PCA, which the theorem says is over-dispersed relative
to the population factor, so the min-var optimizer systematically mis-weights
(too concentrated against the estimated factor). Its flaws are the point: the
paired corrected spec should beat this one out-of-sample if the theorem bites at
p~500, n=252. Falsifier: a forward year where this book's vol is not materially
below the market's (the low-vol premium fails to show up in realized risk), or
where the 2x-levered net return lags SPY by more than its cost drag while the
corrected twin also lags — that kills the anomaly leg, not just the estimator leg.
