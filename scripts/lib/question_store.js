'use strict';

const path = require('path');
const { readJsonl } = require('./io');

const DEFAULT_QUESTIONS_PATH = path.resolve(__dirname, '..', '..', 'data', 'questions', 'questions.jsonl');

function loadQuestions(options = {}) {
    const filePath = options.filePath || DEFAULT_QUESTIONS_PATH;
    return readJsonl(filePath, []);
}

function findById(questionId, options = {}) {
    const questions = options.questions || loadQuestions(options);
    return questions.find((question) => question.question_id === questionId) || null;
}

function findAllById(questionId, options = {}) {
    const questions = options.questions || loadQuestions(options);
    return questions.filter((question) => question.question_id === questionId);
}

function includesText(value, needle) {
    if (!needle) return true;
    return String(value || '').toLowerCase().includes(String(needle).toLowerCase());
}

function filterQuestions(filters = {}, options = {}) {
    const questions = options.questions || loadQuestions(options);
    return questions.filter((question) => {
        if (filters.question_id && question.question_id !== filters.question_id) return false;
        if (filters.source_note_id && question.source_note_id !== filters.source_note_id) return false;
        if (filters.valid !== undefined && question.is_valid_for_library !== filters.valid) return false;
        if (filters.company && !includesText(question.company, filters.company)) return false;
        if (filters.position && !includesText(question.position, filters.position)) return false;
        if (filters.level && !includesText(question.level, filters.level)) return false;
        if (filters.round && !includesText(question.round, filters.round)) return false;
        if (filters.year && String(question.year) !== String(filters.year)) return false;
        if (filters.domain_l1 && question.domain?.l1 !== filters.domain_l1) return false;
        if (filters.domain_l2 && question.domain?.l2 !== filters.domain_l2) return false;
        if (filters.question_type && question.question_type !== filters.question_type) return false;
        if (filters.cognitive_depth && question.cognitive_depth !== filters.cognitive_depth) return false;
        if (filters.entity) {
            const entityNeedle = String(filters.entity).toLowerCase();
            const matched = (question.tech_entities || []).some((entity) =>
                String(entity).toLowerCase().includes(entityNeedle)
            );
            if (!matched) return false;
        }
        return true;
    });
}

function toQueryRow(question) {
    return {
        question_id: question.question_id,
        original_question: question.original_question,
        source_note_id: question.source_note_id,
        note_id: question.source_note_id,
        source_question_index: question.source_question_index,
        company: question.company,
        position: question.position,
        round: question.round,
        level: question.level,
        year: question.year,
        date: question.date,
        domain_l1: question.domain?.l1 || '',
        domain_l2: question.domain?.l2 || '',
        question_type: question.question_type || '',
        cognitive_depth: question.cognitive_depth || '',
        tech_entities: question.tech_entities || [],
        business_context: question.business_context || [],
        is_valid_for_library: question.is_valid_for_library,
        canonical_id: question.canonical_id ?? null,
    };
}

function questionRef(question) {
    return {
        question_id: question.question_id,
        source_note_id: question.source_note_id,
        source_question_index: question.source_question_index,
    };
}

function refKey(ref) {
    return [
        ref.question_id,
        ref.source_note_id,
        ref.source_question_index ?? '',
    ].join('::');
}

module.exports = {
    DEFAULT_QUESTIONS_PATH,
    loadQuestions,
    findById,
    findAllById,
    filterQuestions,
    toQueryRow,
    questionRef,
    refKey,
};
