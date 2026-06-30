/**
 * validate_tagged.js
 * 校验 note_tagged 与 note_structured 的问题数量一致性
 * 
 * 用法:
 *   node scripts/validate_tagged.js <uuid>        — 校验单个笔记
 *   node scripts/validate_tagged.js               — 校验所有已标签化的笔记
 * 
 * 校验规则:
 *   1. tagged_questions 中的每个 question_id 必须存在于 structured 的 hashes 列表中
 *   2. structured 的 hashes 数量必须等于 tagged_questions 数量
 *   3. 输出缺失的 question_id 和对应的原始问题
 */

const fs = require('fs');
const path = require('path');
const { computeQuestionId } = require('./lib/hash');

const STRUCTURED_DIR = path.join(__dirname, '..', 'note_structured');
const TAGGED_DIR = path.join(__dirname, '..', 'note_tagged');

function validateNote(uuid) {
    const structuredPath = path.join(STRUCTURED_DIR, uuid + '.json');
    const taggedPath = path.join(TAGGED_DIR, uuid + '.json');

    if (!fs.existsSync(structuredPath)) {
        return { uuid, status: 'ERROR', message: 'structured file not found' };
    }
    if (!fs.existsSync(taggedPath)) {
        return { uuid, status: 'SKIP', message: 'tagged file not found' };
    }

    const structured = JSON.parse(fs.readFileSync(structuredPath, 'utf-8'));
    const tagged = JSON.parse(fs.readFileSync(taggedPath, 'utf-8'));

    // 获取 structured 中的问题列表及其 hash
    const questions = structured.questions || [];
    const structuredHashes = questions.map((q, i) => ({
        index: i,
        hash: computeQuestionId(q),
        question: q
    }));

    // 获取 tagged 中的 question_id 集合
    const taggedQuestions = tagged.tagged_questions || [];
    const taggedIds = new Set(taggedQuestions.map(q => q.question_id));

    // 找出缺失的问题 (在 structured 中有但 tagged 中没有)
    const missing = structuredHashes.filter(h => !taggedIds.has(h.hash));

    // 找出多余的问题 (在 tagged 中有但 structured 中没有)
    const structuredHashSet = new Set(structuredHashes.map(h => h.hash));
    const extra = taggedQuestions.filter(q => !structuredHashSet.has(q.question_id));

    const result = {
        uuid,
        structured_count: structuredHashes.length,
        tagged_count: taggedQuestions.length,
        missing_count: missing.length,
        extra_count: extra.length,
    };

    if (missing.length === 0 && extra.length === 0) {
        result.status = 'PASS';
    } else {
        result.status = 'FAIL';
        if (missing.length > 0) {
            result.missing = missing.map(m => ({
                hash: m.hash,
                question: m.question
            }));
        }
        if (extra.length > 0) {
            result.extra = extra.map(e => ({
                question_id: e.question_id,
                question: e.original_question
            }));
        }
    }

    return result;
}

// --- Main ---
const args = process.argv.slice(2);

if (args.length > 0) {
    // 校验单个 UUID
    const uuid = args[0].replace('.json', '');
    const result = validateNote(uuid);
    console.log(JSON.stringify(result, null, 2));
    if (result.status === 'FAIL') process.exit(1);
} else {
    // 校验所有已标签化的笔记
    const taggedFiles = fs.readdirSync(TAGGED_DIR).filter(f => f.endsWith('.json'));
    let passCount = 0, failCount = 0, skipCount = 0;
    const failures = [];

    for (const f of taggedFiles) {
        const uuid = f.replace('.json', '');
        const result = validateNote(uuid);
        if (result.status === 'PASS') passCount++;
        else if (result.status === 'SKIP') skipCount++;
        else {
            failCount++;
            failures.push(result);
        }
    }

    console.log(`\n=== Validation Summary ===`);
    console.log(`Total: ${taggedFiles.length}  PASS: ${passCount}  FAIL: ${failCount}  SKIP: ${skipCount}`);

    if (failures.length > 0) {
        console.log(`\n--- Failed Notes ---`);
        for (const f of failures) {
            console.log(`\n${f.uuid}: structured=${f.structured_count} tagged=${f.tagged_count} missing=${f.missing_count}`);
            if (f.missing) {
                f.missing.forEach(m => console.log(`  ✗ [${m.hash.substring(0, 8)}] ${m.question.substring(0, 80)}`));
            }
        }
        process.exit(1);
    } else {
        console.log('\n✓ All tagged notes are consistent!');
    }
}
