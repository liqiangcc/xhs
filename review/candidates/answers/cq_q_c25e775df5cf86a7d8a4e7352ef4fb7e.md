<!-- xhs-answer: {"schema_version":"answer.v1","canonical_id":"cq_q_c25e775df5cf86a7d8a4e7352ef4fb7e","version":1,"status":"draft","updated_at":"2026-08-28","answer_type":"coding","quality_tier":"candidate"} -->
# 手写 EventEmitter：on / emit / once / off

## 核心结论

原题只要求实现 `on`、`emit`、`once`、`off`，没有规定 Node.js `EventEmitter` 的全部兼容语义。这里采用一个明确且可测试的最小契约：同一事件按注册顺序执行；`emit` 透传参数并以 emitter 作为 `this`；`once` 在第一次调用前先注销，因此监听器内部同步重入同一事件也只执行一次；`off(event, listener)` 删除该事件下所有与这个原始函数相同的注册，包括 `once` 注册；每次 `emit` 使用开始时的监听器快照，因此本轮执行期间的 `on/off` 只影响后续轮次；监听器异常直接向调用方抛出。

## 1 分钟版

- 用 `Map<event, ListenerRecord[]>` 保存事件到监听器列表，数组保留注册顺序。
- `on` 追加普通监听器记录；`once` 追加 `once: true` 的记录。
- `emit` 先复制监听器快照，再按顺序调用；遇到 `once` 记录时先从实时列表删除再调用，避免同步重入重复触发。
- `off` 按原始函数 identity 过滤，因此传给 `once` 的原函数也能直接注销。
- 注册通常 O(1)，一次 `emit` 是 O(k)，`off` 需要扫描该事件监听器，为 O(k)。

## 3 分钟版

```javascript
class EventEmitter {
  constructor() {
    this.events = new Map();
  }

  on(event, listener) {
    this.#assertListener(listener);
    const list = this.events.get(event) ?? [];
    list.push({ listener, original: listener, once: false });
    this.events.set(event, list);
    return this;
  }

  once(event, listener) {
    this.#assertListener(listener);
    const list = this.events.get(event) ?? [];
    list.push({ listener, original: listener, once: true });
    this.events.set(event, list);
    return this;
  }

  off(event, listener) {
    this.#assertListener(listener);
    const list = this.events.get(event);
    if (!list) return this;
    const next = list.filter(record => record.original !== listener);
    if (next.length === 0) this.events.delete(event);
    else this.events.set(event, next);
    return this;
  }

  emit(event, ...args) {
    const list = this.events.get(event);
    if (!list || list.length === 0) return false;
    const snapshot = [...list];
    for (const record of snapshot) {
      if (record.once) this.#removeRecord(event, record);
      record.listener.apply(this, args);
    }
    return true;
  }

  #removeRecord(event, target) {
    const list = this.events.get(event);
    if (!list) return;
    const next = list.filter(record => record !== target);
    if (next.length === 0) this.events.delete(event);
    else this.events.set(event, next);
  }

  #assertListener(listener) {
    if (typeof listener !== 'function') {
      throw new TypeError('listener must be a function');
    }
  }
}
```

这里把“原始 listener”和“本次注册 record”分开保存。`off` 面向原始函数 identity；`once` 触发后的精确删除面向 record identity。这样既能让 `off(event, originalFn)` 取消一次性监听器，又不会在触发某个 `once` 时误删同一函数的其他注册实例。

## 关键细节

- **once 先删再调**：若先执行 listener 再删除，而 listener 内同步 `emit` 同一事件，它仍在实时列表里，会重复触发。
- **emit 使用快照**：遍历实时数组时执行 `on/off` 会改变索引和长度，容易产生跳过、重复或新监听器提前参与本轮。快照固定当前轮次的观察集合。
- **重复注册的 off 语义**：原题没规定。这里明确选择一次 `off` 删除同一原始函数的全部注册；若面试官要求只删一个实例，可以按注册记录精确删除。
- **once 与 off 的关系**：record 保存 `original`，所以无需暴露包装函数也能用原函数取消 `once`。
- **异常语义**：这里不吞 listener 异常；某个监听器抛错时 `emit` 立即向上抛出，后续监听器不再执行。
- **返回值**：`on/once/off` 返回 `this`，`emit` 返回本轮开始时是否存在监听器；这些是实现选择，不是来源事实。

## 原理机制

EventEmitter 的核心是维护两个状态不变量：同一事件的注册顺序稳定；一次触发有明确的迭代视图。实时列表负责跨轮次状态，快照负责当前轮次视图；`once` 在调用前修改实时列表，所以当前快照完成这次调用后，任何重入或下一轮都看不到该记录。

这也解释了为什么不能简单遍历实时数组然后事后清理一次性监听器：用户回调可以同步修改 emitter，甚至递归触发同一事件。先定义“本轮快照 + 调用前移除 once”的状态转移，行为才可推导和测试。

## 项目经验版

来源没有提供真实项目中的事件总线、内存泄漏或故障案例，不能虚构。真实项目里还要根据场景决定监听器数量限制、全量清理、异步监听器、错误隔离、通配事件、优先级和调试元数据；这些都不是原题四个方法的必需语义，应在需求明确后再扩展。

## 常见追问

- 问：为什么不用 `Set`？答：如果允许同一函数重复注册，`Set` 会去重；数组把每次注册表示成独立 record，也保留顺序。
- 问：`once` 为什么不只写成 `on(event, wrapper)`？答：可以，但必须保存 wrapper 与 original 的关系，否则 `off(event, originalFn)` 找不到一次性注册。
- 问：emit 中新增 listener 会立刻执行吗？答：本契约不会，因为当前轮使用开始时的快照；它从下一次 emit 才参与。
- 问：emit 中 off 另一个 listener，被删的 listener 本轮还执行吗？答：如果它已在本轮快照中仍会执行；删除影响实时列表和后续轮次。
- 问：如何避免 once 重入两次？答：调用 once listener 前先按 record identity 从实时列表删除。
- 问：事件很多会不会占内存？答：最后一个 record 被删除后清掉 Map key；更复杂的泄漏检测属于额外需求。

## 易错点

- `once` 调完 listener 才删除，遇到同步重入时执行两次。
- 遍历实时数组同时 `splice`，导致索引错位或行为依赖修改顺序。
- 给 `once` 包匿名函数却不保存 original，导致 `off(event, originalFn)` 失效。
- 用 `Set` 后无意改变重复注册语义。
- 没定义 `off` 对重复注册删一个还是全部，却把实现偏好当成原题要求。
- 为了“健壮”吞掉 listener 异常，使调用方无法观察失败。
