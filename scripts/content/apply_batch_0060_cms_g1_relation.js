'use strict';

const fs = require('fs');
const path = require('path');

const ROOT = process.cwd();
const { createApplication } = require(path.join(ROOT, 'src/bootstrap/create-application'));

const TARGET_CID = 'cq_q_d3fea003c007b50735b8e695473de9ac';
const TARGET_BRIDGE_QID = 'd3fea003c007b50735b8e695473de9ac';
const SOURCE_CID = 'cq_q_7960226d99224c6c8d4411110ff10c8b';
const SOURCE_QIDS = [
    '7960226d99224c6c8d4411110ff10c8b',
    '82f00b764cb3e39680f5e559f2a2db67',
    'fc4d287ddc9fb55fb09c4d1acc68398e',
];
const TARGET_TITLE = 'CMS 与 G1 垃圾收集器的区别及场景选择';
const OUT = path.join(ROOT, 'review/content_build/answer_batch_0060');
const APPLY_OUT = path.join(OUT, 'cms_g1_relation_apply');

function readJsonl(relativePath) {
    return fs.readFileSync(path.join(ROOT, relativePath), 'utf8')
        .split(/\r?\n/)
        .filter(Boolean)
        .map(JSON.parse);
}

function sorted(values) {
    return [...values].sort((left, right) => String(left).localeCompare(String(right)));
}

function assertExactIds(actual, expected, label) {
    if (JSON.stringify(sorted(actual || [])) !== JSON.stringify(sorted(expected || []))) {
        throw new Error(`${label} drifted: ${JSON.stringify(actual)}`);
    }
}

function verifyPrimaryRepositorySources(context, byQuestion) {
    if (!context || context.answer_type !== 'mechanism') {
        throw new Error(`${context?.canonical?.canonical_id || 'unknown'}: expected Mechanism frozen context`);
    }
    const canonicalId = context.canonical?.canonical_id;
    for (const source of context.source_questions || []) {
        const row = byQuestion.get(source.question_id);
        if (!row || row.canonical_id !== canonicalId || row.is_valid_for_library !== true) {
            throw new Error(`${source.question_id}: current Question ownership/validity drifted`);
        }
        if (row.original_question !== source.original_question) {
            throw new Error(`${source.question_id}: frozen wording drifted`);
        }
        const notePath = path.join(ROOT, 'note_tagged', `${row.source_note_id}.json`);
        if (!fs.existsSync(notePath)) {
            throw new Error(`${source.question_id}: primary repository note missing`);
        }
        const note = JSON.parse(fs.readFileSync(notePath, 'utf8'));
        const found = (note.tagged_questions || []).some((question) => (
            question.question_id === row.question_id
            && question.original_question === row.original_question
            && question.is_valid_for_library === true
        ));
        if (!found) {
            throw new Error(`${source.question_id}: primary repository source wording drifted`);
        }
    }
}

function assertNoAnswerArtifacts(canonicalId) {
    const candidate = path.join(ROOT, 'review/candidates/answers', `${canonicalId}.md`);
    const evidence = path.join(ROOT, 'review/evidence', `${canonicalId}.json`);
    if (fs.existsSync(candidate) || fs.existsSync(evidence)) {
        throw new Error(`${canonicalId}: relation normalization must happen before candidate/evidence creation`);
    }
}

async function reviewPair(application, sourceQuestionId, label) {
    const suggestion = await application.dedup.suggest({
        mode: 'pair',
        question_ids: [TARGET_BRIDGE_QID, sourceQuestionId],
    });
    if (!Array.isArray(suggestion.relation_candidates) || suggestion.relation_candidates.length !== 1) {
        throw new Error(`${label}: expected exactly one RelationCandidate`);
    }
    const candidate = suggestion.relation_candidates[0];
    assertExactIds(candidate.question_ids, [TARGET_BRIDGE_QID, sourceQuestionId], `${label} candidate Question scope`);
    fs.writeFileSync(path.join(APPLY_OUT, `suggest-${label}.json`), `${JSON.stringify(suggestion, null, 2)}\n`);

    const decision = await application.dedup.recordDecision({
        relation_candidate_key: candidate.relation_candidate_key,
        relation: 'same',
        actor: {
            type: 'ai',
            id: 'batch-0060-cms-g1-source-first-relation-review',
            display_name: 'Batch 0060 CMS/G1 source-first relation reviewer',
        },
        rationale: 'Both frozen current repository sources ask for the same CMS-versus-G1 collector comparison. The target packet additionally preserves one scenario-selection follow-up, which is a deeper variant of the same comparison rather than a different answer contract.',
    });
    fs.writeFileSync(path.join(APPLY_OUT, `decide-${label}.json`), `${JSON.stringify(decision, null, 2)}\n`);

    const prepared = await application.dedup.prepareApply({
        relation_candidate_key: candidate.relation_candidate_key,
        canonical_id: TARGET_CID,
        canonical_title: TARGET_TITLE,
    });
    if (prepared.relation !== 'same' || prepared.intent?.intent_state !== 'ready') {
        throw new Error(`${label}: explicit same decision is not ready for apply`);
    }
    assertExactIds(prepared.intent?.question_ids, [TARGET_BRIDGE_QID, sourceQuestionId], `${label} prepared Question scope`);
    if (prepared.intent?.canonical_target?.canonical_id !== TARGET_CID) {
        throw new Error(`${label}: prepared target Canonical drifted`);
    }
    fs.writeFileSync(path.join(APPLY_OUT, `prepare-${label}.json`), `${JSON.stringify(prepared, null, 2)}\n`);
    return candidate.relation_candidate_key;
}

