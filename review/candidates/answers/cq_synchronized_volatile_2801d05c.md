<!-- xhs-answer: {"schema_version":"answer.v1","canonical_id":"cq_synchronized_volatile_2801d05c","version":1,"status":"draft","updated_at":"2026-08-18","answer_type":"concept","quality_tier":"candidate"} -->
# synchronized 和 volatile 的区别

## 核心结论

`synchronized` 和 `volatile` 都是 Java 内存模型里的同步手段，但解决的问题层级不同：`synchronized` 用 monitor 提供**互斥 + happens-before**，适合把一组读写或复合不变量保护成临界区；`volatile` 不提供互斥，它通过“对某个 volatile 字段的写 happens-before 后续对同一字段的读”发布该字段及此前线程内动作的可见结果，适合状态标志、配置引用等“不依赖读-改-写原子性”的发布场景。`volatile` 不能把 `count++` 变成原子操作，也不能单独维护多个变量之间的不变量。

## 1 分钟版

- **互斥性**：`synchronized` 获取对象 monitor；持锁期间其他线程不能取得同一 monitor。`volatile` 读写是同步动作，但没有“只有一个线程能进入”的临界区。
- **可见性/顺序**：monitor 的 unlock happens-before 后续 lock；volatile 写 happens-before 后续对同一字段的 volatile 读。两者都能建立跨线程 happens-before，不能说“只有 volatile 保证可见性”。
- **原子性边界**：`synchronized` 可以让锁内的一组操作对遵守同一锁协议的线程互斥执行；`volatile` 只改变字段读写的内存语义，`i++` 仍包含取值、加一、写回，多个线程会丢更新。
- **适用场景**：单个状态的发布/停止标志且不存在复合不变量时可用 `volatile`；余额扣减、check-then-act、多个字段必须一起变化等场景需要锁或其他原子/并发原语。
- **实现讨论**：面试可解释 happens-before 和同步动作；不要把某种 CPU 的“内存屏障指令序列”当成 Java 规范的固定契约。

## 3 分钟版

先统一比较维度。`synchronized` 是基于 monitor 的互斥同步。进入同步块前线程必须成功执行 lock；退出时无论正常还是异常都会 unlock。JLS 规定，同一 monitor 的 unlock synchronizes-with 后续 lock，因此只要相关共享状态都遵守同一把锁，既可以避免临界区并发执行，又可以沿 happens-before 推理前一个持锁线程的写入对后一个持锁线程可见。

`volatile` 是字段级同步。JLS 把 volatile read/write 都列为 synchronization actions，并规定对字段 `v` 的 volatile 写 synchronizes-with 后续线程对同一 `v` 的 volatile 读。再结合程序顺序和 happens-before 的传递性，常见发布模式是：线程 A 先写普通数据，随后 `ready = true`（volatile）；线程 B 读到 `ready == true` 后，再读取那些在 volatile 写之前完成的数据，就可以按 JMM 的 happens-before 关系推理其可见性。

但 `volatile` 没有互斥。它不会阻止两个线程同时执行围绕该字段的逻辑，也不会把“读取旧值 → 计算 → 写新值”合并为一个不可分割动作。JLS 对 postfix `++` 的运行时语义明确包含读取变量值、加 1、再把和写回，因此 `volatile int count; count++;` 在多个线程并发时仍可能发生两个线程读到同一个旧值再互相覆盖。这里的关键不是“volatile 写不原子”，而是**整个读-改-写复合操作不是一个原子临界区**。

因此选型看不变量。停止标志 `volatile boolean stopped`、一次替换不可变配置引用等场景，只要正确性只依赖单个发布变量且没有 check-then-act，可用 `volatile` 降低锁的控制复杂度。若“库存 > 0 才扣减”“余额和流水必须一起更新”“两个字段必须保持和为常量”，则需要把检查与修改放进同一互斥/原子协议，通常是 `synchronized`、`Lock`、原子类或更高层并发结构，不能只把字段改成 volatile。

关于“内存屏障”，Java 规范层面最稳妥的答案是 JMM 的 synchronization order、synchronizes-with 和 happens-before。具体 JVM 会把这些语义映射到目标处理器需要的编译器/CPU 约束，但具体屏障或指令序列属于 JVM、JIT 和硬件实现细节，不能把某个平台的实现记忆成所有 JDK/CPU 的固定规则。

## 关键细节

