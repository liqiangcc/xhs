'use strict';

const crypto = require('crypto');
const fs = require('fs');
const path = require('path');
const { loadCanonicalQuestions } = require('./canonical_store');
const { readJson, readJsonl, stablePrettyStringify, stableStringify, ensureDir } = require('./io');
const {
    answerPath,
    parseAnswerMetadata,
    readAnswerFile,
    replaceAnswerMetadata,
    validateAnswerContent,
} = require('./answer_store');
const { render } = require('../content/render_answer_specs');
const { defaultDate } = require('./date');

const DEFAULT_ROOT = path.resolve(__dirname, '..', '..');

function pathsFor(root = DEFAULT_ROOT) {
    return {
        qualityConfig: path.join(root, 'config', 'answer_quality.json'),
        canonicalQuestions: path.join(root, 'data', 'questions', 'canonical_questions.jsonl'),
        questions: path.join(root, 'data', 'questions', 'questions.jsonl'),
        answersDir: path.join(root, 'review', 'answers'),
        candidateAnswersDir: path.join(root, 'review', 'candidates', 'answers'),
        candidateAuditsDir: path.join(root, 'review', 'candidates', 'audits'),
        evidenceDir: path.join(root, 'review', 'evidence'),
    };
}

function sha256(value) {
    return crypto.createHash('sha256').update(String(value), 'utf8').digest('hex');
}

function inferAnswerType(questions = [], canonical = {}) {
    const joined = questions.map((item) => item.question_type || '').join(' ').toLowerCase();
    const title = String(canonical.canonical_title || '').toLowerCase();
    if (/coding|算法手撕|sql/.test(joined)) return 'coding';
    if (/项目|project|故障|线上排障/.test(joined + title)) return 'project';
    if (/行为|behavior|自我介绍|职业|冲突|沟通/.test(joined + title)) return 'behavior';
    if (/场景|system|设计|架构|方案/.test(joined + title)) return 'scenario';
    if (/原理|mechanism|流程|过程|底层/.test(joined + title)) return 'mechanism';
    return 'concept';
}

function answerExcerpt(filePath, limit = 800) {
    if (!fs.existsSync(filePath)) return null;
    const content = fs.readFileSync(filePath, 'utf8');
    return content.slice(content.indexOf('\n') + 1, limit).trim();
}

function buildAnswerContext(options = {}) {
    const root = options.root ? path.resolve(options.root) : DEFAULT_ROOT;
    const paths = pathsFor(root);
    const canonicalId = options['canonical-id'] || options.canonicalId;
    if (!canonicalId) throw new Error('Usage: answer context --canonical-id <id>');
    const canonicals = loadCanonicalQuestions({ filePath: paths.canonicalQuestions });
    const canonical = canonicals.find((item) => item.canonical_id === canonicalId);
    if (!canonical) throw new Error(`Canonical not found: ${canonicalId}`);
    const allQuestions = readJsonl(paths.questions, []);
    const questionIds = new Set(canonical.question_ids || []);
    const sourceQuestions = allQuestions.filter((item) =>
        item.canonical_id === canonicalId || questionIds.has(item.question_id)
    );
    const sameDomain = canonicals.filter((item) =>
        item.canonical_id !== canonicalId
        && item.primary_domain?.l1 === canonical.primary_domain?.l1
        && item.primary_domain?.l2 === canonical.primary_domain?.l2
    );
    const adjacentCanonicals = sameDomain
        .sort((a, b) => Number(b.frequency || 0) - Number(a.frequency || 0) || a.canonical_id.localeCompare(b.canonical_id))
        .slice(0, 5)
        .map((item) => ({
            canonical_id: item.canonical_id,
            canonical_title: item.canonical_title,
            primary_entities: item.primary_entities || [],
            answer_status: item.answer_status,
        }));
    const answerType = inferAnswerType(sourceQuestions, canonical);
    const styleSamples = canonicals
        .filter((item) => item.canonical_id !== canonicalId && item.answer_status === 'ready')
        .map((item) => {
            const filePath = answerPath(item.canonical_id, { answersDir: paths.answersDir });
            if (!fs.existsSync(filePath)) return null;
            const answer = readAnswerFile(filePath);
            if (answer.metadata.quality_tier !== 'curated') return null;
            const itemQuestions = allQuestions.filter((question) => question.canonical_id === item.canonical_id);
            return {
                canonical_id: item.canonical_id,
                canonical_title: item.canonical_title,
                answer_type: answer.metadata.answer_type || inferAnswerType(itemQuestions, item),
                answer_path: path.relative(root, filePath),
                excerpt: answerExcerpt(filePath),
            };
        })
        .filter(Boolean)
        .sort((a, b) => Number(b.answer_type === answerType) - Number(a.answer_type === answerType))
        .slice(0, 3);
    return {
        schema_version: 'answer_context.v1',
        ok: true,
        canonical,
        answer_type: answerType,
        source_questions: sourceQuestions,
        source_variants: [...new Set([
            canonical.canonical_title,
            ...(canonical.aliases || []),
            ...sourceQuestions.map((item) => item.original_question),
        ].filter(Boolean))],
        primary_entities: canonical.primary_entities || [],
        primary_domain: canonical.primary_domain || null,
        companies: canonical.companies || [],
        adjacent_canonicals: adjacentCanonicals,
        curated_style_samples: styleSamples,
    };
}

