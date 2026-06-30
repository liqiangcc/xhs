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
const {
    loadCanonicalQuestions,
    saveCanonicalQuestions,
    suggestCanonicalId,
    makeCanonicalRecord,
    mergeCanonicalRecord,
    shortHash,
} = require('../lib/canonical_store');

const DEFAULT_ROOT = path.resolve(__dirname, '..', '..');
const DEFAULT_BUILD_DATE = process.env.XHS_BUILD_DATE || '2026-06-30';

function defaultPaths(root) {
    return {
        questions: path.join(root, 'data', 'questions', 'questions.jsonl'),
        canonicalQuestions: path.join(root, 'data', 'questions', 'canonical_questions.jsonl'),
        indexDir: path.join(root, 'data', 'indexes'),
        candidateManifest: path.join(root, 'data', 'manifests', 'canonical', 'canonical_candidates.json'),
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
        '  stats',
    ].join('\n'));
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
        generated_at: options.buildDate || DEFAULT_BUILD_DATE,
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
    if (!/^cq_[a-z0-9_]+$/.test(canonicalId)) {
        throw new Error(`Invalid canonical_id: ${canonicalId}`);
    }
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
    saveCanonicalQuestions(records, { filePath: paths.canonicalQuestions });
    saveQuestions(updatedQuestions, { filePath: paths.questions });
    writeIndexes(buildIndexes(updatedQuestions, { canonicalQuestions: records }), paths.indexDir);

    return {
        ok: true,
        canonical_id: canonicalId,
        accepted_candidate_id: candidateId,
        question_ids: [...questionIds].sort(),
        updated_question_rows: updatedQuestions.filter((question) => question.canonical_id === canonicalId && questionIds.has(question.question_id)).length,
        canonical_count: records.length,
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
        else if (command === 'stats') result = runStats(options);
        else throw new Error(`Unknown canonical command: ${command}`);
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
    runStats,
    groupEntityCandidates,
    buildCandidate,
    main,
};
