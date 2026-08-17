'use strict';

function addDays(dateString, days) {
    const date = new Date(`${dateString}T00:00:00Z`);
    date.setUTCDate(date.getUTCDate() + days);
    return date.toISOString().slice(0, 10);
}

function defaultProgressItem(canonicalId, date) {
    return {
        canonical_id: canonicalId,
        status: 'new',
        level: 0,
        review_count: 0,
        last_reviewed_at: null,
        next_review_at: date,
        confidence: 0.5,
        difficulty: 3,
        mistake_count: 0,
        updated_at: date,
    };
}

function ensureProgressItems(progress, canonicalRecords, date) {
    const byId = new Map((progress.items || []).map((item) => [item.canonical_id, item]));
    for (const record of canonicalRecords) {
        if (!byId.has(record.canonical_id)) {
            byId.set(record.canonical_id, defaultProgressItem(record.canonical_id, date));
        }
    }
    return {
        ...progress,
        updated_at: date,
        items: [...byId.values()],
    };
}

function isDue(item, date) {
    return !item.next_review_at || item.next_review_at <= date;
}

module.exports = {
    addDays,
    defaultProgressItem,
    ensureProgressItems,
    isDue,
};