async function main() {
    fs.mkdirSync(APPLY_OUT, { recursive: true });

    const questions = readJsonl('data/questions/questions.jsonl');
    const canonicals = readJsonl('data/questions/canonical_questions.jsonl');
    const byQuestion = new Map(questions.map((question) => [question.question_id, question]));
    const byCanonical = new Map(canonicals.map((canonical) => [canonical.canonical_id, canonical]));
    const target = byCanonical.get(TARGET_CID);
    const source = byCanonical.get(SOURCE_CID);
    if (!target || !source) throw new Error('both CMS/G1 Canonicals must exist before relation review');
    if (!(target.question_ids || []).includes(TARGET_BRIDGE_QID)) throw new Error('target bridge Question ownership drifted');
    assertExactIds(source.question_ids, SOURCE_QIDS, 'source Canonical Question scope');
    assertNoAnswerArtifacts(TARGET_CID);
    assertNoAnswerArtifacts(SOURCE_CID);

    const targetContextPath = path.join(OUT, TARGET_CID, 'context.json');
    const sourceContextPath = path.join(OUT, SOURCE_CID, 'context.json');
    const targetContext = JSON.parse(fs.readFileSync(targetContextPath, 'utf8'));
    const sourceContext = JSON.parse(fs.readFileSync(sourceContextPath, 'utf8'));
    verifyPrimaryRepositorySources(targetContext, byQuestion);
    verifyPrimaryRepositorySources(sourceContext, byQuestion);
    assertExactIds(targetContext.canonical?.question_ids, target.question_ids, 'target frozen context ownership');
    assertExactIds(sourceContext.canonical?.question_ids, SOURCE_QIDS, 'source frozen context ownership');

    fs.writeFileSync(path.join(APPLY_OUT, 'premerge-target-context.json'), `${JSON.stringify(targetContext, null, 2)}\n`);
    fs.writeFileSync(path.join(APPLY_OUT, 'premerge-source-context.json'), `${JSON.stringify(sourceContext, null, 2)}\n`);

    const targetTexts = (targetContext.source_questions || []).map((question) => question.original_question);
    const sourceTexts = (sourceContext.source_questions || []).map((question) => question.original_question);
    const review = [
        '# Batch 0060 CMS/G1 Source-First Relation Review',
        '',
        '## Primary-source facts',
        '',
        `- Target-side repository sources preserve CMS/G1 comparison wording, including one explicit selection variant: ${targetTexts.map((text) => `“${text}”`).join('；')}。`,
        `- Source-side repository sources preserve CMS/G1 comparison wording: ${sourceTexts.map((text) => `“${text}”`).join('；')}。`,
        '- Across all six frozen source Questions, the compared collectors are the same CMS and G1 pair. No source preserves a distinct collector pair, a CMS-only execution-flow contract, a G1-only mechanism contract, or a separate quantitative benchmark contract.',
        '- The target-side “how to choose by scenario” wording deepens the same comparison by asking for decision criteria; it does not require an independent Canonical because a complete comparison answer should already cover trade-offs and applicability boundaries.',
        '',
        'No historical relation/remediation record was consulted before this conclusion.',
        '',
        '## Decision',
        '',
        `Relation: \`same\`. Consolidate \`${SOURCE_CID}\` into survivor \`${TARGET_CID}\`, retain every valid source Question, and use the survivor title “${TARGET_TITLE}” so the deepest preserved source intent remains visible.`,
        '',
        '## Application safety',
        '',
        `The source Canonical owns exactly ${SOURCE_QIDS.length} Questions. The Dedup pair contract reviews each source Question independently against target bridge Question \`${TARGET_BRIDGE_QID}\`. Every explicit same Decision is re-prepared against current revisions immediately before one guarded Canonical merge. The merge fails closed if the source Question scope or reviewed target bridge ownership drifts.`,
        '',
        '## Content consequence',
        '',
        'Do not write two duplicate CMS/G1 answers. Regenerate Batch 0060 source inventory after consolidation; the surviving Mechanism answer must cover collector architecture, phases/concurrency, fragmentation/compaction, pause goals, remembered-set/region behavior, failure/fallback boundaries, version/deprecation boundaries, and scenario-selection trade-offs.',
        '',
    ].join('\n');
    fs.writeFileSync(path.join(OUT, 'cms_g1_relation_review.md'), review);

    const application = createApplication({ root: ROOT });
    const relationKeys = [];
    for (let i = 0; i < SOURCE_QIDS.length; i += 1) {
        relationKeys.push(await reviewPair(application, SOURCE_QIDS[i], `source-${i + 1}`));
    }

    const merged = await application.canonical.merge({
        target: TARGET_CID,
        source: SOURCE_CID,
        reason: `Three explicit source-first same RelationDecisions ${relationKeys.join(', ')} cover every Question owned by ${SOURCE_CID}`,
        expected_source_question_ids: SOURCE_QIDS,
        expected_target_reviewed_question_ids: [TARGET_BRIDGE_QID],
    });
    if (merged.ok !== true) throw new Error('guarded CMS/G1 Canonical merge did not pass integrity');
    fs.writeFileSync(path.join(APPLY_OUT, 'apply.json'), `${JSON.stringify({
        schema_version: 'batch_0060_cms_g1_relation_application.v1',
        relation: 'same',
        relation_candidate_keys: relationKeys,
        source_question_ids: SOURCE_QIDS,
        target_reviewed_question_ids: [TARGET_BRIDGE_QID],
        merge: merged,
    }, null, 2)}\n`);

    const postQuestions = readJsonl('data/questions/questions.jsonl');
    const postCanonicals = readJsonl('data/questions/canonical_questions.jsonl');
    const postByQuestion = new Map(postQuestions.map((question) => [question.question_id, question]));
    const postByCanonical = new Map(postCanonicals.map((canonical) => [canonical.canonical_id, canonical]));
    if (postByCanonical.has(SOURCE_CID)) throw new Error('duplicate CMS/G1 Canonical survived consolidation');
    const survivor = postByCanonical.get(TARGET_CID);
    if (!survivor) throw new Error('CMS/G1 survivor missing after consolidation');
    const expectedSurvivorQuestionIds = sorted([...(target.question_ids || []), ...SOURCE_QIDS]);
    assertExactIds(survivor.question_ids, expectedSurvivorQuestionIds, 'survivor Question scope');
    for (const questionId of expectedSurvivorQuestionIds) {
        if (postByQuestion.get(questionId)?.canonical_id !== TARGET_CID) {
            throw new Error(`${questionId}: survivor ownership missing after consolidation`);
        }
    }

    if (fs.existsSync(path.join(OUT, SOURCE_CID))) fs.rmSync(path.join(OUT, SOURCE_CID), { recursive: true, force: true });

    fs.writeFileSync(path.join(OUT, 'cms_g1_relation_apply.md'), [
        '# Batch 0060 CMS/G1 Relation Application',
        '',
        '- Relation: `same`.',
        `- Survivor: \`${TARGET_CID}\`; all six reviewed CMS/G1 source Questions now belong to it.`,
        `- Retired duplicate Canonical: \`${SOURCE_CID}\`.`,
        '- Each of the three duplicate-side Questions was reviewed through an explicit pair RelationDecision and re-prepared immediately before the guarded merge.',
        '- No Answer or evidence existed for either Canonical before normalization; no Answer was promoted by this operation.',
        '- Batch 0060 source inventory must be regenerated immediately after this normalization.',
        '',
    ].join('\n'));

    const taskPath = path.join(ROOT, 'tasks/answer-batches/TASK-20260711-0313-answer-batch-0060.md');
    let task = fs.readFileSync(taskPath, 'utf8')
        .split(/\r?\n/)
        .filter((line) => !line.startsWith('- [x] Batch 0060 scheduling reconciled against the current Question/Canonical/type SSOT'))
        .join('\n')
        .trimEnd();
    const note = `- [x] CMS/G1 duplicate normalization completed source-first: \`${SOURCE_CID}\` and \`${TARGET_CID}\` preserve the same collector-comparison contract; the target-side scenario-choice wording is a deeper variant of that same comparison. All three source-side Questions were explicitly reviewed against the target bridge, then merged under exact source-scope guards into survivor \`${TARGET_CID}\`. No Answer/evidence existed on either Canonical before consolidation. Batch source inventory is regenerated after this merge before any CMS/G1 candidate is written.`;
    task = `${task}\n${note}\n`;
    fs.writeFileSync(taskPath, task);

    console.log(`PASS relation=same survivor=${TARGET_CID} retired=${SOURCE_CID} merged_questions=${SOURCE_QIDS.length} decisions=${relationKeys.join(',')}`);
}

main().catch((error) => {
    console.error(error.stack || error.message);
    process.exitCode = 1;
});
