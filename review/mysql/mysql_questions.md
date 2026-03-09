# MySQL 领域全量面试题库

> 共计收录 645 道 MySQL 相关面试题。
> 💡 建议复习顺序：1️⃣ 基础概念 (L1_Principle) ➡️ 2️⃣ 运行机制与核心原理 (L2_Mechanism) ➡️ 3️⃣ 实战诊断与调优 (L3_Diagnostic)

## L1_Principle (251 道题目)

| 题目 | 相关技术点 (Entities) | 题型 (Type) |
|---|---|---|
| 辨析 MySQL 事务隔离级别：什么是不可重复读与幻读？ | transaction isolation, phantom read, non-repeatable read | 八股文_Concept |
| 辨析 MySQL 事务隔离级别：什么是不可重复读与幻读？ | transaction isolation, rr vs rc | 八股文_Concept |
| 场景题：表 A 和表 B 的内连接与左连接结果分析 | inner join, left join | 八股文_Concept |
| 创建索引的时候需要考虑哪些问题？ | 索引设计原则, 区分度 | 八股文_Concept |
| 读锁 and 写锁在 SQL 命令中的添加方式（悲观锁实现） | 悲观锁, select for update | 八股文_Concept |
| 读已提交（RC）会导致什么问题？ | mysql, 事务 | 八股文_Concept |
| 对比 MySQL 常用的存储引擎（如 InnoDB 与 MyISAM）的特性 | innodb, myisam | 八股文_Concept |
| 对比 MySQL 中的 `FOR SHARE` 和 `FOR UPDATE` 的区别 | 共享锁, 排他锁 | 八股文_Concept |
| 对比悲观锁与乐观锁的应用场景 | 乐观锁, 悲观锁 | 八股文_Concept |
| 二叉树架构：为什么 MySQL 选择 B+ 树作为索引结构而不是平衡二叉树（AVL/红黑树）？从树高与随机 IO 角度分析？ | b+树, 随机io, 树高 | 八股文_Concept |
| 分库分表的策略有哪些？ | 分库分表 | 八股文_Concept |
| 分库分表是怎么做的？ | 分库分表 | 八股文_Concept |
| 覆盖索引？ | 覆盖索引, 联合索引 | 八股文_Concept |
| 覆盖索引与回表查询？ | 覆盖索引, 回表 | 八股文_Concept |
| 高性能索引设计：在什么情况下需要建立联合索引？如何确定索引列的最佳顺序？ | composite index, cardinality | 场景设计_Scenario |
| 关系型数据库：谈谈你对数据库事务（Transaction）的理解？ | transaction | 八股文_Concept |
| 回表？ | 回表, 二级索引, 聚簇索引 | 八股文_Concept |
| 简单描述 MySQL 中, 索引, 主键, 唯一索引, 联合索引的区别 | 主键索引, 唯一索引, 联合索引, 普通索引 | 八股文_Concept |
| 解释一下 MySQL EXPLAIN 执行计划的各个字段 | explain | 八股文_Concept |
| 解释最左前缀原则及常见的索引失效场景？ | 联合索引, 索引失效 | 八股文_Concept |
| 介绍一下联合索引吧 | 联合索引 | 八股文_Concept |
| 聚簇索引和非聚簇索引？ | 聚簇索引, 非聚簇索引, b+树 | 八股文_Concept |
| 聚簇索引和非聚簇索引的区别 | clustered index | 八股文_Concept |
| 聚簇索引与非聚簇索引，索引失效的情况 | 聚簇/非聚簇索引, 回表查询, 覆盖索引, 最左前缀索引失效 | 八股文_Concept |
| 聚簇索引与非聚簇索引的区别？ | clustered index | 八股文_Concept |
| 聚簇索引原理：叶子节点直接存储完整数据行的物理组织方式？ | clustered index | 八股文_Concept |
| 看索引是否命中是哪个字段? | key, possible_keys | 八股文_Concept |
| 可以说一说Mysql幻读和脏读的区别吗？ | mysql, 幻读, 脏读 | 八股文_Concept |
| 了解数据库隔离性吗？ | 事务隔离级别, acid | 八股文_Concept |
| 了解MySQL的索引吗？有什么用 | mysql, 索引 | 八股文_Concept |
| 利用数据库表介绍 EXISTS 关键字 (返回 TRUE 还是 FALSE)? | exists, semi-join | 八股文_Concept |
| 联合索引：在什么情况下索引会失效（如违背最左匹配原则、范围查询、函数操作等）？ | composite index, leftmost prefix rule | 八股文_Concept |
| 慢SQL调优的具体步骤有哪些？ | mysql, sql调优 | 八股文_Concept |
| 哪些情况下会导致 MySQL 索引失效？ | 索引失效, 联合索引 | 八股文_Concept |
| 哪些情况下会导致数据库索引失效？特别地，联合索引在什么情况下会失效？ | 最左前缀法则, 表达式失效 | 八股文_Concept |
| 哪些数据结构的插入和查询复杂度是 O(1) 的？请分析 MySQL B+ 树索引的效率优势 | b+树, 时间复杂度 | 八股文_Concept |
| 请对比聚簇索引和非聚簇索引的区别 | 聚簇索引, 非聚簇索引 | 八股文_Concept |
| 请解释 MySQL 中行锁与表锁的概念及各自适用的业务场景 | 行锁, 表锁 | 八股文_Concept |
| 请解释数据库事务中的 ACID 特性及其实现方式 | acid, mvcc | 八股文_Concept |
| 请解释最左前缀匹配原则及其重要性 | 索引原则 | 八股文_Concept |
| 请介绍 MySQL 中 explain 命令的作用及关键字段含义。 | explain, mysql | 八股文_Concept |
| 请介绍传输层的核心协议（TCP, UDP） | 最左前缀 | 八股文_Concept |
| 请介绍读写分离的适用场景及其解决的核心问题 | 读写分离 | 八股文_Concept |
| 请介绍数据库索引底层的常用数据结构 | b+树, hash index | 八股文_Concept |
| 请列举 MySQL 事务的四大特性（ACID），并解释不同的隔离级别分别解决了哪些并发问题（脏读、不可重复读、幻读） | acid, 隔离级别 | 八股文_Concept |
| 请详细介绍 MySQL 中有哪些常见的锁（如行锁、间隙锁、临键锁、意向锁等） | mysql锁, next-key lock | 八股文_Concept |
| 请详细介绍数据库索引的概念及其分类 | 索引, 唯一索引, 联合索引 | 八股文_Concept |
| 如何避免 MySQL 索引失效？ | 索引失效 | 八股文_Concept |
| 什么情况下不建议使用数据库索引？ | 索引失效 | 八股文_Concept |
| 什么情况下设置了索引但无法使用 | 索引失效, 左模糊, 隐式转换, 函数计算, 优化器放弃索引 | 八股文_Concept |
| 什么情况下设置了索引但无法使用? | 索引失效 | 八股文_Concept |
| 什么时候需要用到事务？ | 事务 | 八股文_Concept |
| 什么是覆盖索引？ | 覆盖索引 | 八股文_Concept |
| 什么是覆盖索引（Covering Index）？ | 覆盖索引 | 八股文_Concept |
| 什么是覆盖索引与回表查询？ | 覆盖索引, 回表 | 八股文_Concept |
| 什么是回表？什么时候会触发回表？ | 回表, 二级索引 | 八股文_Concept |
| 什么是事务的隔离级别？MySQL默认是哪 个？ | 事务, 隔离级别 | 八股文_Concept |
| 什么是数据库索引？它的本质是什么？ | 索引, b+树 | 八股文_Concept |
| 什么是索引？为什么数据库需要索引？ | database index | 八股文_Concept |
| 什么是索引覆盖？ | 覆盖索引, 回表 | 八股文_Concept |
| 什么是索引覆盖（Index Covering）？它能带来哪些性能提升？ | 覆盖索引 | 八股文_Concept |
| 什么是脏读？什么是幻读？ | mysql, 事务 | 八股文_Concept |
| 实际使用中见过哪些索引？ | 索引, b+树, 聚簇索引 | 八股文_Concept |
| 事务的 ACID 四大特性解析？ | acid | 八股文_Concept |
| 事务日志：Redo Log 与 Undo Log 分别保证了事务的哪些特性（ACID）？ | redo log, undo log | 八股文_Concept |
| 事务一致性：详细分析本地事务（ACID）在交易链路中的边界界定？ | transaction boundary, acid | 八股文_Concept |
| 数据库 Schema 设计：主键（Primary Key）与外键（Foreign Key）的作用及其对数据一致性的影响？ | primary key, foreign key | 八股文_Concept |
| 数据库：聚簇索引与非聚簇索引：数据与索引绑定机制及“回表”查询的性能损耗分析 | clustered index | 八股文_Concept |
| 数据库：请说明 MySQL 的事务隔离级别以及 MVCC（多版本并发控制）的实现原理 | isolation level, mvcc | 八股文_Concept |
| 数据库：一条 SQL 语句从应用端发出到返回结果，在 MySQL 内部经历了哪些核心过程（如解析、缓存、优化器、执行器、存储引擎）？ | 执行路径 | 原理深度_UnderTheHood |
| 数据库：在 SQL 中什么是聚合函数？请列举 5 个常用的聚合函数及其典型用途。 | 聚合函数, count, sum, avg, max, min | 八股文_Concept |
| 数据库：Binlog 的三种格式 (Statement, Row, Mixed) 及各自的写入时机考量 | binlog | 八股文_Concept |
| 数据库：GROUP BY 和 HAVING 的区别是什么？ | group by, having | 八股文_Concept |
| 数据库：INNER JOIN, LEFT JOIN, RIGHT JOIN 之间有什么区别？ | join | 八股文_Concept |
| 数据库：MySQL 常用日志体系 (Binlog, Redo Log, Undo Log, Relay Log) 的功能与写入时机 | mysql logs | 八股文_Concept |
| 数据库：MySQL 索引选型：为什么 B+ 树比 B 树更适合大规模磁盘 IO？ | b+树, disk i/o | 八股文_Concept |
| 数据库：MySQL各种索引结构对比；为什么 B+ 树优于 B 树？ | b+树 | 八股文_Concept |
| 数据库：MySQL主键设计的必要性分析 | primary key | 八股文_Concept |
| 数据库：SQL 统计重复数据：GROUP BY 与 HAVING COUNT(*) > 1 的应用 | group by, having | 八股文_Concept |
| 数据库的隔离级别有哪些？MySQL 默认使用的是哪种？ | 隔离级别, rr | 八股文_Concept |
| 数据库隔离级别有哪些? | 隔离级别 | 八股文_Concept |
| 数据库核心：ACID 特性的具体含义及其在 MySQL 中的实现支柱？ | acid, redo log, undo log | 八股文_Concept |
| 数据库核心：ACID 特性的具体含义及其在 MySQL 中的实现支柱？ | acid, redo/undo log | 八股文_Concept |
| 数据库事务的隔离级别有哪些？分别解决了哪些并发执行中的问题（如脏读、不可重复读、幻读）？ | 隔离级别 | 八股文_Concept |
| 数据库事务的隔离级别有哪些？MySQL默认是哪种？ | transaction, isolation levels | 八股文_Concept |
| 数据库索引：聚簇索引的应用场景与B+树底层布局 | clustered index, b+树 | 八股文_Concept |
| 数据库索引：聚簇索引与非聚簇索引，覆盖索引 | 聚簇索引, 非聚簇索引, 覆盖索引 | 八股文_Concept |
| 数据库索引：在实际项目中，你是如何设置数据库索引的？为什么“索引覆盖”（Covering Index）能显著提升查询速度？ | covering index, index optimization | 八股文_Concept |
| 数据库索引：B 树与 B+ 树在结构及查询效率上有何区别？ | b+树, b-树 | 八股文_Concept |
| 数据库索引：MySQL 的索引（B+ 树）是如何实现的？为什么 B+ 树比 B 树更适合处理范围查询（Range Query）？ | b+树, b tree, range query | 八股文_Concept |
| 数据库索引：MySQL 索引设计的核心原则有哪些？在索引性能与存储效率上，自增 ID 为何通常优于 UUID？ | indexing principles, uuid vs auto-increment | 八股文_Concept |
| 数据库索引：MySQL InnoDB 为什么选择 B+ 树而非 Hash 索引或 B 树？ | b+树, index structure | 八股文_Concept |
| 数据库索引的底层结构（B+ 树 vs 哈希表）？ | b+树, 哈希索引 | 八股文_Concept |
| 数据库索引的底层结构（B+ 树 vs 哈希表）？ | b+树, 哈希索引 | 八股文_Concept |
| 数据库索引底层原理（B+ 树结构及优势）？ | b+树, indexing | 八股文_Concept |
| 数据库索引分类 | 索引分类, 聚集索引, 非聚集索引, 唯一索引 | 八股文_Concept |
| 数据库索引一般是用什么数据结构？和其它数据结构有什么区别？ | b+树, 哈希索引 | 八股文_Concept |
| 数据库性能：在 MySQL 中，单表数据量达到 2000w 以后性能会明显下降，其本质原因是什么（涉及 B+ 树层高、磁盘 I/O、内存命中率）？ | b+ tree tree height, disk i/o, buffer pool | 八股文_Concept |
| 数据库引擎有哪些？说说他们的区别 | innodb, myisam | 八股文_Concept |
| 说说索引的底层实现？ | b+树, 聚簇索引 | 八股文_Concept |
| 索引，InnoDB默认索引 | 索引, innodb | 八股文_Concept |
| 索引的使用 | 索引 | 八股文_Concept |
| 索引失效：请枚举并分析导致 MySQL 索引失效的常见场景（如函数操作、隐式转换、不等于判断等） | index invalidation | 八股文_Concept |
| 索引失效场景有哪些? | index optimization | 八股文_Concept |
| 索引一定越多越好吗？ | 索引优化, dml回推 | 八股文_Concept |
| 索引优化：复合索引（A, B, C）与分别建立 A, B, C 单个索引在查询性能与磁盘空间上的区别？ | 联合索引, 索引命中 | 八股文_Concept |
| 谈谈 MySQL 的事务机制 | acid, mvcc | 八股文_Concept |
| 为什么要高并发下发数据不推荐关系数据库？ | 关系数据库, iops, 连接数连接池 | 原理深度_UnderTheHood |
| 为什么用 B+ 树？ | b+树, 磁盘io | 八股文_Concept |
| 为什么MyISAM查询性能好? | myisam | 八股文_Concept |
| 问了一下mysql，堆栈 | mysql, 堆, 栈, 数据结构 | 八股文_Concept |
| 详细罗列 MySQL 索引失效的几种常见情况？ | index optimization | 八股文_Concept |
| 在查找数据时，聚簇索引 (Clustered Index) 与非聚簇索引 (Secondary Index) 的主要区别是什么？ | 聚集索引, 回表 | 原理深度_UnderTheHood |
| 在什么情况下 MySQL 索引会失效？平时你是如何进行索引问题的排查与定位的？ | 索引实战 | 场景设计_Scenario |
| 在实际开发中，你会遵循哪些原则来创建索引？ | b+树 | 八股文_Concept |
| 在数据库设计中，索引建立过多会对系统产生哪些负面影响？ | index overhead | 八股文_Concept |
| 怎么理解 MySQL 事务的四大特性 (ACID)？ | acid | 八股文_Concept |
| 主键索引 and 唯一索引的区别 | 主键, 唯一索引 | 八股文_Concept |
| 最左前缀原则及索引失效场景？ | 最左前缀匹配, 索引失效 | 八股文_Concept |
| 最左前缀原则示例 | 最左前缀原则 | 八股文_Concept |
| B+ 树与 B 树的区别？ | b+树, b tree | 八股文_Concept |
| B+树相比 B 树的优势 | b+树, b tree, disk io | 八股文_Concept |
| B+Tree 索引与数据量 | b+tree层级高度估算, 页数据块大小, 叶子节点数据承载量, 两三千万行数据阈值 | 八股文_Concept |
| DML 和 DDL 是什么? | dml, ddl | 八股文_Concept |
| InnoDB 存储引擎的核心事务隔离级别是什么？辨析可重复读（RR）与读已提交（RC）的区别？ | transaction isolation, rr vs rc | 八股文_Concept |
| Innodb 的索引结构和 myisam 有区别吗? | innodb, myisam, b+树 | 八股文_Concept |
| Innodb 的索引结构和 myisam 有区别吗？ | 聚簇索引, 非聚簇索引, b+树叶子节点, innodb, myisam | 八股文_Concept |
| InnoDB 的索引类型有哪些？聚簇索引与非聚簇索引的区别是什么？ | 聚簇索引, 非聚簇索引, innodb | 八股文_Concept |
| InnoDB 和 Myisam 的区别 | innodb, myisam, 事务, 行级锁, 外键, 崩溃恢复 | 八股文_Concept |
| InnoDB 和MyISAM区别 | innodb, myisam | 八股文_Concept |
| InnoDB 默认隔离级别 | rr, 可重复读 | 八股文_Concept |
| InnoDB 默认隔离级别是什么? 解决了什么问题? | rr, 不可重复读 | 八股文_Concept |
| InnoDB 中有哪些锁类型（行锁/表锁/间隙锁/临键锁）？ | mysql locks, next-key lock | 八股文_Concept |
| InnoDB和MyISAM的区别 | innodb, myisam, 存储引擎 | 八股文_Concept |
| Innode 的索引结构和 myisam 有区别吗？ | innodb, myisam, b+树 | 八股文_Concept |
| MyISAM 和 InnoDB 的区别是什么? | myisam, innodb, 存储引擎 | 八股文_Concept |
| MySQL 存储引擎：深入剖析 InnoDB 的 B+ 树索引结构，以及为什么这一结构最适合做磁盘存储？ | b+树, clustered index | 八股文_Concept |
| MySQL 存储引擎：InnoDB 为什么优先选择 B+ 树作为索引结构，而非 B 树、红黑树或平衡二叉树？ | b+树, innodb | 原理深度_UnderTheHood |
| MySQL 存储引擎比较 | innodb, myisam | 八股文_Concept |
| MySQL 存储引擎对比：InnoDB 与 MyISAM 的关键技术差异（锁、索引、事务支持）？ | innodb, myisam, mvcc | 八股文_Concept |
| MySQL 存储引擎有哪些？区别是什么？ | innodb, myisam | 八股文_Concept |
| MySQL 的常见优化手段有哪些？ | sql优化, 索引优化, 分库分表 | 八股文_Concept |
| MySQL 的隔离级别有哪些？默认级别是什么？可重复读（RR）解决了哪些并发问题？ | 隔离级别, rr | 八股文_Concept |
| MySQL 的事务隔离级别有哪些？并发事务可能会导致哪些问题？ | 隔离级别, 脏读, 不可重复读, 幻读 | 八股文_Concept |
| MySQL 的索引结构是什么？有哪些特点？ | b+树, 索引 | 八股文_Concept |
| MySQL 的索引是什么结构？ | b+树, 哈希索引 | 八股文_Concept |
| MySQL 的一级索引 and 二级索引的区别 | 聚簇索引, 二级索引 | 八股文_Concept |
| mysql 的主键索引和唯一索引有什么区别？ | 主键索引, 唯一索引 | 八股文_Concept |
| MySQL 高可用：常见的主从同步方案有哪些？请对比它们的优劣势 | replication | 八股文_Concept |
| MySQL 隔离级别：RR 级别下是如何解决幻读（Phantom Read）的（MVCC + Next-key Lock）？ | mvcc, next-key lock, phantom read | 八股文_Concept |
| MySQL 基础：Primary Key 与普通 Index 在底层存储及查询上有何区别？ | clustered index | 八股文_Concept |
| MySQL 架构：B+ 树相比 B 树在磁盘 I/O 次数及范围查询（Range Scan）上的核心性能改进？ | b+树, b tree, disk io | 八股文_Concept |
| MySQL 建表时需要考虑哪些因素？ | 建表规范, 字段选型, 索引设计 | 八股文_Concept |
| MySQL 里记录货币用什么字段类型好 | decimal, 浮点数精度损失, 整型转换 | 八股文_Concept |
| MySQL 联合索引：有三列 (a b c)，用 a=* 和 c=* 能够进行联合索引查询吗？ | 联合索引, 最左前缀匹配, 索引下推 | 坑题_Gotcha |
| MySQL 联合索引原理：a_b_c 三列联合索引的排序规则及最左前缀匹配？ | composite index, leftmost prefix | 八股文_Concept |
| MySQL 默认的隔离级别是什么? 解决了什么问题? | 隔离级别, rr | 八股文_Concept |
| MySQL 默认是什么存储引擎,为啥用这个? | innodb | 原理深度_UnderTheHood |
| MySQL 设计原则：谈谈你对数据库库表设计原则（规范化 vs 反规范化、属性选择、索引设计）的理解？ | 数据库设计, 规范化 | 原理深度_UnderTheHood |
| MySQL 事务的隔离级别，分别解决了什么问题？ | 事务隔离级别, 原子性, 隔离性 | 八股文_Concept |
| MySQL 事务的隔离级别，默认隔离级别是什么？ | mysql, 事务隔离级别, 可重复读 | 八股文_Concept |
| MySQL 事务隔离：详细辨析不可重复读（Non-repeatable Read）与幻读（Phantom Read）在并发事务中产生的根本原因？ | isolation level, concurrency issues | 八股文_Concept |
| MySQL 事务隔离级别及解决的问题？ | isolation levels, acid | 八股文_Concept |
| MySQL 事务特性 (ACID) 及隔离级别 | acid, 隔离级别 | 八股文_Concept |
| MySQL 数据库：在聊天系统中，哪些数据适合存放在关系型数据库中？ | relational data, user information, friendship | 场景设计_Scenario |
| MySQL 数据库的存储引擎了解过哪些? | 存储引擎, innodb, myisam | 八股文_Concept |
| MySQL 数据容灾：描述 MySQL 备份的最佳实践及其与 binlog 恢复流程的结合？ | mysql backup, point-in-time recovery | 八股文_Concept |
| MySQL 数据容灾：描述 MySQL 备份的最佳实践及其与 binlog 恢复流程的结合？ | mysql backup, point-in-time recovery | 八股文_Concept |
| MySQL 索引：回表与索引覆盖的概念？ | table lookup, covering index | 八股文_Concept |
| MySQL 索引：简述 MySQL 索引的实现原理。 | mysql, 索引 | 八股文_Concept |
| MySQL 索引：解释聚簇索引（Clustered Index）和覆盖索引（Covering Index）的概念及区别。 | mysql, 索引 | 八股文_Concept |
| MySQL 索引：介绍 MySQL 索引的底层数据结构。什么是最左前缀匹配原则？ | mysql, 索引, 最左匹配 | 八股文_Concept |
| MySQL 索引：详细辨析聚簇索引（Clustered Index）与非聚簇索引的 B+ 树叶子节点存储内容差异？如何精准避免回表？ | clustered index, non-clustered index | 八股文_Concept |
| MySQL 索引的底层数据结构是怎样的？ | b+树, 磁盘索引 | 八股文_Concept |
| MySQL 索引的底层原理是怎样的？ | acid | 八股文_Concept |
| mysql 索引结构，索引失效 etc? | b+树, 索引失效 | 八股文_Concept |
| MySQL 索引进阶：唯一索引（Unique Index）与普通索引在插入与查找性能上的细微差异？ | unique index, change buffer | 八股文_Concept |
| MySQL 索引深度：索引失效的常见场景分析？ | mysql index, index failure | 八股文_Concept |
| MySQL 索引深度：索引是越多越好吗？分析索引过多的负面影响（如 写入性能、空间成本）？ | 索引优化, 写放大 | 八股文_Concept |
| MySQL 索引失效场景：请详细列举至少三种导致 B+ 树索引失效的操作？ | index invalidation, like-prefix, function-on-column | 八股文_Concept |
| MySQL 索引失效的常见场景？ | 索引失效 | 八股文_Concept |
| MySQL 索引失效的场景有哪些？ | 索引失效, mysql, 最左前缀法则 | 八股文_Concept |
| MySQL 索引失效的场景有哪些？ | 索引失效, 最左前缀原则 | 八股文_Concept |
| MySQL 索引原理 | b+树, 聚簇索引, 二级索引 | 八股文_Concept |
| MySQL 锁机制：如何在 SQL 层面实现乐观锁与悲观锁？ | 乐观锁, 悲观锁 | 八股文_Concept |
| MySQL 一张表能创建几个 B+ 树索引？在什么情况下会触发“回表”操作？ | 非聚集索引, 回表 | 八股文_Concept |
| MySQL 有关权限的表都有哪几个 | 权限表, user, db, tables_priv, columns_priv | 八股文_Concept |
| MySQL 有缓存吗？ | query cache, buffer pool | 八股文_Concept |
| MySQL 运维：如何启动 MySQL 及其查看实例状态？ | mysql operation | 八股文_Concept |
| MySQL 在哪些情况下会发生“回表查询”？如何避免回表？ | 回表, 覆盖索引 | 八股文_Concept |
| MySQL 知识体系了解哪些? | mysql | 八股文_Concept |
| MySQL 中 MyISAM 与 InnoDB 的区别? | myisam, innodb, 事务支持, 锁粒度 | 八股文_Concept |
| MySQL 中 VARCHAR 与 CHAR 的区别以及 VARCHAR(50) 中的 50 代表的涵义是什么? | 数据类型, varchar, char | 八股文_Concept |
| MySQL 中 VARCHAR, CHAR, TEXT 三种类型的区别及适用场景？ | varchar, char, text | 八股文_Concept |
| MySQL 中包含哪些类型的索引？请分别简述其作用。 | mysql索引, b-tree索引, hash索引 | 八股文_Concept |
| MySQL 中导致索引失效的原因有哪些？ | mysql索引, 索引失效 | 八股文_Concept |
| MySQL 中的乐观锁与悲观锁应用场景及其具体实现方式？ | optimistic locking, pessimistic locking, version field | 八股文_Concept |
| MySQL 中索引的主要作用是什么？ | mysql索引 | 八股文_Concept |
| MySQL MVCC 实现原理：详细辨析实时读（Current Read）与快照读（Snapshot Read）的区别？ | mvcc, snapshot read | 八股文_Concept |
| MySQL undo log vs redo log | undo log, redo log, crash recovery | 八股文_Concept |
| MySQL：表数据量级达到多少建议水平分表？(千万级) | sharding threshold | 八股文_Concept |
| MySQL：常见数据类型及其用途；Char与Varchar在底层的具体存储区别 | varchar, char | 八股文_Concept |
| MySQL：隔离级别、幻读及MVCC隔离机制 | transaction isolation, phantom read, mvcc | 八股文_Concept |
| MySQL：聚簇索引与非聚簇索引的区别 | clustered index | 八股文_Concept |
| MySQL：如何显式创建聚簇索引与非聚簇索引？ | primary key, index creation | 八股文_Concept |
| MySQL：什么是索引？详述B+树索引结构及其优势 | b+树 | 八股文_Concept |
| MySQL：最左匹配原则详解 | 最左匹配原则 | 八股文_Concept |
| MySQL：B+树索引结构及其优势 | b+树 | 八股文_Concept |
| MySQL：MyISAM与InnoDB存储引擎性能差异及查询场景选型分析 | innodb, myisam | 八股文_Concept |
| MySQL：MySQL默认存储引擎及其特性优势 | innodb | 八股文_Concept |
| mysql常用索引类型 | b+树索引, hash索引 | 八股文_Concept |
| MySQL存储引擎：聚簇与非聚簇索引对比；B+树优势 | clustered index, innodb | 八股文_Concept |
| MySQL的三个日志（binlog, redo log, undo log）。 | mysql | 八股文_Concept |
| MySQL的事务隔离级别，分别解决什么问题。 | 隔离级别 | 八股文_Concept |
| MySQL的事务隔离级别？ | 事务隔离级别, read committed, repeatable read | 八股文_Concept |
| MySQL的事务隔离级别及其默认级别？ | 隔离级别, rr, rc | 八股文_Concept |
| MySQL的四个隔离级别。 | mysql, 事务 | 八股文_Concept |
| Mysql的索引类型和数据结构划分为哪些？ | mysql, 索引, b+树 | 八股文_Concept |
| MySQL分库分表。 | mysql, 分库分表 | 八股文_Concept |
| mysql隔离级别 | mysql, 隔离级别, 读未提交, 读已提交, 可重复读, 串行化 | 八股文_Concept |
| MySQL隔离级别 | 隔离级别 | 八股文_Concept |
| MySQL回表是什么？ | 回表, 二级索引 | 八股文_Concept |
| MySQL里主要有哪些索引结构?哈希索引和B+树索引比较? | b+树, 哈希索引 | 八股文_Concept |
| MySQL默认的事务隔离级别是哪个？ | mysql, 事务 | 八股文_Concept |
| MySQL默认事务级别 | 事务隔离级别 | 八股文_Concept |
| MySQL事务 | 事务, acid | 八股文_Concept |
| MySQL事务隔离级别? | 事务隔离级别, rc, rr | 八股文_Concept |
| MySQL事务隔离级别及其在该级别下分别解决的并发一致性问题 | mysql, 事务隔离级别, 脏读, 不可重复读, 幻读 | 八股文_Concept |
| mysql数据库默认存储引擎，有什么优点 | innodb | 八股文_Concept |
| MySQL索引：为什么选B+树而不是B树？ | b+树, b-tree | 八股文_Concept |
| MySQL索引：B+树索引结构及优势？ | b+树原理, 索引优点 | 八股文_Concept |
| MySQL索引结构分析：B+树的优势在哪里？ | b+树 | 八股文_Concept |
| MySQL索引剖析：B+树与Hash索引的区别；索引失效与覆盖索引场景分析 | index invalidation, covering index, hash index | 八股文_Concept |
| mysql索引有哪些 | 索引 | 八股文_Concept |
| MySQL索引有哪些？ | b+树索引, 哈希索引, 全文索引, 聚簇索引 | 八股文_Concept |
| MySQL锁有哪些？ | 表锁, 行锁, 间隙锁, 临键锁 | 八股文_Concept |
| MySQL有几种隔离级别？ | mysql, 事务 | 八股文_Concept |
| MySQL有哪几种日志？分别的功能是什么？ | mysql | 八股文_Concept |
| MySQL怎么分析SQL的性能（explain）？慢sql日志怎么开启？ | explain, 慢查询日志 | 八股文_Concept |
| MySQL中有哪些存储引擎？InnoDB和MyISAM的区别？ | mysql | 八股文_Concept |
| redo log, undo log, bin log 的原理和作用 | redo log, undo log, bin log, 事务持久性及回滚, 主从复制 | 八股文_Concept |
| SQL 查询优化中有哪些常用的方法？ | mysql | 八股文_Concept |
| SQL 基础：熟练使用 SELECT, INSERT, UPDATE, DELETE 关键字及 ORDER BY 排序？ | crud | 八股文_Concept |
| SQL 基础：MySQL 父子表关联方式、一对多查询实现及删除外键风险？ | 关联查询, 外键 | 八股文_Concept |
| SQL 中 Join 的作用及各类 Join 区别（INNER/LEFT/RIGHT/FULL）？ | sql join | 八股文_Concept |
| SQL：编写一个包含 Join On 的查询语句 | sql, join | 八股文_Concept |
| SQL：查找员工薪资第二高的信息 | sql, limit, offset | 八股文_Concept |
| SQL：如何找到表中不同 name 的个数？ | sql, distinct | 八股文_Concept |
| Varchar 和 Char | char, varchar, 变长字段, 空间利用率 | 八股文_Concept |
| varchar和char的区别 | varchar, char | 八股文_Concept |
| X 类型锁是什么? | exclusive lock | 八股文_Concept |

