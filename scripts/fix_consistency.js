#!/usr/bin/env node
/**
 * XHS Data Consistency Fixer
 * 
 * 自动修复 check_consistency.js 发现的问题：
 *   1. structured 文件缺失 source 字段 → 补上 "小红书"
 *   2. tagged 文件中 question_id 与 original_question 的 hash 不一致 → 用 Node.js 统一重算
 *   3. tagged 中 original_question 被 AI 篡改（TEXT_DRIFT）→ 从 structured 恢复原文并重算 hash
 *   4. 数量不匹配 → 仅日志提示，不自动修复
 * 
 * Usage:
 *   node scripts/fix_consistency.js              预览模式（只显示将要修改的内容）
 *   node scripts/fix_consistency.js --apply       实际执行修复
 */

'use strict';

const fs = require('fs');
const path = require('path');
const crypto = require('crypto');

const ROOT = path.resolve(__dirname, '..');
const DIRS = {
    structured: path.join(ROOT, 'note_structured'),
    tagged: path.join(ROOT, 'note_tagged'),
};

const dryRun = !process.argv.includes('--apply');

// ── Utils ────────────────────────────────────────────────────────────────

function computeHash(question) {
    const normalized = question.toLowerCase().replace(/[^\w\u4e00-\u9fa5]/g, '');
    return crypto.createHash('md5').update(normalized).digest('hex');
}

function readJson(filePath) {
    try {
        return JSON.parse(fs.readFileSync(filePath, 'utf-8'));
    } catch (e) {
        return null;
    }
}

function writeJson(filePath, data) {
    fs.writeFileSync(filePath, JSON.stringify(data, null, 2) + '\n', 'utf-8');
}

function listJsonIds(dir) {
    if (!fs.existsSync(dir)) return [];
    return fs.readdirSync(dir)
        .filter(f => f.endsWith('.json'))
        .map(f => path.basename(f, '.json'));
}

// ── Main ─────────────────────────────────────────────────────────────────

