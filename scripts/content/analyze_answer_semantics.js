#!/usr/bin/env node
'use strict';

const crypto = require('crypto');
const fs = require('fs');
const path = require('path');
const { defaultDate } = require('../lib/date');
const { readJson, writeJson } = require('../lib/io');
const { listAnswerFiles, readAnswerFile } = require('../lib/answer_store');

const ROOT = path.resolve(__dirname, '..', '..');
const BASELINE_RELATIVE_PATH = path.join('data', 'manifests', 'quality', 'answer_semantic_baseline.json');
const SECTION_NAMES = [
    '核心结论',
    '1 分钟版',
    '3 分钟版',
    '关键细节',
    '原理机制',
    '项目经验版',
    '常见追问',
    '易错点',
];
const DEFECT_PATHS = [
    'long_tail.defects.fallback_core_count',
    'long_tail.defects.generic_scenario_count',
    'long_tail.defects.documents_with_all_global_followups_count',
    'long_tail.defects.repeated_body_line_occurrence_count',
    'long_tail.coding.generic_problem_spec_count',
    'long_tail.coding.generic_sql_count',
    'long_tail.coding.generic_dp_count',
    'long_tail.coding.placeholder_implementation_count',
];

const GLOBAL_FOLLOWUPS = [
    '- 问：这道题最先要澄清什么？答：先确认题目范围、运行版本、输入输出、数据规模、并发与一致性目标；这些条件会直接改变结论和选型。',
    '- 问：如何验证回答不是背诵？答：给出一个可复现样例或真实指标，沿入口、核心状态和输出走一遍，再用失败注入、边界数据或对照实验验证。',
    '- 问：方案的主要代价是什么？答：从复杂度、延迟、吞吐、内存/存储、可用性、一致性和运维成本逐项说明，并指出当前约束下接受该代价的原因。',
    '- 问：题目继续追问源码或底层时怎么答？答：先说明核心数据结构和状态转换，再定位关键入口、并发控制与异常路径；不确定的版本细节明确标注并回到源码或官方文档核验。',
];

function parseArgs(argv) {
    const options = {
        check: false,
        writeBaseline: false,
        overwrite: false,
    };
    for (let index = 2; index < argv.length; index++) {
        const arg = argv[index];
        if (arg === '--check') options.check = true;
        else if (arg === '--write-baseline') options.writeBaseline = true;
        else if (arg === '--overwrite') options.overwrite = true;
        else if (arg === '--root') options.root = argv[++index];
        else if (arg === '--baseline') options.baseline = argv[++index];
        else if (arg === '--date') options.date = argv[++index];
        else throw new Error(`Unknown option: ${arg}`);
    }
    if (options.check && options.writeBaseline) {
        throw new Error('--check and --write-baseline cannot be used together');
    }
    return options;
}

function sha256(content) {
    return crypto.createHash('sha256').update(content).digest('hex');
}

function hashFiles(filePaths, root) {
    const hash = crypto.createHash('sha256');
    for (const filePath of [...filePaths].sort()) {
        hash.update(path.relative(root, filePath));
        hash.update('\0');
        hash.update(fs.readFileSync(filePath));
        hash.update('\0');
    }
    return hash.digest('hex');
}

