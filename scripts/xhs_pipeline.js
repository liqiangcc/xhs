const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

/**
 * XHS Pipeline Orchestrator
 * 
 * 一次性完成所有机械性工作，输出 JSON 任务清单供 AI 执行。
 * 
 * Usage: node scripts/xhs_pipeline.js [limit]
 * 
 * 输出 JSON 格式：
 * {
 *   "batch_size": 10,
 *   "tasks": [
 *     { "uuid": "...", "action": "extract_and_tag", "desc_path": "...", "img_path": "..." },
 *     { "uuid": "...", "action": "tag_only", "structured_path": "...", "hashes": [...] },
 *     { "uuid": "...", "action": "skip", "reason": "already tagged" }
 *   ],
 *   "summary": { "total": 10, "extract_and_tag": 5, "tag_only": 3, "skip": 2 }
 * }
 */

const limit = parseInt(process.argv[2]) || 10;

const DIRS = {
    desc: 'note_desc',
    img: 'note_img_txt',
    structured: 'note_structured',
    tagged: 'note_tagged'
};

// ── Scoring (from filter_notes.js) ───────────────────────────────────────

const SCORE_THRESHOLD = 3;
const EXCLUDE_JD = /内推码|内推链接|工作职责|任职资格|岗位要求|招聘要求/;
const EXCLUDE_OFFER = /offer选择|offer对比|offer比较|背调完|薪资待遇|offer\s*PK/i;

function countChineseQuestionMarks(text) {
    return (text.match(/？/g) || []).length;
}

function hasQuestionListPattern(text) {
    const lines = text.split(/\r?\n/);
    let count = 0;
    for (const line of lines) {
        if (/^\s*\d+[\.\、\)]/.test(line) && line.length > 6 && line.length < 200) {
            count++;
        }
    }
    return count >= 3;
}

function scoreNote(combined) {
    if (EXCLUDE_JD.test(combined)) return -1;
    if (EXCLUDE_OFFER.test(combined) && countChineseQuestionMarks(combined) < 3) return -1;
    if (!/Java|Spring|MySQL|Redis|架构|算法|线程|JVM|消息队列|Kafka|分布式|前端|React|Vue|TCP|HTTP|CSS/.test(combined)) return -1;

    let score = 0;
    if (countChineseQuestionMarks(combined) >= 3) score += 3;
    if (hasQuestionListPattern(combined)) score += 2;
    if (combined.length > 800) score += 1;
    return score;
}

// ── Hash Generation ──────────────────────────────────────────────────────

function generateHashes(structuredPath) {
    try {
        const output = execSync(`node scripts/generate_hashes.js ${structuredPath}`, { encoding: 'utf-8' });
        return output.split('\n').filter(line => line.trim()).map(line => {
            const [index, hash, ...rest] = line.split('|');
            return { index: index.trim(), hash: hash.trim(), question: rest.join('|').trim() };
        });
    } catch (e) {
        return [];
    }
}

// ── Main Pipeline ────────────────────────────────────────────────────────

function run() {
    const structuredSet = new Set(
        fs.existsSync(DIRS.structured)
            ? fs.readdirSync(DIRS.structured).filter(f => f.endsWith('.json')).map(f => path.basename(f, '.json'))
            : []
    );
    const taggedSet = new Set(
        fs.existsSync(DIRS.tagged)
            ? fs.readdirSync(DIRS.tagged).filter(f => f.endsWith('.json')).map(f => path.basename(f, '.json'))
            : []
    );

    const allDescFiles = fs.readdirSync(DIRS.desc).filter(f => f.endsWith('.txt'));
    const candidates = [];

    for (const file of allDescFiles) {
        if (candidates.length >= limit) break;

        const uuid = path.basename(file, '.txt');

        // Already fully processed → skip
        if (taggedSet.has(uuid)) continue;

        // Already structured → only need tagging
        if (structuredSet.has(uuid)) {
            candidates.push({ uuid, preState: 'structured' });
            continue;
        }

        // Not structured → need scoring + full pipeline
        let descText = '';
        try { descText = fs.readFileSync(path.join(DIRS.desc, file), 'utf-8'); } catch (_) { continue; }

        let imgText = '';
        let imgSize = 0;
        const imgPath = path.join(DIRS.img, `${uuid}.txt`);
        try {
            const stat = fs.statSync(imgPath);
            imgSize = stat.size;
            imgText = fs.readFileSync(imgPath, 'utf-8');
        } catch (_) { /* no img */ }

        const combined = descText + '\n' + imgText;
        const score = scoreNote(combined);

        if (imgSize > 100 && score >= 0) {
            candidates.push({ uuid, preState: 'raw', score: score + 2 });
        } else if (score >= SCORE_THRESHOLD) {
            candidates.push({ uuid, preState: 'raw', score });
        }
    }

    // Sort raw candidates by score desc
    candidates.sort((a, b) => (b.score || 0) - (a.score || 0));

    // Build task list
    const tasks = [];
    const summary = { total: 0, extract_and_tag: 0, tag_only: 0, skip: 0 };

    for (const c of candidates) {
        summary.total++;

        if (c.preState === 'structured') {
            // Need hash + tag
            const structuredPath = path.join(DIRS.structured, `${c.uuid}.json`);
            const structuredData = JSON.parse(fs.readFileSync(structuredPath, 'utf-8'));
            const questions = structuredData.questions || [];

            if (questions.length === 0) {
                tasks.push({ uuid: c.uuid, action: 'skip', reason: 'empty questions array' });
                summary.skip++;
                continue;
            }

            const hashes = generateHashes(structuredPath);

            tasks.push({
                uuid: c.uuid,
                action: 'tag_only',
                structured_path: structuredPath,
                metadata: {
                    company: structuredData.company || '未知',
                    position: structuredData.position || '未知',
                    round: structuredData.round || '未注明',
                    level: structuredData.level || '未知',
                    year: structuredData.year || '未知',
                    date: structuredData.date || '未知'
                },
                hashes
            });
            summary.tag_only++;
        } else {
            // Need full pipeline: extract + hash + tag
            const descPath = path.join(DIRS.desc, `${c.uuid}.txt`);
            const imgPath = path.join(DIRS.img, `${c.uuid}.txt`);
            const hasImg = fs.existsSync(imgPath);

            tasks.push({
                uuid: c.uuid,
                action: 'extract_and_tag',
                desc_path: descPath,
                img_path: hasImg ? imgPath : null,
                score: c.score
            });
            summary.extract_and_tag++;
        }
    }

    const output = { batch_size: limit, tasks, summary };

    console.log(JSON.stringify(output, null, 2));
}

run();