function main() {
    if (dryRun) {
        console.log('🔍 预览模式 — 不会修改任何文件。加 --apply 参数执行实际修复。\n');
    } else {
        console.log('🔧 执行修复模式\n');
    }

    let fixedSourceCount = 0;
    let fixedHashFileCount = 0;
    let fixedHashQuestionCount = 0;
    let countMismatchFiles = [];

    const structuredIds = listJsonIds(DIRS.structured);
    const taggedIds = new Set(listJsonIds(DIRS.tagged));

    // ── Fix 1: structured 补 source 字段 ─────────────────────────────────
    console.log('── 修复 1: structured 补 source 字段 ──\n');

    for (const id of structuredIds) {
        const filePath = path.join(DIRS.structured, `${id}.json`);
        const data = readJson(filePath);
        if (!data) continue;

        if (!data.source) {
            fixedSourceCount++;
            if (dryRun) {
                console.log(`  [DRY] ${id} — 将补上 source: "小红书"`);
            } else {
                // 保持字段顺序：note_id, source, company, ...
                const fixed = { note_id: data.note_id, source: '小红书', ...data };
                delete fixed.source; // remove duplicate from spread
                const ordered = { note_id: fixed.note_id, source: '小红书' };
                for (const [k, v] of Object.entries(data)) {
                    if (k !== 'note_id' && k !== 'source') ordered[k] = v;
                }
                writeJson(filePath, ordered);
                console.log(`  [FIXED] ${id} — source: "小红书" 已补上`);
            }
        }
    }

    console.log(`\n  小计: ${fixedSourceCount} 个文件${dryRun ? '将被修复' : '已修复'}\n`);

    // ── Fix 2: tagged 重算 question_id ───────────────────────────────────
    console.log('── 修复 2: tagged 重算 question_id (基于 original_question) ──\n');

    for (const id of structuredIds) {
        if (!taggedIds.has(id)) continue;

        const taggedPath = path.join(DIRS.tagged, `${id}.json`);
        const structuredPath = path.join(DIRS.structured, `${id}.json`);
        const tagged = readJson(taggedPath);
        const structured = readJson(structuredPath);
        if (!tagged || !structured) continue;

        const taggedQuestions = tagged.tagged_questions || [];
        const structuredQuestions = structured.questions || [];

        // 检查数量不匹配
        if (structuredQuestions.length !== taggedQuestions.length) {
            countMismatchFiles.push({
                id,
                structured: structuredQuestions.length,
                tagged: taggedQuestions.length
            });
        }

        // 重算每个 tagged question 的 hash
        let fileModified = false;
        let thisFileFixedCount = 0;

        for (let i = 0; i < taggedQuestions.length; i++) {
            const tq = taggedQuestions[i];
            if (!tq.original_question) continue;

            const correctHash = computeHash(tq.original_question);
            if (tq.question_id !== correctHash) {
                if (dryRun && thisFileFixedCount < 2) {
                    console.log(`  [DRY] ${id} q[${i}]: "${tq.original_question.slice(0, 35)}…"`);
                    console.log(`         ${tq.question_id} → ${correctHash}`);
                }
                tq.question_id = correctHash;
                fileModified = true;
                thisFileFixedCount++;
                fixedHashQuestionCount++;
            }
        }

        // Also fix: 确保 tagged 的 source 字段存在
        if (!tagged.source) {
            tagged.source = '小红书';
            fileModified = true;
        }

        if (fileModified) {
            fixedHashFileCount++;
            if (dryRun && thisFileFixedCount > 2) {
                console.log(`  [DRY] ${id} — 还有 ${thisFileFixedCount - 2} 条 hash 待修复...`);
            }
            if (!dryRun) {
                writeJson(taggedPath, tagged);
                console.log(`  [FIXED] ${id} — ${thisFileFixedCount} 条 hash 已重算`);
            }
        }
    }

    console.log(`\n  小计: ${fixedHashFileCount} 个文件 / ${fixedHashQuestionCount} 条题目的 hash ${dryRun ? '将被修复' : '已修复'}\n`);

    // ── Fix 3: TEXT_DRIFT 修复（tagged original_question 恢复为 structured 原文）───
    console.log('── 修复 3: TEXT_DRIFT 修复（恢复被 AI 篡改的原题文本）──\n');

    let fixedDriftFileCount = 0;
    let fixedDriftQuestionCount = 0;

    for (const id of structuredIds) {
        if (!taggedIds.has(id)) continue;

        const taggedPath = path.join(DIRS.tagged, `${id}.json`);
        const structuredPath = path.join(DIRS.structured, `${id}.json`);
        const tagged = readJson(taggedPath);
        const structured = readJson(structuredPath);
        if (!tagged || !structured) continue;

        const questions = structured.questions || [];
        const taggedQuestions = tagged.tagged_questions || [];
        let fileModified = false;
        let thisFileDriftCount = 0;

        for (let i = 0; i < Math.min(questions.length, taggedQuestions.length); i++) {
            const tq = taggedQuestions[i];
            if (tq.original_question !== questions[i]) {
                if (dryRun && thisFileDriftCount < 2) {
                    console.log(`  [DRY] ${id} q[${i}]:`);
                    console.log(`         "${tq.original_question.slice(0, 45)}…"`);
                    console.log(`       → "${questions[i].slice(0, 45)}…"`);
                }
                tq.original_question = questions[i];
                tq.question_id = computeHash(questions[i]);
                fileModified = true;
                thisFileDriftCount++;
                fixedDriftQuestionCount++;
            }
        }

        if (fileModified) {
            fixedDriftFileCount++;
            if (dryRun && thisFileDriftCount > 2) {
                console.log(`  [DRY] ${id} — 还有 ${thisFileDriftCount - 2} 条待恢复...`);
            }
            if (!dryRun) {
                writeJson(taggedPath, tagged);
                console.log(`  [FIXED] ${id} — ${thisFileDriftCount} 条原题文本已恢复`);
            }
        }
    }

    console.log(`\n  小计: ${fixedDriftFileCount} 个文件 / ${fixedDriftQuestionCount} 条题目 ${dryRun ? '将被恢复' : '已恢复'}\n`);

    // ── Fix 4: 数量不匹配（仅提示） ──────────────────────────────────────
    if (countMismatchFiles.length > 0) {
        console.log('── 不自动修复: 题目数量不匹配 ──\n');
        for (const item of countMismatchFiles) {
            console.log(`  ⚠️  ${item.id}: structured ${item.structured} 题 vs tagged ${item.tagged} 题`);
        }
        console.log('\n  ℹ️  数量不匹配需手动检查，不自动修复。\n');
    }

    // ── Summary ──────────────────────────────────────────────────────────
    console.log('═══════════════════════════════════════════════════');
    console.log('  修复汇总');
    console.log('═══════════════════════════════════════════════════');
    console.log(`  source 补全:     ${fixedSourceCount} 个 structured 文件`);
    console.log(`  hash 重算:       ${fixedHashFileCount} 个 tagged 文件 / ${fixedHashQuestionCount} 条题目`);
    console.log(`  原题恢复:        ${fixedDriftFileCount} 个 tagged 文件 / ${fixedDriftQuestionCount} 条题目`);
    console.log(`  数量不匹配:      ${countMismatchFiles.length} 个文件（需手动检查）`);
    if (dryRun) {
        console.log('\n  ⚡ 以上为预览。执行 node scripts/fix_consistency.js --apply 以实际修复。');
    } else {
        console.log('\n  ✅ 所有自动修复已完成。请运行 node scripts/check_consistency.js 验证。');
    }
    console.log('');
}

main();
