# MySQL 领域全量面试题库

> 共计收录 645 道 MySQL 相关面试题。
> 💡 建议复习顺序：1️⃣ 基础概念 (L1_Principle) ➡️ 2️⃣ 运行机制与核心原理 (L2_Mechanism) ➡️ 3️⃣ 实战诊断与调优 (L3_Diagnostic)

## L1_Principle (251 道题目)

| Question ID | 题目 | 相关技术点 (Entities) | 题型 (Type) |
|---|---|---|---|
| f19d1ae5d9687b30792a51373071a836 | 辨析 MySQL 事务隔离级别：什么是不可重复读与幻读？ | transaction isolation, phantom read, non-repeatable read | 八股文_Concept |
| f19d1ae5d9687b30792a51373071a836 | 辨析 MySQL 事务隔离级别：什么是不可重复读与幻读？ | transaction isolation, rr vs rc | 八股文_Concept |
| 3d70889a1bddaee2f3afadc53db811c8 | 场景题：表 A 和表 B 的内连接与左连接结果分析 | inner join, left join | 八股文_Concept |
| 99f5ce7a47e5da2bdc732e71c45e991c | 创建索引的时候需要考虑哪些问题？ | 索引设计原则, 区分度 | 八股文_Concept |
| 3dc621e926b369996a63b781f313e786 | 读锁 and 写锁在 SQL 命令中的添加方式（悲观锁实现） | 悲观锁, select for update | 八股文_Concept |
| 4c1220880283044be603b0fee958020a | 读已提交（RC）会导致什么问题？ | mysql, 事务 | 八股文_Concept |
| 80e7ce1ae1a392686986d52397bca0de | 对比 MySQL 常用的存储引擎（如 InnoDB 与 MyISAM）的特性 | innodb, myisam | 八股文_Concept |
| b7fdd2795313ef6453a19fcd7976c379 | 对比 MySQL 中的 `FOR SHARE` 和 `FOR UPDATE` 的区别 | 共享锁, 排他锁 | 八股文_Concept |
| 90d36b925f780bf64a91fe6535001fef | 对比悲观锁与乐观锁的应用场景 | 乐观锁, 悲观锁 | 八股文_Concept |
| e921783f414b5d63e3512705c114acb3 | 二叉树架构：为什么 MySQL 选择 B+ 树作为索引结构而不是平衡二叉树（AVL/红黑树）？从树高与随机 IO 角度分析？ | b+树, 随机io, 树高 | 八股文_Concept |
| 1decdb0c9f2709b722f25e14b23d5c04 | 分库分表的策略有哪些？ | 分库分表 | 八股文_Concept |
| f33bfc1dbd2733b7f014313d62acb468 | 分库分表是怎么做的？ | 分库分表 | 八股文_Concept |
| 13dbeda07c4b24d9b1516c63e8d62c45 | 覆盖索引？ | 覆盖索引, 联合索引 | 八股文_Concept |
| 35757415dfea71ef0ed2e43d726603b7 | 覆盖索引与回表查询？ | 覆盖索引, 回表 | 八股文_Concept |
| 9cfff7eaafd61115ff1b26d3b3bc2a9c | 高性能索引设计：在什么情况下需要建立联合索引？如何确定索引列的最佳顺序？ | composite index, cardinality | 场景设计_Scenario |
| 1d8304cbc3876a1862bb587a34b0eca6 | 关系型数据库：谈谈你对数据库事务（Transaction）的理解？ | transaction | 八股文_Concept |
| 4c8fc58775c255e1ec41b536adf0675a | 回表？ | 回表, 二级索引, 聚簇索引 | 八股文_Concept |
| a042ae7a7e3ed47774e4540f0475c363 | 简单描述 MySQL 中, 索引, 主键, 唯一索引, 联合索引的区别 | 主键索引, 唯一索引, 联合索引, 普通索引 | 八股文_Concept |
| 497d2107e4d40e0150d75269ec75c614 | 解释一下 MySQL EXPLAIN 执行计划的各个字段 | explain | 八股文_Concept |
| e4d748f493745e446c88a677fe82df94 | 解释最左前缀原则及常见的索引失效场景？ | 联合索引, 索引失效 | 八股文_Concept |
| 23d393f190aa0fbec96144306742bca4 | 介绍一下联合索引吧 | 联合索引 | 八股文_Concept |
| 863a09fa45fa3af400ce66f8e4068ef7 | 聚簇索引和非聚簇索引？ | 聚簇索引, 非聚簇索引, b+树 | 八股文_Concept |
| 2899582274f7773b01e4c9eb859c4917 | 聚簇索引和非聚簇索引的区别 | clustered index | 八股文_Concept |
| a60d612abdf69979c6b4eed91188fd64 | 聚簇索引与非聚簇索引，索引失效的情况 | 聚簇/非聚簇索引, 回表查询, 覆盖索引, 最左前缀索引失效 | 八股文_Concept |
| 83256bc439a542ad19a6801e8f27038b | 聚簇索引与非聚簇索引的区别？ | clustered index | 八股文_Concept |
| b7f49eac5f8fa7fb4cefc8eda84b6bf6 | 聚簇索引原理：叶子节点直接存储完整数据行的物理组织方式？ | clustered index | 八股文_Concept |
| d7dc47dee3c3bd6b041a9bad45718799 | 看索引是否命中是哪个字段? | key, possible_keys | 八股文_Concept |
| 1c966513893313d3ea984f05be599760 | 可以说一说Mysql幻读和脏读的区别吗？ | mysql, 幻读, 脏读 | 八股文_Concept |
| 125efe4b9cbe7b0ee8a9b6aa7025d7a4 | 了解数据库隔离性吗？ | 事务隔离级别, acid | 八股文_Concept |
| 50124570dcbc85745738674980410ce7 | 了解MySQL的索引吗？有什么用 | mysql, 索引 | 八股文_Concept |
| 467369867314a93a134858bf0d4a3522 | 利用数据库表介绍 EXISTS 关键字 (返回 TRUE 还是 FALSE)? | exists, semi-join | 八股文_Concept |
| 8bd442a5a6941faa4e78145a636a9cc1 | 联合索引：在什么情况下索引会失效（如违背最左匹配原则、范围查询、函数操作等）？ | composite index, leftmost prefix rule | 八股文_Concept |
| e6535be68759af9b0702612c3a8f309c | 慢SQL调优的具体步骤有哪些？ | mysql, sql调优 | 八股文_Concept |
| 857d5a447a278a075e4e62c2b8dbacf4 | 哪些情况下会导致 MySQL 索引失效？ | 索引失效, 联合索引 | 八股文_Concept |
| 140c3c9a73934ffbec6c72fa4f6eb3dd | 哪些情况下会导致数据库索引失效？特别地，联合索引在什么情况下会失效？ | 最左前缀法则, 表达式失效 | 八股文_Concept |
| 246f3c46f20226b9ede19ca6acc139ac | 哪些数据结构的插入和查询复杂度是 O(1) 的？请分析 MySQL B+ 树索引的效率优势 | b+树, 时间复杂度 | 八股文_Concept |
| b1a79576a1ee67a3ab9cdec4166a80b0 | 请对比聚簇索引和非聚簇索引的区别 | 聚簇索引, 非聚簇索引 | 八股文_Concept |
| ae737b4b0d8942e20d60ddb9ab74d33e | 请解释 MySQL 中行锁与表锁的概念及各自适用的业务场景 | 行锁, 表锁 | 八股文_Concept |
| 53bf41a94f5a1bf72ebb1f60370b901c | 请解释数据库事务中的 ACID 特性及其实现方式 | acid, mvcc | 八股文_Concept |
| 30ff38b078ecffc0ba649f2ea8687d9c | 请解释最左前缀匹配原则及其重要性 | 索引原则 | 八股文_Concept |
| f1b88e2e4aa9627885fa923c360be346 | 请介绍 MySQL 中 explain 命令的作用及关键字段含义。 | explain, mysql | 八股文_Concept |
| 4d55b39edaa8eb16e9ada01c32e3370a | 请介绍传输层的核心协议（TCP, UDP） | 最左前缀 | 八股文_Concept |
| 3df90c39f22a90d2926ab7e842b23815 | 请介绍读写分离的适用场景及其解决的核心问题 | 读写分离 | 八股文_Concept |
| 32206a71ceb4a67dce66e9d7f7460178 | 请介绍数据库索引底层的常用数据结构 | b+树, hash index | 八股文_Concept |
| bafb45bc01984d5ca9ee880a9522b207 | 请列举 MySQL 事务的四大特性（ACID），并解释不同的隔离级别分别解决了哪些并发问题（脏读、不可重复读、幻读） | acid, 隔离级别 | 八股文_Concept |
| cf68c69785359d35b98b53611d663ba7 | 请详细介绍 MySQL 中有哪些常见的锁（如行锁、间隙锁、临键锁、意向锁等） | mysql锁, next-key lock | 八股文_Concept |
| 24f6b51f35620a6b21d421ef32ebe153 | 请详细介绍数据库索引的概念及其分类 | 索引, 唯一索引, 联合索引 | 八股文_Concept |
| 2d3f2a62e1f86140224a5cbb2438bc1e | 如何避免 MySQL 索引失效？ | 索引失效 | 八股文_Concept |
| d6c0a2cf7f72b30230417471c0fe7c97 | 什么情况下不建议使用数据库索引？ | 索引失效 | 八股文_Concept |
| a8e1a675f9f4d3696ca81eab7b038fb1 | 什么情况下设置了索引但无法使用 | 索引失效, 左模糊, 隐式转换, 函数计算, 优化器放弃索引 | 八股文_Concept |
| a8e1a675f9f4d3696ca81eab7b038fb1 | 什么情况下设置了索引但无法使用? | 索引失效 | 八股文_Concept |
| 430416cb19e88c8989fbbd6eafc5ae88 | 什么时候需要用到事务？ | 事务 | 八股文_Concept |
| ba2dde3e156641a325fefe55deaea14c | 什么是覆盖索引？ | 覆盖索引 | 八股文_Concept |
| 6d2290a291e006f86eefa573fd7efac2 | 什么是覆盖索引（Covering Index）？ | 覆盖索引 | 八股文_Concept |
| 541623e0770f1d399bdfe2df4a119389 | 什么是覆盖索引与回表查询？ | 覆盖索引, 回表 | 八股文_Concept |
| 57fd9588581df11cf2ac24b82980218a | 什么是回表？什么时候会触发回表？ | 回表, 二级索引 | 八股文_Concept |
| 800926ee76c90f8de04704912f06769f | 什么是事务的隔离级别？MySQL默认是哪 个？ | 事务, 隔离级别 | 八股文_Concept |
| c16beddf5c18f48ede1dd98b4e4e14a5 | 什么是数据库索引？它的本质是什么？ | 索引, b+树 | 八股文_Concept |
| 249c455978bbb38b3597e5272d02daf9 | 什么是索引？为什么数据库需要索引？ | database index | 八股文_Concept |
| 08b915a1f88e082b3a96688af72d41e1 | 什么是索引覆盖？ | 覆盖索引, 回表 | 八股文_Concept |
| e631a53bf8208f2b7810ae411328ed1e | 什么是索引覆盖（Index Covering）？它能带来哪些性能提升？ | 覆盖索引 | 八股文_Concept |
| 58affc4af8837116b039e9f28f704b8a | 什么是脏读？什么是幻读？ | mysql, 事务 | 八股文_Concept |
| fc1f7b383d97caf9585b28337e887e62 | 实际使用中见过哪些索引？ | 索引, b+树, 聚簇索引 | 八股文_Concept |
| 977baaee26107edfeb3b0426ce7261cd | 事务的 ACID 四大特性解析？ | acid | 八股文_Concept |
| 1b19f2636e375aa6f16e4abe61a485e2 | 事务日志：Redo Log 与 Undo Log 分别保证了事务的哪些特性（ACID）？ | redo log, undo log | 八股文_Concept |
| 45a629e41e285031b00d0219ee9412cf2 | 事务一致性：详细分析本地事务（ACID）在交易链路中的边界界定？ | transaction boundary, acid | 八股文_Concept |
| 33e213bcb75751694ffd0a9d708c7eba | 数据库 Schema 设计：主键（Primary Key）与外键（Foreign Key）的作用及其对数据一致性的影响？ | primary key, foreign key | 八股文_Concept |
| 35590fe29d024dd3fdc19937887e22f0 | 数据库：聚簇索引与非聚簇索引：数据与索引绑定机制及“回表”查询的性能损耗分析 | clustered index | 八股文_Concept |
| 71f189a90a4fb7403a1be8fbbe865cc7 | 数据库：请说明 MySQL 的事务隔离级别以及 MVCC（多版本并发控制）的实现原理 | isolation level, mvcc | 八股文_Concept |
| e0a782d42e4a784f3f57257db3171d3d | 数据库：一条 SQL 语句从应用端发出到返回结果，在 MySQL 内部经历了哪些核心过程（如解析、缓存、优化器、执行器、存储引擎）？ | 执行路径 | 原理深度_UnderTheHood |
| 65ab4ade603cd2d98f12373fbb5c1b21 | 数据库：在 SQL 中什么是聚合函数？请列举 5 个常用的聚合函数及其典型用途。 | 聚合函数, count, sum, avg, max, min | 八股文_Concept |
| 5644639fe2536a8534fe6f2aa815d4da | 数据库：Binlog 的三种格式 (Statement, Row, Mixed) 及各自的写入时机考量 | binlog | 八股文_Concept |
| 91523d3de04ec14fd06d1cedbad43b68 | 数据库：GROUP BY 和 HAVING 的区别是什么？ | group by, having | 八股文_Concept |
| c86168311cf677b833b95a8f045837b2 | 数据库：INNER JOIN, LEFT JOIN, RIGHT JOIN 之间有什么区别？ | join | 八股文_Concept |
| bdb06d7a1a94b1f2424a5e029ed7bb93 | 数据库：MySQL 常用日志体系 (Binlog, Redo Log, Undo Log, Relay Log) 的功能与写入时机 | mysql logs | 八股文_Concept |
| 01cc339e425078fe3bf6e62c37ef4e83 | 数据库：MySQL 索引选型：为什么 B+ 树比 B 树更适合大规模磁盘 IO？ | b+树, disk i/o | 八股文_Concept |
| 67eceb29871592c20f7b3e8e727a88d0 | 数据库：MySQL各种索引结构对比；为什么 B+ 树优于 B 树？ | b+树 | 八股文_Concept |
| 41770f13cacccec43559623880ade572 | 数据库：MySQL主键设计的必要性分析 | primary key | 八股文_Concept |
| 813c061969715d764abcb86f8137f4ea | 数据库：SQL 统计重复数据：GROUP BY 与 HAVING COUNT(*) > 1 的应用 | group by, having | 八股文_Concept |
| d94103b45ba85b0b110188256cf00fa0 | 数据库的隔离级别有哪些？MySQL 默认使用的是哪种？ | 隔离级别, rr | 八股文_Concept |
| 6e2f24cab49a0cbacc2c11ec799c95dc | 数据库隔离级别有哪些? | 隔离级别 | 八股文_Concept |
| f4dc273cb3e66ea44ae3c7ab84249477 | 数据库核心：ACID 特性的具体含义及其在 MySQL 中的实现支柱？ | acid, redo log, undo log | 八股文_Concept |
| f4dc273cb3e66ea44ae3c7ab842494770 | 数据库核心：ACID 特性的具体含义及其在 MySQL 中的实现支柱？ | acid, redo/undo log | 八股文_Concept |
| 929484bad01001d817f82e07c8aa7573 | 数据库事务的隔离级别有哪些？分别解决了哪些并发执行中的问题（如脏读、不可重复读、幻读）？ | 隔离级别 | 八股文_Concept |
| d61af97d0a4d175219fa67fb3cf62e22 | 数据库事务的隔离级别有哪些？MySQL默认是哪种？ | transaction, isolation levels | 八股文_Concept |
| c735014af684f25e0f4f346ab5dce194 | 数据库索引：聚簇索引的应用场景与B+树底层布局 | clustered index, b+树 | 八股文_Concept |
| 91c522fe2fa9f89605e94e49c6bf4385 | 数据库索引：聚簇索引与非聚簇索引，覆盖索引 | 聚簇索引, 非聚簇索引, 覆盖索引 | 八股文_Concept |
| 22397d6cdfb9f54cf629629696ef8da8 | 数据库索引：在实际项目中，你是如何设置数据库索引的？为什么“索引覆盖”（Covering Index）能显著提升查询速度？ | covering index, index optimization | 八股文_Concept |
| da0886a823dd64bff7b0c1fabd086780 | 数据库索引：B 树与 B+ 树在结构及查询效率上有何区别？ | b+树, b-树 | 八股文_Concept |
| a66e85cbedde34a8d955f2114718ee13 | 数据库索引：MySQL 的索引（B+ 树）是如何实现的？为什么 B+ 树比 B 树更适合处理范围查询（Range Query）？ | b+树, b tree, range query | 八股文_Concept |
| d46862d92b54e14c2d7e2f79f561294f | 数据库索引：MySQL 索引设计的核心原则有哪些？在索引性能与存储效率上，自增 ID 为何通常优于 UUID？ | indexing principles, uuid vs auto-increment | 八股文_Concept |
| d1201d9c588a133c046c0b47a4faf887 | 数据库索引：MySQL InnoDB 为什么选择 B+ 树而非 Hash 索引或 B 树？ | b+树, index structure | 八股文_Concept |
| 2622a45648b3f99e2cb7d85299c1e032 | 数据库索引的底层结构（B+ 树 vs 哈希表）？ | b+树, 哈希索引 | 八股文_Concept |
| 2622a45648b3f99e2cb7d85299c1e032 | 数据库索引的底层结构（B+ 树 vs 哈希表）？ | b+树, 哈希索引 | 八股文_Concept |
| fb44ed3e7e1447f36cdfd3da58c66f6b | 数据库索引底层原理（B+ 树结构及优势）？ | b+树, indexing | 八股文_Concept |
| 1798ba06da7b5db86e38ac65ca678bb3 | 数据库索引分类 | 索引分类, 聚集索引, 非聚集索引, 唯一索引 | 八股文_Concept |
| f83da4ca083910a3e858a8e54b8bba6c | 数据库索引一般是用什么数据结构？和其它数据结构有什么区别？ | b+树, 哈希索引 | 八股文_Concept |
| 73e2b7e117dba46af1bac615121e58e1 | 数据库性能：在 MySQL 中，单表数据量达到 2000w 以后性能会明显下降，其本质原因是什么（涉及 B+ 树层高、磁盘 I/O、内存命中率）？ | b+ tree tree height, disk i/o, buffer pool | 八股文_Concept |
| df8cb3a414ffc567c3e7a61368ad05b3 | 数据库引擎有哪些？说说他们的区别 | innodb, myisam | 八股文_Concept |
| fdb7455ba33c801b12919587b61f1681 | 说说索引的底层实现？ | b+树, 聚簇索引 | 八股文_Concept |
| 9ed5f7e45157170e20bc0ffbe1139e15 | 索引，InnoDB默认索引 | 索引, innodb | 八股文_Concept |
| c9c14751736c09aab67aa37c19618b85 | 索引的使用 | 索引 | 八股文_Concept |
| 194a3806d35723ee29c1de2041b7d857 | 索引失效：请枚举并分析导致 MySQL 索引失效的常见场景（如函数操作、隐式转换、不等于判断等） | index invalidation | 八股文_Concept |
| 37ef24a4910e4b6796fa01c828b7a91e | 索引失效场景有哪些? | index optimization | 八股文_Concept |
| f4e92f0ca65b0a4985beb0ffee054273 | 索引一定越多越好吗？ | 索引优化, dml回推 | 八股文_Concept |
| 0096702888d0bd5b427d3369c20f6ab0 | 索引优化：复合索引（A, B, C）与分别建立 A, B, C 单个索引在查询性能与磁盘空间上的区别？ | 联合索引, 索引命中 | 八股文_Concept |
| e7a367fdd5c6e61fa6e115b21a8c8428 | 谈谈 MySQL 的事务机制 | acid, mvcc | 八股文_Concept |
| 37e6aeef00d2ea273193b2d6b230f832 | 为什么要高并发下发数据不推荐关系数据库？ | 关系数据库, iops, 连接数连接池 | 原理深度_UnderTheHood |
| 5a1a2c17b1a0e4049480decc1ff4b415 | 为什么用 B+ 树？ | b+树, 磁盘io | 八股文_Concept |
| 8bb9a2c47c4ab709595b9b4b9cf98a82 | 为什么MyISAM查询性能好? | myisam | 八股文_Concept |
| c6e5c60d3d375d3ca596b1339358cacc | 问了一下mysql，堆栈 | mysql, 堆, 栈, 数据结构 | 八股文_Concept |
| ce0a91945a629e41e285e1c300d0219e | 详细罗列 MySQL 索引失效的几种常见情况？ | index optimization | 八股文_Concept |
| 23abb3b30c74ccabae2c537eeaaeb3e4 | 在查找数据时，聚簇索引 (Clustered Index) 与非聚簇索引 (Secondary Index) 的主要区别是什么？ | 聚集索引, 回表 | 原理深度_UnderTheHood |
| 176ff2be1f763a7a4444cd3b940fd218 | 在什么情况下 MySQL 索引会失效？平时你是如何进行索引问题的排查与定位的？ | 索引实战 | 场景设计_Scenario |
| 6119384526888a94117cd2b83130813b | 在实际开发中，你会遵循哪些原则来创建索引？ | b+树 | 八股文_Concept |
| e64ecc6115d3054f9caf124276a35612 | 在数据库设计中，索引建立过多会对系统产生哪些负面影响？ | index overhead | 八股文_Concept |
| 173cff1468974a0ac4187d97a15af02b | 怎么理解 MySQL 事务的四大特性 (ACID)？ | acid | 八股文_Concept |
| 92c63bc390d9e2833421cedd76998ee9 | 主键索引 and 唯一索引的区别 | 主键, 唯一索引 | 八股文_Concept |
| 85393090d1eceb1ac8a11f30b31eca2d | 最左前缀原则及索引失效场景？ | 最左前缀匹配, 索引失效 | 八股文_Concept |
| 0dd53cd673d0b2cbd67b9efce8af62fe | 最左前缀原则示例 | 最左前缀原则 | 八股文_Concept |
| ef96de28b12e32ba05807c71ff3c05cd | B+ 树与 B 树的区别？ | b+树, b tree | 八股文_Concept |
| 99cd272b259fda08c9677b57d85ada49 | B+树相比 B 树的优势 | b+树, b tree, disk io | 八股文_Concept |
| 39ccbb8f14cad70714cab4ed4cec2351 | B+Tree 索引与数据量 | b+tree层级高度估算, 页数据块大小, 叶子节点数据承载量, 两三千万行数据阈值 | 八股文_Concept |
| 11e5a03034639a1e6d79256a2d31477e | DML 和 DDL 是什么? | dml, ddl | 八股文_Concept |
| 2f2fb74e5668713a16ab745b6e317179 | InnoDB 存储引擎的核心事务隔离级别是什么？辨析可重复读（RR）与读已提交（RC）的区别？ | transaction isolation, rr vs rc | 八股文_Concept |
| 95de03286b1696fefa323dda33b56ec8 | Innodb 的索引结构和 myisam 有区别吗? | innodb, myisam, b+树 | 八股文_Concept |
| 95de03286b1696fefa323dda33b56ec8 | Innodb 的索引结构和 myisam 有区别吗？ | 聚簇索引, 非聚簇索引, b+树叶子节点, innodb, myisam | 八股文_Concept |
| 813bfbc973bd450a469eaf8a398dc141 | InnoDB 的索引类型有哪些？聚簇索引与非聚簇索引的区别是什么？ | 聚簇索引, 非聚簇索引, innodb | 八股文_Concept |
| 715204cc65893ef3fa7e907541535501 | InnoDB 和 Myisam 的区别 | innodb, myisam, 事务, 行级锁, 外键, 崩溃恢复 | 八股文_Concept |
| 018bceae70db74af06301d7563100778 | InnoDB 和MyISAM区别 | innodb, myisam | 八股文_Concept |
| 6f55852e6796f9f91350ce7d465c0caa | InnoDB 默认隔离级别 | rr, 可重复读 | 八股文_Concept |
| 7d142387431327816348a97f7fdcedae | InnoDB 默认隔离级别是什么? 解决了什么问题? | rr, 不可重复读 | 八股文_Concept |
| a29a12c573b6e86a6bb73f6e2ae21574 | InnoDB 中有哪些锁类型（行锁/表锁/间隙锁/临键锁）？ | mysql locks, next-key lock | 八股文_Concept |
| 715204cc65893ef3fa7e907541535501 | InnoDB和MyISAM的区别 | innodb, myisam, 存储引擎 | 八股文_Concept |
| 1020cfc1ec313ce70cb6f549f1511a1d | Innode 的索引结构和 myisam 有区别吗？ | innodb, myisam, b+树 | 八股文_Concept |
| ec1127bd35cc631330060f747423b113 | MyISAM 和 InnoDB 的区别是什么? | myisam, innodb, 存储引擎 | 八股文_Concept |
| 45b629e41e285031b00d0219ee9412ch2 | MySQL 存储引擎：深入剖析 InnoDB 的 B+ 树索引结构，以及为什么这一结构最适合做磁盘存储？ | b+树, clustered index | 八股文_Concept |
| 3eae64b9378ff82f2cab8cf7095da7b1 | MySQL 存储引擎：InnoDB 为什么优先选择 B+ 树作为索引结构，而非 B 树、红黑树或平衡二叉树？ | b+树, innodb | 原理深度_UnderTheHood |
| 577a9d67be2981aa151d8af79afd212d | MySQL 存储引擎比较 | innodb, myisam | 八股文_Concept |
| 10819c5a86cb3827a04cca519248cc88 | MySQL 存储引擎对比：InnoDB 与 MyISAM 的关键技术差异（锁、索引、事务支持）？ | innodb, myisam, mvcc | 八股文_Concept |
| ac8ea8c8a6bf08a7428e229c5f96f579 | MySQL 存储引擎有哪些？区别是什么？ | innodb, myisam | 八股文_Concept |
| 75885015c13fe9d5e798ed3ba6ab051c | MySQL 的常见优化手段有哪些？ | sql优化, 索引优化, 分库分表 | 八股文_Concept |
| 094d4ff47d905d03e076343ae4cbd5a1 | MySQL 的隔离级别有哪些？默认级别是什么？可重复读（RR）解决了哪些并发问题？ | 隔离级别, rr | 八股文_Concept |
| 790b72510ec69826ccaaa63df3a44e16 | MySQL 的事务隔离级别有哪些？并发事务可能会导致哪些问题？ | 隔离级别, 脏读, 不可重复读, 幻读 | 八股文_Concept |
| d575199b0d2c482c3c85e1359ef97a8f | MySQL 的索引结构是什么？有哪些特点？ | b+树, 索引 | 八股文_Concept |
| bcdc2df097ccb98d3c195ece56b52af7 | MySQL 的索引是什么结构？ | b+树, 哈希索引 | 八股文_Concept |
| ae35d0c8e3552a1f2add28300ba5c6a9 | MySQL 的一级索引 and 二级索引的区别 | 聚簇索引, 二级索引 | 八股文_Concept |
| dc4579f2508284d9c590e6eee5cda10b | mysql 的主键索引和唯一索引有什么区别？ | 主键索引, 唯一索引 | 八股文_Concept |
| 472e0113c95323556e69287990affeac | MySQL 高可用：常见的主从同步方案有哪些？请对比它们的优劣势 | replication | 八股文_Concept |
| b3f51e626778f8ae39193d57ba2277bc2 | MySQL 隔离级别：RR 级别下是如何解决幻读（Phantom Read）的（MVCC + Next-key Lock）？ | mvcc, next-key lock, phantom read | 八股文_Concept |
| 0225a02c421a419c7f9e8a4a2390933b | MySQL 基础：Primary Key 与普通 Index 在底层存储及查询上有何区别？ | clustered index | 八股文_Concept |
| a94d088e40f616c5861729a2c16d8821 | MySQL 架构：B+ 树相比 B 树在磁盘 I/O 次数及范围查询（Range Scan）上的核心性能改进？ | b+树, b tree, disk io | 八股文_Concept |
| d1cc77113f72f113d86e7f3012974ae6 | MySQL 建表时需要考虑哪些因素？ | 建表规范, 字段选型, 索引设计 | 八股文_Concept |
| d04046e29236467a99a0de40ae5a222e | MySQL 里记录货币用什么字段类型好 | decimal, 浮点数精度损失, 整型转换 | 八股文_Concept |
| 4ef237320c2554c2ab991efa50a1a065 | MySQL 联合索引：有三列 (a b c)，用 a=* 和 c=* 能够进行联合索引查询吗？ | 联合索引, 最左前缀匹配, 索引下推 | 坑题_Gotcha |
| de820116e965413e11e7e38401407b48 | MySQL 联合索引原理：a_b_c 三列联合索引的排序规则及最左前缀匹配？ | composite index, leftmost prefix | 八股文_Concept |
| 51be429b8c914cad1fbe8e1064e7a9f6 | MySQL 默认的隔离级别是什么? 解决了什么问题? | 隔离级别, rr | 八股文_Concept |
| ab44dc4052ad57b7023f4a59d73bdbb5 | MySQL 默认是什么存储引擎,为啥用这个? | innodb | 原理深度_UnderTheHood |
| ef3c15c13384f32fdde459b08c2d1e1d | MySQL 设计原则：谈谈你对数据库库表设计原则（规范化 vs 反规范化、属性选择、索引设计）的理解？ | 数据库设计, 规范化 | 原理深度_UnderTheHood |
| 7ab341ba0e8da633c3dfdb12107107a3 | MySQL 事务的隔离级别，分别解决了什么问题？ | 事务隔离级别, 原子性, 隔离性 | 八股文_Concept |
| 5208c6938fb169ed0396ded37a689270 | MySQL 事务的隔离级别，默认隔离级别是什么？ | mysql, 事务隔离级别, 可重复读 | 八股文_Concept |
| b8e90a743b36cda460e385d051441ae9 | MySQL 事务隔离：详细辨析不可重复读（Non-repeatable Read）与幻读（Phantom Read）在并发事务中产生的根本原因？ | isolation level, concurrency issues | 八股文_Concept |
| 04ac4333dc57aa980951904029986ee7 | MySQL 事务隔离级别及解决的问题？ | isolation levels, acid | 八股文_Concept |
| e24af239bfffd70036fbbce4c02be1b7 | MySQL 事务特性 (ACID) 及隔离级别 | acid, 隔离级别 | 八股文_Concept |
| 9f336231151f6c40624a5d1e9e5151d0 | MySQL 数据库：在聊天系统中，哪些数据适合存放在关系型数据库中？ | relational data, user information, friendship | 场景设计_Scenario |
| 52c7be362af8e9988234301724881dcd | MySQL 数据库的存储引擎了解过哪些? | 存储引擎, innodb, myisam | 八股文_Concept |
| 9c4c443f12f61cd121a7eade74e5c2db | MySQL 数据容灾：描述 MySQL 备份的最佳实践及其与 binlog 恢复流程的结合？ | mysql backup, point-in-time recovery | 八股文_Concept |
| 9c4c443f12f61cd121a7eade74e5c2db | MySQL 数据容灾：描述 MySQL 备份的最佳实践及其与 binlog 恢复流程的结合？ | mysql backup, point-in-time recovery | 八股文_Concept |
| b0e838bb749552dc90bda77704fb92c7 | MySQL 索引：回表与索引覆盖的概念？ | table lookup, covering index | 八股文_Concept |
| bece29125c757120170398a2ffae1d4d | MySQL 索引：简述 MySQL 索引的实现原理。 | mysql, 索引 | 八股文_Concept |
| 4371dd2687a377ecdfe176c889176f91 | MySQL 索引：解释聚簇索引（Clustered Index）和覆盖索引（Covering Index）的概念及区别。 | mysql, 索引 | 八股文_Concept |
| f212949c85e0added7f7b693759500ea | MySQL 索引：介绍 MySQL 索引的底层数据结构。什么是最左前缀匹配原则？ | mysql, 索引, 最左匹配 | 八股文_Concept |
| 42a7b8cf8217288be39b08bc68bc98ec | MySQL 索引：详细辨析聚簇索引（Clustered Index）与非聚簇索引的 B+ 树叶子节点存储内容差异？如何精准避免回表？ | clustered index, non-clustered index | 八股文_Concept |
| 85e198b37fffb9187b536cb102d4db42 | MySQL 索引的底层数据结构是怎样的？ | b+树, 磁盘索引 | 八股文_Concept |
| 263763c5aaa7b4959d83553ea939064c | MySQL 索引的底层原理是怎样的？ | acid | 八股文_Concept |
| a006eb0a65a3b897ad718c744db4d55b | mysql 索引结构，索引失效 etc? | b+树, 索引失效 | 八股文_Concept |
| 893c8a92466f3509a0c91b6bfe64337e | MySQL 索引进阶：唯一索引（Unique Index）与普通索引在插入与查找性能上的细微差异？ | unique index, change buffer | 八股文_Concept |
| 17d347d0c99f3d11960e9bb63d765bd8 | MySQL 索引深度：索引失效的常见场景分析？ | mysql index, index failure | 八股文_Concept |
| 5d12109eab7defd034e9819fe69d36b0 | MySQL 索引深度：索引是越多越好吗？分析索引过多的负面影响（如 写入性能、空间成本）？ | 索引优化, 写放大 | 八股文_Concept |
| 724b231c3df4cb95faa6d41f1195c4c2b | MySQL 索引失效场景：请详细列举至少三种导致 B+ 树索引失效的操作？ | index invalidation, like-prefix, function-on-column | 八股文_Concept |
| 90da07c0319687961ec14db2e557aa6f | MySQL 索引失效的常见场景？ | 索引失效 | 八股文_Concept |
| e26ffaf82bff77ad2f0cc338cb9f7dd2 | MySQL 索引失效的场景有哪些？ | 索引失效, mysql, 最左前缀法则 | 八股文_Concept |
| e26ffaf82bff77ad2f0cc338cb9f7dd2 | MySQL 索引失效的场景有哪些？ | 索引失效, 最左前缀原则 | 八股文_Concept |
| e3fc59ba962006f86cb1c87179fc1e40 | MySQL 索引原理 | b+树, 聚簇索引, 二级索引 | 八股文_Concept |
| ea5bc67a09e1b150138c7d7b29cc81bd | MySQL 锁机制：如何在 SQL 层面实现乐观锁与悲观锁？ | 乐观锁, 悲观锁 | 八股文_Concept |
| ab617fa2d023eaa5369b4bc5f338f6a9 | MySQL 一张表能创建几个 B+ 树索引？在什么情况下会触发“回表”操作？ | 非聚集索引, 回表 | 八股文_Concept |
| 036eca09b8db013f0756dbd2256eac4b | MySQL 有关权限的表都有哪几个 | 权限表, user, db, tables_priv, columns_priv | 八股文_Concept |
| 5545882869db1b4f403050ae39ba8626 | MySQL 有缓存吗？ | query cache, buffer pool | 八股文_Concept |
| fa5ca855d21cf533357b07aa68beb20a | MySQL 运维：如何启动 MySQL 及其查看实例状态？ | mysql operation | 八股文_Concept |
| 6c6f9caae81665791325d5096fe659b6 | MySQL 在哪些情况下会发生“回表查询”？如何避免回表？ | 回表, 覆盖索引 | 八股文_Concept |
| 3299e5532ea15bec4371044fda6aef76 | MySQL 知识体系了解哪些? | mysql | 八股文_Concept |
| 9bd7f75703cdad3dc6ca109e129735f6 | MySQL 中 MyISAM 与 InnoDB 的区别? | myisam, innodb, 事务支持, 锁粒度 | 八股文_Concept |
| 39165067817ae96e2bcaab42524cc5d3 | MySQL 中 VARCHAR 与 CHAR 的区别以及 VARCHAR(50) 中的 50 代表的涵义是什么? | 数据类型, varchar, char | 八股文_Concept |
| 77db8a1cc41051739bc18c0e8be7138b | MySQL 中 VARCHAR, CHAR, TEXT 三种类型的区别及适用场景？ | varchar, char, text | 八股文_Concept |
| 5cde6cd4a07cd5e6367d27f10074b39d | MySQL 中包含哪些类型的索引？请分别简述其作用。 | mysql索引, b-tree索引, hash索引 | 八股文_Concept |
| df2633358fdba27f2bd0fdb92f005c6a | MySQL 中导致索引失效的原因有哪些？ | mysql索引, 索引失效 | 八股文_Concept |
| 05663892466ff3509a0c91b6bfe64337f | MySQL 中的乐观锁与悲观锁应用场景及其具体实现方式？ | optimistic locking, pessimistic locking, version field | 八股文_Concept |
| 44bca77bf1498b10808551443d52b2af | MySQL 中索引的主要作用是什么？ | mysql索引 | 八股文_Concept |
| 6eeba00b10fb59782d0f7750065efa0e | MySQL MVCC 实现原理：详细辨析实时读（Current Read）与快照读（Snapshot Read）的区别？ | mvcc, snapshot read | 八股文_Concept |
| 1bbbf602c719615fd56eff5a770d6f92 | MySQL undo log vs redo log | undo log, redo log, crash recovery | 八股文_Concept |
| 9b3850b379d3697788426de37c5a6bcb | MySQL：表数据量级达到多少建议水平分表？(千万级) | sharding threshold | 八股文_Concept |
| ec9764fbebef55c15756ef868bdde64e | MySQL：常见数据类型及其用途；Char与Varchar在底层的具体存储区别 | varchar, char | 八股文_Concept |
| 29000723bec1277c9c0967e030f0e559 | MySQL：隔离级别、幻读及MVCC隔离机制 | transaction isolation, phantom read, mvcc | 八股文_Concept |
| 4ebd3e4d33b8d66cb0eee00c0d22dabe | MySQL：聚簇索引与非聚簇索引的区别 | clustered index | 八股文_Concept |
| 8ebdb71302cbd3788d53a45232b377a6 | MySQL：如何显式创建聚簇索引与非聚簇索引？ | primary key, index creation | 八股文_Concept |
| ba9a5a8dd2c8f3389bfcbad876ef5c8c | MySQL：什么是索引？详述B+树索引结构及其优势 | b+树 | 八股文_Concept |
| 453f4e957cbdcf11e2206e845c68d7a2 | MySQL：最左匹配原则详解 | 最左匹配原则 | 八股文_Concept |
| 88acf7cf8015452cc5a82e3ed3ec2fbe | MySQL：B+树索引结构及其优势 | b+树 | 八股文_Concept |
| 29bdeb024a9f55a4735b8173d7dbcbd9 | MySQL：MyISAM与InnoDB存储引擎性能差异及查询场景选型分析 | innodb, myisam | 八股文_Concept |
| da94da1714055f9836670d8707f9d9d0 | MySQL：MySQL默认存储引擎及其特性优势 | innodb | 八股文_Concept |
| ddf1ae7aaaba4d81abfd1c7646c9085e | mysql常用索引类型 | b+树索引, hash索引 | 八股文_Concept |
| f507041bc683ff0ea984a4bb4a2164b4 | MySQL存储引擎：聚簇与非聚簇索引对比；B+树优势 | clustered index, innodb | 八股文_Concept |
| 7f36a6e653cc4ecfa7278fa3e9e76bdd | MySQL的三个日志（binlog, redo log, undo log）。 | mysql | 八股文_Concept |
| 0b602bc276afd72a33ac8ed832b4456f | MySQL的事务隔离级别，分别解决什么问题。 | 隔离级别 | 八股文_Concept |
| 1e0183dc6029e9b676a96a73e9287af6 | MySQL的事务隔离级别？ | 事务隔离级别, read committed, repeatable read | 八股文_Concept |
| e59de870f6c6ca0b184e9142fd69b986 | MySQL的事务隔离级别及其默认级别？ | 隔离级别, rr, rc | 八股文_Concept |
| e874babdf2a197bd74bd89422b9feb60 | MySQL的四个隔离级别。 | mysql, 事务 | 八股文_Concept |
| 730ac66c54e0748bb46305d2261f79bb | Mysql的索引类型和数据结构划分为哪些？ | mysql, 索引, b+树 | 八股文_Concept |
| 015fda9029596fb626b2db7cde7f5555 | MySQL分库分表。 | mysql, 分库分表 | 八股文_Concept |
| a02480184c54507fcc77cd5b7ff5d7bf | mysql隔离级别 | mysql, 隔离级别, 读未提交, 读已提交, 可重复读, 串行化 | 八股文_Concept |
| a02480184c54507fcc77cd5b7ff5d7bf | MySQL隔离级别 | 隔离级别 | 八股文_Concept |
| 785c5128bd302a78f7429470c58638ba | MySQL回表是什么？ | 回表, 二级索引 | 八股文_Concept |
| 3879b858f00ad3da4a7154cc0f3dbc2f | MySQL里主要有哪些索引结构?哈希索引和B+树索引比较? | b+树, 哈希索引 | 八股文_Concept |
| 0650d251caaf571a2b29648bba509d3d | MySQL默认的事务隔离级别是哪个？ | mysql, 事务 | 八股文_Concept |
| 837646eedbb3c0addcde110cd92f333b | MySQL默认事务级别 | 事务隔离级别 | 八股文_Concept |
| cc15dc25899a305c6d8a848ac5edda2d | MySQL事务 | 事务, acid | 八股文_Concept |
| 93169ace3d77eeeabd99f371f1b8b7a3 | MySQL事务隔离级别? | 事务隔离级别, rc, rr | 八股文_Concept |
| 524687681f969d813303b825a35553d1 | MySQL事务隔离级别及其在该级别下分别解决的并发一致性问题 | mysql, 事务隔离级别, 脏读, 不可重复读, 幻读 | 八股文_Concept |
| c4fff66018bbf0b602e1ae40548d4866 | mysql数据库默认存储引擎，有什么优点 | innodb | 八股文_Concept |
| 81832664061b85ae2486104efd4e6927 | MySQL索引：为什么选B+树而不是B树？ | b+树, b-tree | 八股文_Concept |
| 397dbc64e4ac245c21fd6daa85d1ae41 | MySQL索引：B+树索引结构及优势？ | b+树原理, 索引优点 | 八股文_Concept |
| 2c136e7f9c6025da71ebb1a637b1653f | MySQL索引结构分析：B+树的优势在哪里？ | b+树 | 八股文_Concept |
| 5ac8df646e1fefe721dfbc77e09d561e | MySQL索引剖析：B+树与Hash索引的区别；索引失效与覆盖索引场景分析 | index invalidation, covering index, hash index | 八股文_Concept |
| e0091bc780849b431db02c6f329a6339 | mysql索引有哪些 | 索引 | 八股文_Concept |
| e0091bc780849b431db02c6f329a6339 | MySQL索引有哪些？ | b+树索引, 哈希索引, 全文索引, 聚簇索引 | 八股文_Concept |
| 904ed936cfd0394feeecf5329813d6cc | MySQL锁有哪些？ | 表锁, 行锁, 间隙锁, 临键锁 | 八股文_Concept |
| 55c69fb491215ba7c258b9c372114f21 | MySQL有几种隔离级别？ | mysql, 事务 | 八股文_Concept |
| c54aefb628ba87d71904a9ef2b5f034c | MySQL有哪几种日志？分别的功能是什么？ | mysql | 八股文_Concept |
| c7743462494a2a74ce3603261361e00a | MySQL怎么分析SQL的性能（explain）？慢sql日志怎么开启？ | explain, 慢查询日志 | 八股文_Concept |
| 76352499dc77dd4f665c1b6842775c8e | MySQL中有哪些存储引擎？InnoDB和MyISAM的区别？ | mysql | 八股文_Concept |
| 47dfb7f0a434733ac970bc9cac6307e4 | redo log, undo log, bin log 的原理和作用 | redo log, undo log, bin log, 事务持久性及回滚, 主从复制 | 八股文_Concept |
| 2b578be03e88737411f5cd612d5e318e | SQL 查询优化中有哪些常用的方法？ | mysql | 八股文_Concept |
| e94bd33160711d1c3c04d43a8e9ebfc9 | SQL 基础：熟练使用 SELECT, INSERT, UPDATE, DELETE 关键字及 ORDER BY 排序？ | crud | 八股文_Concept |
| 3763cd816a67e313d27962b88fd99a45 | SQL 基础：MySQL 父子表关联方式、一对多查询实现及删除外键风险？ | 关联查询, 外键 | 八股文_Concept |
| dc024410221f00d23c1032128919e2e2 | SQL 中 Join 的作用及各类 Join 区别（INNER/LEFT/RIGHT/FULL）？ | sql join | 八股文_Concept |
| fa7370a2509ba649304b3463e770b196 | SQL：编写一个包含 Join On 的查询语句 | sql, join | 八股文_Concept |
| c66470f7d4eade4ad8b5b8c02a536c53 | SQL：查找员工薪资第二高的信息 | sql, limit, offset | 八股文_Concept |
| 769d1d6c348c752c2224480302d2b720 | SQL：如何找到表中不同 name 的个数？ | sql, distinct | 八股文_Concept |
| 58c36e365222a9b2f4b0e5a9f22cb32e | Varchar 和 Char | char, varchar, 变长字段, 空间利用率 | 八股文_Concept |
| bf14946ff66cf12b4e9dd768900e602a | varchar和char的区别 | varchar, char | 八股文_Concept |
| 6d5ede3072359eecb39a4dafae8a2395 | X 类型锁是什么? | exclusive lock | 八股文_Concept |

