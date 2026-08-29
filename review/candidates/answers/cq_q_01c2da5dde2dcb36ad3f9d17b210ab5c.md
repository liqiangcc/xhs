<!-- xhs-answer: {"schema_version":"answer.v1","canonical_id":"cq_q_01c2da5dde2dcb36ad3f9d17b210ab5c","version":1,"status":"draft","updated_at":"2026-08-29","answer_type":"coding","quality_tier":"candidate"} -->
# binlog / MQ 消费卡顿导致缓存与数据库不一致：补救与防复发

## 核心结论

先把数据库视为事实源，按“止损 → 恢复消费 → 可重放补偿 → 全量/增量对账 → 防止旧消息覆盖新值 → 监控和容量治理”处理。消费线程卡住时优先恢复到最后一个**已确认成功应用**的 checkpoint；MQ 积压则先确认是整体吞吐不足还是毒消息/外部依赖阻塞，再做扩容、批量、隔离重试。无论 replay 还是人工补偿，都要保证幂等并阻止旧事件回写新缓存；如果日志已过期或 checkpoint 不可信，就从数据库快照/变更时间做 reconciliation，必要时直接失效缓存让读路径回源重建。TTL 只能降低不一致持续时间，不能替代正确补偿协议。

## 1 分钟版

- **先止损**：确认 DB 正确、缓存错误范围和消费 lag；必要时暂停有风险的缓存更新或把热点 key 切到回源，避免继续扩大错误。
- **恢复消费者**：重启/拉起卡死 worker，修掉阻塞依赖；从最后成功 checkpoint 重放，不要“为了追进度”直接跳过未应用事件。
- **处理毒消息**：有界重试 + 退避；确定性失败可隔离到补偿/DLQ 流程，但要记录原事件和顺序信息，不能静默丢掉。
- **追积压**：消费者可水平扩容时扩容；同时看分区/顺序约束、外部 IO、批处理和 backpressure，避免只加线程反而打爆 DB/缓存。
- **对账修复**：按 DB 扫描 key/version 与缓存比较，缺失/旧值刷新或删除；日志缺失时 reconciliation 是最终兜底。
- **防旧覆盖新**：事件带可比较的 version/change-position，缓存写入前检查版本；或者维护幂等 event-id，保证 duplicate/retry 不重复生效。
- **闭环监控**：lag 时间、backlog age、重试/DLQ、消费耗时、对账差异数和修复队列都要可观测。

## 3 分钟版

下面代码只演示一个关键补偿不变量：**replay / retry / reconciliation 都不能让旧版本覆盖新版本，也不能让删除后的旧事件把缓存复活**。真实 binlog/MQ 的 offset、GTID、event-id 或业务版本要按实际系统映射到这里的 `version`。

```java
import java.util.HashMap;
import java.util.Map;

public final class VersionedCacheRepair {
    public record Change(String key, long version, String value, boolean deleted) {}
    public record Entry(long version, String value) {}

    private final Map<String, Entry> cache = new HashMap<>();
    private final Map<String, Long> appliedVersion = new HashMap<>();

    public boolean apply(Change change) {
        long seen = appliedVersion.getOrDefault(change.key(), -1L);
        if (change.version() <= seen) {
            return false; // duplicate or stale replay
        }

        appliedVersion.put(change.key(), change.version());
        if (change.deleted()) {
            cache.remove(change.key());
        } else {
            cache.put(change.key(), new Entry(change.version(), change.value()));
        }
        return true;
    }

    public boolean reconcileFromDatabase(Change authoritativeSnapshot) {
        return apply(authoritativeSnapshot);
    }

    public Entry get(String key) {
        return cache.get(key);
    }

    public long appliedVersion(String key) {
        return appliedVersion.getOrDefault(key, -1L);
    }
}
```

这不是在声称所有系统都天然有 per-key version，而是把补偿时必须解决的“顺序/幂等”问题显式化。比如缓存已经应用 v4，迟到的 v3 必须跳过；v5 是删除后，也要保留“已应用到 v5”的 tombstone/version 元数据，否则缓存虽然被删了，随后迟到的 v4 仍可能把旧值重新写回来。对于没有业务版本的 CDC，可以用实际 pipeline 提供的可排序 change position、事务序号或幂等事件表实现同类保护。

## 关键细节

