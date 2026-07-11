# CANONICAL_STATE.md — verified repository state (2026-07-10)

Ground truth from the working tree, git, ledgers, and launchd — **not** chat summaries.
Where a repo document contradicts reality, reality wins and the contradiction is flagged.

Auditor: Research Director pass, 2026-07-10. Method: `git status/log/diff`, ledger tails,
runner source, launchd inspection, `.env` redaction check.

---

## 1. Real-money safety — CLEAR

- Every Alpaca client in `scripts/hunt_paper_run.py` is constructed with `paper=True`
  (lines 202, and `alpaca_paper_broker` at 204). Docstring is explicit: "--live submits to
  Alpaca paper only (never real money)."
- `.env` holds only EODHD + Alpaca **paper** keys (redacted; not printed to logs).
- No real-money base URL, no live-trading pathway anywhere in the runner.
- **Verdict: no real-money exposure is reachable from this code.** ✔

## 2. Active paper books — 7 live, not 6 (RECONCILED)

The `BOOKS` dict in `scripts/hunt_paper_run.py` (lines 34–53) trades **7 books**, and the
`_account` ledger aggregate ($100,794 notional ≈ 7 × $14,399) confirms all 7 submit:

| # | book | class | mechanism cluster | tier | ladder |
|---|---|---|---|---|---|
| 1 | vol_managed_qqq | Market (risk-mgmt) | US large-cap vol-management | promoted | 3 |
| 2 | vol_core_svxy | Market (risk-mgmt + VRP sleeve) | US vol-management + variance carry | promoted | 3 |
| 3 | trend_vol_qqq | Market (risk-mgmt + trend) | US vol-management + trend | promoted | 3 |
| 4 | defensive_ensemble | Portfolio (diversified premia) | multi-asset inverse-vol | promoted | 3 |
| 5 | dual_momentum_gold | Market (cross-asset mom) | absolute/relative momentum | **watch** | 2 |
| 6 | momentum_concentrated | Market (XS stock mom) | cross-sectional momentum | **watch** | 2 |
| 7 | dual_momentum_gem | Market (cross-asset mom) | absolute/relative momentum | **watch** | 2 |

- Capital: equal-weight, ~$14,399/book on ~$100.8k paper equity.
- Benchmarks per book: exposure-matched SPY (`bench_spy_nav`) + naive (`bench_naive_nav`).
- **Discrepancy flagged:** `research/hunt2026/STATUS.md` still says "6 books" — it predates
  commit `001245d` which added `dual_momentum_gem` as the 7th (watch-tier). STATUS.md is
  stale by one book. The prompt's "6 vs 7" question resolves to **7 live**.
- **Right now `dual_momentum_gem` and `dual_momentum_gold` hold an identical position**
  (both `{QQQ: 1.5}` — both in risk-on state). They are the intended frozen matched pair;
  their NAV histories differ (gem 1.628 vs gold 1.790). Real independence is 0 at this instant.

## 3. Scheduler — ENABLED

- `~/Library/LaunchAgents/com.rimrim.hunt2026-paper.plist` is **active** (not `.disabled`).
- Runs `.venv/bin/python scripts/hunt_paper_run.py --live`, **weekdays 20:30 local**.
- Log: `artifacts/hunt2026/paper/nightly.log`.
- Two older plists are archived disabled in `audit-bundle/` (`alpha-lab-paper`, `hunt2026-paper`).
- Most recent submissions: all 7 ledgers carry a `2026-07-10` live row.

## 4. OPEN OPERATIONAL ISSUES (need Kristen's call)

### 4a. Dirty working tree on a LIVE-paper script — uncommitted, unpushed
`git status`: `scripts/hunt_paper_run.py` modified but **not committed**, and the branch is
**12 commits ahead of origin/main (unpushed)**. The diff adds held-position pricing so
reconcile can flatten stale/foreign names:
```
+ held_syms = [p.symbol for p in TradingClient(key, secret, paper=True).get_all_positions()]
+ symbols = sorted(set(symbols) | set(held_syms))
```
This is a **real, correct fix** — without it, a held name the current books don't target
(e.g. a leftover AMAT/statarb residual) prices to `None`, gets skipped by reconcile, and
persists silently. **But it is sitting uncommitted on the exact script a launchd job runs
nightly with `--live`.** The next 20:30 run executes whatever is on disk. This is the
"silent live-spec modification / concurrent-process change" risk the charter warns against.
→ **Decision needed:** commit + test this fix, or `git stash` it, before the next run.

### 4b. Duplicate ledger rows — idempotency bug
The uncommitted diff appended **one extra `2026-07-10` row to every book ledger**, exact
duplicate of the prior line (verified on `defensive_ensemble.jsonl`: 4 rows same date,
last two byte-identical). The runner re-ran same-day and appended rather than dedup/replaced.
→ NAV/return attribution that reads "last row per date" is safe; anything that sums or
counts rows will double-count 2026-07-10. Add a same-date replace-or-skip guard.

### 4c. Held-position sprawl in `_account`
`_account` targets include ~30 single-stock names (AMD, AMAT, KLAC, MU, GOOG/GOOGL, …) —
these are `momentum_concentrated`'s book, correctly reconciled. No obvious dead statarb
residual remains in the latest aggregate (the 4a fix is what keeps it that way). ✔ but
verify after the next `--live` run that no None-priced name is skipped.

### 4d. Go-live provenance (already ratified)
Per STATUS.md: first go-live (`8708c26`, `4b35553`) was pushed by a **concurrent session
ahead of Kristen's Stage-4 gate**; surfaced 2026-07-10, Kristen ratified keeping all books
running. Recorded here so the governance gap is not forgotten — controls were weaker than
research discipline, exactly the charter's concern.

## 5. Research artifacts present (reuse, do not rebuild)

Already on disk and authoritative — the independent-alpha program should **extend** these,
not duplicate them:
- `research/hunt2026/`: TRIAL_LEDGER.md (18 trials), FAILURES.md (F-001..F-019 + NR-1..5),
  RESEARCH_OBJECTS.md (layer decomposition), CONFIDENCE_LADDER.md, STATUS.md, PREREGISTRATION.md
- `research/hunt2026/robustness/`: ic_screen (0/10 signals rank IC — F-017..019), deflated
  Sharpe (N=18), xmarket (3/7 clusters, mechanism NOT universal — F-020), defensive_asset
  (GLD third-slot = 2024–26 regime artifact)
- `research/director/`: CHARTER.md, EXPERIMENT_QUEUE.md (11 ranked experiments)
- `research/estimator_lab/`: JSE/PCA boundary — k=1 delta ≈ noise (F-010), JSE beats PCA at
  n=63 long-only (t to −6.5), loses unconstrained (F-021)
- `memos/`: alpha-roadmap, diagnostics, hunt2026 verdicts (holdout / 5y / walkforward)

## 6. Test suite

Not yet run this session (28 test files in `tests/`). → run `pytest -q` before committing 4a.

---

### Bottom line
7 paper books live and safe (paper-only, scheduler on). The research controls are strong;
the **deployment hygiene is the weak point** — an uncommitted bug-fix and a duplicate-row
bug sit on a nightly `--live` script. Nothing here touches real money. The count question is
resolved: **7 books, 4 promoted (all one vol/trend risk-management family + one portfolio
sleeve) + 3 watch-tier momentum books held for forward evidence only.**

> **SUPERSEDED for deployment state (2026-07-10):** the single deployment authority is [/DEPLOYMENT_MANIFEST.md](../../DEPLOYMENT_MANIFEST.md). This audit remains a point-in-time verification record; where they disagree, the manifest wins.
