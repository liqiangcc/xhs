<!-- xhs-answer: {"schema_version":"answer.v1","canonical_id":"cq_equals_hashcode_e7fe32f7","version":2,"status":"needs_update","updated_at":"2026-07-11","quality_tier":"curated_audit_failed","audit_failure":"missing_evidence"} -->
# 为什么重写 equals 必须重写 hashCode？

## 核心结论

Java 约定 equals 相等的对象必须有相同 hashCode，否则 HashMap/HashSet 可能在不同桶中找不到逻辑相等对象；hash 相同则不要求 equals 相等，冲突由桶内比较解决。

## 1 分钟版

- equals 需满足自反、对称、传递、一致及对 null 返回 false。
- hashCode 在参与 equals 的字段不变期间应稳定，并使用相同字段计算。
- 作为 hash key 后修改这些字段，会导致对象仍在旧桶却无法按新 hash 找到。

## 3 分钟版

继承层次中的 equals 容易破坏对称/传递，可用 final 值对象或组合。IDE/record 可生成但仍要确认业务身份字段。 回答时先统一比较维度，再给选择条件与反例；定义本身不是终点，必须说明代价和不适用边界。

## 关键细节

- equals 需满足自反、对称、传递、一致及对 null 返回 false。
- hashCode 在参与 equals 的字段不变期间应稳定，并使用相同字段计算。
- 作为 hash key 后修改这些字段，会导致对象仍在旧桶却无法按新 hash 找到。

## 原理机制

从参与对象、状态变化和主流程展开，再补充并发/故障保证与资源开销。 Java 约定 equals 相等的对象必须有相同 hashCode，否则 HashMap/HashSet 可能在不同桶中找不到逻辑相等对象；hash 相同则不要求 equals 相等，冲突由桶内比较解决。

## 项目经验版

项目映射提示：从真实代码或架构中选择一个使用点，补齐选择条件、替代方案和验证指标；没有事实时不虚构收益。

## 常见追问

- 问：hash 相同对象一定相等吗？答：不一定，hash 空间有限，桶内还要 equals 判定。
- 问：只重写 hashCode 可以吗？答：不能建立业务相等语义，Object.equals 仍按引用比较。
- 问：可变对象能当 key 吗？答：可以但参与 hash/equality 的字段在存放期间必须不变。

## 易错点

- 不要只背定义而不说明选择条件。
- 不要把常见实现说成跨版本唯一结论。
- 不要把 hashCode 当作全局唯一 ID。
