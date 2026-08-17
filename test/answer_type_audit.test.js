'use strict';

const test = require('node:test');
const assert = require('node:assert/strict');
const { classify } = require('../scripts/content/audit_answer_types');

function result(title, questionType = '八股文_Concept', original = title, aliases = []) {
    return classify({ canonical_title: title, aliases }, [{ question_type: questionType, original_question: original }]);
}

function type(title, questionType = '八股文_Concept', original = title, aliases = []) {
    return result(title, questionType, original, aliases).answer_type;
}

test('answer type audit prioritizes expected answer artifact over legacy source label', () => {
    assert.equal(type('算法：合并区间'), 'coding');
    assert.equal(type('如何设计高并发库存扣减'), 'scenario');
    assert.equal(type('描述一次线上故障复盘'), 'project');
    assert.equal(type('AQS 的核心原理'), 'mechanism');
});

test('technical words do not trigger unrelated answer types', () => {
    assert.equal(type('MySQL 事务隔离级别及其解决的问题'), 'concept');
    assert.equal(type('哈希表如何处理 Hash 冲突？'), 'mechanism');
    assert.equal(type('Spring 中同名 Bean 冲突发生在哪个阶段？', '原理深度_UnderTheHood'), 'mechanism');
    assert.equal(type('依赖冲突：在大型 Maven 项目中，如何排查并解决类路径冲突'), 'scenario');
});

test('personal cues remain explicit and fail closed', () => {
    assert.equal(type('团队出现技术分歧时，你如何平衡团队目标与个人意见？', '项目实战_Project'), 'behavior');
    assert.equal(type('在你上一家公司中是如何实现蓝绿发布的？', '场景设计_Scenario'), 'project');
    assert.equal(type('百亿级短 URL 如何生成无冲突短码？', '场景设计_Scenario'), 'scenario');
});

test('explicit coding and SQL requests are recognized without treating MySQL as SQL', () => {
    assert.equal(type('给定一个区间数组，请实现合并区间算法'), 'coding');
    assert.equal(type('编写 SQL 查询每个部门工资最高的员工'), 'coding');
    assert.equal(type('MySQL 常见索引类型及作用'), 'concept');
    assert.equal(type('ArrayList 和 LinkedList 的区别及底层实现'), 'concept');
});

test('real pilot questions are classified by the response artifact they require', () => {
    assert.equal(
        type('并发转账如何保证原子性并避免死锁？', '原理深度_UnderTheHood', '代码手撕：多线程环境下的账户转账（转账操作的原子性与死锁避免）。'),
        'coding',
    );
    assert.equal(
        type('CMS 垃圾收集器的执行流程及 STW 阶段', '八股文_Concept', '[美团] CMS 的垃圾回收过程。为啥要分成 4 步？'),
        'mechanism',
    );
    assert.equal(
        type('IO 多路复用及 select、poll、epoll 的区别', '八股文_Concept', 'IO多路复用'),
        'mechanism',
    );
    assert.equal(
        type('如何选择 Kafka、RocketMQ 和 RabbitMQ？', '八股文_Concept', '如何根据应用场景 choose 合适的消息中间件?'),
        'scenario',
    );
    assert.equal(
        type('如何使用 Redis 正确实现分布式锁？', '八股文_Concept', '如何使用 Redis 实现分布式锁？'),
        'scenario',
    );
    assert.equal(type('TCP 三次握手和四次挥手的过程与原因'), 'mechanism');
});

test('comparison questions stay concept while mechanism-heavy subrequirements remain explicit', () => {
    assert.equal(type('synchronized 和 Lock 的区别'), 'concept');
    assert.equal(type('synchronized 和 volatile 的区别'), 'concept');

    const tcpWait = result('TIME_WAIT 与 CLOSE_WAIT 的区别及 2MSL 原因');
    assert.equal(tcpWait.answer_type, 'concept');
    assert.deepEqual(tcpWait.secondary_requirements, ['mechanism']);
});
