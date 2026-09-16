# CLAUDE.md — alpha-lab

Rules for working in this repo. **Paper-trading research only; nothing here places real orders.**
These override default behavior.

## The one rule that matters

The biggest risk here is not lack of ideas, it is **accidentally fooling yourself**. Every rule
below exists to make a too-good result impossible to ship unquestioned.

When a backtest looks great, **assume a bug until proven otherwise**. Real precedent from this repo:
pairs showed **Sharpe 4.77 → −0.06** the moment a formation-vs-trading look-ahead was fixed
(`tracks/statarb/STATE.md`). The catch was the value, not the number. Act like a skeptical research
partner, not a cheerleader.

## No look-ahead (hard boundary)

- **Fit on the formation window only, apply out-of-sample.** Never standardize or estimate a signal
  using the trading window's own mean/std/params. This is THE pairs bug — each day "knew" the
  window's future mean. Bands come from the *formation* window (`pair_zscore_oos`).
- **Lag before you trade.** Position at *t* uses information through *t−1*; PnL uses lagged weights.
- **Point-in-time universe.** Membership must be as-of the date, never today's index constituents
  (survivorship). Corporate actions applied as-of, not restated.
- If you cannot name *where* the future would leak in, you have not checked hard enough. Say so.

## Train / test separation

- **Replicate first (Stage 2)** to validate the pipeline, not to claim alpha.
- **OOS is the only result that counts.** Always report **net of costs**.
- **Deflated Sharpe with an honest `n_trials`.** Count *every* variant you actually tried
  (`{mega, wide} × {formation/trading/entry params}`), not 1. `n_trials=1` inflates the deflated
  probability — it is a lie you tell yourself.
- **Kill threshold: net Sharpe < 0.5 is dead.** Do not rescue it by adding knobs.

## Data lineage

- Every network pull appends to `data/manifest.jsonl` (`name, source, filters, path, rows, pulled_at`).
- **Tests never touch the network.** `scripts/` pull; `tests/` run offline on fixtures. Keep the full suite green (`.venv/bin/python -m pytest -q`).
- Heavy files (`data/`, `artifacts/`) are gitignored — the manifest + scorecard are the durable record.

## Code-review discipline (before changing anything)

- **Explain the architecture and its dependencies first.** Then propose the *smallest* change that works.
- No rewriting a module to add a feature. No new abstraction with one caller.
- **A bug fix targets the root cause** in the shared function, not the one caller named in the ticket.
- **Always add or extend a test.** A change that can't be tested offline is suspect.
- State assumptions out loud; flag anything that could be look-ahead.

## Stage gates (see README)

- **Stage 0 (hypothesis) and Stage 4 (verdict) are Kristen's calls.** Do not skip her gate.
- Starting a new experiment run or parameter sweep → use the **`quant-experiment`** skill; it stamps
  params + code version so every scorecard is reproducible.

## Cross-model review policy

Before merging, run the cross-model review gate on the diff. It is a three-round Claude+Codex
exchange that writes a verdict to the vault:

```
"$VAULT/scripts/cross_review.sh" ~/projects/alpha-lab [base_branch]
```

Not every change needs it. Split by blast radius:

- **Foundation** (full gate + Kristen reads the diff herself before merge): anything other code
  depends on. Here that means the scorecard / deflated-Sharpe math, the look-ahead guards
  (`pair_zscore_oos`, lagging, point-in-time universe), `data/manifest.jsonl` lineage, shared
  loaders in `scripts/`, and the stage-gate machinery. A bug in these silently corrupts every
  downstream result.
- **Leaf** (single-model pass, or none): a one-off hypothesis notebook under `hypotheses/` or a
  single track's exploratory analysis, a `STATE.md`/`STATUS.md` note, a README edit. If it can
  only fool itself and nothing imports it, skip the full gate.

Examples: editing the deflated-Sharpe formula → foundation. Adding a new pairs param sweep in one
track's notebook → leaf. Changing the shared OOS z-score function → foundation. Fixing a typo in a
track memo → leaf.

## Git: pull before push, always

- Before pushing, always `git pull --rebase origin main` first, then push. Don't stop to ask —
  just do it as part of the commit/push flow.
- The hourly `paper_publish.py` job pushes `STATUS.md`-only commits from a separate clone, so a
  rejected push here almost always means just that — rebase resolves it with no real conflict.
- Still narrate what's being committed and pushed as it happens — don't do it silently.
