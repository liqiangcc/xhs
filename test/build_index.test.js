'use strict';

const test = require('node:test');
const assert = require('node:assert/strict');
const { computeQuestionId } = require('../scripts/lib/hash');
const { buildIndexes } = require('../scripts/lib/index_store');

function question(original, sourceNoteId, index, company, entities, valid = true) {
    return {
        question_id: computeQuestionId(original),
        original_question: original,
        source_note_id: sourceNoteId,
        source_question_index: index,
        company,
        position: 'Java后端',
        round: '一面',
        level: '社招',
        year: '2024',
        date: '未知',
        domain: { l1: '缓存', l2: 'Redis' },
        question_type: '八股文_Concept',
        cognitive_depth: 'L1_Principle',
        tech_entities: entities,
        business_context: [],
        is_valid_for_library: valid,
        canonical_id: null,
        schema_version: 'question.v1',
        taxonomy_version: 'taxonomy.v1',
    };
}

test('builds entity, company, domain, and hotspot indexes from questions', () => {
    const original = 'Redis 有哪些集群模式？';
    const questions = [
        question(original, 'note-a', 0, '美团', ['redis']),
        question(original, 'note-b', 0, '字节', ['Redis']),
        question('MySQL 索引为什么用 B+ 树？', 'note-c', 0, '美团', ['MySQL']),
    ];

    const indexes = buildIndexes(questions);
    assert.equal(indexes.entity.entries.Redis.count, 2);
    assert.equal(indexes.company.entries['美团'].count, 2);
    assert.equal(indexes.domain.l1['缓存'].count, 3);
    assert.equal(indexes.domain.l2['缓存/Redis'].count, 3);
    assert.equal(indexes.hotspot.total_hotspots, 1);
    assert.equal(indexes.hotspot.entries[0].frequency, 2);
    assert.deepEqual(indexes.hotspot.entries[0].companies, ['美团', '字节']);
});
