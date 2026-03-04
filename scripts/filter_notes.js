const fs = require('fs');
const path = require('path');

/**
 * Scans note_desc (+ note_img_txt) for interview notes that haven't been
 * structured yet.  Uses a score-based heuristic to surface only notes that
 * are likely to contain real interview questions.
 *
 * Usage: node scripts/filter_notes.js [limit]
 *
 * Scoring signals
 * ───────────────
 *  +3  Chinese question marks (？) count ≥ 3
 *  +2  Companion note_img_txt file exists and > 100 bytes
 *  +2  Text contains numbered question-list patterns
 *  +1  Combined text length > 800
 *  –∞  Negative signals → immediate exclusion
 *
 * Threshold: score ≥ 3
 */

const limit = parseInt(process.argv[2]) || 10;
const noteDescDir = 'note_desc';
const noteImgTxtDir = 'note_img_txt';
const noteStructuredDir = 'note_structured';
const SCORE_THRESHOLD = 3;

// ── Negative-signal patterns (instant exclusion) ─────────────────────────
const EXCLUDE_JD = /内推码|内推链接|工作职责|任职资格|岗位要求|招聘要求/;
const EXCLUDE_OFFER = /offer选择|offer对比|offer比较|背调完|薪资待遇|offer\s*PK/i;
const EXCLUDE_PURE_SHARE = /关注我.*解锁|欢迎评论区交流|转发收藏|点赞收藏关注/;

// ── Positive-signal helpers ──────────────────────────────────────────────
function countChineseQuestionMarks(text) {
    return (text.match(/？/g) || []).length;
}

function hasQuestionListPattern(text) {
    // Numbered items that look like interview questions
    // e.g.  "1. HashMap底层原理" or "1、说一下Redis"
    const lines = text.split(/\r?\n/);
    let questionLineCount = 0;
    for (const line of lines) {
        if (/^\s*\d+[\.\、\)]/.test(line) && line.length > 6 && line.length < 200) {
            questionLineCount++;
        }
    }
    return questionLineCount >= 3;
}

// ── Main ─────────────────────────────────────────────────────────────────
try {
    const structuredFiles = new Set(
        fs.readdirSync(noteStructuredDir)
            .filter(f => f.endsWith('.json'))
            .map(f => path.basename(f, '.json'))
    );

    const allFiles = fs.readdirSync(noteDescDir).filter(f => f.endsWith('.txt'));

    const results = [];

    for (const file of allFiles) {
        if (results.length >= limit) break;

        const id = path.basename(file, '.txt');
        if (structuredFiles.has(id)) continue;

        // Read desc text
        let descText = '';
        try {
            descText = fs.readFileSync(path.join(noteDescDir, file), 'utf-8');
        } catch (_) { continue; }

        // Read img_txt if exists
        let imgText = '';
        let imgSize = 0;
        const imgPath = path.join(noteImgTxtDir, `${id}.txt`);
        try {
            const stat = fs.statSync(imgPath);
            imgSize = stat.size;
            imgText = fs.readFileSync(imgPath, 'utf-8');
        } catch (_) { /* no img_txt */ }

        const combined = descText + '\n' + imgText;

        // ── Negative signals → skip ──────────────────────────────────
        if (EXCLUDE_JD.test(combined)) continue;
        if (EXCLUDE_OFFER.test(combined) && countChineseQuestionMarks(combined) < 3) continue;

        // Require at least one tech keyword to stay relevant
        if (!/Java|Spring|MySQL|Redis|架构|算法|线程|JVM|消息队列|Kafka|分布式/.test(combined)) continue;

        // ── Positive scoring ─────────────────────────────────────────
        let score = 0;

        const qmarks = countChineseQuestionMarks(combined);
        if (qmarks >= 3) score += 3;

        if (imgSize > 100) score += 2;

        if (hasQuestionListPattern(combined)) score += 2;

        if (combined.length > 800) score += 1;

        if (score >= SCORE_THRESHOLD) {
            results.push({ file, id, score });
        }
    }

    if (results.length > 0) {
        // Sort by score descending so highest-confidence notes come first
        results.sort((a, b) => b.score - a.score);
        results.forEach(r => console.log(r.file));
    } else {
        console.warn('No pending notes found matching the criteria.');
    }
} catch (error) {
    console.error(`Error scanning notes: ${error.message}`);
    process.exit(1);
}
