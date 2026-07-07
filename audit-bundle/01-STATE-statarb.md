# STATE — StatArb (pairs + residual reversion)

**Stage:** 1 (pairs run on real data); residual (Avellaneda-Lee) built + tested, not yet run
**Last session:** 2026-07-07

## Scope
Two free-data-replicable StatArb methods from [[LIT — StatArb, market making & systematic factors]]:
- **Pairs (Gatev-Goetzmann-Rouwenhorst)** — form pairs by min normalized-price distance on a
  trailing window, trade the spread z-score out-of-sample on the next window.
- **Residual reversion (Avellaneda-Lee, lite)** — regress each stock on factor ETFs, trade the
  mean-reverting residual via an OU s-score.

## Built
- `bands.py` — shared entry/exit band logic (long when standardized series ≤ −entry, short ≥ +entry, flat inside exit band). Used by both methods.
- `pairs.py` — normalize, select_pairs (min SSD), `pair_zscore_oos` (formation-window stats applied OOS), pair_pnl (lagged, no look-ahead)
- `residual.py` — `residual_returns` (OLS on factors), `s_score` (standardized cumulative residual)
- `scripts/statarb_run.py` — walk-forward pairs, equal-weight, costs → scorecard
- Tests 8/8 green.

## Result — pairs (2026-07-07, 60 large caps, 2018+, 252d form / 126d trade, 20 pairs, 5bps)
**Net Sharpe −0.06, ann. −0.42%, max DD −28%, 1883 obs.** Dead.

### The story (this is the value)
First run showed **Sharpe 4.77** — impossibly good. Root cause: the spread z-score was
standardized using the *trading-window* mean/std (look-ahead — each day "knew" the window's
future mean). GGR sets the ±2σ bands from the *formation* window. Fixed via `pair_zscore_oos`;
Sharpe collapsed 4.77 → −0.06. **Matches Do & Faff (2010): pairs profitability halved post-2002,
most residual profit dies after costs.** Naive distance pairs has no edge left in liquid large caps.
The 4.77→−0.06 catch is the transferable lesson (formation-vs-trading look-ahead is THE pairs bug).

## Result — pairs, WIDE universe (2026-07-07)
S&P 500 + S&P 600 (1103 names, large + small), within-sector pair formation (`select_pairs_sectored`),
50 pairs, same 252/126 walk-forward, 5bps.
**Net Sharpe 0.23, ann. 0.90%, max DD −11%, hit rate 50%, deflated prob 74%.**

Widening from 60 mega-caps → 1103 large+small moved pairs **−0.06 → +0.23** — a faint pulse,
exactly where the LIT note said the residual edge survives (smaller names). But 0.9%/yr net at
Sharpe 0.23 is **below the 0.5 kill threshold** → still dead-for-me, and nowhere near GGR's historic
~11%/Sharpe-1.5. Consistent with Do & Faff's post-2002 decay. Caveat: deflated prob shown at
n_trials=1 is optimistic — real search = {mega, wide} × {formation/trading/entry params}, so the
honest multiple-testing count is higher and the true deflated prob lower.

## Next
1. Run the **residual (Avellaneda-Lee)** variant — regress universe on SPY + sector ETFs, trade
   s-score reversion. A-L report Sharpe ~1.1–1.5 (decaying); test whether residual reversion
   survives where distance-pairs didn't. (Best remaining shot at a live signal here.)
2. Cointegration-based selection instead of distance; point-in-time universe (WRDS) to kill survivorship.
3. Ledoit-Wolf covariance cleaning (planned `core/` util) for a portfolio-level residual book.

## Result — RESIDUAL reversion (Avellaneda-Lee), 2026-07-07 — FIRST LIVE SIGNAL IN THE LAB
Rolling single-factor regression of each stock on its SECTOR ETF (betas lagged, no look-ahead) →
idiosyncratic residual → s-score of the cumulative residual → mean-reversion (long s≤−1.25, short
s≥+1.25, flat inside ±0.5). Dollar-neutral, equal-weight, `scripts/statarb_residual_run.py`.

**Canonical: S&P 500 (503 names), skip=1, 10bps, n_trials=20 → net Sharpe 2.67**, ann. 12.5%,
max DD −6.3%, hit rate 60%, deflated prob 100%. Subperiods 2.91 (2018–22) / 2.40 (2022–26).

### It survived every skeptical audit (this is why I believe it — provisionally)
| Audit | Result | Kills? |
| ----- | ------ | ------ |
| skip=0 → skip=1 (bid-ask bounce / same-close reversal) | 3.42 → 3.61 | NO — reversion persists a day out |
| winsorize daily returns to [−50%,+100%] (bad-tick/halt) | 3.61 → 2.66 | NO (but ~26% was data-error reversion — removed) |
| **S&P 500 only @ 10bps (is it just small-cap microstructure?)** | **2.67, DD −6.3%** | NO — *strongest* in the most liquid names |
| S&P 600 only @ 30bps | 1.56 | NO — survives high small-cap costs too |
| multiple testing (n_trials=20 deflation) | prob 100% | NO — Sharpe 2.67 over ~2015 days has huge headroom |

### Remaining risks (do NOT treat 2.67 as final)
1. **Survivorship bias** — current S&P 500 membership. Residual reversion on *survivors* can be inflated;
   this is the single biggest unaddressed threat. Needs point-in-time membership (WRDS/CRSP).
2. **Higher than the paper** — A-L reported ~1.1–1.5 (already decaying by 2007); 2.67 on 2018–26 is
   *higher*, which is itself a reason for skepticism. Likely helped by (a) survivorship, (b) COVID-era
   vol where reversion paid unusually well (2018–22 subperiod 2.91 includes Mar-2020), (c) unmodeled
   frictions (borrow/short availability, market impact, real fills vs close).
