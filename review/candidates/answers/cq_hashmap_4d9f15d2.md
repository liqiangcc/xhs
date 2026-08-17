<!-- xhs-answer: {"schema_version":"answer.v1","canonical_id":"cq_hashmap_4d9f15d2","version":1,"status":"draft","updated_at":"2026-08-17","answer_type":"mechanism","quality_tier":"candidate"} -->
# HashMap 原理

## 核心结论

以 OpenJDK 21 `HashMap` 为界，它是“数组桶 + 冲突链表/红黑树”的非线程安全 Map。`put` 先对 `hashCode` 做高低位混合，用 `(n - 1) & hash` 定位桶；同 key 用 `equals` 覆盖 value，不同 key 冲突则进入链表或树。默认初始容量 16、负载因子 0.75；超过阈值扩容。单桶节点数达到树化条件且表容量至少 64 时转红黑树，否则优先扩容；树桶主要缓解过长桶，但源码给出的最坏 O(log n) 边界有前提：key 的 hash 可区分，或同 hash key 可排序，不能外推成所有碰撞都保证对数复杂度。它也不会让 HashMap 变成并发容器。

## 1 分钟版

- 结构：table 是桶数组；桶内先是 Node 链，再在条件满足时是 TreeNode 红黑树。
- 定位：`hash(key)` 将 `hashCode()` 与其无符号右移 16 位异或，数组长度是 2 的幂时用 `(n - 1) & hash` 得到桶下标。
- 插入：空桶直接放；首节点、链表或树内先按 hash 和 `equals` 查找已有 key，找到就替换 value，否则插入新节点；`size > threshold` 后扩容。
- 边界：默认 16 / 0.75；桶达到 8 的树化阈值但 table 小于 64 时不是树化而是 resize。树桶的 O(log n) 最坏界要求 hash 可区分或 key 可排序；大量同 hash 且不可比较的 key 不能承诺该界。HashMap 不同步，结构性并发修改必须在外部同步或改用并发容器。

## 3 分钟版

`HashMap` 解决的是把 key 映射到较少候选桶：先取 key 的 hash，再通过高低位混合减少高位信息完全丢失的风险；当 table 长度为 2 的幂时，`(n - 1) & hash` 等价于按容量取低位，同时比通用取模更直接。null key 的 hash 是 0，因此也走第 0 桶的正常冲突逻辑。

`get` 定位桶后先检查首节点，再在链表或红黑树中比对 hash、引用相等或 `equals`。`put` 的主流程是：table 未初始化先 resize 创建；定位空桶则新建；非空桶先找同 key，没找到则追加到链表或调用树节点插入；最后增加 size，超过 `threshold` 时 resize。扩容会重建桶数组并重新分配节点，所以容量和 load factor 同时决定内存开销与扩容代价。

OpenJDK 21 的常量是默认容量 16、默认 load factor 0.75、`TREEIFY_THRESHOLD=8`、`UNTREEIFY_THRESHOLD=6`、`MIN_TREEIFY_CAPACITY=64`。注意“8”不是孤立口诀：桶过长但总表还小，源码会先 resize。树节点约为普通节点的两倍大小，因此树化只在桶足够长时启用。源码对树桶最坏 O(log n) 的说明带有明确条件：key 要么 hash 不同，要么在 hash 相同时可排序（例如同类并实现合适的 `Comparable`）。如果大量 key 的 hash 完全相同且彼此不可比较，树节点查找可能需要探索多个分支，所以不能把树化概括成任意坏哈希都严格保证 O(log n)。

并发和迭代是另一条边界：源码明确该实现不同步；多线程且至少一个结构性修改时必须外部同步。迭代器是 fail-fast 的 best effort，只能帮助暴露 bug，不能依赖 `ConcurrentModificationException` 保证业务正确性。需要并发更新时按操作语义选择 `ConcurrentHashMap` 或外部锁，而不是给 HashMap 的个别操作加侥幸的读写锁。

## 关键细节

