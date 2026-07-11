export const meta = {
  name: 'director-generate-queue',
  description: 'Research Director pipeline: generate hypotheses -> dedup-gate vs failures -> engineer minimal experiments -> allocate research capital into a ranked queue',
  phases: [
    { title: 'Generate', detail: 'hypothesis generators (Layer A / B / C-D)' },
    { title: 'Review', detail: 'failure-database dedup gate' },
    { title: 'Engineer', detail: 'minimal frozen-spec designs for approved hypotheses' },
    { title: 'Allocate', detail: 'rank by info-gain/cost, bucket 40/40/20' },
  ],
}

const HYP = {
  type: 'object', required: ['hypotheses'],
  properties: { hypotheses: { type: 'array', items: {
    type: 'object',
    required: ['id', 'statement', 'mechanism', 'layer', 'direction', 'supporting_evidence', 'contradicting_evidence', 'confidence'],
    properties: {
      id: { type: 'string', description: 'short slug, e.g. H-sector-rev' },
      statement: { type: 'string', description: 'falsifiable hypothesis, not a strategy' },
      mechanism: { type: 'string', description: 'who is on the other side / why the effect exists' },
      layer: { type: 'string', enum: ['A', 'B', 'C', 'D'] },
      direction: { type: 'string', description: 'predicted sign/effect' },
      supporting_evidence: { type: 'string', description: 'cite repo files or literature' },
      contradicting_evidence: { type: 'string' },
      confidence: { type: 'number', description: '0-100' },
    } } } },
}

const REVIEW = {
  type: 'object', required: ['reviews'],
  properties: { reviews: { type: 'array', items: {
    type: 'object',
    required: ['id', 'related_failures', 'similarity', 'recommendation', 'justification'],
    properties: {
      id: { type: 'string' },
      related_failures: { type: 'string', description: 'failure IDs / ledger rows, or "none"' },
      similarity: { type: 'number', description: '0-1 vs the nearest prior test' },
      recommendation: { type: 'string', enum: ['APPROVE', 'REJECT', 'NEEDS_DIFFERENTIATION'] },
      justification: { type: 'string' },
    } } } },
}

const DESIGN = {
  type: 'object',
  required: ['id', 'layer', 'control', 'treatment', 'success_criteria', 'failure_criteria', 'expected_effect', 'required_data', 'minimal_impl', 'runtime_est', 'complexity', 'info_gain'],
  properties: {
    id: { type: 'string' }, layer: { type: 'string' },
    control: { type: 'string' }, treatment: { type: 'string' },
    success_criteria: { type: 'string' }, failure_criteria: { type: 'string' },
    expected_effect: { type: 'string' }, required_data: { type: 'string' },
    minimal_impl: { type: 'string', description: 'the smallest thing that tests it, on existing panels where possible' },
    runtime_est: { type: 'string' }, complexity: { type: 'number', description: '1-10, lower simpler' },
    info_gain: { type: 'string', description: 'what branch of hypothesis space each outcome eliminates' },
  },
}

const QUEUE = {
  type: 'object', required: ['markdown', 'top_pick'],
  properties: {
    markdown: { type: 'string', description: 'the full EXPERIMENT_QUEUE.md body' },
    top_pick: { type: 'string', description: 'id of the single highest info-gain/cost experiment' },
  },
}

const REPO = `Repo: ~/projects/alpha-lab. Ground every claim in real files. Read as needed:
research/hunt2026/TRIAL_LEDGER.md (18 specs + statuses), FAILURES.md (F-001..F-016 +
negative-result registry), RESEARCH_OBJECTS.md (Layer A-D registry), walkforward/summary.md,
robustness/{param_maps,deflated,ic,ic_screen,xmarket}.md (some written by the platform fleet),
research/estimator_lab/ (if present). The prime directive: reduce uncertainty, optimize
information gain per experiment, NOT backtest return. Free daily data only (yfinance/Alpaca);
costs 10bps/side stocks, 2bps ETFs; leverage <= 2x.`

