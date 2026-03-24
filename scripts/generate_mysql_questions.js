const fs = require('fs');

const data = JSON.parse(fs.readFileSync('hashmap_slim.json', 'utf8'));

// Filter MySQL questions
const mysqlQuestions = data.filter(q => q.domain && q.domain.l1 === '数据库' && q.domain.l2 === 'MySQL');

const depthPriority = ['L1_Principle', 'L2_Mechanism', 'L3_Diagnostic', 'Unknown'];
const entityThemes = [
    {
        name: '索引体系',
        test: value => /(索引|index|b\+树|b-tree|b tree|哈希索引|hash index|聚簇|非聚簇|clustered|covering|回表|最左|icp|页分裂|page split)/i.test(value)
    },
    {
        name: '事务与锁',
        test: value => /(事务|acid|mvcc|readview|read view|隔离|isolation|脏读|幻读|不可重复读|锁|lock|next-key|gap lock|行锁|表锁|死锁)/i.test(value)
    },
    {
        name: '日志与恢复',
        test: value => /(binlog|redo log|undo log|relay log|wal|crash|恢复|备份|backup|point-in-time|2pc|两阶段提交)/i.test(value)
    },
    {
        name: '存储引擎',
        test: value => /(innodb|myisam|buffer pool|存储引擎)/i.test(value)
    },
    {
        name: 'SQL 与执行计划',
        test: value => /(sql|explain|join|group by|having|exists|优化器|执行器|执行计划|慢查询|deep paging|limit|offset|分页)/i.test(value)
    },
    {
        name: '架构与高可用',
        test: value => /(replication|主从|分库分表|sharding|读写分离|高可用|canal|主从延迟|半同步复制|异步复制)/i.test(value)
    },
    {
        name: '建模与数据类型',
        test: value => /(varchar|char|text|decimal|数据类型|建表|schema|primary key|foreign key|主键|外键|规范化)/i.test(value)
    }
];

function pickPrimaryDepth(depths) {
    for (const depth of depthPriority) {
        if (depths.has(depth)) return depth;
    }

    return 'Unknown';
}

function normalizeType(type) {
    return type || 'Unknown';
}

function classifyEntityThemes(entities) {
    const themes = new Set();

    entities.forEach(entity => {
        entityThemes.forEach(theme => {
            if (theme.test(entity)) {
                themes.add(theme.name);
            }
        });
    });

    if (themes.size === 0) {
        themes.add('其他');
    }

    return [...themes];
}

const mergedQuestionMap = new Map();

mysqlQuestions.forEach(q => {
    const key = q.question_id || q.original_question;

    if (!mergedQuestionMap.has(key)) {
        mergedQuestionMap.set(key, {
            question_id: q.question_id || '-',
            original_question: q.original_question || '-',
            depths: new Set(),
            questionTypes: new Set(),
            techEntities: new Set(),
            rawCount: 0
        });
    }

    const merged = mergedQuestionMap.get(key);
    merged.rawCount += 1;

    merged.depths.add(q.cognitive_depth || 'Unknown');
    merged.questionTypes.add(normalizeType(q.question_type));
    (q.tech_entities || []).forEach(entity => merged.techEntities.add(entity));
});

const mergedQuestions = [...mergedQuestionMap.values()].map(item => {
    const entities = [...item.techEntities].sort((a, b) => a.localeCompare(b, 'zh-CN'));
    const questionTypes = [...item.questionTypes].sort((a, b) => a.localeCompare(b, 'zh-CN'));

    return {
        question_id: item.question_id,
        original_question: item.original_question,
        cognitive_depth: pickPrimaryDepth(item.depths),
        question_types: questionTypes,
        question_type: questionTypes.join(' / '),
        tech_entities: entities,
        entity_themes: classifyEntityThemes(entities),
        raw_count: item.rawCount
    };
});

// Group by Cognitive Depth
const groups = {
    'L1_Principle': [],
    'L2_Mechanism': [],
    'L3_Diagnostic': [],
    'Unknown': []
};

mergedQuestions.forEach(q => {
    const depth = q.cognitive_depth || 'Unknown';
    if (!groups[depth]) groups[depth] = [];
    groups[depth].push(q);
});

// Sort each group by tech_entities popularity for better review flow, 
// but for simplicity we'll just sort them alphabetically by question so similar ones group together
Object.keys(groups).forEach(depth => {
    groups[depth].sort((a, b) => a.original_question.localeCompare(b.original_question));
});

const typeGroups = {};
mergedQuestions.forEach(q => {
    q.question_types.forEach(type => {
        if (!typeGroups[type]) typeGroups[type] = [];
        typeGroups[type].push(q);
    });
});

Object.keys(typeGroups).forEach(type => {
    typeGroups[type].sort((a, b) => a.original_question.localeCompare(b.original_question));
});

