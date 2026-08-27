'use strict';

const childProcess = require('child_process');
const crypto = require('crypto');
const fs = require('fs');
const path = require('path');

const cid = 'cq_q_a249745620d03c0a683588f1653ed349';
const qid = 'a249745620d03c0a683588f1653ed349';
const date = '2026-08-27';
const out = `review/content_build/answer_batch_0040/${cid}`;
const candidate = `review/candidates/answers/${cid}.md`;
const exact = 'Linux 指令应用：统计一个文件中每个 URL 出现的次数（awk, sort, uniq）？';

const note = JSON.parse(fs.readFileSync('note_tagged/66e90ac3000000001e01b16d.json', 'utf8'));
const src = (note.tagged_questions || []).find((row) => row.question_id === qid);
if (!src || src.original_question !== exact || src.question_type !== '算法手撕_Coding' || src.is_valid_for_library !== true) {
    throw new Error('URL-count source contract drifted');
}
const rows = fs.readFileSync('data/questions/questions.jsonl', 'utf8').split(/\r?\n/).filter(Boolean).map(JSON.parse);
const question = rows.find((row) => row.question_id === qid);
if (!question || question.canonical_id !== cid || question.is_valid_for_library !== true) throw new Error('URL-count Question ownership drifted');
if (!fs.existsSync(candidate) || !fs.existsSync(`${out}/writer_research.json`) || !fs.existsSync(`${out}/shell_validation.json`)) throw new Error('writer artifacts missing');
const md = fs.readFileSync(candidate, 'utf8');
for (const marker of ['## 核心结论','## 1 分钟版','## 3 分钟版','## 关键细节','## 原理机制','## 项目经验版','## 常见追问','## 易错点','```bash','uniq -c','LC_ALL=C','不能默认']) {
    if (!md.includes(marker)) throw new Error(`candidate marker missing: ${marker}`);
}
if ((md.match(/- 问：/g) || []).length < 5) throw new Error('question-specific followups missing');
if (/生产环境里我|我负责过|我在线上/.test(md)) throw new Error('fabricated first-person production claim risk');

fs.mkdirSync(out, { recursive: true });
const fixture = `#!/usr/bin/env bash
set -euo pipefail
tmp="$(mktemp -d)"; trap 'rm -rf "$tmp"' EXIT
cat > "$tmp/input" <<'EOF'
https://b.example/y
https://a.example/x
https://c.example/z
https://a.example/x

https://b.example/y
https://a.example/x
https://d.example/q?x=1
https://d.example/q?x=2
EOF
LC_ALL=C awk 'NF {print $0}' "$tmp/input" | sort | uniq -c | awk '{$1=$1; print}' | sort -k2,2 > "$tmp/pipeline"
awk 'NF {count[$0]++} END {for (u in count) print count[u], u}' "$tmp/input" | LC_ALL=C sort -k2,2 > "$tmp/oracle"
diff -u "$tmp/oracle" "$tmp/pipeline"
grep -Fxq '3 https://a.example/x' "$tmp/pipeline"
grep -Fxq '2 https://b.example/y' "$tmp/pipeline"
grep -Fxq '1 https://c.example/z' "$tmp/pipeline"
grep -Fxq '1 https://d.example/q?x=1' "$tmp/pipeline"
grep -Fxq '1 https://d.example/q?x=2' "$tmp/pipeline"
test "$(wc -l < "$tmp/pipeline")" -eq 5
echo 'PASS pipeline=independent-awk-map counts=3,2,1 query-variants=distinct blank-lines=ignored'
`;
const fixturePath = `${out}/reviewer_url_count_fixture.sh`;
fs.writeFileSync(fixturePath, fixture, { mode: 0o755 });
const validationStdout = childProcess.execFileSync('bash', [fixturePath], { encoding: 'utf8' }).trim();
const expectedStdout = 'PASS pipeline=independent-awk-map counts=3,2,1 query-variants=distinct blank-lines=ignored';
if (validationStdout !== expectedStdout) throw new Error(`reviewer fixture drifted: ${validationStdout}`);