## L2_Mechanism (331 道题目)

| 题目 | 相关技术点 (Entities) | 题型 (Type) |
|---|---|---|
| [快手]Inno DB 如何解决幻读? | 幻读, mvcc, next-key lock | 原理深度_UnderTheHood |
| 不停机大规模数据迁移：如何将生产环境下 16 张大表平滑迁移并扩容至 64 张表？详述双写校对与切流后的回滚预案？ | 分库分表, 数据迁移, 双写 | 场景设计_Scenario |
| 查询语句使用 OFFSET + LIMIT 为什么会变慢？如何进行优化？ | mysql, 延迟关联 | 原理深度_UnderTheHood |
| 场景：快照读与当前读如何避免幻读？ | snapshot read, current read, next-key lock | 原理深度_UnderTheHood |
| 场景设计：数据量 1000 万的分页查询设计，每次查 20 条数据，如何优化深分页 SQL？ | 深分页优化, 自增id优化 | 系统设计_Architecture |
| 场景题：请使用乐观锁方案实现一个高并发下的 PV（页面访问量）统计功能 | cas sql | 场景设计_Scenario |
| 场景题：在一个包含 id 和 name 列的表中，幻读是如何发生的？ | 幻读 | 场景设计_Scenario |
| 除了索引优化，减少数据传输量具体可以怎么实现？ | mysql | 原理深度_UnderTheHood |
| 串行化解决了什么问题? 为什么不作为默认隔离级别? | 串行化, 幻读, 性能 | 原理深度_UnderTheHood |
| 存储引擎：辨析聚簇索引（Clustered Index）与非聚簇索引的物理存储结构区别？ | clustered index, non-clustered index | 原理深度_UnderTheHood |
| 存储引擎对比：MySQL (B+ Tree) 与 MongoDB 的核心优势架构对比，各自的适用业务场景？ | mysql, mongodb, b+树 | 八股文_Concept |
| 存储原理：MySQL 索引的叶子节点具体存储在内存还是磁盘的什么位置？Buffer Pool 的作用是什么？ | buffer pool, disk storage | 原理深度_UnderTheHood |
| 大数据量分页优化：如何利用“延迟关联”或“书签分页”技术优化“查询第 10000 页回答”的 deep paging 慢查询？ | 分页优化, 延迟关联 | 方案设计_Scenario |
| 代码阅读题 2 (SQL 优化)：对比两条 SQL 语句的执行效率。其中一条完全命中索引，另一条由于未覆盖索引导致“回表”查询，请解释其性能差异 | 回表, 覆盖索引 | 原理深度_UnderTheHood |
| 当 MySQL 表数据量达到百万/千万级时，为提高查询效率会采取哪些具体的索引优化手段？ | 索引优化, 大表查询 | 集成对接_Integration |
| 当前读（Locking Read）涉及哪些锁，不同 SQL 的锁分析？ | locking read, select for update | 原理深度_UnderTheHood |
| 当前读与快照读的区别? RC和RR级别的快照生成时机? | 当前读, 快照读, mvcc, readview | 原理深度_UnderTheHood |
| 读写分离（Read-Write Splitting）的实现方式及其导致的数据一致性（延迟）问题处理？ | read-write splitting, slave lag | 场景设计_Scenario |
| 读已提交 (RC) and 可重复读 (RR) 如何利用 MVCC 实现？ | rc, rr, readview | 原理深度_UnderTheHood |
| 多表关联查询性能优化：知乎核心“用户-回答-评论”关联查询频繁时，应采取何种索引设计或数据模型反规范化策略？ | 关联查询, 反规范化 | 方案设计_Scenario |
| 非聚簇索引的回表机制是什么？ | 回表, 非聚簇索引 | 原理深度_UnderTheHood |
| 非聚簇索引中的字段只存储了主键值吗? | index covering | 原理深度_UnderTheHood |
| 分布式 ID 与自增：MySQL 中 auto_increment 锁的模式及在高并发写入下的瓶颈？ | auto_increment, lock mode, distributed id | 原理深度_UnderTheHood |
| 分库分表：如何设计一个水平分库分表的方案？ | 分库分表 | 场景设计_Scenario |
| 分库分表后的全局统计挑战：如何实现跨 user_id 分片后的“全站热帖 TOP 100”查询流程？ | 分库分表, sharding | 场景设计_Scenario |
| 分片键怎么选？ | 分库分表 | 场景设计_Scenario |
| 分页查询时，如果数据量特别大，如何避免性能问题？ | 分页 | 原理深度_UnderTheHood |
| 隔离级别深度演进：RR 与 RC 模式下 MVCC 实现的具体差异？ | 隔离级别, rc, rr | 原理深度_UnderTheHood |
| 回表查询原理解析 | index lookup, bookmark lookup | 原理深度_UnderTheHood |
| 基础设施：数据库版本是多少？为什么选择“可重复读”（Repeatable Read）作为默认的事务隔离级别？Redis 采用的是几主几从的部署架构？ | repeatable read, redis replication | 原理深度_UnderTheHood |
| 技术对比：B+ 树结构相比 B 树有哪些优点？相比平衡二叉树、跳表又有何优劣？ | b+树, b树, skiplist | 原理深度_UnderTheHood |
| 建表为什么用自增主键？为什么不用uuid？ | 自增主键, uuid, 聚簇索引, b+树 | 原理深度_UnderTheHood |
| 介绍一下 MySQL 的 MVCC 机制，它主要是用来解决什么问题的？ | mvcc, readview, 版本链 | 原理深度_UnderTheHood |
| 金融级敏感数据存储加密：针对客户姓名、身份证号、银行卡号等敏感信息，如何在数据库层面实现加解密（如 AES-256）与脱敏策略？ | aes加密, 数据脱敏 | 原理深度_UnderTheHood |
| 金融历史交易记录冷热分离：针对 5 年以上历史记录查询慢的问题，如何设计基于时间维度的分库分表与 Elasticsearch/HBase 归档方案？ | 冷热分离, elasticsearch, 分库分表 | 架构设计_Architecture |
| 聚簇索引（Clustered Index）的适用场景有哪些？什么是页分裂（Page Splitting）问题？ | 聚集索引, 页分裂 | 原理深度_UnderTheHood |
| 聚簇索引使用场景及页分裂问题 | 聚簇索引, 页分裂 | 原理深度_UnderTheHood |
| 可重复读级别是怎么实现的（MVCC）？ | mvcc, read view, undo log | 原理深度_UnderTheHood |
| 可重复读解决了哪些问题 | 可重复读, 幻读 | 原理深度_UnderTheHood |
| 快照读和当前读 | mvcc, 快照读, 当前读, readview, undo log | 原理深度_UnderTheHood |
| 乐观锁与悲观锁在数据库层面上分别是如何实现的？ | 乐观锁, 悲观锁 | 原理深度_UnderTheHood |
| 了解过 b 树与 b+ 树的区别吗？为什么 b+ 树需要这么做？ | b-tree, b+树, 索引 | 原理深度_UnderTheHood |
| 联合索引：对于联合索引 `(A, B, C)`，执行 `WHERE B=1 AND A=2 AND C=3` 时，索引是否生效？请解释 MySQL 查询优化器（Optimizer）在此时的作用 | composite index, query optimizer | 原理深度_UnderTheHood |
| 联合索引：给定联合索引 `(a, b, c)`，执行查询 `WHERE a=1 AND b>2 AND c=3` 时，能用到哪些索引字段？请结合“最左前缀法则”详述索引失效的边界点 | composite index, leftmost prefix rule | 八股文_Concept |
| 联合索引：在创建联合索引时需要注意哪些事项（如最左匹配原则、区分度等）？ | 联合索引 | 原理深度_UnderTheHood |
| 联合索引(a, b, c)，where b = 1能否走索引？where a = 1呢？ | 联合索引, 最左前缀原则 | 场景设计_Scenario |
| 联合索引查询时的 B+ 树与单索引查询时的 B+ 树有什么区别？ | b+树, 联合索引排序, 组合键大小比较 | 原理深度_UnderTheHood |
| 联合索引失效场景：如 a, b 有索引，c 没有，查询条件 where c=xx and a=xx and b=xx 能否用索引？ | 联合索引, 索引失效, 最左匹配原则 | 原理深度_UnderTheHood |
| 联合索引原理及索引失效场景 | 联合索引, 索引失效, 最左前缀法则 | 原理深度_UnderTheHood |
| 慢查询排查：如何进行EXPLAIN分析、优化索引或重构SQL？ | mysql | 原理深度_UnderTheHood |
| 面对高并发写请求，如何评估并缓解数据库（DB）的写压力？ | write pressure, batch insert, async commit | 场景设计_Scenario |
| 模糊查询中 % 的位置对索引的影响？ | 模糊查询, like, 索引失效 | 原理深度_UnderTheHood |
| 哪些情况下索引会失效？除了增加索引，还有哪些优化查询的方法？ | 索引失效, 查询优化 | 八股文_Concept |
| 那怎么解决幻读呢？ | mysql, 幻读, mvcc, 间隙锁 | 原理深度_UnderTheHood |
| 评论系统性能优化：在大数据量场景下，评论楼层展示如何避免 SELECT COUNT(*) 导致的性能下降？ | select count, 性能优化 | 场景设计_Scenario |
| 请编写 SQL：给定订单表 order（字段：orderId, userId, time），查出所有用户各自最新的一个订单信息。 | sql, group by, 窗口函数 | 算法手撕_Coding |
| 请根据具体业务例子说明如何合理创建索引 | 索引优化 | 原理深度_UnderTheHood |
| 请简述 MySQL 主从复制的原理。 | binlog, relay log | 原理深度_UnderTheHood |
| 请解释 MySQL 事务的 ACID 特性。如果系统在事务执行期间意外宕机，MySQL 如何通过 redo log 与 binlog 的一致性检查来决定是否需要回滚事务？ | xa事务, 崩溃恢复 | 原理深度_UnderTheHood |
| 请介绍 MySQL 的四大日志（binlog, undolog, redolog, relaylog）及其作用，并说明日志与事务 ACID 特性的关系 | logs, acid, redo log, undo log | 原理深度_UnderTheHood |
| 请介绍 MySQL 索引及其底层数据结构。对于“性别”这种区分度较低的字段，是否适合建立索引？为什么？ | 索引区分度, b+树 | 原理深度_UnderTheHood |
| 请描述 MySQL 事务的四大特性（ACID），以及数据库是如何通过底层机制（如 redo/undo log, MVCC）来保证这些特性的？ | acid, mvcc, redo log, undo log | 原理深度_UnderTheHood |
| 请描述一条 MySQL SELECT 语句的完整执行流程 | 执行引擎, 查询优化器 | 原理深度_UnderTheHood |
| 请说明联合索引（复合索引）失效的具体情况及其背后的逻辑 | index failure, composite index | 原理深度_UnderTheHood |
| 请谈谈你对数据库索引及事务机制的理解。MySQL 是如何实现事务隔离级别的？ | 索引, mvcc | 原理深度_UnderTheHood |
| 请详细解释 MySQL 中的 MVCC（多版本并发控制）实现机制 | mvcc, read view | 原理深度_UnderTheHood |
| 请详细介绍 MySQL 里的索引，包括分类以及为什么选用 B+Tree 作为存储结构？ | b+树, 聚集索引, 非聚集索引 | 原理深度_UnderTheHood |
| 如果没有指定主键，InnoDB 会如何处理？是否会创建默认主键？ | innodb, 聚簇索引, rowid | 原理深度_UnderTheHood |
| 如果字段类型是数字，但在查询条件中将其与字符串进行比较，这种情况下会走索引吗？为什么？ | 隐式类型转换, sarg | 原理深度_UnderTheHood |
| 如何保证 MySQL 主库和从库之间的“强一致性”？ | 半同步复制, 全同步复制 | 原理深度_UnderTheHood |
| 如何搭建 MySQL 的主从集群？请详细解释异步复制和半同步复制的区别 | mysql复制, 异步复制, 半同步复制 | 原理深度_UnderTheHood |
| 如何解决幻读问题？ | mysql, 间隙锁, mvcc | 原理深度_UnderTheHood |
| 如何设计存储海量聊天数据的数据库表结构？请给出具体的索引优化策略？ | sharding, chat log table, composite index | 场景设计_Scenario |
| 如何通过 SQL 加锁来解决幻读问题？你所加的是什么锁（如 Gap Lock / Next-Key Lock）？ | 间隙锁, 临键锁 | 原理深度_UnderTheHood |
| 如何通过监听 Binlog 的方式保证数据一致性？ | canal, binlog | 原理深度_UnderTheHood |
| 三种日志的区别、WAL技术 | binlog, redo log, undo log, wal先行写日志, 原子性及两阶段提交 | 原理深度_UnderTheHood |
| 什么是 MySQL 的深度分页问题？如何解决？ | mysql, 深度分页 | 原理深度_UnderTheHood |
| 什么是覆盖索引？请举例说明索引失效的场景以及回表查询的原理。 | 覆盖索引, 索引失效, 回表查询 | 原理深度_UnderTheHood |
| 什么是联合索引？如果建立了 BCD 联合索引，按 BD 查询和按 CD 查询有什么区别？ | 联合索引, 最左匹配原则 | 原理深度_UnderTheHood |
| 什么是索引下推 (Index Condition Pushdown)？ | 索引下推, icp | 原理深度_UnderTheHood |
| 什么是跳表? 为何 MySQL 不使用跳表? | skip list, b+ tree contrast | 原理深度_UnderTheHood |
| 生产环境零停机数据扩容迁移：详述在不停机情况下将 16 张核心表扩容至 128 张表的完整迁移路径（双写、同步、灰度采样、平滑切流）？ | 数据库迁移, 双写 | 场景设计_Scenario |
| 实践中如何优化MySQL? | mysql调优 | 原理深度_UnderTheHood |
| 事务的 ACID 特性及其在 InnoDB 中的底层实现原理（Undo/Redo Log, MVCC, Locks）？ | acid, undo log, redo log, mvcc | 原理深度_UnderTheHood |
| 事务的四大特性 (ACID) 是什么？数据库系统是如何支持这些特性的？ | acid, redo log, undo log | 原理深度_UnderTheHood |
| 事务隔离：简述数据库的隔离级别。可重复读（RR）级别是如何实现的？MVCC 能否彻底解决幻读问题？ | mvcc, rr | 原理深度_UnderTheHood |
| 事务隔离：请详述 InnoDB 的 MVCC（多版本并发控制）实现原理。它是如何解决不可重复读与幻读问题的？ | mvcc, read view, undo log, repeatable read | 原理深度_UnderTheHood |
| 事务隔离：事务的各隔离级别（RU, RC, RR, Serializable）分别解决了哪些并发问题？在“可重复读”（RR）级别下，InnoDB 是如何解决“幻读”问题的？ | next-key lock, gap lock, phantom read | 原理深度_UnderTheHood |
| 事务隔离级别，如何避免幻读？ | 事务隔离级别, 幻读, 间隙锁, next-key lock, mvcc | 原理深度_UnderTheHood |
| 事务选择 | 事务隔离级别, acid | 场景设计_Scenario |
| 事务与并发：MySQL 的 MVCC（多版本并发控制）和两阶段提交（2PC）是如何实现的？ | mvcc, 2pc | 原理深度_UnderTheHood |
| 事务原理：什么是 ACID 特性？InnoDB 引擎分别是通过哪些机制（如 Redo Log, Undo Log, MVCC, Next-Key Lock）保证这些特性的？ | acid, mvcc, redo log, undo log | 原理深度_UnderTheHood |
| 数据表结构设计有哪些核心要点？在什么情况下会考虑分表策略？ | 分表, 范式设计 | 原理深度_UnderTheHood |
| 数据建模：在你的项目中，数据库表设计时主要选用了哪些数据类型（如 JSON, Decimal, DateTime）？选用依据及对索引性能的影响是什么？ | mysql data types, json storage, indexing performance | 场景设计_Scenario |
| 数据库：基于 B+ 树的索引存储原理：以“创建时间”字段索引为例描述存储结构 | compound index, non-clustered index | 原理深度_UnderTheHood |
| 数据库：如何编写复杂 SQL 实现数据统计？（考察点：聚合函数、JOIN 操作、窗口函数初探）。 | sql | 算法手撕_Coding |
| 数据库：在 MySQL 调优中，如何根据 `EXPLAIN` 命令的输出结果判断某个索引是否生效？请列举至少三个常见的索引失效场景。 | explain, 索引失效 | 原理深度_UnderTheHood |
| 数据库：在 MySQL 联合索引中，为什么“最左前缀原则”如此重要？如果查询条件跳过了联合索引的第一个字段，索引还能发挥作用吗？ | 最左前缀 | 原理深度_UnderTheHood |
| 数据库：在 MySQL 优化中，创建索引通常需要遵循哪些核心原则（如离散度高、覆盖索引、避免过度索引）？请列举至少两个典型的索引失效场景。 | 索引优化 | 原理深度_UnderTheHood |
| 数据库：在 MySQL 中，哪些情况下会导致索引失效？请描述 B+ 树索引的物理存储结构。 | b+树, 最左前缀 | 原理深度_UnderTheHood |
| 数据库：在 MySQL 中构建联合索引时，需要遵循什么原则（如最左前缀法则、离散度大的列在前、覆盖索引）？ | 联合索引 | 原理深度_UnderTheHood |
| 数据库：在 SQL 优化中，`EXISTS` 和 `IN` 子句哪个效率更高？请结合驱动表、索引命中及底层执行计划进行分析。 | exists, in, 执行计划 | 原理深度_UnderTheHood |
| 数据库：在技术选型时，如何评估 MySQL 与 PostgreSQL 的差异？为什么在某些高并发场景下会考虑使用 Elasticsearch (ES) 而非关系型数据库？ | postgresql, es | 经验思考_Reflection |
| 数据库：在什么情况下不建议为字段建立索引？请结合数据区分度、更新频率及表规模进行分析。 | 索引设计 | 经验思考_Reflection |
| 数据库：MySQL 的 InnoDB 存储引擎与 MyISAM 的索引结构有何本质区别？ | innodb, myisam, 聚簇索引 | 原理深度_UnderTheHood |
| 数据库：MySQL 的隔离级别有哪些？请详细描述 MVCC（多版本并发控制）的实现原理及其解决的问题。 | mvcc | 原理深度_UnderTheHood |
| 数据库：MySQL 联合索引的“最左匹配原则”及 B+ 树多列索引的存储结构 | composite index | 原理深度_UnderTheHood |
| 数据库：MySQL 索引的底层实现 (B+ Tree)；为什么 B+ 树在大规模磁盘存储中优于 B 树？ | b+树 | 原理深度_UnderTheHood |
| 数据库：MySQL 索引的底层原理是什么？索引有哪些优缺点？ | b+树, 索引 | 原理深度_UnderTheHood |
| 数据库：MySQL 索引体系详解：主键索引 (Clustered Index) 与 非主键索引 (Secondary Index) 的存储差异 | clustered index | 原理深度_UnderTheHood |
| 数据库：MySQL 中 B+ 树的层高通常受哪些因素（如 Page 大小、Key 长度、数据行大小）影响？如何根据层高估算表的数据容量上限？ | b+树, page | 原理深度_UnderTheHood |
| 数据库：MySQL 中常见的索引失效场景有哪些（如隐式类型转换、最左匹配失败、函数操作）？请口述如何创建一个全文索引并描述其应用场景。 | 全文索引 | 原理深度_UnderTheHood |
| 数据库：MySQL 中聚集索引 (Clustered Index) 和非聚集索引的区别是什么？ | clustered index, 二级索引 | 原理深度_UnderTheHood |
| 数据库：MySQL 主从同步 (Replication) 的底层原理与 Binlog 的解析交互过程 | mysql replication | 原理深度_UnderTheHood |
| 数据库：MySQL Binlog 的作用及应用场景 (如主从复制、数据恢复)；Binlog 在事务提交时的写入时机分析 | binlog | 原理深度_UnderTheHood |
| 数据库：SQL 中 join on 与 where 条件过滤的执行顺序差异分析 | sql execution order | 原理深度_UnderTheHood |
| 数据库：WHERE 过滤行与 HAVING 过滤组的底层执行顺序差异及对索引的影响 | sql execution order | 原理深度_UnderTheHood |
| 数据库的唯一索引是用哪些数据结构实现的 | 唯一索引, b+树, 哈希索引 | 原理深度_UnderTheHood |
| 数据库分库分表（ShardingSphere）在高频交易场景下的具体落地？ | shardingsphere, database sharding | 场景设计_Scenario |
| 数据库恢复策略 (WAL, redo log, undo log) 详解 | wal, redo log, undo log | 原理深度_UnderTheHood |
| 数据库架构：实习公司的数据库是如何部署的？请详细说明 MySQL 一主多从架构下是如何保证数据一致性的。 | mysql, 主从复制 | 原理深度_UnderTheHood |
| 数据库进阶：什么是存储过程？在现代高并发互联网架构中，为什么通常不建议使用存储过程？ | 存储过程 | 架构设计_Architecture |
| 数据库进阶：在实战中应对单表亿级数据时，你的分库分表拆分维度、中间件选型及扩容迁移方案如何？ | sharding, data migration, mycat | 场景设计_Scenario |
| 数据库进阶：在实战中应对单表亿级数据时，你的分库分表拆分维度、中间件选型及扩容迁移方案如何？ | sharding-jdbc, data migration, horizontal sharding | 场景设计_Scenario |
| 数据库连接池选型：京东商品服务为何从Druid切换到HikariCP？参数如何优化？ | 连接池, druid, hikaricp | 原理深度_UnderTheHood |
| 数据库设计：UUID 适合做数据库的主键吗？请从 B+ 树索引的分裂开销、存储效率与聚簇索引特性角度进行分析 | uuid, b+ tree fragmentation, clustered index | 原理深度_UnderTheHood |
| 数据库深度：MySQL RR 隔离级别下，MVCC（一致性读）结合 Next-Key Lock 解决幻读的具体推导过程？ | mvcc, next-key lock, phantom read | 原理深度_UnderTheHood |
| 数据库实践：在你的项目中，核心业务表的索引是如何设计的？ | mysql, 索引设计 | 项目深挖_Project |
| 数据库事务：请详述 MySQL 的四种事务隔离级别。InnoDB 引擎中的 MVCC（多版本并发控制）机制是如何利用 Undo Log 和 Read View 实现快照读的？ | mvcc, undo log, readview | 原理深度_UnderTheHood |
| 数据库事务的持久性（Durability）是怎么实现的？ | redo log, 持久性 | 原理深度_UnderTheHood |
| 数据库事务的原子性（Atomicity）是怎么实现的？ | undo log, 原子性 | 原理深度_UnderTheHood |
| 数据库索引：给定复合索引（A, B），分析在不同查询条件下索引的生效情况（最左匹配原则）。 | 复合索引, 最左匹配 | 原理深度_UnderTheHood |
| 数据库索引：在联合索引场景下，如果前缀字段使用了范围查询（Range Query），后续字段的“最左匹配原则（Leftmost Prefix Rule）”会发生什么变化？ | composite index, range query invalidation | 原理深度_UnderTheHood |
| 数据库索引：MySQL 索引的底层数据结构是什么？在什么特定业务场景下会考虑使用哈希索引（Hash Index）而非 B+ Tree？ | b+树, hash index physics, search complexity | 原理深度_UnderTheHood |
| 数据库索引：MySQL 索引为什么采用 B+ 树？请解释最左匹配原则与回表查询的概念 | b+树, index lookback | 原理深度_UnderTheHood |
| 数据库索引的底层实现原理和优化 | b+树, 索引 | 原理深度_UnderTheHood |
| 数据库索引的底层原理（B+树） | b+树, 索引, 聚簇索引, 非聚簇索引, 页分裂 | 原理深度_UnderTheHood |
| 数据库索引在更新、新增场景下是否会被使用？详述聚集索引与非聚集索引的差异？ | 索引, 聚集索引 | 原理深度_UnderTheHood |
| 数据库性能：JOIN 查询中“小表驱动大表”的理论依据与执行优化？ | nested loop join | 原理深度_UnderTheHood |
| 数据库一致性：MySQL 如何通过三色日志（Binlog, Redo, Undo）协作保证事务的 ACID 特性？ | binlog, redo log, undo log, acid | 原理深度_UnderTheHood |
| 数据库灾备优化：在高并发环境下，如果主库发生故障，如何设计快速切换与数据零丢失方案？ | replication, failover, mha, orchestrator | 场景设计_Scenario |
| 数据同步：Canal 的工作原理及其如何保证主从/异构数据库间的数据一致性？ | canal, 数据同步 | 原理深度_UnderTheHood |
| 说一下 MySQL 的日志 (binlog, redo log, undo log) | mysql日志 | 原理深度_UnderTheHood |
| 算法：手撕实现特定的复杂 SQL 查询场景 (业务多表关联与聚合) | sql coding | 算法手撕_Coding |
| 索引的底层实现原理和优化 | b+树, 聚簇索引, 覆盖索引, 索引下推 | 原理深度_UnderTheHood |
| 索引的结构是什么？B+ 树结构的叶子节点和非叶子节点有什么区别？B+ 树最底层是双向链表有什么好处？ | b+树原理结构, 内节点只存键值不存数据, 叶子节点存数据与主键, 底层双向链表范围扫描优化 | 原理深度_UnderTheHood |
| 索引的B+树底层结构是怎样的？ | b+树, 索引结构 | 八股文_Concept |
| 索引及其数据结构，说说最左前缀匹配 | b+树, 索引, 最左前缀匹配, 联合索引 | 原理深度_UnderTheHood |
| 索引设计：如何根据业务场景创建正确且高效的索引？请从数据量庞大对插入/更新性能影响的角度进行分析 | indexing strategy | 原理深度_UnderTheHood |
| 索引实践：在实际业务中你会如何建立索引？有哪些具体的考量因素？ | mysql, 索引 | 工具使用_Tooling |
| 索引下推？ | 索引下推, icp, innodb | 八股文_Concept |
| 索引优化详细讲讲 | 索引优化, explain, 覆盖索引, 最左前缀法则 | 原理深度_UnderTheHood |
| 索引在什么情况下会失效？对索引做计算或使用函数会导致失效，如何理解？能举例说明吗？如果使用 LENGTH 函数构造 SQL，如何导致索引失效？ | 索引失效条件原因, 全表扫描触发, 索引列上运算函数使b+tree失效破坏有序性, length(str)陷阱 | 原理深度_UnderTheHood |
| 谈谈你对 MySQL 性能调优的理解和具体做法。 | mysql | 原理深度_UnderTheHood |
| 网络安全：什么是 SQL 注入？其底层注入漏洞原理是什么？如何通过预编译（PreparedStatement）从根本上防范？ | sql注入, preparedstatement | 八股文_Concept |
| 为啥不用 Hash 索引?Hash 索引查找的时候是不是更快吗? | hash 索引, b+树 | 原理深度_UnderTheHood |
| 为什么 MySQL 表删除了一堆数据,但是文件大小不变? | 数据空洞, 物理删除, 碎片 | 原理深度_UnderTheHood |
| 为什么 MySQL 选择 B+ 树作为索引结构？相较于红黑树或 N 叉平衡树，它在 I/O 层面有哪些核心优势？ | b+树, 磁盘io | 架构设计_Architecture |
| 为什么不用B树？B+树会带来什么可能的隐患？ | b+树, b树, mysql | 原理深度_UnderTheHood |
| 为什么单表达到2000万就有查询性能问题 | mysql, b+树层级, 索引页缓存, 磁盘io, 2000万瓶颈 | 原理深度_UnderTheHood |
| 为什么高并发下数据写入不推荐关系数据库？ | rdbms, nosql, 由于b+树分裂导致的写入性能 | 原理深度_UnderTheHood |
| 为什么加索引可以加快扫描范围？ | 索引, b+树, 磁盘io | 原理深度_UnderTheHood |
| 为什么索引会加快查询 | 索引原理, 磁盘io, b+树 | 原理深度_UnderTheHood |
| 线上 SQL 优化经验：MySQL 索引选择器（Optimizer）的工作机制及如何强制指定索引？ | mysql优化, force index | 原理深度_UnderTheHood |
| 详细解析 MySQL binlog 的工作模式（Statement, Row, Mixed）及其在主从复制中的具体流程？ | binlog mode, replication, relay log | 原理深度_UnderTheHood |
| 详细解析 MySQL binlog 的工作模式（Statement, Row, Mixed）及其在主从复制中的具体流程？ | binlog, mysql replication | 原理深度_UnderTheHood |
| 详细介绍 MySQL 的 ACID 特性、隔离级别、并发问题以及 MVCC 机制 | acid, mvcc | 八股文_Concept |
| 性能优化：在实际使用中，MySQL 的 B+ 树索引有哪些可以优化的点？ | mysql优化 | 原理深度_UnderTheHood |
| 一个表有索引说说它的查询过程？ | 索引查找, 回表 | 原理深度_UnderTheHood |
| 一颗b+树能存储多少数据 | b+树容量, 页大小 | 原理深度_UnderTheHood |
| 以 (a,b,c) 为例,在什么情况下,单查 b 也能命中联合索引? | 联合索引, 最左前缀原则, 索引覆盖 | 原理深度_UnderTheHood |
| 有 abc 复合索引, a=1 and b=1 走不走索引? a=1 and c=1 呢? | 复合索引, 最左匹配原则 | 八股文_Concept |
| 有什么策略能避免幻读？ | mysql, mvcc, 间隙锁 | 原理深度_UnderTheHood |
| 元数据锁及其作用? | mdl | 原理深度_UnderTheHood |
| 在 InnoDB 存储引擎下，一张表在底层存储时涉及哪些文件？ | innodb, ibd, ibdata1 | 原理深度_UnderTheHood |
| 在 MySQL B+ 树索引结构中，如果叶子节点满了会执行什么操作（涉及页分裂）？ | 页分裂, b+树 | 原理深度_UnderTheHood |
| 在哪些场景下 MySQL 索引会失效？请解释最左前缀匹配原则的底层逻辑 | 索引失效, 最左前缀 | 原理深度_UnderTheHood |
| 在设计数据库时，你会考虑哪些核心方面？请重点介绍 B+ 树的数据结构 | b+树, 磁盘io | 原理深度_UnderTheHood |
| 在数据库设计中，你们在 MySQL 中对哪些字段创建了索引？请说明具体的索引优化理由 | 索引优化 | 场景设计_Scenario |
| 在线DDL策略 | mysql, online ddl, pt-osc, gh-ost, 锁表问题 | 原理深度_UnderTheHood |
| 在已有索引的情况下，执行一条 update 语句依然极其缓慢，可能的原因有哪些（长事务、死锁、索引过多、硬件瓶颈等）？ | metadata lock, deadlock, insert/update slowdown | 场景设计_Scenario |
| 账户余额扣减竞态治理：在高并发账户扣减场景中，如何解决“丢失更新”问题？详细对比悲观锁（FOR UPDATE）与乐观锁（Version/CAS）在银行核心系统中的适用性？ | 悲观锁, 乐观锁, 竞态条件 | 原理深度_UnderTheHood |
| 针对长文本（Long Text）字段，应该如何建立索引以优化查询效率？ | 前缀索引, 全文索引 | 原理深度_UnderTheHood |
| 知乎分库分表实践：回答表按 answer_id 分片后，如何设计倒排索引或索引表以支持高效查询某用户的“全部回答”？ | 分库分表, 索引表 | 架构设计_Architecture |
| 执行计划里有哪些字段? 哪些比较重要? | explain, type, rows, extra | 八股文_Concept |
| 主键索引和二级索引的查询过程 | primary index, secondary index, b+ tree seek | 原理深度_UnderTheHood |
| 主键索引如何构建 B+ 树? 为什么 3-4 层可以存千万级数据? | b+ tree structure, fan-out, page size | 原理深度_UnderTheHood |
| 组合索引与单列索引的区别？最左匹配原则的底层逻辑？ | compound index, leftmost matching | 原理深度_UnderTheHood |
| 最左前缀原则知道吗,给你一个索引再给你一个查询条件判断是否能用到索引,查询条件的顺序改变能用到索引吗 | 最左前缀原则, 联合索引 | 原理深度_UnderTheHood |
| B+ 树范围查询的优化策略 (如索引下推) | 索引下推 | 原理深度_UnderTheHood |
| B+ 树数据结构原理 | b+树, mysql索引 | 原理深度_UnderTheHood |
| B+ 树索引结构及相比 B 树的优势？ | b+树, b树 | 原理深度_UnderTheHood |
| B树与B+树结构区别，典型应用（InnoDB索引构建） | b-tree, b+树, innodb, 索引结构 | 原理深度_UnderTheHood |
| Explain的type字段中，什么样的需要优化 | explain, type字段 | 原理深度_UnderTheHood |
| InnoDB 并发可见性分析：详述 MVCC（多版本并发控制）如何结合间隙锁（Gap Lock）解决可重复读级别下的“幻读”问题？ | mvcc, gap lock | 原理深度_UnderTheHood |
| InnoDB 存储引擎在 REPEATABLE READ (RR) 级别下是如何在最大程度上避免幻读的？ | mvcc, next-key lock, 间隙锁 | 原理深度_UnderTheHood |
| InnoDB 底层数据结构（B+ 树）？ | b+树, innodb | 八股文_Concept |
| InnoDB 为啥索引的数据结果要用 B+树? | b+树, innodb, 索引原理 | 原理深度_UnderTheHood |
| InnoDB RR 级别下幻读被完全避免了吗？在什么情况下仍可能出现幻读？为何还需要 SERIALIZABLE 级别？ | 幻读, 当前读, 快照读 | 原理深度_UnderTheHood |
| InnoDB索引的底层数据结构? | b+树, innodb | 原理深度_UnderTheHood |
| MVCC 过是怎么实现的? | mvcc | 原理深度_UnderTheHood |
| MVCC 机制深度：详细描述 MVCC 的内部实现细节（ReadView, 版本链）及其解决的并发问题？ | mvcc, readview, undo log | 原理深度_UnderTheHood |
| MVCC 机制深度应用：MVCC 如何在“不可重复读”与“读取已提交”隔离级别中发挥不同作用？ | readview, snapshot | 原理深度_UnderTheHood |
| MVCC 机制深度应用：MVCC 如何在“不可重复读”与“读取已提交”隔离级别中发挥不同作用？ | mvcc, readview | 原理深度_UnderTheHood |
| MVCC 实现机制 | mvcc, readview, undo log | 原理深度_UnderTheHood |
| MVCC的流程 | mvcc, readview, undo log, 版本链, 可见性判断 | 原理深度_UnderTheHood |
| MVCC机制可能产生什么问题（如旧版本堆积）？如何解决？ | mvcc, purge thread | 原理深度_UnderTheHood |
| MVCC原理？ | mvcc, readview, undo log, 版本链 | 原理深度_UnderTheHood |
| MyISAM 索引与 InnoDB 索引的区别？ | 聚簇索引, 非聚簇索引 | 原理深度_UnderTheHood |
| MySQL 并发控制：幻读（Phantom Read）的底层解决机制（Next-Key Locks）及 MVCC 在其中扮演的角色？ | phantom read, next-key lock, mvcc | 原理深度_UnderTheHood |
| MySQL 并发控制：详细描述范围查询（Range Query）在不同隔离级别下对联合索引产生的间隙锁（Gap Lock）范围？ | gap lock, composite index, rr isolation | 原理深度_UnderTheHood |
| MySQL 常用优化策略及索引失效的深度分析？ | mysql优化, 索引失效 | 原理深度_UnderTheHood |
| MySQL 存储：通过三层 B+ 树的索引结构，如何估算其能承载的记录总数（基于 Page Size 16KB 与指针大小计算）？ | mysql, b+树, page | 原理深度_UnderTheHood |
| MySQL 存储：为什么 InnoDB 的主键索引能显著加速随机查询？B+ 树平衡过程对页分裂（Page Split）的影响？ | innodb, clustered index, b+树, page split | 原理深度_UnderTheHood |
| MySQL 存储：INT 与 DATETIME/TIMESTAMP 等基础数据类型在磁盘上的底层存储字节数及编码方式？ | mysql, 数据类型, 存储 | 八股文_Concept |
| MySQL 存储极限：一张表最多存储多少行数据（计算器推导逻辑）？ | b+ tree capacity, page size | 原理深度_UnderTheHood |
| MySQL 存储引擎 MyISAM 与 InnoDB 的区别？ | myisam, innodb, 事务 | 分析题_Analysis |
| MySQL 大表 DDL 治理：在千万级回答表上新增字段或索引，如何利用 ghost 等工具避免长时间锁表并降低主从延迟？ | ddl, gh-ost | 方案设计_Scenario |
| MySQL 的 B+ 树索引原理？ | b+树 | 原理深度_UnderTheHood |
| MySQL 的底层实现原理? 为什么用 B+ 树? | b+树, innodb | 原理深度_UnderTheHood |
| MySQL 的底层数据结构是什么？与早期版本或其他数据库相比，这种结构（如 B+ 树）有哪些核心优势？ | b+树 | 原理深度_UnderTheHood |
| MySQL 的索引是什么结构，有什么特点？ | b+树, 聚簇索引, 非聚簇索引 | 原理深度_UnderTheHood |
| MySQL 的索引是怎么实现的？ | mysql, 索引, b+树 | 原理深度_UnderTheHood |
| MySQL 的锁机制：在什么特定场景下会触发表级锁（Table Lock）？ | table lock | 八股文_Concept |
| MySQL 底层为什么要采用 B+ 树作为索引结构？ | b+树 | 原理深度_UnderTheHood |
| MySQL 高可用架构方案：设计一套包含“读写分离、半同步复制、自动故障转移（MHA/Orchestrator）”的数据库方案？ | 高可用, 读写分离 | 架构设计_Architecture |
| MySQL 隔离级别：RR 如何解决幻读？ | rr, 间隙锁, next-key lock | 八股文_Concept |
| MySQL 回表性能：什么是回表（Look-up）？在复杂查询中，如何通过联合索引与覆盖索引（Covering Index）规避此开销？ | look-up, covering index | 原理深度_UnderTheHood |
| MySQL 机制：MVCC 的工作原理、隔离级别定义及具体示例（如 RR 与 RC 的差异）？ | mvcc, readview | 原理深度_UnderTheHood |
| MySQL 架构：详细描述 MySQL 主从复制的三个核心线程（IO Thread, SQL Thread）及其实现异步复制与增强半同步复制的区别？ | mysql主从复制, 异步复制, 半同步复制 | 原理深度_UnderTheHood |
| MySQL 间隙锁定义及应用场景 | gap lock, phantom read, rr isolation | 八股文_Concept |
| MySQL 健壮性：ACID 原子性是如何通过 Undo Log 保证的？如果在 Insert 执行中宕机，MySQL 复载（Recovery）时的逻辑推导过程？ | undo log, acid, recovery | 原理深度_UnderTheHood |
| MySQL 聚簇索引（Clustered Index）与非聚簇索引（Secondary Index）的底层存储差异及回表开销优化？ | mysql, 聚簇索引, 非聚簇索引 | 原理深度_UnderTheHood |
| MySQL 慢 SQL 调优的步骤有哪些（Explain 计划分析、索引优化、全表扫描规避、分页优化等）？ | explain plan, sql optimization | 场景设计_Scenario |
| MySQL 慢查询原因及定位处理 | slow query log, explain, profiler | 场景设计_Scenario |
| MySQL 日志：MySQL 共有哪几种类型的日志（binlog, redolog, undolog）？它们分别负责什么？binlog 的主要格式（Row, Statement, Mixed）是怎样的？ | binlog, redo log, undo log | 原理深度_UnderTheHood |
| MySQL 日志系统：binlog, redolog, undolog 的区别与作用？ | binlog, redo log, undo log | 八股文_Concept |
| MySQL 日志系统：Redo Log 与 Undo Log 的底层实现原理及其在持久化与原子性中的作用？ | redo log, undo log, wal | 原理深度_UnderTheHood |
| MySQL 如何避免重复插入数据? | insert ignore, replace into, on duplicate key update | 场景设计_Scenario |
| MySQL 如何解决并发问题? 各种锁的作用? | row lock, gap lock, next-key lock | 原理深度_UnderTheHood |
| MySQL 深度分页问题及解决方案（limit 优化）？ | limit optimization, deferred join | 场景设计_Scenario |
| MySQL 事务：详细解析二阶段提交（2PC）在 InnoDB 存储引擎与 Binlog 之间保证数据最终一致性的工作流？ | 2pc, innodb, binlog, 数据一致性 | 原理深度_UnderTheHood |
| MySQL 事务：在可重复读（RR）隔离级别下，如何利用 Next-Key Lock（Gap Lock + Record Lock）解决幻读问题？ | mysql, next-key lock, 幻读 | 原理深度_UnderTheHood |
| MySQL 事务：在可重复读（RR）级别下，MySQL 是通过什么机制实现隔离的？MVCC 中的多版本数据是如何产生的？ | rr isolation, mvcc | 原理深度_UnderTheHood |
| MySQL 事务：InnoDB 存储引擎是如何实现事务（ACID 特性）的？ | innodb, redo log, undo log | 原理深度_UnderTheHood |
| MySQL 事务的隔离级别及解决的问题 | mysql, 事务隔离级别, 脏读, 不可重复读, 幻读, mvcc | 八股文_Concept |
| MySQL 事务隔离：详细描述 MVCC 的底层实现原理（ReadView, Undo Log 指针等）？ | mvcc, readview, undo log | 原理深度_UnderTheHood |
| MySQL 事务隔离级别及 MVCC + undo log 实现读已提交和可重复读的具体机制？ | mvcc, undo log, rr/rc isolation | 原理深度_UnderTheHood |
| MySQL 事务隔离级别及如何解决幻读问题？ | mysql 事务隔离级别, 幻读 | 原理深度_UnderTheHood |
| MySQL 事务日志：Binlog 的三种格式（Statement, Row, Mixed）及其在主从同步可靠性上的优缺点对比？ | binlog, replication | 原理深度_UnderTheHood |
| MySQL 事务一致性：详细辨析 Redo Log（重做日志）与 Binlog（归档日志）在写入时机、存储格式及奔溃恢复中的区别？ | redo log, binlog, crash recovery | 原理深度_UnderTheHood |
| MySQL 是否具备保存非结构化数据的能力？如果是，该如何实现？ | json, mysql | 原理深度_UnderTheHood |
| MySQL 数据库中是否涉及存储过程（Stored Procedure）的使用？在现代架构中其优劣势分析？ | 存储过程 | 架构设计_Architecture |
| MySQL 索引 B+ 树原理？为什么比 B 树、Hash 索引更高效？ | mysql 索引, b+树 | 原理深度_UnderTheHood |
| MySQL 索引：强制使用索引（FORCE INDEX）的语法场景及优化器选择不走索引的常见原因（如过滤性差、回表开销大）？ | force index, mysql优化器, 回表 | 原理深度_UnderTheHood |
| MySQL 索引：请详细解释 MySQL 索引的原理，并对比不同存储引擎或不同数据库（如 MongoDB）在索引实现上的差异 | b+树, wiredtiger | 原理深度_UnderTheHood |
| MySQL 索引：什么是“回表”查询？如何通过联合索引（索引覆盖）避免回表以提升查询效率？ | mysql索引, 回表, 覆盖索引 | 八股文_Concept |
| MySQL 索引：详细解释“索引下推”（Index Condition Pushdown, ICP）的工作原理？在联合索引 (A, B, C) 场景下，查询条件 (A, C) 如何利用索引？ | icp, composite index | 原理深度_UnderTheHood |
| MySQL 索引：针对 TEXT/LONGTEXT 等大文本字段，常见的索引策略（前缀索引、全文本索引、外部 ES 同步）及其优缺点对比？ | mysql索引, 前缀索引, 全文搜索 | 八股文_Concept |
| MySQL 索引：MySQL 聚簇索引的底层数据结构是什么？为什么选择 B+ 树而非其他数据结构（如红黑树、B 树、哈希表）？请进行对比分析。 | b+树 | 原理深度_UnderTheHood |
| MySQL 索引：MySQL 中索引的存储形式是什么？结合 B+ 树结构，详细分析为什么联合索引必须遵循最左前缀匹配原则。 | b+树, 联合索引 | 原理深度_UnderTheHood |
| MySQL 索引的底层数据结构是什么？为什么选择 B+ 树而非 B 树？ | b+树 | 原理深度_UnderTheHood |
| MySQL 索引底层实现原理：为什么 B+ 树在大规模 IO 场景下优于 B 树或红黑树？ | b+树, disk io, clustered index | 原理深度_UnderTheHood |
| MySQL 索引底层实现原理：为什么 B+ 树在大规模 IO 场景下优于 B 树或红黑树？ | b+树, index density | 原理深度_UnderTheHood |
| MySQL 索引覆盖优化：如何针对“SELECT * FROM answers WHERE user_id=? AND create_time>? ORDER BY vote_count DESC”设计最优索引？ | 复合索引, 索引优化 | 原理深度_UnderTheHood |
| MySQL 索引进阶：为何联合索引遵循最左匹配原则（Leftmost Prefix Rule）？索引下推（ICP）如何在 Server 层级提升查询效率？ | leftmost prefix, icp | 八股文_Concept |
| MySQL 索引类型及其底层 B+ 树原理？ | mysql 索引, b+树 | 原理深度_UnderTheHood |
| MySQL 索引深度：索引类型（主键、唯一、普通）、无主键表是否仍有主键索引、B+ 树与 B 树的区别？ | b+树, 聚集索引 | 原理深度_UnderTheHood |
| MySQL 索引失效深度剖析：针对复杂 WHERE 条件与 ORDER BY 组合的慢查询，如何精准优化复合索引？ | 复合索引, 慢查询优化 | 原理深度_UnderTheHood |
| MySQL 索引为什么不用红黑树或 AVL 树，而选择 B+ 树？ | b+树, 红黑树, 磁盘io | 原理深度_UnderTheHood |
| MySQL 索引下推（Index Condition Pushdown）：在什么场景下会生效？如何减少回表次数？ | icp, index optimization | 原理深度_UnderTheHood |
| MySQL 索引优化：详细描述回表（Look-up）操作及其对查询性能的影响？如何通过覆盖索引优化？ | mysql, look-up, covering index | 原理深度_UnderTheHood |
| MySQL 索引优化场景：什么是 Filesort？如何避免？ | filesort, using index, mysql优化 | 原理深度_UnderTheHood |
| MySQL 锁：间隙锁（Gap Lock）的触发场景及其在防止幻读中的具体工作机理？ | gap lock, 幻读, mysql锁 | 原理深度_UnderTheHood |
| MySQL 锁机制：请描述 InnoDB 行锁（Record Lock）、间隙锁（Gap Lock）与临键锁（Next-key Lock）的应用场景及死锁回避策略？ | next-key lock, deadlock avoidance | 原理深度_UnderTheHood |
| MySQL 锁机制：详细辨析行级锁（Row Lock）与表级锁（Table Lock）的区别及其对并发性能的影响？ | mysql lock, row lock, table lock | 原理深度_UnderTheHood |
| MySQL 锁升级：当 Update 语句的 Where 条件字段未加索引时，InnoDB 引擎会采取何种级别的锁定？如何通过优化避免全表锁？ | lock escalation, full table lock | 场景设计_Scenario |
| MySQL 为什么不使用红黑树而是 B+tree? | b+树, 红黑树, 磁盘io | 原理深度_UnderTheHood |
| Mysql 为什么一定要有一个主键？ | 聚簇索引, innodb存储引擎 | 原理深度_UnderTheHood |
| Mysql 为什么用 B+ 树，B+ 树和 B 树，红黑树等有什么区别 | b+树, b树, 红黑树, 磁盘io, 范围查询 | 原理深度_UnderTheHood |
| MySQL 现场手撕练习题（具体题目未列出）？ | sql | 算法手撕_Coding |
| MySQL 性能：Explain 执行计划中各个关键字段（type, key, Extra）的含义？如何通过 Extra 字段判断是否使用了索引过滤？ | explain, sql optimization | 八股文_Concept |
| MySQL 优化：请尽可能详细地说明 SQL 优化的常见方式（包括执行计划分析、索引覆盖、关联查询优化、大表深度分页优化等） | explain plan, covering index, deferred join | 场景设计_Scenario |
| MySQL 语句的执行过程是怎样的？ | 执行引擎, 分析器, 优化器 | 原理深度_UnderTheHood |
| MySQL 原理：详细描述 MySQL 执行一条 UPDATE 语句的完整全流程。 | mysql, update日志 | 原理深度_UnderTheHood |
| MySQL 运维：Binlog 存储的具体二进制内容及其在主从同步中的异步/半同步复制原理？ | binlog, replication, async/semi-sync | 原理深度_UnderTheHood |
| MySQL 中聚簇索引与非聚簇索引的区别是什么？B+ 树相比其他结构（如 Hash, 二叉树）的优势体现在哪里？ | b+树, 聚集索引 | 原理深度_UnderTheHood |
| MySQL 中遇到慢查询如何查看执行计划? | explain, 慢查询 | 原理深度_UnderTheHood |
| MySQL 主键索引和普通索引的区别是什么? 谁的性能更好一些? | 主键索引, 普通索引, 聚簇索引 | 原理深度_UnderTheHood |
| MySQL 最左前缀匹配：给定索引 (a, b, c)，查询条件为 a=1 and b>1 and c=1，这会走索引吗？为什么 c=1 部分可能不走索引？ | 最左前缀, 范围查询, 索引失效 | 原理深度_UnderTheHood |
| MySQL JOIN 查询中，条件写在 ON 后面和 WHERE 后面的区别？ | join, on, where | 八股文_Concept |
| MySQL MVCC 的底层原理 | mvcc | 原理深度_UnderTheHood |
| MySQL MVCC 机制：ReadView、undo log 在实现事务隔离中的作用？ | mvcc, undo log, readview | 原理深度_UnderTheHood |
| MySQL MVCC（多版本并发控制）实现原理（ReadView、Undo Log、隐藏列的协作） | mysql, mvcc, readview, undo log | 原理深度_UnderTheHood |
| MySQL：创建联合索引时为什么要将高频字段放在最前面？ | compound index | 原理深度_UnderTheHood |
| MySQL：哈希索引与B+树索引的对比分析及适用场景 | hash index, b+树 | 原理深度_UnderTheHood |
| MySQL：回表、索引覆盖、索引下推的概念与原理 | index lookups, covering index, icp | 原理深度_UnderTheHood |
| MySQL：Char 与 Varchar 的底层存储架构区别及对 I/O 的影响 | varchar, char | 原理深度_UnderTheHood |
| MySQL的索引结构是什么？为什么使用 B+树？ | mysql, 索引, b+树 | 原理深度_UnderTheHood |
| MySQL的索引数据结构是什么，主键索引和非主键索引在数据结构上有什么区别 | b+树, 聚簇索引, 二级索引 | 原理深度_UnderTheHood |
| MySQL的执行过程？ | 执行计划, 解析器, 优化器, 执行器 | 原理深度_UnderTheHood |
| mysql的acid特性是怎么实现的 | mysql, acid, redo log, undo log, mvcc, 锁 | 原理深度_UnderTheHood |
| mysql的B+树数据结构 | b+树, mysql, innodb, 索引 | 原理深度_UnderTheHood |
| MySQL的redo log和binlog有什么区别？ | mysql, redo log, binlog | 原理深度_UnderTheHood |
| MySQL调优你是怎么做的？ | mysql, 性能调优 | 原理深度_UnderTheHood |
| MySQL调优你是怎么做的？ | mysql | 原理深度_UnderTheHood |
| MySQL日志：redo log、undo log、binlog，写入顺序？ | redo log, undo log, binlog, 两阶段提交 | 原理深度_UnderTheHood |
| MySQL日志的存储位置在哪？是物理的还是逻辑的？ | mysql | 原理深度_UnderTheHood |
| MySQL如何实现事务的? 主要 undolog 日志是怎么工作的? | undo log, 原子性, 回滚 | 原理深度_UnderTheHood |
| MySQL索引：联合索引失效场景分析：where a=** order by b 等复合条件下的索引命中逻辑 | compound index, index invalidation | 原理深度_UnderTheHood |
| MySQL索引底层B+树的数据结构特征及其节点查找过程 | mysql, b+树, 索引 | 原理深度_UnderTheHood |
| MySQL索引原理？以及为什么要用B+树？用其他的可以吗？ | b+树, 索引 | 原理深度_UnderTheHood |
| mysql行锁（说知道记录锁，临键锁，间隙锁，具体怎么用忘记了） | 行锁, 间隙锁, 记录锁 | 原理深度_UnderTheHood |
| MySQL优化：如何在数据库中存储IP地址？(INT型替代字符串) | ip storage | 原理深度_UnderTheHood |
| mysql怎么实现事务 | mysql, innodb, 事务, undo log, redo log, mvcc | 原理深度_UnderTheHood |
| MySQL中，ID一定要自增吗？能不能不自增？如果不自增会产生什么问题？为什么建议自增？ | mysql, 索引 | 原理深度_UnderTheHood |
| ORM 映射：MyBatis 中 '#' 与 '$' 的底层差异及其在防范 SQL 注入上的作用机理？数据库记录到 Java 对象的映射背后是如何实现的？ | mybatis, sql injection, preparedstatement | 八股文_Concept |
| redo log 的作用，buffer pool 的原理，redo log 刷盘的时机的，redo log 满了怎么处理，为什么用 redo log 而不是 bin log 恢复数据 | redo log, buffer pool, 刷盘机制, wal, crash-safe, checkpoint | 原理深度_UnderTheHood |
| RTree 索引是怎么构建的？ | rtree, 空间索引 | 原理深度_UnderTheHood |
| SELECT x, y FOR UPDATE 的作用是什么？加的是什么锁？会变成表锁吗？ | mysql, 锁 | 原理深度_UnderTheHood |
| SQL 调优：Explain 命令中的 key、rows、extra 字段含义？索引优化器成本分析原理？ | explain, mysql优化器 | 原理深度_UnderTheHood |
| SQL 分析：执行 `WHERE id > 10` 时会加锁吗？加什么锁？是否会锁定 `id > 20` 的记录？ | 范围查询, next-key lock | 原理深度_UnderTheHood |
| SQL 分析：执行 `WHERE name > 'test1'` 会加锁吗？加锁的粒度和逻辑是怎样的？ | 非唯一索引锁 | 原理深度_UnderTheHood |
| SQL 考题：三表关联查询及子查询的应用实现？ | sql查询, 子查询 | 算法手撕_Coding |
| SQL 实战：编写两个场景化的 SQL 查询语句。 | sql | 手撕代码_Coding |
| SQL 实战：编写两个场景化的 SQL 查询语句。 | sql select, scenario sql | 手撕代码_Coding |
| SQL 索引优化：对于 select * from t where a = 100 and b > 100 and b <= 1000 and c = 10，请设计对应的联合索引并解释原因？ | composite index, range query optimization | 场景设计_Scenario |
| SQL：给定 table1，要求：当字段 a 在所有元组中都等于 '1' 时，返回字段 b='2' 的前 2 条数据，按字段 c 排序。请编写对应的 SQL 语句。 | - | 算法手撕_Coding |
| SQL：如何找到表中重复次数最多的 name 及其重复的个数？ | sql, group by, hadving | 原理深度_UnderTheHood |
| SQL：有一个收入记录表 `income_records` (user_id, income, month)，请编写 SQL 计算每个用户每个月的收入总额，并筛选出单月收入总额大于 1000 的记录（要求包含 user_id 和 month）。 | - | 算法手撕_Coding |
| text和varchar底层存储区别 | text, varchar | 原理深度_UnderTheHood |

