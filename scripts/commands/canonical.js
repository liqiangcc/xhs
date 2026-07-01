#!/usr/bin/env node
'use strict';

const path = require('path');
const { normalizeQuestion } = require('../lib/hash');
const { readJson, writeJson } = require('../lib/io');
const {
    loadQuestions,
    saveQuestions,
    questionRef,
    refKey,
} = require('../lib/question_store');
const { loadIndexes, buildIndexes, writeIndexes } = require('../lib/index_store');
const { normalizeEntity, validateDomain } = require('../lib/taxonomy');
const { writeRunManifest } = require('../lib/run_manifest');
const { applyGlobalBooleanOption, shouldWriteReports } = require('../lib/cli_options');
const { defaultDate } = require('../lib/date');
const {
    loadCanonicalQuestions,
    saveCanonicalQuestions,
    suggestCanonicalId,
    makeCanonicalRecord,
    mergeCanonicalRecord,
    shortHash,
} = require('../lib/canonical_store');

const DEFAULT_ROOT = path.resolve(__dirname, '..', '..');

function defaultPaths(root) {
    return {
        questions: path.join(root, 'data', 'questions', 'questions.jsonl'),
        canonicalQuestions: path.join(root, 'data', 'questions', 'canonical_questions.jsonl'),
        indexDir: path.join(root, 'data', 'indexes'),
        candidateManifest: path.join(root, 'data', 'manifests', 'canonical', 'canonical_candidates.json'),
        qualityReport: path.join(root, 'data', 'manifests', 'canonical', 'canonical_quality_report.json'),
    };
}

function parseArgs(argv) {
    const args = argv.slice(2);
    const command = args[0];
    const options = { _: [] };
    const booleanFlags = new Set(['hotspot', 'valid']);
    for (let index = 1; index < args.length; index++) {
        const arg = args[index];
        if (!arg) continue;
        if (arg.startsWith('--')) {
            const key = arg.replace(/^--/, '');
            if (applyGlobalBooleanOption(options, key)) continue;
            if (booleanFlags.has(key)) options[key] = true;
            else options[key] = args[++index];
        } else {
            options._.push(arg);
        }
    }
    return { command, options };
}

function printHelp() {
    console.log([
        'Usage: node scripts/xhs.js canonical <suggest|accept|stats> [options]',
        '',
        'Commands:',
        '  suggest --entity <value> [--limit <n>]',
        '  suggest --hotspot [--limit <n>]',
        '  accept --candidate-id <id> --canonical-id <cq_id>',
        '  list [--priority <P0|P1|P2|P3>] [--answer-status <status>] [--limit <n>]',
        '  check',
        '  merge --target <canonical_id> --source <canonical_id> --reason <text>',
        '  split --canonical-id <id> --question-id <qid> --new-canonical-id <id> --title <title>',
        '  stats',
        '',
        'Options:',
        '  --noWrite     Do not write reports or run manifests for read-only commands',
        '  --noManifest  Do not write the run manifest',
    ].join('\n'));
}

function assertCanonicalId(canonicalId) {
    if (!/^cq_[a-z0-9_]+$/.test(canonicalId || '')) {
        throw new Error(`Invalid canonical_id: ${canonicalId}`);
    }
}

function priorityRank(priority) {
    return { P0: 0, P1: 1, P2: 2, P3: 3 }[priority] ?? 9;
}

function pickPriority(...priorities) {
    return priorities
        .filter(Boolean)
        .sort((a, b) => priorityRank(a) - priorityRank(b))[0] || 'P2';
}

function computePriority(frequency, companiesLength) {
    if (frequency >= 5 || companiesLength >= 4) return 'P0';
    if (frequency >= 3) return 'P1';
    return 'P2';
}

function buildQuestionMap(questions) {
    const map = new Map();
    for (const question of questions) map.set(refKey(questionRef(question)), question);
    return map;
}

function rowsFromRefs(refs, questionMap) {
    const rows = [];
    const seen = new Set();
    for (const ref of refs || []) {
        const key = refKey(ref);
        if (seen.has(key)) continue;
        seen.add(key);
        const question = questionMap.get(key);
        if (question) rows.push(question);
    }
    return rows;
}

