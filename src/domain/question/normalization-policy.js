'use strict';

/**
 * Historical Question text normalization used by IDs and Canonical semantic
 * checks. Keep this rule in Domain so hashing, integrity checks, and future
 * interfaces cannot drift independently.
 */
function normalizeQuestionText(text) {
    return String(text ?? '')
        .toLowerCase()
        .replace(/[^\w\u4e00-\u9fa5]/g, '');
}

module.exports = {
    normalizeQuestionText,
};
