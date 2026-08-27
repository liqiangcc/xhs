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
    // Promotion intentionally changes only the formal answer metadata (status,
    // quality tier and version).  The evidence remains bound to the immutable
    // candidate bytes, whose hash is copied into formal metadata at promotion.
    // Re-auditing a curated answer must therefore compare that recorded
    // candidate hash instead of the post-promotion file hash.
    const expectedCandidateHash = candidate.metadata.quality_tier === 'curated'
        ? candidate.metadata.candidate_sha256
        : sha256(candidate.content);
    if (!expectedCandidateHash || evidence.candidate_sha256 !== expectedCandidateHash) {
        errors.push({ error: 'candidate_hash_mismatch' });
    }
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
    const regex = /(?:```|~~~)(java|sql|javascript|js)\s*\n([\s\S]*?)\n(?:```|~~~)/gi;
    let match;
    while ((match = regex.exec(String(content)))) {
        blocks.push({ language: match[1].toLowerCase(), code: match[2] });
    }
    return blocks;
}

function compileJava(code) {
    const hasCompleteClass = /\b(?:public\s+)?(?:final\s+|abstract\s+)?class\s+[A-Za-z_$][\w$]*/.test(code)
        || /\b(?:public\s+)?(?:sealed\s+)?(?:interface|record|enum)\s+[A-Za-z_$][\w$]*/.test(code);
    if (!hasCompleteClass) {
        return { ok: false, error: 'java_class_required' };
    }
    const tempDir = fs.mkdtempSync(path.join(os.tmpdir(), 'xhs-answer-javac-'));
    try {
        const publicMatch = code.match(/\bpublic\s+(?:final\s+|abstract\s+)?(?:class|interface|record|enum)\s+([A-Za-z_$][\w$]*)/);
        const fallbackMatch = code.match(/\b(?:class|interface|record|enum)\s+([A-Za-z_$][\w$]*)/);
        const className = (publicMatch || fallbackMatch || [])[1] || 'Solution';
        const filePath = path.join(tempDir, `${className}.java`);
        fs.writeFileSync(filePath, code, 'utf8');
        const result = childProcess.spawnSync('javac', [filePath], { encoding: 'utf8', timeout: 20000 });
        return { ok: result.status === 0, error: result.status === 0 ? null : (result.stderr || result.stdout || 'javac_failed').slice(0, 4000) };
    } finally {
        fs.rmSync(tempDir, { recursive: true, force: true });
    }
}

