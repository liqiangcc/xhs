'use strict';

const crypto = require('crypto');
const { normalizeQuestionText } = require('../../src/domain/question/normalization-policy');

function normalizeQuestion(text) {
    return normalizeQuestionText(text);
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
