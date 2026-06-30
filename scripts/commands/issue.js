#!/usr/bin/env node
'use strict';

const fs = require('fs');
const os = require('os');
const path = require('path');
const { spawnSync } = require('child_process');
const { loadCanonicalQuestions } = require('../lib/canonical_store');
const { answerPath, readAnswerFile } = require('../lib/answer_store');
const {
    loadIssueLinks,
    saveIssueLinks,
    issueLinkMap,
    upsertIssueLink,
    buildIssueCard,
    validateIssueLinks,
    isManagedLabel,
    labelDefinition,
    labelValue,
} = require('../lib/issue_store');
const { loadProgress, progressMap } = require('../lib/review_store');
const { writeRunManifest } = require('../lib/run_manifest');
const { applyGlobalBooleanOption } = require('../lib/cli_options');

const DEFAULT_ROOT = path.resolve(__dirname, '..', '..');
const DEFAULT_REPO = 'liqiangcc/xhs';
const DEFAULT_BUILD_DATE = process.env.XHS_BUILD_DATE || '2026-06-30';

function defaultPaths(root) {
    return {
        canonicalQuestions: path.join(root, 'data', 'questions', 'canonical_questions.jsonl'),
        answersDir: path.join(root, 'review', 'answers'),
        issueLinksPath: path.join(root, 'review', 'issue_links.json'),
        progressPath: path.join(root, 'review', 'progress.json'),
    };
}

function parseArgs(argv) {
    const args = argv.slice(2);
    const command = args[0];
    const options = { _: [] };
    const booleanFlags = new Set(['apply', 'allow-missing', 'help']);
    for (let index = 1; index < args.length; index++) {
        const arg = args[index];
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
        'Usage: node scripts/xhs.js issue <render|sync|check> [options]',
        '',
        'Commands:',
        '  render --canonical-id <id> [--repo <owner/repo>] [--allow-missing]',
        '  sync --canonical-id <id> [--repo <owner/repo>] [--apply] [--allow-missing]',
        '  sync [--priority <P0|P1|P2|P3>] [--answer-status <status>] [--repo <owner/repo>] [--apply]',
        '  check',
        '',
        'Options:',
        '  --noWrite     Print only; do not write the run manifest',
        '  --noManifest  Do not write the run manifest',
    ].join('\n'));
}

function defaultGhRunner(args) {
    const result = spawnSync('gh', args, { encoding: 'utf8' });
    if (result.status !== 0) {
        const message = (result.stderr || result.stdout || '').trim() || `gh exited with status ${result.status}`;
        throw new Error(message);
    }
    return (result.stdout || '').trim();
}

function selectRecords(records, options = {}) {
    let selected = records;
    if (options['canonical-id']) {
        selected = selected.filter((record) => record.canonical_id === options['canonical-id']);
        if (!selected.length) throw new Error(`Canonical not found: ${options['canonical-id']}`);
    }
    if (options.priority) selected = selected.filter((record) => record.review_priority === options.priority);
    if (options['answer-status']) selected = selected.filter((record) => record.answer_status === options['answer-status']);
    return selected.sort((a, b) =>
        a.review_priority.localeCompare(b.review_priority)
        || a.canonical_id.localeCompare(b.canonical_id)
    );
}

function loadAnswerForRecord(record, paths, options = {}) {
    const filePath = answerPath(record.canonical_id, { answersDir: paths.answersDir });
    if (!fs.existsSync(filePath)) {
        if (options['allow-missing']) return null;
        throw new Error(`Answer missing for ${record.canonical_id}; use --allow-missing to render a placeholder`);
    }
    const answer = readAnswerFile(filePath);
    if (answer.metadata.canonical_id !== record.canonical_id) {
        throw new Error(`Answer metadata mismatch for ${record.canonical_id}: ${answer.metadata.canonical_id}`);
    }
    return {
        filePath,
        relativePath: path.relative(options.root || DEFAULT_ROOT, filePath),
        content: answer.content,
        status: answer.metadata.status || 'draft',
    };
}

function renderCard(record, paths, options = {}) {
    const answer = loadAnswerForRecord(record, paths, options);
    const effectiveRecord = answer ? { ...record, answer_status: answer.status } : record;
    return buildIssueCard(effectiveRecord, {
        repo: options.repo,
        branch: options.branch || 'master',
        answerContent: answer?.content,
        answerRelativePath: answer?.relativePath,
        progress: options.progress || null,
    });
}

function ensureLabels(repo, labels, runner) {
    for (const label of labels) {
        const definition = labelDefinition(label);
        runner([
            'label',
            'create',
            label,
            '--repo',
            repo,
            '--description',
            definition.description,
            '--color',
            definition.color,
            '--force',
        ]);
    }
}

