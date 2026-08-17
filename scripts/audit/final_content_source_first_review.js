'use strict';

const fs = require('fs');
const path = require('path');
const crypto = require('crypto');
const { execFileSync } = require('child_process');

const ROOT = path.resolve(__dirname, '../..');
const REPORT_DIR = path.join(ROOT, 'review', 'reports');
const QUESTION_PATH = path.join(ROOT, 'data', 'questions', 'questions.jsonl');
const CANONICAL_PATH = path.join(ROOT, 'data', 'questions', 'canonical_questions.jsonl');
const ANSWER_DIR = path.join(ROOT, 'review', 'answers');
const PROGRESS_PATH = path.join(ROOT, 'review', 'progress.json');
const OUT_JSON = path.join(REPORT_DIR, 'FINAL_SOURCE_FIRST_REVIEW.json');
const OUT_MD = path.join(REPORT_DIR, 'FINAL_SOURCE_FIRST_REVIEW.md');
const PASS_MARKER = path.join(REPORT_DIR, 'FINAL_SOURCE_FIRST_REVIEW_PASS');

function readJsonl(file) {
  return fs.readFileSync(file, 'utf8')
    .split(/\r?\n/)
    .filter(Boolean)
    .map((line, index) => {
      try {
        return JSON.parse(line);
      } catch (error) {
        throw new Error(`${path.relative(ROOT, file)}:${index + 1}: ${error.message}`);
      }
    });
}

function readJson(file) {
  return JSON.parse(fs.readFileSync(file, 'utf8'));
}

function walk(dir) {
  if (!fs.existsSync(dir)) return [];
  const files = [];
  for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
    const full = path.join(dir, entry.name);
    if (entry.isDirectory()) files.push(...walk(full));
    else files.push(full);
  }
  return files;
}

function parseMetadata(text) {
  const first = text.split(/\r?\n/, 1)[0] || '';
  const match = first.match(/<!--\s*xhs-answer:\s*(\{.*\})\s*-->/);
  if (!match) return null;
  try {
    return JSON.parse(match[1]);
  } catch (_) {
    return null;
  }
}

function extractProgressIds(raw) {
  if (Array.isArray(raw)) {
    return raw.map((row) => row && row.canonical_id).filter(Boolean);
  }
  if (!raw || typeof raw !== 'object') return [];
  for (const key of ['items', 'progress', 'records', 'rows']) {
    if (Array.isArray(raw[key])) {
      return raw[key].map((row) => row && row.canonical_id).filter(Boolean);
    }
  }
  return Object.keys(raw).filter((key) => key.startsWith('cq_'));
}

function normalizedAnswerHash(text) {
  const normalized = text
    .replace(/<!--[^]*?-->/g, '')
    .replace(/cq_[A-Za-z0-9_-]+/g, '<CANONICAL_ID>')
    .replace(/\s+/g, ' ')
    .trim();
  return crypto.createHash('sha256').update(normalized).digest('hex');
}

function severityWeight(severity) {
  return { blocker: 4, critical: 3, major: 2, minor: 1, info: 0 }[severity] ?? 0;
}

function runGate(name, args) {
  const started = Date.now();
  try {
    execFileSync(args[0], args.slice(1), {
      cwd: ROOT,
      encoding: 'utf8',
      stdio: 'pipe',
      maxBuffer: 128 * 1024 * 1024,
    });
    return { name, status: 'PASS', exit_code: 0, duration_ms: Date.now() - started };
  } catch (error) {
    const output = `${error.stdout || ''}\n${error.stderr || ''}`.trim();
    return {
      name,
      status: 'FAIL',
      exit_code: Number.isInteger(error.status) ? error.status : 1,
      duration_ms: Date.now() - started,
      output_tail: output.slice(-12000),
    };
  }
}

function addFinding(findings, severity, code, message, evidence = {}) {
  findings.push({ severity, code, message, evidence, status: 'open' });
}

fs.mkdirSync(REPORT_DIR, { recursive: true });
if (fs.existsSync(PASS_MARKER)) fs.rmSync(PASS_MARKER);

// Source-first boundary: only current source/data and executable behavior are read
// before the conclusion is formed. Historical review/remediation records are not inputs.
const auditedSha = process.env.AUDITED_SHA || execFileSync('git', ['rev-parse', 'HEAD'], {
  cwd: ROOT,
  encoding: 'utf8',
}).trim();
const questions = readJsonl(QUESTION_PATH);
const canonicals = readJsonl(CANONICAL_PATH);
const progress = readJson(PROGRESS_PATH);
const findings = [];

