# Pre-registration — is GLD the right third risk-menu asset, or a 2021-2026 accident?

### EXP-2026-07-10-defensive-asset

**Hypothesis** (one falsifiable sentence, mechanism included):
GLD's contribution to dual_momentum_gold is a regime artifact — the 252d-momentum framework
selects whichever asset is trending, and GLD's edge over a two-asset {SPY,QQQ} menu is
concentrated in windows ending 2024-2026 (the gold run) rather than spread across regimes;
any liquid, low-equity-correlation third asset would have looked similar ex-ante.

**Layer touched** (exactly one) + registered baseline:
Layer A/C — risk-menu composition only. Everything else (252d lookback, winner-take-all
1.5x risk leg, absolute-momentum gate vs BIL, momentum-picked {TLT,BIL} defensive leg at
1.0x) is held EXACTLY as frozen in specs/dual_momentum_gold/spec.py. Baseline = the frozen
GLD variant; the critical control = NONE (two-asset {SPY,QQQ} menu).

**Alpha type tag**: market

**Expected result** (numeric, on which evaluator):
Walk-forward, panel_2005.parquet, rolling 12m windows / quarterly steps (walk_forward.py
window logic; ~72 shared windows since BIL data starts 2007-05 and binds all variants).
Expected: GLD beats NONE in 55-65% of all windows, but in windows ending BEFORE 2024-01-01
the win share drops to ~50% and the median 12m delta (GLD − NONE) to ≤ +1%; several
alternative third assets (SLV, DBC, TLT-in-menu) land within ±2% median 12m of GLD.

**Alternative result** (what the world looks like if the hypothesis is false):
GLD beats NONE in ≥60% of windows with the edge spread across decades — pre-2024 win share
≥55% AND pre-2024 median 12m delta ≥ +1.5% — and GLD clearly dominates the other third-asset
candidates (highest median excess vs SPY of the menu variants in both halves). That is the
"gold is structurally the right diversifier under this framework" world.

**Registered variants** (10, all reported, nothing cherry-picked): third asset =
GLD (frozen baseline) / TLT / DBC / XLU / XLP / UUP / SLV / VNQ / NONE ({SPY,QQQ} only) /
EQW-defensive (synthetic equal-weight GLD+TLT+BIL basket as the third asset; if it wins the
momentum race it is held as the basket at 1.5x split equally).

**Decisive statistic (pre-committed)**: count of 12m windows where the GLD variant's return
exceeds the NONE variant's, split at window-end 2024-01-01. Verdict rule:
- "regime artifact" if pre-2024 win share ≤ 52% OR pre-2024 median delta ≤ +0.5%;
- "structural" if pre-2024 win share ≥ 55% AND pre-2024 median delta ≥ +1.5%;
- anything between → "weak/indeterminate, do not bank the gold slot".

**Failure / kill condition** (pre-committed, decidable from harness output):
This is a robustness probe of an already-frozen spec, not a new spec hunt. Kill rule for
the iteration: one run of the 10 registered variants, no post-hoc additions to the menu
list, no lookback/leverage retuning if results disappoint. If the verdict is "regime
artifact", dual_momentum_gold's ledger discount stands and NO menu change is proposed from
this data (any replacement third asset chosen from this table would itself be hindsight).

**Trial-ledger row**: TRIAL_LEDGER.md — robustness-experiment row added in the same commit
(1 experiment, 10 registered variants, adaptive loop YES).

**Derived from prior holdout results?** YES — the question exists because dual_momentum_gold
survived the hunt-2 5y blind holdout (+29.1%) and the ledger already flags "gold-menu design
hindsight". This is an adaptive loop and is flagged as such in the hunt-level table.

---
**Result** (filled after the run, never edited above this line):
