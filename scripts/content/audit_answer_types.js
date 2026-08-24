#!/usr/bin/env node
'use strict';

const fs = require('fs');
const path = require('path');
const { loadCanonicalQuestions } = require('../lib/canonical_store');
const { readJsonl, stableStringify, writeJsonl } = require('../lib/io');

const ROOT = path.resolve(__dirname, '..', '..');
const TYPES = ['concept', 'mechanism', 'scenario', 'coding', 'project', 'behavior'];

function sourceSignals(questions) {
    const rawTypes = questions.map((row) => String(row.question_type || '').toLowerCase());
    const matches = {
        coding: rawTypes.some((value) => /coding|算法|编程题/.test(value)),
        behavior: rawTypes.some((value) => /behavioral|non_tech|personal|reflection|行为|hr/.test(value)),
        project: rawTypes.some((value) => /project|experience|postmortem|项目|实践/.test(value)),
        scenario: rawTypes.some((value) => /scenario|architecture|tooling|integration|analysis|场景|系统设计/.test(value)),
        mechanism: rawTypes.some((value) => /underthehood|lowlevel|原理|源码/.test(value)),
    };
    matches.concept = rawTypes.some((value) => /concept|八股文|概念/.test(value) || !/coding|算法|编程题|behavioral|non_tech|personal|reflection|行为|hr|project|experience|postmortem|项目|实践|scenario|architecture|tooling|integration|analysis|场景|系统设计|underthehood|lowlevel|原理|源码/.test(value));
    return TYPES.filter((type) => matches[type]);
}

function classify(canonical, questions) {
    const title = [
        canonical.canonical_title,
        ...(canonical.aliases || []),
        ...questions.map((row) => row.original_question),
    ].filter(Boolean).join('\n').toLowerCase();
    const sourceTypeSignals = sourceSignals(questions);

    // Personal-answer types must have an explicit first-person/team/career cue.
    // Technical terms such as Hash/Bean/classpath “冲突” are not behavior questions.
    const behaviorCue = /职业规划|职业选择|为什么离职|离职原因|自我介绍|个人优缺点|期望薪资|未来\s*\d+\s*[-—~至到]\s*年|团队(?:目标|分歧|冲突)|沟通(?:分歧|冲突)|个人意见|如何推动方案决策|技术决策冲突|不同阶段的工作经历|核心成长|如何平衡团队|你最大的(?:优点|缺点)|你对.*(?:实践|思考|看法|见解)/;

    // A legacy Project source label is not evidence that the expected answer is
    // a first-person STAR story. Require an explicit personal action/experience
    // cue before classifying as Project. This keeps questions such as
    // “项目中 HashMap 的底层原理是什么” in the technical queue while preserving
    // genuine “你如何落地/排查/优化” project questions.
    const projectCue = /上一家公司|你曾经|你是如何|你如何(?:落地|实现|设计|排查|优化)|你的职责|实际项目(?:中)?.*(?:负责|职责|落地|实现|设计|排查|优化)|你们?(?:的)?项目(?:中|里)?.*(?:你|你们).*(?:如何|怎么|为何|为什么).*(?:落地|实现|设计|排查|优化|选择|采用|使用)|线上(?:故障|事故).*你|故障复盘|线上故障排查|复盘一次|用过哪些设计模式|设计模式.*(?:落地|应用|实践)|请问你的.*qps|为什么使用.+不用|你们采用.+架构/;
    const sourceProjectCue = sourceTypeSignals.includes('project') && /上一家公司|你的职责|你曾经|你是如何|你如何|你们(?:如何|怎么|为何|为什么|采用|使用|选择)|线上(?:故障|事故)|故障复盘|复盘一次|实际项目.*(?:负责|职责|落地|实现|设计|排查|优化)/.test(title);

    // SQL must be an explicit language/query request. The substring “sql” in
    // “mysql” must never classify a database theory question as Coding.
    const explicitSqlCue = /(?:^|[^a-z])sql(?:[^a-z]|$).*(?:查询|语句|实现|编写|优化)|(?:编写|写出|实现).*(?:^|[^a-z])sql(?:[^a-z]|$)/;
    const codingCue = /代码手撕|手撕代码|手写|代码实现|编程题|leetcode|(?:编写|写出|实现).*(?:代码|函数|方法|程序)|给定.*(?:数组|链表|字符串|二叉树|区间|矩阵)|反转链表|合并区间|最长(?:递增|公共|回文)|最短路径|二分查找|动态规划|背包问题|判断.*(?:链表环|回文)|实现\s*lru|排序算法|多线程环境下的账户转账/;

    // Scenario classification is about producing a concrete design/selection
    // under constraints. Keep these cues ahead of mechanism classification so
    // “how to use Redis to implement a distributed lock” is not reduced to a
    // mechanism-only answer.
    const scenarioCue = /(?:如何|怎么|怎样)(?:设计|保证|确保|提升|优化|避免).*(?:系统|架构|一致性|可靠性|高可用|幂等|性能|全量扫描)|设计.*(?:系统|架构|方案)|高并发|容量规划|容灾|灾备|灰度发布|蓝绿发布|附近的人|短\s*url|短链接|秒杀|搜索引擎|缓存一致性|exactly[- ]?once|消息.*只被消费一次|提升.*(?:rocketmq|kafka|消息).*性能|文件上传.*(?:设计|流程)|如何(?:排查|解决).*(?:类路径|classpath|依赖|故障|问题)|(?:如何|怎么|怎样).*(?:选择|选型).*(?:消息中间件|中间件|kafka|rocketmq|rabbitmq|数据库|缓存|存储|技术方案)|如何(?:使用|利用).*redis.*(?:实现|做).*分布式锁/;

    // Some questions contain comparison words but still require a state/flow
    // explanation as the primary artifact. These strong cues must be evaluated
    // before the generic “区别/对比 -> concept” rule.
    const strongMechanismCue = /cms.*(?:垃圾回收|垃圾收集|收集器).*(?:执行|回收)?(?:流程|过程)|(?:cms|垃圾回收).*(?:为什么|为啥).*(?:分成|需要).*(?:步|阶段)|(?:io|i\/o)\s*多路复用|tcp.*(?:三次握手|四次挥手).*(?:过程|原理|原因)/;
    const mechanismCue = /原理|底层|机制|生命周期|工作流程|执行流程|运行流程|处理流程|复制流程|恢复流程|状态(?:转换|变化)|为什么快|如何保证.*(?:原子性|可见性|有序性)|安全点|等待与唤醒|加锁失败后的等待|如何实现分布式锁|binlog|undo\s*log|零拷贝|\bisr\b|\bspi\b|hashmap.*(?:原理|底层)|hash(?:表| table)?.*冲突|bean.*生命周期/;
    const comparisonCue = /区别|对比/;
    const conceptCue = /有哪些|类型|分类|状态|策略|是什么|什么是|特点|优缺点|常见.*(?:算法|索引|场景)/;

    let answerType;
    let rationale;
    if (behaviorCue.test(title)) {
        answerType = 'behavior';
        rationale = 'explicit_personal_or_team_behavior_evidence_required';
    } else if (projectCue.test(title) || sourceProjectCue) {
        answerType = 'project';
        rationale = 'explicit_real_project_evidence_required';
    } else if (explicitSqlCue.test(title) || codingCue.test(title)) {
        answerType = 'coding';
        rationale = 'explicit_runnable_algorithm_or_sql_requested';
    } else if (scenarioCue.test(title)) {
        answerType = 'scenario';
        rationale = 'requires_assumptions_data_flow_and_tradeoffs';
    } else if (strongMechanismCue.test(title)) {
        answerType = 'mechanism';
        rationale = 'strong_state_flow_or_protocol_mechanism_required';
    } else if (comparisonCue.test(title)) {
        answerType = 'concept';
        rationale = 'explicit_comparison';
    } else if (mechanismCue.test(title)) {
        answerType = 'mechanism';
        rationale = 'requires_participants_state_flow_and_boundary';
    } else if (conceptCue.test(title)) {
        answerType = 'concept';
        rationale = 'definition_comparison_or_enumeration';
    } else if (sourceTypeSignals.length === 1) {
        [answerType] = sourceTypeSignals;
        rationale = 'single_source_type_fallback';
    } else {
        answerType = 'concept';
        rationale = 'definition_or_comparison_default';
    }

    const secondary = [];
    if (answerType === 'concept' && /原理|底层|机制|实现|原因|为什么|为啥/.test(title)) secondary.push('mechanism');
    if (answerType === 'scenario' && /原理|底层|源码|机制/.test(title)) secondary.push('mechanism');
    if (answerType === 'project' && /设计|方案|架构|高并发|一致性/.test(title)) secondary.push('scenario');
    if (answerType === 'behavior' && /技术|项目|方案|选型/.test(title)) secondary.push('project');

    const flags = [];
    if (sourceTypeSignals.length > 1) flags.push('mixed_source_question_type');
    if (secondary.length) flags.push('secondary_coverage_required');
    if (sourceTypeSignals.length && !sourceTypeSignals.includes(answerType)) flags.push('source_type_overridden');
    return {
        answer_type: answerType,
        rationale,
        secondary_requirements: secondary,
        source_type_signals: sourceTypeSignals,
        risk_flags: flags,
    };
}