function assertPathWithin(filePath, parentDir, label) {
    const resolved = path.resolve(filePath);
    const parent = `${path.resolve(parentDir)}${path.sep}`;
    if (!resolved.startsWith(parent)) throw new Error(`${label} must be inside ${path.relative(DEFAULT_ROOT, parentDir)}`);
    return resolved;
}

function candidateMetadata(metadata, canonicalId, answerType, date) {
    return {
        ...metadata,
        schema_version: 'answer.v1',
        canonical_id: canonicalId,
        version: Number(metadata.version || 1),
        status: 'draft',
        updated_at: date,
        answer_type: answerType,
        quality_tier: 'candidate',
    };
}

function renderCandidate(options = {}) {
    const root = options.root ? path.resolve(options.root) : DEFAULT_ROOT;
    const paths = pathsFor(root);
    const specPath = options.spec ? path.resolve(options.spec) : null;
    if (!specPath) throw new Error('Usage: answer candidate render --spec <json>');
    const spec = readJson(specPath);
    const entry = spec.answer || spec;
    const canonicalId = entry.canonical_id;
    if (!canonicalId) throw new Error('Candidate spec requires canonical_id');
    const canonical = loadCanonicalQuestions({ filePath: paths.canonicalQuestions })
        .find((item) => item.canonical_id === canonicalId);
    if (!canonical) throw new Error(`Canonical not found: ${canonicalId}`);
    const date = options.date || spec.updated_at || defaultDate(options);
    const answerType = entry.answer_type || entry.type || buildAnswerContext({ root, canonicalId }).answer_type;
    let content;
    if (typeof entry.content === 'string') {
        parseAnswerMetadata(entry.content, specPath);
        content = replaceAnswerMetadata(entry.content, candidateMetadata(parseAnswerMetadata(entry.content), canonicalId, answerType, date));
    } else {
        content = render({ ...entry, type: answerType }, canonical, date);
        content = replaceAnswerMetadata(content, candidateMetadata(parseAnswerMetadata(content), canonicalId, answerType, date));
    }
    const filePath = path.join(paths.candidateAnswersDir, `${canonicalId}.md`);
    const changed = !fs.existsSync(filePath) || fs.readFileSync(filePath, 'utf8') !== content;
    if (!options.noWrite) {
        ensureDir(paths.candidateAnswersDir);
        fs.writeFileSync(filePath, content, 'utf8');
    }
    return {
        schema_version: 'answer_candidate_render.v1',
        ok: true,
        dry_run: Boolean(options.noWrite),
        canonical_id: canonicalId,
        answer_type: answerType,
        candidate_path: path.relative(root, filePath),
        candidate_sha256: sha256(content),
        changed,
    };
}

function scoreReview(review, config) {
    const scores = review?.scores || {};
    const dimensionScores = {};
    const errors = [];
    let total = 0;
    for (const [dimension, rule] of Object.entries(config.dimensions || {})) {
        const score = Number(scores[dimension]);
        dimensionScores[dimension] = Number.isFinite(score) ? score : 0;
        total += dimensionScores[dimension];
        if (!Number.isFinite(score)) errors.push({ error: 'missing_dimension_score', dimension });
        else if (score < rule.minimum_score) errors.push({ error: 'dimension_below_minimum', dimension, score, minimum: rule.minimum_score });
        else if (score > rule.weight) errors.push({ error: 'dimension_above_weight', dimension, score, maximum: rule.weight });
    }
    return { scores: dimensionScores, total_score: total, errors };
}

function evidencePathFor(candidate, paths, explicitPath) {
    if (explicitPath) return path.resolve(explicitPath);
    return path.join(paths.evidenceDir, `${candidate.metadata.canonical_id}.json`);
}

