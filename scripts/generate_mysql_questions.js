const fs = require('fs');

const data = JSON.parse(fs.readFileSync('hashmap_slim.json', 'utf8'));

// Filter MySQL questions
const mysqlQuestions = data.filter(q => q.domain && q.domain.l1 === '数据库' && q.domain.l2 === 'MySQL');

// Group by Cognitive Depth
const groups = {
    'L1_Principle': [],
    'L2_Mechanism': [],
    'L3_Diagnostic': [],
    'Unknown': []
};

mysqlQuestions.forEach(q => {
    const depth = q.cognitive_depth || 'Unknown';
    if (!groups[depth]) groups[depth] = [];
    groups[depth].push(q);
});

// Sort each group by tech_entities popularity for better review flow, 
// but for simplicity we'll just sort them alphabetically by question so similar ones group together
Object.keys(groups).forEach(depth => {
    groups[depth].sort((a, b) => a.original_question.localeCompare(b.original_question));
});

let md = `# MySQL 领域全量面试题库\n\n`;
md += `> 共计收录 ${mysqlQuestions.length} 道 MySQL 相关面试题。\n`;
md += `> 💡 建议复习顺序：1️⃣ 基础概念 (L1_Principle) ➡️ 2️⃣ 运行机制与核心原理 (L2_Mechanism) ➡️ 3️⃣ 实战诊断与调优 (L3_Diagnostic)\n\n`;

// Helper to escape pipes for markdown tables
function safeString(str) {
    if (!str) return '-';
    return String(str).replace(/\|/g, '\\|').replace(/\n/g, '<br>');
}

// Generate markdown sections
const depthsOrder = ['L1_Principle', 'L2_Mechanism', 'L3_Diagnostic', 'Unknown'];

depthsOrder.forEach(depth => {
    const qs = groups[depth];
    if (qs && qs.length > 0) {
        md += `## ${depth} (${qs.length} 道题目)\n\n`;
        md += `| 题目 | 相关技术点 (Entities) | 题型 (Type) |\n`;
        md += `|---|---|---|\n`;

        qs.forEach(q => {
            const ents = (q.tech_entities || []).join(', ');
            md += `| ${safeString(q.original_question)} | ${safeString(ents)} | ${safeString(q.question_type)} |\n`;
        });
        md += `\n`;
    }
});

fs.writeFileSync('review/mysql/mysql_questions.md', md, 'utf8');
console.log(`Successfully generated review/mysql/mysql_questions.md containing ${mysqlQuestions.length} questions.`);
