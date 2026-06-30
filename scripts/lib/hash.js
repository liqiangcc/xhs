'use strict';

const crypto = require('crypto');

function normalizeQuestion(text) {
    return String(text ?? '')
        .toLowerCase()
        .replace(/[^\w\u4e00-\u9fa5]/g, '');
}

function computeQuestionId(text) {
    return crypto
        .createHash('md5')
        .update(normalizeQuestion(text), 'utf8')
        .digest('hex');
}

module.exports = {
    normalizeQuestion,
    computeQuestionId,
};