phase('Generate')
const gens = await parallel([
  () => agent(`${REPO}\nROLE: Hypothesis Generator, LAYER A (does a phenomenon exist?).
Propose 4 falsifiable, mechanism-referenced hypotheses about market phenomena testable on
our data. NOT strategies, NO parameters, NO implementation. Favor ideas the IC screen or
cross-market work could newly illuminate. Avoid anything already killed (check FAILURES.md).`,
    { label: 'gen:layerA', schema: HYP }),
  () => agent(`${REPO}\nROLE: Hypothesis Generator, LAYER B (can we estimate it better?).
Propose 4 estimator-improvement hypotheses (covariance / PCA / shrinkage / factor /
residualization / random-matrix), each a matched-pair claim: new estimator beats current on
realized out-of-sample RISK. The Goldberg/JSE k>1 program lives here — extend it, don't
repeat the settled k=1 result (F-010).`,
    { label: 'gen:layerB', schema: HYP }),
  () => agent(`${REPO}\nROLE: Hypothesis Generator, LAYERS C & D (portfolio construction /
execution). Propose 4 hypotheses about turning known signals into better portfolios or
executing them better (turnover control, regime-conditional sizing, open/close execution
reopening F-006, confidence-weighted ensembling). Matched-pair framing.`,
    { label: 'gen:layerCD', schema: HYP }),
])
const hyps = gens.filter(Boolean).flatMap(g => g.hypotheses)
log(`generated ${hyps.length} hypotheses`)

phase('Review')
const chunks = [[], [], []]
hyps.forEach((h, i) => chunks[i % 3].push(h))
const reviews = (await parallel(chunks.filter(c => c.length).map(chunk => () =>
  agent(`${REPO}\nROLE: Failure Database Reviewer (the dedup gate). For EACH hypothesis
below, search FAILURES.md, TRIAL_LEDGER.md, RESEARCH_OBJECTS.md and decide: already-failed /
parameter-variation / new-regime-test / new-mechanism. REJECT parameter variations and
re-runs of dead ideas; APPROVE genuinely new mechanisms/universes/estimators;
NEEDS_DIFFERENTIATION if close but arguably distinct. Be strict — protecting the trial count
is the point.\n\nHYPOTHESES:\n${JSON.stringify(chunk, null, 1)}`,
    { label: 'review:gate', schema: REVIEW }))))
  .filter(Boolean).flatMap(r => r.reviews)
const verdict = Object.fromEntries(reviews.map(r => [r.id, r]))
const approved = hyps.filter(h => verdict[h.id] && verdict[h.id].recommendation !== 'REJECT')
log(`${approved.length}/${hyps.length} approved or needs-differentiation`)

phase('Engineer')
const designs = (await parallel(approved.map(h => () =>
  agent(`${REPO}\nROLE: Experiment Engineer. Convert this ONE hypothesis into the MINIMAL
experiment: control + treatment differing in exactly ONE layer, success + failure criteria,
expected effect size, required data, runtime estimate, complexity 1-10, and the info_gain
(what each outcome eliminates). Prefer designs runnable on existing panels
(research/hunt2026/panel_2005.parquet) with <=3 frozen params, no grid search. Reviewer
note: ${JSON.stringify(verdict[h.id] || {})}.\n\nHYPOTHESIS:\n${JSON.stringify(h, null, 1)}`,
    { label: `eng:${h.id}`, schema: DESIGN })))).filter(Boolean)
log(`engineered ${designs.length} experiment designs`)

phase('Allocate')
const queue = await agent(`${REPO}\nROLE: Research Capital Allocator. Rank ALL experiment
designs below by expected information gain / total cost. Bucket them 40% high-confidence
extensions, 40% medium-confidence exploration, 20% moonshots. For each: P(success),
info-gain (branch eliminated), cost (research + runtime), score = infogain/cost, and its
kill condition. Then emit the full EXPERIMENT_QUEUE.md body as markdown: a ranked table
(rank, id, bucket, layer, P(success), info-gain/cost score, kill condition, one-line design)
followed by the top-3 experiments written out in full pre-registration form
(hypothesis/mechanism/layer/expected/alternative/failure-condition/data/minimal-impl). Name
the single highest-value next experiment as top_pick. Optimize for learning per experiment,
not expected return.\n\nDESIGNS:\n${JSON.stringify(designs, null, 1)}`,
  { label: 'allocate:queue', schema: QUEUE, effort: 'high' })

return { n_generated: hyps.length, n_approved: approved.length,
         n_designed: designs.length, top_pick: queue.top_pick, markdown: queue.markdown }
