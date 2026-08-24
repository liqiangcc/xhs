<!-- xhs-answer: {"schema_version":"answer.v1","canonical_id":"cq_mysql_index_types_8ee09a1a","version":1,"status":"draft","updated_at":"2026-08-17","answer_type":"concept","quality_tier":"candidate"} -->
# MySQL 常见索引类型及作用

## 核心结论

MySQL 8.4 里的“索引类型”不要混成单一维度。DDL 定义层可以看到 `PRIMARY KEY`、`UNIQUE`、普通 `INDEX/KEY`、`FULLTEXT`、`SPATIAL`，并允许一个索引包含多个 key part；`KEY` 是 `INDEX` 的同义写法，语法还提供 `USING {BTREE|HASH}`，实际支持范围要看存储引擎。优化层面，索引条目帮助 MySQL 定位满足条件的行，但额外索引会占空间，并增加 INSERT、UPDATE、DELETE 的维护成本。对 InnoDB，还要单独理解“聚簇索引与二级索引”：聚簇索引保存行数据，通常采用主键；二级索引记录包含主键列，用它回到聚簇索引定位行。

## 1 分钟版

- DDL 分类：`PRIMARY KEY`、`UNIQUE`、普通 `INDEX/KEY`、`FULLTEXT`、`SPATIAL` 都是 MySQL 8.4 `CREATE TABLE` 可声明的索引/键定义；`KEY` 与 `INDEX` 同义。
- 列组合：一个索引定义可以有一个或多个 key part，所以“单列/多列”是另一维度，不应和 PRIMARY/UNIQUE 等混为一种分类。
- 访问方法：DDL 语法提供 `USING BTREE|HASH`，但能否使用以及如何实现由具体存储引擎决定，不能把 HASH 当成 InnoDB 普通索引的通用结论。
- 成本：官方优化文档明确，索引可帮助定位满足 `WHERE` 条件的行；无用索引浪费空间，每个索引还增加写操作维护成本。
- InnoDB 结构：聚簇索引保存行数据；通常主键就是聚簇索引。二级索引记录带着主键列，因此主键越长，所有二级索引的空间代价也越大。

## 3 分钟版

第一步先拆分类维度。MySQL 8.4 `CREATE TABLE` 的索引定义包括 `PRIMARY KEY`、`UNIQUE [INDEX|KEY]`、普通 `INDEX|KEY`、`FULLTEXT`、`SPATIAL`；其中 `KEY` 是 `INDEX` 的同义词。同一个索引定义还可以列出多个 key part，因此“单列还是多列”描述的是 key part 数量，不是新的约束类别。至于 `FULLTEXT`、`SPATIAL` 的具体查询能力、数据类型与限制，本文当前证据只确认它们是独立 DDL 索引定义，不再外推其用途细节。

第二步再看访问方法。MySQL 8.4 DDL 语法列出 `USING {BTREE|HASH}`，但这只是语法层事实；官方文档同时要求结合存储引擎理解索引实现。因此不能从这段语法直接推导“所有表都能自由选择 HASH”，也不能把某个引擎的内部组织当成 MySQL 全局定义。

第三步看为什么建索引。MySQL 8.4 优化文档说明，索引条目帮助快速定位满足 `WHERE` 条件的行；同一份文档也明确指出，不需要的索引会浪费空间，而且每个索引都会增加 INSERT、UPDATE、DELETE 的维护成本。所以索引不是“越多越好”，而是读路径收益与空间/写维护成本的权衡。本答案不在没有具体 SQL 证据时给出固定的复合索引列顺序规则。

第四步单独说明 InnoDB。官方 InnoDB index-types 文档把 clustered index 和 secondary index 区分开：聚簇索引保存行数据，通常选择主键；如果没有合适主键，InnoDB 还有自己的回退规则。二级索引记录包含二级索引列以及主键列，查找完整行时可借主键定位聚簇索引中的记录。官方文档还明确指出，主键过长会增加二级索引占用空间。因此“PRIMARY KEY”和“clustered index”在典型 InnoDB 表中高度相关，但前者首先是表级键定义，后者是 InnoDB 的存储组织概念，回答时要注明引擎边界。

