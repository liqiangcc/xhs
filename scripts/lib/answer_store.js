'use strict';

const fs = require('fs');
const path = require('path');
const { ensureDir } = require('./io');

const DEFAULT_ANSWERS_DIR = path.resolve(__dirname, '..', '..', 'review', 'answers');
const META_PREFIX = '<!-- xhs-answer: ';
const META_SUFFIX = ' -->';

function answerPath(canonicalId, options = {}) {
    return path.join(options.answersDir || DEFAULT_ANSWERS_DIR, `${canonicalId}.md`);
}

function parseAnswerMetadata(content, filePath = '') {
    const firstLine = String(content || '').split(/\r?\n/, 1)[0] || '';
    if (!firstLine.startsWith(META_PREFIX) || !firstLine.endsWith(META_SUFFIX)) {
        throw new Error(`Missing xhs-answer metadata${filePath ? ` in ${filePath}` : ''}`);
    }
    const json = firstLine.slice(META_PREFIX.length, -META_SUFFIX.length);
    return JSON.parse(json);
}

function readAnswerFile(filePath) {
    const content = fs.readFileSync(filePath, 'utf8');
    return {
        filePath,
        metadata: parseAnswerMetadata(content, filePath),
        content,
    };
}

function listAnswerFiles(options = {}) {
    const dir = options.answersDir || DEFAULT_ANSWERS_DIR;
    if (!fs.existsSync(dir)) return [];
    return fs.readdirSync(dir)
        .filter((file) => file.endsWith('.md'))
        .sort()
        .map((file) => path.join(dir, file));
}

function buildAnswerTemplate(record, options = {}) {
    const metadata = {
        schema_version: 'answer.v1',
        canonical_id: record.canonical_id,
        version: Number(options.version || 1),
        status: options.status || 'draft',
        updated_at: options.date || '2026-06-30',
    };
    return [
        `${META_PREFIX}${JSON.stringify(metadata)}${META_SUFFIX}`,
        `# ${record.canonical_title}`,
        '',
        '## 核心结论',
        '',
        'TODO',
        '',
        '## 1 分钟版',
        '',
        'TODO',
        '',
        '## 3 分钟版',
        '',
        'TODO',
        '',
        '## 关键细节',
        '',
        '- TODO',
        '',
        '## 原理机制',
        '',
        '- TODO',
        '',
        '## 项目经验版',
        '',
        'TODO',
        '',
        '## 常见追问',
        '',
        '- TODO',
        '',
        '## 易错点',
        '',
        '- TODO',
        '',
    ].join('\n');
}

function writeAnswerTemplate(record, options = {}) {
    const filePath = answerPath(record.canonical_id, options);
    if (fs.existsSync(filePath) && !options.overwrite) {
        return { created: false, filePath };
    }
    ensureDir(path.dirname(filePath));
    fs.writeFileSync(filePath, buildAnswerTemplate(record, options), 'utf8');
    return { created: true, filePath };
}

function statusByCanonicalId(options = {}) {
    const statuses = new Map();
    for (const filePath of listAnswerFiles(options)) {
        const answer = readAnswerFile(filePath);
        statuses.set(answer.metadata.canonical_id, answer.metadata.status || 'draft');
    }
    return statuses;
}

module.exports = {
    DEFAULT_ANSWERS_DIR,
    answerPath,
    parseAnswerMetadata,
    readAnswerFile,
    listAnswerFiles,
    buildAnswerTemplate,
    writeAnswerTemplate,
    statusByCanonicalId,
};