- `threshold` 是扩容阈值，通常由 capacity × load factor 得到；预估元素数时应结合负载因子设置初始容量，避免反复 resize。
- 同一 key 的判断不是只比较 hash：hash 相同后仍要通过引用相等或 `equals` 判定；因此可变 key 会破坏查找预期。
- resize 时链表可能被拆到原下标和 `index + oldCap` 两个位置；这是容量翻倍和二进制位变化带来的分流，不是重新计算业务 hashCode。
- resize 分裂后，每个分区节点数不超过 6 时会退回普通节点；删除路径是否退树取决于源码中的树形条件，不能把它简化成统一的“删到 6 就退树”。
- TreeNode 主要按 hash 排序；hash 相同时，满足可比较条件才可用比较顺序帮助定位。相同 hash 且不可比较时，查找路径可能需要搜索两个子树，因此复杂度承诺必须带上源码的可区分/可排序前提。

## 原理机制

参与者是 `Node[] table`、链表 Node、TreeNode、`size`、`threshold` 和 `modCount`。状态路径为 `empty table → allocated table → bucket node/list/tree → resize/split`：

1. 调用 `put`，计算混合 hash，并按 `(n - 1) & hash` 找桶。
2. 桶为空则创建 Node；冲突时在首节点、链或树中做 key 比较，得到“覆盖旧值”或“新增节点”。
3. 新增导致 `size` 越过阈值时扩容；容量通常翻倍，节点按旧容量对应的一个二进制位拆分到两个桶。
4. 碰撞很长且 table 足够大时链转树；删除/分裂后又可能 untreeify，控制 TreeNode 的额外内存成本。

平均 O(1) 依赖良好 hash 分布和受控负载。树桶在 key 的 hash 可区分或 key 可排序时提供源码所述的最坏 O(log n) 边界；相同 hash 且不可排序时不应承诺该复杂度。扩容仍是一次明显的时间与内存开销。hash 分布、初始容量和 key 不可变性是比死记阈值更重要的输入条件。

## 项目经验版

项目映射提示：补入真实 key 类型、预计元素数、是否多线程、是否允许 null、容量预估和压测中的碰撞/扩容证据。如果担心恶意或异常 hash，还要构造“不同 hash”“同 hash 且 Comparable”“同 hash 且不可比较”三类 key 做基准，避免只看到树化就宣称所有碰撞都 O(log n)。没有这些事实时，不要虚构 OOM、死循环或性能优化事故。

## 常见追问

- 问：为什么容量常设为 2 的幂？答：源码用 `(n - 1) & hash` 定位；容量为 2 的幂时掩码覆盖连续低位，并使扩容分流可由一个新增位判断。
- 问：链表长度到 8 就一定树化吗？答：不一定。OpenJDK 21 还要求 table 容量至少 64；否则 `treeifyBin` 会先触发 resize。
- 问：树化后任何碰撞查询都是 O(log n) 吗？答：不是。源码的最坏 O(log n) 说明要求 key 的 hash 可区分，或同 hash key 可排序；同 hash 且不可比较时查找可能需要探索树的多个分支，不能无条件承诺对数界。
- 问：为什么重写 `equals` 要重写 `hashCode`？答：同一逻辑 key 必须先落到可查到的桶，再由 equals 确认；两者不一致会让 put/get 的定位和匹配脱节。
- 问：fail-fast 能保证并发安全吗？答：不能。源码定义它为 best effort 的 bug 检测；并发结构性修改仍需同步或并发容器。

## 易错点

- 不要把“数组 + 链表 + 红黑树”说成所有 Java 版本和所有桶都固定如此；本文限定 OpenJDK 21，且树化受阈值和容量条件约束。
- 不要把 0.75、8、64 当业务常量；它们是该实现的默认/源码阈值，容量预估要结合实际负载。
- 不要把“树化”直接等同于“所有碰撞场景保证 O(log n)”；源码的复杂度边界取决于 hash 可区分或 key 可排序。
- 不要说 HashMap 线程安全或依赖 fail-fast 纠正并发错误。
- 不要忽略 key 的 `equals`/`hashCode` 契约和可变性，否则再好的桶结构也无法保证可查找性。
