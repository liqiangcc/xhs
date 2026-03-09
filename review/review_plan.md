# 📋 面试题复习计划

> 基于 955 篇小红书面经笔记、9600+ 道去重题目的数据分析生成。
> 策略：**L2领域为骨架 + tech_entity 深挖 + 高频题查漏**

---

## 🔴 P0 — 必须掌握（高频核心，建议 3-4 天）

### 1. MySQL（645 题）
**核心实体**：`B+树`(68) · `MySQL`(63) · `MVCC`(48) · `InnoDB`(37) · `索引`(32) · `ACID`(24) · `索引失效`(24)

```bash
node scripts/query_tagged.js entity --value B+树 --slim
node scripts/query_tagged.js entity --value MVCC --slim
node scripts/query_tagged.js entity --value InnoDB --slim
node scripts/query_tagged.js entity --value 索引失效 --slim
```

复习路线：
- [ ] 索引原理：B+树结构 → 聚簇/非聚簇 → 联合索引 → 覆盖索引 → 索引失效场景
- [ ] 事务机制：ACID → 隔离级别 → MVCC（ReadView） → 幻读 → Next-Key Lock
- [ ] SQL调优：EXPLAIN → 慢查询优化 → 分库分表

---

### 2. Java 并发编程（480+124=604 题）
**核心实体**：`synchronized`(100) · `ThreadPoolExecutor`(64) · `线程池`(69) · `CAS`(55) · `volatile`(50) · `ReentrantLock`(59) · `ThreadLocal`(41) · `AQS`(37)

```bash
node scripts/query_tagged.js entity --value synchronized --slim
node scripts/query_tagged.js entity --value CAS --slim
node scripts/query_tagged.js entity --value volatile --slim
node scripts/query_tagged.js entity --value AQS --slim
node scripts/query_tagged.js entity --value ThreadLocal --slim
node scripts/query_tagged.js entity --value 线程池 --slim
```

复习路线：
- [ ] 锁机制：synchronized原理 → 锁升级 → ReentrantLock vs synchronized → AQS
- [ ] 原子操作：CAS → volatile可见性 → happens-before
- [ ] 并发工具：线程池参数 → ThreadLocal内存泄漏 → CountDownLatch/CyclicBarrier
- [ ] 并发容器：ConcurrentHashMap (JDK7 vs 8)

---

### 3. Redis（313+146+74=533 题）
**核心实体**：`Redis`(172) · `AOF`(48) · `RDB`(43) · `分布式锁`(24) · `Redisson`(15) · `Redis Cluster`(23) · `ZSet`(10)

```bash
node scripts/query_tagged.js entity --value Redis --slim
node scripts/query_tagged.js entity --value AOF --slim
node scripts/query_tagged.js entity --value Redisson --slim
node scripts/query_tagged.js entity --value 缓存穿透 --slim
```

复习路线：
- [ ] 数据结构：String/Hash/List/Set/ZSet → 底层编码（SDS/ZipList/SkipList）
- [ ] 持久化：RDB vs AOF → 混合持久化
- [ ] 高可用：主从 → Sentinel → Cluster
- [ ] 应用：缓存穿透/击穿/雪崩 → 分布式锁（Redisson） → 大Key问题

---

### 4. JVM（359+155=514 题）
**核心实体**：`JVM`(48) · `GC`(41) · `CMS`(34) · `G1`(41) · `ClassLoader`(24) · `双亲委派`(23) · `OOM`(14) · `ZGC`(13)

```bash
node scripts/query_tagged.js entity --value GC --slim
node scripts/query_tagged.js entity --value CMS --slim
node scripts/query_tagged.js entity --value G1 --slim
node scripts/query_tagged.js entity --value OOM --slim
node scripts/query_tagged.js entity --value 双亲委派 --slim
```

复习路线：
- [ ] 内存模型：堆/栈/方法区/元空间 → 对象创建流程 → 内存溢出场景
- [ ] 垃圾回收：GC Roots → 可达性分析 → CMS vs G1 vs ZGC → 调优参数
- [ ] 类加载：双亲委派 → 打破双亲委派 → 热部署

---

## 🟡 P1 — 重点掌握（中高频，建议 3-4 天）

### 5. Java 集合框架（196 题）
**核心实体**：`HashMap`(92) · `ConcurrentHashMap`(37) · `ArrayList`(34) · `LinkedList`(25) · `红黑树`(21)

复习路线：
- [ ] HashMap：数组+链表+红黑树 → put流程 → 扩容(2的幂) → 线程不安全原因
- [ ] ConcurrentHashMap：JDK7分段锁 vs JDK8 CAS+synchronized
- [ ] ArrayList vs LinkedList → 扩容机制 → 随机访问 vs 插入删除

---

### 6. TCP/IP 与 HTTP（146+101=247 题）
**核心实体**：`TCP`(77) · `HTTP`(29) · `HTTPS`(23) · `UDP`(25) · `SSL/TLS`(17) · `DNS`(13) · `三次握手`(23) · `四次挥手`(23)

复习路线：
- [ ] TCP：三次握手/四次挥手 → TIME_WAIT → 滑动窗口 → 拥塞控制
- [ ] HTTP：1.0 vs 1.1 vs 2.0 vs 3.0 → HTTPS握手 → SSL/TLS → GET vs POST
- [ ] DNS解析流程 → CDN原理

