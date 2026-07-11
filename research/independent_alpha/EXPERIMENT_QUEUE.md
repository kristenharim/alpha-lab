# EXPERIMENT_QUEUE.md — Independent-Alpha candidate experiments (ranked)

*Agent 12 (Rank) · 2026-07-10 · hypotheses: `HYPOTHESIS_QUEUE.md` · dedup: `HYPOTHESIS_DEDUP.md`*

**Reconciliation with `research/director/EXPERIMENT_QUEUE.md`.** That queue owns the 11 director-ranked
experiments (H-jse-weakfactor EXECUTED; H-overnight-exec, H-band-turnover-core, H-ewma-cov, H-sector-leadlag,
etc.) and its 2026-07-10 audit selected the current trio (EXP-OPS-REALITY, EXP-EST-CROSSOVER [closed],
EXP-IC-EARNINGS-FWD [accruing]). This file does **not** re-rank those; it ranks the 23 NEW independent-alpha
candidates and slots them *after / alongside* the director trio. Overlaps are flagged, not duplicated:
H-D1 is adjacent to director #2; H-cov-temporal-smooth to director #4/#5; H-E4/A4-03 extend the accruing
EXP-IC-EARNINGS-FWD track the audit already ranked above price-only probes.

## Scoring

`Priority = P(material belief change) × decision value × generality × mechanism novelty / research cost`.
Each component is a rough 1-5 (no false precision). **data_now=false is heavily discounted** — an
uncollectable experiment cannot change belief this quarter, so every forward-collect / data-build item
sinks below every testable-now item regardless of merit. Composite is directional, not a computed decimal.
Buckets honor the 40% high / 40% medium / 20% moonshot budget over the actionable near-term set.

Legend: P=P(belief change) · D=decision value · G=generality · N=mechanism novelty · C=research cost
(1=cheap, 5=expensive) · **now**=testable now.

---

## Ranked table

