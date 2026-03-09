const fs = require('fs');
const path = require('path');

const data = JSON.parse(fs.readFileSync('hashmap_slim.json', 'utf8'));

// Filter MySQL questions
const mysqlQuestions = data.filter(q => q.domain && q.domain.l1 === '数据库' && q.domain.l2 === 'MySQL');

const totalCount = mysqlQuestions.length;

// Aggregation objects
const cognitiveDepthStats = {};
const questionTypeStats = {};
const entityStats = {};

mysqlQuestions.forEach(q => {
    // Cognitive Depth
    const depth = q.cognitive_depth || 'Unknown';
    cognitiveDepthStats[depth] = (cognitiveDepthStats[depth] || 0) + 1;

    // Question Type
    const qType = q.question_type || 'Unknown';
    questionTypeStats[qType] = (questionTypeStats[qType] || 0) + 1;

    // Entities
    (q.tech_entities || []).forEach(e => {
        entityStats[e] = (entityStats[e] || 0) + 1;
    });
});

// Sort stats
const sortedDepth = Object.entries(cognitiveDepthStats).sort((a, b) => b[1] - a[1]);
const sortedType = Object.entries(questionTypeStats).sort((a, b) => b[1] - a[1]);
const sortedEntities = Object.entries(entityStats).sort((a, b) => b[1] - a[1]);

// Generate Markdown
let md = `# MySQL 领域专属统计报告\n\n`;
md += `> **总计题目数量：** ${totalCount} 道\n`;
md += `> **涵盖知识点(实体)总数：** ${sortedEntities.length} 个\n\n`;

md += `## 🧠 认知深度分布 (Cognitive Depth)\n\n`;
md += `| 认知图谱层级 | 题数 | 占比 |\n`;
md += `|---|---|---|\n`;
sortedDepth.forEach(([depth, count]) => {
    const percentage = ((count / totalCount) * 100).toFixed(1) + '%';
    md += `| ${depth} | ${count} | ${percentage} |\n`;
});

md += `\n## 📝 题型分布 (Question Type)\n\n`;
md += `| 题目类型 | 题数 | 占比 |\n`;
md += `|---|---|---|\n`;
sortedType.forEach(([qType, count]) => {
    const percentage = ((count / totalCount) * 100).toFixed(1) + '%';
    md += `| ${qType} | ${count} | ${percentage} |\n`;
});

md += `\n## 👑 核心技术实体 Top 30 (Tech Entities)\n\n`;
md += `| 排名 | 技术点 (Entity) | 出现频次 | 重点建议 |\n`;
md += `|---|---|---|---|\n`;

sortedEntities.slice(0, 30).forEach(([entity, count], index) => {
    const rank = index + 1;
    let focus = '';
    if (rank <= 5) focus = '⭐⭐⭐⭐⭐ 必考核心';
    else if (rank <= 15) focus = '⭐⭐⭐⭐ 高频重点';
    else focus = '⭐⭐⭐ 常见考点';

    md += `| ${rank} | **${entity}** | ${count} | ${focus} |\n`;
});

md += `\n## 💡 下一步复习建议\n\n`;
md += `你可以使用本地查询命令，按照以上高频 \`tech_entities\` 逐个突破 MySQL 领域：\n\n`;
md += `\`\`\`bash\n`;
md += `# 按实体抽刷最核心的考点（比如：mysql）\n`;
md += `node scripts/query_tagged.js entity --value \"mysql\" --slim\n\n`;
md += `# 按认知深度复习（从浅入深：先刷 L1 原理）\n`;
md += `node scripts/query_tagged.js domain --l2 \"MySQL\" --depth \"L1_Principle\" --slim\n`;
md += `\`\`\`\n`;

fs.writeFileSync('review/mysql/mysql_stats.md', md, 'utf8');
console.log('Successfully generated review/mysql/mysql_stats.md');
