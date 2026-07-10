'use strict';

const test = require('node:test');
const assert = require('node:assert/strict');
const { classify } = require('../scripts/content/audit_answer_types');

test('answer type audit prioritizes expected answer artifact over legacy source label', () => {
    assert.equal(classify({ canonical_title: '算法：合并区间', aliases: [] }, [{ question_type: '八股文_Concept', original_question: '算法：合并区间' }]).answer_type, 'coding');
    assert.equal(classify({ canonical_title: '如何设计高并发库存扣减', aliases: [] }, [{ question_type: '八股文_Concept', original_question: '设计库存系统' }]).answer_type, 'scenario');
    assert.equal(classify({ canonical_title: '描述一次线上故障复盘', aliases: [] }, [{ question_type: '八股文_Concept', original_question: '故障复盘' }]).answer_type, 'project');
    assert.equal(classify({ canonical_title: 'AQS 的核心原理', aliases: [] }, [{ question_type: '八股文_Concept', original_question: 'AQS 原理' }]).answer_type, 'mechanism');
});
