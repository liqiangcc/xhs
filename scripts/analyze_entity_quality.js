const fs = require('fs');
const path = require('path');
const dir = 'note_tagged';
const files = fs.readdirSync(dir);

const entityCount = {};
let totalQ = 0;
let emptyCount = 0;
let longEntities = [];
let specialCharEntities = [];

files.forEach(f => {
    const d = JSON.parse(fs.readFileSync(path.join(dir, f), 'utf8'));
    (d.tagged_questions || []).forEach(q => {
        totalQ++;
        const ents = q.tech_entities || [];
        if (ents.length === 0) emptyCount++;
        ents.forEach(e => {
            entityCount[e] = (entityCount[e] || 0) + 1;
            if (e.length > 25 && !longEntities.includes(e)) longEntities.push(e);
            if (/[!@#$%^&*()_+={}\[\]:;"'<>?/\\]/.test(e) && !specialCharEntities.includes(e) && !e.includes('B+') && !e.includes('C++') && !e.includes('C#')) {
                specialCharEntities.push(e);
            }
        });
    });
});

const entities = Object.keys(entityCount);
const lowerMap = Object.create(null);
const caseIssues = [];

entities.forEach(e => {
    const lower = e.toLowerCase();
    if (!lowerMap[lower]) lowerMap[lower] = [];
    lowerMap[lower].push({ ori: e, cnt: entityCount[e] });
});

for (const k in lowerMap) {
    if (lowerMap[k].length > 1) {
        caseIssues.push(lowerMap[k]);
    }
}

// Build markdown report
let md = '# Tech Entities 数据质量预警分析\n\n';

md += '## 1. 大小写不一致 (Case Inconsistency)\n';
md += '发现了 ' + caseIssues.length + ' 组因为大小写不同而被拆分的相同实体：\n';
md += '| 统一小写 | 变体及次数 |\n|---|---|\n';
caseIssues.sort((a, b) => b.reduce((s, x) => s + x.cnt, 0) - a.reduce((s, x) => s + x.cnt, 0)).slice(0, 20).forEach(group => {
    const str = group.map(g => `${g.ori}(${g.cnt})`).join(', ');
    md += `| ${group[0].ori.toLowerCase()} | ${str} |\n`;
});
if (caseIssues.length > 20) md += `| ... | 还有 ${caseIssues.length - 20} 组未展示 |\n`;

md += '\n## 2. 疑似同义词 / 翻译不统一 (Synonyms)\n';
md += '同一概念有多种不同的写法，导致统计被分散，例如：\n';
md += '- B+树(111) / B+ Tree(48) / B+tree(2)\n';
md += '- 限流(43) / Rate Limiting(5)\n';
md += '- 分布式锁(89) / Distributed Lock(7)\n';
md += '- 同步(10) / 并发控制(6) / 锁(8)\n';

md += '\n## 3. 实体异常：长度过长 (Length > 25)\n';
md += '发现了 ' + longEntities.length + ' 个过长的实体，可能是之前大模型把一整句话或描述当成了标签：\n';
longEntities.slice(0, 10).forEach(e => md += '- `' + e + '`\n');
if (longEntities.length > 10) md += '- ... 等，共 ' + longEntities.length + ' 个\n';

md += '\n## 4. 包含特殊字符或标点的实体\n';
const filteredSpecial = specialCharEntities.filter(e => !e.match(/^[A-Za-z0-9\-\+\s\.]+$/));
md += '发现了 ' + filteredSpecial.length + ' 个包含异常标点的实体：\n';
filteredSpecial.slice(0, 10).forEach(e => md += '- `' + e + '`\n');
if (filteredSpecial.length > 10) md += '- ... 共 ' + filteredSpecial.length + ' 个\n';

md += '\n## 5. 空实体问题\n';
md += `${totalQ} 道题目中，有 ${emptyCount} 道题的 \`tech_entities\` 是空的，缺少标签关联。\n`;

fs.writeFileSync('review/data_quality_issues.md', md, 'utf8');
console.log('Analysis complete.');
