'use strict';

const path = require('path');
const { readJson } = require('./io');
const { todayString } = require('./review_store');

const DEFAULT_STRATEGY_PATH = path.resolve(__dirname, '..', '..', 'config', 'review_strategy.json');

function loadReviewStrategy(options = {}) {
    return readJson(options.strategyPath || DEFAULT_STRATEGY_PATH);
}

function daysBetween(fromDate, toDate) {
    const from = new Date(`${fromDate}T00:00:00Z`);
    const to = new Date(`${toDate || fromDate}T00:00:00Z`);
    return Math.round((to.getTime() - from.getTime()) / 86400000);
}

function scoreReviewRow(row, options = {}) {
    const strategy = options.strategy || loadReviewStrategy(options);
    const date = todayString(options);
    const progress = row.progress || {};
    const dueInDays = daysBetween(date, progress.next_review_at || date);
    const priorityScore = strategy.priority_weights?.[row.review_priority] ?? 0;
    const statusScore = strategy.status_weights?.[progress.status || 'new'] ?? 0;
    const answerScore = strategy.answer_status_weights?.[row.answer_status || 'missing'] ?? 0;
    const frequencyScore = Number(row.frequency || 0) * Number(strategy.frequency_weight || 0);
    const difficultyScore = Number(progress.difficulty || 0) * Number(strategy.difficulty_weight || 0);
    const mistakeScore = Number(progress.mistake_count || 0) * Number(strategy.mistake_weight || 0);
    const dueScore = dueInDays <= 0
        ? Number(strategy.due_bonus || 0)
        : -dueInDays * Number(strategy.upcoming_day_penalty || 0);
    return priorityScore + statusScore + answerScore + frequencyScore + difficultyScore + mistakeScore + dueScore;
}

function rankReviewRows(rows, options = {}) {
    return [...rows]
        .map((row) => ({
            ...row,
            review_score: scoreReviewRow(row, options),
        }))
        .sort((a, b) =>
            b.review_score - a.review_score
            || (a.progress?.next_review_at || '').localeCompare(b.progress?.next_review_at || '')
            || b.frequency - a.frequency
            || a.canonical_id.localeCompare(b.canonical_id)
        );
}

module.exports = {
    DEFAULT_STRATEGY_PATH,
    loadReviewStrategy,
    scoreReviewRow,
    rankReviewRows,
};