---

### 7. 消息中间件 — Kafka & RocketMQ（联合约 200 题）
**核心实体**：`Kafka`(93) · `RocketMQ`(76) · `消息队列`(37)

复习路线：
- [ ] Kafka：分区/副本 → ISR → 零拷贝 → 消费者组 → 事务消息
- [ ] RocketMQ：存储模型 → 延时消息 → 死信队列 → 事务消息
- [ ] 通用：消息丢失/重复/顺序 → 幂等性 → 削峰填谷

---

### 8. 系统设计 — 高并发（132 题）
**核心实体**：`秒杀`(13) · `高并发`(13) · `限流`(10) · `分布式锁`(9) · `乐观锁`(7)

复习路线：
- [ ] 秒杀系统：页面静态化 → Redis预扣 → 异步下单 → 限流/降级
- [ ] 限流算法：令牌桶 vs 漏桶 vs 滑动窗口
- [ ] 分布式锁：Redis SETNX → Redisson → ZooKeeper

---

### 9. 操作系统 — 进程与线程（90 题）
**核心实体**：`进程`(22) · `线程`(22) · `上下文切换`(11) · `死锁`(6) · `epoll`(4)

复习路线：
- [ ] 进程 vs 线程 vs 协程
- [ ] 进程通信：管道/消息队列/共享内存/信号量
- [ ] IO多路复用：select vs poll vs epoll
- [ ] 死锁条件 → 避免策略

---

## 🟢 P2 — 锦上添花（建议 2-3 天）

### 10. Spring 生态（~215 题）
**核心实体**：`AOP`(79) · `Spring`(55) · `动态代理`(41) · `Spring Boot`(48)

- [ ] IOC 容器：Bean生命周期 → 循环依赖（三级缓存）
- [ ] AOP：动态代理（JDK vs CGLIB） → 切面执行顺序
- [ ] Spring Boot 自动配置原理

### 11. 设计模式（69 题）
- [ ] 单例（DCL + volatile） → 工厂 → 策略 → 观察者 → 代理

### 12. 分布式系统（~200 题）
- [ ] 分布式事务：2PC/3PC → TCC → Saga → 最终一致性
- [ ] CAP/BASE → 一致性哈希 → 分布式ID

### 13. 算法（链表/树/DP，~250 题）
- [ ] 链表：反转/合并/环检测/LRU
- [ ] 树：层序遍历/LCA/BST
- [ ] 动态规划 → 双指针 → 排序算法

### 14. Elasticsearch / 微服务（各~50-70 题）
- [ ] ES 倒排索引 → 分词 → 深分页优化
- [ ] 微服务治理：注册中心 → 熔断降级 → 链路追踪

---

## 🏆 高频必考题 Top 10（每道出现 5-8 次）

| # | 题目 | 频次 |
|---|------|------|
| 1 | TCP 与 UDP 的区别，TCP 如何保证可靠传输 | 8 |
| 2 | 死锁发生的必要条件及如何避免 | 8 |
| 3 | 布隆过滤器原理及在 Redis 中的应用 | 8 |
| 4 | HashMap / HashSet 底层结构，是否线程安全 | 8 |
| 5 | String 为什么设计为不可变 | 7 |
| 6 | Spring IOC 和 AOP 核心概念 | 7 |
| 7 | 三数之和（算法） | 6 |
| 8 | ReentrantLock 与 synchronized 区别 | 6 |
| 9 | 微服务架构如何做系统拆分 | 6 |
| 10 | 进程和线程的区别 | 5 |

---

## 📅 建议时间安排（共 8-10 天）

| 天数 | 模块 | 重点 |
|------|------|------|
| Day 1 | MySQL 索引+事务 | B+树, MVCC, 索引失效 |
| Day 2 | MySQL 调优 + Redis 基础 | SQL优化, 数据结构, 持久化 |
| Day 3 | Redis 高可用 + 缓存场景 | Cluster, 穿透/击穿/雪崩, 分布式锁 |
| Day 4 | Java 并发（锁） | synchronized, CAS, AQS, volatile |
| Day 5 | Java 并发（工具）+ 集合 | 线程池, ThreadLocal, HashMap |
| Day 6 | JVM | GC, CMS/G1/ZGC, OOM, 类加载 |
| Day 7 | 网络 + 操作系统 | TCP, HTTP/HTTPS, 进程/线程 |
| Day 8 | 消息中间件 | Kafka, RocketMQ |
| Day 9 | 系统设计 + 分布式 | 秒杀, 分布式事务, CAP |
| Day 10 | Spring + 设计模式 + 算法 | IOC/AOP, 链表/树/DP |

---

## 🛠️ 查询命令速查

```bash
# 按实体查
node scripts/query_tagged.js entity --value HashMap --slim
# 按领域查
node scripts/query_tagged.js domain --l2 JVM --slim
# 高频题
node scripts/query_tagged.js hotspot --slim
# 按公司
node scripts/query_tagged.js company --name 字节跳动 --slim
# 按认知深度
node scripts/query_tagged.js depth --value L3_Diagnostic --slim
# 组合过滤
node scripts/query_tagged.js domain --l2 MySQL --filter-company 美团 --slim
```