function buildAudit(options = {}) {
    const root = options.root || ROOT;
    const canonicals = loadCanonicalQuestions({ filePath: path.join(root, 'data', 'questions', 'canonical_questions.jsonl') });
    const byCanonical = new Map();
    for (const question of readJsonl(path.join(root, 'data', 'questions', 'questions.jsonl'))) {
        if (!byCanonical.has(question.canonical_id)) byCanonical.set(question.canonical_id, []);
        byCanonical.get(question.canonical_id).push(question);
    }
    return canonicals.map((canonical) => ({ schema_version: 'answer_type_audit.v1', canonical_id: canonical.canonical_id, canonical_title: canonical.canonical_title, ...classify(canonical, byCanonical.get(canonical.canonical_id) || []) }))
        .sort((a, b) => a.canonical_id.localeCompare(b.canonical_id));
}

function run(options = {}) {
    const root = options.root || ROOT;
    const output = path.join(root, 'data', 'manifests', 'quality', 'answer_type_audit.jsonl');
    const rows = buildAudit({ root });
    const expected = `${rows.map(stableStringify).join('\n')}\n`;
    const current = fs.existsSync(output) ? fs.readFileSync(output, 'utf8') : '';
    if (!options.noWrite && !options.check) writeJsonl(output, rows);
    return { schema_version: 'answer_type_audit_report.v1', ok: !options.check || current === expected, check: Boolean(options.check), canonical_count: rows.length, type_counts: Object.fromEntries(TYPES.map((type) => [type, rows.filter((row) => row.answer_type === type).length])), mixed_count: rows.filter((row) => row.risk_flags.length > 0).length, output: path.relative(root, output) };
}

function main(argv = process.argv) {
    const options = { check: argv.includes('--check'), noWrite: argv.includes('--noWrite') };
    const rootIndex = argv.indexOf('--root'); if (rootIndex >= 0) options.root = path.resolve(argv[rootIndex + 1]);
    const result = run(options); console.log(JSON.stringify(result, null, 2)); return result.ok ? 0 : 1;
}

if (require.main === module) process.exitCode = main();
module.exports = { classify, buildAudit, run, main };