function normalizedDomain(question) {
    const result = validateDomain(question.domain || {});
    return result.valid ? result.normalized_domain : (question.domain || { l1: '其他', l2: '其他' });
}

function domainKey(question) {
    const domain = normalizedDomain(question);
    return `${domain.l1}/${domain.l2}`;
}

function tokenizeQuestion(text) {
    const normalized = normalizeQuestion(text);
    const tokens = new Set();
    for (const word of normalized.match(/[a-z0-9_]+/g) || []) {
        if (word.length >= 2) tokens.add(word);
    }
    const chinese = normalized.match(/[\u4e00-\u9fa5]+/g) || [];
    for (const chunk of chinese) {
        if (chunk.length === 1) tokens.add(chunk);
        for (let index = 0; index < chunk.length - 1; index++) {
            tokens.add(chunk.slice(index, index + 2));
        }
    }
    return tokens;
}

function jaccard(a, b) {
    if (!a.size || !b.size) return 0;
    let intersection = 0;
    for (const item of a) if (b.has(item)) intersection++;
    return intersection / (a.size + b.size - intersection);
}

function sortedQuestions(questions) {
    return [...questions].sort((a, b) =>
        a.question_id.localeCompare(b.question_id)
        || a.source_note_id.localeCompare(b.source_note_id, 'zh')
        || (a.source_question_index ?? 0) - (b.source_question_index ?? 0)
    );
}

function countValues(values) {
    const counts = new Map();
    for (const value of values) counts.set(value, (counts.get(value) || 0) + 1);
    return counts;
}

function pickTop(values, fallback) {
    const counts = countValues(values.filter(Boolean));
    const sorted = [...counts.entries()].sort((a, b) => b[1] - a[1] || String(a[0]).localeCompare(String(b[0]), 'zh'));
    return sorted[0]?.[0] || fallback;
}

function buildCandidate(mode, seed, questions) {
    const sorted = sortedQuestions(questions);
    const questionIds = [...new Set(sorted.map((question) => question.question_id))].sort();
    const aliases = [...new Set(sorted.map((question) => question.original_question))]
        .sort((a, b) => a.length - b.length || a.localeCompare(b, 'zh'))
        .slice(0, 20);
    const companies = [...new Set(sorted.map((question) => question.company || '未知'))]
        .sort((a, b) => a.localeCompare(b, 'zh'));
    const sourceNoteIds = [...new Set(sorted.map((question) => question.source_note_id))]
        .sort((a, b) => a.localeCompare(b, 'zh'));
    const domains = sorted.map(normalizedDomain);
    const primaryDomain = JSON.parse(pickTop(
        domains.map((domain) => JSON.stringify(domain)),
        JSON.stringify({ l1: '其他', l2: '其他' })
    ));
    const entities = [];
    for (const question of sorted) {
        for (const entity of question.tech_entities || []) {
            const normalized = normalizeEntity(entity);
            if (normalized) entities.push(normalized);
        }
    }
    const primaryEntities = [...new Set(entities)]
        .sort((a, b) => (countValues(entities).get(b) || 0) - (countValues(entities).get(a) || 0) || a.localeCompare(b, 'zh'))
        .slice(0, 8);
    const canonicalTitle = aliases[0] || sorted[0]?.original_question || seed;
    const canonicalIdSuggestion = suggestCanonicalId(primaryEntities[0] || seed || canonicalTitle, questionIds);
    const frequency = sorted.length;
    return {
        candidate_id: `cand_${shortHash(`${mode}|${seed}|${questionIds.join('|')}`)}`,
        mode,
        seed,
        canonical_id_suggestion: canonicalIdSuggestion,
        canonical_title: canonicalTitle,
        aliases,
        question_ids: questionIds,
        primary_domain: primaryDomain,
        primary_entities: primaryEntities,
        companies,
        frequency,
        source_note_ids: sourceNoteIds,
        refs: sorted.map(questionRef),
        review_priority: frequency >= 5 || companies.length >= 4 ? 'P0' : (frequency >= 3 ? 'P1' : 'P2'),
    };
}

