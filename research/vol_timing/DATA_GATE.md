# Vol-timing project — data gate + Phase 1 hypothesis (2026-07-14)

New project, separate from the (stopped) price-only timing program and from the
existing books (factor-premium strategies under separate monitoring).

## Data-readiness inventory

| source | coverage | freq | PIT quality | missing | cost |
|---|---|---|---|---|---|
| ^VIX spot (in hunt panel) | 2014-01 → 2026-07-10 | daily close | index published 4:15pm ET — LATER than 4pm equity close; handled by ≥1-day trade delay | 0 gaps | free |
| ^VIX3M (pulled, manifest-logged: `data/raw/vix3m_daily.parquet`) | 2006-07 → 2026-07-10 | daily close | same 4:15pm convention | 0 on panel dates | free |
| ^VVIX (available, not pulled) | 2007 → | daily | same | — | free |
| ^SKEW (available, not pulled) | 1990 → | daily | same | — | free |
| ^VIX9D (available, not pulled) | 2011 → | daily | same | — | free |
| Realized vol | from panel SPY/QQQ closes | daily | clean | none | free |
| VIX futures term structure | CBOE historical settlements exist free but scattered; **proxy used instead: VIX/VIX3M spot ratio** (standard slope proxy, same publication timing) | — | — | — | free |
| Option chains / IV surface / strike-level skew | **NOT freely available historically** (OptionMetrics, CBOE DataShop = paid) | — | — | — | PAID — not acquired, per rules |
| SVXY (instrument, in panel) | 2014-01 → 2026-07-10 | daily | product mechanics CHANGED 2018-02-28: −1x → −0.5x (post-Volmageddon deleveraging) — regime split mandatory | 0 | free |

Honest-scope statement (required): with free data only, the testable object is
**index-level option-implied information** (VIX family are model-free implied-vol
indices — genuinely option-implied) — NOT strike-level surfaces, variance-swap P&L, or
futures-roll P&L. The instrument is the SVXY ETF, whose product menu is itself
survivorship-conditioned (XIV, the −1x predecessor that died in Feb-2018, is absent
from the panel — on record from the Stage-2 audit).

Look-ahead risks identified: (1) VIX-family 4:15pm publication vs 4:00pm equity close
→ any same-close trade is look-ahead; resolved by the harness convention (signal at
close t → weights at close t+1 → earn t+2 relative to signal date… net effective delay
one full trading day). (2) yfinance index history is a current pull — index values are
not revised, so backfill risk is negligible; SVXY splits are auto-adjusted (verified
adjustment on the panel in Stage-2's split check). (3) The phantom-row-corrected panel
is used throughout.

**Data-readiness verdict: READY for the narrower index-level hypothesis; option-chain
hypotheses require paid data and are out of scope unless Kristen approves a purchase.**

## Phase 1 — the one hypothesis (simplest testable; no strategic fork requiring
Kristen: term structure is the only candidate that is simultaneously new-to-repo,
parameter-free, and directly one of her worked examples)

**H: Volatility-carry exposure has negative expected reward when the VIX term
structure is inverted. Rule: hold SVXY when VIX/VIX3M < 1 (contango), hold BIL when
VIX/VIX3M ≥ 1 (inversion). This should beat constant SVXY exposure net of costs, with
the improvement concentrated in tail outcomes.**

- Why the predictor should matter: the sign of vol-carry ≈ the slope of the vol term
  structure. In contango the short-vol position collects roll-down plus the variance
  risk premium; inversion means the market prices near-term risk above medium-term —
  expected carry flips negative and crash-conditional losses concentrate there. The
  spot ratio VIX/VIX3M is the standard PIT proxy for the futures slope.
- Instrument/exposure changed: SVXY ↔ BIL, binary, gross always 1.0 (no financing).
- Expected sign: gated ≥ benchmarks net; primary channel = crash-period return and
  max drawdown, per the mechanism.
- Holding period: daily evaluation; signal-side stats (no returns examined): inversion
  = 7.7% of 2014–2026 days, 81 episodes, median length 1 day → whipsaw churn is a
  REAL COST pre-accepted at 2 bps/side; concentrated in 2018/2020/2025 as the
  mechanism predicts.
- Realistic delay: one trading day (above).
- Exact benchmarks: (frozen in the prereg) B1 constant 1.0 SVXY; B2 exposure-matched
  constant mix w̄·SVXY + (1−w̄)·BIL with w̄ = training-period ON-fraction — B2 exists
  to separate timing skill from mere average-exposure reduction.
- Why this is NOT the failed price-only rules repackaged: F-007 gated on VIX LEVEL vs
  realized vol; the vol_core_svxy sleeve gates on VIX vs its own rolling median — both
  are level/price functions of in-panel series. This signal is the implied term-
  structure SLOPE, information from a different option maturity (3M), absent from the
  panel and from every prior spec. It is, however, still a daily-close gate, so
  NR-3's finding (daily gates gave ZERO protection in the Aug-2024/Apr-2025 gap
  events, F-007) is carried as the PRE-STATED expected failure mode for fast crashes —
  the mechanism's realistic best case is slow-stress protection (2022-style), which is
  exactly what the decision rules' "risk-management improvement, not alpha" label is
  for. 2008 cannot be included (no SVXY; no futures data) — fast-crash exposure is
  stated, not simulated, per the F-013 rule's spirit.
- Hindsight honesty (pre-stated): contango-gating short-vol is PUBLIC folk knowledge;
  this experiment is a disciplined REPLICATION-plus-audit of a known mechanism on our
  data, costs, and product mechanics — not discovery. The claim-bearing holdout and
  placebos are what make a positive result meaningful despite that.
