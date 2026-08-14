'use strict';

const { addDays, isDue } = require('../../domain/review/progress-policy');
const { rankReviewRows } = require('../../domain/review/ranking-policy');
const { assertReviewPlanWriter } = require('../../ports/services/review-plan-writer');
const { createReviewQueueStateLoader } = require('./review-queue-state');

function selectPrepareRows(rows, strategy, input = {}) {
    const date = input.date;
    let selected;
    if (input.days) {
        const maxDate = addDays(date, Number(input.days || 7));
        selected = rows.filter((row) =>
            !row.progress.next_review_at || row.progress.next_review_at <= maxDate
        );
    } else {
        selected = rows.filter((row) => isDue(row.progress, date));
    }

    selected = rankReviewRows(selected, { strategy, date });

    if (input.priority) {
        selected = selected.filter((row) => row.review_priority === input.priority);
    }
    if (input.status) {
        selected = selected.filter((row) => row.progress.status === input.status);
    }
    if (input.domain) {
        selected = selected.filter((row) => row.primary_domain?.l1 === input.domain);
    }
    if (input.company) {
        selected = selected.filter((row) =>
            (row.companies || []).some((company) => company.includes(input.company))
        );
    }
    if (input.level) {
        selected = selected.filter((row) =>
            (row.levels || []).some((level) => level.includes(input.level))
        );
    }
    if (input.topic) {
        const topic = String(input.topic).toLowerCase();
        selected = selected.filter((row) =>
            row.canonical_title.toLowerCase().includes(topic)
            || (row.primary_entities || []).some((entity) =>
                String(entity).toLowerCase().includes(topic)
            )
            || row.primary_domain?.l1?.toLowerCase().includes(topic)
            || row.primary_domain?.l2?.toLowerCase().includes(topic)
        );
    }

    return selected.slice(0, Number(input.limit || 20));
}

function createReviewPrepareUseCase(dependencies = {}) {
    const loadReviewQueueState = createReviewQueueStateLoader(dependencies);
    const planWriter = assertReviewPlanWriter(dependencies.planWriter);

    return function reviewPrepare(input = {}) {
        const state = loadReviewQueueState(input);
        const target = input.target;
        if (!target) {
            throw new Error('Usage: review prepare --target <name>');
        }

        const rows = selectPrepareRows(state.rows, state.strategy, input);
        const dryRun = input.write_plan === false;
        const planPath = dryRun
            ? null
            : planWriter.write({
                target,
                date: input.date,
                rows,
                with_issues: Boolean(input.with_issues),
            });

        return {
            schema_version: 'review_prepare_result.v1',
            ok: true,
            dry_run: dryRun,
            target,
            plan_path: planPath,
            item_count: rows.length,
            rows,
        };
    };
}

module.exports = {
    selectPrepareRows,
    createReviewPrepareUseCase,
};
