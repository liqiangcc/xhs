# Content Inventory

Generated baseline: 2026-07-10. Source of truth: `data/questions/canonical_questions.jsonl` and `review/answers/`.

## Baseline

| Metric | Value |
|---|---:|
| Question rows | 9,620 |
| Current reviewable rows | 9,362 |
| Rows requiring validity re-audit | 258 |
| Canonical records | 34 |
| Assigned rows | 134 |
| Ready answers | 34 |
| Reviewed canonical | 0 |

## Existing Canonical Assets

### Java Collections, Language And Concurrency

- `cq_arraylist_9d3444a1` — ArrayList 和 LinkedList 的区别
- `cq_hashmap_4d9f15d2` — HashMap 原理
- `cq_hashmap_d74d2fd7` — ConcurrentHashMap 原理
- `cq_stringbuffer_8b8caf0d` — StringBuilder 和 StringBuffer 的区别
- `cq_topic_36aeccc5` — 线程池的拒绝策略
- `cq_topic_c569b06e` — `==` 和 `equals` 的区别

### Spring

- `cq_bean_319a398d` — Spring Bean 生命周期

### Database And Cache

- `cq_force_index_5e733952` — 优化器选错索引
- `cq_topic_99ffa229` — MySQL 索引失效
- `cq_topic_9e860ba7` — 数据库查询瓶颈优化
- `cq_redis_ff848e90` — Redis 为什么快
- `cq_topic_2494ec69` — Redis 持久化

### Message Queue

- `cq_rocketmq_b7347b07` — RocketMQ 顺序消费性能

### Network And Operating System

- `cq_http_c439559c` — HTTP 与 HTTPS 的区别
- `cq_tcp_e9932fa7` — TCP 与 UDP 的区别
- `cq_topic_f575096b` — 进程和线程的区别

### System Design And Troubleshooting

- `cq_easyexcel_0f713ce7` — 百万级 Excel 导入
- `cq_topic_0c5b15b3` — 搜索引擎设计
- `cq_topic_20fba961` — 库存超卖与少卖
- `cq_topic_71d1f3c1` — 分布式调度框架
- `cq_topic_89b69343` — 高并发压力保护
- `cq_topic_956bc5ce` — QPS 提升十倍
- `cq_topic_e60c993a` — 全链路压测平台
- `cq_topic_f003d8b7` — API 响应慢排查
- `cq_topic_fcc849e5` — 微服务拆分
- `cq_topic_fe047aa4` — 秒杀系统

### Coding

- `cq_merge_intervals_866286e5` — 合并区间
- `cq_topic_3f61dd36` — 反转链表 II
- `cq_topic_722fbd80` — 三数之和
- `cq_topic_745b29f7` — K 个一组翻转链表
- `cq_topic_77ee33f1` — 反转链表
- `cq_topic_ac84034f` — 最长递增子序列
- `cq_topic_cc39dcdb` — 字符串大数加法

### Other

- `cq_ai_055f19f9` — AI 在后端工程化中的实践

## High-Priority Coverage Gaps

| Topic | Existing Strength | Immediate Gaps |
|---|---|---|
| Java collections | HashMap/CHM/ArrayList basics | resize details, fail-fast, CopyOnWriteArrayList, collection selection |
| Java concurrency | one thread-pool subtopic | thread lifecycle, pool parameters, AQS, CAS/ABA, synchronized/volatile, ThreadLocal |
| JVM | none | memory model, object allocation, GC, class loading, troubleshooting |
| MySQL | index failure and optimization | B+ tree, transaction/isolation, MVCC, locks, redo/undo/binlog, replication |
| Redis | performance and persistence | data structures, expiry/eviction, HA, cache risks, consistency, distributed lock |
| Spring | Bean lifecycle | IoC, AOP, transactions, circular dependency, MVC |
| MQ | one RocketMQ performance card | architecture, reliability, idempotency, ordering, backlog, transaction messages, Kafka |
| Network/OS | TCP/UDP, HTTP/HTTPS, process/thread | handshake/wave, TIME_WAIT, epoll, IPC, coroutine |
| System design | strong scenario start | capacity estimation, distributed transaction, ID, consistency, multi-active, file/LBS systems |
| Troubleshooting | API latency | JVM CPU/memory, DB, MQ backlog, cache, network, incident response |
| Project/behavior | absent from canonical layer | project deep dives, conflict, challenge, planning, leadership, HR |

## Inventory Decisions

- Existing 34 assets are the C1 calibration set.
- Current `ready` means structurally complete; semantic readiness is re-audited in C1/C3.
- The 258 currently invalid rows are not accepted as final exclusions; each is re-audited in C7.
- Every subsequent batch must close Canonical, Answer and ReviewProgress together.