function checkJavaScript(code) {
    const tempDir = fs.mkdtempSync(path.join(os.tmpdir(), 'xhs-answer-node-check-'));
    try {
        const filePath = path.join(tempDir, 'candidate.mjs');
        fs.writeFileSync(filePath, code, 'utf8');
        const result = childProcess.spawnSync(process.execPath, ['--check', filePath], { encoding: 'utf8', timeout: 15000 });
        return { ok: result.status === 0, error: result.status === 0 ? null : (result.stderr || result.stdout || 'node_check_failed').slice(0, 2000) };
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
            const validation = block.language === 'java' ? compileJava(block.code) : block.language === 'sql' ? parseSql(block.code) : checkJavaScript(block.code);
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
    const payload = readJson(setPath);
    return Array.isArray(payload) ? payload : payload.canonical_ids || payload.items || [];
}

function selectAuditCandidates(options = {}) {
    const root = options.root ? path.resolve(options.root) : DEFAULT_ROOT;
    const paths = pathsFor(root);
    let files = [];
    if (options.candidate) files = [assertPathWithin(path.resolve(options.candidate), paths.candidateAnswersDir, 'candidate')];
    else if (options.set) files = readSetIds(path.resolve(options.set)).map((id) => path.join(paths.candidateAnswersDir, `${id}.md`));
    else if (options.all) files = fs.existsSync(paths.candidateAnswersDir)
        ? fs.readdirSync(paths.candidateAnswersDir).filter((name) => name.endsWith('.md')).map((name) => path.join(paths.candidateAnswersDir, name))
        : [];
    else {
        const canonicalId = options['canonical-id'] || options.canonicalId;
        if (!canonicalId) throw new Error('Usage: answer audit --candidate <path> | --canonical-id <id> | --set <json> | --all');
        files = [path.join(paths.candidateAnswersDir, `${canonicalId}.md`)];
    }
    return [...new Set(files)];
}

function auditAnswerCandidate(options = {}) {
    const root = options.root ? path.resolve(options.root) : DEFAULT_ROOT;
    const paths = pathsFor(root);
    const files = selectAuditCandidates({ ...options, root });
    const rows = [];
    for (const filePath of files) {
        if (!fs.existsSync(filePath)) {
            rows.push({ schema_version: 'answer_audit.v1', ok: false, candidate_path: path.relative(root, filePath), error: 'candidate_missing' });
            continue;
        }
        rows.push(auditOneCandidate(filePath, { ...options, root }));
    }
    const failed = rows.filter((row) => !row.ok);
    const report = {
        schema_version: 'answer_audit_report.v1',
        ok: failed.length === 0,
        dry_run: Boolean(options.noWrite),
        candidate_count: rows.length,
        passed_count: rows.length - failed.length,
        failed_count: failed.length,
        rows,
    };
    if (!options.noWrite) {
        ensureDir(paths.candidateAuditsDir);
        const reportPath = options.report || path.join(paths.candidateAuditsDir, `audit-${Date.now()}.json`);
        writeJson(path.resolve(reportPath), report);
    }
    return report;
}

function updateCanonicalAnswerStatus(filePath, canonicalId, status) {
    const rows = readJsonl(filePath, []);
    let found = false;
    const next = rows.map((item) => {
        if (item.canonical_id !== canonicalId) return item;
        found = true;
        return { ...item, answer_status: status };
    });
    if (!found) throw new Error(`Canonical not found while updating answer status: ${canonicalId}`);
    const content = next.map((item) => stableStringify(item)).join('\n') + (next.length ? '\n' : '');
    fs.writeFileSync(filePath, content, 'utf8');
}

function createBatchSnapshot(root, canonicalId) {
    const paths = pathsFor(root);
    const tempDir = fs.mkdtempSync(path.join(os.tmpdir(), 'xhs-answer-promote-'));
    for (const relativePath of [
        'data/questions/canonical_questions.jsonl',
        'data/review/progress.jsonl',
        `review/answers/${canonicalId}.md`,
    ]) {
        const source = path.join(root, relativePath);
        const target = path.join(tempDir, relativePath);
        ensureDir(path.dirname(target));
        if (fs.existsSync(source)) fs.copyFileSync(source, target);
    }
    return tempDir;
}

function restoreBatchSnapshot(root, tempDir, canonicalId) {
    for (const relativePath of [
        'data/questions/canonical_questions.jsonl',
        'data/review/progress.jsonl',
        `review/answers/${canonicalId}.md`,
    ]) {
        const source = path.join(tempDir, relativePath);
        const target = path.join(root, relativePath);
        if (fs.existsSync(source)) fs.copyFileSync(source, target);
        else fs.rmSync(target, { force: true });
    }
}

function verifyPromotionGates(root, canonicalId, candidatePath, options = {}) {
    const checks = [];
    const runCheck = (name, fn) => {
        try {
            const output = fn();
            checks.push({ name, ok: output?.ok !== false, output });
            if (output?.ok === false) throw new Error(`${name} failed`);
        } catch (error) {
            checks.push({ name, ok: false, error: error.message });
            throw error;
        }
    };
    runCheck('candidate_audit', () => auditOneCandidate(candidatePath, { root }));
    runCheck('review_integrity', () => require('./review_integrity').checkReviewIntegrity({ root, noWrite: true }));
    runCheck('answer_validate_strict', () => require('./answer_store').validateAnswers({ root, strict: true, noWrite: true }));
    runCheck('canonical_check', () => require('./canonical_store').checkCanonicalQuestions({ root, noWrite: true }));
    runCheck('repository_validate_all', () => require('./validate_all').validateAll({ root, noWrite: true }));
    if (options.command) {
        const result = childProcess.spawnSync(options.command, { cwd: root, shell: true, encoding: 'utf8', timeout: Number(options.timeout || 120000) });
        checks.push({ name: 'type_specific_command', ok: result.status === 0, command: options.command, stdout: result.stdout?.slice(-4000), stderr: result.stderr?.slice(-4000) });
        if (result.status !== 0) throw new Error('type_specific_command failed');
    }
    return checks;
}

function promoteAnswerCandidate(options = {}) {
    const root = options.root ? path.resolve(options.root) : DEFAULT_ROOT;
    const paths = pathsFor(root);
    const canonicalId = options['canonical-id'] || options.canonicalId;
    if (!canonicalId) throw new Error('Usage: answer promote --canonical-id <id> --batch-id <id>');
    const candidatePath = path.join(paths.candidateAnswersDir, `${canonicalId}.md`);
    if (!fs.existsSync(candidatePath)) throw new Error(`Candidate missing: ${candidatePath}`);
    const candidate = readAnswerFile(candidatePath);
    const evidencePath = evidencePathFor(candidate, paths, options.evidence);
    const evidence = fs.existsSync(evidencePath) ? readJson(evidencePath) : null;
    const config = readJson(paths.qualityConfig);
    const humanGateEnabled = options.requireHuman === true || (config.promotion.require_human_review_for_pilot && countHumanReviewApprovals(paths) < config.promotion.pilot_human_review_count);
    if (humanGateEnabled) {
        const error = humanReviewError(evidence);
        if (error) throw new Error(error);
    }
    verifyPromotionGates(root, canonicalId, candidatePath, { command: options.command, timeout: options.timeout });
    if (options.noWrite) return { schema_version: 'answer_promotion.v1', ok: true, dry_run: true, canonical_id: canonicalId };
    const snapshot = createBatchSnapshot(root, canonicalId);
    try {
        const formalPath = path.join(paths.answersDir, `${canonicalId}.md`);
        const existingVersion = fs.existsSync(formalPath) ? Number(readAnswerFile(formalPath).metadata.version || 0) : 0;
        const promoted = replaceAnswerMetadata(candidate.content, {
            ...candidate.metadata,
            schema_version: 'answer.v1',
            canonical_id: canonicalId,
            version: Math.max(existingVersion + 1, Number(candidate.metadata.version || 1)),
            status: 'ready',
            updated_at: options.date || defaultDate(options),
            answer_type: candidate.metadata.answer_type,
            quality_tier: 'curated',
            candidate_sha256: evidence.candidate_sha256,
            writer_id: evidence.writer.writer_id,
            writer_version: evidence.writer.writer_version,
            reviewer_id: evidence.review.reviewer_id,
            reviewer_version: evidence.review.reviewer_version,
            promoted_at: options.date || defaultDate(options),
            promotion_batch_id: options['batch-id'] || options.batchId || null,
        });
        ensureDir(paths.answersDir);
        fs.writeFileSync(formalPath, promoted, 'utf8');
        updateCanonicalAnswerStatus(paths.canonicalQuestions, canonicalId, 'ready');
        require('./review_progress').ensureProgress({ root, canonicalId, noWrite: false });
        require('./review_integrity').checkReviewIntegrity({ root, noWrite: true });
        require('./answer_store').validateAnswers({ root, strict: true, noWrite: true });
        require('./canonical_store').checkCanonicalQuestions({ root, noWrite: true });
        require('./validate_all').validateAll({ root, noWrite: true });
        return {
            schema_version: 'answer_promotion.v1',
            ok: true,
            dry_run: false,
            canonical_id: canonicalId,
            answer_path: path.relative(root, formalPath),
            canonical_questions_path: path.relative(root, paths.canonicalQuestions),
            review_progress_path: path.relative(root, path.join(root, 'data', 'review', 'progress.jsonl')),
        };
    } catch (error) {
        restoreBatchSnapshot(root, snapshot, canonicalId);
        throw error;
    } finally {
        fs.rmSync(snapshot, { recursive: true, force: true });
    }
}

module.exports = {
    pathsFor,
    inferAnswerType,
    buildAnswerContext,
    renderCandidate,
    compileJava,
    checkJavaScript,
    parseSql,
    validateSpecializedCandidate,
    auditOneCandidate,
    auditAnswerCandidate,
    recordHumanReview,
    promoteAnswerCandidate,
};
