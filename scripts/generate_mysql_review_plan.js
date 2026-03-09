const fs = require('fs');

const data = JSON.parse(fs.readFileSync('hashmap_slim.json', 'utf8'));
const qs = data.filter(q => q.domain && q.domain.l1 === '数据库' && q.domain.l2 === 'MySQL');

// Entity stats
const entityStats = {};
qs.forEach(q => {
    (q.tech_entities || []).forEach(e => {
        entityStats[e] = (entityStats[e] || 0) + 1;
    });
});
const sortedEntities = Object.entries(entityStats).sort((a, b) => b[1] - a[1]);

// Cognitive depth stats
const depthStats = {};
qs.forEach(q => {
    const d = q.cognitive_depth || 'Unknown';
    depthStats[d] = (depthStats[d] || 0) + 1;
});

// Question type stats
const typeStats = {};
qs.forEach(q => {
    const t = q.question_type || 'Unknown';
    typeStats[t] = (typeStats[t] || 0) + 1;
});

// Co-occurrence pairs
const pairs = {};
qs.forEach(q => {
    const ents = q.tech_entities || [];
    for (let i = 0; i < ents.length; i++) {
        for (let j = i + 1; j < ents.length; j++) {
            const arr = [ents[i], ents[j]].sort();
            const pairKey = arr[0] + ' + ' + arr[1];
            pairs[pairKey] = (pairs[pairKey] || 0) + 1;
        }
    }
});
const sortedPairs = Object.entries(pairs).sort((a, b) => b[1] - a[1]).slice(0, 15);

// Build the review plan
let md = `# 📋 MySQL 专项复习计划\n\n`;
md += `> 基于 ${qs.length} 道 MySQL 面试真题的数据分析生成。\n`;
md += `> 策略：**按知识模块分阶段递进，每个模块内按"概念→原理→实战"三段式推进**\n\n`;

md += `---\n\n`;
md += `## 📊 数据概览\n\n`;
md += `| 指标 | 数值 |\n|---|---|\n`;
md += `| 总题目数 | ${qs.length} |\n`;
md += `| 不重复技术实体 | ${sortedEntities.length} |\n`;
Object.entries(depthStats).sort((a, b) => b[1] - a[1]).forEach(([d, c]) => {
    md += `| ${d} | ${c} (${((c / qs.length) * 100).toFixed(1)}%) |\n`;
});

md += `\n## 🔗 高频"连环夺命问"组合 (面试官最爱绑定考的知识点对)\n\n`;
md += `| 排名 | 技术点组合 | 共同出现次数 | 典型问法 |\n`;
md += `|---|---|---|---|\n`;

const pairHints = {
    'redo log + undo log': '分别保证 ACID 的哪个特性？崩溃恢复时各自起什么作用？',
    'innodb + myisam': '两者有什么区别？为什么 InnoDB 成了默认引擎？',
    'b+树 + 索引': 'MySQL 索引为什么选择 B+树而不是 B 树或红黑树？',
    'mvcc + undo log': 'MVCC 底层是怎么通过 undo log 版本链实现的？',
    'mvcc + readview': 'ReadView 在 RC 和 RR 隔离级别下的生成时机有什么不同？',
    'mysql + 索引': '索引的底层数据结构是什么？什么场景下索引会失效？',
    'b+树 + innodb': 'InnoDB 的聚簇索引和非聚簇索引在 B+树上的存储有何不同？',
    'acid + undo log': 'undo log 保证了 ACID 中的哪个特性？',
    'readview + undo log': '一条 SELECT 在 RR 级别下是如何通过 ReadView 和版本链找到可见版本的？',
    'b+树 + 聚簇索引': '聚簇索引的 B+树叶子节点存的是什么？和非聚簇索引有什么区别？',
    '聚簇索引 + 非聚簇索引': '什么是回表？覆盖索引是怎么避免回表的？',
    'b+树 + mysql': '为什么 MySQL 用 B+树而不用哈希索引？',
    'b+树 + 磁盘io': 'B+树相比 B 树为什么能减少磁盘 IO 次数？',
    'acid + redo log': 'redo log 是如何保证持久性的？WAL 机制是什么？',
    'explain + 慢查询': '拿到一条慢 SQL，你会怎么用 explain 分析？关注哪些字段？'
};

