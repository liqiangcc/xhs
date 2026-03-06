const fs = require('fs');
const path = require('path');
const crypto = require('crypto');

/**
 * XHS Pipeline Orchestrator
 * 
 * 统一入口，AI 只需要调用这一个脚本。
 * 
 * 用法：
 *   node scripts/xhs_pipeline.js [limit]       获取任务清单（默认 10 条）
 *   node scripts/xhs_pipeline.js hash <uuid>    为指定笔记生成 hash（用于 extract_and_tag 后）
 * 
 * 任务清单 JSON 格式：
 * {
 *   "batch_size": 10,
 *   "tasks": [...],
 *   "summary": { "total": 10, "extract_and_tag": 5, "tag_only": 3, "skip": 2 }
 * }
 */

const DIRS = {
    desc: 'note_desc',
    img: 'note_img_txt',
    structured: 'note_structured',
    tagged: 'note_tagged'
};

// ── Hash Generation (inline, no external command) ────────────────────────

function computeHash(question) {
    const normalized = question.toLowerCase().replace(/[^\w\u4e00-\u9fa5]/g, '');
    return crypto.createHash('md5').update(normalized).digest('hex');
}

function generateHashes(structuredPath) {
    try {
        const data = JSON.parse(fs.readFileSync(structuredPath, 'utf-8'));
        const questions = data.questions || [];
        return questions.map((q, i) => ({
            index: String(i),
            hash: computeHash(q),
            question: q
        }));
    } catch (e) {
        return [];
    }
}

// ── Scoring ──────────────────────────────────────────────────────────────

const SCORE_THRESHOLD = 2;
const EXCLUDE_JD = /内推码|内推链接|工作职责|任职资格|岗位要求|招聘要求/;
const EXCLUDE_OFFER = /offer选择|offer对比|offer比较|背调完|薪资待遇|offer\s*PK/i;

function countQuestionMarks(text) {
    return (text.match(/[？?]/g) || []).length;
}

function hasQuestionListPattern(text) {
    const lines = text.split(/\r?\n/);
    let count = 0;
    for (const line of lines) {
        // Match: 1. 1、 1) 1️⃣ 1．  and also ● ✅ ⭕ bullet markers
        if ((/^\s*\d+[\.\.\、\)️⃣]/.test(line) || /^\s*[●✅⭕☑►▸•]/.test(line)) && line.length > 6 && line.length < 200) {
            count++;
        }
    }
    return count >= 3;
}

function scoreNote(combined) {
    if (EXCLUDE_JD.test(combined)) return -1;
    if (EXCLUDE_OFFER.test(combined) && countQuestionMarks(combined) < 3) return -1;
    if (!/Java|Spring|MySQL|Redis|架构|算法|线程|JVM|消息队列|Kafka|分布式|前端|React|Vue|TCP|HTTP|CSS|Go|Golang|Python|C\+\+|Rust|Flink|Spark|Hadoop|Hive|HDFS|Docker|K8s|Kubernetes|Linux|Git|操作系统|数据库|索引|锁|事务|网络|进程|协程|面经|八股|MongoDB|Elasticsearch|RabbitMQ|RocketMQ|Nginx|Nacos|Dubbo|Netty|Zookeeper/i.test(combined)) return -1;

    let score = 0;
    if (countQuestionMarks(combined) >= 3) score += 3;
    if (hasQuestionListPattern(combined)) score += 2;
    if (combined.length > 800) score += 1;
    return score;
}

// ── Sub-command: hash ────────────────────────────────────────────────────

function runHashCommand(uuid) {
    const structuredPath = path.join(DIRS.structured, `${uuid}.json`);
    if (!fs.existsSync(structuredPath)) {
        console.error(JSON.stringify({ error: `File not found: ${structuredPath}` }));
        process.exit(1);
    }

    const hashes = generateHashes(structuredPath);
    const data = JSON.parse(fs.readFileSync(structuredPath, 'utf-8'));

    const output = {
        uuid,
        question_count: hashes.length,
        metadata: {
            company: data.company || '未知',
            position: data.position || '未知',
            round: data.round || '未注明',
            level: data.level || '未知',
            year: data.year || '未知',
            date: data.date || '未知'
        },
        hashes
    };

    console.log(JSON.stringify(output, null, 2));
}

// ── Main: Task List ──────────────────────────────────────────────────────

function runTaskList(limit, filter) {
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
            if (filter === 'extract_only') continue; // skip tag_only when filter is extract_only
            candidates.push({ uuid, preState: 'structured' });
            continue;
        }

        // Not structured → need extract_and_tag
        if (filter === 'tag_only') continue; // skip extract_and_tag when filter is tag_only

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
        } else if (descText.length >= 300 && score >= 0) {
            // Rescue gate: substantial text with tech keywords but non-standard format
            candidates.push({ uuid, preState: 'raw', score: score + 1 });
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

// ── Entry Point ──────────────────────────────────────────────────────────

const args = process.argv.slice(2);

if (args[0] === 'hash' && args[1]) {
    runHashCommand(args[1]);
} else {
    const limit = parseInt(args[0]) || 10;
    const filter = args[1]; // 'tag_only' | 'extract_only' | undefined (all)
    runTaskList(limit, filter);
}
