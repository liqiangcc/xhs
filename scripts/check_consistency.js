#!/usr/bin/env node
/**
 * XHS Data Consistency Checker
 * 
 * 检查 note_structured/ 与 note_tagged/ 之间的数据一致性。
 * 
 * Usage: node scripts/check_consistency.js [--fix-dry-run]
 * 
 * 检查项：
 *   1. structured 有但 tagged 没有（漏打标）
 *   2. tagged 有但 structured 没有（孤立标签文件）
 *   3. structured 中 questions 为空数组的笔记
 *   4. tagged 中 tagged_questions 为空数组的笔记
 *   5. structured ↔ tagged 题目数量不匹配
 *   6. tagged JSON schema 缺失必要字段
 *   7. hash 一致性（tagged 中的 question_id 是否与 structured 中的题目 hash 吻合）
 */

'use strict';

const fs = require('fs');
const path = require('path');
const { computeQuestionId } = require('./lib/hash');

const ROOT = path.resolve(__dirname, '..');
const DIRS = {
    structured: path.join(ROOT, 'note_structured'),
    tagged: path.join(ROOT, 'note_tagged'),
};

// ── Utils ────────────────────────────────────────────────────────────────

function listJsonIds(dir) {
    if (!fs.existsSync(dir)) return new Set();
    return new Set(
        fs.readdirSync(dir)
            .filter(f => f.endsWith('.json'))
            .map(f => path.basename(f, '.json'))
    );
}

function readJson(filePath) {
    try {
        return JSON.parse(fs.readFileSync(filePath, 'utf-8'));
    } catch (e) {
        return null;
    }
}

// ── Required fields ──────────────────────────────────────────────────────

const STRUCTURED_REQUIRED = ['note_id', 'source', 'company', 'position', 'round', 'level', 'year', 'date', 'questions'];
const TAGGED_REQUIRED = ['note_id', 'source', 'company', 'position', 'round', 'level', 'year', 'date', 'tagged_questions'];
const TAGGED_Q_REQUIRED = ['question_id', 'original_question', 'domain', 'question_type', 'cognitive_depth', 'tech_entities', 'is_valid_for_library'];

// ── Main ─────────────────────────────────────────────────────────────────

