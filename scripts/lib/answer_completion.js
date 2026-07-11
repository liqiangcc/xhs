'use strict';

const crypto = require('crypto');
const fs = require('fs');
const path = require('path');
const { loadCanonicalQuestions } = require('./canonical_store');
const { loadQuestions } = require('./question_store');
const { answerPath, listAnswerFiles, readAnswerFile } = require('./answer_store');
const { readJson, readJsonl, writeJson, writeJsonl } = require('./io');
const { auditOneCandidate } = require('./answer_quality');
const { loadProgress, progressMap } = require('./review_store');

const DEFAULT_ROOT = path.resolve(__dirname, '..', '..');
const TYPE_ORDER = ['coding', 'mechanism', 'scenario', 'concept', 'project', 'behavior'];

function pathsFor(root = DEFAULT_ROOT) {
    return {
        canonicalQuestions: path.join(root, 'data', 'questions', 'canonical_questions.jsonl'),
        questions: path.join(root, 'data', 'questions', 'questions.jsonl'),
        answers: path.join(root, 'review', 'answers'),
        candidates: path.join(root, 'review', 'candidates', 'answers'),
        evidence: path.join(root, 'review', 'evidence'),
        typeAudit: path.join(root, 'data', 'manifests', 'quality', 'answer_type_audit.jsonl'),
        completionAudit: path.join(root, 'data', 'manifests', 'quality', 'final_answer_completion_audit.jsonl'),
        reachability: path.join(root, 'data', 'manifests', 'quality', 'question_answer_reachability.json'),
        weeklyQuality: path.join(root, 'data', 'manifests', 'quality', 'weekly_answer_quality.json'),
        weeklyPlans: path.join(root, 'review', 'plans', 'weekly_answer_quality'),
        sessions: path.join(root, 'review', 'sessions'),
        progress: path.join(root, 'review', 'progress.json'),
    };
}

function rootFor(options = {}) {
    return options.root ? path.resolve(options.root) : DEFAULT_ROOT;
}

function normalizedTypes(value) {
    return [...new Set([].concat(value || []).flatMap((item) => String(item).split(',')).map((item) => item.trim()).filter(Boolean))];
}

function isCuratedReady(answer) {
    return answer?.metadata?.status === 'ready' && answer.metadata.quality_tier === 'curated';
}

function answerMap(paths) {
    const rows = new Map();
    const errors = [];
    for (const filePath of listAnswerFiles({ answersDir: paths.answers })) {
        try {
            const answer = readAnswerFile(filePath);
            const id = answer.metadata.canonical_id;
            if (rows.has(id)) errors.push({ error: 'duplicate_answer_id', canonical_id: id });
            rows.set(id, { answer, filePath });
        } catch (error) {
            errors.push({ error: 'invalid_answer_file', file: filePath, detail: error.message });
        }
    }
    return { rows, errors };
}

function evidenceFor(paths, canonicalId) {
    const filePath = path.join(paths.evidence, `${canonicalId}.json`);
    if (!fs.existsSync(filePath)) return { filePath, evidence: null, error: null };
    try {
        return { filePath, evidence: readJson(filePath), error: null };
    } catch (error) {
        return { filePath, evidence: null, error: error.message };
    }
}

function typeMap(paths) {
    return new Map(readJsonl(paths.typeAudit, []).map((row) => [row.canonical_id, row.answer_type]));
}

