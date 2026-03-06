#!/usr/bin/env node
/**
 * 查询需要重新做 OCR 的笔记
 *
 * 筛选逻辑：
 *   1. 笔记尚未被结构化（note_structured 中不存在）
 *   2. 笔记的 desc 中含有技术关键词（通过了关键词门槛）
 *   3. 满足以下任一条件：
 *      a) 有图片 URL（note_images）但没有 OCR 结果（note_img_txt）
 *      b) OCR 结果文件 < 100 字节（内容过短，可能失败）
 *      c) 完全没有 OCR 结果，但 desc 暗示笔记含图片面试题
 *
 * Usage:
 *   node scripts/find_ocr_needed.js                        输出摘要 + ID 列表
 *   node scripts/find_ocr_needed.js --json                  输出 JSON 格式
 *   node scripts/find_ocr_needed.js --ids-only              仅输出 ID（每行一个）
 *   node scripts/find_ocr_needed.js --ids-only --limit 5    仅输出前 N 个 ID
 */

'use strict';

const fs = require('fs');
const path = require('path');

const ROOT = path.resolve(__dirname, '..');
const DIRS = {
    desc: path.join(ROOT, 'note_desc'),
    imgTxt: path.join(ROOT, 'note_img_txt'),
    images: path.join(ROOT, 'note_images'),
    structured: path.join(ROOT, 'note_structured'),
    tagged: path.join(ROOT, 'note_tagged'),
};

// ── 技术关键词（与 xhs_pipeline.js 保持一致）──────────────────────────
const TECH_KW = /Java|Spring|MySQL|Redis|架构|算法|线程|JVM|消息队列|Kafka|分布式|前端|React|Vue|TCP|HTTP|CSS|Go|Golang|Python|C\+\+|Rust|Flink|Spark|Hadoop|Hive|HDFS|Docker|K8s|Kubernetes|Linux|Git|操作系统|数据库|索引|锁|事务|网络|进程|协程|面经|八股|MongoDB|Elasticsearch|RabbitMQ|RocketMQ|Nginx|Nacos|Dubbo|Netty|Zookeeper/i;

// ── 排除模式 ─────────────────────────────────────────────────────────
const EXCLUDE_JD = /内推码|内推链接|工作职责|任职资格|岗位要求|招聘要求/;
const EXCLUDE_OFFER = /offer选择|offer对比|offer比较|背调完|薪资待遇|offer\s*PK/i;

// ── Utils ────────────────────────────────────────────────────────────
function listIds(dir, ext) {
    if (!fs.existsSync(dir)) return new Set();
    return new Set(
        fs.readdirSync(dir)
            .filter(f => f.endsWith(ext))
            .map(f => {
                // note_images 文件名格式: {id}_urls.txt
                if (ext === '_urls.txt') return f.replace(/_urls\.txt$/, '');
                return path.basename(f, ext);
            })
    );
}

function safeRead(filePath) {
    try { return fs.readFileSync(filePath, 'utf-8'); } catch (_) { return ''; }
}

function safeSize(filePath) {
    try { return fs.statSync(filePath).size; } catch (_) { return -1; }
}