sortedPairs.forEach(([pair, count], i) => {
    const hint = pairHints[pair] || '—';
    md += `| ${i + 1} | **${pair}** | ${count} | ${hint} |\n`;
});

md += `\n---\n\n`;
md += `## 🗓️ 分模块复习计划 (建议 3 天完成)\n\n`;

// Module 1: 索引体系
md += `### 📦 模块一：索引体系 (Day 1 上午)\n\n`;
md += `> 这是 MySQL 面试的**第一战场**，几乎每场面试必问。\n\n`;
md += `**核心实体：**\n`;
const indexEntities = ['b+树', '索引', '聚簇索引', '覆盖索引', '联合索引', '索引失效', '索引优化', '非聚簇索引', '唯一索引', '最左前缀'];
indexEntities.forEach(e => {
    const count = entityStats[e] || 0;
    if (count > 0) md += `- \`${e}\` (${count}次)\n`;
});
md += `\n**复习清单：**\n`;
md += `- [ ] B+树的结构特点，和 B 树、红黑树、哈希索引的区别\n`;
md += `- [ ] 聚簇索引 vs 非聚簇索引，回表是什么，覆盖索引怎么避免回表\n`;
md += `- [ ] 联合索引的最左前缀法则，什么时候索引会失效\n`;
md += `- [ ] explain 的关键字段：type、key、key_len、Extra\n`;
md += `- [ ] 索引优化实战：深度分页、order by 优化、count(*) 优化\n\n`;
md += `**抽题命令：**\n`;
md += `\`\`\`bash\nnode scripts/query_tagged.js entity --value "b+树" --slim\nnode scripts/query_tagged.js entity --value "索引失效" --slim\nnode scripts/query_tagged.js entity --value "覆盖索引" --slim\n\`\`\`\n\n`;

// Module 2: 事务与锁
md += `### 📦 模块二：事务与锁机制 (Day 1 下午)\n\n`;
md += `> MVCC + 锁 + 隔离级别是大厂 MySQL 面试的**深水区**。\n\n`;
md += `**核心实体：**\n`;
const txEntities = ['mvcc', '事务隔离级别', 'undo log', 'redo log', 'acid', 'readview', '间隙锁', '死锁', '乐观锁', '悲观锁', '行锁', '表锁', 'next-key lock'];
txEntities.forEach(e => {
    const count = entityStats[e] || 0;
    if (count > 0) md += `- \`${e}\` (${count}次)\n`;
});
md += `\n**复习清单：**\n`;
md += `- [ ] ACID 四大特性分别靠什么机制保证\n`;
md += `- [ ] 四种隔离级别及各自解决的问题（脏读/不可重复读/幻读）\n`;
md += `- [ ] MVCC 底层原理：undo log 版本链 + ReadView 可见性判断\n`;
md += `- [ ] RC 和 RR 下 ReadView 生成时机的区别\n`;
md += `- [ ] redo log vs undo log vs binlog 三者的区别与协作\n`;
md += `- [ ] 行锁、间隙锁、Next-Key Lock 的加锁规则\n`;
md += `- [ ] 死锁产生条件及排查方法\n\n`;
md += `**抽题命令：**\n`;
md += `\`\`\`bash\nnode scripts/query_tagged.js entity --value "mvcc" --slim\nnode scripts/query_tagged.js entity --value "undo log" --slim\nnode scripts/query_tagged.js entity --value "事务隔离级别" --slim\n\`\`\`\n\n`;

// Module 3: 存储引擎与日志
md += `### 📦 模块三：存储引擎与日志系统 (Day 2 上午)\n\n`;
md += `> InnoDB 架构 + 三大日志是理解 MySQL 内核的基石。\n\n`;
md += `**核心实体：**\n`;
const engineEntities = ['innodb', 'myisam', 'buffer pool', 'binlog', 'redo log', 'undo log', 'wal', '两阶段提交', '主从复制'];
engineEntities.forEach(e => {
    const count = entityStats[e] || 0;
    if (count > 0) md += `- \`${e}\` (${count}次)\n`;
});
md += `\n**复习清单：**\n`;
md += `- [ ] InnoDB vs MyISAM 核心区别（事务、锁、外键、崩溃恢复）\n`;
md += `- [ ] InnoDB 内存架构：Buffer Pool、Change Buffer、Log Buffer\n`;
md += `- [ ] WAL 机制：为什么先写日志再写磁盘\n`;
md += `- [ ] redo log + binlog 的两阶段提交保证一致性\n`;
md += `- [ ] 主从复制原理：binlog → relay log → SQL 线程回放\n\n`;
md += `**抽题命令：**\n`;
md += `\`\`\`bash\nnode scripts/query_tagged.js entity --value "innodb" --slim\nnode scripts/query_tagged.js entity --value "binlog" --slim\nnode scripts/query_tagged.js entity --value "buffer pool" --slim\n\`\`\`\n\n`;

