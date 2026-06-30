'use strict';

const crypto = require('crypto');
const path = require('path');
const { readJson, writeJson } = require('./io');

const DEFAULT_ISSUE_LINKS_PATH = path.resolve(__dirname, '..', '..', 'review', 'issue_links.json');
const DEFAULT_DATE = process.env.XHS_BUILD_DATE || '2026-06-30';
const CARD_META_PREFIX = '<!-- xhs-review-card: ';
const CARD_META_SUFFIX = ' -->';

function defaultIssueLinks(options = {}) {
    return {
        schema_version: 'review_issue_links.v1',
        updated_at: options.date || DEFAULT_DATE,
        items: [],
    };
}

function loadIssueLinks(options = {}) {
    const store = readJson(options.filePath || DEFAULT_ISSUE_LINKS_PATH, defaultIssueLinks(options));
    return {
        ...defaultIssueLinks(options),
        ...store,
        items: Array.isArray(store.items) ? store.items : [],
    };
}

function saveIssueLinks(store, options = {}) {
    const sorted = {
        schema_version: 'review_issue_links.v1',
        updated_at: options.date || DEFAULT_DATE,
        items: [...(store.items || [])].sort((a, b) => a.canonical_id.localeCompare(b.canonical_id)),
    };
    writeJson(options.filePath || DEFAULT_ISSUE_LINKS_PATH, sorted);
    return sorted;
}

function issueLinkMap(store) {
    return new Map((store.items || []).map((item) => [item.canonical_id, item]));
}

function upsertIssueLink(store, link, options = {}) {
    const byId = issueLinkMap(store);
    byId.set(link.canonical_id, {
        ...byId.get(link.canonical_id),
        ...link,
        synced_at: options.date || DEFAULT_DATE,
    });
    return {
        ...store,
        updated_at: options.date || DEFAULT_DATE,
        items: [...byId.values()],
    };
}

function cardHash(card) {
    return crypto.createHash('sha256')
        .update(JSON.stringify({
            title: card.title,
            labels: card.labels,
            body: card.body,
        }))
        .digest('hex');
}

