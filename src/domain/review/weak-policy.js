'use strict';

function isWeakReviewProgress(progress) {
    if (!progress || typeof progress !== 'object') return false;

    return progress.status === 'weak'
        || progress.mistake_count > 0
        || (progress.review_count > 0 && progress.confidence < 0.5);
}

module.exports = {
    isWeakReviewProgress,
};