- Java SE 21 JLS 把 volatile read、volatile write、monitor lock 和 monitor unlock 都列为 synchronization actions。
- 同一 monitor 的 unlock synchronizes-with 后续 lock；对同一 volatile 字段的写 synchronizes-with 后续读。两条规则都可形成 happens-before。
- `synchronized` 的互斥只约束竞争同一 monitor 的线程；JLS 明确指出，拿到对象锁本身不会阻止别的线程绕开锁直接访问未同步字段。因此正确性依赖一致的同步协议。
- `volatile` 是字段修饰符，不是临界区。它没有 monitor owner，也没有“持有 volatile”这一状态，不能直接表达多个操作必须一起完成。
- `count++` 的规范语义是取得变量值、加 1、再存回；即使变量是 volatile，也不能据此获得整个复合动作的互斥性。
- 不要把“volatile = 可见性、synchronized = 原子性”当成完整答案：`synchronized` 同样建立可见性/顺序关系，而 volatile 的关键边界是没有互斥和复合操作原子性。
- 本答案以 Java SE 21 JLS 的语言/内存模型契约为边界，不承诺某个 HotSpot 版本或某种 CPU 的固定屏障指令。

## 原理机制

JMM 的推理链路可以写成两条。

第一条是 monitor：线程 A 在 `synchronized(lock)` 中修改共享状态 → A 对 `lock` 执行 unlock → 线程 B 后续成功 lock 同一 monitor → B 在临界区读取共享状态。规范的 synchronizes-with 边加上程序顺序形成 happens-before，所以只要访问遵守同一锁协议，B 能按该顺序观察 A 的受保护写入，同时 monitor 所有权保证临界区不会由两个持有同一锁的线程并发执行。

第二条是 volatile 发布：A 写普通数据 → A 写 `volatile ready=true` → B 后续读同一个 volatile `ready` 并观察到该发布 → B 读取普通数据。volatile 写到后续读建立 synchronizes-with，再由 happens-before 传递性把 A 在发布前的动作与 B 在观察发布后的动作连接起来。这个链路没有“B 独占一段代码”的状态，因此两个线程仍能并发执行 `count++`、check-then-act 或跨多个变量的更新。

资源和失败边界也来自这个差异：monitor 竞争可能让线程等待，锁范围过大还会扩大串行区；volatile 不建立互斥等待，但若用它承载本应由原子事务保护的复合不变量，会得到逻辑竞态而不是更高效的正确程序。性能选择应在正确性模型确定后再测，而不是先按“锁慢、volatile 快”决定。

## 项目经验版

项目映射提示：先写出共享状态的不变量，再决定同步原语。例如“服务收到停止信号后让工作线程尽快观察并退出”，若只有一个布尔状态且没有与其他状态绑定的复合条件，可考虑 `volatile`；而“剩余名额大于 0 才扣减并生成成功记录”包含检查和修改的原子边界，仅把 `remaining` 声明成 volatile 不够。真实项目还应记录目标 JDK、并发度、竞争比例和失败表现，再通过压力测试/线程诊断验证，而不是声称某个原语天然更快。

## 常见追问

- 问：`volatile` 能保证 `i++` 线程安全吗？答：不能。`i++` 的规范语义包含读取旧值、计算和写回；volatile 使相关读写具有同步语义，但不会把整个复合操作变成一个互斥的原子步骤。
- 问：`synchronized` 也保证可见性吗？答：是。同一 monitor 的 unlock happens-before 后续 lock，所以正确使用同一锁保护共享状态时，前一个临界区的写入可以通过 happens-before 对后一个临界区可见。
- 问：什么时候 volatile 足够？答：当正确性可以由一个字段的独立读写/发布表达，并且没有依赖当前值再更新、跨字段不变量或必须一次性执行的一组操作时。停止标志和不可变快照引用是典型思路，但仍要验证具体协议。
- 问：volatile 能替代锁吗？答：只能在不需要互斥和复合原子性的场景替代部分锁用途。需要 check-then-act、累加、跨字段一致性时，要选择锁、原子类或更高层并发结构。
- 问：volatile 底层是不是固定插入 StoreStore/StoreLoad 等屏障？答：不要把特定 JVM/架构的实现细节当 Java 规范。JLS 规定的是 volatile 同步动作、synchronizes-with 和 happens-before；JVM 如何映射到机器屏障取决于实现与硬件。

## 易错点

- 不要说“volatile 保证原子性”。更准确地说，单次 volatile 读/写受 JMM 规则约束，但 `++`、检查后更新和跨字段不变量仍不是一个原子事务。
- 不要说“synchronized 只保证原子性，不保证可见性”。monitor unlock/lock 本身就建立 synchronizes-with/happens-before。
- 不要把 volatile 理解成“每次都直接读主内存”或 synchronized 理解成“强制刷新 CPU 缓存”。这是容易失真的硬件化比喻，规范契约应使用 happens-before。
- 不要用 volatile 保护多个字段之间的关系；一个 volatile 发布字段可以发布此前状态，但这与“任意线程可并发修改那些状态仍保持不变量”是两件事。
- 不要为了性能先把锁换成 volatile。先证明无互斥/复合原子性需求，再做基于目标 JDK 和负载的性能测量。
