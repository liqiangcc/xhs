<!-- xhs-answer: {"schema_version":"answer.v1","canonical_id":"cq_stringbuffer_8b8caf0d","version":1,"status":"draft","updated_at":"2026-07-11","answer_type":"concept","quality_tier":"candidate"} -->
# StringBuilder 和 StringBuffer 的区别

## 核心结论

两者都是可变字符序列，API 大体兼容；Java SE 21 中 `StringBuffer` 的方法是同步的，适合确实由多个线程共享同一可变缓冲区的场景；`StringBuilder` 不保证同步，单线程或线程封闭场景优先使用它。不要仅因“代码在多线程服务里”就选 `StringBuffer`：关键是该实例是否被并发共享。

## 1 分钟版

- 共同点：都支持 `append`、`insert`，都有 capacity，容量不足时会自动增长。
- 并发：`StringBuilder` 不保证线程安全；`StringBuffer` 提供同步的可变字符操作。
- 选择：局部变量、方法内拼接、线程封闭对象用 `StringBuilder`；多个线程必须共同修改同一缓冲区且确实需要其同步语义时才考虑 `StringBuffer`。
- 边界：`StringBuffer` 的同步不自动把“读取、判断、修改”多步业务操作变成原子事务；跨方法复合操作仍须自行协调。

## 3 分钟版

两者解决的是反复修改字符序列，区别首先是同步契约而非“谁绝对更快”。Java SE 21 文档说明 `StringBuilder` 是与 `StringBuffer` API 兼容、但不保证同步的可变字符序列；单线程使用时推荐优先 `StringBuilder`。`StringBuffer` 是线程安全的可变字符序列，其操作是同步的。

两者的 `append` 都在末尾追加，`insert` 在指定位置插入；都维护 capacity，字符长度未超过容量时无需重新分配内部缓冲区，超出时自动扩容。已知拼接规模时可传入初始 capacity 或调用 `ensureCapacity`，但不要把特定 JDK 的扩容倍率当成 API 契约。

选型先判断所有权。请求处理中的局部拼接器通常不共享，选 `StringBuilder`；若一个实例确实被多个线程共同改写且仅需要单次方法调用的同步，可评估 `StringBuffer`。若需要“检查长度后追加、再发布结果”这类复合不变量，应把完整临界区或更高层并发设计说清楚，不能只依赖单个同步方法。

## 关键细节

- `StringBuilder` 文档明确不适合多线程并发使用；需要同步时建议使用 `StringBuffer`。
- 两者的 `append`/`insert` 都是可变更新；与不可变 `String` 的比较应另建话题，不能混为“字符串是否可变”。
- `StringBuilder` 实现 `Comparable` 但不重写 `equals`；不要把其自然顺序与 `equals` 等同性混为一谈，尤其不要把它当作有稳定值语义的有序集合键。
- 容量是缓冲空间，不等于当前 `length`；容量相关的具体增长策略不应硬编码为跨版本事实。

## 原理机制

调用 `append` 时，字符追加到当前可变序列尾部；容量足够时复用缓冲空间，不足时自动扩大。`StringBuffer` 通过同步方法让单次操作互斥，代价是并发协调；`StringBuilder` 没有该同步保证，因此调用者必须保证实例不被并发修改。同步解决的是对同一对象的访问竞争，不替业务定义完整的多步原子性。

## 项目经验版

项目映射提示：说明拼接器是否跨线程共享、生命周期是否局限在请求内、是否有容量预估和并发测试。没有这些证据时，不要编造把 `StringBuffer` 换成 `StringBuilder` 后的吞吐提升。

## 常见追问

- 问：服务是多线程的，局部 `StringBuilder` 能用吗？答：能否使用取决于该实例是否共享；线程封闭的局部变量没有并发访问同一实例。
- 问：`StringBuffer` 能保证一段多步逻辑原子吗？答：单个同步方法有同步语义，但跨多个调用的检查和更新仍要由调用方组织完整临界区。
- 问：什么时候预设 capacity？答：已知或可合理估计最终长度时可预留，以减少增量扩容；不能依赖未承诺的具体增长倍率。
- 问：`StringBuilder` 能按 `equals` 放入 `TreeSet` 吗？答：其自然顺序与 `equals` 不一致，文档要求对此类有序集合使用保持谨慎。

## 易错点

- 不要把“应用是多线程”直接等同于“每个拼接器必须用 StringBuffer”。
- 不要把 StringBuffer 的单方法同步误说成业务复合操作自动原子。
- 不要把某个 JDK 的容量增长公式当作通用规范。
- 不要把 StringBuilder 的比较顺序当作等同性。
