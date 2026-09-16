# CRSP pipeline validation

**Question:** does a panel built from raw CRSP reproduce two published return series closely enough to trust results built on it?

**Method, step by step.** (1) Every monthly CRSP record for common shares (share code 10/11) on NYSE, AMEX and Nasdaq, 1963–2024. (2) Delisting returns folded into the delisting month; a performance delisting with no recorded return is booked at −30% (Shumway 1997). (3) Market equity = |price| × shares outstanding; each month's weights use the *previous* month's market equity. (4) Market: value-weighted average return of all stocks, minus the T-bill rate. (5) Momentum: return from 12 months ago to 2 months ago (skipping last month); each month, stocks above the 90th and below the 10th percentile of NYSE stocks; value-weighted top minus bottom. (6) Compare with Ken French's MKT−RF and UMD from WRDS. French's UMD uses a 2×3 size/momentum sort, so a correlation near but below 1 is expected for the decile spread; the market series should match almost exactly.

Panel: 3,441,216 stock-months, 26,200 distinct securities, 22,204 of which carry a delisting return.

| Series (mine vs French) | Months | n | Correlation | My mean, %/yr | French mean, %/yr | Tracking error, %/month |
|:--|:--|--:|--:|--:|--:|--:|
| Market excess return vs MKT−RF | 1964-01–2024-12 | 732 | 1.000 | 6.97 | 6.99 | 0.02 |
| Momentum decile spread vs UMD | 1964-01–2024-12 | 732 | 0.905 | 14.29 | 7.24 | 3.87 |
| Same spread, delisting returns ignored, vs UMD | 1964-01–2024-12 | 732 | 0.907 | 14.08 | 7.24 | 3.81 |

One row = one series compared month by month over the full overlap.