const canonicalById = new Map();
for (const canonical of canonicals) {
  if (!canonical.canonical_id) {
    addFinding(findings, 'blocker', 'CANONICAL_ID_MISSING', 'A Canonical row has no canonical_id.');
    continue;
  }
  if (canonicalById.has(canonical.canonical_id)) {
    addFinding(findings, 'blocker', 'CANONICAL_ID_DUPLICATE', `Duplicate canonical_id ${canonical.canonical_id}.`);
  }
  canonicalById.set(canonical.canonical_id, canonical);
}

const questionById = new Map();
for (const question of questions) {
  if (question.question_id) questionById.set(question.question_id, question);
}
const validQuestions = questions.filter((question) => question.is_valid_for_library !== false);
const invalidQuestions = questions.filter((question) => question.is_valid_for_library === false);
const validUnassigned = validQuestions.filter((question) => !question.canonical_id);
if (validUnassigned.length) {
  addFinding(findings, 'blocker', 'VALID_QUESTION_UNASSIGNED', `${validUnassigned.length} valid Question rows have no canonical_id.`, {
    sample_question_ids: validUnassigned.slice(0, 25).map((row) => row.question_id),
  });
}

const danglingQuestionBindings = validQuestions.filter(
  (question) => question.canonical_id && !canonicalById.has(question.canonical_id),
);
if (danglingQuestionBindings.length) {
  addFinding(findings, 'blocker', 'QUESTION_BINDING_DANGLING', `${danglingQuestionBindings.length} Question rows reference a missing Canonical.`, {
    sample: danglingQuestionBindings.slice(0, 25).map((row) => ({
      question_id: row.question_id,
      canonical_id: row.canonical_id,
    })),
  });
}

const emptyCanonicals = [];
const membershipMismatches = [];
for (const canonical of canonicals) {
  const questionIds = Array.isArray(canonical.question_ids) ? canonical.question_ids : [];
  if (!questionIds.length) emptyCanonicals.push(canonical.canonical_id);
  for (const questionId of questionIds) {
    const question = questionById.get(questionId);
    if (!question || question.canonical_id !== canonical.canonical_id) {
      membershipMismatches.push({
        canonical_id: canonical.canonical_id,
        question_id: questionId,
        actual_canonical_id: question && question.canonical_id,
      });
    }
  }
}
if (emptyCanonicals.length) {
  addFinding(findings, 'major', 'CANONICAL_WITHOUT_SOURCE_QUESTION', `${emptyCanonicals.length} Canonicals have no question_ids.`, {
    sample_canonical_ids: emptyCanonicals.slice(0, 25),
  });
}
if (membershipMismatches.length) {
  addFinding(findings, 'blocker', 'CANONICAL_MEMBERSHIP_MISMATCH', `${membershipMismatches.length} Canonical/Question ownership mismatches exist.`, {
    sample: membershipMismatches.slice(0, 25),
  });
}

