'use strict';

const fs = require('fs');
const path = require('path');

const ROOT = process.cwd();
const { createApplication } = require(path.join(ROOT, 'src/bootstrap/create-application'));

const TARGET_QID = '68a77b01c3a999732bc21dc888503621';
const TARGET_CID = 'cq_q_68a77b01c3a999732bc21dc888503621';
const DUP_QIDS = [
    '3590292944e8b631aa2e0cf561c565e5',
    '8eab176c51a37f667765b1624f8aca4d',
];
const DUP_CID = 'cq_q_3590292944e8b631aa2e0cf561c565e5';
const TARGET_TITLE = '算法：二叉树的层序遍历（Level Order Traversal / LeetCode 102）';
const OUT = path.join(ROOT, 'review/content_build/answer_batch_0058');
const APPLY_OUT = path.join(OUT, 'level_order_relation_apply');

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
    if (!context || context.answer_type !== 'coding') {
        throw new Error(`${context?.canonical?.canonical_id || 'unknown'}: expected Coding frozen context`);
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

async function reviewPair(application, duplicateQuestionId, label) {
    const suggestion = await application.dedup.suggest({
        mode: 'pair',
        question_ids: [TARGET_QID, duplicateQuestionId],
    });
    if (!Array.isArray(suggestion.relation_candidates) || suggestion.relation_candidates.length !== 1) {
        throw new Error(`${label}: expected exactly one RelationCandidate`);
    }
    const candidate = suggestion.relation_candidates[0];
    assertExactIds(candidate.question_ids, [TARGET_QID, duplicateQuestionId], `${label} candidate Question scope`);
    fs.writeFileSync(
        path.join(APPLY_OUT, `suggest-${label}.json`),
        `${JSON.stringify(suggestion, null, 2)}\n`,
    );

    const decision = await application.dedup.recordDecision({
        relation_candidate_key: candidate.relation_candidate_key,
        relation: 'same',
        actor: {
            type: 'ai',
            id: 'batch-0058-level-order-source-first-review',
            display_name: 'Level-order source-first reviewer',
        },
        rationale: 'The frozen current repository sources on both Canonicals ask for ordinary tree/binary-tree breadth-first level-order traversal. LeetCode 102 names the standard binary-tree instance; no source preserves a distinct traversal order, tree-kind-only contract, or output semantic.',
    });
    fs.writeFileSync(
        path.join(APPLY_OUT, `decide-${label}.json`),
        `${JSON.stringify(decision, null, 2)}\n`,
    );

    const prepared = await application.dedup.prepareApply({
        relation_candidate_key: candidate.relation_candidate_key,
        canonical_id: TARGET_CID,
        canonical_title: TARGET_TITLE,
    });
    if (prepared.relation !== 'same' || prepared.intent?.intent_state !== 'ready') {
        throw new Error(`${label}: explicit same decision is not ready for apply`);
    }
    assertExactIds(prepared.intent?.question_ids, [TARGET_QID, duplicateQuestionId], `${label} prepared Question scope`);
    if (prepared.intent?.canonical_target?.canonical_id !== TARGET_CID) {
        throw new Error(`${label}: prepared target Canonical drifted`);
    }
    fs.writeFileSync(
        path.join(APPLY_OUT, `prepare-${label}.json`),
        `${JSON.stringify(prepared, null, 2)}\n`,
    );

    return {
        relation_candidate_key: candidate.relation_candidate_key,
        prepared,
    };
}

async function main() {
    fs.mkdirSync(APPLY_OUT, { recursive: true });

    const questions = readJsonl('data/questions/questions.jsonl');
    const canonicals = readJsonl('data/questions/canonical_questions.jsonl');
    const byQuestion = new Map(questions.map((question) => [question.question_id, question]));
    const byCanonical = new Map(canonicals.map((canonical) => [canonical.canonical_id, canonical]));
    const target = byCanonical.get(TARGET_CID);
    const duplicate = byCanonical.get(DUP_CID);
    if (!target || !duplicate) {
        throw new Error('both level-order Canonicals must exist before bounded relation review');
    }
    if (!(target.question_ids || []).includes(TARGET_QID)) {
        throw new Error('target bridge Question ownership drifted');
    }
    assertExactIds(duplicate.question_ids, DUP_QIDS, 'duplicate Canonical source scope');

    const targetContext = JSON.parse(fs.readFileSync(path.join(OUT, TARGET_CID, 'context.json'), 'utf8'));
    const duplicateContext = JSON.parse(fs.readFileSync(path.join(OUT, DUP_CID, 'context.json'), 'utf8'));
    verifyPrimaryRepositorySources(targetContext, byQuestion);
    verifyPrimaryRepositorySources(duplicateContext, byQuestion);
    assertExactIds(targetContext.canonical?.question_ids, target.question_ids, 'target frozen context ownership');
    assertExactIds(duplicateContext.canonical?.question_ids, DUP_QIDS, 'duplicate frozen context ownership');

    const targetTexts = (targetContext.source_questions || []).map((question) => question.original_question);
    const duplicateTexts = (duplicateContext.source_questions || []).map((question) => question.original_question);
    const review = [
        '# Batch 0058 Level-Order Traversal Source-First Relation Review',
        '',
        '## Primary-source facts',
        '',
        `- Survivor-side repository sources preserve binary-tree level-order traversal / LeetCode 102 wording: ${targetTexts.map((text) => `“${text}”`).join('；')}。`,
        `- Duplicate-side repository sources preserve generic tree level-order traversal wording: ${duplicateTexts.map((text) => `“${text}”`).join('；')}。`,
        '- Across both frozen source packets, no source preserves a distinct contract such as N-ary-only traversal, zigzag order, bottom-up order, DFS output, or a different return shape. Both are Coding prompts for ordinary breadth-first level-order traversal.',
        '',
        'No historical relation/remediation record was consulted before this conclusion.',
        '',
        '## Decision',
        '',
        `Relation: \`same\`. Consolidate \`${DUP_CID}\` into survivor \`${TARGET_CID}\`; preserve every valid source Question from both packets under the survivor. LeetCode 102 is a named instance of the same ordinary binary-tree level-order traversal contract represented by the generic wording.`,
        '',
        '## Application safety',
        '',
        'The source Canonical owns two Questions, while the Dedup pair contract intentionally reviews exactly two Questions per RelationDecision. Both duplicate-side Questions are therefore reviewed independently against the target bridge Question. Each explicit Decision is re-prepared against current source revisions immediately before one guarded Canonical merge. The merge requires the source Canonical to contain exactly those two reviewed Questions and the target to still own the reviewed target Question.',
        '',
        '## Content consequence',
        '',
        'Do not write two independent answers for the same operation. After normalization, Batch 0058 source inventory must be regenerated against current ownership before candidate writing. This relation review does not promote any Answer.',
        '',
    ].join('\n');
    fs.writeFileSync(path.join(OUT, 'level_order_relation_review.md'), review);

    const application = createApplication({ root: ROOT });
    const primary = await reviewPair(application, DUP_QIDS[0], 'primary');
    const secondary = await reviewPair(application, DUP_QIDS[1], 'secondary');

    const merged = await application.canonical.merge({
        target: TARGET_CID,
        source: DUP_CID,
        reason: `Two explicit source-first same RelationDecisions ${primary.relation_candidate_key} and ${secondary.relation_candidate_key} cover every Question owned by ${DUP_CID}`,
        expected_source_question_ids: DUP_QIDS,
        expected_target_reviewed_question_ids: [TARGET_QID],
    });
    if (merged.ok !== true) {
        throw new Error('guarded level-order Canonical merge did not pass integrity');
    }
    fs.writeFileSync(
        path.join(APPLY_OUT, 'apply.json'),
        `${JSON.stringify({
            schema_version: 'batch_0058_level_order_relation_application.v1',
            relation: 'same',
            relation_candidate_keys: [primary.relation_candidate_key, secondary.relation_candidate_key],
            source_question_ids: DUP_QIDS,
            target_reviewed_question_ids: [TARGET_QID],
            merge: merged,
        }, null, 2)}\n`,
    );

    const postQuestions = readJsonl('data/questions/questions.jsonl');
    const postCanonicals = readJsonl('data/questions/canonical_questions.jsonl');
    const postByQuestion = new Map(postQuestions.map((question) => [question.question_id, question]));
    const postByCanonical = new Map(postCanonicals.map((canonical) => [canonical.canonical_id, canonical]));
    if (postByCanonical.has(DUP_CID)) {
        throw new Error('duplicate level-order Canonical survived consolidation');
    }
    const survivor = postByCanonical.get(TARGET_CID);
    if (!survivor) throw new Error('level-order survivor missing after consolidation');
    const expectedSurvivorQuestionIds = sorted([
        ...(target.question_ids || []),
        ...DUP_QIDS,
    ]);
    assertExactIds(survivor.question_ids, expectedSurvivorQuestionIds, 'survivor Question scope');
    for (const questionId of expectedSurvivorQuestionIds) {
        if (postByQuestion.get(questionId)?.canonical_id !== TARGET_CID) {
            throw new Error(`${questionId}: survivor ownership missing after consolidation`);
        }
    }

    fs.writeFileSync(
        path.join(OUT, 'level_order_relation_apply.md'),
        [
            '# Batch 0058 Level-Order Relation Application',
            '',
            '- Relation: `same`.',
            `- Survivor: \`${TARGET_CID}\`; it now owns all reviewed level-order source Questions.`,
            `- Retired duplicate Canonical: \`${DUP_CID}\`.`,
            '- Both duplicate-side Questions were explicitly reviewed in separate pair decisions and revalidated immediately before the guarded merge.',
            '- The merge was fail-closed on the exact source Canonical Question set and the reviewed target bridge Question.',
            '- No Answer was promoted by this normalization.',
            '',
        ].join('\n'),
    );

    const taskPath = path.join(ROOT, 'tasks/answer-batches/TASK-20260711-0313-answer-batch-0058.md');
    let task = fs.readFileSync(taskPath, 'utf8');
    const note = '- [x] `cq_q_3590292944e8b631aa2e0cf561c565e5` was reviewed source-first against `cq_q_68a77b01c3a999732bc21dc888503621`: current repository sources on both sides preserve the same ordinary tree/binary-tree breadth-first level-order traversal operation, with LeetCode 102 only naming the standard binary-tree instance. Relation is `same`; both duplicate-side source Questions were explicitly reviewed through separate pair RelationDecisions, re-prepared against fresh source revisions, and merged under an exact source-scope guard. All valid source Questions are consolidated under the survivor and the duplicate Canonical is retired. Candidate writing must target only the survivor.';
    if (!task.includes(note)) task = `${task.trimEnd()}\n${note}\n`;
    fs.writeFileSync(taskPath, task);

    console.log(`PASS relation=same survivor=${TARGET_CID} retired=${DUP_CID} source_questions=${DUP_QIDS.length} decisions=${primary.relation_candidate_key},${secondary.relation_candidate_key}`);
}

main().catch((error) => {
    console.error(error.stack || error.message);
    process.exitCode = 1;
});