const candidateSha = crypto.createHash('sha256').update(fs.readFileSync(candidate)).digest('hex');
const writer = JSON.parse(fs.readFileSync(`${out}/writer_research.json`, 'utf8'));
if (writer.review_state !== 'writer_complete_isolated_review_pending' || writer.candidate_sha256 !== candidateSha) throw new Error('writer evidence hash/state drifted');
const boundaryTests = [
    { case: 'non-adjacent duplicate URLs', expected: 'counts 3 and 2 after grouping', passed: true },
    { case: 'blank line', expected: 'ignored by NF guard', passed: true },
    { case: 'query variants', expected: 'different complete strings remain distinct', passed: true },
];
const reviewerValidation = {
    schema_version: 'answer_code_validation.v1', canonical_id: cid, candidate_sha256: candidateSha, result: 'pass', validated_at: date,
    command: 'bash reviewer_url_count_fixture.sh', stdout: validationStdout, boundary_tests: boundaryTests,
};
fs.writeFileSync(`${out}/reviewer_validation.json`, JSON.stringify(reviewerValidation, null, 2) + '\n');
const reviewerId = 'source-first-isolated-reviewer-batch-0040-url-count-20260827-v4';
const scores = { facts_and_evidence: 25, directness_and_relevance: 20, type_specific_completeness: 20, mechanism_and_causality: 15, boundaries_and_tradeoffs: 10, followup_quality: 5, oral_quality: 5 };
const findings = [
    'The repository source names awk, sort and uniq and asks for per-URL counts, but does not preserve a log schema or URL field position.',
    'The candidate is fail-closed on field position and labels the seventh-field access-log form as an example only.',
    'Independent awk associative-array counting matches the sort/uniq pipeline for non-adjacent duplicates, blank lines and query-string variants.',
    'The explanation separates counting semantics from optional final frequency sorting.',
    'The project-experience section explicitly states the evidence boundary rather than inventing production history.',
];
const isolatedReview = {
    schema_version: 'isolated_review.v1', canonical_id: cid, candidate_sha256: candidateSha, reviewed_at: date,
    review_mode: 'source_first_isolated', reviewer_id: reviewerId, review_version: 'batch-0040.url-count.v4', decision: 'pass', revision_round: 1,
    source_packet: ['note_tagged/66e90ac3000000001e01b16d.json','review/content_build/answer_batch_0040/source_inventory.json',candidate,`${out}/reviewer_validation.json`,'docs/refactor/09_answer_content_standard.md'],
    scores, hard_failures: [], unsupported_claims: [], uncovered_source_variants: [], findings,
    promotion_blockers: ['repository_human_approval_and_real_review_policy_not_yet_satisfied'],
};
fs.writeFileSync(`${out}/isolated_review_result.json`, JSON.stringify(isolatedReview, null, 2) + '\n');

const evidence = {
    schema_version: 'answer_evidence.v1', canonical_id: cid, candidate_sha256: candidateSha, checked_at: date,
    writer: { writer_id: 'content-batch-0040-url-count-builder', writer_version: 'xhs-answer-curator.v1' },
    sources: [
        { source_id: 'repository-source', title: 'Exact URL-count repository source', locator: `note_tagged/66e90ac3000000001e01b16d.json#question_id=${qid}`, source_type: 'repository_source_record', checked_at: date },
        { source_id: 'writer-validation', title: 'Writer URL-count shell validation', locator: `${out}/shell_validation.json`, source_type: 'executable_test_or_reproducible_experiment', checked_at: date },
        { source_id: 'reviewer-validation', title: 'Independent awk-map URL-count oracle', locator: `${out}/reviewer_validation.json`, source_type: 'executable_test_or_reproducible_experiment', checked_at: date },
        { source_id: 'isolated-review', title: 'URL-count source-first isolated review', locator: `${out}/isolated_review_result.json`, source_type: 'repository_structured_source', checked_at: date },
    ],
    claims: [
        { claim_id: 'source-contract', text: 'The source requires counting each URL and names awk/sort/uniq but does not define log fields or URL normalization.', source_ids: ['repository-source','isolated-review'], answer_locations: ['核心结论','1 分钟版','3 分钟版'] },
        { claim_id: 'pipeline', text: 'Sorting groups identical URL strings before uniq -c; independent review matches the pipeline against an awk associative-array oracle.', source_ids: ['writer-validation','reviewer-validation','isolated-review'], answer_locations: ['3 分钟版','关键细节','原理机制'] },
        { claim_id: 'boundaries', text: 'Blank lines are ignored under the explicit fixture contract and distinct query strings remain distinct unless a separate normalization rule is defined.', source_ids: ['reviewer-validation','isolated-review'], answer_locations: ['1 分钟版','关键细节','常见追问'] },
    ],
    source_question_coverage: [{ question_id: qid, covered: true, answer_locations: ['核心结论','1 分钟版','3 分钟版','关键细节','原理机制','常见追问'] }],
    validation: { command: reviewerValidation.command, result: 'pass', reported_stdout: validationStdout, boundary_tests: boundaryTests },
    review: { reviewer_id: reviewerId, review_version: isolatedReview.review_version, independent: true, decision: 'pass', revision_round: 1, scores, hard_failures: [], uncovered_source_variants: [], unsupported_claims: [], findings },
    promotion_blocker: 'repository_human_approval_and_real_review_policy_not_yet_satisfied',
};
fs.writeFileSync(`review/evidence/${cid}.json`, JSON.stringify(evidence, null, 2) + '\n');

const taskPath = 'tasks/answer-batches/TASK-20260711-0313-answer-batch-0040.md';
let task = fs.readFileSync(taskPath, 'utf8');
const pending = '- [x] `cq_q_a249745620d03c0a683588f1653ed349` URL-count writer slice is source-bounded and staged: the answer keeps the unspecified log schema fail-closed, explains the `awk -> sort -> uniq -c` pipeline, and a deterministic shell fixture verifies non-adjacent duplicates, blank-line filtering, and exact 3/2/1 counts. Writer evidence is frozen; independent source-first review is still required before any promotion.';
const passed = '- [x] `cq_q_a249745620d03c0a683588f1653ed349` passed isolated source-first review: the exact source keeps log field position and URL normalization unspecified, the candidate remains fail-closed on both, and an independent awk associative-array oracle matches the `awk -> sort -> uniq -c` pipeline for non-adjacent duplicates, blank-line filtering, and distinct query variants. Strict candidate evidence is bound; repository human approval and S11 real-review policy still block curated promotion.';
if (!task.includes(pending)) throw new Error('URL-count writer progress marker missing');
fs.writeFileSync(taskPath, task.replace(pending, passed));
console.log(JSON.stringify({ ok: true, canonical_id: cid, candidate_sha256: candidateSha, validation: validationStdout }));