function refreshCanonicalRecord(record, questions) {
    const questionIds = new Set(record.question_ids || []);
    const rows = questions.filter((question) => questionIds.has(question.question_id));
    const companies = [...new Set(rows.map((question) => question.company || '未知'))]
        .sort((a, b) => a.localeCompare(b, 'zh'));
    const entities = [];
    for (const question of rows) {
        for (const entity of question.tech_entities || []) {
            const normalized = normalizeEntity(entity);
            if (normalized) entities.push(normalized);
        }
    }
    const primaryEntities = entities.length
        ? [...new Set(entities)].sort((a, b) =>
            (countValues(entities).get(b) || 0) - (countValues(entities).get(a) || 0)
            || a.localeCompare(b, 'zh')
        ).slice(0, 8)
        : (record.primary_entities || []);
    const domains = rows.map(normalizedDomain);
    const primaryDomain = domains.length
        ? JSON.parse(pickTop(domains.map((domain) => JSON.stringify(domain)), JSON.stringify(record.primary_domain || { l1: '其他', l2: '其他' })))
        : (record.primary_domain || { l1: '其他', l2: '其他' });
    const frequency = rows.length || Number(record.frequency || 0);
    return {
        ...record,
        aliases: [...new Set(record.aliases || [record.canonical_title].filter(Boolean))]
            .sort((a, b) => a.length - b.length || a.localeCompare(b, 'zh')),
        question_ids: [...questionIds].sort(),
        primary_domain: primaryDomain,
        primary_entities: primaryEntities,
        companies,
        frequency,
        review_priority: pickPriority(record.review_priority, computePriority(frequency, companies.length)),
        schema_version: 'canonical_question.v1',
    };
}

function persistCanonicalState(paths, questions, records) {
    const refreshed = records.map((record) => refreshCanonicalRecord(record, questions));
    saveCanonicalQuestions(refreshed, { filePath: paths.canonicalQuestions });
    saveQuestions(questions, { filePath: paths.questions });
    writeIndexes(buildIndexes(questions, { canonicalQuestions: refreshed }), paths.indexDir);
    return refreshed;
}

function groupEntityCandidates(questions, seed, limit) {
    const clusters = [];
    for (const question of sortedQuestions(questions.filter((item) => item.is_valid_for_library && !item.canonical_id))) {
        const tokens = tokenizeQuestion(question.original_question);
        const dKey = domainKey(question);
        let target = null;
        for (const cluster of clusters) {
            if (cluster.domain_key !== dKey && question.question_id !== cluster.question_ids[0]) continue;
            if (question.question_id === cluster.question_ids[0] || jaccard(tokens, cluster.tokens) >= 0.38) {
                target = cluster;
                break;
            }
        }
        if (!target) {
            target = {
                domain_key: dKey,
                tokens,
                question_ids: [question.question_id],
                questions: [],
            };
            clusters.push(target);
        }
        target.questions.push(question);
        if (!target.question_ids.includes(question.question_id)) target.question_ids.push(question.question_id);
    }
    return clusters
        .filter((cluster) => {
            const sourceCount = new Set(cluster.questions.map((question) => question.source_note_id)).size;
            return cluster.questions.length >= 2 && (cluster.question_ids.length >= 2 || sourceCount >= 2);
        })
        .map((cluster) => buildCandidate('entity', seed, cluster.questions))
        .sort((a, b) =>
            b.frequency - a.frequency
            || b.companies.length - a.companies.length
            || a.candidate_id.localeCompare(b.candidate_id)
        )
        .slice(0, limit);
}

function suggestFromEntity(options, paths) {
    const entity = options.entity || options._[0];
    if (!entity) throw new Error('Usage: canonical suggest --entity <value>');
    const limit = Number(options.limit || 50);
    const questions = loadQuestions({ filePath: paths.questions });
    const questionMap = buildQuestionMap(questions);
    const indexes = loadIndexes(paths.indexDir);
    const normalized = normalizeEntity(entity);
    const lower = String(entity).toLowerCase();
    const refs = [];
    for (const [key, bucket] of Object.entries(indexes.entity.entries || {})) {
        if (key === normalized || key.toLowerCase().includes(lower)) refs.push(...bucket.refs);
    }
    return groupEntityCandidates(rowsFromRefs(refs, questionMap), normalized || entity, limit);
}