function sectionBody(content, title) {
    const marker = `## ${title}\n`;
    const start = content.indexOf(marker);
    if (start < 0) return '';
    const rest = content.slice(start + marker.length);
    const next = rest.search(/\n##\s+/);
    return (next < 0 ? rest : rest.slice(0, next)).trim();
}

function increment(target, key) {
    const normalized = key || 'unknown';
    target[normalized] = (target[normalized] || 0) + 1;
}

function normalizeBodyLines(row) {
    const titleWithoutPunctuation = row.title.replace(/[？?。！!]+$/, '');
    return row.content
        .split(/\r?\n/)
        .map((line) => line.trim())
        .filter((line) => line
            && !line.startsWith('<!--')
            && !line.startsWith('#')
            && !line.startsWith('- 领域：')
            && !line.startsWith('- 关键实体：')
            && !line.startsWith('- 来源问法：'))
        .map((line) => line
            .split(row.title).join('<TITLE>')
            .split(titleWithoutPunctuation).join('<TITLE>'));
}

function normalizeFollowup(line, row) {
    const titleWithoutPunctuation = row.title.replace(/[？?。！!]+$/, '');
    return line
        .split(row.title).join('<TITLE>')
        .split(titleWithoutPunctuation).join('<TITLE>');
}

function percentage(numerator, denominator) {
    return denominator ? numerator / denominator : 0;
}

function collectRows(root) {
    return listAnswerFiles({ answersDir: path.join(root, 'review', 'answers') }).map((filePath) => {
        const answer = readAnswerFile(filePath);
        const title = (answer.content.match(/^#\s+(.+)$/m) || [])[1] || '';
        const group = answer.metadata.quality_tier === 'long_tail_baseline' ? 'long_tail' : 'curated';
        return {
            filePath,
            relativePath: path.relative(root, filePath),
            metadata: answer.metadata,
            content: answer.content,
            title,
            group,
            sections: Object.fromEntries(SECTION_NAMES.map((name) => [name, sectionBody(answer.content, name)])),
        };
    });
}

function uniqueSectionCounts(rows) {
    return Object.fromEntries(SECTION_NAMES.map((name) => {
        const unique = new Set(rows.map((row) => row.sections[name]));
        return [name, {
            unique_count: unique.size,
            unique_rate: percentage(unique.size, rows.length),
        }];
    }));
}

function repeatedLineMetrics(rows) {
    const lines = rows.flatMap(normalizeBodyLines);
    const counts = new Map();
    for (const line of lines) counts.set(line, (counts.get(line) || 0) + 1);
    const repeatedOccurrences = lines.filter((line) => counts.get(line) > 1).length;
    return {
        body_line_occurrence_count: lines.length,
        unique_body_line_count: counts.size,
        repeated_body_line_occurrence_count: repeatedOccurrences,
        repeated_body_line_occurrence_rate: percentage(repeatedOccurrences, lines.length),
    };
}

function followupMetrics(rows) {
    const lines = [];
    let documentsWithAllGlobalFollowups = 0;
    for (const row of rows) {
        const followups = row.sections['常见追问'].split(/\r?\n/).filter((line) => line.startsWith('- 问：'));
        if (GLOBAL_FOLLOWUPS.every((line) => followups.includes(line))) {
            documentsWithAllGlobalFollowups += 1;
        }
        lines.push(...followups.map((line) => normalizeFollowup(line, row)));
    }
    const counts = new Map();
    for (const line of lines) counts.set(line, (counts.get(line) || 0) + 1);
    return {
        followup_count: lines.length,
        normalized_unique_followup_count: counts.size,
        documents_with_all_global_followups_count: documentsWithAllGlobalFollowups,
    };
}

function implementationBlock(content) {
    return (content.match(/~~~(?:java|sql)\n([\s\S]*?)\n~~~/i) || [])[1] || '';
}

function codingMetrics(rows) {
    const coding = rows.filter((row) => row.metadata.answer_type === 'coding');
    const problemSpec = coding.filter((row) => /static final class ProblemSpec/.test(row.content));
    const genericSql = coding.filter((row) => /WITH base AS \(/.test(row.content));
    const genericDp = coding.filter((row) => /static long solveDp\(/.test(row.content));
    const placeholders = new Set([...problemSpec, ...genericSql, ...genericDp].map((row) => row.metadata.canonical_id));
    return {
        answer_count: coding.length,
        unique_implementation_block_count: new Set(coding.map((row) => implementationBlock(row.content))).size,
        generic_problem_spec_count: problemSpec.length,
        generic_sql_count: genericSql.length,
        generic_dp_count: genericDp.length,
        placeholder_implementation_count: placeholders.size,
    };
}

function groupMetrics(rows) {
    const answerTypes = {};
    const statuses = {};
    for (const row of rows) {
        increment(answerTypes, row.metadata.answer_type || 'curated');
        increment(statuses, row.metadata.status);
    }
    return {
        answer_count: rows.length,
        answer_types: answerTypes,
        statuses,
        section_uniqueness: uniqueSectionCounts(rows),
        ...repeatedLineMetrics(rows),
        ...followupMetrics(rows),
    };
}

function buildReport(options = {}) {
    const root = path.resolve(options.root || ROOT);
    const rows = collectRows(root);
    const longTail = rows.filter((row) => row.group === 'long_tail');
    const curated = rows.filter((row) => row.group === 'curated');
    const answersDir = path.join(root, 'review', 'answers');
    const answerFiles = listAnswerFiles({ answersDir });
    const canonicalPath = path.join(root, 'data', 'questions', 'canonical_questions.jsonl');
    const questionPath = path.join(root, 'data', 'questions', 'questions.jsonl');
    const longTailMetrics = groupMetrics(longTail);
    const fallbackCore = longTail.filter((row) => row.sections['核心结论'].startsWith('复习「'));
    const genericScenario = longTail.filter((row) => row.metadata.answer_type === 'scenario'
        && !row.sections['核心结论'].includes('核心技术判断：'));

    return {
        schema_version: 'answer_semantic_baseline.v1',
        generated_at: defaultDate(options),
        inputs: {
            answers_sha256: hashFiles(answerFiles, root),
            canonical_questions_sha256: sha256(fs.readFileSync(canonicalPath)),
            questions_sha256: sha256(fs.readFileSync(questionPath)),
        },
        methodology: {
            group_rule: 'quality_tier=long_tail_baseline is long_tail; every other answer is curated',
            repeated_line_rule: 'trim non-empty body lines; exclude metadata, headings and review locator; normalize the answer title; count every occurrence whose normalized line appears more than once',
            placeholder_code_rule: 'union of generic ProblemSpec, generic source_table SQL and solveDp/transition skeletons',
        },
        total_answer_count: rows.length,
        curated: groupMetrics(curated),
        long_tail: {
            ...longTailMetrics,
            defects: {
                fallback_core_count: fallbackCore.length,
                generic_scenario_count: genericScenario.length,
                documents_with_all_global_followups_count: longTailMetrics.documents_with_all_global_followups_count,
                repeated_body_line_occurrence_count: longTailMetrics.repeated_body_line_occurrence_count,
            },
            coding: codingMetrics(longTail),
        },
    };
}

function getPath(value, dottedPath) {
    return dottedPath.split('.').reduce((current, key) => current?.[key], value);
}

function compareToBaseline(current, baseline) {
    const regressions = [];
    for (const metric of DEFECT_PATHS) {
        const currentValue = getPath(current, metric);
        const baselineValue = getPath(baseline, metric);
        if (!Number.isFinite(currentValue) || !Number.isFinite(baselineValue)) {
            regressions.push({ metric, error: 'missing_numeric_metric', baseline: baselineValue, current: currentValue });
        } else if (currentValue > baselineValue) {
            regressions.push({ metric, error: 'defect_regression', baseline: baselineValue, current: currentValue });
        }
    }
    return {
        schema_version: 'answer_semantic_check.v1',
        ok: regressions.length === 0,
        baseline_generated_at: baseline.generated_at,
        current_generated_at: current.generated_at,
        current_inputs: current.inputs,
        regressions,
        current,
    };
}

function main(argv = process.argv) {
    const options = parseArgs(argv);
    const root = path.resolve(options.root || ROOT);
    const baselinePath = options.baseline
        ? path.resolve(options.baseline)
        : path.join(root, BASELINE_RELATIVE_PATH);
    const current = buildReport({ ...options, root });

    if (options.writeBaseline) {
        if (fs.existsSync(baselinePath) && !options.overwrite) {
            throw new Error(`Baseline already exists: ${baselinePath}; pass --overwrite to replace it intentionally`);
        }
        writeJson(baselinePath, current);
        console.log(JSON.stringify({ ok: true, written: path.relative(root, baselinePath), report: current }, null, 2));
        return 0;
    }

    if (options.check) {
        const baseline = readJson(baselinePath);
        const result = compareToBaseline(current, baseline);
        console.log(JSON.stringify(result, null, 2));
        return result.ok ? 0 : 1;
    }

    console.log(JSON.stringify(current, null, 2));
    return 0;
}

if (require.main === module) {
    try {
        process.exitCode = main();
    } catch (error) {
        console.error(error.message);
        process.exitCode = 1;
    }
}

module.exports = {
    DEFECT_PATHS,
    GLOBAL_FOLLOWUPS,
    buildReport,
    codingMetrics,
    compareToBaseline,
    main,
    sectionBody,
};
