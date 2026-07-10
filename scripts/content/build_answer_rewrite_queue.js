#!/usr/bin/env node
'use strict';

const fs = require('fs');
const path = require('path');
const { loadCanonicalQuestions } = require('../lib/canonical_store');
const { readJson, readJsonl, stablePrettyStringify, stableStringify, writeJson, writeJsonl, ensureDir } = require('../lib/io');
const { answerPath, readAnswerFile } = require('../lib/answer_store');

const ROOT = path.resolve(__dirname, '..', '..');
const TYPE_ORDER = { coding: 0, mechanism: 1, scenario: 2, concept: 3, project: 4, behavior: 5 };

function outputPaths(root) {
    return {
        queue: path.join(root, 'data', 'manifests', 'quality', 'answer_rewrite_queue.jsonl'),
        batches: path.join(root, 'data', 'manifests', 'quality', 'answer_rewrite_batches.json'),
        typeAudit: path.join(root, 'data', 'manifests', 'quality', 'answer_type_audit.jsonl'),
        answers: path.join(root, 'review', 'answers'),
        taskDir: path.join(root, 'tasks', 'answer-batches'),
    };
}

function buildQueue(options = {}) {
    const root = options.root || ROOT;
    const paths = outputPaths(root);
    const audit = new Map(readJsonl(paths.typeAudit).map((row) => [row.canonical_id, row]));
    const rows = loadCanonicalQuestions({ filePath: path.join(root, 'data', 'questions', 'canonical_questions.jsonl') }).map((canonical) => {
        const answer = readAnswerFile(answerPath(canonical.canonical_id, { answersDir: paths.answers }));
        const type = audit.get(canonical.canonical_id);
        const riskFlags = [...(type?.risk_flags || [])];
        if (answer.metadata.quality_tier === 'long_tail_baseline') riskFlags.push('long_tail_baseline');
        if (answer.metadata.quality_tier === 'curated_audit_failed') riskFlags.push('historical_curated_audit_failed');
        if (/ProblemSpec|source_table|solveDp/.test(answer.content)) riskFlags.push('placeholder_implementation');
        return {
            schema_version: 'answer_rewrite_queue.v1',
            batch_id: null,
            canonical_id: canonical.canonical_id,
            canonical_title: canonical.canonical_title,
            answer_type: type?.answer_type || 'concept',
            secondary_requirements: type?.secondary_requirements || [],
            primary_domain: canonical.primary_domain,
            review_priority: canonical.review_priority,
            frequency: canonical.frequency,
            risk_flags: [...new Set(riskFlags)].sort(),
            dependencies: [],
            status: 'queued',
            task_file: null,
        };
    }).sort((a, b) =>
        Number(b.risk_flags.includes('historical_curated_audit_failed')) - Number(a.risk_flags.includes('historical_curated_audit_failed'))
        || Number(b.risk_flags.includes('placeholder_implementation')) - Number(a.risk_flags.includes('placeholder_implementation'))
        || ({ P0: 0, P1: 1, P2: 2, P3: 3 }[a.review_priority] ?? 9) - ({ P0: 0, P1: 1, P2: 2, P3: 3 }[b.review_priority] ?? 9)
        || TYPE_ORDER[a.answer_type] - TYPE_ORDER[b.answer_type]
        || b.frequency - a.frequency
        || a.canonical_id.localeCompare(b.canonical_id)
    );
    const batches = [];
    rows.forEach((row, index) => {
        const number = Math.floor(index / 10) + 1;
        const batchId = `TASK-20260711-0313-answer-batch-${String(number).padStart(4, '0')}`;
        const taskFile = path.join('tasks', 'answer-batches', `${batchId}.md`);
        row.batch_id = batchId; row.task_file = taskFile;
        if (!batches[number - 1]) batches[number - 1] = { batch_id: batchId, task_file: taskFile, canonical_ids: [] };
        batches[number - 1].canonical_ids.push(row.canonical_id);
    });
    return { rows, batches };
}

function taskContent(batch, rows) {
    const items = rows.filter((row) => row.batch_id === batch.batch_id);
    return [
        `# ${batch.batch_id}`,
        '', '- Status: `pending`', '- Root task: `TASK-20260711-0313-long-tail-answer-quality`', `- Canonical count: \`${items.length}\``,
        '- Required workflow: boundary check → primary-source research → candidate → isolated review → evidence/code gate → human approval (pilot) → atomic promotion.',
        '', '## Canonicals', '',
        ...items.map((row) => `- \`${row.canonical_id}\` — ${row.answer_type}; risks: ${row.risk_flags.join(', ') || 'none'}`),
        '', '## Completion', '',
        '- [ ] Every candidate passes `answer audit --require-evidence`.',
        '- [ ] Every promotion has an independent reviewer and required human approval.',
        '- [ ] `answer validate --strict`, `canonical check`, and applicable code tests pass.',
        '',
    ].join('\n');
}

function run(options = {}) {
    const root = options.root || ROOT;
    const paths = outputPaths(root);
    const { rows, batches } = buildQueue({ root });
    const queueText = `${rows.map(stableStringify).join('\n')}\n`;
    const batchValue = { schema_version: 'answer_rewrite_batches.v1', batch_size: 10, batch_count: batches.length, batches };
    const expectedTasks = new Map(batches.map((batch) => [path.join(root, batch.task_file), taskContent(batch, rows)]));
    const currentQueue = fs.existsSync(paths.queue) ? fs.readFileSync(paths.queue, 'utf8') : '';
    const currentBatches = fs.existsSync(paths.batches) ? fs.readFileSync(paths.batches, 'utf8') : '';
    const checkOk = currentQueue === queueText && currentBatches === stablePrettyStringify(batchValue)
        && [...expectedTasks.entries()].every(([filePath, content]) => fs.existsSync(filePath) && fs.readFileSync(filePath, 'utf8') === content);
    if (!options.noWrite && !options.check) {
        writeJsonl(paths.queue, rows); writeJson(paths.batches, batchValue);
        for (const [filePath, content] of expectedTasks) { ensureDir(path.dirname(filePath)); fs.writeFileSync(filePath, content, 'utf8'); }
    }
    return { schema_version: 'answer_rewrite_queue_report.v1', ok: !options.check || checkOk, check: Boolean(options.check), queued_count: rows.length, batch_count: batches.length, batch_size: 10, type_counts: Object.fromEntries(Object.keys(TYPE_ORDER).map((type) => [type, rows.filter((row) => row.answer_type === type).length])), output: path.relative(root, paths.queue) };
}

function main(argv = process.argv) {
    const options = { check: argv.includes('--check'), noWrite: argv.includes('--noWrite') };
    const rootIndex = argv.indexOf('--root'); if (rootIndex >= 0) options.root = path.resolve(argv[rootIndex + 1]);
    const result = run(options); console.log(JSON.stringify(result, null, 2)); return result.ok ? 0 : 1;
}

if (require.main === module) process.exitCode = main();
module.exports = { buildQueue, run, main };