## L3_Diagnostic (62 道题目)

| 题目 | 相关技术点 (Entities) | 题型 (Type) |
|---|---|---|
| 并发安全：什么是“死锁（Deadlock）”？请列举一个数据库（MySQL）中由于索引加锁顺序不一致导致死锁的真实业务场景 | deadlock, lock graph, index lock contention | 场景设计_Scenario |
| 场景：给定一个sql语句，询问加了什么锁？ | mysql锁, 事务隔离级别 | 场景设计_Scenario |
| 场景估算：使用索引键进行单条SQL查询时，底层磁盘I/O的次数是如何确定的？ | mysql, 索引, 磁盘io, b+树 | 原理深度_UnderTheHood |
| 场景设计：在主从架构下，如果主从同步延迟较高，导致用户刚创建的数据无法立即在列表页查出，应如何优化用户体验？ | 主从延迟, 强一致性查询 | 场景设计_Scenario |
| 场景题：假设数据库中有海量并发任务需要频繁修改用户余额。为了保证并发安全且不因加锁导致严重的性能瓶颈，你有哪些优化方案？ | 分库分表, 热点数据打散, 缓冲池 | 场景设计_Scenario |
| 出现错误 Duplicate entry '...' for key 'base_data.PRIMARY' 是什么原因？ | duplicate entry, 主键冲突, 唯一性约束 | 底层机制_LowLevel |
| 存储优化：针对海量数据的 SQL 慢查询，请从索引覆盖、子查询优化及执行计划分析给出系统性调优方案？ | sql optimization, explain plan | 场景设计_Scenario |
| 高并发优化：当 MySQL 查询压力过大时，除了分库分表外，还有哪些行之有效的手段？ | read-write splitting, connection pool | 场景设计_Scenario |
| 给你几个字段让你设计其属性类型,大小,后分析哪些字段适合建立索引,哪些不适合建立索引,索引的选择性是什么意思 | 索引, 索引选择性, 字段类型 | 场景设计_Scenario |
| 技术挑战：假设强制要求利用 SQL 实现字典树（Trie Tree）逻辑，你会如何进行 Schema 设计与查询？ | trie树, sql建模 | 系统设计_Architecture |
| 慢 SQL 排查：请描述你定位、排查并优化一条慢 SQL 的完整工作流 | explain, slow query log | 场景设计_Scenario |
| 你遇到过哪些导致 MySQL 索引失效的场景？ | 索引失效 | 原理深度_UnderTheHood |
| 你在日常工作中对 SQL 进行了什么优化? | sql优化, 索引优化, 覆盖索引, 深度分页 | 项目深挖_Project |
| 请描述慢 SQL 的排查流程 | 慢查询, explain | 场景设计_Scenario |
| 请描述慢查询的优化流程及常用手段 | explain, 慢查询 | 场景设计_Scenario |
| 如果索引优化后查询依然缓慢，你会采取哪些进一步措施（如分库分表、硬件扩容等）？ | 分库分表 | 场景设计_Scenario |
| 如何查看索引是否高效利用？ | explain, 索引, type, key_len | 场景设计_Scenario |
| 如何优化SQL？ | sql优化, explain, 索引, 慢查询 | 场景设计_Scenario |
| 使用乐观锁解决超卖问题及高并发优化？ | 乐观锁, sharding | 场景设计_Scenario |
| 事务深度：隔离级别详解、RR 模式下的幻读/侧写问题及 Spring 事务失效场景分析？ | 隔离级别, 事务失效 | 原理深度_UnderTheHood |
| 数据库：如何利用 EXPLAIN 语句来分析 and 优化慢 SQL 查询？ | explain, 慢查询 | 场景设计_Scenario |
| 数据库：索引碎片化的成因及优化手段 (OPTIMIZE TABLE 或重建索引机制) | index fragmentation, optimize table | 原理深度_UnderTheHood |
| 数据库：在处理千万级以上的 SaaS 业务数据时，你会采取哪些 MySQL 优化手段（如分库分表、索引下推优化、大分页查询优化）？ | 分库分表 | 原理深度_UnderTheHood |
| 数据库：在秒杀过程中，MySQL 的哪部分数据需要修改？如何处理库存扣减的高并发写压力？ | 库存扣减, 行锁, redis预减库存 | 场景设计_Scenario |
| 数据库：在设计电商系统的商品表时，为“库存”字段增加索引是否合理？请分析索引带来的查询优势与更新压力平衡。 | 索引, b+树 | 场景设计_Scenario |
| 数据库：在什么情况下应该建立索引？如何评价一个索引设计的好坏？ | 索引设计, 区分度 | 场景设计_Scenario |
| 数据库：针对“深度分页”查询，有哪些常用的 SQL 优化策略？ | 深度分页, 子查询优化 | 场景设计_Scenario |
| 数据库：MySQL 的索引决策是在哪一步完成的？如果执行计划选择了错误的索引，你有哪些排查和调优手段（如 force index, analyze table）？ | 执行计划, force index | 经验思考_Reflection |
| 数据库并发：在高并发下单场景下，如何根据业务需求选择合适的 MySQL 锁策略？ | 并发控制 | 场景设计_Scenario |
| 数据库调优：分享一次你在线上真实处理慢查询（Slow Query）的经历？涉及哪些索引覆盖与 SQL 重写技巧？ | 慢查询, index coverage | 原理深度_UnderTheHood |
| 数据库集群：如何排查并解决 MySQL 主从同步延迟问题？ | master-slave delay, binlog | 场景设计_Scenario |
| 数据库死锁分析：针对 Gap Lock 导致的并发更新死锁，如何进行压力测试复现并设计规避策略？ | 死锁, gap lock | 原理深度_UnderTheHood |
| 数据库优化：针对字段众多且拥有百万/千万级数据的单表，在执行深度分页（Deep Paging）查询时，有哪些具体的 SQL 优化方案（如子查询优化、延迟关联、覆盖索引）？ | deep paging, deferred join, covering index | 场景设计_Scenario |
| 数据库诊断：当查询性能不佳时，你会使用哪些索引失效分析工具（如 EXPLAIN）？执行计划中的 `type` 和 `extra` 字段分别代表什么含义？ | explain plan analysis, index invalidation, sql optimization statistics | 场景设计_Scenario |
| 算法：三个sql | sql查询 | 算法手撕_Coding |
| 写密集型数据库的索引优化与锁冲突规避 | 写密集, 锁冲突 | 场景设计_Scenario |
| 在实现新功能时，你是如何设计数据模型和表结构的？请介绍核心设计思路 | 表结构设计 | 场景设计_Scenario |
| 在主从同步过程中，如果从库在重做（Relay Log）时失败了，该如何解决？ | 主从不同步, relay log修复 | 场景设计_Scenario |
| MySQL 查询优化：在大表（数亿级）场景下，如何优化分页查询（Deep Paging）以避免全表扫描（利用子查询/ID 偏移）？ | mysql, deep paging, 分页查询 | 原理深度_UnderTheHood |
| MySQL 处理每秒 10 万级订单写入的优化方案？ | 批量写入, 分库分表 | 场景设计_Scenario |
| MySQL 调优策略、慢查询日志定位及 EXPLAIN 结果分析？ | mysql调优, explain | 原理深度_UnderTheHood |
| MySQL 健壮性：ACID 原子性是如何通过 Undo Log 保证的？如果在 Insert 执行中宕机，MySQL 复载（Recovery）时的逻辑推导过程？ | mysql, acid, undo log, 崩溃恢复 | 原理深度_UnderTheHood |
| MySQL 慢查询排查流程：慢查询日志 → explain 执行计划分析（type/key/extra）？ | 慢查询, explain | 原理深度_UnderTheHood |
| MySQL 慢查询优化：Explain 执行计划关注点及索引调优策略？ | mysql 慢查询, explain | 原理深度_UnderTheHood |
| MySQL 如何恢复到误删除前的状态? | binlog, 数据恢复 | 场景设计_Scenario |
| MySQL 死锁实战：京东库存服务出现 “间隙锁+插入意向锁” 死锁，如何复现和解决？ | mysql锁, 间隙锁, 插入意向锁 | 原理深度_UnderTheHood |
| MySQL 索引实战：针对具体业务表及查询语句，如何设计最优索引？辨析不同索引方案的优劣及索引失效（Index Skip Scan）场景？ | mysql index, index skip scan | 场景设计_Scenario |
| MySQL 异常分析：为什么数据库的自增 ID 会出现不连续的跳过现象？请列举至少两个场景（如唯一索引冲突、事务回滚）？ | auto-increment id, rollback, locking | 原理深度_UnderTheHood |
| MySQL 优化：B+ 树相比于 B 树在磁盘存储上的核心优势是什么？针对千万级数据的“慢 SQL”及“深度分页（Deep Paging）”问题，你有对应的优化思路吗？ | b+树, 慢查询, deep paging | 场景设计_Scenario |
| MySQL 主从：详细解析主从延迟（Replication Lag）产生的原因及业务测兜底方案（如强制路由主库、Binlog 并行回放）？ | mysql主从, 主从延迟, binlog | 原理深度_UnderTheHood |
| MySQL 主从延迟导致重复派单如何解决？ | 主从延迟, 幂等 | 场景设计_Scenario |
| MySQL 自增 ID 在高并发或分布式场景下可能存在哪些问题？如何解决？ | 自增id, 雪花算法, uuid | 场景设计_Scenario |
| MySQL的索引失效？ | 索引失效, 最左前缀, 函数 | 场景设计_Scenario |
| MySQL死锁分析：线上出现INSERT ON DUPLICATE KEY UPDATE导致的死锁，如何复现和规避？ | mysql死锁, insert on duplicate key update | 原理深度_UnderTheHood |
| SQL 实战：针对复杂业务逻辑 design 并讨论最优索引方案。 | sql index design | 场景设计_Scenario |
| SQL 性能抉择：join 操作一定会导致性能问题吗？如何根据表数据量与索引状态决定连接策略？ | sql join, index | 场景设计_Scenario |
| SQL 优化：给定 SQL select * from table where a > ? and b = ? or c = ? order by d desc limit 10，请分析该语句的执行效率并提出优化建议。 | sql优化, explain, 复合索引 | 场景设计_Scenario |
| SQL 优化：针对一个包含百万级数据量的表，如何解决“深度分页”查询带来的性能问题？ | 深度分页, 延迟关联 | 场景设计_Scenario |
| SQL 优化案例：SELECT * FROM orders WHERE status=1 AND create_time>? 执行慢，如何优化？ | 索引优化, 复合索引 | 场景设计_Scenario |
| SQL 遇到慢查询你会怎么去定位和优化？ | 慢查询, explain | 原理深度_UnderTheHood |
| SQL优化实战：SELECT * FROM orders WHERE user_id=? AND status IN(1,2,3) ORDER BY create_time DESC如何建索引？ | 索引优化, 复合索引 | 场景设计_Scenario |
| TCP 是如何通过序列号、确认应答等机制保证可靠传输的？ | 索引失效, explain | 场景设计_Scenario |

