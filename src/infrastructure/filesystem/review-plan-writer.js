'use strict';

const fs = require('fs');
const path = require('path');

function safeName(value) {
    return String(value || 'default')
        .toLowerCase()
        .replace(/[^a-z0-9_\-\u4e00-\u9fa5]+/g, '_')
        .replace(/^_+|_+$/g, '') || 'default';
}

function renderReviewPlan(plan = {}) {
    const rows = plan.rows || [];
    const withIssues = Boolean(plan.with_issues);
    const table = withIssues
        ? [
            '| canonical_id | priority | answer | due | issue | title |',
            '|---|---|---|---|---|---|',
            ...rows.map((row) => `| ${row.canonical_id} | ${row.review_priority} | ${row.answer_status} | ${row.progress.next_review_at || ''} | ${row.issue_url || ''} | ${row.canonical_title} |`),
        ]
        : [
            '| canonical_id | priority | answer | due | title |',
            '|---|---|---|---|---|',
            ...rows.map((row) => `| ${row.canonical_id} | ${row.review_priority} | ${row.answer_status} | ${row.progress.next_review_at || ''} | ${row.canonical_title} |`),
        ];

    return [
        `# ${plan.target}`,
        '',
        `Generated: ${plan.date}`,
        '',
        ...table,
        '',
    ].join('\n');
}

function createFsReviewPlanWriter(options = {}) {
    if (!options.root) {
        throw new Error('Filesystem review plan writer root is required');
    }
    const plansDir = options.plansDir || path.join(options.root, 'review', 'plans');

    return {
        write(plan = {}) {
            const filePath = path.join(plansDir, `${safeName(plan.target)}.md`);
            fs.mkdirSync(path.dirname(filePath), { recursive: true });
            fs.writeFileSync(filePath, renderReviewPlan(plan), 'utf8');
            return path.relative(options.root, filePath);
        },
    };
}

module.exports = {
    safeName,
    renderReviewPlan,
    createFsReviewPlanWriter,
};