- **checkpoint 的含义必须是“副作用成功后”**：如果先提交 offset/checkpoint，再写缓存失败，重启后会从更后位置继续，形成永久缺口；除非系统明确接受 at-most-once 语义。
- **重放前先判断日志是否还在**：binlog 有保留/清理周期；如果所需区间已经被 purge，不能假装 replay 还能恢复，只能用 DB 快照/对账重新建立基线。
- **毒消息不能拖死整条链路**：确定性错误反复重试会阻塞后续消息。可隔离，但对有顺序要求的同 key/分区必须设计“隔离后如何保持或恢复顺序”，不能简单跳过就宣布一致。
- **MQ 慢要找瓶颈**：CPU、序列化、网络、下游 DB/缓存、锁竞争、单分区顺序都可能限制吞吐。扩消费者前要确认 broker/partition 和下游容量允许并行。
- **reconciliation 是独立安全网**：即使 replay 正常，也应允许定期抽样或全量扫描 DB 与缓存的 version/value，发现漏消费、人工误操作、过期日志等非单一故障。
- **删除事件也要有版本记忆**：只 `cache.delete(key)` 而不保留已应用版本，可能被迟到旧消息复活。
- **TTL 不是一致性协议**：它能让错误缓存最终过期，但不能保证过期前读取正确，也不能保证过期后一定立刻重建正确值。
- **先恢复正确性，再追求追平速度**：盲目提高并发可能加剧 DB/缓存压力，造成二次故障；应设置最大并发、速率和 backpressure。

## 原理机制

这类故障的本质是“事实源已经前进，但派生状态没有按同一变化序列前进”。因此补救要恢复两个不变量：第一，**不漏**——从可信 checkpoint 之后的变化最终都被应用，日志缺口则由数据库 reconciliation 补齐；第二，**不倒退**——duplicate、retry、乱序或人工补偿不能把已经更晚的缓存状态覆盖成旧状态。

binlog/CDC replay 解决“我还能找到历史变化”的问题；MQ 重试/DLQ 解决“某个变化一时处理不了”的问题；DB reconciliation 解决“历史变化已经找不到或消费记录不可信”的问题；version/idempotency 解决“重复和乱序会不会把修复再次破坏”的问题。这四层互补，不能只靠重启消费者。

## 项目经验版

来源没有指定 MySQL 版本、MQ 产品、缓存类型、offset 提交语义和业务版本字段，所以不能给出“Kafka 开多少 partition”或“Redis 用哪个 Lua”这样的伪精确答案。真实事故中我会先冻结时间线：DB 最新位置、消费者最后成功位置、最老可重放位置、MQ 最老消息年龄、错误 key 范围；然后选择 replay 或 snapshot-reconcile，并把修复吞吐限制在下游可承受范围。恢复后再补自动对账和告警，避免下一次只能靠人工发现。

## 常见追问

- 问：消费者重启就够了吗？答：不够。要确认从哪个成功 checkpoint 恢复、历史日志是否还在，以及失败期间是否存在已经跳过/丢失的事件。
- 问：为什么不能直接把 MQ offset 跳到最新？答：这会把未应用变化永久丢掉，除非随后有可靠的 DB reconciliation 且业务明确接受这条恢复路径。
- 问：DLQ 会不会破坏顺序？答：可能。对同 key/分区有严格顺序时，隔离毒消息必须配套暂停该顺序域、版本保护或后续重放策略。
- 问：缓存不一致时刷新还是删除？答：取决于读路径。删除后回源重建通常更简单，但要考虑缓存击穿；直接刷新则必须确保使用 DB 最新版本并防止旧事件随后覆盖。
- 问：怎么防重复消费？答：幂等写：使用 event-id 去重，或比较业务/version/change-position，只接受比已应用状态更新的变化。
- 问：如何判断“已经恢复”？答：消费 lag/backlog 回到正常区间还不够，还要让 reconciliation 差异归零或低于明确阈值，并持续观察一段稳定窗口。

## 易错点

- 看到消费者卡住就直接跳 offset，未补偿被跳过的数据。
- retry 没有上限和隔离，把一个毒消息变成全局阻塞。
- 只做 `cache.delete`，不保存删除版本，迟到旧事件把缓存复活。
- 扩容消费者却忽略同 key/分区顺序和下游容量，追 backlog 反而制造乱序/雪崩。
- 把 TTL 当作强一致保证。
- 只看 backlog 数量不看最老消息年龄和 DB/缓存实际差异。