## L2_Mechanism (331 道题目)

| Question ID | 题目 | 相关技术点 (Entities) | 题型 (Type) |
|---|---|---|---|
| b4868fc5266cc5dab4120cea35852a7b | [快手]Inno DB 如何解决幻读? | 幻读, mvcc, next-key lock | 原理深度_UnderTheHood |
| 5d974ce649f1bcf4e0fc48e1e8e332f4 | 不停机大规模数据迁移：如何将生产环境下 16 张大表平滑迁移并扩容至 64 张表？详述双写校对与切流后的回滚预案？ | 分库分表, 数据迁移, 双写 | 场景设计_Scenario |
| 7ed052e82f4153cb66c3901f6244520b | 查询语句使用 OFFSET + LIMIT 为什么会变慢？如何进行优化？ | mysql, 延迟关联 | 原理深度_UnderTheHood |
| c7529574cf0984d563c1728a43a75d95 | 场景：快照读与当前读如何避免幻读？ | snapshot read, current read, next-key lock | 原理深度_UnderTheHood |
| f16acd9e5dd7b6b75ecf14fca38c7c5c | 场景设计：数据量 1000 万的分页查询设计，每次查 20 条数据，如何优化深分页 SQL？ | 深分页优化, 自增id优化 | 系统设计_Architecture |
| 3d9be4af910499a32adcac6d76d02d9b | 场景题：请使用乐观锁方案实现一个高并发下的 PV（页面访问量）统计功能 | cas sql | 场景设计_Scenario |
| 7204e1434001de7a4d3c6fb7608e7eac | 场景题：在一个包含 id 和 name 列的表中，幻读是如何发生的？ | 幻读 | 场景设计_Scenario |
| 9d52d6f14e6042c3771eda258d8e137f | 除了索引优化，减少数据传输量具体可以怎么实现？ | mysql | 原理深度_UnderTheHood |
| f2fcf221450d24da0ee3734ba3aedf1e | 串行化解决了什么问题? 为什么不作为默认隔离级别? | 串行化, 幻读, 性能 | 原理深度_UnderTheHood |
| 7dd93769f810f2b392dfc8b144a92f3f | 存储引擎：辨析聚簇索引（Clustered Index）与非聚簇索引的物理存储结构区别？ | clustered index, non-clustered index | 原理深度_UnderTheHood |
| 23592b65ba16dec9aedda3e5e8abe3a9 | 存储引擎对比：MySQL (B+ Tree) 与 MongoDB 的核心优势架构对比，各自的适用业务场景？ | mysql, mongodb, b+树 | 八股文_Concept |
| af8b28f253c69a136fce907726c9983e | 存储原理：MySQL 索引的叶子节点具体存储在内存还是磁盘的什么位置？Buffer Pool 的作用是什么？ | buffer pool, disk storage | 原理深度_UnderTheHood |
| 0fe43b40362287d96d454a9d582e13da | 大数据量分页优化：如何利用“延迟关联”或“书签分页”技术优化“查询第 10000 页回答”的 deep paging 慢查询？ | 分页优化, 延迟关联 | 方案设计_Scenario |
| a0af948c2055306cc23da5fa5a91bf3d | 代码阅读题 2 (SQL 优化)：对比两条 SQL 语句的执行效率。其中一条完全命中索引，另一条由于未覆盖索引导致“回表”查询，请解释其性能差异 | 回表, 覆盖索引 | 原理深度_UnderTheHood |
| 9d0a2c20f02aebc2004de9f301754dc9 | 当 MySQL 表数据量达到百万/千万级时，为提高查询效率会采取哪些具体的索引优化手段？ | 索引优化, 大表查询 | 集成对接_Integration |
| f82a84371950e328feb26d57738520b6 | 当前读（Locking Read）涉及哪些锁，不同 SQL 的锁分析？ | locking read, select for update | 原理深度_UnderTheHood |
| 99f0328ea89191698bc1db3386b735dc | 当前读与快照读的区别? RC和RR级别的快照生成时机? | 当前读, 快照读, mvcc, readview | 原理深度_UnderTheHood |
| a742d60fa8a5ce265c6743df18ee3956 | 读写分离（Read-Write Splitting）的实现方式及其导致的数据一致性（延迟）问题处理？ | read-write splitting, slave lag | 场景设计_Scenario |
| 437aec2d436fde0c9bcdb1a8b78476d6 | 读已提交 (RC) and 可重复读 (RR) 如何利用 MVCC 实现？ | rc, rr, readview | 原理深度_UnderTheHood |
| a8b2d61d63349245f25d60b4b7988126 | 多表关联查询性能优化：知乎核心“用户-回答-评论”关联查询频繁时，应采取何种索引设计或数据模型反规范化策略？ | 关联查询, 反规范化 | 方案设计_Scenario |
| e4e115dbf090f49c7d85e76694d8d60f | 非聚簇索引的回表机制是什么？ | 回表, 非聚簇索引 | 原理深度_UnderTheHood |
| 0f1bbebc4cffba5586797af75cacb65c | 非聚簇索引中的字段只存储了主键值吗? | index covering | 原理深度_UnderTheHood |
| 05663892466ff3509a0c91b6bfe64337f0 | 分布式 ID 与自增：MySQL 中 auto_increment 锁的模式及在高并发写入下的瓶颈？ | auto_increment, lock mode, distributed id | 原理深度_UnderTheHood |
| 018ff45fd77ecd2171f79a4e513a0205 | 分库分表：如何设计一个水平分库分表的方案？ | 分库分表 | 场景设计_Scenario |
| 7c97c921933ee64af188c86f181ff7ed | 分库分表后的全局统计挑战：如何实现跨 user_id 分片后的“全站热帖 TOP 100”查询流程？ | 分库分表, sharding | 场景设计_Scenario |
| db3260c4ec322f388a78bd2819e6594d | 分片键怎么选？ | 分库分表 | 场景设计_Scenario |
| 050f173ff4ec253580b6cbe5b2319c28 | 分页查询时，如果数据量特别大，如何避免性能问题？ | 分页 | 原理深度_UnderTheHood |
| 874cfba539c749b5ec74a1b3542fe7ee | 隔离级别深度演进：RR 与 RC 模式下 MVCC 实现的具体差异？ | 隔离级别, rc, rr | 原理深度_UnderTheHood |
| 34e73e2c6cc110dae5377b6e564c2338 | 回表查询原理解析 | index lookup, bookmark lookup | 原理深度_UnderTheHood |
| 5a663e78db72f59e4172cbba7a3dbfa3 | 基础设施：数据库版本是多少？为什么选择“可重复读”（Repeatable Read）作为默认的事务隔离级别？Redis 采用的是几主几从的部署架构？ | repeatable read, redis replication | 原理深度_UnderTheHood |
| 3b69227c3deb8ae323eb9817da6fd9b9 | 技术对比：B+ 树结构相比 B 树有哪些优点？相比平衡二叉树、跳表又有何优劣？ | b+树, b树, skiplist | 原理深度_UnderTheHood |
| cdcf3ef94acae19a4e9d3ef98f7995f4 | 建表为什么用自增主键？为什么不用uuid？ | 自增主键, uuid, 聚簇索引, b+树 | 原理深度_UnderTheHood |
| 464fd36061bd88356ef47f96897e313e | 介绍一下 MySQL 的 MVCC 机制，它主要是用来解决什么问题的？ | mvcc, readview, 版本链 | 原理深度_UnderTheHood |
| 98db7d3580e9f3ac93d09c39a89c0c91 | 金融级敏感数据存储加密：针对客户姓名、身份证号、银行卡号等敏感信息，如何在数据库层面实现加解密（如 AES-256）与脱敏策略？ | aes加密, 数据脱敏 | 原理深度_UnderTheHood |
| dfcae329fa4d779718b5e8c17c131275 | 金融历史交易记录冷热分离：针对 5 年以上历史记录查询慢的问题，如何设计基于时间维度的分库分表与 Elasticsearch/HBase 归档方案？ | 冷热分离, elasticsearch, 分库分表 | 架构设计_Architecture |
| d48067fdc962fdc64a30c41e13cd6e91 | 聚簇索引（Clustered Index）的适用场景有哪些？什么是页分裂（Page Splitting）问题？ | 聚集索引, 页分裂 | 原理深度_UnderTheHood |
| 81fef79879611cad4ff672037489e921 | 聚簇索引使用场景及页分裂问题 | 聚簇索引, 页分裂 | 原理深度_UnderTheHood |
| f0e655d27a40970e8f3ee4bf8fe7ecd8 | 可重复读级别是怎么实现的（MVCC）？ | mvcc, read view, undo log | 原理深度_UnderTheHood |
| 2e3408593695b7bfb5e27d367cab7978 | 可重复读解决了哪些问题 | 可重复读, 幻读 | 原理深度_UnderTheHood |
| 718fbcad3bdbb2ff48ffb9e8855ab4b7 | 快照读和当前读 | mvcc, 快照读, 当前读, readview, undo log | 原理深度_UnderTheHood |
| bca343fd50fffc2430ea51aeaf64bc99 | 乐观锁与悲观锁在数据库层面上分别是如何实现的？ | 乐观锁, 悲观锁 | 原理深度_UnderTheHood |
| 0ebedf1c9a85dc7ca7e399c567261f7a | 了解过 b 树与 b+ 树的区别吗？为什么 b+ 树需要这么做？ | b-tree, b+树, 索引 | 原理深度_UnderTheHood |
| 5e34a7b49e5a3ef783a93f6302e22ae3 | 联合索引：对于联合索引 `(A, B, C)`，执行 `WHERE B=1 AND A=2 AND C=3` 时，索引是否生效？请解释 MySQL 查询优化器（Optimizer）在此时的作用 | composite index, query optimizer | 原理深度_UnderTheHood |
| c27c02b7909ab4b8d30d0ada53a98dde | 联合索引：给定联合索引 `(a, b, c)`，执行查询 `WHERE a=1 AND b>2 AND c=3` 时，能用到哪些索引字段？请结合“最左前缀法则”详述索引失效的边界点 | composite index, leftmost prefix rule | 八股文_Concept |
| 5055fe3426ee7ea5296d2862d28cce0f | 联合索引：在创建联合索引时需要注意哪些事项（如最左匹配原则、区分度等）？ | 联合索引 | 原理深度_UnderTheHood |
| 718a85250bc198a0c2003b308ead8f00 | 联合索引(a, b, c)，where b = 1能否走索引？where a = 1呢？ | 联合索引, 最左前缀原则 | 场景设计_Scenario |
| 56adbbb36be7cd66dd1547a3a7a31de5 | 联合索引查询时的 B+ 树与单索引查询时的 B+ 树有什么区别？ | b+树, 联合索引排序, 组合键大小比较 | 原理深度_UnderTheHood |
| 35744f433d5d58e3671f4cdcfd106a5a | 联合索引失效场景：如 a, b 有索引，c 没有，查询条件 where c=xx and a=xx and b=xx 能否用索引？ | 联合索引, 索引失效, 最左匹配原则 | 原理深度_UnderTheHood |
| 59e32d5f7dc9a6467fdfbfc6575c21de | 联合索引原理及索引失效场景 | 联合索引, 索引失效, 最左前缀法则 | 原理深度_UnderTheHood |
| 6ce3cc34ae700a3748f30ddc1e520fb5 | 慢查询排查：如何进行EXPLAIN分析、优化索引或重构SQL？ | mysql | 原理深度_UnderTheHood |
| 74a426bad6df2e42e9a93c107d3661d8 | 面对高并发写请求，如何评估并缓解数据库（DB）的写压力？ | write pressure, batch insert, async commit | 场景设计_Scenario |
| 3d9b17939cd32bda412ed1b8b3ac165d | 模糊查询中 % 的位置对索引的影响？ | 模糊查询, like, 索引失效 | 原理深度_UnderTheHood |
| 9d903cc9959cf7b20160899faf9456e8 | 哪些情况下索引会失效？除了增加索引，还有哪些优化查询的方法？ | 索引失效, 查询优化 | 八股文_Concept |
| fca80995f22f33b20a46da81cb8f0d53 | 那怎么解决幻读呢？ | mysql, 幻读, mvcc, 间隙锁 | 原理深度_UnderTheHood |
| 526b1e141ba6d0c55b33275078cd7adf | 评论系统性能优化：在大数据量场景下，评论楼层展示如何避免 SELECT COUNT(*) 导致的性能下降？ | select count, 性能优化 | 场景设计_Scenario |
| d616ff7e2ef391e07c984e8bd0a965a6 | 请编写 SQL：给定订单表 order（字段：orderId, userId, time），查出所有用户各自最新的一个订单信息。 | sql, group by, 窗口函数 | 算法手撕_Coding |
| c718a89ccd545717a3b72ca0666e2d85 | 请根据具体业务例子说明如何合理创建索引 | 索引优化 | 原理深度_UnderTheHood |
| c1454f882f3a780faeb76c1f90b56426 | 请简述 MySQL 主从复制的原理。 | binlog, relay log | 原理深度_UnderTheHood |
| 792e0375e1affc4e877378839f72fc49 | 请解释 MySQL 事务的 ACID 特性。如果系统在事务执行期间意外宕机，MySQL 如何通过 redo log 与 binlog 的一致性检查来决定是否需要回滚事务？ | xa事务, 崩溃恢复 | 原理深度_UnderTheHood |
| 7e85f4769e696d2d397fdd8abc409459 | 请介绍 MySQL 的四大日志（binlog, undolog, redolog, relaylog）及其作用，并说明日志与事务 ACID 特性的关系 | logs, acid, redo log, undo log | 原理深度_UnderTheHood |
| 0f6fbe199c7933cd326ec90e75c3071a | 请介绍 MySQL 索引及其底层数据结构。对于“性别”这种区分度较低的字段，是否适合建立索引？为什么？ | 索引区分度, b+树 | 原理深度_UnderTheHood |
| d84c9f5803b76295b65b4e09f94fdbb0 | 请描述 MySQL 事务的四大特性（ACID），以及数据库是如何通过底层机制（如 redo/undo log, MVCC）来保证这些特性的？ | acid, mvcc, redo log, undo log | 原理深度_UnderTheHood |
| d43be1ed7d5b2d1a79962d67c6ab6949 | 请描述一条 MySQL SELECT 语句的完整执行流程 | 执行引擎, 查询优化器 | 原理深度_UnderTheHood |
| f7d62b60105e3e906f700fb121c6fc09 | 请说明联合索引（复合索引）失效的具体情况及其背后的逻辑 | index failure, composite index | 原理深度_UnderTheHood |
| 536e924f933e99a2b6c83ac988df61e5 | 请谈谈你对数据库索引及事务机制的理解。MySQL 是如何实现事务隔离级别的？ | 索引, mvcc | 原理深度_UnderTheHood |
| d21290863e9b8ac8cb5882ea09348621 | 请详细解释 MySQL 中的 MVCC（多版本并发控制）实现机制 | mvcc, read view | 原理深度_UnderTheHood |
| d65aae7a4a6f23bc05384ef83865a98c | 请详细介绍 MySQL 里的索引，包括分类以及为什么选用 B+Tree 作为存储结构？ | b+树, 聚集索引, 非聚集索引 | 原理深度_UnderTheHood |
| 4685d4147430b4a5de734be01ebb757f | 如果没有指定主键，InnoDB 会如何处理？是否会创建默认主键？ | innodb, 聚簇索引, rowid | 原理深度_UnderTheHood |
| ee4e84fc3cf4a9e70961ad974d573aef | 如果字段类型是数字，但在查询条件中将其与字符串进行比较，这种情况下会走索引吗？为什么？ | 隐式类型转换, sarg | 原理深度_UnderTheHood |
| 8761de069c8739ad832d79780affc372 | 如何保证 MySQL 主库和从库之间的“强一致性”？ | 半同步复制, 全同步复制 | 原理深度_UnderTheHood |
| 33701de261a601a75bfb92aa304e3149 | 如何搭建 MySQL 的主从集群？请详细解释异步复制和半同步复制的区别 | mysql复制, 异步复制, 半同步复制 | 原理深度_UnderTheHood |
| 7e3181f7eb257e62ea4e3bd35fda6819 | 如何解决幻读问题？ | mysql, 间隙锁, mvcc | 原理深度_UnderTheHood |
| bcd16b7292e1edbc3fd8d12d79212e99 | 如何设计存储海量聊天数据的数据库表结构？请给出具体的索引优化策略？ | sharding, chat log table, composite index | 场景设计_Scenario |
| acd4d6fcc113ec35b7715944a520e532 | 如何通过 SQL 加锁来解决幻读问题？你所加的是什么锁（如 Gap Lock / Next-Key Lock）？ | 间隙锁, 临键锁 | 原理深度_UnderTheHood |
| fbd04c3271f5812ea85b0eca2cd3008e | 如何通过监听 Binlog 的方式保证数据一致性？ | canal, binlog | 原理深度_UnderTheHood |
| bb2633a9d0c369fb86b39057ac4bc284 | 三种日志的区别、WAL技术 | binlog, redo log, undo log, wal先行写日志, 原子性及两阶段提交 | 原理深度_UnderTheHood |
| 475e8e4f60ae768a7fbe9ab28d8233a1 | 什么是 MySQL 的深度分页问题？如何解决？ | mysql, 深度分页 | 原理深度_UnderTheHood |
| ae2661b8fc78cfe35ef88b43e01855d2 | 什么是覆盖索引？请举例说明索引失效的场景以及回表查询的原理。 | 覆盖索引, 索引失效, 回表查询 | 原理深度_UnderTheHood |
| 1fea800261c56b98d48685eec58f3416 | 什么是联合索引？如果建立了 BCD 联合索引，按 BD 查询和按 CD 查询有什么区别？ | 联合索引, 最左匹配原则 | 原理深度_UnderTheHood |
| c6377dc8d4b7cc37e42a57737c2215ef | 什么是索引下推 (Index Condition Pushdown)？ | 索引下推, icp | 原理深度_UnderTheHood |
| c5d026ddf733c0e1b11434bb47ed8ce3 | 什么是跳表? 为何 MySQL 不使用跳表? | skip list, b+ tree contrast | 原理深度_UnderTheHood |
| fb83cb2f7baa34ca698dcf81a332bd3e | 生产环境零停机数据扩容迁移：详述在不停机情况下将 16 张核心表扩容至 128 张表的完整迁移路径（双写、同步、灰度采样、平滑切流）？ | 数据库迁移, 双写 | 场景设计_Scenario |
| 571d135342fed6ee4cb4734e360d673c | 实践中如何优化MySQL? | mysql调优 | 原理深度_UnderTheHood |
| 4f3e52240abf45c5e9e4a5f4fc342478 | 事务的 ACID 特性及其在 InnoDB 中的底层实现原理（Undo/Redo Log, MVCC, Locks）？ | acid, undo log, redo log, mvcc | 原理深度_UnderTheHood |
| 5f341c163fed278ce15f707063d2b4ac | 事务的四大特性 (ACID) 是什么？数据库系统是如何支持这些特性的？ | acid, redo log, undo log | 原理深度_UnderTheHood |
| 81251a5fe08e7569280f0b5c7dad8a75 | 事务隔离：简述数据库的隔离级别。可重复读（RR）级别是如何实现的？MVCC 能否彻底解决幻读问题？ | mvcc, rr | 原理深度_UnderTheHood |
| b71c996529e332e375c163a54087e8f3 | 事务隔离：请详述 InnoDB 的 MVCC（多版本并发控制）实现原理。它是如何解决不可重复读与幻读问题的？ | mvcc, read view, undo log, repeatable read | 原理深度_UnderTheHood |
| b68b78f893aa0e6bbbea719ce55f32b7 | 事务隔离：事务的各隔离级别（RU, RC, RR, Serializable）分别解决了哪些并发问题？在“可重复读”（RR）级别下，InnoDB 是如何解决“幻读”问题的？ | next-key lock, gap lock, phantom read | 原理深度_UnderTheHood |
| bd8803a1d328e36f695e2f7ed723e94c | 事务隔离级别，如何避免幻读？ | 事务隔离级别, 幻读, 间隙锁, next-key lock, mvcc | 原理深度_UnderTheHood |
| 5f4935a4e3ea6905f4fcb01dd73e1e94 | 事务选择 | 事务隔离级别, acid | 场景设计_Scenario |
| fae39ac4f02ec839def13939880212b2 | 事务与并发：MySQL 的 MVCC（多版本并发控制）和两阶段提交（2PC）是如何实现的？ | mvcc, 2pc | 原理深度_UnderTheHood |
| c874e7ccaa30dc2fb0dcd08b5bd69b52 | 事务原理：什么是 ACID 特性？InnoDB 引擎分别是通过哪些机制（如 Redo Log, Undo Log, MVCC, Next-Key Lock）保证这些特性的？ | acid, mvcc, redo log, undo log | 原理深度_UnderTheHood |
| 482dae766c5457cd9046e3cefb3502a3 | 数据表结构设计有哪些核心要点？在什么情况下会考虑分表策略？ | 分表, 范式设计 | 原理深度_UnderTheHood |
| f8772b4c6e4be40c0839cda6f44e7bbb | 数据建模：在你的项目中，数据库表设计时主要选用了哪些数据类型（如 JSON, Decimal, DateTime）？选用依据及对索引性能的影响是什么？ | mysql data types, json storage, indexing performance | 场景设计_Scenario |
| ce7d35a868fb5bd7b60de402ec015a54 | 数据库：基于 B+ 树的索引存储原理：以“创建时间”字段索引为例描述存储结构 | compound index, non-clustered index | 原理深度_UnderTheHood |
| eaf825db44ef16c9fe652237862bf9da | 数据库：如何编写复杂 SQL 实现数据统计？（考察点：聚合函数、JOIN 操作、窗口函数初探）。 | sql | 算法手撕_Coding |
| 8481f4c1f8ab4b013ef504a9fb7f2855 | 数据库：在 MySQL 调优中，如何根据 `EXPLAIN` 命令的输出结果判断某个索引是否生效？请列举至少三个常见的索引失效场景。 | explain, 索引失效 | 原理深度_UnderTheHood |
| e46517d4bca32b2d83f0392c6701e9ec | 数据库：在 MySQL 联合索引中，为什么“最左前缀原则”如此重要？如果查询条件跳过了联合索引的第一个字段，索引还能发挥作用吗？ | 最左前缀 | 原理深度_UnderTheHood |
| f4f8ed53665414bb28f98bfc7bae25e4 | 数据库：在 MySQL 优化中，创建索引通常需要遵循哪些核心原则（如离散度高、覆盖索引、避免过度索引）？请列举至少两个典型的索引失效场景。 | 索引优化 | 原理深度_UnderTheHood |
| a4a18d302102605e001932053b96b6bb | 数据库：在 MySQL 中，哪些情况下会导致索引失效？请描述 B+ 树索引的物理存储结构。 | b+树, 最左前缀 | 原理深度_UnderTheHood |
| 6b04e6d7c8128c41626b923b5c4fe372 | 数据库：在 MySQL 中构建联合索引时，需要遵循什么原则（如最左前缀法则、离散度大的列在前、覆盖索引）？ | 联合索引 | 原理深度_UnderTheHood |
| 6ace11d31c667e36d5a2730a40db4b33 | 数据库：在 SQL 优化中，`EXISTS` 和 `IN` 子句哪个效率更高？请结合驱动表、索引命中及底层执行计划进行分析。 | exists, in, 执行计划 | 原理深度_UnderTheHood |
| 036c72c279bb049b5743201f1bf55aee | 数据库：在技术选型时，如何评估 MySQL 与 PostgreSQL 的差异？为什么在某些高并发场景下会考虑使用 Elasticsearch (ES) 而非关系型数据库？ | postgresql, es | 经验思考_Reflection |
| c965894cd9100118a5f6df2cfeac4814 | 数据库：在什么情况下不建议为字段建立索引？请结合数据区分度、更新频率及表规模进行分析。 | 索引设计 | 经验思考_Reflection |
| b120167f4de6c509c15275d22f9dee68 | 数据库：MySQL 的 InnoDB 存储引擎与 MyISAM 的索引结构有何本质区别？ | innodb, myisam, 聚簇索引 | 原理深度_UnderTheHood |
| a26172ebb6cae0984f8bd664dcedf36d | 数据库：MySQL 的隔离级别有哪些？请详细描述 MVCC（多版本并发控制）的实现原理及其解决的问题。 | mvcc | 原理深度_UnderTheHood |
| 825dc259f74906104ff39462110008e7 | 数据库：MySQL 联合索引的“最左匹配原则”及 B+ 树多列索引的存储结构 | composite index | 原理深度_UnderTheHood |
| 7627f9b1fb0ef7d3e870c536fd387d2c | 数据库：MySQL 索引的底层实现 (B+ Tree)；为什么 B+ 树在大规模磁盘存储中优于 B 树？ | b+树 | 原理深度_UnderTheHood |
| f94aef2b8357e056d88060d98294a864 | 数据库：MySQL 索引的底层原理是什么？索引有哪些优缺点？ | b+树, 索引 | 原理深度_UnderTheHood |
| 2c6ff8825aa538c579fce47679629a24 | 数据库：MySQL 索引体系详解：主键索引 (Clustered Index) 与 非主键索引 (Secondary Index) 的存储差异 | clustered index | 原理深度_UnderTheHood |
| 0d366b9dd655d2d04a07ff374febff36 | 数据库：MySQL 中 B+ 树的层高通常受哪些因素（如 Page 大小、Key 长度、数据行大小）影响？如何根据层高估算表的数据容量上限？ | b+树, page | 原理深度_UnderTheHood |
| 2121c5d182d2db5e47abb0b703f6f2d1 | 数据库：MySQL 中常见的索引失效场景有哪些（如隐式类型转换、最左匹配失败、函数操作）？请口述如何创建一个全文索引并描述其应用场景。 | 全文索引 | 原理深度_UnderTheHood |
| d56c4005d3279f544864ce069ff691a1 | 数据库：MySQL 中聚集索引 (Clustered Index) 和非聚集索引的区别是什么？ | clustered index, 二级索引 | 原理深度_UnderTheHood |
| 6da5d611b6b64b85786444bb0896bb4e | 数据库：MySQL 主从同步 (Replication) 的底层原理与 Binlog 的解析交互过程 | mysql replication | 原理深度_UnderTheHood |
| 42936bc3b2155cce4a1dd891dc295996 | 数据库：MySQL Binlog 的作用及应用场景 (如主从复制、数据恢复)；Binlog 在事务提交时的写入时机分析 | binlog | 原理深度_UnderTheHood |
| 5ad0ac275b2ef5028bf893e590bb6b8f | 数据库：SQL 中 join on 与 where 条件过滤的执行顺序差异分析 | sql execution order | 原理深度_UnderTheHood |
| df3c42d5cb2e7c8a2027ed0cf6bec803 | 数据库：WHERE 过滤行与 HAVING 过滤组的底层执行顺序差异及对索引的影响 | sql execution order | 原理深度_UnderTheHood |
| 0b9b60076cdb9dfadf7c8aba85681f0d | 数据库的唯一索引是用哪些数据结构实现的 | 唯一索引, b+树, 哈希索引 | 原理深度_UnderTheHood |
| 50b794b31c44ff840c817dc19b261f67 | 数据库分库分表（ShardingSphere）在高频交易场景下的具体落地？ | shardingsphere, database sharding | 场景设计_Scenario |
| e91622a9ed34ea4c5ed7ef6410aa3d9f | 数据库恢复策略 (WAL, redo log, undo log) 详解 | wal, redo log, undo log | 原理深度_UnderTheHood |
| ea050bbc1973897e0b3b67bd7178d4a3 | 数据库架构：实习公司的数据库是如何部署的？请详细说明 MySQL 一主多从架构下是如何保证数据一致性的。 | mysql, 主从复制 | 原理深度_UnderTheHood |
| 893c4a80cb9c52bcff1eac9540755bef | 数据库进阶：什么是存储过程？在现代高并发互联网架构中，为什么通常不建议使用存储过程？ | 存储过程 | 架构设计_Architecture |
| f2b7498ac46d2124ebf3efe4c8a49161a | 数据库进阶：在实战中应对单表亿级数据时，你的分库分表拆分维度、中间件选型及扩容迁移方案如何？ | sharding, data migration, mycat | 场景设计_Scenario |
| f2b7498ac46d2124ebf3efe4c8a49161 | 数据库进阶：在实战中应对单表亿级数据时，你的分库分表拆分维度、中间件选型及扩容迁移方案如何？ | sharding-jdbc, data migration, horizontal sharding | 场景设计_Scenario |
| 1f446e1f7ad64734ac0e0cc8d9c90372 | 数据库连接池选型：京东商品服务为何从Druid切换到HikariCP？参数如何优化？ | 连接池, druid, hikaricp | 原理深度_UnderTheHood |
| f55afee0d909017912246cdf724c7af2 | 数据库设计：UUID 适合做数据库的主键吗？请从 B+ 树索引的分裂开销、存储效率与聚簇索引特性角度进行分析 | uuid, b+ tree fragmentation, clustered index | 原理深度_UnderTheHood |
| b5569252be5c4322679809ea3f1f44da | 数据库深度：MySQL RR 隔离级别下，MVCC（一致性读）结合 Next-Key Lock 解决幻读的具体推导过程？ | mvcc, next-key lock, phantom read | 原理深度_UnderTheHood |
| 2d3e4b9440ed409287f1f3952b2db412 | 数据库实践：在你的项目中，核心业务表的索引是如何设计的？ | mysql, 索引设计 | 项目深挖_Project |
| b43bb9cf330a7be0815e9df983d7cdb6 | 数据库事务：请详述 MySQL 的四种事务隔离级别。InnoDB 引擎中的 MVCC（多版本并发控制）机制是如何利用 Undo Log 和 Read View 实现快照读的？ | mvcc, undo log, readview | 原理深度_UnderTheHood |
| de93dcaac83d862df12ce5e02206faa9 | 数据库事务的持久性（Durability）是怎么实现的？ | redo log, 持久性 | 原理深度_UnderTheHood |
| d40fda49e8f8590edfe401f7abccd89e | 数据库事务的原子性（Atomicity）是怎么实现的？ | undo log, 原子性 | 原理深度_UnderTheHood |
| fbccfd1d1660573285447e55b22bb70d | 数据库索引：给定复合索引（A, B），分析在不同查询条件下索引的生效情况（最左匹配原则）。 | 复合索引, 最左匹配 | 原理深度_UnderTheHood |
| aa69912ea627693317a1f446347e999d | 数据库索引：在联合索引场景下，如果前缀字段使用了范围查询（Range Query），后续字段的“最左匹配原则（Leftmost Prefix Rule）”会发生什么变化？ | composite index, range query invalidation | 原理深度_UnderTheHood |
| 70b24b28d551a431918bd98381a5fe62 | 数据库索引：MySQL 索引的底层数据结构是什么？在什么特定业务场景下会考虑使用哈希索引（Hash Index）而非 B+ Tree？ | b+树, hash index physics, search complexity | 原理深度_UnderTheHood |
| 5603c0824633b809d36ac8c7dda217e9 | 数据库索引：MySQL 索引为什么采用 B+ 树？请解释最左匹配原则与回表查询的概念 | b+树, index lookback | 原理深度_UnderTheHood |
| d0855f06f52cde11183138aeb03ce4ae | 数据库索引的底层实现原理和优化 | b+树, 索引 | 原理深度_UnderTheHood |
| bfd3cf7ce93e1380c6b36bf9819fe0fe | 数据库索引的底层原理（B+树） | b+树, 索引, 聚簇索引, 非聚簇索引, 页分裂 | 原理深度_UnderTheHood |
| d05eaeb747d4bc2ff950f7ece71b5f90 | 数据库索引在更新、新增场景下是否会被使用？详述聚集索引与非聚集索引的差异？ | 索引, 聚集索引 | 原理深度_UnderTheHood |
| d6893dadab4e4e554f5354eb8d78be30 | 数据库性能：JOIN 查询中“小表驱动大表”的理论依据与执行优化？ | nested loop join | 原理深度_UnderTheHood |
| bd86dd9434f4b91c282e362b78f52322 | 数据库一致性：MySQL 如何通过三色日志（Binlog, Redo, Undo）协作保证事务的 ACID 特性？ | binlog, redo log, undo log, acid | 原理深度_UnderTheHood |
| 35a804a5fc431326707e025b140f54f4 | 数据库灾备优化：在高并发环境下，如果主库发生故障，如何设计快速切换与数据零丢失方案？ | replication, failover, mha, orchestrator | 场景设计_Scenario |
| 0e33b1e485e577e111fdd1e08ec51516 | 数据同步：Canal 的工作原理及其如何保证主从/异构数据库间的数据一致性？ | canal, 数据同步 | 原理深度_UnderTheHood |
| 214478b4a79f55b2d6fa9639a469d790 | 说一下 MySQL 的日志 (binlog, redo log, undo log) | mysql日志 | 原理深度_UnderTheHood |
| 26cf490d9490e9cd7962dbe074fdc06d | 算法：手撕实现特定的复杂 SQL 查询场景 (业务多表关联与聚合) | sql coding | 算法手撕_Coding |
| 5336c41901e26a779102034dac98230c | 索引的底层实现原理和优化 | b+树, 聚簇索引, 覆盖索引, 索引下推 | 原理深度_UnderTheHood |
| d653f8729d857358cca5b475626b8fdd | 索引的结构是什么？B+ 树结构的叶子节点和非叶子节点有什么区别？B+ 树最底层是双向链表有什么好处？ | b+树原理结构, 内节点只存键值不存数据, 叶子节点存数据与主键, 底层双向链表范围扫描优化 | 原理深度_UnderTheHood |
| 9886712df419d8fe4903fd2f06a94a5b | 索引的B+树底层结构是怎样的？ | b+树, 索引结构 | 八股文_Concept |
| 61a6881678ba20350a80a5bbb42606d8 | 索引及其数据结构，说说最左前缀匹配 | b+树, 索引, 最左前缀匹配, 联合索引 | 原理深度_UnderTheHood |
| 7da5bc00a55b030b16ace39457ca791c | 索引设计：如何根据业务场景创建正确且高效的索引？请从数据量庞大对插入/更新性能影响的角度进行分析 | indexing strategy | 原理深度_UnderTheHood |
| a6838e8268806ba5daccbd9fe3fb06bc | 索引实践：在实际业务中你会如何建立索引？有哪些具体的考量因素？ | mysql, 索引 | 工具使用_Tooling |
| 58d36de27ff0e41f3515ab790995fc88 | 索引下推？ | 索引下推, icp, innodb | 八股文_Concept |
| 49a57cbea9e7b91a47ddf87adf31d9a8 | 索引优化详细讲讲 | 索引优化, explain, 覆盖索引, 最左前缀法则 | 原理深度_UnderTheHood |
| c2edf64eff70c7e45dc232995653976d | 索引在什么情况下会失效？对索引做计算或使用函数会导致失效，如何理解？能举例说明吗？如果使用 LENGTH 函数构造 SQL，如何导致索引失效？ | 索引失效条件原因, 全表扫描触发, 索引列上运算函数使b+tree失效破坏有序性, length(str)陷阱 | 原理深度_UnderTheHood |
| 99f34437eae306a767f24acab541b35c | 谈谈你对 MySQL 性能调优的理解和具体做法。 | mysql | 原理深度_UnderTheHood |
| 5fc897cdc6b911e7f1abdac760a464a5 | 网络安全：什么是 SQL 注入？其底层注入漏洞原理是什么？如何通过预编译（PreparedStatement）从根本上防范？ | sql注入, preparedstatement | 八股文_Concept |
| 2309a1810d94bbc74f8f9012f19b0883 | 为啥不用 Hash 索引?Hash 索引查找的时候是不是更快吗? | hash 索引, b+树 | 原理深度_UnderTheHood |
| 1d58b0eac6f2a671b1cfebb76d9a4380 | 为什么 MySQL 表删除了一堆数据,但是文件大小不变? | 数据空洞, 物理删除, 碎片 | 原理深度_UnderTheHood |
| 0d2eb971ad3c4cb0faec6dfbf026a178 | 为什么 MySQL 选择 B+ 树作为索引结构？相较于红黑树或 N 叉平衡树，它在 I/O 层面有哪些核心优势？ | b+树, 磁盘io | 架构设计_Architecture |
| 3da9ee459ea49eecd3d63c336992f182 | 为什么不用B树？B+树会带来什么可能的隐患？ | b+树, b树, mysql | 原理深度_UnderTheHood |
| 93f66f286d503ec29e68b90015f88ff1 | 为什么单表达到2000万就有查询性能问题 | mysql, b+树层级, 索引页缓存, 磁盘io, 2000万瓶颈 | 原理深度_UnderTheHood |
| b5b7c5d338e072df6295e6ca462d55e2 | 为什么高并发下数据写入不推荐关系数据库？ | rdbms, nosql, 由于b+树分裂导致的写入性能 | 原理深度_UnderTheHood |
| 11ac5a05fbfffe51e8f506c49d066d1e | 为什么加索引可以加快扫描范围？ | 索引, b+树, 磁盘io | 原理深度_UnderTheHood |
| 5e701f7fc649cf04f1def8754f40e228 | 为什么索引会加快查询 | 索引原理, 磁盘io, b+树 | 原理深度_UnderTheHood |
| e5dff97595a87d3f47929d4914af92ee | 线上 SQL 优化经验：MySQL 索引选择器（Optimizer）的工作机制及如何强制指定索引？ | mysql优化, force index | 原理深度_UnderTheHood |
| 20533a04b1cfcc5c718f837622cb6354 | 详细解析 MySQL binlog 的工作模式（Statement, Row, Mixed）及其在主从复制中的具体流程？ | binlog mode, replication, relay log | 原理深度_UnderTheHood |
| 20533a04b1cfcc5c718f837622cb6354 | 详细解析 MySQL binlog 的工作模式（Statement, Row, Mixed）及其在主从复制中的具体流程？ | binlog, mysql replication | 原理深度_UnderTheHood |
| b4e27b44f5a471f242d5be9a3009527f | 详细介绍 MySQL 的 ACID 特性、隔离级别、并发问题以及 MVCC 机制 | acid, mvcc | 八股文_Concept |
| 00d86b5c44fff1969a0723ce0b4dd90a | 性能优化：在实际使用中，MySQL 的 B+ 树索引有哪些可以优化的点？ | mysql优化 | 原理深度_UnderTheHood |
| 639e1f3ddd6868f3507aca54566f3d09 | 一个表有索引说说它的查询过程？ | 索引查找, 回表 | 原理深度_UnderTheHood |
| 567e4109adb4c310e430b3eb5a84a047 | 一颗b+树能存储多少数据 | b+树容量, 页大小 | 原理深度_UnderTheHood |
| 5237ddf5e9317a225210bdc9796967c5 | 以 (a,b,c) 为例,在什么情况下,单查 b 也能命中联合索引? | 联合索引, 最左前缀原则, 索引覆盖 | 原理深度_UnderTheHood |
| 071a5a8649ff9a82a8f05a92253d2ef9 | 有 abc 复合索引, a=1 and b=1 走不走索引? a=1 and c=1 呢? | 复合索引, 最左匹配原则 | 八股文_Concept |
| 8d991a66514bf184f053d0ca77cf7f58 | 有什么策略能避免幻读？ | mysql, mvcc, 间隙锁 | 原理深度_UnderTheHood |
| ec2c46af1ae8734b4c658bef9f2d4aba | 元数据锁及其作用? | mdl | 原理深度_UnderTheHood |
| c7d4d4ec11fd1a58e7c9383c332f83d3 | 在 InnoDB 存储引擎下，一张表在底层存储时涉及哪些文件？ | innodb, ibd, ibdata1 | 原理深度_UnderTheHood |
| 0bb2308282b6a1ce16523d10967633ba | 在 MySQL B+ 树索引结构中，如果叶子节点满了会执行什么操作（涉及页分裂）？ | 页分裂, b+树 | 原理深度_UnderTheHood |
| a03ddcc9b67e31e142fb158205ad9958 | 在哪些场景下 MySQL 索引会失效？请解释最左前缀匹配原则的底层逻辑 | 索引失效, 最左前缀 | 原理深度_UnderTheHood |
| 785bda6903c299e5546020d24bcd14a6 | 在设计数据库时，你会考虑哪些核心方面？请重点介绍 B+ 树的数据结构 | b+树, 磁盘io | 原理深度_UnderTheHood |
| a6c63605d7c2538b12cde98f1ed25d37 | 在数据库设计中，你们在 MySQL 中对哪些字段创建了索引？请说明具体的索引优化理由 | 索引优化 | 场景设计_Scenario |
| 4a70b64bc2a1ac299bcc669d781ebbac | 在线DDL策略 | mysql, online ddl, pt-osc, gh-ost, 锁表问题 | 原理深度_UnderTheHood |
| b8e8a114e3ec713184147e2cae69a3d4 | 在已有索引的情况下，执行一条 update 语句依然极其缓慢，可能的原因有哪些（长事务、死锁、索引过多、硬件瓶颈等）？ | metadata lock, deadlock, insert/update slowdown | 场景设计_Scenario |
| 9fe1bcb70486815f3fbffdb2326af915 | 账户余额扣减竞态治理：在高并发账户扣减场景中，如何解决“丢失更新”问题？详细对比悲观锁（FOR UPDATE）与乐观锁（Version/CAS）在银行核心系统中的适用性？ | 悲观锁, 乐观锁, 竞态条件 | 原理深度_UnderTheHood |
| 04b7b33269039aa6815962b13c041cec | 针对长文本（Long Text）字段，应该如何建立索引以优化查询效率？ | 前缀索引, 全文索引 | 原理深度_UnderTheHood |
| ae78d91be7436d928c1db08efdf8868d | 知乎分库分表实践：回答表按 answer_id 分片后，如何设计倒排索引或索引表以支持高效查询某用户的“全部回答”？ | 分库分表, 索引表 | 架构设计_Architecture |
| 7f36782d8173f7bbda0cc714fce744e4 | 执行计划里有哪些字段? 哪些比较重要? | explain, type, rows, extra | 八股文_Concept |
| 59fbdde8dfbf5dc0fb88083d013c624a | 主键索引和二级索引的查询过程 | primary index, secondary index, b+ tree seek | 原理深度_UnderTheHood |
| 5b2dd2418ce2dac771dced062cb19c75 | 主键索引如何构建 B+ 树? 为什么 3-4 层可以存千万级数据? | b+ tree structure, fan-out, page size | 原理深度_UnderTheHood |
| 840335734a63d774d1e848e832185bc8 | 组合索引与单列索引的区别？最左匹配原则的底层逻辑？ | compound index, leftmost matching | 原理深度_UnderTheHood |
| 0d2d1d1001a2e9566db6329885e1d15d | 最左前缀原则知道吗,给你一个索引再给你一个查询条件判断是否能用到索引,查询条件的顺序改变能用到索引吗 | 最左前缀原则, 联合索引 | 原理深度_UnderTheHood |
| 24678ebeb8b730b1d47a98820e20cd1b | B+ 树范围查询的优化策略 (如索引下推) | 索引下推 | 原理深度_UnderTheHood |
| 16a3e3060d3274d9bb6218b97ea99a8d | B+ 树数据结构原理 | b+树, mysql索引 | 原理深度_UnderTheHood |
| 85893249093ad35085d26f9cc9263854 | B+ 树索引结构及相比 B 树的优势？ | b+树, b树 | 原理深度_UnderTheHood |
| 882437f9ef7a6b3ecc8ebf0480a68e32 | B树与B+树结构区别，典型应用（InnoDB索引构建） | b-tree, b+树, innodb, 索引结构 | 原理深度_UnderTheHood |
| cab7fb5123c537b1355c1428e016710f | Explain的type字段中，什么样的需要优化 | explain, type字段 | 原理深度_UnderTheHood |
| b2ff3e25d443558de6f8fd7cfc2017db | InnoDB 并发可见性分析：详述 MVCC（多版本并发控制）如何结合间隙锁（Gap Lock）解决可重复读级别下的“幻读”问题？ | mvcc, gap lock | 原理深度_UnderTheHood |
| a9c880fb1125e484b2297e1bc2b4c72e | InnoDB 存储引擎在 REPEATABLE READ (RR) 级别下是如何在最大程度上避免幻读的？ | mvcc, next-key lock, 间隙锁 | 原理深度_UnderTheHood |
| f0797f7dd488e3f9027b41ff3eb8033e | InnoDB 底层数据结构（B+ 树）？ | b+树, innodb | 八股文_Concept |
| d78ea29d2b50012ce89ca8d95c3b9715 | InnoDB 为啥索引的数据结果要用 B+树? | b+树, innodb, 索引原理 | 原理深度_UnderTheHood |
| 6acb7a3484828e3face59abd856bebad | InnoDB RR 级别下幻读被完全避免了吗？在什么情况下仍可能出现幻读？为何还需要 SERIALIZABLE 级别？ | 幻读, 当前读, 快照读 | 原理深度_UnderTheHood |
| 5c2828d9a13d21b523cb90747f1ed197 | InnoDB索引的底层数据结构? | b+树, innodb | 原理深度_UnderTheHood |
| 25e1b015e058f288f94a5cad408c92d3 | MVCC 过是怎么实现的? | mvcc | 原理深度_UnderTheHood |
| 596870f70595308962226d1bc91f150e | MVCC 机制深度：详细描述 MVCC 的内部实现细节（ReadView, 版本链）及其解决的并发问题？ | mvcc, readview, undo log | 原理深度_UnderTheHood |
| d71885548e606b20bb0cdee4aa036e94 | MVCC 机制深度应用：MVCC 如何在“不可重复读”与“读取已提交”隔离级别中发挥不同作用？ | readview, snapshot | 原理深度_UnderTheHood |
| d71885548e606b20bb0cdee4aa036e940 | MVCC 机制深度应用：MVCC 如何在“不可重复读”与“读取已提交”隔离级别中发挥不同作用？ | mvcc, readview | 原理深度_UnderTheHood |
| 052bc454ac3915278b6e80be1dadd04f | MVCC 实现机制 | mvcc, readview, undo log | 原理深度_UnderTheHood |
| fc02b3e5f6e49c9215b32729e48b251c | MVCC的流程 | mvcc, readview, undo log, 版本链, 可见性判断 | 原理深度_UnderTheHood |
| fd2c3911547c83e07911ef8d6f83da3a | MVCC机制可能产生什么问题（如旧版本堆积）？如何解决？ | mvcc, purge thread | 原理深度_UnderTheHood |
| 227d076d3975a423c84924448b9cd9f9 | MVCC原理？ | mvcc, readview, undo log, 版本链 | 原理深度_UnderTheHood |
| 2a5da1fcf1fa451648568b6aee9617f4 | MyISAM 索引与 InnoDB 索引的区别？ | 聚簇索引, 非聚簇索引 | 原理深度_UnderTheHood |
| dad6f25b3a4d9d8ce7eb35322539dcd2 | MySQL 并发控制：幻读（Phantom Read）的底层解决机制（Next-Key Locks）及 MVCC 在其中扮演的角色？ | phantom read, next-key lock, mvcc | 原理深度_UnderTheHood |
| 14d6c6e5f01be9c5515e5e368af6e085 | MySQL 并发控制：详细描述范围查询（Range Query）在不同隔离级别下对联合索引产生的间隙锁（Gap Lock）范围？ | gap lock, composite index, rr isolation | 原理深度_UnderTheHood |
| 0c56f3b17c8c05a8630a22fdf81f5b4a | MySQL 常用优化策略及索引失效的深度分析？ | mysql优化, 索引失效 | 原理深度_UnderTheHood |
| f611de611bcbb2857c0742ba08bd7e00 | MySQL 存储：通过三层 B+ 树的索引结构，如何估算其能承载的记录总数（基于 Page Size 16KB 与指针大小计算）？ | mysql, b+树, page | 原理深度_UnderTheHood |
| a6a5702f4a3d9c61c4d1a5f54aee70b1 | MySQL 存储：为什么 InnoDB 的主键索引能显著加速随机查询？B+ 树平衡过程对页分裂（Page Split）的影响？ | innodb, clustered index, b+树, page split | 原理深度_UnderTheHood |
| 4e228cc591a114b8737ba43384bb9115 | MySQL 存储：INT 与 DATETIME/TIMESTAMP 等基础数据类型在磁盘上的底层存储字节数及编码方式？ | mysql, 数据类型, 存储 | 八股文_Concept |
| c6072a6354739dc240b8d6be5fe1e6bb | MySQL 存储极限：一张表最多存储多少行数据（计算器推导逻辑）？ | b+ tree capacity, page size | 原理深度_UnderTheHood |
| 68d8ebb4ed971abcbcd7f3f2b43e63a4 | MySQL 存储引擎 MyISAM 与 InnoDB 的区别？ | myisam, innodb, 事务 | 分析题_Analysis |
| 3d8eea9d92899a0c07e03a283e281b6a | MySQL 大表 DDL 治理：在千万级回答表上新增字段或索引，如何利用 ghost 等工具避免长时间锁表并降低主从延迟？ | ddl, gh-ost | 方案设计_Scenario |
| f5e27a6d895f32b2e84192e21c324b10 | MySQL 的 B+ 树索引原理？ | b+树 | 原理深度_UnderTheHood |
| 79029d5ba049978ad099efd777076d60 | MySQL 的底层实现原理? 为什么用 B+ 树? | b+树, innodb | 原理深度_UnderTheHood |
| 7eee71f7d79ff82abd4518e5c01b5255 | MySQL 的底层数据结构是什么？与早期版本或其他数据库相比，这种结构（如 B+ 树）有哪些核心优势？ | b+树 | 原理深度_UnderTheHood |
| d84e75407db37be52e59f203d223e14e | MySQL 的索引是什么结构，有什么特点？ | b+树, 聚簇索引, 非聚簇索引 | 原理深度_UnderTheHood |
| 3d761f334771683af6b5eb0062ee07d1 | MySQL 的索引是怎么实现的？ | mysql, 索引, b+树 | 原理深度_UnderTheHood |
| 2b9a93b51bf3abb3c36681f4f3461674 | MySQL 的锁机制：在什么特定场景下会触发表级锁（Table Lock）？ | table lock | 八股文_Concept |
| ebb61920d8a4ebdd695821ef01a1c3d0 | MySQL 底层为什么要采用 B+ 树作为索引结构？ | b+树 | 原理深度_UnderTheHood |
| 03ec8eedbea3ece8a6807cd6e05e0e2e | MySQL 高可用架构方案：设计一套包含“读写分离、半同步复制、自动故障转移（MHA/Orchestrator）”的数据库方案？ | 高可用, 读写分离 | 架构设计_Architecture |
| 358700693a4099ce65f02f89ca098328 | MySQL 隔离级别：RR 如何解决幻读？ | rr, 间隙锁, next-key lock | 八股文_Concept |
| 28d915a3bea94c2fd10ad16713a5de4f | MySQL 回表性能：什么是回表（Look-up）？在复杂查询中，如何通过联合索引与覆盖索引（Covering Index）规避此开销？ | look-up, covering index | 原理深度_UnderTheHood |
| ce351014589f2196b6c0ac96f8e17f3e | MySQL 机制：MVCC 的工作原理、隔离级别定义及具体示例（如 RR 与 RC 的差异）？ | mvcc, readview | 原理深度_UnderTheHood |
| d5ed7d9a775c053385493552eb9ef7bd | MySQL 架构：详细描述 MySQL 主从复制的三个核心线程（IO Thread, SQL Thread）及其实现异步复制与增强半同步复制的区别？ | mysql主从复制, 异步复制, 半同步复制 | 原理深度_UnderTheHood |
| 403cfcd95ee7f0a78b4f77a857b4bf2b | MySQL 间隙锁定义及应用场景 | gap lock, phantom read, rr isolation | 八股文_Concept |
| 26bdd88df4ab3644f8a4bc8747e1635a | MySQL 健壮性：ACID 原子性是如何通过 Undo Log 保证的？如果在 Insert 执行中宕机，MySQL 复载（Recovery）时的逻辑推导过程？ | undo log, acid, recovery | 原理深度_UnderTheHood |
| c4e3f6726231b5b6d80053fbf2e17a9b | MySQL 聚簇索引（Clustered Index）与非聚簇索引（Secondary Index）的底层存储差异及回表开销优化？ | mysql, 聚簇索引, 非聚簇索引 | 原理深度_UnderTheHood |
| e933dcc2dcde0ca20d5e6db9efd8ed94 | MySQL 慢 SQL 调优的步骤有哪些（Explain 计划分析、索引优化、全表扫描规避、分页优化等）？ | explain plan, sql optimization | 场景设计_Scenario |
| 4f116a339e6a99a2c3a09e86ba1b6e6e | MySQL 慢查询原因及定位处理 | slow query log, explain, profiler | 场景设计_Scenario |
| a76a6b2ec7947f5f2bab2549e56de38f | MySQL 日志：MySQL 共有哪几种类型的日志（binlog, redolog, undolog）？它们分别负责什么？binlog 的主要格式（Row, Statement, Mixed）是怎样的？ | binlog, redo log, undo log | 原理深度_UnderTheHood |
| baa2e0e325523ec07c783a6aa0a3a0ac | MySQL 日志系统：binlog, redolog, undolog 的区别与作用？ | binlog, redo log, undo log | 八股文_Concept |
| ba9f481763a0f08e590549693cea37b9 | MySQL 日志系统：Redo Log 与 Undo Log 的底层实现原理及其在持久化与原子性中的作用？ | redo log, undo log, wal | 原理深度_UnderTheHood |
| 63aa7450a095a55c8730b69b563a25a6 | MySQL 如何避免重复插入数据? | insert ignore, replace into, on duplicate key update | 场景设计_Scenario |
| e796d62ff9269b64388bd1684575c773 | MySQL 如何解决并发问题? 各种锁的作用? | row lock, gap lock, next-key lock | 原理深度_UnderTheHood |
| 1b58bbb9bca779b938a98831946f33ad | MySQL 深度分页问题及解决方案（limit 优化）？ | limit optimization, deferred join | 场景设计_Scenario |
| 0c8f30ee4679d7808f3c492637b51d0c | MySQL 事务：详细解析二阶段提交（2PC）在 InnoDB 存储引擎与 Binlog 之间保证数据最终一致性的工作流？ | 2pc, innodb, binlog, 数据一致性 | 原理深度_UnderTheHood |
| 83c709a4be62faa62df7092b5e999009 | MySQL 事务：在可重复读（RR）隔离级别下，如何利用 Next-Key Lock（Gap Lock + Record Lock）解决幻读问题？ | mysql, next-key lock, 幻读 | 原理深度_UnderTheHood |
| 3b85da4285b8f98ad38c6cc01633282c | MySQL 事务：在可重复读（RR）级别下，MySQL 是通过什么机制实现隔离的？MVCC 中的多版本数据是如何产生的？ | rr isolation, mvcc | 原理深度_UnderTheHood |
| 5661f5f4fb0f04f2bf0e87d8634263b4 | MySQL 事务：InnoDB 存储引擎是如何实现事务（ACID 特性）的？ | innodb, redo log, undo log | 原理深度_UnderTheHood |
| c998bc75cc7845a5f260c2542a8830ab | MySQL 事务的隔离级别及解决的问题 | mysql, 事务隔离级别, 脏读, 不可重复读, 幻读, mvcc | 八股文_Concept |
| 893c8a92466f3509a0c91b6bfe64337b | MySQL 事务隔离：详细描述 MVCC 的底层实现原理（ReadView, Undo Log 指针等）？ | mvcc, readview, undo log | 原理深度_UnderTheHood |
| bc2bf1d842fa7a340172c0209088893b | MySQL 事务隔离级别及 MVCC + undo log 实现读已提交和可重复读的具体机制？ | mvcc, undo log, rr/rc isolation | 原理深度_UnderTheHood |
| 90f1465d3d4e062494192b0244192e21 | MySQL 事务隔离级别及如何解决幻读问题？ | mysql 事务隔离级别, 幻读 | 原理深度_UnderTheHood |
| e0b4c9ca2f8f3514ccd8ad130d875fd5 | MySQL 事务日志：Binlog 的三种格式（Statement, Row, Mixed）及其在主从同步可靠性上的优缺点对比？ | binlog, replication | 原理深度_UnderTheHood |
| 0ccfd3a26608ac311e1f3624fea5d491 | MySQL 事务一致性：详细辨析 Redo Log（重做日志）与 Binlog（归档日志）在写入时机、存储格式及奔溃恢复中的区别？ | redo log, binlog, crash recovery | 原理深度_UnderTheHood |
| fe4c33ee9fb26eff484fbcb4bef52455 | MySQL 是否具备保存非结构化数据的能力？如果是，该如何实现？ | json, mysql | 原理深度_UnderTheHood |
| 4f2655e9a69554bcbb29fdf5e6e890e8 | MySQL 数据库中是否涉及存储过程（Stored Procedure）的使用？在现代架构中其优劣势分析？ | 存储过程 | 架构设计_Architecture |
| 52857410214c1022e3f200d2f01f2bc2 | MySQL 索引 B+ 树原理？为什么比 B 树、Hash 索引更高效？ | mysql 索引, b+树 | 原理深度_UnderTheHood |
| 0d888306c3f5f11cdc097cb7d37821bd | MySQL 索引：强制使用索引（FORCE INDEX）的语法场景及优化器选择不走索引的常见原因（如过滤性差、回表开销大）？ | force index, mysql优化器, 回表 | 原理深度_UnderTheHood |
| a05590e47c285a198e786897f9eb6230 | MySQL 索引：请详细解释 MySQL 索引的原理，并对比不同存储引擎或不同数据库（如 MongoDB）在索引实现上的差异 | b+树, wiredtiger | 原理深度_UnderTheHood |
| 63164a2f16b95f1efb603b704a87c19d | MySQL 索引：什么是“回表”查询？如何通过联合索引（索引覆盖）避免回表以提升查询效率？ | mysql索引, 回表, 覆盖索引 | 八股文_Concept |
| ec87c34c0c30582cea6bfc3b6d317933 | MySQL 索引：详细解释“索引下推”（Index Condition Pushdown, ICP）的工作原理？在联合索引 (A, B, C) 场景下，查询条件 (A, C) 如何利用索引？ | icp, composite index | 原理深度_UnderTheHood |
| 53c0e5648a987c5596eae89cd1c62d95 | MySQL 索引：针对 TEXT/LONGTEXT 等大文本字段，常见的索引策略（前缀索引、全文本索引、外部 ES 同步）及其优缺点对比？ | mysql索引, 前缀索引, 全文搜索 | 八股文_Concept |
| 46865b48f454a59adf64b8f14233ff89 | MySQL 索引：MySQL 聚簇索引的底层数据结构是什么？为什么选择 B+ 树而非其他数据结构（如红黑树、B 树、哈希表）？请进行对比分析。 | b+树 | 原理深度_UnderTheHood |
| 201220dd77ec344af4e48fec05aaf36c | MySQL 索引：MySQL 中索引的存储形式是什么？结合 B+ 树结构，详细分析为什么联合索引必须遵循最左前缀匹配原则。 | b+树, 联合索引 | 原理深度_UnderTheHood |
| 55053116686054423c5ead36eebf5f05 | MySQL 索引的底层数据结构是什么？为什么选择 B+ 树而非 B 树？ | b+树 | 原理深度_UnderTheHood |
| ec2389120704f9c4f9d5be5eb29339dd | MySQL 索引底层实现原理：为什么 B+ 树在大规模 IO 场景下优于 B 树或红黑树？ | b+树, disk io, clustered index | 原理深度_UnderTheHood |
| ec2389120704f9c4f9d5be5eb29339dd | MySQL 索引底层实现原理：为什么 B+ 树在大规模 IO 场景下优于 B 树或红黑树？ | b+树, index density | 原理深度_UnderTheHood |
| 66b535a8ef5cb162913a9eff41ef0bbc | MySQL 索引覆盖优化：如何针对“SELECT * FROM answers WHERE user_id=? AND create_time>? ORDER BY vote_count DESC”设计最优索引？ | 复合索引, 索引优化 | 原理深度_UnderTheHood |
| 667b5874989e6739065dccba4cb0d83a | MySQL 索引进阶：为何联合索引遵循最左匹配原则（Leftmost Prefix Rule）？索引下推（ICP）如何在 Server 层级提升查询效率？ | leftmost prefix, icp | 八股文_Concept |
| 4b68427f7142013f982928392173f218 | MySQL 索引类型及其底层 B+ 树原理？ | mysql 索引, b+树 | 原理深度_UnderTheHood |
| b5accc07568aec3b018230ee698d8a0f | MySQL 索引深度：索引类型（主键、唯一、普通）、无主键表是否仍有主键索引、B+ 树与 B 树的区别？ | b+树, 聚集索引 | 原理深度_UnderTheHood |
| 891f1db6b68a4380608b41d4412aaa82 | MySQL 索引失效深度剖析：针对复杂 WHERE 条件与 ORDER BY 组合的慢查询，如何精准优化复合索引？ | 复合索引, 慢查询优化 | 原理深度_UnderTheHood |
| 386f525ac5b01a53016ec32f5ff24bc1 | MySQL 索引为什么不用红黑树或 AVL 树，而选择 B+ 树？ | b+树, 红黑树, 磁盘io | 原理深度_UnderTheHood |
| 45b629e41e285031b00d0219ee9412cg2 | MySQL 索引下推（Index Condition Pushdown）：在什么场景下会生效？如何减少回表次数？ | icp, index optimization | 原理深度_UnderTheHood |
| 0bb9a7bd919b1369ea1202cdb00bc87e | MySQL 索引优化：详细描述回表（Look-up）操作及其对查询性能的影响？如何通过覆盖索引优化？ | mysql, look-up, covering index | 原理深度_UnderTheHood |
| 0e6b4eff4390eb5ea7944bd7fa77052e | MySQL 索引优化场景：什么是 Filesort？如何避免？ | filesort, using index, mysql优化 | 原理深度_UnderTheHood |
| 27f21aa86e901c7832168a9e6c46f7a0 | MySQL 锁：间隙锁（Gap Lock）的触发场景及其在防止幻读中的具体工作机理？ | gap lock, 幻读, mysql锁 | 原理深度_UnderTheHood |
| 2d1153433e8ddf422f2034b1daac7ea4 | MySQL 锁机制：请描述 InnoDB 行锁（Record Lock）、间隙锁（Gap Lock）与临键锁（Next-key Lock）的应用场景及死锁回避策略？ | next-key lock, deadlock avoidance | 原理深度_UnderTheHood |
| 96ad46e3efa4f9499f79ba30ceb60635 | MySQL 锁机制：详细辨析行级锁（Row Lock）与表级锁（Table Lock）的区别及其对并发性能的影响？ | mysql lock, row lock, table lock | 原理深度_UnderTheHood |
| 5c254d51a7e5a16ae920e5468c50d8c6 | MySQL 锁升级：当 Update 语句的 Where 条件字段未加索引时，InnoDB 引擎会采取何种级别的锁定？如何通过优化避免全表锁？ | lock escalation, full table lock | 场景设计_Scenario |
| 55c53395aa02d19e13fe599c5c5f9f66 | MySQL 为什么不使用红黑树而是 B+tree? | b+树, 红黑树, 磁盘io | 原理深度_UnderTheHood |
| a8c149b43b36958c4b9dcb4eedaa8384 | Mysql 为什么一定要有一个主键？ | 聚簇索引, innodb存储引擎 | 原理深度_UnderTheHood |
| ce5a0c56fb500086e0e96f4f771f906e | Mysql 为什么用 B+ 树，B+ 树和 B 树，红黑树等有什么区别 | b+树, b树, 红黑树, 磁盘io, 范围查询 | 原理深度_UnderTheHood |
| 4b68427f7142013f982928392173f218 | MySQL 现场手撕练习题（具体题目未列出）？ | sql | 算法手撕_Coding |
| 0fda23c50e3ec6138e9cab97450f46f5 | MySQL 性能：Explain 执行计划中各个关键字段（type, key, Extra）的含义？如何通过 Extra 字段判断是否使用了索引过滤？ | explain, sql optimization | 八股文_Concept |
| 8f05ddfe08a4f00804a8ad8083139f0b | MySQL 优化：请尽可能详细地说明 SQL 优化的常见方式（包括执行计划分析、索引覆盖、关联查询优化、大表深度分页优化等） | explain plan, covering index, deferred join | 场景设计_Scenario |
| 5a8acc2bdf9590328b58a5746279755c | MySQL 语句的执行过程是怎样的？ | 执行引擎, 分析器, 优化器 | 原理深度_UnderTheHood |
| 9e0395f5f27a7a5259b8950233790b08 | MySQL 原理：详细描述 MySQL 执行一条 UPDATE 语句的完整全流程。 | mysql, update日志 | 原理深度_UnderTheHood |
| 140a969a49244f72a041400b2d45e151 | MySQL 运维：Binlog 存储的具体二进制内容及其在主从同步中的异步/半同步复制原理？ | binlog, replication, async/semi-sync | 原理深度_UnderTheHood |
| 67bdc64840f4d445c3977043bb8ef283 | MySQL 中聚簇索引与非聚簇索引的区别是什么？B+ 树相比其他结构（如 Hash, 二叉树）的优势体现在哪里？ | b+树, 聚集索引 | 原理深度_UnderTheHood |
| e790a5c93538945b2f7377f0bc62293a | MySQL 中遇到慢查询如何查看执行计划? | explain, 慢查询 | 原理深度_UnderTheHood |
| 4d2ef11e17251ddb7fde5af62ec1b1e2 | MySQL 主键索引和普通索引的区别是什么? 谁的性能更好一些? | 主键索引, 普通索引, 聚簇索引 | 原理深度_UnderTheHood |
| 6aad2a3b332953a12bd19bb42da49550 | MySQL 最左前缀匹配：给定索引 (a, b, c)，查询条件为 a=1 and b>1 and c=1，这会走索引吗？为什么 c=1 部分可能不走索引？ | 最左前缀, 范围查询, 索引失效 | 原理深度_UnderTheHood |
| 0595bfe8157e271450e003fa499c78a0 | MySQL JOIN 查询中，条件写在 ON 后面和 WHERE 后面的区别？ | join, on, where | 八股文_Concept |
| 99c45d2ba851b28e5bfb55ac53f20924 | MySQL MVCC 的底层原理 | mvcc | 原理深度_UnderTheHood |
| a81173fa73a250c1d949af3bd323e99e | MySQL MVCC 机制：ReadView、undo log 在实现事务隔离中的作用？ | mvcc, undo log, readview | 原理深度_UnderTheHood |
| fbceac103ac47191f939ade301b17ddf | MySQL MVCC（多版本并发控制）实现原理（ReadView、Undo Log、隐藏列的协作） | mysql, mvcc, readview, undo log | 原理深度_UnderTheHood |
| 02b75852ec6434ec8c97cdefad1f978e | MySQL：创建联合索引时为什么要将高频字段放在最前面？ | compound index | 原理深度_UnderTheHood |
| 8871d3eacd8eee53203556bee5535956 | MySQL：哈希索引与B+树索引的对比分析及适用场景 | hash index, b+树 | 原理深度_UnderTheHood |
| 14bf5803813d47ee536bc5440c379b4b | MySQL：回表、索引覆盖、索引下推的概念与原理 | index lookups, covering index, icp | 原理深度_UnderTheHood |
| d64179d66b1b9f882fb30ae79072570c | MySQL：Char 与 Varchar 的底层存储架构区别及对 I/O 的影响 | varchar, char | 原理深度_UnderTheHood |
| 96ac3b620489085db541c3c0c9c5ed22 | MySQL的索引结构是什么？为什么使用 B+树？ | mysql, 索引, b+树 | 原理深度_UnderTheHood |
| cdd06437c540379784d0d85c4e5e953b | MySQL的索引数据结构是什么，主键索引和非主键索引在数据结构上有什么区别 | b+树, 聚簇索引, 二级索引 | 原理深度_UnderTheHood |
| 4ff7f6184d82a23e0747fecfe3dbcea3 | MySQL的执行过程？ | 执行计划, 解析器, 优化器, 执行器 | 原理深度_UnderTheHood |
| 825e1af7bce4b99c7405e5847bda86f9 | mysql的acid特性是怎么实现的 | mysql, acid, redo log, undo log, mvcc, 锁 | 原理深度_UnderTheHood |
| ecc3aaeb215adc5a87c04a7b38829cce | mysql的B+树数据结构 | b+树, mysql, innodb, 索引 | 原理深度_UnderTheHood |
| 6de4c775362093ffdc6b2f4204abc8ab | MySQL的redo log和binlog有什么区别？ | mysql, redo log, binlog | 原理深度_UnderTheHood |
| f5c7c93aadf161d7a072362ad2023952 | MySQL调优你是怎么做的？ | mysql, 性能调优 | 原理深度_UnderTheHood |
| f5c7c93aadf161d7a072362ad2023952 | MySQL调优你是怎么做的？ | mysql | 原理深度_UnderTheHood |
| 8c2eeaeccab096648d86848d75170278 | MySQL日志：redo log、undo log、binlog，写入顺序？ | redo log, undo log, binlog, 两阶段提交 | 原理深度_UnderTheHood |
| 0d60d728ab367f561556ca826a3b2cca | MySQL日志的存储位置在哪？是物理的还是逻辑的？ | mysql | 原理深度_UnderTheHood |
| 73f30ec416261dffbeb232705894e2bb | MySQL如何实现事务的? 主要 undolog 日志是怎么工作的? | undo log, 原子性, 回滚 | 原理深度_UnderTheHood |
| ec41dfc9113539dc0cb43fc22b552071 | MySQL索引：联合索引失效场景分析：where a=** order by b 等复合条件下的索引命中逻辑 | compound index, index invalidation | 原理深度_UnderTheHood |
| 590ab6cabdda2063fc8d665a65a489eb | MySQL索引底层B+树的数据结构特征及其节点查找过程 | mysql, b+树, 索引 | 原理深度_UnderTheHood |
| bd4f9e155f1c60157b3a61f047760c9d | MySQL索引原理？以及为什么要用B+树？用其他的可以吗？ | b+树, 索引 | 原理深度_UnderTheHood |
| 5aca7a9c14702d8e8164e7a76d8e2ffc | mysql行锁（说知道记录锁，临键锁，间隙锁，具体怎么用忘记了） | 行锁, 间隙锁, 记录锁 | 原理深度_UnderTheHood |
| 376cba1ebc70e55599f1dccd8e0b215c | MySQL优化：如何在数据库中存储IP地址？(INT型替代字符串) | ip storage | 原理深度_UnderTheHood |
| 3e3a61572df9b09ca4da0c4c3cc68240 | mysql怎么实现事务 | mysql, innodb, 事务, undo log, redo log, mvcc | 原理深度_UnderTheHood |
| 7998d741c9fbc23edda9e2e4c4aaf6d0 | MySQL中，ID一定要自增吗？能不能不自增？如果不自增会产生什么问题？为什么建议自增？ | mysql, 索引 | 原理深度_UnderTheHood |
| 0b285d418ed19751a65181323b7d3351 | ORM 映射：MyBatis 中 '#' 与 '$' 的底层差异及其在防范 SQL 注入上的作用机理？数据库记录到 Java 对象的映射背后是如何实现的？ | mybatis, sql injection, preparedstatement | 八股文_Concept |
| 51e2098da04c298536577f29891520c1 | redo log 的作用，buffer pool 的原理，redo log 刷盘的时机的，redo log 满了怎么处理，为什么用 redo log 而不是 bin log 恢复数据 | redo log, buffer pool, 刷盘机制, wal, crash-safe, checkpoint | 原理深度_UnderTheHood |
| d7b02dbd7acf8c7adfbdc7a3cd4598e7 | RTree 索引是怎么构建的？ | rtree, 空间索引 | 原理深度_UnderTheHood |
| 7fc475253f674e7dbc02ad75be6198f0 | SELECT x, y FOR UPDATE 的作用是什么？加的是什么锁？会变成表锁吗？ | mysql, 锁 | 原理深度_UnderTheHood |
| 13d62299d6acfb306e38f0462e1a3c9e | SQL 调优：Explain 命令中的 key、rows、extra 字段含义？索引优化器成本分析原理？ | explain, mysql优化器 | 原理深度_UnderTheHood |
| 6867cd9bc36f6d6ad4923cadcb9cbf3b | SQL 分析：执行 `WHERE id > 10` 时会加锁吗？加什么锁？是否会锁定 `id > 20` 的记录？ | 范围查询, next-key lock | 原理深度_UnderTheHood |
| 81603e45dcf55423eb9cc0f20a6eb7a6 | SQL 分析：执行 `WHERE name > 'test1'` 会加锁吗？加锁的粒度和逻辑是怎样的？ | 非唯一索引锁 | 原理深度_UnderTheHood |
| b0a6332f0d7a0639860523642571848f | SQL 考题：三表关联查询及子查询的应用实现？ | sql查询, 子查询 | 算法手撕_Coding |
| 373c4880046afd8a909ec99542b4e6c30 | SQL 实战：编写两个场景化的 SQL 查询语句。 | sql | 手撕代码_Coding |
| 373c4880046afd8a909ec99542b4e6c3 | SQL 实战：编写两个场景化的 SQL 查询语句。 | sql select, scenario sql | 手撕代码_Coding |
| 658891b03db1cb7c73b1505c0a18a39a | SQL 索引优化：对于 select * from t where a = 100 and b > 100 and b <= 1000 and c = 10，请设计对应的联合索引并解释原因？ | composite index, range query optimization | 场景设计_Scenario |
| b4d7dd86ede4f8fda6a9b027026545be | SQL：给定 table1，要求：当字段 a 在所有元组中都等于 '1' 时，返回字段 b='2' 的前 2 条数据，按字段 c 排序。请编写对应的 SQL 语句。 | - | 算法手撕_Coding |
| 9823d9f2636cc0e4f198d9c01c20a848 | SQL：如何找到表中重复次数最多的 name 及其重复的个数？ | sql, group by, hadving | 原理深度_UnderTheHood |
| 9ebb896630d1e350f41ee29dec6f3cdf | SQL：有一个收入记录表 `income_records` (user_id, income, month)，请编写 SQL 计算每个用户每个月的收入总额，并筛选出单月收入总额大于 1000 的记录（要求包含 user_id 和 month）。 | - | 算法手撕_Coding |
| 6f57df29da4e0f4af6f8ae89753a8c54 | text和varchar底层存储区别 | text, varchar | 原理深度_UnderTheHood |