function parseMarkdownSections(content) {
    const sections = new Map();
    let current = null;
    for (const line of String(content || '').split(/\r?\n/)) {
        const heading = line.match(/^##\s+(.+?)\s*$/);
        if (heading) {
            current = heading[1].trim();
            if (!sections.has(current)) sections.set(current, []);
            continue;
        }
        if (current) sections.get(current).push(line);
    }
    return sections;
}

function stripAnswerMetadata(content) {
    return String(content || '').replace(/^<!-- xhs-answer: .*? -->\r?\n?/, '');
}

function compactMarkdown(value, options = {}) {
    const maxLines = Number(options.maxLines || 8);
    const maxChars = Number(options.maxChars || 900);
    const lines = String(value || '')
        .split(/\r?\n/)
        .map((line) => line.trimEnd())
        .filter((line, index, all) => line.trim() || (index > 0 && index < all.length - 1));
    let compact = lines.slice(0, maxLines).join('\n').trim();
    if (!compact) return 'TODO';
    if (compact.length > maxChars) compact = `${compact.slice(0, maxChars - 3).trimEnd()}...`;
    return compact;
}

function pickSection(sections, names) {
    for (const [title, lines] of sections.entries()) {
        if (names.some((name) => title.includes(name))) return compactMarkdown(lines.join('\n'));
    }
    return null;
}

function extractAnswerCardSections(answerContent) {
    const content = stripAnswerMetadata(answerContent);
    const sections = parseMarkdownSections(content);
    const fallback = content
        .split(/\r?\n/)
        .filter((line) => !line.startsWith('#'))
        .join('\n');
    return {
        conclusion: pickSection(sections, ['核心结论', '1 分钟结论', '结论']) || compactMarkdown(fallback, { maxLines: 4 }),
        details: pickSection(sections, ['关键细节', '关键要点', '细节']) || 'TODO',
        followups: pickSection(sections, ['常见追问', '追问']) || 'TODO',
    };
}

function issueTitle(record) {
    return `[Review][${record.review_priority}] ${record.canonical_id} ${record.canonical_title}`;
}

function issueLabels(record) {
    return [
        'review',
        `priority:${record.review_priority}`,
        `answer:${record.answer_status || 'missing'}`,
    ];
}

function fullAnswerLink(relativePath, options = {}) {
    if (!relativePath) return 'missing';
    if (!options.repo) return relativePath;
    const branch = options.branch || 'master';
    return `https://github.com/${options.repo}/blob/${branch}/${relativePath}`;
}

function joinLimited(values, limit = 6) {
    const items = [...new Set(values || [])].filter(Boolean).slice(0, limit);
    return items.length ? items.join(', ') : '未知';
}

function buildIssueBody(record, options = {}) {
    const metadata = {
        schema_version: 'review_issue_card.v1',
        canonical_id: record.canonical_id,
    };
    const sections = options.answerContent
        ? extractAnswerCardSections(options.answerContent)
        : {
            conclusion: '答案待补充。',
            details: 'TODO',
            followups: 'TODO',
        };
    const answerPath = options.answerRelativePath || `review/answers/${record.canonical_id}.md`;
    const answerLink = options.answerContent ? fullAnswerLink(answerPath, options) : 'missing';
    return [
        `${CARD_META_PREFIX}${JSON.stringify(metadata)}${CARD_META_SUFFIX}`,
        `# ${record.canonical_title}`,
        '',
        '## 1 分钟结论',
        '',
        sections.conclusion,
        '',
        '## 关键细节',
        '',
        sections.details,
        '',
        '## 常见追问',
        '',
        sections.followups,
        '',
        '## 复习入口',
        '',
        `- canonical_id: \`${record.canonical_id}\``,
        `- priority: \`${record.review_priority}\``,
        `- answer_status: \`${record.answer_status || 'missing'}\``,
        `- frequency: \`${record.frequency || 0}\``,
        `- companies: ${joinLimited(record.companies)}`,
        `- full answer: ${options.answerContent ? `[${answerPath}](${answerLink})` : answerLink}`,
        '',
    ].join('\n');
}

function buildIssueCard(record, options = {}) {
    const card = {
        title: issueTitle(record),
        labels: issueLabels(record),
        body: buildIssueBody(record, options),
    };
    return {
        ...card,
        body_hash: cardHash(card),
    };
}

function validateIssueLinks(store, canonicalRecords) {
    const canonicalIds = new Set(canonicalRecords.map((record) => record.canonical_id));
    const seenCanonicalIds = new Set();
    const seenIssueNumbers = new Map();
    const errors = [];
    if (store.schema_version !== 'review_issue_links.v1') {
        errors.push({ error: 'invalid_schema_version', schema_version: store.schema_version });
    }
    for (const item of store.items || []) {
        if (!item.canonical_id || !canonicalIds.has(item.canonical_id)) {
            errors.push({ error: 'unknown_canonical_id', canonical_id: item.canonical_id });
        }
        if (seenCanonicalIds.has(item.canonical_id)) {
            errors.push({ error: 'duplicate_canonical_id', canonical_id: item.canonical_id });
        }
        seenCanonicalIds.add(item.canonical_id);
        if (!item.issue_number || !item.issue_url) {
            errors.push({ error: 'missing_issue_reference', canonical_id: item.canonical_id });
        }
        if (!item.body_hash) {
            errors.push({ error: 'missing_body_hash', canonical_id: item.canonical_id });
        }
        if (item.issue_number) {
            const owner = seenIssueNumbers.get(item.issue_number);
            if (owner && owner !== item.canonical_id) {
                errors.push({ error: 'duplicate_issue_number', issue_number: item.issue_number, canonical_ids: [owner, item.canonical_id].sort() });
            }
            seenIssueNumbers.set(item.issue_number, item.canonical_id);
        }
    }
    return errors;
}

module.exports = {
    DEFAULT_ISSUE_LINKS_PATH,
    CARD_META_PREFIX,
    CARD_META_SUFFIX,
    defaultIssueLinks,
    loadIssueLinks,
    saveIssueLinks,
    issueLinkMap,
    upsertIssueLink,
    extractAnswerCardSections,
    buildIssueBody,
    buildIssueCard,
    validateIssueLinks,
};
