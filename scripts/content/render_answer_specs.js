#!/usr/bin/env node
'use strict';

const fs = require('fs');
const path = require('path');
const { loadCanonicalQuestions } = require('../lib/canonical_store');
const { parseAnswerMetadata, replaceAnswerMetadata } = require('../lib/answer_store');

const ROOT = path.resolve(__dirname, '..', '..');

const TYPE_TEXT = {
    concept: {
        deep: '回答时先统一比较维度，再给选择条件与反例；定义本身不是终点，必须说明代价和不适用边界。',
        mechanism: '从参与对象、状态变化和主流程展开，再补充并发/故障保证与资源开销。',
        mapping: '项目映射提示：从真实代码或架构中选择一个使用点，补齐选择条件、替代方案和验证指标；没有事实时不虚构收益。',
        mistakes: ['不要只背定义而不说明选择条件。', '不要把常见实现说成跨版本唯一结论。'],
    },
    mechanism: {
        deep: '按“目标—核心数据结构—主流程—保证机制—开销—版本边界”复述，并指出失败或退化路径。',
        mechanism: '入口触发状态变化，核心结构保存中间状态，协调/恢复路径处理并发与故障；实际语义需绑定版本和配置。',
        mapping: '项目映射提示：填写真实版本、配置、规模、观测指标与故障演练；只阅读源码时不包装成线上实践。',
        mistakes: ['不要跳过状态变化和失败路径。', '不要脱离版本、配置和负载讨论性能。'],
    },
    scenario: {
        deep: '先澄清规模、QPS、数据量、一致性、延迟和故障目标，再画主链路，补齐幂等、容量、降级、对账、观测和替代方案。',
        mechanism: '入口按容量预算接收流量，核心链路用分区/缓存/异步扩展，持久层维护最终不变量，补偿与对账让故障状态收敛。',
        mapping: '项目映射提示：把示例数字替换为真实规模和 SLO，补齐个人决策、压测证据、回滚与复盘；不使用未经确认的项目成果。',
        mistakes: ['不要只罗列组件而没有数据流和容量。', '不要只设计成功路径，必须说明超时、重试、降级和对账。'],
    },
    coding: {
        deep: '先声明输入约束和不变量，再逐步推导实现；最后给出复杂度、空值/极值用例和至少一个变体。',
        mechanism: '正确性由循环/状态不变量保证；每次迭代只做保持不变量的局部更新，结束条件把局部结论扩展到完整输入。',
        mapping: '算法训练映射：先口述不变量，再手写 Java 并用边界用例走查；算法训练不应被包装成虚构项目经历。',
        mistakes: ['不要只给代码而不解释不变量。', '不要遗漏复杂度、空输入和变体。'],
    },
    project: {
        deep: '使用真实 STAR/事故证据组织背景、约束、个人动作、指标、取舍与复盘；缺少事实时只提供提问框架。',
        mechanism: '以时间线串联告警、假设、证据、止血、根因、修复和防复发，区分团队动作与个人动作。',
        mapping: '项目映射提示：必须由用户补充真实背景、个人职责、证据、结果和复盘；不得生成确定口吻的个人故事。',
        mistakes: ['不要先猜根因再挑证据。', '不要虚构个人职责、事故指标或量化结果。'],
    },
};

function parseArgs(argv) {
    const options = {};
    for (let i = 2; i < argv.length; i++) {
        if (argv[i] === '--spec') options.spec = path.resolve(argv[++i]);
        else if (argv[i] === '--check') options.check = true;
        else if (argv[i] === '--date') options.date = argv[++i];
    }
    if (!options.spec) throw new Error('Usage: render_answer_specs.js --spec <file> [--check] [--date YYYY-MM-DD]');
    return options;
}