## L3_Diagnostic (62 道题目)

| Question ID | 题目 | 相关技术点 (Entities) | 题型 (Type) |
|---|---|---|---|
| 0c362af5e5eccffd477ff97b267641e0 | 并发安全：什么是“死锁（Deadlock）”？请列举一个数据库（MySQL）中由于索引加锁顺序不一致导致死锁的真实业务场景 | deadlock, lock graph, index lock contention | 场景设计_Scenario |
| 8bdfcf6ce38a1351510590a6c8ac5317 | 场景：给定一个sql语句，询问加了什么锁？ | mysql锁, 事务隔离级别 | 场景设计_Scenario |
| deeb73fd62a44e9596580c99187be211 | 场景估算：使用索引键进行单条SQL查询时，底层磁盘I/O的次数是如何确定的？ | mysql, 索引, 磁盘io, b+树 | 原理深度_UnderTheHood |
| 25004cc23c963b3fd21f1385ce22f116 | 场景设计：在主从架构下，如果主从同步延迟较高，导致用户刚创建的数据无法立即在列表页查出，应如何优化用户体验？ | 主从延迟, 强一致性查询 | 场景设计_Scenario |
| 6822cf317a5712d280be7d8876f011f8 | 场景题：假设数据库中有海量并发任务需要频繁修改用户余额。为了保证并发安全且不因加锁导致严重的性能瓶颈，你有哪些优化方案？ | 分库分表, 热点数据打散, 缓冲池 | 场景设计_Scenario |
| f24d4b29e4a2d6b91c38031d33d19c9d | 出现错误 Duplicate entry '...' for key 'base_data.PRIMARY' 是什么原因？ | duplicate entry, 主键冲突, 唯一性约束 | 底层机制_LowLevel |
| c2f2a904f57a066bafb335d82a8462a2 | 存储优化：针对海量数据的 SQL 慢查询，请从索引覆盖、子查询优化及执行计划分析给出系统性调优方案？ | sql optimization, explain plan | 场景设计_Scenario |
| 61798dccf506fefb0ab2c230c1d2744a | 高并发优化：当 MySQL 查询压力过大时，除了分库分表外，还有哪些行之有效的手段？ | read-write splitting, connection pool | 场景设计_Scenario |
| 6068a148ebf09e3fed80238a5b30406f | 给你几个字段让你设计其属性类型,大小,后分析哪些字段适合建立索引,哪些不适合建立索引,索引的选择性是什么意思 | 索引, 索引选择性, 字段类型 | 场景设计_Scenario |
| 54464d674f9d06279a271fd664d182c5 | 技术挑战：假设强制要求利用 SQL 实现字典树（Trie Tree）逻辑，你会如何进行 Schema 设计与查询？ | trie树, sql建模 | 系统设计_Architecture |
| c1ae0ebb83e8e0cdc75692ac790562f8 | 慢 SQL 排查：请描述你定位、排查并优化一条慢 SQL 的完整工作流 | explain, slow query log | 场景设计_Scenario |
| 2a7320a856ee111ccd5f30528fe5e751 | 你遇到过哪些导致 MySQL 索引失效的场景？ | 索引失效 | 原理深度_UnderTheHood |
| 473f58ee5fa7fd11d6f1a52ed7c4c79e | 你在日常工作中对 SQL 进行了什么优化? | sql优化, 索引优化, 覆盖索引, 深度分页 | 项目深挖_Project |
| e95bfc2b7dcf052880fd4b9d3f3649ce | 请描述慢 SQL 的排查流程 | 慢查询, explain | 场景设计_Scenario |
| 2a578c8bda2e147f6f3ad792139a879a | 请描述慢查询的优化流程及常用手段 | explain, 慢查询 | 场景设计_Scenario |
| e229cf61fcf7b23d2d1f8b19ac404fb3 | 如果索引优化后查询依然缓慢，你会采取哪些进一步措施（如分库分表、硬件扩容等）？ | 分库分表 | 场景设计_Scenario |
| bf7c0c5f28b4b3e6c3c111bfe3fbee3c | 如何查看索引是否高效利用？ | explain, 索引, type, key_len | 场景设计_Scenario |
| ecfcb0f9f218f562de542914d5237532 | 如何优化SQL？ | sql优化, explain, 索引, 慢查询 | 场景设计_Scenario |
| 5ff223e4451122a63260c6d9a16f21a3 | 使用乐观锁解决超卖问题及高并发优化？ | 乐观锁, sharding | 场景设计_Scenario |
| 0db2e917327a9cad7223101a0b73284e | 事务深度：隔离级别详解、RR 模式下的幻读/侧写问题及 Spring 事务失效场景分析？ | 隔离级别, 事务失效 | 原理深度_UnderTheHood |
| c73984366ad8aa9cb310e1764fdca204 | 数据库：如何利用 EXPLAIN 语句来分析 and 优化慢 SQL 查询？ | explain, 慢查询 | 场景设计_Scenario |
| 5886c8601e4fe0b0b03742deb945d42a | 数据库：索引碎片化的成因及优化手段 (OPTIMIZE TABLE 或重建索引机制) | index fragmentation, optimize table | 原理深度_UnderTheHood |
| c95c168b4dd28d2d6471738b9e466970 | 数据库：在处理千万级以上的 SaaS 业务数据时，你会采取哪些 MySQL 优化手段（如分库分表、索引下推优化、大分页查询优化）？ | 分库分表 | 原理深度_UnderTheHood |
| 3aca15ca5f4c89ae0a6fb54754be92b5 | 数据库：在秒杀过程中，MySQL 的哪部分数据需要修改？如何处理库存扣减的高并发写压力？ | 库存扣减, 行锁, redis预减库存 | 场景设计_Scenario |
| 2b4522b8d768e9e062fc3493f36e1dad | 数据库：在设计电商系统的商品表时，为“库存”字段增加索引是否合理？请分析索引带来的查询优势与更新压力平衡。 | 索引, b+树 | 场景设计_Scenario |
| 761a6393bbbceb4da3679c4bdb8883de | 数据库：在什么情况下应该建立索引？如何评价一个索引设计的好坏？ | 索引设计, 区分度 | 场景设计_Scenario |
| b82d4125069ad3e331974604aa6983b7 | 数据库：针对“深度分页”查询，有哪些常用的 SQL 优化策略？ | 深度分页, 子查询优化 | 场景设计_Scenario |
| 17cc79bb46ed277e765633b49d45b4c5 | 数据库：MySQL 的索引决策是在哪一步完成的？如果执行计划选择了错误的索引，你有哪些排查和调优手段（如 force index, analyze table）？ | 执行计划, force index | 经验思考_Reflection |
| 348c4e84a9795f3b1789cc3263c6d602 | 数据库并发：在高并发下单场景下，如何根据业务需求选择合适的 MySQL 锁策略？ | 并发控制 | 场景设计_Scenario |
| ce48f490bbc286f02f7225849fe8d2cd | 数据库调优：分享一次你在线上真实处理慢查询（Slow Query）的经历？涉及哪些索引覆盖与 SQL 重写技巧？ | 慢查询, index coverage | 原理深度_UnderTheHood |
| 50796d8c663a26d5e2ac330323bc9b17 | 数据库集群：如何排查并解决 MySQL 主从同步延迟问题？ | master-slave delay, binlog | 场景设计_Scenario |
| 289ccab326aa3ad5d62a9133e9e2b8b5 | 数据库死锁分析：针对 Gap Lock 导致的并发更新死锁，如何进行压力测试复现并设计规避策略？ | 死锁, gap lock | 原理深度_UnderTheHood |
| 40482003d7e1d4196c4f98d0a3749b52 | 数据库优化：针对字段众多且拥有百万/千万级数据的单表，在执行深度分页（Deep Paging）查询时，有哪些具体的 SQL 优化方案（如子查询优化、延迟关联、覆盖索引）？ | deep paging, deferred join, covering index | 场景设计_Scenario |
| fd47cd9e533960d9ae4e3ba07c0c1fd7 | 数据库诊断：当查询性能不佳时，你会使用哪些索引失效分析工具（如 EXPLAIN）？执行计划中的 `type` 和 `extra` 字段分别代表什么含义？ | explain plan analysis, index invalidation, sql optimization statistics | 场景设计_Scenario |
| bacead7768fb94e10596031ff77a5c72 | 算法：三个sql | sql查询 | 算法手撕_Coding |
| cdfc7259a126cda64dcd488b40aeb439 | 写密集型数据库的索引优化与锁冲突规避 | 写密集, 锁冲突 | 场景设计_Scenario |
| 3351c19b6673f93ad8ee8b51e16ce1f4 | 在实现新功能时，你是如何设计数据模型和表结构的？请介绍核心设计思路 | 表结构设计 | 场景设计_Scenario |
| 46b8c8cb54d53eb6c62e4b17f36c5517 | 在主从同步过程中，如果从库在重做（Relay Log）时失败了，该如何解决？ | 主从不同步, relay log修复 | 场景设计_Scenario |
| c0ca3633ce051531088aa60a52ec7857 | MySQL 查询优化：在大表（数亿级）场景下，如何优化分页查询（Deep Paging）以避免全表扫描（利用子查询/ID 偏移）？ | mysql, deep paging, 分页查询 | 原理深度_UnderTheHood |
| f839a3a6929f8701c3f200cd0e19b8a4 | MySQL 处理每秒 10 万级订单写入的优化方案？ | 批量写入, 分库分表 | 场景设计_Scenario |
| 778f093c8ddc91578b379a3b3cb749b7 | MySQL 调优策略、慢查询日志定位及 EXPLAIN 结果分析？ | mysql调优, explain | 原理深度_UnderTheHood |
| 26bdd88df4ab3644f8a4bc8747e1635a | MySQL 健壮性：ACID 原子性是如何通过 Undo Log 保证的？如果在 Insert 执行中宕机，MySQL 复载（Recovery）时的逻辑推导过程？ | mysql, acid, undo log, 崩溃恢复 | 原理深度_UnderTheHood |
| ddf4d73a99605dffd986a470ad59cd29 | MySQL 慢查询排查流程：慢查询日志 → explain 执行计划分析（type/key/extra）？ | 慢查询, explain | 原理深度_UnderTheHood |
| 4b68427f7142013f982928392173f21a | MySQL 慢查询优化：Explain 执行计划关注点及索引调优策略？ | mysql 慢查询, explain | 原理深度_UnderTheHood |
| 937746ed9ad5212040cc0b0d33087d68 | MySQL 如何恢复到误删除前的状态? | binlog, 数据恢复 | 场景设计_Scenario |
| 6637cf81c2933a6d663d751abcdb18cb | MySQL 死锁实战：京东库存服务出现 “间隙锁+插入意向锁” 死锁，如何复现和解决？ | mysql锁, 间隙锁, 插入意向锁 | 原理深度_UnderTheHood |
| 104c9a54199980d99acb8bc474f67838 | MySQL 索引实战：针对具体业务表及查询语句，如何设计最优索引？辨析不同索引方案的优劣及索引失效（Index Skip Scan）场景？ | mysql index, index skip scan | 场景设计_Scenario |
| 14ad6d87910708c2f26ed59184fe5e3c | MySQL 异常分析：为什么数据库的自增 ID 会出现不连续的跳过现象？请列举至少两个场景（如唯一索引冲突、事务回滚）？ | auto-increment id, rollback, locking | 原理深度_UnderTheHood |
| 7cc4ca614df7ef85d932f87347df59ec | MySQL 优化：B+ 树相比于 B 树在磁盘存储上的核心优势是什么？针对千万级数据的“慢 SQL”及“深度分页（Deep Paging）”问题，你有对应的优化思路吗？ | b+树, 慢查询, deep paging | 场景设计_Scenario |
| 4551785177c9386638924a9890029dbf | MySQL 主从：详细解析主从延迟（Replication Lag）产生的原因及业务测兜底方案（如强制路由主库、Binlog 并行回放）？ | mysql主从, 主从延迟, binlog | 原理深度_UnderTheHood |
| 9fc0493a86b3af1e5d1fa9716f6e2d10 | MySQL 主从延迟导致重复派单如何解决？ | 主从延迟, 幂等 | 场景设计_Scenario |
| 451ce54c245eeea70225770fe669a6cd | MySQL 自增 ID 在高并发或分布式场景下可能存在哪些问题？如何解决？ | 自增id, 雪花算法, uuid | 场景设计_Scenario |
| c2b7e6841b12a407e717ed3cedc533e5 | MySQL的索引失效？ | 索引失效, 最左前缀, 函数 | 场景设计_Scenario |
| 48a3a5a194f5dd916ad8aa028ab0e617 | MySQL死锁分析：线上出现INSERT ON DUPLICATE KEY UPDATE导致的死锁，如何复现和规避？ | mysql死锁, insert on duplicate key update | 原理深度_UnderTheHood |
| 363a04efadd127f5edcbc0a1c87779df | SQL 实战：针对复杂业务逻辑 design 并讨论最优索引方案。 | sql index design | 场景设计_Scenario |
| 4e7c1f9bc1acd06cc7aec3fe8c843e04 | SQL 性能抉择：join 操作一定会导致性能问题吗？如何根据表数据量与索引状态决定连接策略？ | sql join, index | 场景设计_Scenario |
| 3c7b1f10abf68ceede4df212516b33d6 | SQL 优化：给定 SQL select * from table where a > ? and b = ? or c = ? order by d desc limit 10，请分析该语句的执行效率并提出优化建议。 | sql优化, explain, 复合索引 | 场景设计_Scenario |
| 4925d72af707a6646702d6531ff62adc | SQL 优化：针对一个包含百万级数据量的表，如何解决“深度分页”查询带来的性能问题？ | 深度分页, 延迟关联 | 场景设计_Scenario |
| ee8960a3615be599130d595906b49e05 | SQL 优化案例：SELECT * FROM orders WHERE status=1 AND create_time>? 执行慢，如何优化？ | 索引优化, 复合索引 | 场景设计_Scenario |
| 0c22e8b347dec07b824d646a83dcf90d | SQL 遇到慢查询你会怎么去定位和优化？ | 慢查询, explain | 原理深度_UnderTheHood |
| 1146b3fd2fdc403aee824d46cc198926 | SQL优化实战：SELECT * FROM orders WHERE user_id=? AND status IN(1,2,3) ORDER BY create_time DESC如何建索引？ | 索引优化, 复合索引 | 场景设计_Scenario |
| 55379088df7962c500476180d3679164 | TCP 是如何通过序列号、确认应答等机制保证可靠传输的？ | 索引失效, explain | 场景设计_Scenario |