// ── Main ─────────────────────────────────────────────────────────────
function main() {
    const args = process.argv.slice(2);
    const mode = args.find(a => a.startsWith('--') && !['--limit', '--offset', '--local-images-only'].includes(a)) || '';
    const limitIdx = args.indexOf('--limit');
    const limit = limitIdx >= 0 ? parseInt(args[limitIdx + 1], 10) : Infinity;
    const offsetIdx = args.indexOf('--offset');
    const offset = offsetIdx >= 0 ? parseInt(args[offsetIdx + 1], 10) : 0;
    const localImagesOnly = args.includes('--local-images-only');

    const descIds = listIds(DIRS.desc, '.txt');
    const structuredIds = listIds(DIRS.structured, '.json');
    const imgTxtIds = listIds(DIRS.imgTxt, '.txt');

    // note_images 文件名是 {id}_urls.txt
    const imageFileIds = new Set();
    if (fs.existsSync(DIRS.images)) {
        for (const f of fs.readdirSync(DIRS.images)) {
            if (f.endsWith('_urls.txt')) {
                imageFileIds.add(f.replace(/_urls\.txt$/, ''));
            }
        }
    }

    // 检查本地已下载的图片
    const downloadedImagesIds = new Set();
    const downloadedDir = path.join(ROOT, 'downloaded_images');
    if (fs.existsSync(downloadedDir)) {
        for (const f of fs.readdirSync(downloadedDir)) {
            const dirPath = path.join(downloadedDir, f);
            if (fs.statSync(dirPath).isDirectory()) {
                const files = fs.readdirSync(dirPath);
                const hasValidImage = files.some(file => safeSize(path.join(dirPath, file)) > 0);
                if (hasValidImage) {
                    downloadedImagesIds.add(f);
                }
            }
        }
    }

    const results = [];

    for (const id of descIds) {
        // 已结构化的不需要
        if (structuredIds.has(id)) continue;

        const hasLocalImages = downloadedImagesIds.has(id);
        if (localImagesOnly && !hasLocalImages) continue;

        const descText = safeRead(path.join(DIRS.desc, `${id}.txt`));
        if (!descText) continue;

        // 排除非面经
        if (EXCLUDE_JD.test(descText)) continue;
        if (EXCLUDE_OFFER.test(descText) && (descText.match(/[？?]/g) || []).length < 3) continue;

        // 必须含技术关键词
        if (!TECH_KW.test(descText)) continue;

        const hasImageUrls = imageFileIds.has(id);
        const hasOcr = imgTxtIds.has(id);
        const ocrPath = path.join(DIRS.imgTxt, `${id}.txt`);
        const ocrSize = hasOcr ? safeSize(ocrPath) : -1;

        let reason = '';

        if (hasImageUrls && !hasOcr) {
            reason = 'has_images_no_ocr';
        } else if (hasImageUrls && hasOcr && ocrSize < 100) {
            reason = 'has_images_ocr_too_short';
        } else if (!hasImageUrls && !hasOcr) {
            reason = 'no_images_no_ocr';
        } else if (!hasImageUrls && hasOcr && ocrSize < 100) {
            reason = 'no_images_ocr_too_short';
        } else {
            // 有 OCR 且 >= 100 字节，不需要重新做
            continue;
        }

        // 统计 desc 中的图片线索
        const imageHints = /[图片]|见图|看图|如图|截图|手写/.test(descText);

        results.push({
            id,
            reason,
            has_image_urls: hasImageUrls,
            has_ocr: hasOcr,
            ocr_size: ocrSize,
            desc_length: descText.length,
            desc_has_image_hint: imageHints,
        });
    }

    // 排序优先级：有图片URL的优先，然后按 desc 长度降序
    results.sort((a, b) => {
        const priorityA = a.has_image_urls ? 0 : 1;
        const priorityB = b.has_image_urls ? 0 : 1;
        if (priorityA !== priorityB) return priorityA - priorityB;
        return b.desc_length - a.desc_length;
    });

    // ── 输出 ──────────────────────────────────────────────────────────
    if (mode === '--json') {
        const summary = {
            total: results.length,
            has_images_no_ocr: results.filter(r => r.reason === 'has_images_no_ocr').length,
            has_images_ocr_too_short: results.filter(r => r.reason === 'has_images_ocr_too_short').length,
            no_images_no_ocr: results.filter(r => r.reason === 'no_images_no_ocr').length,
            no_images_ocr_too_short: results.filter(r => r.reason === 'no_images_ocr_too_short').length,
        };
        console.log(JSON.stringify({ summary, notes: results }, null, 2));
        return;
    }

    if (mode === '--ids-only') {
        const output = results.slice(offset, offset + limit);
        for (const r of output) console.log(r.id);
        return;
    }

    // 默认：摘要 + 表格
    const byReason = {};
    for (const r of results) {
        byReason[r.reason] = (byReason[r.reason] || 0) + 1;
    }

    console.log('\n═══════════════════════════════════════════════════');
    console.log('  需要重新做 OCR 的笔记');
    console.log('═══════════════════════════════════════════════════\n');
    console.log(`  总计: ${results.length} 个笔记\n`);

    console.log('  按原因分类:');
    const reasonLabels = {
        has_images_no_ocr: '有图片URL 无OCR结果',
        has_images_ocr_too_short: '有图片URL OCR内容<100字节',
        no_images_no_ocr: '无图片URL 无OCR结果',
        no_images_ocr_too_short: '无图片URL OCR内容<100字节',
    };
    for (const [reason, count] of Object.entries(byReason)) {
        console.log(`    ${reasonLabels[reason] || reason}: ${count}`);
    }

    // 有图片URL的列表（最优先处理）
    const withImages = results.filter(r => r.has_image_urls);
    if (withImages.length > 0) {
        console.log(`\n  ⭐ 有图片URL的笔记 (${withImages.length} 个，优先处理):`);
        console.log('  ' + '─'.repeat(48));
        for (const r of withImages) {
            console.log(`    ${r.id}  [${r.reason}]  desc=${r.desc_length}字`);
        }
    }

    // 无图片URL但需要OCR的
    const withoutImages = results.filter(r => !r.has_image_urls);
    if (withoutImages.length > 0) {
        console.log(`\n  📝 无图片URL的笔记 (${withoutImages.length} 个，需先获取图片):`);
        console.log('  ' + '─'.repeat(48));
        // 只显示前 20 个
        for (const r of withoutImages.slice(0, 20)) {
            console.log(`    ${r.id}  [${r.reason}]  desc=${r.desc_length}字`);
        }
        if (withoutImages.length > 20) {
            console.log(`    ... 还有 ${withoutImages.length - 20} 个`);
        }
    }

    console.log('\n═══════════════════════════════════════════════════\n');
}

main();