function render(entry, canonical, date) {
    const profile = TYPE_TEXT[entry.type];
    if (!profile) throw new Error(`Unsupported answer type: ${entry.type}`);
    if (!Array.isArray(entry.points) || entry.points.length < 3) throw new Error(`${entry.canonical_id}: at least three points required`);
    if (!Array.isArray(entry.followups) || entry.followups.length < 3) throw new Error(`${entry.canonical_id}: at least three followups required`);
    const followups = entry.followups.map((item) => {
        const split = item.indexOf('|');
        if (split < 1) throw new Error(`${entry.canonical_id}: followup must use question|answer`);
        return `- 问：${item.slice(0, split)}答：${item.slice(split + 1)}`;
    });
    const implementation = entry.java
        ? `\n\n\`\`\`java\n${entry.java.trim()}\n\`\`\``
        : '';
    const complexity = entry.complexity ? `\n- 复杂度：${entry.complexity}` : '';
    // Curated specs historically include type guidance as a fallback. Candidate
    // prose is independently researched and reviewed, so appending generic
    // guidance there can contaminate an otherwise topic-specific answer.
    const includeTypeGuidance = entry.include_type_guidance !== false;
    const deep = [entry.deep, includeTypeGuidance ? profile.deep : null].filter(Boolean).join(' ');
    const mechanism = [includeTypeGuidance ? profile.mechanism : null, entry.mechanism || entry.core].filter(Boolean).join(' ');
    const mistakes = [
        ...(includeTypeGuidance ? profile.mistakes : []),
        ...(entry.mistakes || []),
    ].map((item) => `- ${item}`);
    return [
        `<!-- xhs-answer: ${JSON.stringify({ schema_version: 'answer.v1', canonical_id: entry.canonical_id, version: 1, status: 'ready', updated_at: date, quality_tier: 'curated' })} -->`,
        `# ${canonical.canonical_title}`,
        '',
        '## 核心结论',
        '',
        entry.core,
        '',
        '## 1 分钟版',
        '',
        ...entry.points.map((item) => `- ${item}`),
        '',
        '## 3 分钟版',
        '',
        `${deep}${implementation}`,
        '',
        '## 关键细节',
        '',
        ...entry.points.map((item) => `- ${item}`),
        ...(entry.constraints || []).map((item) => `- ${item}`),
        ...(entry.complexity ? [`- 复杂度：${entry.complexity}`] : []),
        '',
        '## 原理机制',
        '',
        `${mechanism}${complexity}`,
        '',
        '## 项目经验版',
        '',
        profile.mapping,
        '',
        '## 常见追问',
        '',
        ...followups,
        '',
        '## 易错点',
        '',
        ...mistakes,
        '',
    ].join('\n');
}

function main() {
    const options = parseArgs(process.argv);
    const spec = JSON.parse(fs.readFileSync(options.spec, 'utf8'));
    const date = options.date || spec.updated_at;
    const canonicals = new Map(loadCanonicalQuestions().map((record) => [record.canonical_id, record]));
    const changed = [];
    for (const entry of spec.answers || []) {
        const canonical = canonicals.get(entry.canonical_id);
        if (!canonical) throw new Error(`Unknown canonical_id: ${entry.canonical_id}`);
        let output = render(entry, canonical, date);
        const filePath = path.join(ROOT, 'review', 'answers', `${entry.canonical_id}.md`);
        const current = fs.existsSync(filePath) ? fs.readFileSync(filePath, 'utf8') : null;
        // Historical spec rendering is content-only. It must never silently restore
        // a demoted answer to ready/curated or erase audit metadata.
        if (current) output = replaceAnswerMetadata(output, parseAnswerMetadata(current, filePath));
        if (current !== output) {
            changed.push(path.relative(ROOT, filePath));
            if (!options.check) fs.writeFileSync(filePath, output, 'utf8');
        }
    }
    const result = { ok: changed.length === 0 || !options.check, check: Boolean(options.check), answer_count: (spec.answers || []).length, changed_files: changed };
    console.log(JSON.stringify(result, null, 2));
    if (options.check && changed.length) process.exitCode = 1;
}

if (require.main === module) main();

module.exports = {
    TYPE_TEXT,
    render,
};