## 关键细节

- `INDEX` 与 `KEY` 在 MySQL 8.4 DDL 中同义；不要把它们说成两种物理结构。
- `PRIMARY KEY`、`UNIQUE`、普通索引、`FULLTEXT`、`SPATIAL` 属于 DDL 定义层；BTREE/HASH 属于访问方法语法；clustered/secondary 属于 InnoDB 组织层，三组概念不能混为一张平级清单。
- 多列索引只是一个索引含多个 key part；在没有具体 SQL、数据分布和更细的一手规则时，不应凭经验宣称固定列顺序一定最优。
- 当前证据只确认 `FULLTEXT`、`SPATIAL` 是独立索引定义，不在本答案中扩展其专门用途与限制。
- InnoDB 二级索引记录包含主键列，所以主键长度会影响每个二级索引的空间占用；这是明确的 InnoDB 边界，不应外推到所有存储引擎。

## 原理机制

可以把索引问题分成两个状态路径。

查询路径是 `查询条件 → 可用索引条目 → 定位候选行`。索引让 MySQL 不必只依赖全表逐行检查，但是否实际采用某个索引由查询与优化器决定；本题只陈述官方文档支持的“索引帮助定位满足条件的行”这一层，不承诺任何具体 SQL 必然走索引。

维护路径是 `INSERT/UPDATE/DELETE → 表数据变化 → 相关索引也要维护`。因此每增加一份索引结构，就增加空间与写维护成本。InnoDB 还多一层结构关系：`secondary key → secondary index record（含主键列）→ clustered index 中的行`。这解释了为什么 InnoDB 主键设计会影响二级索引空间。

## 项目经验版

项目映射时先记录真实存储引擎、现有主键和索引、主要查询条件、读写比例、索引空间，再用具体 SQL 和执行计划验证设计。没有这些事实时，不虚构“某字段应当排复合索引第一位”“某索引一定覆盖查询”或“建立索引后性能必然提升多少”。

## 常见追问

- 问：`KEY` 和 `INDEX` 有区别吗？答：MySQL 8.4 `CREATE TABLE` 文档把 `KEY` 定义为 `INDEX` 的同义写法，不要把二者解释成不同物理索引。
- 问：主键索引和 InnoDB 聚簇索引是一个概念吗？答：不是同一分类维度。InnoDB 通常使用主键作为聚簇索引，而聚簇索引保存行数据；回答时应注明这是 InnoDB 的组织规则。
- 问：为什么不能给每列都建索引？答：官方优化文档明确说无用索引浪费空间，而且每个索引增加 INSERT、UPDATE、DELETE 的维护成本。
- 问：为什么 InnoDB 主键不宜无边界地变长？答：官方文档明确二级索引记录包含主键列，因此长主键会增加二级索引空间。
- 问：复合索引列顺序怎么选？答：本题现有证据只确认一个索引可有多个 key part；具体顺序必须结合具体 SQL 和更细的一手优化规则验证，不能脱离查询直接给万能口诀。

## 易错点

- 不要把 PRIMARY/UNIQUE、BTREE/HASH、clustered/secondary 当成同一个分类维度。
- 不要把 `FULLTEXT`、`SPATIAL` 的具体用途写得超过当前一手证据映射；这里只确认它们是独立 DDL 定义。
- 不要声称 PRIMARY/UNIQUE 的具体写入校验实现细节，除非补充对应的一手约束文档或源码证据。
- 不要在当前证据不足时宣称多列索引固定列顺序、覆盖索引免回表等更细优化结论。
- 不要把 `USING HASH` 当作所有 MySQL/InnoDB 普通索引的通用实现。
