> **SUPERSEDED 2026-07-11 — and this file corrects an error it originally made.**
> A concurrent session built the authoritative data layer at `research/discovery/data/`
> (commit `9257c2c`, VERDICT **PASS**). It found what this file got WRONG: **FRED is NOT
> blocked-on-key** — FRED serves a **keyless CSV endpoint** (`fredgraph.csv?id=`, verified
> working: returns DGS10 etc. with no API key). The authoritative layer ingests DGS*/DFF/
> T10Y2Y/VIXCLS/VXVCLS keyless, excludes revised macro (GDP/CPI) to avoid vintage
> contamination, admits VIX/VIX3M as **state only** (curve shape, not vol-carry return), and
> passes a full leakage audit (poison-stable, VIXCLS==panel ^VIX corr 1.0). Item-7 preregs
> (EXP-A bond-carry, EXP-B conditional-vol) and item-8 orthogonality benchmark were also
> built there. **Use `research/discovery/data/` — not this directory.**
>
> The one finding here worth keeping: **yfinance `^VIX3M` is ~6 business days stale**
> (last 2026-07-02), so if anyone reaches for yfinance VIX3M for a *live* signal it would
> starve — prefer FRED VXVCLS (the authoritative layer already does). Kept as a record of
> the error and this caveat; not a live project.

---

# Macro Data Layer (FRED rates/curve + VIX/VIX3M term structure) — audit-first [SUPERSEDED]

Per the program: **the data audit is the deliverable before any strategy is built.** No
signal, sleeve, or book may be created until the relevant sub-layer earns an explicit PASS.
This project builds the point-in-time data layer and gates it; item-7 preregistrations
(bond-carry, conditional vol-management) are held behind these verdicts.

## Sub-layer verdicts (2026-07-11)

### FRED rates / yield curve — BLOCKED (no key)
No FRED API key is present (`~/.config/rimrimos`, `.env`, env all checked). The point-in-time
rates/curve layer — and therefore the **bond-carry preregistration (item 7a)** — cannot be
built until a free FRED key is provided. When it is, the audit must additionally test what
VIX indices don't have: **release lags and revisions/vintages** (macro series are restated;
ALFRED vintage dates are mandatory to avoid using revised data that wasn't known in real
time). Audit framework is scaffolded; verdict pending key.

### VIX / VIX3M term structure — RESEARCH: conditional PASS · LIVE: BLOCK
`vix_termstructure_audit.py` (deliverable, no strategy built). 3/5 checks pass:

| check | verdict | detail |
|---|---|---|
| release_lag | PASS | CBOE EOD indices; close(t) available ~4:15pm ET, before next-day decisions |
| revisions | PASS | index levels computed, not restated — no vintage problem |
| calendar_alignment | BLOCK* | 2891 common days; **92%** of equity days have both series |
| freshness_for_live | BLOCK | VIX3M last 2026-07-02 vs 2026-07-10 — **6 business days stale** |
| future_poison | PASS | poison last 21 days ×5 → prior lagged feature changes by **0.00e+00** (no look-ahead) |

\*calendar_alignment is a soft block: a research signal uses the aligned intersection (2891
days is ample); it is not a look-ahead or correctness failure.

**Verdict:**
- **RESEARCH use — conditional PASS.** History is complete, a lagged contango-slope feature
  has zero look-ahead, no revisions. A conditional-vol-management study may use it *if* it
  restricts to the aligned intersection and treats the 8% coverage gap explicitly.
- **LIVE use — BLOCK.** yfinance VIX3M is ~6 business days stale — it would starve a live
  term-structure signal. Live requires a same-day VIX3M source (CBOE direct, or a broker
  feed) before anything using it can touch the paper roster.

## Gate on item-7 preregistrations
- **Bond-carry predictability (7a):** BLOCKED — needs the FRED layer (no key).
- **Conditional vol-management (7b):** research-UNBLOCKED (VIX3M research-PASS) — MAY proceed
  to a *preregistration* next, but (i) research-only, not live; (ii) must pass the
  Orthogonality Benchmark (item 8) — positive residual vs SPY/QQQ and the existing books,
  low residual correlation, incremental ensemble value, crisis contribution — before any
  Stage-4 consideration; (iii) do not combine with bond-carry, do not tune thresholds.

Nothing here is promoted to the funded roster. The audit is the product; the verdicts gate
everything downstream.