function suggestFromHotspot(options, paths) {
    const limit = Number(options.limit || 100);
    const questions = loadQuestions({ filePath: paths.questions });
    const questionMap = buildQuestionMap(questions);
    const indexes = loadIndexes(paths.indexDir);
    return (indexes.hotspot.entries || [])
        .map((entry) => buildCandidate(
            'hotspot',
            entry.question_id,
            rowsFromRefs(entry.refs, questionMap).filter((question) => question.is_valid_for_library && !question.canonical_id),
        ))
        .filter((candidate) => candidate.frequency >= 2)
        .slice(0, limit);
}

function writeCandidateManifest(candidates, options, paths) {
    const manifest = {
        schema_version: 'canonical_candidates.v1',
        generated_at: defaultDate(options),
        mode: options.hotspot ? 'hotspot' : 'entity',
        seed: options.hotspot ? 'hotspot' : (options.entity || options._[0] || ''),
        source: {
            questions: 'data/questions/questions.jsonl',
            indexes: 'data/indexes',
        },
        candidate_count: candidates.length,
        candidates,
    };
    writeJson(paths.candidateManifest, manifest);
    return manifest;
}

function runSuggest(options = {}) {
    const root = options.root ? path.resolve(options.root) : DEFAULT_ROOT;
    const paths = defaultPaths(root);
    const candidates = options.hotspot
        ? suggestFromHotspot(options, paths)
        : suggestFromEntity(options, paths);
    return writeCandidateManifest(candidates, options, paths);
}

function runAccept(options = {}) {
    const root = options.root ? path.resolve(options.root) : DEFAULT_ROOT;
    const paths = defaultPaths(root);
    const candidateId = options['candidate-id'];
    const canonicalId = options['canonical-id'];
    if (!candidateId || !canonicalId) {
        throw new Error('Usage: canonical accept --candidate-id <id> --canonical-id <cq_id>');
    }
    assertCanonicalId(canonicalId);
    const manifest = readJson(paths.candidateManifest);
    const candidate = (manifest.candidates || []).find((item) => item.candidate_id === candidateId);
    if (!candidate) throw new Error(`Candidate not found: ${candidateId}`);

    const questions = loadQuestions({ filePath: paths.questions });
    const questionIds = new Set(candidate.question_ids || []);
    const conflictingQuestion = questions.find((question) =>
        questionIds.has(question.question_id)
        && question.canonical_id
        && question.canonical_id !== canonicalId
    );
    if (conflictingQuestion) {
        throw new Error(`Question ${conflictingQuestion.question_id} already belongs to ${conflictingQuestion.canonical_id}`);
    }

    const records = loadCanonicalQuestions({ filePath: paths.canonicalQuestions });
    const incoming = makeCanonicalRecord(candidate, canonicalId, { title: options.title });
    const existingIndex = records.findIndex((record) => record.canonical_id === canonicalId);
    if (existingIndex >= 0) records[existingIndex] = mergeCanonicalRecord(records[existingIndex], incoming);
    else records.push(incoming);

    for (const record of records) {
        if (record.canonical_id === canonicalId) continue;
        const overlap = (record.question_ids || []).find((questionId) => questionIds.has(questionId));
        if (overlap) throw new Error(`Question ${overlap} already belongs to ${record.canonical_id}`);
    }

    const updatedQuestions = questions.map((question) =>
        questionIds.has(question.question_id)
            ? { ...question, canonical_id: canonicalId }
            : question
    );
    const refreshed = persistCanonicalState(paths, updatedQuestions, records);

    return {
        ok: true,
        canonical_id: canonicalId,
        accepted_candidate_id: candidateId,
        question_ids: [...questionIds].sort(),
        updated_question_rows: updatedQuestions.filter((question) => question.canonical_id === canonicalId && questionIds.has(question.question_id)).length,
        canonical_count: refreshed.length,
    };
}

