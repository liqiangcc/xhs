# Canonical Batch Queue

Baseline: 2026-07-10. Batch size: 10. The queue is ordered for high-value-first construction; all long-tail questions remain in scope for C7.

`attach` means enrich an existing Canonical. `create` means create a new Canonical after checking the top existing matches. `review` means the current candidate has a taxonomy or boundary issue that must be resolved first.

## Batch 1 — Existing Attachments And Java Concurrency

| # | Candidate | Recommended action | Target / intended title |
|---:|---|---|---|
| 1 | 线程和进程的区别 | attach | `cq_topic_f575096b` |
| 2 | TCP 与 UDP 的区别 | attach | `cq_tcp_e9932fa7` |
| 3 | 反转链表 II | attach | `cq_topic_3f61dd36` |
| 4 | RocketMQ 顺序消费性能 | attach | `cq_rocketmq_b7347b07` |
| 5 | 索引失效场景 | attach | `cq_topic_99ffa229` |
| 6 | AQS 原理 | create | AQS 的核心原理和同步队列 |
| 7 | ReentrantLock 公平/非公平锁 | create | ReentrantLock 如何实现公平与非公平 |
| 8 | CAS 与 ABA | create | CAS 原理、ABA 与解决方案 |
| 9 | ThreadLocal 内存泄漏 | create | ThreadLocal 为什么泄漏以及如何避免 |
| 10 | 线程状态 | create | Java 线程的生命周期和状态转换 |

## Batch 2 — MySQL And Redis

| # | Candidate | Recommended action | Target / intended title |
|---:|---|---|---|
| 11 | synchronized 与 Lock 的区别 | review | taxonomy 错误；修正为 Java 并发后创建 |
| 12 | Redis AOF 重写 | attach/create | 先判断是否归入 `cq_topic_2494ec69` |
| 13 | MySQL binlog 模式与复制 | create | binlog 模式和主从复制流程 |
| 14 | Undo Log 与崩溃恢复 | create | Undo Log 如何保证原子性 |
| 15 | 聚簇与非聚簇索引 | create | 聚簇索引和非聚簇索引的区别 |
| 16 | MySQL 与 Redis 双写一致性 | create | 缓存一致性的常见方案与取舍 |
| 17 | B+ 树索引 | create | MySQL 为什么使用 B+ 树 |
| 18 | MySQL 隔离级别 | create | 隔离级别、异常现象和实现 |
| 19 | MVCC | create | MVCC、Read View 与版本链 |
| 20 | Redis 过期与淘汰 | create | Redis 过期删除和内存淘汰 |

## Batch 3 — Message Queue, Spring And Network

| # | Candidate | Recommended action | Target / intended title |
|---:|---|---|---|
| 21 | RocketMQ 核心架构 | create | NameServer、Broker、Producer、Consumer |
| 22 | Kafka 避免重复消费 | create | Kafka 重复消费与业务幂等 |
| 23 | Kafka ISR | create | ISR 的作用与副本同步 |
| 24 | 消息只消费一次 | create | exactly-once 语义与业务幂等边界 |
| 25 | Spring 同 ID Bean 冲突 | create | Bean 定义冲突发生在哪个阶段 |
| 26 | Spring AOP | create | Spring AOP 原理和代理选择 |
| 27 | Spring 事务失效 | create | 声明式事务失效场景 |
| 28 | TCP 三次握手 | create | TCP 三次握手过程和异常处理 |
| 29 | TIME_WAIT 2MSL | create | TIME_WAIT 为什么等待 2MSL |
| 30 | TIME_WAIT 与 CLOSE_WAIT | create | 两种状态的成因与排查 |

## Batch 4 — System Design And Remaining Backbone

| # | Candidate | Recommended action | Target / intended title |
|---:|---|---|---|
| 31 | 分布式链路追踪 | create | 如何设计分布式链路追踪系统 |
| 32 | 架构分层 | create | 复杂系统为什么需要分层 |
| 33 | 同城多活数据同步 | create | 多活架构的数据同步与一致性 |
| 34 | 短 URL 生成 | create | 百亿短链如何生成无冲突 ID |
| 35 | 三千万用户短视频系统 | create | 合并重复候选后建立一个 Canonical |
| 36 | 网盘秒传与限速 | create | 文件去重、秒传、分片和限速 |
| 37 | Redis 分布式锁等待逻辑 | create | 锁竞争、阻塞唤醒与续期 |
| 38 | IPC 方式 | create | 进程间通信方式及选择 |
| 39 | Java 三大特性 | create | 封装、继承、多态及工程边界 |
| 40 | 设计模式实践 | create | 常用设计模式与项目选择条件 |

## Queue Acceptance Rules

- Every row is checked against existing Canonical records before mutation.
- Taxonomy errors are corrected before acceptance.
- Duplicate candidates inside this queue are merged into one decision.
- Each accepted row gets a strict-valid answer in the same batch.
- Batch completion is recorded only after canonical, answer, index and review checks pass.

## C2 Execution Note

C2 completed 26 create decisions and reached 60 Canonical records / 208 assigned rows. Queue rows 6–10, 12–16, 18, 21–23, 27–28 and 38 are complete. The batch also completed SPI, Spring Boot auto-configuration, dependency injection, JVM OOM, CMS, GC algorithms, Redis distributed lock, MQ selection and IO multiplexing from the same hotspot review. Remaining rows stay queued for later stages; their presence does not mean the completed assets should be recreated.
