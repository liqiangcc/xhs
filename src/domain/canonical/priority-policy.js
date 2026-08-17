'use strict';

const PRIORITY_RANK = Object.freeze({
    P0: 0,
    P1: 1,
    P2: 2,
    P3: 3,
});

/**
 * Return the ordering rank for a canonical review priority.
 * Unknown values intentionally sort after all supported priorities so the
 * policy preserves the legacy behavior during incremental migration.
 */
function priorityRank(priority) {
    return PRIORITY_RANK[priority] ?? 9;
}

/**
 * Pick the highest review priority from the provided values.
 * Empty input falls back to P2, matching the current canonical behavior.
 */
function pickPriority(...priorities) {
    return priorities
        .filter(Boolean)
        .sort((a, b) => priorityRank(a) - priorityRank(b))[0] || 'P2';
}

/**
 * Derive review priority from observed question frequency and company spread.
 *
 * Current policy:
 * - P0 when frequency >= 5 OR distinct company count >= 4
 * - P1 when frequency >= 3
 * - P2 otherwise
 */
function computePriority(frequency, companiesLength) {
    if (frequency >= 5 || companiesLength >= 4) return 'P0';
    if (frequency >= 3) return 'P1';
    return 'P2';
}

module.exports = {
    PRIORITY_RANK,
    priorityRank,
    pickPriority,
    computePriority,
};