function runList(options = {}) {
    const root = options.root ? path.resolve(options.root) : DEFAULT_ROOT;
    const paths = defaultPaths(root);
    const limit = Number(options.limit || 50);
    const records = loadCanonicalQuestions({ filePath: paths.canonicalQuestions })
        .filter((record) => !options.priority || record.review_priority === options.priority)
        .filter((record) => !options['answer-status'] || record.answer_status === options['answer-status'])
        .sort((a, b) =>
            priorityRank(a.review_priority) - priorityRank(b.review_priority)
            || b.frequency - a.frequency
            || a.canonical_id.localeCompare(b.canonical_id)
        );
    return {
        schema_version: 'canonical_list.v1',
        total_count: records.length,
        returned_count: Math.min(records.length, limit),
        records: records.slice(0, limit).map((record) => ({
            canonical_id: record.canonical_id,
            canonical_title: record.canonical_title,
            review_priority: record.review_priority,
            answer_status: record.answer_status,
            frequency: record.frequency,
            question_ids: record.question_ids,
            companies: record.companies,
            primary_domain: record.primary_domain,
            primary_entities: record.primary_entities,
        })),
    };
}

function normalizedTitle(record) {
    return normalizeQuestion([
        record.canonical_title,
        ...(record.aliases || []),
    ].join(' '));
}

function runCheck(options = {}) {
    const root = options.root ? path.resolve(options.root) : DEFAULT_ROOT;
    const paths = defaultPaths(root);
    const records = loadCanonicalQuestions({ filePath: paths.canonicalQuestions });
    const questions = loadQuestions({ filePath: paths.questions });
    const rowsByQuestionId = new Map();
    for (const question of questions) {
        if (!rowsByQuestionId.has(question.question_id)) rowsByQuestionId.set(question.question_id, []);
        rowsByQuestionId.get(question.question_id).push(question);
    }
    const recordsById = new Map(records.map((record) => [record.canonical_id, record]));
    const canonicalByQuestionId = new Map();
    const duplicateQuestionIds = [];
    const missingQuestionIds = [];
    const bindingMismatches = [];
    const orphanBindings = [];
    const unlistedBindings = [];

    for (const record of records) {
        for (const questionId of record.question_ids || []) {
            if (!rowsByQuestionId.has(questionId)) {
                missingQuestionIds.push({ canonical_id: record.canonical_id, question_id: questionId });
            }
            const owner = canonicalByQuestionId.get(questionId);
            if (owner && owner !== record.canonical_id) {
                duplicateQuestionIds.push({ question_id: questionId, canonical_ids: [owner, record.canonical_id].sort() });
            } else {
                canonicalByQuestionId.set(questionId, record.canonical_id);
            }
            for (const question of rowsByQuestionId.get(questionId) || []) {
                if (question.canonical_id !== record.canonical_id) {
                    bindingMismatches.push({
                        question_id: question.question_id,
                        source_note_id: question.source_note_id,
                        source_question_index: question.source_question_index,
                        expected_canonical_id: record.canonical_id,
                        actual_canonical_id: question.canonical_id,
                    });
                }
            }
        }
    }

    for (const question of questions) {
        if (!question.canonical_id) continue;
        const record = recordsById.get(question.canonical_id);
        if (!record) {
            orphanBindings.push(questionRef(question));
        } else if (!(record.question_ids || []).includes(question.question_id)) {
            unlistedBindings.push({
                ...questionRef(question),
                canonical_id: question.canonical_id,
            });
        }
    }

    const suspectedDuplicates = [];
    for (let left = 0; left < records.length; left++) {
        for (let right = left + 1; right < records.length; right++) {
            const a = records[left];
            const b = records[right];
            if (normalizedTitle(a) && normalizedTitle(a) === normalizedTitle(b)) {
                suspectedDuplicates.push({
                    canonical_ids: [a.canonical_id, b.canonical_id],
                    reason: 'same_normalized_title_or_aliases',
                    titles: [a.canonical_title, b.canonical_title],
                });
            }
        }
    }

    const blockingCount = duplicateQuestionIds.length
        + missingQuestionIds.length
        + bindingMismatches.length
        + orphanBindings.length
        + unlistedBindings.length;
    const report = {
        schema_version: 'canonical_quality_report.v1',
        ok: blockingCount === 0,
        record_count: records.length,
        assigned_question_rows: questions.filter((question) => question.canonical_id).length,
        duplicate_question_id_count: duplicateQuestionIds.length,
        missing_question_id_count: missingQuestionIds.length,
        binding_mismatch_count: bindingMismatches.length,
        orphan_binding_count: orphanBindings.length,
        unlisted_binding_count: unlistedBindings.length,
        suspected_duplicate_count: suspectedDuplicates.length,
        duplicate_question_ids: duplicateQuestionIds,
        missing_question_ids: missingQuestionIds,
        binding_mismatches: bindingMismatches,
        orphan_bindings: orphanBindings,
        unlisted_bindings: unlistedBindings,
        suspected_duplicates: suspectedDuplicates,
    };
    if (shouldWriteReports(options)) {
        writeJson(paths.qualityReport, report);
    }
    return report;
}

