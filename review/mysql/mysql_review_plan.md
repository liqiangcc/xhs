# 📋 MySQL 专项复习计划

> 基于 645 道 MySQL 面试真题的数据分析生成。
> 策略：**按知识模块分阶段递进，每个模块内按"概念→原理→实战"三段式推进**
> **详细题目清单：** [detailed_review_questions.md](file:///c:/Users/liqiang12/IdeaProjects/xhs/review/mysql/detailed_review_questions.md)

---

## 📊 数据概览

| 指标 | 数值 |
|---|---|
| 总题目数 | 645 |
| 不重复技术实体 | 508 |
| L2_Mechanism | 331 (51.3%) |
| L1_Principle | 251 (38.9%) |
| L3_Diagnostic | 62 (9.6%) |
| N_A | 1 (0.2%) |

## 🔗 高频"连环夺命问"组合 (面试官最爱绑定考的知识点对)

| 排名 | 技术点组合 | 共同出现次数 | 典型问法 |
|---|---|---|---|
| 1 | **redo log + undo log** | 19 | 分别保证 ACID 的哪个特性？崩溃恢复时各自起什么作用？ |
| 2 | **innodb + myisam** | 17 | 两者有什么区别？为什么 InnoDB 成了默认引擎？ |
| 3 | **b+树 + 索引** | 17 | MySQL 索引为什么选择 B+树而不是 B 树或红黑树？ |
| 4 | **mvcc + undo log** | 17 | MVCC 底层是怎么通过 undo log 版本链实现的？ |
| 5 | **mvcc + readview** | 13 | ReadView 在 RC 和 RR 隔离级别下的生成时机有什么不同？ |
| 6 | **mysql + 索引** | 12 | 索引的底层数据结构是什么？什么场景下索引会失效？ |
| 7 | **b+树 + innodb** | 10 | InnoDB 的聚簇索引和非聚簇索引在 B+树上的存储有何不同？ |
| 8 | **acid + undo log** | 10 | undo log 保证了 ACID 中的哪个特性？ |
| 9 | **readview + undo log** | 9 | 一条 SELECT 在 RR 级别下是如何通过 ReadView 和版本链找到可见版本的？ |
| 10 | **b+树 + 聚簇索引** | 9 | 聚簇索引的 B+树叶子节点存的是什么？和非聚簇索引有什么区别？ |
| 11 | **聚簇索引 + 非聚簇索引** | 9 | 什么是回表？覆盖索引是怎么避免回表的？ |
| 12 | **b+树 + mysql** | 9 | 为什么 MySQL 用 B+树而不用哈希索引？ |
| 13 | **b+树 + 磁盘io** | 9 | B+树相比 B 树为什么能减少磁盘 IO 次数？ |
| 14 | **acid + redo log** | 8 | redo log 是如何保证持久性的？WAL 机制是什么？ |
| 15 | **explain + 慢查询** | 7 | 拿到一条慢 SQL，你会怎么用 explain 分析？关注哪些字段？ |

---

## 🗓️ 分模块复习计划 (建议 3 天完成)

### 📦 模块一：索引体系 (Day 1 上午)

> 这是 MySQL 面试的**第一战场**，几乎每场面试必问。

**核心实体：**
- `b+树` (99次)
- `索引` (32次)
- `聚簇索引` (23次)
- `覆盖索引` (16次)
- `联合索引` (18次)
- `索引失效` (24次)
- `索引优化` (12次)
- `非聚簇索引` (10次)
- `唯一索引` (6次)
- `最左前缀` (6次)

**复习清单：**
- [ ] B+树的结构特点，和 B 树、红黑树、哈希索引的区别
- [ ] 聚簇索引 vs 非聚簇索引，回表是什么，覆盖索引怎么避免回表
- [ ] 联合索引的最左前缀法则，什么时候索引会失效
- [ ] explain 的关键字段：type、key、key_len、Extra
- [ ] 索引优化实战：深度分页、order by 优化、count(*) 优化

**抽题命令：**
```bash
node scripts/query_tagged.js entity --value "b+树" --slim
node scripts/query_tagged.js entity --value "索引失效" --slim
node scripts/query_tagged.js entity --value "覆盖索引" --slim
```

### 📦 模块二：事务与锁机制 (Day 1 下午)

> MVCC + 锁 + 隔离级别是大厂 MySQL 面试的**深水区**。

**核心实体：**
- `mvcc` (48次)
- `事务隔离级别` (11次)
- `undo log` (35次)
- `redo log` (23次)
- `acid` (24次)
- `readview` (15次)
- `间隙锁` (10次)
- `死锁` (1次)
- `乐观锁` (5次)
- `悲观锁` (5次)
- `行锁` (4次)
- `表锁` (2次)
- `next-key lock` (15次)

**复习清单：**
- [ ] ACID 四大特性分别靠什么机制保证
- [ ] 四种隔离级别及各自解决的问题（脏读/不可重复读/幻读）
- [ ] MVCC 底层原理：undo log 版本链 + ReadView 可见性判断
- [ ] RC 和 RR 下 ReadView 生成时机的区别
- [ ] redo log vs undo log vs binlog 三者的区别与协作
- [ ] 行锁、间隙锁、Next-Key Lock 的加锁规则
- [ ] 死锁产生条件及排查方法

**抽题命令：**
```bash
node scripts/query_tagged.js entity --value "mvcc" --slim
node scripts/query_tagged.js entity --value "undo log" --slim
node scripts/query_tagged.js entity --value "事务隔离级别" --slim
```

### 📦 模块三：存储引擎与日志系统 (Day 2 上午)

> InnoDB 架构 + 三大日志是理解 MySQL 内核的基石。

**核心实体：**
- `innodb` (37次)
- `myisam` (18次)
- `buffer pool` (4次)
- `binlog` (18次)
- `redo log` (23次)
- `undo log` (35次)
- `wal` (3次)
- `两阶段提交` (1次)
- `主从复制` (2次)

**复习清单：**
- [ ] InnoDB vs MyISAM 核心区别（事务、锁、外键、崩溃恢复）
- [ ] InnoDB 内存架构：Buffer Pool、Change Buffer、Log Buffer
- [ ] WAL 机制：为什么先写日志再写磁盘
- [ ] redo log + binlog 的两阶段提交保证一致性
- [ ] 主从复制原理：binlog → relay log → SQL 线程回放

**抽题命令：**
```bash
node scripts/query_tagged.js entity --value "innodb" --slim
node scripts/query_tagged.js entity --value "binlog" --slim
node scripts/query_tagged.js entity --value "buffer pool" --slim
```

### 📦 模块四：SQL 优化与慢查询排查 (Day 2 下午)

> 面试中区分"会用 MySQL"和"精通 MySQL"的分水岭。

**核心实体：**
- `慢查询` (9次)
- `explain` (23次)
- `索引优化` (12次)
- `分库分表` (14次)
- `深度分页` (4次)
- `sql优化` (4次)
- `查询优化` (1次)
- `执行计划` (3次)

**复习清单：**
- [ ] 慢查询发现与定位：slow_query_log + explain
- [ ] explain 各字段含义及优化方向
- [ ] 深度分页优化方案（延迟关联、游标分页）
- [ ] 大表优化策略：分库分表、读写分离
- [ ] 常见 SQL 写法优化（避免 select *、减少子查询等）

**抽题命令：**
```bash
node scripts/query_tagged.js entity --value "慢查询" --slim
node scripts/query_tagged.js entity --value "分库分表" --slim
node scripts/query_tagged.js entity --value "explain" --slim
```

### 📦 模块五：高可用与分布式 (Day 3)

> 社招/高级岗位的加分项，校招面试中出现频率也在上升。

**核心实体：**
- `分库分表` (14次)
- `主从复制` (2次)
- `读写分离` (2次)
- `shardingsphere` (1次)
- `数据迁移` (1次)

**复习清单：**
- [ ] 主从复制延迟问题及解决方案
- [ ] 读写分离的实现方式及一致性保证
- [ ] 分库分表的拆分策略（水平/垂直）
- [ ] 分库分表后的问题：跨库 join、分布式事务、全局 ID
- [ ] 数据迁移与扩容方案

**抽题命令：**
```bash
node scripts/query_tagged.js entity --value "分库分表" --slim
node scripts/query_tagged.js entity --value "主从复制" --slim
```

---

## ✅ 总复习进度追踪

| 模块 | 核心考点数 | 状态 |
|---|---|---|
| 模块一：索引体系 | 10 | 🚧 进行中 |
| 模块二：事务与锁 | 13 | ⬜ 未开始 |
| 模块三：引擎与日志 | 9 | ⬜ 未开始 |
| 模块四：SQL 优化 | 8 | ⬜ 未开始 |
| 模块五：高可用 | 5 | ⬜ 未开始 |
