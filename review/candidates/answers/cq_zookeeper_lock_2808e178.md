<!-- xhs-answer: {"schema_version":"answer.v1","canonical_id":"cq_zookeeper_lock_2808e178","version":1,"status":"draft","updated_at":"2026-07-11","quality_tier":"candidate","answer_type":"mechanism"} -->
# ZooKeeper 如何实现分布式锁？

## 核心结论

ZooKeeper 锁通常不是抢一个固定节点，而是在锁目录下创建带 GUID 的临时顺序节点。客户端若自己的序号最小即持锁；否则只 watch 排在自己前一位的节点，前驱删除后重新取 children 判断。临时节点在会话过期后会被删除，顺序节点给出排队顺序；只监听前驱避免所有等待者同时被唤醒。

## 1 分钟版

- 每个获取请求生成 GUID，在 `/locks/order/guid-lock-` 创建 `EPHEMERAL_SEQUENTIAL` 节点并保存服务端返回的完整路径。
- 读取同目录 children 并按序号排序：自己最小则持锁；否则对紧邻前驱执行 `exists(path, watch=true)`，前驱已经不存在就重新读取而不是盲等。
- 释放只删除自己的完整节点；关联会话实际过期时，临时节点由 ZooKeeper 删除，后继 watcher 再竞争。
- 创建调用发生可恢复错误时，先按 GUID 查找本会话留下的节点；不能因不知道 create 是否已成功而再创建一条无关排队节点。

## 3 分钟版

参与者是 lock parent、每个客户端的 GUID 临时顺序子节点、children 列表与前驱节点 watch。进入时客户端创建 `EPHEMERAL_SEQUENTIAL`，服务端在路径末尾追加递增序号；随后读取 children。最小序号节点持锁，其余客户端不 watch parent 或全部更小节点，而只 watch 直接前驱。前驱被删除后，收到通知的客户端重新读取 children：若现在最小则持锁，否则换成新的直接前驱继续 watch。这样一次删除通常只推进一个写锁等待者，而不是形成 herd effect。

退出时持有者 delete 自己的节点；连接中断不等于节点已删除，临时节点只在关联会话实际过期后由 ZooKeeper 删除。创建请求超时或连接异常也可能出现“服务端已创建但客户端未拿到路径”，官方 recipe 要求在 reconnect 后以 GUID 检查 children 再决定恢复等待还是重试。业务临界区的状态提交与下游授权仍须由业务自身定义，不能从节点删除推断下游已自动完成任何操作。

成本是每次竞争的 create、getChildren 与 watch 状态，锁热点会把所有请求串行化并增加会话/节点压力；它适合短、低冲突的协调临界区，不适合长事务或高频数据路径。在单一热点且持锁时间有界的设计假设下，等待时间随前方持锁工作累积；实际值仍要以 children 数、等待时间、会话过期、create/exists 错误、异常遗留 GUID 和持锁业务耗时压测验证。

## 关键细节

- 每个获取请求生成 GUID，在 `/locks/order/guid-lock-` 创建 `EPHEMERAL_SEQUENTIAL` 节点并保存服务端返回的完整路径。
- 读取同目录 children 并按序号排序：自己最小则持锁；否则对紧邻前驱执行 `exists(path, watch=true)`，前驱已经不存在就重新读取而不是盲等。
- 释放只删除自己的完整节点；关联会话实际过期时，临时节点由 ZooKeeper 删除，后继 watcher 再竞争。
- 创建调用发生可恢复错误时，先按 GUID 查找本会话留下的节点；不能因不知道 create 是否已成功而再创建一条无关排队节点。
- 本文以 Apache ZooKeeper 官方 Recipes 与当前 3.9.5 CreateMode API 为边界；Recipes 是客户端约定，不是服务端自动提供的锁 API。
- `EPHEMERAL_SEQUENTIAL` 节点在关联会话过期时删除，且名称追加递增序号；客户端必须保存实际返回的路径。
- watch 触发后要重新读取状态；在设置前驱 watch 时前驱可能已经删除，需重新判断。
- 不要对 parent 或全部前驱设置 watch；写锁按直接前驱监听以避免无谓唤醒。

## 原理机制

状态机为 `create ephemeral-sequential → list children → {lowest: hold | predecessor: watch} → predecessor deleted → re-list → release/session expiry`。顺序号是排队比较键，临时属性把会话过期映射为节点删除；前驱 watch 把删除事件只交给下一个可能取得锁的客户端。create 的 GUID 把客户端请求与目录中的节点对应起来，用于处理响应丢失后的不确定状态。单一热点的等待成本受前方节点数和各自持锁时间影响，不能脱离负载给出固定性能结论。

## 项目经验版

项目映射提示：填写真实版本、配置、规模、观测指标与故障演练；只阅读源码时不包装成线上实践。

## 常见追问

- 问：为什么不直接创建固定 `/lock` 节点？答：固定节点只有抢占失败或轮询，无法给所有等待者排序；临时顺序子节点同时提供排队序号与会话清理。
- 问：为什么只监听前一个节点？答：前驱删除后只有直接后继可能成为最小节点；监听 parent 会在每次删除唤醒全部等待者并形成 herd effect。
- 问：create 超时后能否马上再创建？答：不能先假定第一次失败；按 GUID 查询已有子节点，若已创建就继续该节点的排队流程。
- 问：连接中断后节点会立刻删除吗？答：不会把短暂断连等同于删除；临时节点的自动删除边界是关联会话实际过期，客户端应按连接/会话状态重新判断。

## 易错点

- 不要把 TCP 断开、连接丢失和 ZooKeeper 会话过期混为同一时刻。
- 不要用顺序节点名称猜测自己创建的节点；响应丢失场景要用 GUID 关联。
- 不要将 ZooKeeper 节点删除外推成下游数据库、存储或外部系统已自动完成状态转换。
- 不要把所有等待者都 watch 在同一个 parent 上。
