const fs = require('fs');
const d = JSON.parse(fs.readFileSync('hashmap_slim.json', 'utf8'));

// Build L2 stats again
const l2Stats = {};
const l2Entities = {};

d.forEach(q => {
    if (!q.domain || !q.domain.l1 || !q.domain.l2) return;
    const l2 = q.domain.l1 + ' -> ' + q.domain.l2;
    l2Stats[l2] = (l2Stats[l2] || 0) + 1;

    if (!l2Entities[l2]) l2Entities[l2] = {};
    (q.tech_entities || []).forEach(e => {
        l2Entities[l2][e] = (l2Entities[l2][e] || 0) + 1;
    });
});

let md = '# 📋 面试题复习计划 (纯净终极版)\n\n';
md += '> 基于最新清洗且完全合并过的 `tech_entities` 数据生成。\n';
md += '> 策略：**按优先级 P0→P1→P2 顺次复习，以 L2 领域为骨架，深挖核心 entity**\n\n---\n\n';

md += '## 🔴 P0 — 必须掌握（高频核心，建议前 3 天搞定）\n\n';

const p0 = [
    { name: '数据库 -> MySQL', days: 'Day 1' },
    { name: 'Java -> 并发编程(JUC)', days: 'Day 2' },
    { name: '中间件 -> Redis', days: 'Day 3' }
];

p0.forEach(t => {
    md += '### ' + t.name + ' (' + l2Stats[t.name] + '题) - 📅 ' + t.days + '\n';
    const ents = Object.entries(l2Entities[t.name] || {}).sort((a, b) => b[1] - a[1]).slice(0, 8);
    md += '**👑 核心实体 Top 8：**\n';
    md += ents.map(e => '`' + e[0] + '`(' + e[1] + ')').join(' | ') + '\n\n';
    md += '**⚡ 建议抽题命令：**\n';
    md += '```bash\n';
    ents.slice(0, 4).forEach(e => {
        md += 'node scripts/query_tagged.js entity --value "' + e[0] + '" --slim\n';
    });
    md += '```\n\n';
});

md += '---\n## 🟡 P1 — 重点领域（大厂必问，建议中间 4 天搞定）\n\n';

const p1 = [
    { name: 'Java -> JVM', days: 'Day 4' },
    { name: 'Java -> 集合框架', days: 'Day 5' },
    { name: '计算机网络 -> TCP/IP', days: 'Day 5' },
    { name: '框架 -> Spring/SpringBoot', days: 'Day 6' },
    { name: '中间件 -> Kafka', days: 'Day 7' },
    { name: '中间件 -> RocketMQ', days: 'Day 7' }
];

p1.forEach(t => {
    if (!l2Stats[t.name]) return;
    md += '### ' + t.name + ' (' + l2Stats[t.name] + '题) - 📅 ' + t.days + '\n';
    const ents = Object.entries(l2Entities[t.name] || {}).sort((a, b) => b[1] - a[1]).slice(0, 6);
    md += '**👑 核心实体 Top 6：**\n';
    md += ents.map(e => '`' + e[0] + '`(' + e[1] + ')').join(' | ') + '\n\n';
    md += '**⚡ 建议抽题命令：**\n';
    md += '```bash\n';
    if (ents.length > 0) md += 'node scripts/query_tagged.js entity --value "' + ents[0][0] + '" --slim\n';
    if (ents.length > 1) md += 'node scripts/query_tagged.js entity --value "' + ents[1][0] + '" --slim\n';
    md += '```\n\n';
});

md += '---\n## 🟢 P2 — 进阶与系统设计（区分度，最后 3 天主攻）\n\n';

const p2 = [
    { name: '系统设计 -> 系统设计', days: 'Day 8-9' },
    { name: '中间件 -> Elasticsearch', days: 'Day 10' },
    { name: '云原生 -> Docker/K8s', days: 'Day 10' }
];

p2.forEach(t => {
    if (!l2Stats[t.name]) return;
    md += '### ' + t.name + ' (' + l2Stats[t.name] + '题) - 📅 ' + t.days + '\n';
    const ents = Object.entries(l2Entities[t.name] || {}).sort((a, b) => b[1] - a[1]).slice(0, 6);
    md += '**👑 核心实体 Top 6：**\n';
    md += ents.map(e => '`' + e[0] + '`(' + e[1] + ')').join(' | ') + '\n\n';
});

fs.writeFileSync('review/review_plan.md', md, 'utf8');
console.log('Successfully updated review/review_plan.md');