function queueStatus(options = {}) {
    const root = rootFor(options);
    const paths = pathsFor(root);
    const types = normalizedTypes(options.type);
    const requestedTypes = types.length ? new Set(types) : null;
    const canonicalRows = loadCanonicalQuestions({ filePath: paths.canonicalQuestions });
    const answerRows = answerMap(paths).rows;
    const typesByCanonical = typeMap(paths);
    const rows = canonicalRows.map((canonical) => {
        const stored = answerRows.get(canonical.canonical_id);
        const answer = stored?.answer || null;
        const answerType = typesByCanonical.get(canonical.canonical_id) || answer?.metadata?.answer_type || null;
        const curatedReady = isCuratedReady(answer);
        return {
            canonical_id: canonical.canonical_id,
            answer_type: answerType,
            answer_path: stored ? path.relative(root, stored.filePath) : null,
            answer_status: answer?.metadata?.status || 'missing',
            quality_tier: answer?.metadata?.quality_tier || null,
            status: curatedReady ? 'complete' : 'queued',
        };
    }).filter((row) => !requestedTypes || requestedTypes.has(row.answer_type));
    const remaining = rows.filter((row) => row.status !== 'complete');
    const unknownTypes = types.filter((type) => !TYPE_ORDER.includes(type));
    return {
        schema_version: 'answer_queue_status.v1',
        ok: unknownTypes.length === 0 && (!options['expect-empty'] || remaining.length === 0),
        requested_types: types,
        unknown_types: unknownTypes,
        total_count: rows.length,
        complete_count: rows.length - remaining.length,
        remaining_count: remaining.length,
        remaining: options.full ? remaining : remaining.slice(0, 100),
        remaining_sample_truncated: !options.full && remaining.length > 100,
    };
}

function completionRows(options = {}) {
    const root = rootFor(options);
    const paths = pathsFor(root);
    const canonicals = loadCanonicalQuestions({ filePath: paths.canonicalQuestions });
    const questions = loadQuestions({ filePath: paths.questions });
    const validByCanonical = new Map();
    for (const question of questions.filter((question) => question.is_valid_for_library !== false)) {
        if (!validByCanonical.has(question.canonical_id)) validByCanonical.set(question.canonical_id, []);
        validByCanonical.get(question.canonical_id).push(question);
    }
    const { rows: answers, errors: answerFileErrors } = answerMap(paths);
    const types = typeMap(paths);
    const progress = progressMap(loadProgress({ progressPath: paths.progress }));
    const rows = canonicals.map((canonical) => {
        const errors = [];
        const stored = answers.get(canonical.canonical_id);
        const answer = stored?.answer || null;
        const sourceQuestions = validByCanonical.get(canonical.canonical_id) || [];
        if (!answer) errors.push('missing_answer');
        if (answer && !isCuratedReady(answer)) errors.push('not_curated_ready');
        if (canonical.answer_status !== 'ready') errors.push('canonical_not_ready');
        if (answer && canonical.answer_status !== answer.metadata.status) errors.push('canonical_answer_status_mismatch');
        if (sourceQuestions.length === 0) errors.push('canonical_without_valid_question');
        const canonicalQuestionIds = new Set(canonical.question_ids || []);
        if (sourceQuestions.some((question) => !canonicalQuestionIds.has(question.question_id))) errors.push('canonical_question_membership_mismatch');
        const evidenceInfo = evidenceFor(paths, canonical.canonical_id);
        if (!evidenceInfo.evidence) errors.push(evidenceInfo.error ? 'invalid_evidence' : 'missing_evidence');
        let audit = null;
        if (answer && isCuratedReady(answer) && evidenceInfo.evidence) {
            try {
                audit = auditOneCandidate(stored.filePath, { root, allowFormal: true, evidence: evidenceInfo.filePath });
                if (!audit.ok) errors.push('answer_audit_failed');
            } catch (error) {
                errors.push('answer_audit_error');
            }
        }
        const progressItem = progress.get(canonical.canonical_id) || null;
        if (!progressItem) errors.push('missing_review_progress');
        return {
            schema_version: 'final_answer_completion_row.v1',
            canonical_id: canonical.canonical_id,
            question_count: sourceQuestions.length,
            answer_path: stored ? path.relative(root, stored.filePath) : null,
            answer_status: answer?.metadata?.status || 'missing',
            quality_tier: answer?.metadata?.quality_tier || null,
            answer_type: types.get(canonical.canonical_id) || answer?.metadata?.answer_type || null,
            evidence_path: evidenceInfo.evidence ? path.relative(root, evidenceInfo.filePath) : null,
            audit_score: audit?.total_score ?? null,
            audit_passed: audit?.ok ?? false,
            last_reviewed_at: progressItem?.last_reviewed_at || null,
            review_progress_present: Boolean(progressItem),
            ok: errors.length === 0,
            errors,
        };
    });
    const canonicalIds = new Set(canonicals.map((canonical) => canonical.canonical_id));
    const orphanAnswers = [...answers.keys()].filter((id) => !canonicalIds.has(id)).sort();
    const orphanEvidence = fs.existsSync(paths.evidence)
        ? fs.readdirSync(paths.evidence).filter((name) => name.endsWith('.json') && !name.endsWith('.review.json'))
            .map((name) => path.basename(name, '.json')).filter((id) => !canonicalIds.has(id)).sort()
        : [];
    return { root, paths, rows, answer_file_errors: answerFileErrors, orphan_answers: orphanAnswers, orphan_evidence: orphanEvidence };
}

