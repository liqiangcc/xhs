'use strict';

const crypto = require('crypto');
const childProcess = require('child_process');
const fs = require('fs');
const os = require('os');
const path = require('path');
const { loadCanonicalQuestions } = require('./canonical_store');
const { readJson, readJsonl, writeJson, stablePrettyStringify, stableStringify, ensureDir } = require('./io');
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
    const styleSamples = options.includeStyleSamples === false ? [] : canonicals
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
        // Candidates must contain only writer-supplied topic prose. The
        // historical renderer's generic type guidance belongs to curated specs
        // and would otherwise introduce cross-topic contamination.
        content = render({ ...entry, type: answerType, include_type_guidance: false }, canonical, date);
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

const GENERIC_FOLLOWUP_PATTERNS = [
    /这道题最先要澄清什么/,
    /如何验证回答不是背诵/,
    /方案的主要代价是什么/,
    /题目继续追问源码或底层时怎么答/,
    /核心判断是什么/,
];

const TEMPLATE_PATTERNS = [
    /先界定题目中的概念、版本和约束/,
    /先确认题目范围、运行版本、输入输出、数据规模/,
    /结论必须能由样例、日志、指标、源码或最小实验/,
    /static\s+final\s+class\s+ProblemSpec/,
    /WITH\s+base\s+AS\s*\(/i,
    /static\s+long\s+solveDp\s*\(/,
];

const STRONG_TOPIC_ANCHORS = [
    'Redis', 'MySQL', 'PostgreSQL', 'MongoDB', 'Kafka', 'RocketMQ', 'RabbitMQ', 'ZooKeeper',
    'Elasticsearch', 'Spring', 'Netty', 'Dubbo', 'JVM', 'AQS', 'HashMap', 'B+ 树', 'B+树',
];

function addHardFailure(target, id) {
    if (!target.includes(id)) target.push(id);
}

function extractSection(content, title) {
    const match = String(content).match(new RegExp(`(?:^|\\n)##\\s+${title.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')}\\s*\\n([\\s\\S]*?)(?=\\n##\\s+|$)`));
    return match ? match[1].trim() : '';
}

function validateAnswerEvidence(evidence, candidate, context, config) {
    const errors = [];
    const hardFailures = [];
    if (!evidence || typeof evidence !== 'object') return { errors: [{ error: 'missing_evidence' }], hard_failures: ['missing_evidence'] };
    if (evidence.schema_version !== 'answer_evidence.v1') errors.push({ error: 'invalid_evidence_schema_version' });
    if (evidence.canonical_id !== candidate.metadata.canonical_id) errors.push({ error: 'evidence_canonical_mismatch' });
    if (evidence.candidate_sha256 !== sha256(candidate.content)) errors.push({ error: 'candidate_hash_mismatch' });
    if (!/^\d{4}-\d{2}-\d{2}$/.test(evidence.checked_at || '')) errors.push({ error: 'invalid_checked_at' });
    if (!evidence.writer?.writer_id || !evidence.writer?.writer_version) errors.push({ error: 'missing_writer_version' });
    if (!evidence.review?.reviewer_id || !evidence.review?.review_version) errors.push({ error: 'missing_reviewer_version' });
    if (!Number.isInteger(evidence.review?.revision_round) || evidence.review.revision_round < 0
        || evidence.review.revision_round > config.promotion.maximum_revision_rounds) {
        errors.push({ error: 'invalid_revision_round', maximum: config.promotion.maximum_revision_rounds });
    }

    const allowedSourceTypes = new Set(config.evidence_policy.source_priority);
    const sourceIds = new Set();
    if (!Array.isArray(evidence.sources) || evidence.sources.length === 0) {
        addHardFailure(hardFailures, 'missing_evidence');
        errors.push({ error: 'sources_required' });
    } else {
        for (const [index, source] of evidence.sources.entries()) {
            if (!source?.source_id || sourceIds.has(source.source_id)) errors.push({ error: 'invalid_or_duplicate_source_id', index });
            else sourceIds.add(source.source_id);
            if (!source?.title || !source?.locator) errors.push({ error: 'source_title_and_locator_required', source_id: source?.source_id || null });
            if (!allowedSourceTypes.has(source?.source_type)) errors.push({ error: 'invalid_source_type', source_id: source?.source_id || null });
            if (!/^\d{4}-\d{2}-\d{2}$/.test(source?.checked_at || '')) errors.push({ error: 'invalid_source_checked_at', source_id: source?.source_id || null });
        }
    }
    if (!Array.isArray(evidence.claims) || evidence.claims.length === 0) {
        addHardFailure(hardFailures, 'missing_evidence');
        errors.push({ error: 'claims_required' });
    } else {
        const claimIds = new Set();
        for (const [index, claim] of evidence.claims.entries()) {
            if (!claim?.claim_id || claimIds.has(claim.claim_id)) errors.push({ error: 'invalid_or_duplicate_claim_id', index });
            else claimIds.add(claim.claim_id);
            if (!claim?.text || !Array.isArray(claim.answer_locations) || claim.answer_locations.length === 0) {
                errors.push({ error: 'claim_text_and_locations_required', claim_id: claim?.claim_id || null });
            }
            if (!Array.isArray(claim.source_ids) || claim.source_ids.length === 0
                || claim.source_ids.some((sourceId) => !sourceIds.has(sourceId))) {
                addHardFailure(hardFailures, 'unsupported_factual_claim');
                errors.push({ error: 'claim_source_mapping_invalid', claim_id: claim?.claim_id || null });
            }
        }
    }

    const coverageByQuestionId = new Map((evidence.source_question_coverage || []).map((row) => [row.question_id, row]));
    for (const question of context.source_questions || []) {
        const coverage = coverageByQuestionId.get(question.question_id);
        if (!coverage?.covered || !Array.isArray(coverage.answer_locations) || coverage.answer_locations.length === 0) {
            addHardFailure(hardFailures, 'uncovered_source_variant');
            errors.push({ error: 'source_question_not_covered', question_id: question.question_id });
        }
    }
    return { errors, hard_failures: hardFailures };
}

function extractCodeBlocks(content) {
    const blocks = [];
    const regex = /(?:```|~~~)(java|sql)\s*\n([\s\S]*?)\n(?:```|~~~)/gi;
    let match;
    while ((match = regex.exec(content))) blocks.push({ language: match[1].toLowerCase(), code: match[2].trim() });
    return blocks;
}

function compileJava(code) {
    const tempDir = fs.mkdtempSync(path.join(os.tmpdir(), 'xhs-answer-javac-'));
    try {
        const className = (code.match(/public\s+(?:final\s+)?class\s+([A-Za-z_$][\w$]*)/) || code.match(/class\s+([A-Za-z_$][\w$]*)/) || [])[1];
        if (!className) return { ok: false, error: 'java_class_required' };
        const filePath = path.join(tempDir, `${className}.java`);
        fs.writeFileSync(filePath, code, 'utf8');
        const result = childProcess.spawnSync('javac', ['-encoding', 'UTF-8', '-d', tempDir, filePath], { encoding: 'utf8', timeout: 15000 });
        return { ok: result.status === 0, error: result.status === 0 ? null : (result.stderr || result.stdout || 'javac_failed').slice(0, 2000) };
    } finally {
        fs.rmSync(tempDir, { recursive: true, force: true });
    }
}

function parseSql(code) {
    const stripped = code.replace(/--[^\n]*/g, '').replace(/\/\*[\s\S]*?\*\//g, '').trim();
    if (!/^(?:WITH\b[\s\S]+?\b(?:SELECT|INSERT|UPDATE|DELETE)\b|SELECT\b|INSERT\b|UPDATE\b|DELETE\b)/i.test(stripped)) {
        return { ok: false, error: 'sql_statement_required' };
    }
    let depth = 0;
    let quote = null;
    for (let index = 0; index < stripped.length; index++) {
        const char = stripped[index];
        if (quote) {
            if (char === quote && stripped[index - 1] !== '\\') quote = null;
        } else if (char === '\'' || char === '"' || char === '`') quote = char;
        else if (char === '(') depth += 1;
        else if (char === ')') {
            depth -= 1;
            if (depth < 0) return { ok: false, error: 'sql_unbalanced_parentheses' };
        }
    }
    if (quote || depth !== 0) return { ok: false, error: quote ? 'sql_unclosed_quote' : 'sql_unbalanced_parentheses' };
    if (/\b(?:source_table|your_table|table_name|column_name)\b|<[^>]+>|\bTODO\b/i.test(stripped)) return { ok: false, error: 'sql_placeholder' };
    return { ok: true, error: null };
}

function validateSpecializedCandidate(candidate, evidence, context) {
    const errors = [];
    const hardFailures = [];
    const content = candidate.content;
    const core = extractSection(content, '核心结论');
    const followups = extractSection(content, '常见追问').split(/\r?\n/).filter((line) => /^-\s*问[：:]/.test(line));
    const genericFollowups = followups.filter((line) => GENERIC_FOLLOWUP_PATTERNS.some((pattern) => pattern.test(line)));
    if (followups.length < 3 || genericFollowups.length > 0) {
        addHardFailure(hardFailures, 'generic_followups');
        errors.push({ error: 'followups_not_question_specific', followup_count: followups.length, generic_count: genericFollowups.length });
    }
    const matchedTemplates = TEMPLATE_PATTERNS.filter((pattern) => pattern.test(content)).map(String);
    if (matchedTemplates.length > 0 || /^复习「/.test(core)) {
        addHardFailure(hardFailures, 'template_only_answer');
        errors.push({ error: 'legacy_template_detected', patterns: matchedTemplates });
    }
    const allowedText = [context.canonical.canonical_title, ...(context.primary_entities || []), ...(context.source_variants || [])].join(' ').toLowerCase();
    const coreLower = core.toLowerCase();
    const relevantTokens = [...(context.primary_entities || []), ...String(context.canonical.canonical_title || '').split(/[\s：:，,？?、与和的]+/)]
        .filter((value) => String(value).length >= 2);
    const hasRelevantCoreToken = relevantTokens.some((token) => coreLower.includes(String(token).toLowerCase()));
    const foreignAnchors = STRONG_TOPIC_ANCHORS.filter((anchor) => coreLower.includes(anchor.toLowerCase()) && !allowedText.includes(anchor.toLowerCase()));
    if (!hasRelevantCoreToken && foreignAnchors.length > 0) {
        addHardFailure(hardFailures, 'cross_topic_contamination');
        errors.push({ error: 'foreign_core_topic', entities: foreignAnchors });
    }

    const answerType = candidate.metadata.answer_type;
    if (answerType === 'coding') {
        const blocks = extractCodeBlocks(content);
        if (blocks.length === 0) {
            addHardFailure(hardFailures, 'placeholder_implementation');
            errors.push({ error: 'coding_block_required' });
        }
        for (const block of blocks) {
            const validation = block.language === 'java' ? compileJava(block.code) : parseSql(block.code);
            if (!validation.ok) {
                addHardFailure(hardFailures, /placeholder|required/.test(validation.error || '') ? 'placeholder_implementation' : 'unrunnable_implementation');
                errors.push({ error: `${block.language}_validation_failed`, detail: validation.error });
            }
        }
        const boundaryTests = evidence?.validation?.boundary_tests;
        if (!Array.isArray(boundaryTests) || boundaryTests.length < 3 || boundaryTests.some((item) => item.passed !== true || !item.case || item.expected === undefined)) {
            addHardFailure(hardFailures, 'unrunnable_implementation');
            errors.push({ error: 'three_passing_boundary_tests_required' });
        }
    }
    if (answerType === 'project' || answerType === 'behavior') {
        if (/\bTODO\b|\bTBD\b|\bXX+\b|\[[^\]]*(?:公司|项目|指标|数据|补充)[^\]]*\]|<[^>]*(?:公司|项目|指标|数据|补充)[^>]*>/i.test(content)) {
            addHardFailure(hardFailures, 'placeholder_implementation');
            errors.push({ error: 'unfilled_experience_placeholder' });
        }
        const firstPersonFact = /(?:我|我们)(?:负责|主导|推动|上线|排查|优化|将|使|曾经)|(?:提升|降低|节省|达到)\s*\d+(?:\.\d+)?%/.test(content);
        if (firstPersonFact && (!Array.isArray(evidence?.experience_facts) || evidence.experience_facts.length === 0)) {
            addHardFailure(hardFailures, 'fabricated_experience');
            errors.push({ error: 'first_person_claim_without_experience_evidence' });
        }
    }
    return { errors, hard_failures: hardFailures };
}

function evidencePathFor(candidate, paths, explicitPath) {
    if (explicitPath) return path.resolve(explicitPath);
    return path.join(paths.evidenceDir, `${candidate.metadata.canonical_id}.json`);
}

function humanReviewError(evidence) {
    const review = evidence?.human_review;
    if (!review || review.reviewer_type !== 'human' || review.decision !== 'approved'
        || !review.reviewer_id || !review.batch_id || !review.attestation
        || !/^\d{4}-\d{2}-\d{2}$/.test(review.reviewed_at || '')) {
        return 'human_review_required';
    }
    return null;
}

function countHumanReviewApprovals(paths) {
    if (!fs.existsSync(paths.evidenceDir)) return 0;
    return fs.readdirSync(paths.evidenceDir)
        .filter((name) => name.endsWith('.json'))
        .map((name) => readJson(path.join(paths.evidenceDir, name)))
        .filter((evidence) => !humanReviewError(evidence))
        .length;
}

function recordHumanReview(options = {}) {
    const root = options.root ? path.resolve(options.root) : DEFAULT_ROOT;
    const paths = pathsFor(root);
    const canonicalId = options['canonical-id'] || options.canonicalId;
    if (!canonicalId || !options.evidence || !options.review) {
        throw new Error('Usage: answer human-review --canonical-id <id> --evidence <path> --review <json>');
    }
    const evidencePath = assertPathWithin(path.resolve(options.evidence), paths.evidenceDir, 'evidence');
    const evidence = readJson(evidencePath);
    const review = readJson(path.resolve(options.review));
    if (evidence.canonical_id !== canonicalId || review.canonical_id !== canonicalId) throw new Error('human review canonical_id mismatch');
    if (review.candidate_sha256 !== evidence.candidate_sha256) throw new Error('human review candidate hash mismatch');
    if (review.reviewer_type !== 'human' || !review.reviewer_id || !review.batch_id || !review.attestation
        || !/^\d{4}-\d{2}-\d{2}$/.test(review.reviewed_at || '') || !['approved', 'rejected'].includes(review.decision)) {
        throw new Error('invalid human review record');
    }
    const nextEvidence = { ...evidence, human_review: review };
    if (!options.noWrite) writeJson(evidencePath, nextEvidence);
    return { schema_version: 'answer_human_review.v1', ok: true, dry_run: Boolean(options.noWrite), canonical_id: canonicalId, decision: review.decision, batch_id: review.batch_id };
}

function auditOneCandidate(filePath, options = {}) {
    const root = options.root ? path.resolve(options.root) : DEFAULT_ROOT;
    const paths = pathsFor(root);
    const config = readJson(paths.qualityConfig);
    const candidate = readAnswerFile(filePath);
    const canonicalId = candidate.metadata.canonical_id;
    const errors = [];
    const hardFailures = [];
    if (candidate.metadata.quality_tier !== 'candidate'
        && !(options.allowFormal && ['curated', 'curated_audit_failed'].includes(candidate.metadata.quality_tier))) {
        errors.push({ error: 'invalid_candidate_tier' });
    }
    const readyView = { ...candidate, metadata: { ...candidate.metadata, status: 'ready' } };
    for (const issue of validateAnswerContent(readyView)) errors.push(issue);
    const evidencePath = evidencePathFor(candidate, paths, options.evidence);
    const evidence = fs.existsSync(evidencePath) ? readJson(evidencePath) : null;
    const context = buildAnswerContext({ root, canonicalId, includeStyleSamples: false });
    const evidenceValidation = validateAnswerEvidence(evidence, candidate, context, config);
    errors.push(...evidenceValidation.errors);
    for (const id of evidenceValidation.hard_failures) addHardFailure(hardFailures, id);
    const specializedValidation = validateSpecializedCandidate(candidate, evidence, context);
    errors.push(...specializedValidation.errors);
    for (const id of specializedValidation.hard_failures) addHardFailure(hardFailures, id);
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
    const resolved = path.resolve(setPath);
    const value = resolved.endsWith('.jsonl') ? readJsonl(resolved) : readJson(resolved);
    const rows = Array.isArray(value) ? value : value.canonical_ids || value.rows || value.answers || [];
    return new Set(rows.map((item) => typeof item === 'string' ? item : item.canonical_id).filter(Boolean));
}

function runAnswerAudit(options = {}) {
    if (options.fixtures) {
        return require('../content/check_answer_evidence').runEvidenceFixtures(options);
    }
    const root = options.root ? path.resolve(options.root) : DEFAULT_ROOT;
    const paths = pathsFor(root);
    let candidatePaths;
    if (options.candidate) {
        candidatePaths = [assertPathWithin(path.resolve(options.candidate), paths.candidateAnswersDir, 'candidate')];
    } else if (options.tier === 'curated') {
        candidatePaths = fs.existsSync(paths.answersDir)
            ? fs.readdirSync(paths.answersDir).filter((name) => name.endsWith('.md')).sort().map((name) => path.join(paths.answersDir, name))
            : [];
    } else {
        candidatePaths = fs.existsSync(paths.candidateAnswersDir)
            ? fs.readdirSync(paths.candidateAnswersDir).filter((name) => name.endsWith('.md')).sort().map((name) => path.join(paths.candidateAnswersDir, name))
            : [];
    }
    const types = new Set([].concat(options.type || []).filter(Boolean));
    const setIds = readSetIds(options.set);
    const selectedPaths = candidatePaths.filter((filePath) => {
        const answer = readAnswerFile(filePath);
        if (options.tier && answer.metadata.quality_tier !== options.tier) return false;
        const title = (answer.content.match(/^#\s+(.+)$/m) || [])[1] || answer.metadata.canonical_id;
        if (types.size && !types.has(answer.metadata.answer_type || inferAnswerType([], { canonical_title: title }))) return false;
        if (setIds && !setIds.has(answer.metadata.canonical_id)) return false;
        if (options['require-code'] && !/(?:```|~~~)(?:java|sql)\b/i.test(answer.content)) return false;
        return true;
    });
    const rows = selectedPaths.map((filePath) => auditOneCandidate(filePath, { ...options, allowFormal: options.tier === 'curated' })).filter((row) => {
        if (options['require-evidence'] && !row.evidence_path) return false;
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
    const qualityConfig = readJson(paths.qualityConfig);
    const humanReviewNeeded = qualityConfig.promotion.require_human_review_for_pilot
        && countHumanReviewApprovals(paths) < Number(qualityConfig.promotion.pilot_human_review_count || 0);
    const humanError = humanReviewNeeded ? humanReviewError(evidence) : null;
    if (humanError) {
        return {
            schema_version: 'answer_promote.v1', ok: false, promoted: false, canonical_id: canonicalId,
            audit: { ...audit, ok: false, hard_failures: [...new Set([...audit.hard_failures, 'missing_human_review'])], errors: [...audit.errors, { error: humanError }] },
        };
    }
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

function atomicDemote(options = {}) {
    const root = options.root ? path.resolve(options.root) : DEFAULT_ROOT;
    const paths = pathsFor(root);
    const canonicalId = options['canonical-id'] || options.canonicalId;
    if (!canonicalId || !options.evidence) throw new Error('Usage: answer demote --canonical-id <id> --evidence <path>');
    const evidencePath = assertPathWithin(path.resolve(options.evidence), paths.evidenceDir, 'evidence');
    const formalPath = answerPath(canonicalId, { answersDir: paths.answersDir });
    if (!fs.existsSync(formalPath)) throw new Error(`Formal answer not found: ${canonicalId}`);
    const formal = readAnswerFile(formalPath);
    const evidence = readJson(evidencePath);
    if (formal.metadata.canonical_id !== canonicalId || evidence.canonical_id !== canonicalId) {
        throw new Error('canonical_id must match the formal answer and evidence');
    }
    if (evidence.candidate_sha256 !== sha256(formal.content)) throw new Error('evidence does not match formal answer hash');
    if (!evidence.review?.independent || !evidence.review?.reviewer_id || evidence.review.reviewer_id === evidence.writer?.writer_id) {
        throw new Error('demotion requires an independent reviewer record');
    }
    if (evidence.review.decision === 'pass' && !(evidence.review.hard_failures || []).length) {
        throw new Error('demotion requires a revise/reject decision or a hard failure');
    }
    const canonicals = loadCanonicalQuestions({ filePath: paths.canonicalQuestions });
    const index = canonicals.findIndex((item) => item.canonical_id === canonicalId);
    if (index < 0) throw new Error(`Canonical not found: ${canonicalId}`);
    const nextMetadata = {
        ...formal.metadata,
        version: Number(formal.metadata.version || 0) + 1,
        status: 'needs_update',
        quality_tier: 'curated_audit_failed',
        updated_at: options.date || defaultDate(options),
        audit_evidence_version: evidence.review.review_version || evidence.schema_version,
    };
    const nextFormal = replaceAnswerMetadata(formal.content, nextMetadata);
    const nextCanonicals = canonicals.map((item, itemIndex) => itemIndex === index ? { ...item, answer_status: 'needs_update' } : item);
    const nextCanonicalText = `${nextCanonicals.sort((a, b) => a.canonical_id.localeCompare(b.canonical_id)).map(stableStringify).join('\n')}\n`;
    if (options.noWrite) return { schema_version: 'answer_demote.v1', ok: true, demoted: false, dry_run: true, canonical_id: canonicalId };
    const oldFormal = fs.readFileSync(formalPath, 'utf8');
    const oldCanonicals = fs.readFileSync(paths.canonicalQuestions, 'utf8');
    const formalTemp = `${formalPath}.demote-${process.pid}.tmp`;
    const canonicalTemp = `${paths.canonicalQuestions}.demote-${process.pid}.tmp`;
    fs.writeFileSync(formalTemp, nextFormal, 'utf8');
    fs.writeFileSync(canonicalTemp, nextCanonicalText, 'utf8');
    try {
        fs.renameSync(formalTemp, formalPath);
        fs.renameSync(canonicalTemp, paths.canonicalQuestions);
    } catch (error) {
        fs.writeFileSync(formalPath, oldFormal, 'utf8');
        fs.writeFileSync(paths.canonicalQuestions, oldCanonicals, 'utf8');
        fs.rmSync(formalTemp, { force: true });
        fs.rmSync(canonicalTemp, { force: true });
        throw error;
    }
    return { schema_version: 'answer_demote.v1', ok: true, demoted: true, canonical_id: canonicalId, answer_path: path.relative(root, formalPath), version: nextMetadata.version };
}

function atomicDemoteMissingEvidence(options = {}) {
    const root = options.root ? path.resolve(options.root) : DEFAULT_ROOT;
    const paths = pathsFor(root);
    const canonicalId = options['canonical-id'] || options.canonicalId;
    if (!canonicalId) throw new Error('canonical_id is required');
    const formalPath = answerPath(canonicalId, { answersDir: paths.answersDir });
    if (!fs.existsSync(formalPath)) throw new Error(`Formal answer not found: ${canonicalId}`);
    const formal = readAnswerFile(formalPath);
    if (formal.metadata.quality_tier !== 'curated' || formal.metadata.status !== 'ready') {
        throw new Error('only ready curated answers may be demoted for missing evidence');
    }
    const evidencePath = path.join(paths.evidenceDir, `${canonicalId}.json`);
    if (fs.existsSync(evidencePath)) throw new Error('evidence exists; use audited answer demote instead');
    const canonicals = loadCanonicalQuestions({ filePath: paths.canonicalQuestions });
    const index = canonicals.findIndex((item) => item.canonical_id === canonicalId);
    if (index < 0) throw new Error(`Canonical not found: ${canonicalId}`);
    const nextMetadata = {
        ...formal.metadata,
        version: Number(formal.metadata.version || 0) + 1,
        status: 'needs_update',
        quality_tier: 'curated_audit_failed',
        updated_at: options.date || defaultDate(options),
        audit_failure: 'missing_evidence',
    };
    const nextFormal = replaceAnswerMetadata(formal.content, nextMetadata);
    const nextCanonicals = canonicals.map((item, itemIndex) => itemIndex === index ? { ...item, answer_status: 'needs_update' } : item);
    const nextCanonicalText = `${nextCanonicals.sort((a, b) => a.canonical_id.localeCompare(b.canonical_id)).map(stableStringify).join('\n')}\n`;
    if (options.noWrite) return { schema_version: 'answer_demote_missing_evidence.v1', ok: true, demoted: false, dry_run: true, canonical_id: canonicalId };
    const oldFormal = fs.readFileSync(formalPath, 'utf8');
    const oldCanonicals = fs.readFileSync(paths.canonicalQuestions, 'utf8');
    const formalTemp = `${formalPath}.missing-evidence-${process.pid}.tmp`;
    const canonicalTemp = `${paths.canonicalQuestions}.missing-evidence-${process.pid}.tmp`;
    fs.writeFileSync(formalTemp, nextFormal, 'utf8');
    fs.writeFileSync(canonicalTemp, nextCanonicalText, 'utf8');
    try {
        fs.renameSync(formalTemp, formalPath);
        fs.renameSync(canonicalTemp, paths.canonicalQuestions);
    } catch (error) {
        fs.writeFileSync(formalPath, oldFormal, 'utf8');
        fs.writeFileSync(paths.canonicalQuestions, oldCanonicals, 'utf8');
        fs.rmSync(formalTemp, { force: true });
        fs.rmSync(canonicalTemp, { force: true });
        throw error;
    }
    return { schema_version: 'answer_demote_missing_evidence.v1', ok: true, demoted: true, canonical_id: canonicalId, answer_path: path.relative(root, formalPath), version: nextMetadata.version };
}

module.exports = {
    pathsFor,
    sha256,
    inferAnswerType,
    buildAnswerContext,
    renderCandidate,
    extractCodeBlocks,
    compileJava,
    parseSql,
    validateAnswerEvidence,
    validateSpecializedCandidate,
    auditOneCandidate,
    runAnswerAudit,
    atomicPromote,
    atomicDemote,
    atomicDemoteMissingEvidence,
    recordHumanReview,
    humanReviewError,
    countHumanReviewApprovals,
};