| # | experiment (hypothesis id) | lane | class | now | P | D | G | N | C | bucket | why here |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | **H-E1** reversal × liquidity-shock (signal-space rank IC) | E | Market | ✅ | 4 | 3 | 4 | 4 | 1 | **high** | NR-1's *named* untested angle + ic_screen-sanctioned interaction; in-repo panel, decisive kill/revive; near-zero research overhead (sanctioned reopen). Level-1 ceiling is the only cap. |
| 2 | **H-D1** MOC vs MOO fill point on the live vol books | D | Execution | ✅ | 3 | 5 | 3 | 2 | 1 | **high** | Directly actionable on 3 LIVE paper books — tells whether the 20:30 open-fill leaks the overnight gap. Data on disk; distinct from director #2. Highest decision value on the board. |
| 3 | **H-lw-target** LW constant-correlation vs identity target | F | Estimator | ✅ | 3 | 2 | 3 | 3 | 1 | **high** | Closes the exact "blunt target" open item RESULTS.md flagged; ~15-line diff on the existing harness. Clean docket-closer even if it loses to MP. |
| 4 | **H-idio-shrink** residual-diagonal shrinkage in PCA/JSE | F | Estimator | ✅ | 3 | 2 | 3 | 4 | 1 | **high** | The only untested min-var lever (the residual diagonal); mechanistically orthogonal to every mapped estimator. Cheap, decisive per-month paired-t. |
| 5 | **H-robust-cov** tail-robust correlation → MP | F | Estimator | ✅ | 2.5 | 2 | 3 | 3 | 1 | medium | Orthogonal moment-vs-spectrum axis; cheap. Coin-flip — likely inert at n=252 (F-021), bites in tails; a clean registered result either way. |
| 6 | **H-cov-temporal-smooth** turnover-aware Σ path smoothing | F | Estimator | ✅ | 3 | 2 | 2 | 2 | 1 | medium | Attacks the binding turnover constraint on net Sharpe; cheap. **NEEDS_DIFF** — must report Δ vs director #4 (band) and #5 (EWMA), else re-measures a docketed lever. |
| 7 | **H-D2** calendar-selective overnight harvest | D | Market/Exec | ✅ | 2.5 | 3 | 3 | 3 | 1 | medium | Calendar-conditioned time-series harvest that defeats the turnover objection killing the uniform overnight book; distinct from F-006/F-019 and director #2. Thin decayed edge (honest). |
| 8 | **H-C-sbcorr** stock-bond correlation regime → defensive leg | C | Portfolio/Est | ✅ | 3 | 2 | 3 | 3 | 1 | medium | Attacks the F-012/F-020 blind assumption that bonds hedge; data on disk. **NEEDS_DIFF** — must beat the fixed-hedge AND the momentum-picked TLT/BIL leg; report as a hedge (NR-5), never alpha. |
| 9 | **H-D3** adverse-gap execution deferral | D | Execution | ✅ | 2 | 3 | 2 | 2 | 1 | medium | Cheap complement to H-D1. Low prior (~35%) — NR-1 says gaps continue rather than revert; the narrow adverse-gap-tail reversion is the bet, and a kill is useful. |
| 10 | **H-C-value** cross-asset 5y-reversal value | C | Market | ✅ | 2 | 3 | 3 | 3 | 2 | moonshot | Genuinely diversifying (opposite sign to the momentum books), data on disk — but ~4 independent 5y windows ⇒ low power; more a low-cost registered probe than a decisive test. |
| — | *forward-collect / data-build (discounted — collect first, cannot move belief this quarter)* | | | ❌ | | | | | | | |
| 11 | **H-E4** momentum × earnings-confirmation (fundamental momentum) | E | Market | ❌ | 3 | 4 | 4 | 4 | 3 | moonshot | F-016's *sanctioned* momentum×earnings reopen; re-grades a dead source. Pipeline (earnings-fwd) already accruing — highest-value forward item, but blocked on months of PIT depth. |
| 12 | **HYP-A4-03-lowcov** coverage-conditioned PEAD (absorbs H-E2) | A | Market | ❌ | 3 | 3 | 4 | 3 | 2 | moonshot | Cheapest new feed (FREE rec-count), extends the accruing earnings track, closes the F-016 diffusion door. Forward-only; low pre-test in compressed large-cap coverage. |
| 13 | **H-E3** promoted family × macro funding/inflation regime | E | Market | ❌ | 2.5 | 5 | 3 | 4 | 2 | moonshot | Highest decision value of all — adjudicates trend-ALPHA vs levered-BETA on the axis F-020 lacked, re-grading the promoted family's level. But few macro regimes ⇒ low power, 2022-artifact risk; needs FRED ingest. |
| 14 | **HYP-A4-01-estrev** forward analyst estimate-revision drift | A | Market | ❌ | 3 | 3 | 3 | 3 | 3 | — | New nightly `revisions.jsonl` feed; additive to PEAD (CJL). Forward-only accrual. |
| 15 | **H-C-carry** cross-asset carry (bond slice free/FRED) | C | Market | ❌ | 3 | 3 | 4 | 4 | 3 | — | Orthogonal to the whole trend library (KMPV); bond-carry slice cheap from FRED, full x-asset licensed. Post-2018 decay + short-vol crash risk. |
| 16 | **HYP-A4-02-revqual** revenue-confirmed beat quality | A | Market | ❌ | 3 | 3 | 3 | 3 | 3 | — | New revenue axis; free source unproven, thin cohorts accrue slowly. |
| 17 | **HYP-A4-04-disagree** analyst-disagreement × surprise (DMS) | A | Market | ❌ | 2.5 | 3 | 3 | 3 | 3 | — | Distinct from the prereg return-dispersion conditioner; free rec-spread proxy is noisy ⇒ mislabel risk. |
| 18 | **H-C-breakeven** breakeven-inflation trend rotation | C | Market | ❌ | 2.5 | 3 | 3 | 3 | 2 | — | Cheap FRED enable, clear mechanism — but one inflation up-cycle in-sample ⇒ single-regime trap (F-020 lesson); pre-register a pre/post split. |
| 19 | **H-FF-01** S&P 600/400 index-add forced demand | B | Market | ❌ | 2.5 | 3 | 4 | 3 | 5 | — | F-005's *named* reopen (small-cap, less-efficient universe) — legitimate but data-blocked: no PIT 600/400 membership or delisted-inclusive small-cap prices. Heavy data build. |
| 20 | **H-FF-02** IPO lockup-expiry supply shock | B | Market | ❌ | 2 | 3 | 3 | 4 | 5 | — | New source, short-biased; EDGAR S-1 parse + survivorship post-IPO panel + borrow costs. |
| 21 | **H-FF-03** secondary-offering pressure + reversal | B | Market | ❌ | 2 | 3 | 3 | 3 | 5 | — | New source; EDGAR 424B5/8-K deal terms + survivorship + borrow; info-vs-liquidity hard to separate in-repo. |
| 22 | **H-FF-04** Russell reconstitution forced flow | B | Market | ❌ | 2 | 3 | 3 | 3 | 5 | — | New source but most-arbitraged/decayed in the lane (F-005 cautionary prior); Russell membership history absent. |
| 23 | **H-D4-auction** closing-auction imbalance | D | Exec/Market | ❌ | ? | 3 | 3 | 4 | 5 | park | Honest data-gap marker (no bid/ask/auction/tick data anywhere) — the F-019 "higher-frequency harness" reopen; PARK until data is acquired. |