function runMerge(options = {}) {
    const root = options.root ? path.resolve(options.root) : DEFAULT_ROOT;
    const paths = defaultPaths(root);
    const targetId = options.target;
    const sourceId = options.source;
    if (!targetId || !sourceId || !options.reason) {
        throw new Error('Usage: canonical merge --target <canonical_id> --source <canonical_id> --reason <text>');
    }
    assertCanonicalId(targetId);
    assertCanonicalId(sourceId);
    if (targetId === sourceId) throw new Error('target and source must be different');

    const questions = loadQuestions({ filePath: paths.questions });
    const records = loadCanonicalQuestions({ filePath: paths.canonicalQuestions });
    const target = records.find((record) => record.canonical_id === targetId);
    const source = records.find((record) => record.canonical_id === sourceId);
    if (!target) throw new Error(`Target canonical not found: ${targetId}`);
    if (!source) throw new Error(`Source canonical not found: ${sourceId}`);

    const merged = mergeCanonicalRecord(target, {
        ...source,
        canonical_id: targetId,
        aliases: [source.canonical_title, ...(source.aliases || [])].filter(Boolean),
        answer_status: target.answer_status !== 'missing' ? target.answer_status : source.answer_status,
    });
    merged.review_priority = pickPriority(target.review_priority, source.review_priority);
    const updatedQuestions = questions.map((question) =>
        question.canonical_id === sourceId
            ? { ...question, canonical_id: targetId }
            : question
    );
    const nextRecords = records
        .filter((record) => record.canonical_id !== sourceId)
        .map((record) => (record.canonical_id === targetId ? merged : record));
    const refreshed = persistCanonicalState(paths, updatedQuestions, nextRecords);
    const report = runCheck({ root });
    return {
        ok: report.ok,
        target: targetId,
        source: sourceId,
        reason: options.reason,
        canonical_count: refreshed.length,
        moved_question_ids: source.question_ids,
        assigned_question_rows: updatedQuestions.filter((question) => question.canonical_id === targetId).length,
    };
}