function currentIssueLabels(repo, issueNumber, runner) {
    const output = runner([
        'issue',
        'view',
        String(issueNumber),
        '--repo',
        repo,
        '--json',
        'labels',
    ]);
    const parsed = JSON.parse(output || '{}');
    return (parsed.labels || []).map((label) => label.name).filter(Boolean);
}

function withBodyFile(body, callback) {
    const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'xhs-issue-'));
    const filePath = path.join(dir, 'body.md');
    try {
        fs.writeFileSync(filePath, body, 'utf8');
        return callback(filePath);
    } finally {
        fs.rmSync(dir, { recursive: true, force: true });
    }
}

function parseIssueUrl(stdout) {
    const line = String(stdout || '').split(/\r?\n/).find((item) => /^https?:\/\//.test(item.trim()));
    const issueUrl = line ? line.trim() : '';
    const match = issueUrl.match(/\/issues\/(\d+)(?:$|[?#])/);
    if (!issueUrl || !match) throw new Error(`Unable to parse issue URL from gh output: ${stdout}`);
    return {
        issue_url: issueUrl,
        issue_number: Number(match[1]),
    };
}

function createIssue(repo, card, runner) {
    return withBodyFile(card.body, (bodyFile) => {
        const args = [
            'issue',
            'create',
            '--repo',
            repo,
            '--title',
            card.title,
            '--body-file',
            bodyFile,
        ];
        for (const label of card.labels) args.push('--label', label);
        return parseIssueUrl(runner(args));
    });
}

function updateIssue(repo, issueNumber, card, runner, options = {}) {
    const currentLabels = currentIssueLabels(repo, issueNumber, runner);
    const desiredLabels = new Set(card.labels);
    const labelsToRemove = currentLabels
        .filter((label) => isManagedLabel(label) && !desiredLabels.has(label))
        .sort();
    const labelsToAdd = card.labels
        .filter((label) => !currentLabels.includes(label))
        .sort();
    const bodyChanged = options.bodyChanged !== false;
    if (!bodyChanged && labelsToRemove.length === 0 && labelsToAdd.length === 0) {
        return { changed: false, labels_added: [], labels_removed: [] };
    }
    return withBodyFile(card.body, (bodyFile) => {
        const args = [
            'issue',
            'edit',
            String(issueNumber),
            '--repo',
            repo,
        ];
        if (bodyChanged) args.push('--title', card.title, '--body-file', bodyFile);
        for (const label of labelsToRemove) args.push('--remove-label', label);
        for (const label of labelsToAdd) args.push('--add-label', label);
        runner(args);
        return {
            changed: true,
            labels_added: labelsToAdd,
            labels_removed: labelsToRemove,
        };
    });
}

function answerStatusFromCard(card) {
    return labelValue(card.labels, 'answer:', 'missing');
}

function reviewStatusFromCard(card) {
    return labelValue(card.labels, 'review:', 'new');
}

function runRender(options = {}) {
    const root = options.root ? path.resolve(options.root) : DEFAULT_ROOT;
    const paths = defaultPaths(root);
    const canonicalId = options['canonical-id'];
    if (!canonicalId) throw new Error('Usage: issue render --canonical-id <id>');
    const records = loadCanonicalQuestions({ filePath: paths.canonicalQuestions });
    const record = records.find((item) => item.canonical_id === canonicalId);
    if (!record) throw new Error(`Canonical not found: ${canonicalId}`);
    const byProgress = progressMap(loadProgress({ progressPath: paths.progressPath, date: options.date || DEFAULT_BUILD_DATE }));
    const card = renderCard(record, paths, {
        ...options,
        root,
        repo: options.repo || DEFAULT_REPO,
        progress: byProgress.get(record.canonical_id),
    });
    return {
        schema_version: 'issue_render_result.v1',
        ok: true,
        canonical_id: canonicalId,
        ...card,
    };
}

function runSync(options = {}, dependencies = {}) {
    const root = options.root ? path.resolve(options.root) : DEFAULT_ROOT;
    const repo = options.repo || DEFAULT_REPO;
    const apply = Boolean(options.apply);
    const runner = dependencies.runner || defaultGhRunner;
    const paths = defaultPaths(root);
    const records = selectRecords(loadCanonicalQuestions({ filePath: paths.canonicalQuestions }), options);
    const byProgress = progressMap(loadProgress({ progressPath: paths.progressPath, date: options.date || DEFAULT_BUILD_DATE }));
    let store = loadIssueLinks({ filePath: paths.issueLinksPath, date: options.date || DEFAULT_BUILD_DATE });
    const links = issueLinkMap(store);
    const rows = [];
    const errors = [];
    let storeChanged = false;

    for (const record of records) {
        let card;
        try {
            card = renderCard(record, paths, {
                ...options,
                root,
                repo,
                progress: byProgress.get(record.canonical_id),
            });
        } catch (error) {
            if (!options['allow-missing'] && /Answer missing/.test(error.message)) {
                rows.push({
                    canonical_id: record.canonical_id,
                    action: 'skip_missing_answer',
                    issue_url: links.get(record.canonical_id)?.issue_url || null,
                });
                continue;
            }
            errors.push({ canonical_id: record.canonical_id, error: error.message });
            continue;
        }

        const existing = links.get(record.canonical_id);
        let action = existing ? (existing.body_hash === card.body_hash ? 'noop' : 'update') : 'create';
        let issue = existing ? {
            issue_number: existing.issue_number,
            issue_url: existing.issue_url,
        } : null;
        let labelUpdate = null;

        try {
            if (apply && action === 'create') {
                ensureLabels(repo, card.labels, runner);
                issue = createIssue(repo, card, runner);
                store = upsertIssueLink(store, {
                    canonical_id: record.canonical_id,
                    issue_number: issue.issue_number,
                    issue_url: issue.issue_url,
                    answer_status: answerStatusFromCard(card),
                    review_status: reviewStatusFromCard(card),
                    labels: card.labels,
                    body_hash: card.body_hash,
                }, { date: options.date || DEFAULT_BUILD_DATE });
                storeChanged = true;
                links.set(record.canonical_id, {
                    canonical_id: record.canonical_id,
                    issue_number: issue.issue_number,
                    issue_url: issue.issue_url,
                    answer_status: answerStatusFromCard(card),
                    review_status: reviewStatusFromCard(card),
                    labels: card.labels,
                    body_hash: card.body_hash,
                });
            } else if (apply && existing) {
                ensureLabels(repo, card.labels, runner);
                labelUpdate = updateIssue(repo, existing.issue_number, card, runner, { bodyChanged: action === 'update' });
                if (action === 'noop' && labelUpdate.changed) action = 'sync_labels';
                if (action !== 'noop') {
                    store = upsertIssueLink(store, {
                        canonical_id: record.canonical_id,
                        issue_number: issue.issue_number,
                        issue_url: issue.issue_url,
                        answer_status: answerStatusFromCard(card),
                        review_status: reviewStatusFromCard(card),
                        labels: card.labels,
                        body_hash: card.body_hash,
                    }, { date: options.date || DEFAULT_BUILD_DATE });
                    storeChanged = true;
                    links.set(record.canonical_id, {
                        canonical_id: record.canonical_id,
                        issue_number: issue.issue_number,
                        issue_url: issue.issue_url,
                        answer_status: answerStatusFromCard(card),
                        review_status: reviewStatusFromCard(card),
                        labels: card.labels,
                        body_hash: card.body_hash,
                    });
                }
            }
            rows.push({
                canonical_id: record.canonical_id,
                action,
                applied: apply && action !== 'noop',
                issue_number: issue?.issue_number || null,
                issue_url: issue?.issue_url || null,
                labels: card.labels,
                labels_added: labelUpdate?.labels_added || [],
                labels_removed: labelUpdate?.labels_removed || [],
                body_hash: card.body_hash,
            });
        } catch (error) {
            errors.push({ canonical_id: record.canonical_id, error: error.message });
        }
    }

    if (apply && storeChanged) {
        store = saveIssueLinks(store, { filePath: paths.issueLinksPath, date: options.date || DEFAULT_BUILD_DATE });
    }

    return {
        schema_version: 'issue_sync_result.v1',
        ok: errors.length === 0,
        applied: apply,
        repo,
        selected_count: records.length,
        synced_count: rows.filter((row) => row.applied).length,
        skipped_count: rows.filter((row) => row.action === 'skip_missing_answer').length,
        rows,
        errors,
    };
}

function runCheck(options = {}) {
    const root = options.root ? path.resolve(options.root) : DEFAULT_ROOT;
    const paths = defaultPaths(root);
    const records = loadCanonicalQuestions({ filePath: paths.canonicalQuestions });
    const store = loadIssueLinks({ filePath: paths.issueLinksPath, date: options.date || DEFAULT_BUILD_DATE });
    const errors = validateIssueLinks(store, records);
    return {
        schema_version: 'issue_check_result.v1',
        ok: errors.length === 0,
        link_count: store.items.length,
        error_count: errors.length,
        errors,
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
        if (command === 'render') result = runRender(options);
        else if (command === 'sync') result = runSync(options);
        else if (command === 'check') result = runCheck(options);
        else throw new Error(`Unknown issue command: ${command}`);
        writeRunManifest(options.root ? path.resolve(options.root) : DEFAULT_ROOT, `issue_${command}`, result, options);
        console.log(JSON.stringify(result, null, 2));
        return result.ok === false ? 1 : 0;
    } catch (error) {
        console.error(error.message);
        return 1;
    }
}

if (require.main === module) {
    process.exitCode = main(process.argv);
}

module.exports = {
    runRender,
    runSync,
    runCheck,
    main,
};