function closure(options = {}) {
    const data = completionRows(options);
    const incomplete = data.rows.filter((row) => !row.ok);
    const ok = incomplete.length === 0 && data.answer_file_errors.length === 0 && data.orphan_answers.length === 0 && data.orphan_evidence.length === 0;
    if (options.audit && !options.noWrite) writeJsonl(data.paths.completionAudit, data.rows);
    return {
        schema_version: options.audit ? 'answer_closure_audit.v1' : 'answer_closure_check.v1',
        ok,
        dry_run: Boolean(options.noWrite),
        canonical_count: data.rows.length,
        completed_count: data.rows.length - incomplete.length,
        incomplete_count: incomplete.length,
        answer_file_errors: data.answer_file_errors,
        orphan_answers: data.orphan_answers,
        orphan_evidence: data.orphan_evidence,
        rows: options.full ? data.rows : incomplete.slice(0, 100),
        incomplete_sample_truncated: !options.full && incomplete.length > 100,
        output: options.audit ? path.relative(data.root, data.paths.completionAudit) : null,
    };
}

function reachability(options = {}) {
    const root = rootFor(options);
    const paths = pathsFor(root);
    const completion = completionRows({ root });
    const completionById = new Map(completion.rows.map((row) => [row.canonical_id, row]));
    const canonicals = loadCanonicalQuestions({ filePath: paths.canonicalQuestions });
    const canonicalById = new Map(canonicals.map((canonical) => [canonical.canonical_id, canonical]));
    const seenQuestionIds = new Set();
    const rows = loadQuestions({ filePath: paths.questions }).filter((question) => question.is_valid_for_library !== false).map((question) => {
        const errors = [];
        const canonical = canonicalById.get(question.canonical_id);
        const completionRow = completionById.get(question.canonical_id);
        if (seenQuestionIds.has(question.question_id)) errors.push('duplicate_valid_question_id');
        seenQuestionIds.add(question.question_id);
        if (!canonical) errors.push('missing_canonical');
        if (canonical && !(canonical.question_ids || []).includes(question.question_id)) errors.push('canonical_question_membership_mismatch');
        if (!completionRow?.ok) errors.push('canonical_not_curated_ready');
        return {
            schema_version: 'question_answer_reachability_row.v1',
            question_id: question.question_id,
            canonical_id: question.canonical_id || null,
            answer_path: completionRow?.answer_path || null,
            evidence_path: completionRow?.evidence_path || null,
            review_progress_present: Boolean(completionRow?.review_progress_present),
            ok: errors.length === 0,
            errors,
        };
    });
    const failed = rows.filter((row) => !row.ok);
    const result = {
        schema_version: 'question_answer_reachability.v1', ok: failed.length === 0,
        dry_run: Boolean(options.noWrite), valid_question_count: rows.length,
        reachable_count: rows.length - failed.length, unreachable_count: failed.length,
        rows: options.full ? rows : failed,
    };
    if (!options.noWrite) writeJson(paths.reachability, result);
    return result;
}