function auditOneCandidate(filePath, options = {}) {
    const root = options.root ? path.resolve(options.root) : DEFAULT_ROOT;
    const paths = pathsFor(root);
    const config = readJson(paths.qualityConfig);
    const candidate = readAnswerFile(filePath);
    const canonicalId = candidate.metadata.canonical_id;
    const errors = [];
    const hardFailures = [];
    if (candidate.metadata.quality_tier !== 'candidate') errors.push({ error: 'invalid_candidate_tier' });
    const readyView = { ...candidate, metadata: { ...candidate.metadata, status: 'ready' } };
    for (const issue of validateAnswerContent(readyView)) errors.push(issue);
    const evidencePath = evidencePathFor(candidate, paths, options.evidence);
    const evidence = fs.existsSync(evidencePath) ? readJson(evidencePath) : null;
    if (!evidence) hardFailures.push('missing_evidence');
    if (evidence && evidence.canonical_id !== canonicalId) errors.push({ error: 'evidence_canonical_mismatch' });
    if (evidence && evidence.candidate_sha256 !== sha256(candidate.content)) errors.push({ error: 'candidate_hash_mismatch' });
    const review = evidence?.review || null;
    const scored = scoreReview(review, config);
    errors.push(...scored.errors);
    for (const id of review?.hard_failures || []) hardFailures.push(id);
    if (!review?.independent || !review?.reviewer_id || review.reviewer_id === evidence?.writer?.writer_id) {
        hardFailures.push('missing_independent_review');
    }
    if (review?.decision !== 'pass') errors.push({ error: 'review_not_passed', decision: review?.decision || null });
    if (scored.total_score < config.promotion.minimum_total_score) {
        errors.push({ error: 'total_score_below_minimum', score: scored.total_score, minimum: config.promotion.minimum_total_score });
    }
    const knownHardFailures = new Set((config.hard_failures || []).map((item) => item.id));
    for (const id of [...new Set(hardFailures)]) {
        if (!knownHardFailures.has(id)) errors.push({ error: 'unknown_hard_failure', id });
    }
    const uniqueHardFailures = [...new Set(hardFailures)];
    const ok = errors.length === 0 && uniqueHardFailures.length === 0;
    return {
        schema_version: 'answer_audit.v1',
        ok,
        canonical_id: canonicalId,
        candidate_path: path.relative(root, filePath),
        candidate_sha256: sha256(candidate.content),
        answer_type: candidate.metadata.answer_type || null,
        quality_tier: candidate.metadata.quality_tier || null,
        evidence_path: evidence ? path.relative(root, evidencePath) : null,
        scores: scored.scores,
        total_score: scored.total_score,
        hard_failures: uniqueHardFailures,
        errors,
        revision_suggestions: review?.revision_suggestions || [],
    };
}

function readSetIds(setPath) {
    if (!setPath) return null;
    const value = readJson(path.resolve(setPath));
    const rows = Array.isArray(value) ? value : value.canonical_ids || value.rows || value.answers || [];
    return new Set(rows.map((item) => typeof item === 'string' ? item : item.canonical_id).filter(Boolean));
}