function runSplit(options = {}) {
    const root = options.root ? path.resolve(options.root) : DEFAULT_ROOT;
    const paths = defaultPaths(root);
    const canonicalId = options['canonical-id'];
    const questionId = options['question-id'];
    const newCanonicalId = options['new-canonical-id'];
    const title = options.title;
    if (!canonicalId || !questionId || !newCanonicalId || !title) {
        throw new Error('Usage: canonical split --canonical-id <id> --question-id <qid> --new-canonical-id <id> --title <title>');
    }
    assertCanonicalId(canonicalId);
    assertCanonicalId(newCanonicalId);
    if (canonicalId === newCanonicalId) throw new Error('new-canonical-id must differ from canonical-id');

    const questions = loadQuestions({ filePath: paths.questions });
    const records = loadCanonicalQuestions({ filePath: paths.canonicalQuestions });
    if (records.some((record) => record.canonical_id === newCanonicalId)) {
        throw new Error(`Canonical already exists: ${newCanonicalId}`);
    }
    const source = records.find((record) => record.canonical_id === canonicalId);
    if (!source) throw new Error(`Canonical not found: ${canonicalId}`);
    if (!(source.question_ids || []).includes(questionId)) {
        throw new Error(`Question ${questionId} is not part of ${canonicalId}`);
    }
    const sourceRows = questions.filter((question) => question.question_id === questionId);
    if (!sourceRows.length) throw new Error(`Question not found: ${questionId}`);
    const updatedQuestions = questions.map((question) =>
        question.question_id === questionId && question.canonical_id === canonicalId
            ? { ...question, canonical_id: newCanonicalId }
            : question
    );
    const remainingQuestionIds = (source.question_ids || []).filter((id) => id !== questionId);
    const newRecord = {
        canonical_id: newCanonicalId,
        canonical_title: title,
        aliases: [...new Set([title, ...sourceRows.map((question) => question.original_question)])],
        question_ids: [questionId],
        primary_domain: normalizedDomain(sourceRows[0]),
        primary_entities: [...new Set(sourceRows.flatMap((question) => question.tech_entities || []).map((entity) => normalizeEntity(entity)).filter(Boolean))],
        companies: [...new Set(sourceRows.map((question) => question.company || '未知'))].sort((a, b) => a.localeCompare(b, 'zh')),
        frequency: sourceRows.length,
        review_priority: computePriority(sourceRows.length, new Set(sourceRows.map((question) => question.company || '未知')).size),
        answer_status: 'missing',
        schema_version: 'canonical_question.v1',
    };
    const nextRecords = records
        .filter((record) => record.canonical_id !== canonicalId)
        .concat(remainingQuestionIds.length ? [{ ...source, question_ids: remainingQuestionIds }] : [])
        .concat(newRecord);
    const refreshed = persistCanonicalState(paths, updatedQuestions, nextRecords);
    const report = runCheck({ root });
    return {
        ok: report.ok,
        source: canonicalId,
        new_canonical_id: newCanonicalId,
        question_id: questionId,
        canonical_count: refreshed.length,
    };
}

function runStats(options = {}) {
    const root = options.root ? path.resolve(options.root) : DEFAULT_ROOT;
    const paths = defaultPaths(root);
    const records = loadCanonicalQuestions({ filePath: paths.canonicalQuestions });
    const questions = loadQuestions({ filePath: paths.questions });
    const canonicalQuestionIds = new Set(records.flatMap((record) => record.question_ids || []));
    return {
        schema_version: 'canonical_stats.v1',
        canonical_count: records.length,
        canonical_question_id_count: canonicalQuestionIds.size,
        assigned_question_rows: questions.filter((question) => question.canonical_id).length,
        top_canonical: [...records]
            .sort((a, b) => b.frequency - a.frequency || a.canonical_id.localeCompare(b.canonical_id))
            .slice(0, Number(options.limit || 20))
            .map((record) => ({
                canonical_id: record.canonical_id,
                canonical_title: record.canonical_title,
                frequency: record.frequency,
                companies: record.companies,
                primary_entities: record.primary_entities,
            })),
    };
}

function main(argv = process.argv) {
    const { command, options } = parseArgs(argv);
    if (!command || command === 'help' || options.help) {
        printHelp();
        return 0;
    }
    try {
        let result;
        if (command === 'suggest') result = runSuggest(options);
        else if (command === 'accept') result = runAccept(options);
        else if (command === 'list') result = runList(options);
        else if (command === 'check') result = runCheck(options);
        else if (command === 'merge') result = runMerge(options);
        else if (command === 'split') result = runSplit(options);
        else if (command === 'stats') result = runStats(options);
        else throw new Error(`Unknown canonical command: ${command}`);
        writeRunManifest(options.root ? path.resolve(options.root) : DEFAULT_ROOT, `canonical_${command}`, result, options);
        console.log(JSON.stringify(result, null, 2));
        return 0;
    } catch (error) {
        console.error(error.message);
        return 1;
    }
}

if (require.main === module) {
    process.exitCode = main(process.argv);
}

module.exports = {
    runSuggest,
    runAccept,
    runList,
    runCheck,
    runMerge,
    runSplit,
    runStats,
    groupEntityCandidates,
    buildCandidate,
    main,
};