function isoWeek(value) {
    const date = new Date(`${value}T00:00:00Z`);
    const day = date.getUTCDay() || 7;
    date.setUTCDate(date.getUTCDate() + 4 - day);
    const yearStart = new Date(Date.UTC(date.getUTCFullYear(), 0, 1));
    const week = Math.ceil((((date - yearStart) / 86400000) + 1) / 7);
    return `${date.getUTCFullYear()}-W${String(week).padStart(2, '0')}`;
}

function assertWeek(week) {
    if (!/^\d{4}-W\d{2}$/.test(week || '')) throw new Error('week must use YYYY-Www');
    return week;
}

function deterministicSort(week, rows) {
    return [...rows].sort((a, b) => crypto.createHash('sha256').update(`${week}:${a.canonical_id}`).digest('hex')
        .localeCompare(crypto.createHash('sha256').update(`${week}:${b.canonical_id}`).digest('hex')) || a.canonical_id.localeCompare(b.canonical_id));
}

function weeklySample(week, options = {}) {
    assertWeek(week);
    const root = rootFor(options);
    const paths = pathsFor(root);
    const types = typeMap(paths);
    const answers = answerMap(paths).rows;
    const ready = loadCanonicalQuestions({ filePath: paths.canonicalQuestions }).filter((canonical) => isCuratedReady(answers.get(canonical.canonical_id)?.answer));
    const selected = [];
    const selectedIds = new Set();
    const availability = {};
    for (const type of TYPE_ORDER) {
        const candidates = deterministicSort(week, ready.filter((canonical) => types.get(canonical.canonical_id) === type));
        availability[type] = candidates.length;
        for (const canonical of candidates.slice(0, 5)) { selected.push({ canonical_id: canonical.canonical_id, answer_type: type }); selectedIds.add(canonical.canonical_id); }
    }
    for (const canonical of deterministicSort(week, ready).filter((canonical) => !selectedIds.has(canonical.canonical_id)).slice(0, Math.max(0, 60 - selected.length))) {
        selected.push({ canonical_id: canonical.canonical_id, answer_type: types.get(canonical.canonical_id) || null });
    }
    const plan = { schema_version: 'weekly_answer_quality_sample.v1', week, sample_size: selected.length, minimum_per_type: 5, availability, items: selected };
    const planPath = path.join(paths.weeklyPlans, `${week}.json`);
    const existing = fs.existsSync(planPath) ? readJson(planPath) : null;
    const sufficient = selected.length >= 60 && TYPE_ORDER.every((type) => availability[type] >= 5);
    const matchesExisting = Boolean(existing) && JSON.stringify(existing) === JSON.stringify(plan);
    if (!options.noWrite && !options.check) writeJson(planPath, plan);
    return { ...plan, ok: sufficient && (!options.check || matchesExisting), dry_run: Boolean(options.noWrite), plan_path: path.relative(root, planPath), plan_exists: Boolean(existing), plan_matches: matchesExisting };
}

function previousWeeks(endWeek, count) {
    const [year, number] = endWeek.match(/^(\d{4})-W(\d{2})$/).slice(1).map(Number);
    const anchor = new Date(Date.UTC(year, 0, 4 + (number - 1) * 7));
    return Array.from({ length: count }, (_, index) => {
        const date = new Date(anchor);
        date.setUTCDate(date.getUTCDate() - (count - 1 - index) * 7);
        return isoWeek(date.toISOString().slice(0, 10));
    });
}

function eventsForWeek(paths, week) {
    if (!fs.existsSync(paths.sessions)) return [];
    const events = [];
    for (const name of fs.readdirSync(paths.sessions).filter((name) => name.endsWith('.json')).sort()) {
        try {
            const session = readJson(path.join(paths.sessions, name));
            if (isoWeek(session.date || '') !== week) continue;
            for (const event of session.events || []) events.push(event);
        } catch (_) { /* review integrity reports malformed files separately */ }
    }
    return events;
}