function runAnswerAudit(options = {}) {
    const root = options.root ? path.resolve(options.root) : DEFAULT_ROOT;
    const paths = pathsFor(root);
    let candidatePaths;
    if (options.candidate) {
        candidatePaths = [assertPathWithin(path.resolve(options.candidate), paths.candidateAnswersDir, 'candidate')];
    } else {
        candidatePaths = fs.existsSync(paths.candidateAnswersDir)
            ? fs.readdirSync(paths.candidateAnswersDir).filter((name) => name.endsWith('.md')).sort().map((name) => path.join(paths.candidateAnswersDir, name))
            : [];
    }
    const types = new Set([].concat(options.type || []).filter(Boolean));
    const setIds = readSetIds(options.set);
    const rows = candidatePaths.map((filePath) => auditOneCandidate(filePath, options)).filter((row) => {
        if (options.tier && row.quality_tier !== options.tier) return false;
        if (types.size && !types.has(row.answer_type)) return false;
        if (setIds && !setIds.has(row.canonical_id)) return false;
        if (options['require-evidence'] && !row.evidence_path) return false;
        if (options['require-code']) {
            const content = fs.readFileSync(path.resolve(root, row.candidate_path), 'utf8');
            if (!/```(?:java|sql)\b/i.test(content)) return false;
        }
        return true;
    });
    if (!options.noWrite) {
        ensureDir(paths.candidateAuditsDir);
        for (const row of rows) fs.writeFileSync(path.join(paths.candidateAuditsDir, `${row.canonical_id}.json`), stablePrettyStringify(row), 'utf8');
    }
    return {
        schema_version: 'answer_audit_report.v1',
        ok: rows.length > 0 && rows.every((row) => row.ok),
        dry_run: Boolean(options.noWrite),
        candidate_count: rows.length,
        passed_count: rows.filter((row) => row.ok).length,
        failed_count: rows.filter((row) => !row.ok).length,
        rows,
    };
}

function atomicPromote(options = {}) {
    const root = options.root ? path.resolve(options.root) : DEFAULT_ROOT;
    const paths = pathsFor(root);
    const canonicalId = options['canonical-id'] || options.canonicalId;
    if (!canonicalId || !options.candidate || !options.evidence) {
        throw new Error('Usage: answer promote --canonical-id <id> --candidate <path> --evidence <path>');
    }
    const candidatePath = assertPathWithin(path.resolve(options.candidate), paths.candidateAnswersDir, 'candidate');
    const evidencePath = assertPathWithin(path.resolve(options.evidence), paths.evidenceDir, 'evidence');
    const candidate = readAnswerFile(candidatePath);
    if (candidate.metadata.canonical_id !== canonicalId) throw new Error('candidate canonical_id does not match requested canonical_id');
    const audit = auditOneCandidate(candidatePath, { ...options, root, evidence: evidencePath });
    if (!audit.ok) return { schema_version: 'answer_promote.v1', ok: false, promoted: false, canonical_id: canonicalId, audit };
    const canonicals = loadCanonicalQuestions({ filePath: paths.canonicalQuestions });
    const index = canonicals.findIndex((item) => item.canonical_id === canonicalId);
    if (index < 0) throw new Error(`Canonical not found: ${canonicalId}`);
    const formalPath = answerPath(canonicalId, { answersDir: paths.answersDir });
    const oldFormal = fs.existsSync(formalPath) ? fs.readFileSync(formalPath, 'utf8') : null;
    const oldMetadata = oldFormal ? parseAnswerMetadata(oldFormal, formalPath) : {};
    const evidence = readJson(evidencePath);
    const nextMetadata = {
        ...candidate.metadata,
        version: Number(oldMetadata.version || 0) + 1,
        status: 'ready',
        quality_tier: 'curated',
        updated_at: options.date || defaultDate(options),
        candidate_sha256: audit.candidate_sha256,
        evidence_version: evidence.review?.review_version || evidence.schema_version,
    };
    delete nextMetadata.generator_version;
    const nextFormal = replaceAnswerMetadata(candidate.content, nextMetadata);
    const nextCanonicals = canonicals.map((item, itemIndex) => itemIndex === index ? { ...item, answer_status: 'ready' } : item);
    const nextCanonicalText = `${nextCanonicals.sort((a, b) => a.canonical_id.localeCompare(b.canonical_id)).map(stableStringify).join('\n')}\n`;
    if (options.noWrite) {
        return { schema_version: 'answer_promote.v1', ok: true, promoted: false, dry_run: true, canonical_id: canonicalId, audit };
    }
    ensureDir(path.dirname(formalPath));
    const canonicalPath = paths.canonicalQuestions;
    const oldCanonicalText = fs.readFileSync(canonicalPath, 'utf8');
    const formalTemp = `${formalPath}.promote-${process.pid}.tmp`;
    const canonicalTemp = `${canonicalPath}.promote-${process.pid}.tmp`;
    fs.writeFileSync(formalTemp, nextFormal, 'utf8');
    fs.writeFileSync(canonicalTemp, nextCanonicalText, 'utf8');
    try {
        fs.renameSync(formalTemp, formalPath);
        fs.renameSync(canonicalTemp, canonicalPath);
    } catch (error) {
        if (oldFormal === null) fs.rmSync(formalPath, { force: true });
        else fs.writeFileSync(formalPath, oldFormal, 'utf8');
        fs.writeFileSync(canonicalPath, oldCanonicalText, 'utf8');
        fs.rmSync(formalTemp, { force: true });
        fs.rmSync(canonicalTemp, { force: true });
        throw error;
    }
    return {
        schema_version: 'answer_promote.v1',
        ok: true,
        promoted: true,
        dry_run: false,
        canonical_id: canonicalId,
        answer_path: path.relative(root, formalPath),
        version: nextMetadata.version,
        audit,
    };
}

module.exports = {
    pathsFor,
    sha256,
    inferAnswerType,
    buildAnswerContext,
    renderCandidate,
    auditOneCandidate,
    runAnswerAudit,
    atomicPromote,
};