function main() {
    const structuredIds = listJsonIds(DIRS.structured);
    const taggedIds = listJsonIds(DIRS.tagged);

    const issues = [];
    let warnCount = 0;
    let errorCount = 0;

    function warn(category, id, msg) {
        issues.push({ severity: 'WARN', category, id, msg });
        warnCount++;
    }
    function error(category, id, msg) {
        issues.push({ severity: 'ERROR', category, id, msg });
        errorCount++;
    }

    // ── Check 1: structured 有但 tagged 没有 ─────────────────────────────
    const missingTagged = [...structuredIds].filter(id => !taggedIds.has(id));
    for (const id of missingTagged) {
        const data = readJson(path.join(DIRS.structured, `${id}.json`));
        const qCount = data?.questions?.length ?? 0;
        if (qCount > 0) {
            error('MISSING_TAGGED', id, `structured 有 ${qCount} 道题，但 tagged 文件不存在`);
        } else {
            warn('MISSING_TAGGED_EMPTY', id, `structured 存在但 questions 为空，tagged 文件不存在`);
        }
    }

    // ── Check 2: tagged 有但 structured 没有 ──────────────────────────────
    const orphanTagged = [...taggedIds].filter(id => !structuredIds.has(id));
    for (const id of orphanTagged) {
        error('ORPHAN_TAGGED', id, `tagged 文件存在，但 structured 文件不存在（孤立数据）`);
    }

    // ── Check 3-7: 逐个检查共有文件 ──────────────────────────────────────
    const commonIds = [...structuredIds].filter(id => taggedIds.has(id));

    for (const id of commonIds) {
        const structured = readJson(path.join(DIRS.structured, `${id}.json`));
        const tagged = readJson(path.join(DIRS.tagged, `${id}.json`));

        if (!structured) {
            error('PARSE_ERROR', id, `structured JSON 解析失败`);
            continue;
        }
        if (!tagged) {
            error('PARSE_ERROR', id, `tagged JSON 解析失败`);
            continue;
        }

        // Check 3: structured schema
        for (const field of STRUCTURED_REQUIRED) {
            if (!(field in structured)) {
                warn('SCHEMA_STRUCTURED', id, `structured 缺少字段: ${field}`);
            }
        }

        // Check 4: tagged schema
        for (const field of TAGGED_REQUIRED) {
            if (!(field in tagged)) {
                warn('SCHEMA_TAGGED', id, `tagged 缺少字段: ${field}`);
            }
        }

        const questions = structured.questions || [];
        const taggedQuestions = tagged.tagged_questions || [];

        // Check 5: 题目数量不匹配
        if (questions.length !== taggedQuestions.length) {
            warn('COUNT_MISMATCH', id,
                `structured 有 ${questions.length} 道题，tagged 有 ${taggedQuestions.length} 道题`);
        }

        // Check 6: tagged_questions 中的 schema 检查
        for (let i = 0; i < taggedQuestions.length; i++) {
            const tq = taggedQuestions[i];
            for (const field of TAGGED_Q_REQUIRED) {
                if (!(field in tq)) {
                    warn('SCHEMA_TAGGED_Q', id,
                        `tagged_questions[${i}] 缺少字段: ${field} (题: "${(tq.original_question || '').slice(0, 30)}...")`);
                }
            }
            // domain 子字段
            if (tq.domain && (!tq.domain.l1 || !tq.domain.l2)) {
                warn('SCHEMA_TAGGED_Q', id,
                    `tagged_questions[${i}].domain 缺少 l1/l2 (题: "${(tq.original_question || '').slice(0, 30)}...")`);
            }
        }

        // Check 7a: Hash 自身一致性（tagged 的 question_id 是否等于 computeHash(original_question)）
        for (let i = 0; i < taggedQuestions.length; i++) {
            const tq = taggedQuestions[i];
            if (!tq.original_question || !tq.question_id) continue;
            const expectedHash = computeQuestionId(tq.original_question);
            if (tq.question_id !== expectedHash) {
                error('HASH_SELF_MISMATCH', id,
                    `tagged_questions[${i}] question_id 与 original_question 的 hash 不一致: "${tq.original_question.slice(0, 30)}…" 预期=${expectedHash.slice(0, 8)}…, 实际=${tq.question_id.slice(0, 8)}…`);
            }
        }

        // Check 7b: 原题文本漂移（structured questions vs tagged original_question 不一致）
        for (let i = 0; i < Math.min(questions.length, taggedQuestions.length); i++) {
            if (questions[i] !== taggedQuestions[i]?.original_question) {
                warn('TEXT_DRIFT', id,
                    `题[${i}] 文本不一致:\n           S: "${questions[i].slice(0, 50)}"\n           T: "${(taggedQuestions[i]?.original_question || '').slice(0, 50)}"`);
            }
        }
    }

    // ── Output ───────────────────────────────────────────────────────────
    console.log('\n═══════════════════════════════════════════════════');
    console.log('  XHS 数据一致性检查报告');
    console.log('═══════════════════════════════════════════════════\n');

    console.log(`  note_structured/  ${structuredIds.size} 个文件`);
    console.log(`  note_tagged/      ${taggedIds.size} 个文件`);
    console.log(`  共有文件          ${commonIds.length} 个`);
    console.log(`  漏打标            ${missingTagged.length} 个`);
    console.log(`  孤立标签          ${orphanTagged.length} 个\n`);

    if (issues.length === 0) {
        console.log('  ✅ 未发现任何问题，数据完全一致！\n');
        return;
    }

    // Group by category
    const byCategory = {};
    for (const issue of issues) {
        if (!byCategory[issue.category]) byCategory[issue.category] = [];
        byCategory[issue.category].push(issue);
    }

    for (const [category, items] of Object.entries(byCategory)) {
        const icon = items[0].severity === 'ERROR' ? '❌' : '⚠️';
        console.log(`${icon} ${category} (${items.length} 条)`);
        console.log('─'.repeat(50));
        for (const item of items.slice(0, 20)) {
            console.log(`  [${item.severity}] ${item.id}`);
            console.log(`         ${item.msg}`);
        }
        if (items.length > 20) {
            console.log(`  ... 还有 ${items.length - 20} 条，省略显示`);
        }
        console.log('');
    }

    console.log('───────────────────────────────────────────────────');
    console.log(`  汇总: ${errorCount} 个 ERROR, ${warnCount} 个 WARN`);
    console.log('───────────────────────────────────────────────────\n');

    // 输出 JSON 到 stderr 以便程序化处理
    console.error(JSON.stringify({ errorCount, warnCount, issues }, null, 2));
}

main();