function stability(options = {}) {
    const root = rootFor(options);
    const paths = pathsFor(root);
    const weeks = Number(options.weeks || 1);
    if (!Number.isInteger(weeks) || weeks < 1) throw new Error('weeks must be a positive integer');
    const endWeek = assertWeek(options.week || isoWeek(new Date().toISOString().slice(0, 10)));
    const historical = readJson(paths.weeklyQuality, { schema_version: 'weekly_answer_quality.v1', weeks: [] });
    const snapshots = new Map((historical.weeks || []).map((row) => [row.week, row]));
    const reports = previousWeeks(endWeek, weeks).map((week) => {
        const planPath = path.join(paths.weeklyPlans, `${week}.json`);
        const plan = fs.existsSync(planPath) ? readJson(planPath) : null;
        const events = eventsForWeek(paths, week);
        const byId = new Map(events.map((event) => [event.canonical_id, event]));
        const missing = (plan?.items || []).filter((item) => !byId.has(item.canonical_id)).map((item) => item.canonical_id);
        const invalidOral = (plan?.items || []).filter((item) => {
            const event = byId.get(item.canonical_id);
            return event && (event.oral_version !== 'one_minute' || event.followup_answered !== true);
        }).map((item) => item.canonical_id);
        const hardFailures = events.filter((event) => event.hard_failure === true || (event.hard_failures || []).length > 0).map((event) => event.canonical_id);
        const unresolvedFeedback = events.filter((event) => (event.quality_defects || []).length > 0 && !event.feedback_closed_at).map((event) => event.canonical_id);
        const snapshot = snapshots.get(week) || null;
        const errors = [];
        if (!plan || plan.sample_size < 60 || TYPE_ORDER.some((type) => plan.availability?.[type] < 5)) errors.push('invalid_or_missing_sample');
        if (missing.length) errors.push('missing_review_events');
        if (invalidOral.length) errors.push('missing_one_minute_or_followup');
        if (hardFailures.length) errors.push('hard_failure_recorded');
        if (unresolvedFeedback.length) errors.push('unresolved_feedback');
        if (!snapshot) errors.push('missing_weekly_snapshot');
        return { week, ok: errors.length === 0, sample_size: plan?.sample_size || 0, missing_review_count: missing.length, invalid_oral_count: invalidOral.length, hard_failure_count: hardFailures.length, unresolved_feedback_count: unresolvedFeedback.length, curated_ready_count: snapshot?.curated_ready_count ?? null, errors };
    });
    const regression = reports.some((report, index) => index > 0 && (report.curated_ready_count === null || report.curated_ready_count < reports[index - 1].curated_ready_count));
    const ok = reports.every((report) => report.ok) && (!options['require-zero-hard-fail'] || reports.every((report) => report.hard_failure_count === 0)) && (!options['require-no-regression'] || !regression);
    const result = { schema_version: 'answer_stability_report.v1', ok, dry_run: Boolean(options.noWrite), weeks, end_week: endWeek, regression_detected: regression, reports };
    if (!options.noWrite) {
        const current = reports[reports.length - 1];
        const nextWeeks = [...snapshots.values()].filter((row) => row.week !== current.week);
        nextWeeks.push({ week: current.week, curated_ready_count: current.curated_ready_count, hard_failure_count: current.hard_failure_count, reviewed_count: current.sample_size - current.missing_review_count, generated_at: new Date().toISOString().slice(0, 10) });
        writeJson(paths.weeklyQuality, { schema_version: 'weekly_answer_quality.v1', weeks: nextWeeks.sort((a, b) => a.week.localeCompare(b.week)) });
    }
    return result;
}

module.exports = { queueStatus, closure, reachability, weeklySample, stability, completionRows, pathsFor };