const entityThemeGroups = {};
mergedQuestions.forEach(q => {
    q.entity_themes.forEach(theme => {
        if (!entityThemeGroups[theme]) entityThemeGroups[theme] = [];
        entityThemeGroups[theme].push(q);
    });
});

Object.keys(entityThemeGroups).forEach(theme => {
    entityThemeGroups[theme].sort((a, b) => a.original_question.localeCompare(b.original_question));
});

let md = `# MySQL 领域全量面试题库\n\n`;
md += `> 原始记录 ${mysqlQuestions.length} 条，合并重复题后共 ${mergedQuestions.length} 道唯一 MySQL 面试题。\n`;
md += `> 💡 建议复习顺序：1️⃣ 基础概念 (L1_Principle) ➡️ 2️⃣ 运行机制与核心原理 (L2_Mechanism) ➡️ 3️⃣ 实战诊断与调优 (L3_Diagnostic)\n\n`;
md += `## 使用说明\n\n`;
md += `- **主表**：按认知深度分组，适合纵向复习。\n`;
md += `- **附录 A**：按题型分组，适合按面试问法集中刷题。\n`;
md += `- **附录 B**：按 Entities 主题归并分组，适合按知识模块查漏补缺。\n`;
md += `- **重复题处理**：同一 Question ID 的重复记录已合并，Entities 会自动并集。\n\n`;

md += `## 快速导航\n\n`;
md += `- [主表：按认知深度](#主表按认知深度)\n`;
md += `- [附录 A：按 Type 分组](#附录-a按-type-分组)\n`;
md += `- [附录 B：按 Entities 主题分组](#附录-b按-entities-主题分组)\n\n`;

md += `## 主表：按认知深度\n\n`;

// Helper to escape pipes for markdown tables
function safeString(str) {
    if (!str) return '-';
    return String(str).replace(/\|/g, '\\|').replace(/\n/g, '<br>');
}

function renderQuestionTable(items) {
    let section = `| Question ID | 题目 | 相关技术点 (Entities) | 题型 (Type) |\n`;
    section += `|---|---|---|---|\n`;

    items.forEach(q => {
        const ents = q.tech_entities.join(', ');
        section += `| ${q.question_id} | ${safeString(q.original_question)} | ${safeString(ents)} | ${safeString(q.question_type)} |\n`;
    });

    return `${section}\n`;
}

// Generate markdown sections
const depthsOrder = ['L1_Principle', 'L2_Mechanism', 'L3_Diagnostic', 'Unknown'];

depthsOrder.forEach(depth => {
    const qs = groups[depth];
    if (qs && qs.length > 0) {
        md += `## ${depth} (${qs.length} 道题目)\n\n`;
        md += renderQuestionTable(qs);
    }
});

md += `## 附录 A：按 Type 分组\n\n`;
md += `| Type | 唯一题数 |\n`;
md += `|---|---|\n`;

Object.keys(typeGroups)
    .sort((a, b) => typeGroups[b].length - typeGroups[a].length || a.localeCompare(b, 'zh-CN'))
    .forEach(type => {
        md += `| ${safeString(type)} | ${typeGroups[type].length} |\n`;
    });

md += `\n`;

Object.keys(typeGroups)
    .sort((a, b) => typeGroups[b].length - typeGroups[a].length || a.localeCompare(b, 'zh-CN'))
    .forEach(type => {
        md += `### ${safeString(type)} (${typeGroups[type].length} 道题目)\n\n`;
        md += renderQuestionTable(typeGroups[type]);
    });

md += `## 附录 B：按 Entities 主题分组\n\n`;
md += `> 说明：本附录按技术实体做主题归并；一题可能同时归入多个主题，用于横向检索。\n\n`;
md += `| Entities 主题 | 唯一题数 |\n`;
md += `|---|---|\n`;

Object.keys(entityThemeGroups)
    .sort((a, b) => entityThemeGroups[b].length - entityThemeGroups[a].length || a.localeCompare(b, 'zh-CN'))
    .forEach(theme => {
        md += `| ${safeString(theme)} | ${entityThemeGroups[theme].length} |\n`;
    });

md += `\n`;

Object.keys(entityThemeGroups)
    .sort((a, b) => entityThemeGroups[b].length - entityThemeGroups[a].length || a.localeCompare(b, 'zh-CN'))
    .forEach(theme => {
        md += `### ${safeString(theme)} (${entityThemeGroups[theme].length} 道题目)\n\n`;
        md += renderQuestionTable(entityThemeGroups[theme]);
    });

fs.writeFileSync('review/mysql/mysql_questions.md', md, 'utf8');
console.log(`Successfully generated review/mysql/mysql_questions.md containing ${mergedQuestions.length} merged questions from ${mysqlQuestions.length} raw rows.`);
