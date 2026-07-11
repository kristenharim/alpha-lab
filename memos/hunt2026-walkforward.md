# hunt2026 walk-forward — from two verdicts to eighty-two (2026-07-10)

Third pass of the hunt, implementing the platform upgrades: extended ETF panel to 2005
(stocks honestly stay 2014+ — no survivorship fiction), rolling 12-month windows stepped
quarterly (82 windows for ETF specs, 44-48 for stock specs), naive-implementation
benchmarks, trial ledger (TRIAL_LEDGER.md), failure database (FAILURES.md), and the
Layer A-D research-object registry (RESEARCH_OBJECTS.md). Since all specs are frozen,
walk-forward here adds evidence without adding trials.

Full table: research/hunt2026/walkforward/summary.md. SPY base rate: median 12m +14.2%,
≥18% in only 34% of windows, worst −36.8%.

## What 82 windows changed

1. **The robust core is the vol-managed family, full stop.** vol_managed_qqq: median 12m
   +27.0%, beats SPY in 78% of windows, +13.4pp median excess, ≥18% in 59% — across GFC,
   2011, 2015, 2018, COVID, 2022. vol_core_svxy similar (85% beat-SPY). Nothing else is close.
2. **vix_panic_buyer is retired.** Worst window −62.1% — the GFC's serial VIX spikes
   turned the panic-add into leverage on a falling knife. Both blind windows just happened
   to contain no cascade regime. This finding alone justified the panel extension (F-013).
3. **The implementation-benchmark discipline immediately paid for itself.** Attribution of
   trend_vol_qqq via its two naive parents: gate-only +13.4pp median excess, vol-target-only
   +13.4pp, the sophisticated combination +8.0pp — the combo BUYS tail relief (worst −22%
   vs −31%) with median return. Reported the old way ("trend_vol_qqq made 24.7% blind") it
   looked like additive engineering; the honest number is a negative median delta vs its own
   naive parent (F-014).
4. **defensive_ensemble is a capital preserver, not an 18% machine.** Median +15.0%, ≥18%
   in just 36% of windows — but 84% positive and worst −18.3%. Its 5y blind +19.9% was a
   good draw of a moderate-return, shallow-drawdown book. Reframed, not retired.
5. **momentum_concentrated demoted to sleeve** (F-015): the 2015-2020 momentum winter gives
   it −4.6pp median excess across 44 windows; its 1y-blind shine was a favorable draw.
6. **Goldberg pair, third consistent read**: JSE ≥ raw again over 44 windows (+3.4 vs +3.5
   median excess, marginally better worst). Direction has now been right in every eval mode;
   the k=3-5 unconstrained experiment is the registered next step.

## Revised promotion list (Stage 4 gate: Kristen)

| book | walk-forward case | role |
|---|---|---|
| vol_managed_qqq | +13.4pp median excess, 78% beat-SPY, 82 windows | core compounder |
| vol_core_svxy | +12.4pp, 85% beat-SPY | core alternative (SVXY sleeve adds carry + complexity) |
| trend_vol_qqq | +8.0pp, worst −22% (best tail in the QQQ family) | drawdown-sensitive variant |
| defensive_ensemble | +1.4pp, worst −18.3%, 84% positive | capital preserver / bear-regime sleeve |

Not promoted: vix_panic_buyer (F-013), momentum_concentrated standalone (F-015),
everything already retired in the ledger.

## Platform state

The research engine now has: frozen-spec harness → pre-holdout git freeze → one-shot
blind eval → walk-forward re-scoring → naive-benchmark attribution → trial ledger with
adaptive-loop counting → failure database → layer registry with pre-registered next
experiments (JSE k=3-5; open/close execution to reopen the overnight effect F-006; EWMA
matched pair). Paper trading as pipeline stage 3 is designed and awaiting the Stage 4 call.

Honesty footnote: adjacent walk-forward windows overlap 75% (252d window / 63d step), so
82 windows ≈ 20 independent draws; round-1 specs' pre-2025 windows overlap their fit data.
The oos_* columns in the summary carry the clean subset. Direction of every conclusion
above survives restricting to those.
