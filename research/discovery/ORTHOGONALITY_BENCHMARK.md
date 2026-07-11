# Experiment 5 — Orthogonality Benchmark (permanent gate)

The permanent Stage-4 residual-independence test. Every discovery candidate must clear it
before it can be called independent. Implementation: [orthogonality_benchmark.py](orthogonality_benchmark.py).

## What it computes
For a candidate daily return series it regresses on the control set
**X = [1, SPY, QQQ, the 7 live books]** (trend / vol-targeting / leverage / momentum ARE the
books, so this is the "beyond the existing Alpha Lab portfolio" test) and reports, component by
component (charter § 3C — never one opaque score):

| metric | meaning | independence threshold |
|---|---|---|
| `max_corr_to_book` | largest \|return corr\| to any single book | < 0.50 |
| `max_residual_corr` | largest \|corr\| after removing SPY+QQQ from both | < 0.35 |
| `resid_alpha_ann` / `resid_alpha_t` | alpha after the full control set + t | t > 2 for a residual edge |
| `resid_sharpe` | Sharpe of the residual stream | — (reported) |
| `crisis_bps_per_day` | mean candidate return on worst-decile SPY days | — (diversifier value) |
| `incr_ens_dSharpe` / `incr_ens_P_gt0` | ΔSharpe adding it to the equal-risk 4-book ensemble, block-bootstrap P(Δ>0) | P > 0.90 for portfolio value |

## Suggested tags (the reviewer assigns the final charter verdict)
- **NOT INDEPENDENT** — fails the corr gate (it's the existing cluster with new timing).
- **INDEPENDENT BUT NO EDGE** — orthogonal but no residual α; judge purely on crisis / drawdown contribution.
- **MEASUREMENT SUPPORTED** — independent + residual edge, but not yet portfolio-incremental.
- **PORTFOLIO CANDIDATE** — independent + residual edge + incremental ensemble Sharpe.

## Self-check (runnable, `python research/discovery/orthogonality_benchmark.py`)
Passed 2026-07-10:
- existing book (`vol_core_svxy`) fed as candidate → **NOT INDEPENDENT**, max corr 1.00 ✓
- orthogonal zero-mean noise → **INDEPENDENT BUT NO EDGE**, max corr 0.02, α t = −1.3, P(incr)=0.01 ✓
- orthogonal noise + steady drift → **PORTFOLIO CANDIDATE**, max corr 0.03, α t = 5.5, P(incr)=1.00 ✓

## Usage
```python
from orthogonality_benchmark import score_candidate
report = score_candidate(candidate_daily_returns, label="my-candidate")
```
Candidate series must be daily net returns with a DatetimeIndex overlapping the panel
(≥252 common days). Reuses the frozen `compute_independence` reconstruction so the control set
is identical to the runner's P&L convention. Fixed bootstrap seed → reproducible.

## Limits (honest)
- Control set is SPY + QQQ + the 7 books; sector factors (XLK etc.) are a noted future extension.
- Equal-weight promoted ensemble for the incremental test (each book is already vol-shaped);
  an equal-risk inverse-vol variant is a one-line change if a candidate is borderline.
- A pass here is necessary, not sufficient — Stage 5 Red Team (cost stress, execution delay,
  regime, clean-room replication) still follows.