const answerFiles = walk(ANSWER_DIR).filter((file) => {
  if (!file.endsWith('.md')) return false;
  const relative = path.relative(ANSWER_DIR, file).split(path.sep);
  return !relative.includes('archive') && !relative.includes('archived');
});
const answerById = new Map();
const answerDefects = [];
const normalizedClusters = new Map();
for (const file of answerFiles) {
  const relative = path.relative(ROOT, file);
  const filenameId = path.basename(file, '.md');
  const text = fs.readFileSync(file, 'utf8');
  const metadata = parseMetadata(text);
  const canonicalId = metadata && metadata.canonical_id || filenameId;
  if (answerById.has(canonicalId)) {
    addFinding(findings, 'blocker', 'ACTIVE_ANSWER_DUPLICATE', `More than one active answer exists for ${canonicalId}.`, {
      first: answerById.get(canonicalId).file,
      second: relative,
    });
  }
  answerById.set(canonicalId, { file: relative, metadata, text });

  if (!metadata) answerDefects.push({ canonical_id: canonicalId, file: relative, defect: 'metadata_missing_or_invalid' });
  else {
    if (metadata.canonical_id !== filenameId) {
      answerDefects.push({ canonical_id: canonicalId, file: relative, defect: 'metadata_filename_mismatch' });
    }
    if (metadata.status !== 'ready') {
      answerDefects.push({ canonical_id: canonicalId, file: relative, defect: 'status_not_ready', status: metadata.status });
    }
  }
  const body = text.replace(/^<!--[^\n]*-->\s*/, '');
  if (/(?:TODO|TBD|待补充|占位|请补充|\[填写|\{\{)/i.test(body)) {
    answerDefects.push({ canonical_id: canonicalId, file: relative, defect: 'placeholder' });
  }
  const hash = normalizedAnswerHash(text);
  if (!normalizedClusters.has(hash)) normalizedClusters.set(hash, []);
  normalizedClusters.get(hash).push(canonicalId);
}

const missingAnswers = canonicals
  .filter((canonical) => !answerById.has(canonical.canonical_id))
  .map((canonical) => canonical.canonical_id);
if (missingAnswers.length) {
  addFinding(findings, 'blocker', 'CANONICAL_ANSWER_MISSING', `${missingAnswers.length} Canonicals have no active answer.`, {
    sample_canonical_ids: missingAnswers.slice(0, 25),
  });
}
if (answerDefects.length) {
  const defectCounts = {};
  for (const row of answerDefects) defectCounts[row.defect] = (defectCounts[row.defect] || 0) + 1;
  addFinding(findings, 'major', 'ANSWER_NOT_COMPLETE', `${answerDefects.length} active-answer completion defects exist.`, {
    by_defect: defectCounts,
    sample: answerDefects.slice(0, 50),
  });
}

const massDuplicateClusters = [...normalizedClusters.values()]
  .filter((cluster) => cluster.length >= 20)
  .sort((left, right) => right.length - left.length);
if (massDuplicateClusters.length) {
  addFinding(findings, 'major', 'MASS_IDENTICAL_ANSWERS', `${massDuplicateClusters.length} normalized answer clusters contain 20 or more identical answers.`, {
    largest_clusters: massDuplicateClusters.slice(0, 10).map((cluster) => ({
      count: cluster.length,
      sample_canonical_ids: cluster.slice(0, 12),
    })),
  });
}

const progressIds = new Set(extractProgressIds(progress));
const missingProgress = canonicals
  .filter((canonical) => !progressIds.has(canonical.canonical_id))
  .map((canonical) => canonical.canonical_id);
if (missingProgress.length) {
  addFinding(findings, 'blocker', 'REVIEW_PROGRESS_MISSING', `${missingProgress.length} Canonicals have no ReviewProgress.`, {
    sample_canonical_ids: missingProgress.slice(0, 25),
  });
}
const orphanProgress = [...progressIds].filter((canonicalId) => !canonicalById.has(canonicalId));
if (orphanProgress.length) {
  addFinding(findings, 'major', 'REVIEW_PROGRESS_ORPHAN', `${orphanProgress.length} ReviewProgress records reference missing Canonicals.`, {
    sample_canonical_ids: orphanProgress.slice(0, 25),
  });
}

const invalidWithoutReason = invalidQuestions.filter((question) => {
  return !(question.invalid_reason || question.exclusion_reason || question.validation_reason || question.reason || question.invalid_reasons);
});
if (invalidWithoutReason.length) {
  addFinding(findings, 'major', 'EXCLUDED_QUESTION_WITHOUT_REASON', `${invalidWithoutReason.length} excluded Question rows lack a recorded reason.`, {
    sample_question_ids: invalidWithoutReason.slice(0, 25).map((row) => row.question_id),
  });
}

const suspiciousPersonalClaims = [];
for (const [canonicalId, answer] of answerById) {
  if (!/(我在|我负责|我们项目|线上事故|最终提升|最终降低)/.test(answer.text)) continue;
  if (/(项目映射|示例|模板|按真实经历|不要虚构|需替换|可结合)/.test(answer.text)) continue;
  suspiciousPersonalClaims.push({ canonical_id: canonicalId, file: answer.file });
}
if (suspiciousPersonalClaims.length) {
  addFinding(findings, 'major', 'UNVERIFIED_PERSONAL_CLAIMS', `${suspiciousPersonalClaims.length} answers contain first-person project claims without an explicit evidence/template boundary.`, {
    sample: suspiciousPersonalClaims.slice(0, 30),
  });
}

const gates = [
  runGate('npm test', ['npm', 'test']),
  runGate('npm run ci:check', ['npm', 'run', 'ci:check']),
  runGate('answer semantic gate', ['npm', 'run', 'ci:answer:semantic']),
  runGate('answer evidence gate', ['npm', 'run', 'ci:answer:evidence']),
  runGate('answer code gate', ['npm', 'run', 'ci:answer:code']),
  runGate('answer coverage gate', ['npm', 'run', 'ci:answer:coverage']),
];
for (const gate of gates.filter((row) => row.status !== 'PASS')) {
  addFinding(findings, 'blocker', 'EXECUTABLE_GATE_FAILED', `${gate.name} failed with exit code ${gate.exit_code}.`, {
    output_tail: gate.output_tail,
  });
}

const openBlockingFindings = findings.filter(
  (finding) => finding.status === 'open' && severityWeight(finding.severity) >= severityWeight('major'),
);
const metrics = {
  question_rows: questions.length,
  valid_question_rows: validQuestions.length,
  invalid_question_rows: invalidQuestions.length,
  valid_unassigned_count: validUnassigned.length,
  canonical_count: canonicals.length,
  active_answer_count: answerById.size,
  ready_answer_count: [...answerById.values()].filter((answer) => answer.metadata && answer.metadata.status === 'ready').length,
  missing_answer_count: missingAnswers.length,
  review_progress_count: progressIds.size,
  missing_review_progress_count: missingProgress.length,
  excluded_without_reason_count: invalidWithoutReason.length,
  mass_identical_answer_cluster_count: massDuplicateClusters.length,
};
const verdict = openBlockingFindings.length ? 'FAIL' : 'PASS';
const report = {
  schema_version: 'xhs_final_source_first_review.v1',
  audited_sha: auditedSha,
  generated_at: new Date().toISOString(),
  method: {
    source_first: true,
    historical_reviews_read_before_conclusion: false,
    review_scope: [
      'Question/Canonical ownership and reachability',
      'active Answer completeness and anti-template checks',
      'ReviewProgress completeness and orphan detection',
      'excluded Question explainability',
      'unverified personal-experience claim detection',
      'full repository and answer quality gates',
    ],
  },
  verdict,
  metrics,
  gates,
  findings,
  open_blocking_finding_count: openBlockingFindings.length,
};
fs.writeFileSync(OUT_JSON, `${JSON.stringify(report, null, 2)}\n`);

const markdown = [
  '# XHS Final Source-First Review',
  '',
  `- Fixed audited SHA: \`${auditedSha}\``,
  `- Verdict: **${verdict}**`,
  '- Review method: source-first; no historical review or remediation record was read before the conclusion.',
  `- Open Blocker/Critical/Major findings: ${openBlockingFindings.length}`,
  '',
  '## Completion Metrics',
  '',
  `- Question rows: ${metrics.question_rows}; valid: ${metrics.valid_question_rows}; valid unassigned: ${metrics.valid_unassigned_count}`,
  `- Canonicals: ${metrics.canonical_count}`,
  `- Active answers: ${metrics.active_answer_count}; ready: ${metrics.ready_answer_count}; missing: ${metrics.missing_answer_count}`,
  `- ReviewProgress: ${metrics.review_progress_count}; missing: ${metrics.missing_review_progress_count}`,
  `- Excluded rows without reason: ${metrics.excluded_without_reason_count}`,
  '',
  '## Executable Verification',
  '',
  ...gates.map((gate) => `- ${gate.status === 'PASS' ? 'PASS' : 'FAIL'} — \`${gate.name}\` (${gate.duration_ms} ms)`),
  '',
  '## Findings',
  '',
  ...(findings.length
    ? findings.map((finding) => `- **${finding.severity.toUpperCase()} ${finding.code}** — ${finding.message}`)
    : ['No findings.']),
  '',
  '## Final Decision',
  '',
  verdict === 'PASS'
    ? 'The fixed snapshot satisfies the repository-local refactor, content completeness, reachability, review-state, and executable quality gates. It is ready for final inspection.'
    : 'The fixed snapshot is not ready for final inspection. All open Blocker/Critical/Major findings must be remediated and the new SHA re-reviewed.',
  '',
].join('\n');
fs.writeFileSync(OUT_MD, markdown);
if (verdict === 'PASS') fs.writeFileSync(PASS_MARKER, `${auditedSha}\n`);

console.log(JSON.stringify({ audited_sha: auditedSha, verdict, metrics, open_blocking_finding_count: openBlockingFindings.length }));
if (verdict !== 'PASS') process.exitCode = 2;