---

## Bucket composition (near-term actionable set = the 10 testable-now)

- **High (4 ≈ 40%):** H-E1, H-D1, H-lw-target, H-idio-shrink — two sanctioned/flagged-open reopens
  (near-zero overhead), one live-book-actionable execution test, one orthogonal estimator lever. All ≤~40-line
  diffs on in-repo panels, each <1 min runtime, each decisive in every branch.
- **Medium (4-5 ≈ 40%):** H-robust-cov, H-cov-temporal-smooth, H-D2, H-C-sbcorr, H-D3 — orthogonal
  probes and open-door closers at coin-toss-to-moderate P; two carry NEEDS_DIFF caveats (report Δ vs the
  docketed lever).
- **Moonshot (≈ 20%):** H-C-value (thin-window, testable-now but low-power) + the highest-value
  forward-collect items whose payoff is a source re-grade (H-E4, HYP-A4-03, H-E3). Speculative payoff,
  higher cost / data-gated.

## Sequencing

1. **Run the 4 high-bucket testable-now experiments first** (H-E1, H-D1, H-lw-target, H-idio-shrink) —
   all cheap in-repo, each retires or advances a live docket entry (NR-1 reopen, live-book execution
   leakage, RESULTS.md blunt-target, the untested diagonal lever). H-D1 chains onto the live reconcile
   harness (ops-reality) which will *empirically* confirm/deny the same overnight-gap leakage forward.
2. **Then the medium testable-now probes** (H-robust-cov, H-cov-temporal-smooth [Δ vs director #4/#5],
   H-D2, H-C-sbcorr [Δ vs momentum-picked leg], H-D3) — independent, parallelizable.
3. **Kick off forward-collection in parallel, now** (it gates everything below): the FREE feeds first —
   `stock/recommendation` count-sum for HYP-A4-03 (coverage) and HYP-A4-04 (disagreement proxy), the
   nightly forward-EPS snapshot for HYP-A4-01, and FRED ingest for H-E3 / H-C-carry / H-C-breakeven.
   H-E4 and the coverage/revision earnings hypotheses ride the already-accruing EXP-IC-EARNINGS-FWD panel —
   deeper each quarter, testable when n crosses the pre-registered bars.
4. **Data-build lane (B) and H-D4** wait for a survivorship-safe small-cap / EDGAR / Russell panel and an
   intraday feed respectively — scope these as data-acquisition tasks, not experiments, until the data exists.

## Standing caveats carried from the record

- **H-E1 is signal-space only.** A confirmed conditional IC is evidence-ladder **level 1** — tradability
  stays gated behind NR-1's cost wall (measured ≤2-3 bps/side or intraday execution). Do not promote a rank
  IC to a book.
- **H-C-sbcorr / H-E3 re-grade or hedge existing sources — not new market alpha.** Score H-C-sbcorr as a
  Portfolio/Estimator hedge (NR-5: "better tail, worse median" is a hedge, never additive alpha); H-E3's
  win-case merely relabels the promoted family's excess as trend-alpha vs beta, it adds no new book.
- **Forward-only means forward-only.** No Lane-A hypothesis may claim backfilled history as evidence
  (exp-ic-earnings-fwd rule); the yfinance earnings cache is survivorship-biased and unusable for H-E4.
