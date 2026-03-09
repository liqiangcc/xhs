# 📋 面试题复习计划 (纯净终极版)

> 基于最新清洗且完全合并过的 `tech_entities` 数据生成。
> 策略：**按优先级 P0→P1→P2 顺次复习，以 L2 领域为骨架，深挖核心 entity**

---

## 🔴 P0 — 必须掌握（高频核心，建议前 3 天搞定）

### 数据库 -> MySQL (645题) - 📅 Day 1
**👑 核心实体 Top 8：**
`b+树`(99) | `mysql`(63) | `mvcc`(48) | `innodb`(37) | `undo log`(35) | `索引`(32) | `索引失效`(24) | `acid`(24)

**⚡ 建议抽题命令：**
```bash
node scripts/query_tagged.js entity --value "b+树" --slim
node scripts/query_tagged.js entity --value "mysql" --slim
node scripts/query_tagged.js entity --value "mvcc" --slim
node scripts/query_tagged.js entity --value "innodb" --slim
```

### Java -> 并发编程(JUC) (480题) - 📅 Day 2
**👑 核心实体 Top 8：**
`线程池`(103) | `synchronized`(84) | `锁`(45) | `cas`(43) | `volatile`(41) | `threadlocal`(31) | `hashmap`(30) | `aqs`(28)

**⚡ 建议抽题命令：**
```bash
node scripts/query_tagged.js entity --value "线程池" --slim
node scripts/query_tagged.js entity --value "synchronized" --slim
node scripts/query_tagged.js entity --value "锁" --slim
node scripts/query_tagged.js entity --value "cas" --slim
```

### 中间件 -> Redis (313题) - 📅 Day 3
**👑 核心实体 Top 8：**
`redis`(91) | `分布式锁`(25) | `aof`(24) | `rdb`(22) | `redis集群`(16) | `redisson`(15) | `zset`(13) | `io多路复用`(9)

**⚡ 建议抽题命令：**
```bash
node scripts/query_tagged.js entity --value "redis" --slim
node scripts/query_tagged.js entity --value "分布式锁" --slim
node scripts/query_tagged.js entity --value "aof" --slim
node scripts/query_tagged.js entity --value "rdb" --slim
```

---
## 🟡 P1 — 重点领域（大厂必问，建议中间 4 天搞定）

### Java -> JVM (359题) - 📅 Day 4
**👑 核心实体 Top 6：**
`jvm`(37) | `gc`(35) | `cms`(34) | `g1`(30) | `classloader`(18) | `双亲委派`(14)

**⚡ 建议抽题命令：**
```bash
node scripts/query_tagged.js entity --value "jvm" --slim
node scripts/query_tagged.js entity --value "gc" --slim
```

### Java -> 集合框架 (196题) - 📅 Day 5
**👑 核心实体 Top 6：**
`hashmap`(119) | `arraylist`(34) | `红黑树`(25) | `linkedlist`(25) | `扩容`(13) | `hashtable`(9)

**⚡ 建议抽题命令：**
```bash
node scripts/query_tagged.js entity --value "hashmap" --slim
node scripts/query_tagged.js entity --value "arraylist" --slim
```

### 计算机网络 -> TCP/IP (146题) - 📅 Day 5
**👑 核心实体 Top 6：**
`tcp`(69) | `udp`(25) | `三次握手`(23) | `四次挥手`(23) | `time_wait`(14) | `ack`(6)

**⚡ 建议抽题命令：**
```bash
node scripts/query_tagged.js entity --value "tcp" --slim
node scripts/query_tagged.js entity --value "udp" --slim
```

### 中间件 -> Kafka (53题) - 📅 Day 7
**👑 核心实体 Top 6：**
`kafka`(32) | `消息队列`(6) | `消息堆积`(4) | `解耦`(3) | `削峰填谷`(3) | `rocketmq`(3)

**⚡ 建议抽题命令：**
```bash
node scripts/query_tagged.js entity --value "kafka" --slim
node scripts/query_tagged.js entity --value "消息队列" --slim
```

### 中间件 -> RocketMQ (30题) - 📅 Day 7
**👑 核心实体 Top 6：**
`rocketmq`(19) | `顺序消费`(4) | `nameserver`(3) | `定时投递`(2) | `broker`(2) | `消息堆积`(2)

**⚡ 建议抽题命令：**
```bash
node scripts/query_tagged.js entity --value "rocketmq" --slim
node scripts/query_tagged.js entity --value "顺序消费" --slim
```

---
## 🟢 P2 — 进阶与系统设计（区分度，最后 3 天主攻）

### 系统设计 -> 系统设计 (9题) - 📅 Day 8-9
**👑 核心实体 Top 6：**
`幂等性`(2) | `软件架构`(1) | `重复请求`(1) | `websocket`(1) | `轮询`(1) | `限流`(1)

### 中间件 -> Elasticsearch (5题) - 📅 Day 10
**👑 核心实体 Top 6：**
`倒排索引`(3) | `elasticsearch`(2) | `es filter cache`(1) | `shard rebalance`(1) | `lucene lifecycle`(1) | `dual-write`(1)

