'use strict';

function sorted(values) {
    return [...values].sort((a, b) => String(a).localeCompare(String(b)));
}

function evaluateReviewIntegrity(input = {}) {
    const canonicalRecords = input.canonical_records || [];
    const progress = input.progress || { items: [] };
    const sessionSources = input.session_sources || [];
    const canonicalIds = new Set(canonicalRecords.map((record) => record.canonical_id));
    const occurrences = new Map();
    const malformedProgressItems = [];

    for (const [index, item] of (progress.items || []).entries()) {
        const canonicalId = item?.canonical_id;
        if (!canonicalId || typeof canonicalId !== 'string') {
            malformedProgressItems.push({ index, canonical_id: canonicalId || null });
            continue;
        }
        occurrences.set(canonicalId, (occurrences.get(canonicalId) || 0) + 1);
    }

    const duplicateProgressCanonicalIds = [...occurrences.entries()]
        .filter(([, count]) => count > 1)
        .map(([canonical_id, count]) => ({ canonical_id, count }))
        .sort((a, b) => a.canonical_id.localeCompare(b.canonical_id));
    const staleProgressCanonicalIds = sorted(
        [...occurrences.keys()].filter((canonicalId) => !canonicalIds.has(canonicalId)),
    );
    const missingProgressCanonicalIds = sorted(
        [...canonicalIds].filter((canonicalId) => !occurrences.has(canonicalId)),
    );

    const staleSessionEvents = [];
    for (const source of sessionSources) {
        if (source?.parse_error) {
            staleSessionEvents.push({
                source: source.source,
                index: null,
                canonical_id: null,
                reason: source.parse_error,
            });
            continue;
        }
        for (const [index, event] of (source?.session?.events || []).entries()) {
            if (!event?.canonical_id || !canonicalIds.has(event.canonical_id)) {
                staleSessionEvents.push({
                    source: source.source,
                    index,
                    canonical_id: event?.canonical_id || null,
                    reason: event?.canonical_id ? 'unknown_canonical_id' : 'missing_canonical_id',
                });
            }
        }
    }

    const hardFailureCount = malformedProgressItems.length
        + duplicateProgressCanonicalIds.length
        + staleProgressCanonicalIds.length
        + staleSessionEvents.length;

    return {
        ok: hardFailureCount === 0,
        canonical_count: canonicalRecords.length,
        progress_item_count: (progress.items || []).length,
        initialized_progress_count: occurrences.size,
        missing_progress_count: missingProgressCanonicalIds.length,
        missing_progress_sample: missingProgressCanonicalIds.slice(0, 20),
        duplicate_progress_canonical_ids: duplicateProgressCanonicalIds,
        stale_progress_canonical_ids: staleProgressCanonicalIds,
        malformed_progress_items: malformedProgressItems,
        stale_session_events: staleSessionEvents,
        hard_failure_count: hardFailureCount,
    };
}

module.exports = {
    evaluateReviewIntegrity,
};
