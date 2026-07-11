export const meta = {
  name: 'redteam-audit',
  description: 'Independent 10-agent red-team audit of alpha-lab evidence + adjudication',
  phases: [
    { title: 'Audit', detail: '10 independent auditors, isolated outputs, no cross-reading' },
    { title: 'Adjudicate', detail: 'reproduce CRITICAL/HIGH findings, resolve conflicts, verdicts' },
  ],
}

const FINDING = {
  type: 'object',
  required: ['id', 'component', 'severity', 'status', 'summary'],
  properties: {
    id: { type: 'string' }, component: { type: 'string' }, category: { type: 'string' },
    severity: { type: 'string', enum: ['CRITICAL', 'HIGH', 'MEDIUM', 'LOW'] },
    status: { type: 'string', enum: ['CONFIRMED BUG', 'CONFIRMED METHODOLOGICAL WEAKNESS', 'PLAUSIBLE CONCERN', 'RULED OUT', 'NOT TESTABLE WITH CURRENT DATA'] },
    summary: { type: 'string' }, evidence: { type: 'string' },
    affects_paper_evidence: { type: 'string' }, belief_change: { type: 'string' },
  },
}
const REPORT = {
  type: 'object',
  required: ['agent', 'findings', 'summary', 'report_path'],
  properties: {
    agent: { type: 'string' },
    findings: { type: 'array', items: FINDING },
    summary: { type: 'string' },
    report_path: { type: 'string' },
  },
}

const COMMON = (n, name) => `
You are Red-Team ${name} (Agent ${n}) auditing ~/projects/alpha-lab at frozen commit
ffb5778 (verify with git rev-parse HEAD; if HEAD moved, note it and audit the frozen
commit's content via git show where it matters).

READ FIRST, in order:
1. redteam/2026-07-10/SCOPE.md (frozen checksums — verify data files against them before use)
2. redteam/2026-07-10/CHARTER.md — sections 1-4 and YOUR agent section ONLY. Execute it.
Repository context you may use: research/hunt2026/ (harness.py, specs/, SPEC_CONVENTIONS.md,
TRIAL_LEDGER.md, FAILURES.md, RESEARCH_OBJECTS.md, walkforward/, robustness/, results*/,
preregistrations/), research/estimator_lab/, scripts/hunt_paper_run.py,
scripts/hunt_paper_reconcile.py, core/, ledgers/hunt2026/, memos/, tests/.

HARD RULES (charter sec 1+3):
- READ-ONLY outside redteam/2026-07-10/agent${n}/ — write ALL outputs (report.md, scratch
  code, patch proposals as .patch files, difference CSVs) there and nowhere else.
- Never modify frozen specs, panels, manifest, ledgers, schedulers; never touch the broker
  in a mutating way (read-only API calls allowed only if your section needs fills/positions).
- Do not read redteam/2026-07-10/agent<other>/ directories.
- Use ~/projects/alpha-lab/.venv/bin/python. Attempt to FALSIFY claims; never tune.
- Every finding needs the classification fields from charter sec 4; do not call a
  hypothetical a bug; use RULED OUT liberally where you actually ruled things out.
Write redteam/2026-07-10/agent${n}/report.md (full detail, reproducible commands, quoted
tables) and return the structured summary. Your final output is data for the Adjudicator.`

phase('Audit')
const auditors = await parallel([
  () => agent(`${COMMON(1, 'Code & Leakage Auditor')}`, { label: 'rt:1-code-leakage', phase: 'Audit', schema: REPORT, effort: 'high' }),
  () => agent(`${COMMON(2, 'Independent Engine Auditor')}`, { label: 'rt:2-engine', phase: 'Audit', schema: REPORT, effort: 'high' }),
  () => agent(`${COMMON(3, 'Data & Universe Auditor')}`, { label: 'rt:3-data', phase: 'Audit', schema: REPORT, effort: 'high' }),
  () => agent(`${COMMON(4, 'Statistical & Selection Auditor')}`, { label: 'rt:4-stats', phase: 'Audit', schema: REPORT, effort: 'high' }),
  () => agent(`${COMMON(5, 'Market & Execution Realism Auditor')}`, { label: 'rt:5-execution', phase: 'Audit', schema: REPORT, effort: 'high' }),
  () => agent(`${COMMON(6, 'Robustness & Perturbation Auditor')}`, { label: 'rt:6-perturbation', phase: 'Audit', schema: REPORT, effort: 'high' }),
  () => agent(`${COMMON(7, 'Regime & Concentration Auditor')}`, { label: 'rt:7-regime', phase: 'Audit', schema: REPORT, effort: 'high' }),
  () => agent(`${COMMON(8, 'Clean-Room Replication Auditor')}
EXTRA CONSTRAINT unique to you: you may NOT open any spec.py under research/hunt2026/specs/
or any strategy code — your inputs are params.json, MECHANISM.md, SPEC_CONVENTIONS.md, the
research briefs in research/hunt2026/research_findings.json, and the panels. You MAY read
harness.py ONLY to learn the scoring convention you must match, not to copy code.`, { label: 'rt:8-cleanroom', phase: 'Audit', schema: REPORT, effort: 'high' }),
  () => agent(`${COMMON(9, 'Risk & Return-Source Auditor')}`, { label: 'rt:9-risk-source', phase: 'Audit', schema: REPORT, effort: 'high' }),
  () => agent(`${COMMON(10, 'Adversarial Implementation Auditor')}`, { label: 'rt:10-adversarial', phase: 'Audit', schema: REPORT, effort: 'high' }),
])