3. Turnover is high → very cost-sensitive (2.67@10bps large-cap, 1.2@30bps). Capacity-limited.

## Result — POINT-IN-TIME re-test (2026-07-07) — survivorship attack, free-data ceiling
`scripts/statarb_residual_run.py --pit --cost-bps 10`. Reconstructs point-in-time S&P 500 membership
(fja05680 maintained change-log, `core/data/universe.py::fetch_sp500_pit_changes`), then trades each
name ONLY on its actual index-membership days (`membership_mask`, forward-filled snapshots). Removes
the **inclusion look-ahead** the baseline had — 156 current members were added mid-window yet traded
from 2018.

**Baseline (survivor universe) 2.67 → PIT-membership 2.50** (ann. 11.5%, DD −5.5%, hit 58.4%,
subperiods 2.67 / 2.31). A −0.17 haircut. Signal survives the achievable correction.

### But 2.50 is an UPPER BOUND, not the true PIT Sharpe — and the gap is unmeasurable on free data
- Of the **505 S&P 500 members on 2018-01-02, 144 were gone by 2026; 120 of those have NO price
  series in yfinance** (acquired/failed → delisted). Probed directly: SIVB, FRC, XLNX, ATVI, CERN,
  ABMD… all return empty. (The one "SBNY" hit is a post-2024 symbol *reuse*, not Signature Bank — a trap.)
- So the PIT run still trades a *thinned* member set: **~447 of ~500 real members per day** (min 384
  in 2018, where the most names have since died). The missing ~53/day are exactly the delisted tail.
- Those dead names are the adverse-selection trades a reversion signal *loses* on (bought the dip,
  name kept falling into delisting). Re-adding them can only LOWER the Sharpe. → true PIT Sharpe ≤ 2.50,
  by an amount only CRSP/WRDS point-in-time PRICES can pin down. WRDS is blocked; yfinance cannot fix this.

**What the PIT run does and doesn't fix:** ✅ inclusion look-ahead (fixed, cost −0.17). ❌ delisting
survivorship (structurally unfixable on free data). The residual bias points DOWN.

## Result — FALLING-KNIFE stress test (2026-07-07) — how survivorship-fragile is the edge?
`--long-floor X`: forbid longs while s < −X (skip deep-dip entries + stop out held longs that keep
falling). The deepest-negative-s longs are the survivor-universe analogue of the missing dead-name
longs (bought a name in steep idiosyncratic decline). If the edge lives there, it's survivorship-fragile.

Survivor baseline (2.67), tightening the floor toward the −1.25 entry:
| long floor | Net Sharpe | Ann. return | Max DD |
| ---------- | ---------- | ----------- | ------ |
| off (base) | 2.67 | 12.5% | −6.3% |
| −3.0 | 2.57 | 11.5% | −5.1% |
| −2.5 | 2.31 | 10.1% | −4.5% |
| −2.0 | 1.86 | 7.8% | −4.3% |
| −1.75 | 1.71 | 7.1% | −4.3% |

PIT universe consistency point: **PIT + floor −2.0 = 1.69** (vs PIT no-floor 2.50) — same ~0.8 erosion,
so the fragility is not a survivor-set quirk.

### Read: a decomposition, not a pass/fail
- The edge **erodes steadily but does NOT collapse**. A **robust core of ~1.7 Sharpe / 7.1% ann**
  survives removing ALL longs deeper than −1.75 — that core clears the 0.5 kill threshold by ~3.4×.
- But **~43% of the headline return (5.4% of 12.5%) sits in longs deeper than −1.75σ** — the −2σ-to-−3σ
  dip-buying trades. That band is exactly where survivorship bias bites: dead names entered the same
  deep-dip longs and never bounced. So this premium is survivor-inflated to an unknown-but-nonzero degree.
- Removing the deep longs also **halves max drawdown** (−6.3% → −4.3%): the falling-knife trades carried
  most of the tail risk, not just the return.
- **Bracket on the true survivorship-free Sharpe: ~1.7 (robust floor) ≤ true ≤ 2.50 (PIT upper bound).**
  Free data can't pin it tighter (dead-name prices needed); forward paper trading resolves it directly.

## Verdict for HYP-005
- **Pairs: dead-for-me** (−0.06 mega, +0.23 wide, sub-threshold).
- **Residual reversion: ALIVE, but survivorship-sensitive. 2.67 baseline → 2.50 point-in-time (upper
  bound) → ~1.7 robust core (deep-dip longs removed). Survived 7 audits.** Not a pure survivorship
  artifact — a Sharpe-1.7 core clears the kill bar 3.4× — but ~half the headline return is fragile
  deep-dip premium that a delisting-inclusive universe would partly erase. The one test structurally
  **immune to survivorship — forward paper trading** — is the decisive next step (live universe forward,
  no omitted dead names by construction), and paper the FULL signal (not the floored one) to see how the
  fragile premium behaves live.

## Next
1. **Paper trade (Stage 5) — the survivorship-immune test.** Daily s-score book on the *current live*
   S&P 500, track live vs backtest. Resolves the ~1.7-to-2.50 bracket directly. Instrument the deep-dip
   (s < −2) longs separately — that bucket is where live-vs-backtest divergence should show first.
2. If CRSP/WRDS ever unblocks: point-in-time *prices* (not just membership) for the true survivorship-free number.
3. Ledoit-Wolf covariance cleaning for a portfolio-level (vs equal-weight) residual book.
