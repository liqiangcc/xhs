#!/usr/bin/env node
'use strict';

const fs = require('fs');
const path = require('path');
const { normalizeQuestion } = require('../lib/hash');
const { loadCanonicalQuestions } = require('../lib/canonical_store');
const { readJson, readJsonl, stableStringify, writeJsonl } = require('../lib/io');

const ROOT = path.resolve(__dirname, '..', '..');

function parseArgs(argv) {
    const options = { check: false };
    for (let index = 2; index < argv.length; index++) {
        const arg = argv[index];
        if (arg === '--check') options.check = true;
        else if (arg === '--root') options.root = path.resolve(argv[++index]);
        else throw new Error(`Unknown option: ${arg}`);
    }
    return options;
}

function tokens(text) {
    const value = normalizeQuestion(text || '');
    const values = new Set((value.match(/[a-z0-9_]{2,}/g) || []));
    for (const chunk of value.match(/[\u4e00-\u9fa5]+/g) || []) {
        for (let index = 0; index < chunk.length - 1; index++) values.add(chunk.slice(index, index + 2));
    }
    return values;
}

function jaccard(a, b) {
    let shared = 0;
    for (const value of a) if (b.has(value)) shared++;
    return shared ? shared / (a.size + b.size - shared) : 0;
}

function containment(sharedCount, leftSize, rightSize) {
    const smaller = Math.min(leftSize, rightSize);
    return smaller > 0 ? sharedCount / smaller : 0;
}

function featureRows(canonicals) {
    return canonicals.map((canonical) => ({
        canonical,
        normalized_title: normalizeQuestion(canonical.canonical_title),
        tokens: tokens([canonical.canonical_title, ...(canonical.aliases || [])].join(' ')),
        entities: new Set((canonical.primary_entities || []).map((value) => String(value).toLowerCase())),
        domain_key: `${canonical.primary_domain?.l1 || '其他'}/${canonical.primary_domain?.l2 || '其他'}`,
    }));
}

function addBucket(map, key, index) {
    if (!key) return;
    if (!map.has(key)) map.set(key, []);
    map.get(key).push(index);
}

function reviewedDecisions(root) {
    const manifest = readJson(path.join(root, 'data', 'manifests', 'canonical', 'boundary_review_decisions.json'), {
        schema_version: 'canonical_boundary_review_decisions.v1',
        items: [],
    });
    return new Map((manifest.items || []).map((item) => [item.candidate_id, item]));
}

function buildCandidates(options = {}) {
    const root = options.root || ROOT;
    const decisions = reviewedDecisions(root);
    const features = featureRows(loadCanonicalQuestions({ filePath: path.join(root, 'data', 'questions', 'canonical_questions.jsonl') }));
    const buckets = new Map();
    features.forEach((row, index) => {
        addBucket(buckets, `title:${row.normalized_title}`, index);
        for (const entity of row.entities) addBucket(buckets, `entity:${entity}`, index);
        for (const token of row.tokens) if (token.length >= 3) addBucket(buckets, `token:${token}`, index);
    });
    const pairs = new Set();
    for (const indexes of buckets.values()) {
        if (indexes.length < 2 || indexes.length > 80) continue;
        for (let left = 0; left < indexes.length; left++) for (let right = left + 1; right < indexes.length; right++) {
            pairs.add(`${Math.min(indexes[left], indexes[right])}:${Math.max(indexes[left], indexes[right])}`);
        }
    }
    const rows = [];
    for (const pair of pairs) {
        const [leftIndex, rightIndex] = pair.split(':').map(Number);
        const left = features[leftIndex];
        const right = features[rightIndex];
        const exactTitle = left.normalized_title === right.normalized_title;
        const titleScore = exactTitle ? 1 : jaccard(left.tokens, right.tokens);
        const sharedEntities = [...left.entities].filter((entity) => right.entities.has(entity));
        const entityScore = sharedEntities.length ? 1 : 0;
        const entityContainment = containment(sharedEntities.length, left.entities.size, right.entities.size);
        const domainScore = left.domain_key === right.domain_key ? 1 : 0;
        const score = Number((titleScore * 0.7 + entityScore * 0.2 + domainScore * 0.1).toFixed(4));
        const titleEligible = titleScore >= 0.55 && (entityScore || domainScore);
        const containedVariantEligible = domainScore === 1
            && sharedEntities.length >= 2
            && entityContainment >= 0.75
            && titleScore >= 0.35;
        if (!(exactTitle || titleEligible || containedVariantEligible)) continue;
        const [a, b] = [left.canonical, right.canonical].sort((x, y) => x.canonical_id.localeCompare(y.canonical_id));
        const candidateId = `boundary_${a.canonical_id}_${b.canonical_id}`;
        const decision = decisions.get(candidateId);
        rows.push({
            schema_version: 'canonical_boundary_candidate.v1',
            candidate_id: candidateId,
            canonical_ids: [a.canonical_id, b.canonical_id],
            algorithm_score: score,
            evidence: {
                exact_normalized_title: exactTitle,
                title_token_jaccard: Number(titleScore.toFixed(4)),
                shared_entities: sharedEntities.sort(),
                shared_entity_count: sharedEntities.length,
                entity_containment: Number(entityContainment.toFixed(4)),
                same_domain: domainScore === 1,
                contained_variant_signal: containedVariantEligible,
            },
            proposed_action: exactTitle ? 'merge_review' : 'boundary_review',
            reviewer_decision: decision?.decision || 'pending',
            reviewer_note: decision?.note || null,
        });
    }
    return rows.sort((a, b) => b.algorithm_score - a.algorithm_score || a.candidate_id.localeCompare(b.candidate_id));
}

function main(argv = process.argv) {
    try {
        const options = parseArgs(argv);
        const root = options.root || ROOT;
        const output = path.join(root, 'data', 'manifests', 'canonical', 'long_tail_duplicate_candidates.jsonl');
        const rows = buildCandidates({ root });
        const expected = `${rows.map(stableStringify).join('\n')}${rows.length ? '\n' : ''}`;
        const current = fs.existsSync(output) ? fs.readFileSync(output, 'utf8') : '';
        const report = { schema_version: 'canonical_boundary_audit.v1', ok: !options.check || current === expected, check: options.check, candidate_count: rows.length, output: path.relative(root, output) };
        if (!options.check) writeJsonl(output, rows);
        console.log(JSON.stringify(report, null, 2));
        return report.ok ? 0 : 1;
    } catch (error) {
        console.error(error.message);
        return 1;
    }
}

if (require.main === module) process.exitCode = main();

module.exports = { buildCandidates, main };
