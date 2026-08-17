<!-- xhs-answer: {"schema_version":"answer.v1","canonical_id":"cq_hashmap_4d9f15d2","version":2,"status":"draft","updated_at":"2026-08-17","answer_type":"mechanism","quality_tier":"candidate"} -->
# HashMap 原理

## 核心结论

以 OpenJDK 21 `HashMap` 为边界，它是“桶数组 + 链表/树桶”的非线程安全 Map。`put` 先对 `hashCode` 做高低位混合，用 `(n - 1) & hash` 定位桶；同 key 用引用相等或 `equals` 判断并覆盖 value，不同 key 冲突则进入链表或树桶。默认初始容量 16、负载因子 0.75；元素数超过阈值会扩容。单桶达到树化条件且表容量至少 64 时才树化，否则优先扩容。树桶用于改善严重碰撞下可区分 key 的桶内查找，但不能无条件把所有坏哈希场景都宣称为 O(log n)。

## 1 分钟版

- 结构：`table` 是桶数组；桶内通常是 `Node` 链，达到条件后可变成 `TreeNode` 树桶。
- 定位：`hash(key)` 将 `hashCode()` 与其无符号右移 16 位异或；数组长度为 2 的幂时，用 `(n - 1) & hash` 得到桶下标。
- 插入：空桶直接放；非空桶先按 hash、引用相等或 `equals` 找同 key，找到就替换 value，否则追加节点或进入树插入；新增后 `size > threshold` 会扩容。
- 边界：默认 16 / 0.75，`TREEIFY_THRESHOLD=8`，但 table 小于 64 时 `treeifyBin` 优先 resize。树桶改善的是特定严重碰撞路径，不是“任何坏哈希都稳定 O(log n)”。
- 并发：`HashMap` 本身不同步；多线程存在结构性修改时需要外部同步，或使用适合语义的并发容器。

## 3 分钟版

`HashMap` 的第一步是把 key 映射到较少候选桶。OpenJDK 21 的 `hash` 会把 `hashCode()` 的高位信息混到低位；当 table 长度是 2 的幂时，`(n - 1) & hash` 使用连续低位做桶定位。null key 的混合 hash 为 0，因此走第 0 桶的正常冲突逻辑。

`get` 定位桶后先检查首节点，再在链表或树桶里比较 hash，以及 key 的引用相等或 `equals`。`put` 的主流程是：table 未初始化时先 resize 建表；桶空则新建节点；非空桶先找已有 key，找不到时追加链表节点或调用树节点插入；真正新增后增加 `size`，超过 `threshold` 再 resize。扩容重建桶数组并重新分配节点，因此容量和 load factor 同时影响内存占用、碰撞概率与扩容频率。

OpenJDK 21 常量包括默认容量 16、默认 load factor 0.75、`TREEIFY_THRESHOLD=8`、`UNTREEIFY_THRESHOLD=6`、`MIN_TREEIFY_CAPACITY=64`。这里“8”不是孤立口诀：桶很长但整张表仍小，源码会先扩容而不是立即树化。树节点有更高空间成本，所以树化只为严重碰撞提供退化保护。

复杂度要限定条件。源码说明树桶在 key 具有可比较或可区分关系时能提供更好的桶内查找；它还包含 tie-break 逻辑处理不可直接排序的 key。面试回答可以说“树桶缓解严重碰撞”，但不能把所有完全同 hash 的输入都机械承诺为 O(log n)。正常平均 O(1) 仍依赖 hash 分布、负载和业务 key 特性。

并发是独立边界：源码明确该实现不同步；如果多个线程并发访问且至少一个线程做结构性修改，必须在外部同步。迭代器的 fail-fast 只是 best effort 的错误检测，不能把 `ConcurrentModificationException` 当并发正确性机制。

## 关键细节

- `threshold` 是扩容阈值，通常由 capacity × load factor 得到；预估元素数时应结合负载因子设置初始容量，减少重复 resize。
- 同一 key 不是只比 hash：hash 相同后仍需引用相等或 `equals`；因此 key 的 `equals`/`hashCode` 契约和可变性直接影响可查找性。
- resize 时链表节点可按旧容量对应的新增二进制位拆到原下标或 `index + oldCap`，无需重新调用业务 `hashCode`。
- 树桶分裂后分区较小时可退回普通节点；删除路径也有自己的树形判断，不能简化成“节点删到 6 就一定退树”。
- 树桶是空间换退化保护；正常分布下不应为了“追求 O(log n)”主动制造树化。

## 原理机制

参与状态包括 `Node[] table`、链表 `Node`、`TreeNode`、`size`、`threshold` 和用于结构变更检测的 `modCount`。状态路径为：

`empty table → allocated table → bucket node/list/tree → threshold exceeded → resize/split`。

1. `put` 计算混合 hash，并用 `(n - 1) & hash` 选桶。
2. 桶为空则新建节点；冲突时在首节点、链或树里做 key 匹配，得到“覆盖旧值”或“新增节点”。
3. 新增使 `size` 超过阈值时扩容；容量通常翻倍，节点按旧容量对应的一位拆分到两个桶。
4. 单桶过长且 table 足够大时树化；后续删除或扩容分裂又可能退回普通节点，以控制树节点额外成本。

平均查找成本来自“较均匀的桶分布 + 受控负载”；极端碰撞时树桶提供额外退化保护，但保护能力仍受 key 的 hash/可区分性和具体源码路径约束。扩容则是一次明显的 CPU 与额外数组内存开销。

## 项目经验版

项目映射提示：补入真实 key 类型、预计元素数、是否多线程、是否允许 null、容量预估、是否观察过碰撞/扩容，以及压测或 profile 证据。没有这些事实时，不要虚构 OOM、异常循环或“树化后性能提升多少倍”。

## 常见追问

- 问：为什么容量常设为 2 的幂？答：源码用 `(n - 1) & hash` 定位；容量为 2 的幂时掩码覆盖连续低位，也使扩容分流可由一个新增位判断。
- 问：链表长度到 8 就一定树化吗？答：不一定。OpenJDK 21 还要求 table 容量至少 64；否则 `treeifyBin` 优先 resize。
- 问：树化后是不是所有碰撞都 O(log n)？答：不能这样无条件承诺。源码的树查找和排序会利用 hash、可比较 key 与 tie-break 规则；应表述为树桶改善严重碰撞退化，而不是对任意坏 hash 输入给统一复杂度保证。
- 问：为什么重写 `equals` 通常也要重写 `hashCode`？答：逻辑相等的 key 必须先能落到一致的查找位置，再由 `equals` 确认；两者契约不一致会破坏 put/get 预期。
- 问：fail-fast 能保证并发安全吗？答：不能。它是 best effort 的 bug 检测；并发结构性修改仍需同步或并发容器。

## 易错点

- 不要把“数组 + 链表 + 红黑树”无边界套到所有 Java 版本；这里限定 OpenJDK 21。
- 不要把 0.75、8、64 当成业务常量；它们是当前实现的默认值/阈值。
- 不要把树桶无条件说成“所有坏哈希都 O(log n)”。
- 不要说 `HashMap` 线程安全或依赖 fail-fast 修复并发错误。
- 不要忽略 key 的 `equals`/`hashCode` 契约和可变性。
