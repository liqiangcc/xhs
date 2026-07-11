<!-- xhs-answer: {"schema_version":"answer.v1","canonical_id":"cq_cas_64fa0b00","version":1,"status":"draft","updated_at":"2026-07-11","answer_type":"mechanism","quality_tier":"candidate"} -->
# CAS 的原理、ABA 问题与解决方案

## 核心结论

CAS（Compare-And-Set）把“当前值仍等于预期值吗”和“写入新值”合成一次原子条件更新：相等则成功写入，否则失败并由调用方决定重读、重试或返回冲突。ABA 的关键不是值曾经变化就必然出错，而是业务若只比较当前引用/值，`A → B → A` 会让 CAS 重新看到 A，无法区分它是否经历过中间变化；此时可把版本号/时间戳作为比较条件的一部分，例如 Java 的 `AtomicStampedReference` 同时比较 reference 与 stamp。

## 1 分钟版

- CAS 的输入是期望值与新值；当前值匹配期望值时原子更新，失败说明状态已不是本次读取时的状态。
- CAS 失败只表示当前状态不满足本次 expected 条件；调用方必须明确定义失败后是重新读取还是返回冲突，不能把失败当作已提交。
- ABA 是“当前值相同但历史变化对业务有意义”的问题：线程读到 A，别的线程改成 B 又改回 A，普通 CAS 仍可能成功。
- 若业务只关心当前值，ABA 未必是问题；若必须识别版本变化，比较 `(value, stamp)`，每次有效变更同步推进 stamp，CAS 同时校验两者。

## 3 分钟版

CAS 的状态流是：`读取 observed → 计算 candidate → compareAndSet(observed, candidate) → 成功提交或失败重试/退出`。Java SE 21 的 `AtomicReference.compareAndSet` 按引用恒等 `==` 比较 current 与 expected，匹配时原子设置新值并返回成功。因此读取与写入之间没有把整个业务流程锁住；竞争者先完成更新时，本次 CAS 失败，调用方必须重新读取和计算，不能继续使用旧推导。

ABA 发生在“只比较当前 reference 是否还是 expected”不足以表达业务前提时。设线程 T1 读到 A；T2 完成 `A→B→A`；T1 再按 expected=A 发起普通 CAS，API 只比较此刻 reference 是否 `== A`，它无法从这个比较本身知道中间状态。若 A 的回归不改变业务语义，例如只关心当前空位是否可用，不必为了名词强加版本号；若中间变化意味着资源已被取走又归还、节点已被复用等，必须把版本纳入条件。

Java 的 `AtomicStampedReference.compareAndSet` 只有在 current reference 与 expected reference 都以 `==` 匹配、且 current stamp 等于 expected stamp 时，才原子更新 reference 和 stamp。于是将状态建模成 `(reference, stamp)`：T1 读取 `(A, 7)`，T2 即使把 reference 改回 A 也把 stamp 推进为 9，T1 带 `(A, 7)` 的 CAS 会失败并重新判断。stamp 的正确性前提是每次业务上相关的变更都与 stamp 的更新一同进入这个条件更新；若遗漏该状态迁移，API 本身不能补回遗漏的业务版本。

## 关键细节

- Java SE 21 `AtomicReference.compareAndSet` 的匹配是 reference `==`，不是 `equals`；可变对象内部字段变化不等于 reference 已变化。
- `AtomicStampedReference.compareAndSet` 同时校验 reference 与 stamp，并在成功时原子设置二者；它是“版本作为状态”的 API 支撑，不替业务定义何时递增版本。
- ABA 只在中间状态对本次决策有意义时是缺陷。若业务断言仅为“当前仍是 A”，普通 CAS 的可见状态已足够。
- `compareAndSet` 的失败是 API 的正常返回路径；必须把重读、重算或返回冲突写入调用方状态机，不能把旧候选值继续当作已验证状态。

## 原理机制

普通 CAS 的可验证前提只有 `current == expected`，成功后状态变为 `newValue`。因此它保证的是一次条件写的原子性，不是“从读取到提交期间没有任何状态历史”。引入 stamp 后，前提变为 `(currentReference == expectedReference) ∧ (currentStamp == expectedStamp)`；参与 stamp 更新的中间变更会破坏旧前提，使旧 CAS 返回失败。额外状态是 stamp；失败后的重读、重算或冲突返回属于调用方状态机，而不是 API 自动替它完成的事务。

## 项目经验版

项目映射提示：补充真实共享状态、状态迁移图、失败后是否重试、并发度、冲突率、ABA 中间变化为什么有业务意义、stamp 生成规则、监控与降级策略。没有这些事实时，不要虚构“CAS 替换锁后吞吐量提升了多少”。

## 常见追问

- 问：CAS 失败代表什么？答：只表示当前状态不再满足本次 expected 条件；应重新读取后再计算，或按业务返回冲突，不能直接沿用旧候选值。
- 问：ABA 一定要用版本号吗？答：不一定。先判断中间变化是否影响业务正确性；只有需要识别历史变化时，才把版本/stamp 纳入 CAS 条件。
- 问：`AtomicStampedReference` 如何发现 ABA？答：它同时比较 reference 与 stamp。中间变更若同步更新 stamp，即使 reference 回到 A，旧 stamp 也不匹配。
- 问：CAS 成功是否等于整个业务操作成功？答：不等于。它只证明这一次 reference（以及使用 stamped API 时的 stamp）满足条件并完成更新；多步骤业务的其他不变量仍需由调用方单独建模和校验。

## 易错点

- 不要把 CAS 的 `==` 比较说成对象内容相等，也不要忽略 expected 与 newValue 的身份语义。
- 不要把 ABA 描述成“只要 A 回来 CAS 就一定错”；错误取决于中间变化是否破坏业务前提。
- 不要只加一个 stamp 字段却不定义哪些迁移必须推进它；那样无法建立版本检测的前提。
- 不要把 CAS 返回 `false` 当成可以忽略的分支；旧 observed 已不再证明当前状态，必须重新读取、重算或明确返回冲突。
