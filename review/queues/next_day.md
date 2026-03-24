# Next Day Queue

## 2026-03-24
- note_id: 680f7bf7000000000e004ccf | 高可用三板斧 | 原因：14/25，边界和场景不足 | 骨架：限流防过载 / 熔断防扩散 / 降级保核心
- note_id: 680f7bf7000000000e004ccf | JVM 调优 + MAT | 原因：13/25，排查链路不完整 | 骨架：监控 -> GC日志 -> dump -> Histogram -> Dominator Tree -> GC Roots
- note_id: 680f7bf7000000000e004ccf | HashMap 并发 | 原因：18/25，需补复合操作原子性 | 骨架：线程不安全 -> 覆盖/丢失/1.7环链 -> CHM -> 原子API
- note_id: 680f7bf7000000000e004ccf | 本地缓存设计 | 原因：直接分析，需复述 | 骨架：ConcurrentHashMap/Caffeine -> TTL -> 淘汰 -> 防穿透/击穿/雪崩
- note_id: 680f7bf7000000000e004ccf | CompletableFuture 超时控制 | 原因：17/25，需补异常与取消语义 | 骨架：supplyAsync -> allOf -> orTimeout/completeOnTimeout -> fallback
- note_id: 680f7bf7000000000e004ccf | ThreadLocal 链路跟踪 | 原因：19/25，需补异步透传 | 骨架：入口set -> 链路取值 -> remove -> 异步线程显式透传
- note_id: 680f7bf7000000000e004ccf | 跨服务数据一致性 | 原因：18/25，需补最终一致优先级 | 骨架：本地事务局限 -> 消息表/TCC/Seata -> 幂等/补偿