// Module 4: SQL 优化与慢查询
md += `### 📦 模块四：SQL 优化与慢查询排查 (Day 2 下午)\n\n`;
md += `> 面试中区分"会用 MySQL"和"精通 MySQL"的分水岭。\n\n`;
md += `**核心实体：**\n`;
const tuningEntities = ['慢查询', 'explain', '索引优化', '分库分表', '深度分页', 'sql优化', '查询优化', '执行计划'];
tuningEntities.forEach(e => {
    const count = entityStats[e] || 0;
    if (count > 0) md += `- \`${e}\` (${count}次)\n`;
});
md += `\n**复习清单：**\n`;
md += `- [ ] 慢查询发现与定位：slow_query_log + explain\n`;
md += `- [ ] explain 各字段含义及优化方向\n`;
md += `- [ ] 深度分页优化方案（延迟关联、游标分页）\n`;
md += `- [ ] 大表优化策略：分库分表、读写分离\n`;
md += `- [ ] 常见 SQL 写法优化（避免 select *、减少子查询等）\n\n`;
md += `**抽题命令：**\n`;
md += `\`\`\`bash\nnode scripts/query_tagged.js entity --value "慢查询" --slim\nnode scripts/query_tagged.js entity --value "分库分表" --slim\nnode scripts/query_tagged.js entity --value "explain" --slim\n\`\`\`\n\n`;

// Module 5: 高可用与分布式
md += `### 📦 模块五：高可用与分布式 (Day 3)\n\n`;
md += `> 社招/高级岗位的加分项，校招面试中出现频率也在上升。\n\n`;
md += `**核心实体：**\n`;
const haEntities = ['分库分表', '主从复制', '读写分离', '分布式事务', 'shardingsphere', '数据迁移', '分布式id'];
haEntities.forEach(e => {
    const count = entityStats[e] || 0;
    if (count > 0) md += `- \`${e}\` (${count}次)\n`;
});
md += `\n**复习清单：**\n`;
md += `- [ ] 主从复制延迟问题及解决方案\n`;
md += `- [ ] 读写分离的实现方式及一致性保证\n`;
md += `- [ ] 分库分表的拆分策略（水平/垂直）\n`;
md += `- [ ] 分库分表后的问题：跨库 join、分布式事务、全局 ID\n`;
md += `- [ ] 数据迁移与扩容方案\n\n`;
md += `**抽题命令：**\n`;
md += `\`\`\`bash\nnode scripts/query_tagged.js entity --value "分库分表" --slim\nnode scripts/query_tagged.js entity --value "主从复制" --slim\n\`\`\`\n\n`;

// Summary checklist
md += `---\n\n`;
md += `## ✅ 总复习进度追踪\n\n`;
md += `| 模块 | 核心考点数 | 状态 |\n`;
md += `|---|---|---|\n`;
md += `| 模块一：索引体系 | ${indexEntities.filter(e => entityStats[e]).length} | ⬜ 未开始 |\n`;
md += `| 模块二：事务与锁 | ${txEntities.filter(e => entityStats[e]).length} | ⬜ 未开始 |\n`;
md += `| 模块三：引擎与日志 | ${engineEntities.filter(e => entityStats[e]).length} | ⬜ 未开始 |\n`;
md += `| 模块四：SQL 优化 | ${tuningEntities.filter(e => entityStats[e]).length} | ⬜ 未开始 |\n`;
md += `| 模块五：高可用 | ${haEntities.filter(e => entityStats[e]).length} | ⬜ 未开始 |\n`;

fs.writeFileSync('review/mysql/mysql_review_plan.md', md, 'utf8');
console.log('Successfully generated review/mysql/mysql_review_plan.md');