const ok = auditors.filter(Boolean)
log(`${ok.length}/10 auditors reported; adjudicating`)

phase('Adjudicate')
const VERDICT = {
  type: 'object',
  required: ['verdicts', 'confirmed_bugs', 'summary', 'paper_evidence_usable', 'report_path'],
  properties: {
    verdicts: { type: 'array', items: { type: 'object', required: ['book', 'verdict'], properties: {
      book: { type: 'string' },
      verdict: { type: 'string', enum: ['INVALIDATED', 'BLOCKED', 'PROVISIONAL', 'SURVIVES RED-TEAM AUDIT', 'NOT TESTABLE'] },
      overall_confidence: { type: 'number' }, one_liner: { type: 'string' } } } },
    confirmed_bugs: { type: 'array', items: { type: 'string' } },
    methodological_weaknesses: { type: 'array', items: { type: 'string' } },
    ruled_out: { type: 'array', items: { type: 'string' } },
    paper_evidence_usable: { type: 'string' },
    fixes_before_paper_interpretation: { type: 'array', items: { type: 'string' } },
    fixes_before_live_capital: { type: 'array', items: { type: 'string' } },
    results_to_rerun_or_relabel: { type: 'array', items: { type: 'string' } },
    summary: { type: 'string' }, report_path: { type: 'string' },
  },
}
const adj = await agent(`
You are the Red-Team ADJUDICATOR for ~/projects/alpha-lab (frozen commit ffb5778).
Read redteam/2026-07-10/CHARTER.md sections 6-9 (your mandate), SCOPE.md, then EVERY
agent report: redteam/2026-07-10/agent{1..10}/report.md.

Structured agent summaries (findings lists) for cross-reference:
${JSON.stringify(ok.map(r => ({ agent: r.agent, findings: r.findings, summary: r.summary })), null, 1).slice(0, 60000)}

Your mandate (charter sec 6): REPRODUCE every CRITICAL and HIGH finding yourself
(re-run the agent's reproducible procedure; a finding you cannot reproduce gets demoted
with a note); resolve conflicts between agents (code vs data vs method vs prose); dedupe;
separate shared-platform defects from strategy-specific ones; list historical reports to
withdraw/amend/rerun; rule whether current paper observations remain usable. You may not
improve strategies. Read-only outside redteam/2026-07-10/adjudicator/.

Then produce the charter sec 9 final report at redteam/2026-07-10/adjudicator/FINAL_REPORT.md:
scope+checksums; executive verdict; confirmed bugs; methodological weaknesses; plausible
unresolved concerns; ruled out; shared-engine findings; data findings; strategy-by-strategy
verdicts (INVALIDATED/BLOCKED/PROVISIONAL/SURVIVES/NOT TESTABLE) with the 8-axis 0-100
confidence scorecard (forward evidence capped at 60); clean-room differences; statistical
conclusions; execution conclusions; return-source decomposition; production gates status
(before-paper-interpretation and before-live-capital, per charter sec 10); results to
rerun/relabel; remaining unknowns; the exact recommended NEXT AUDIT (not an alpha
experiment). Every conclusion: signed effect size, uncertainty, economic materiality,
scope condition. Prose quotes tables. Return the structured verdict.`,
  { label: 'rt:adjudicator', phase: 'Adjudicate', schema: VERDICT, effort: 'max' })

return { auditors: ok.map(r => ({ agent: r.agent, n: r.findings.length, summary: r.summary.slice(0, 400) })), adjudication: adj }
