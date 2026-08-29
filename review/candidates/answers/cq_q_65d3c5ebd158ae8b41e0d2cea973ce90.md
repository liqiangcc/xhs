<!-- xhs-answer: {"schema_version":"answer.v1","canonical_id":"cq_q_65d3c5ebd158ae8b41e0d2cea973ce90","version":1,"status":"draft","updated_at":"2026-08-30","answer_type":"mechanism","quality_tier":"candidate"} -->
# Spring 如何解决循环依赖问题？

## 核心结论

Spring Framework 解决的不是“所有循环依赖”，而是**一部分单例 Bean 在实例已经创建、但属性填充和初始化尚未完成时发生的循环引用**。核心做法是：Bean 实例化后，如果满足单例、正在创建且允许循环引用等条件，就先注册一个“早期引用工厂”；另一个 Bean 在注入它时，可以从单例注册表中拿到这个早期引用，从而打断 `A -> B -> A` 的创建闭环。等 A 完成属性填充和初始化后，再把最终单例放入正式单例表。

面试里常说的“三级缓存”，对应当前 Spring Framework 源码里的三个结构：`singletonObjects`、`earlySingletonObjects`、`singletonFactories`。第三层工厂不是为了“多一层缓存性能”，而是为了**延迟创建早期引用，并允许 `SmartInstantiationAwareBeanPostProcessor` 在真正需要早期引用时提供一致的早期代理引用**。

这个机制有边界：**构造器之间的循环依赖不能靠它解决**，因为构造器执行前连可提前暴露的实例都还没有；prototype 等非单例场景也不能直接套用这套单例早期暴露机制。Spring 官方文档也建议优先重构循环依赖，而不是把它当成推荐设计。

## 1 分钟版

可以按“为什么能解、三级结构分别做什么、什么情况解不了”回答：

1. A 开始创建，先完成实例化，但还没完成依赖注入和初始化。
2. 如果 A 是符合条件的单例，Spring 会把一个 `ObjectFactory` 放进 `singletonFactories`，这个工厂能在需要时返回 A 的早期引用。
3. A 填充属性时发现依赖 B，于是开始创建 B。
4. B 填充属性时又依赖 A。此时 A 已经实例化，所以 Spring 可以在 A“正在创建”的条件下查单例注册表：
   - 先找 `singletonObjects`；
   - 没有则看 `earlySingletonObjects`；
   - 还没有则调用 `singletonFactories` 里的工厂创建早期引用，并把结果转入 `earlySingletonObjects`。
5. B 拿到 A 的早期引用后可以完成创建；随后 A 再拿到完成后的 B，最终 A 也完成初始化并进入 `singletonObjects`。

三个结构的角色：

- `singletonObjects`：已经完成注册的最终单例；
- `earlySingletonObjects`：已经真正生成出来的早期引用；
- `singletonFactories`：延迟生成早期引用的工厂。

边界：

- 构造器 `A(B)`、`B(A)` 这种循环通常无法这样打断；
- 这条路径针对单例早期暴露，不是 prototype 或任意对象图的通用解法；
- 有 AOP/代理时，早期引用需要通过 `getEarlyBeanReference` 等钩子保持与最终包装语义一致。

## 3 分钟版

以单例 A、B 的属性注入循环为例：

`A -> B -> A`

### 1. 创建 A：先实例化，后注入

Spring 创建 A 时，先得到 A 的实例。此时 A 还没有完成属性填充和初始化，但“对象本身已经存在”。

对于满足条件的单例，`AbstractAutowireCapableBeanFactory` 会在继续填充依赖前注册一个早期引用工厂，大致可以理解为：

```text
singletonFactories[A] = () -> getEarlyBeanReference(A)
```

这一步是后面能打断循环的关键。它不是直接把 A 当最终 Bean 发布出去，而是先保留一个“如果别人现在确实需要 A，就生成早期引用”的入口。

### 2. A 依赖 B，于是开始创建 B

A 在属性填充阶段发现依赖 B，于是容器转去创建 B。

B 同样先实例化，然后在属性填充时发现又依赖 A。

### 3. B 查找 A 的早期引用

此时 A 还没完成，所以 `singletonObjects` 中没有最终 A。

Spring 的单例注册表在确认 A 正处于创建过程中后，可以继续查早期状态：

```text
singletonObjects
    ↓ miss
earlySingletonObjects
    ↓ miss
singletonFactories
    ↓ invoke ObjectFactory
early reference
```

工厂第一次被真正调用后，得到的早期引用会进入 `earlySingletonObjects`，相应工厂不再继续充当待生成入口。

于是 B 得到了一个可以引用的 A，B 的依赖闭环被打断，B 可以继续初始化直至完成。

### 4. 回到 A，完成最终发布

B 完成后，A 的依赖 B 也就满足了。A 继续完成初始化流程，最终正式注册到 `singletonObjects`。

因此本质顺序是：

```text
instantiate
→ register early-reference factory
→ populate dependencies
→ initialize
→ publish final singleton
```

循环能被打断的前提，是某个节点已经完成“实例化”，所以能有一个早期对象引用提供给另一边。

### 5. 为什么需要 `singletonFactories`

如果只有“最终对象表 + 早期对象表”，也可以想象提前把原始 A 放进去，但这会丢掉一个很重要的控制点：**早期引用可能需要经过 BeanPostProcessor 的早期引用钩子**。

当前 Spring Framework 的 `getEarlyBeanReference` 会让 `SmartInstantiationAwareBeanPostProcessor` 有机会提供早期引用。这样，在存在自动代理等基础设施时，容器可以尽量让依赖方拿到与后续包装语义一致的引用，而不是无条件先泄露 raw bean。

因此第三层工厂的价值之一是：

- 延迟到“真的有人循环依赖它”时才生成早期引用；
- 把早期引用生成交给统一钩子；
- 避免简单地把原始对象直接塞进早期表。

## 关键细节

- **“三级缓存”是面试口语**：源码里本质是三个单例暴露/注册结构，不要把它们都描述成普通意义上的缓存。
- **只在已经实例化之后才有早期引用**：所以构造器到构造器的环没有可提前暴露实例，官方文档明确指出这类构造器循环会失败并可能出现 `BeanCurrentlyInCreationException`。
- **早期引用不是最终完成态 Bean**：依赖已经可以引用它，但属性、初始化回调等生命周期步骤可能尚未结束。
- **第三层是工厂，不是对象**：只有真正发生早期访问时才物化引用。
- **代理一致性是重要原因**：`getEarlyBeanReference` 会调用 `SmartInstantiationAwareBeanPostProcessor`，早期引用不一定等于原始实例。
- **Spring 还会防止 raw-injection / final-wrapping 不一致**：如果别的 Bean 已拿到 raw 早期对象，而最终 Bean 又被包装，容器需要检测这种不一致，而不是默默产生两个不同语义的引用。
- **有策略开关和作用域边界**：早期暴露路径受单例、正在创建以及 `allowCircularReferences` 等条件约束。
- **prototype 不能照搬**：这套实现依赖单例注册表的创建中状态和早期暴露结构，不是 prototype Bean 的通用循环处理机制。
- **解决“能创建”不等于设计合理**：循环依赖会增加生命周期、代理和初始化顺序的理解成本，官方 API/文档倾向于建议重构依赖关系。

## 原理机制

循环依赖难点不在“图里有环”本身，而在对象生命周期存在阶段性：

```text
尚未实例化
→ 已实例化但未填充依赖
→ 已填充但未完成初始化
→ 最终单例
```

如果 A 和 B 都要求“对方必须是最终完成态以后我才能开始创建”，那么 `A -> B -> A` 永远无法前进。

Spring 对支持的单例场景放宽了这个约束：**依赖方可以先拿到一个已经实例化但尚未完全初始化的早期引用**。这样图上的环被临时切开：

```text
A 已实例化
→ 创建 B
→ B 获取 A early reference
→ B 完成
→ A 注入 B
→ A 完成
```

`singletonObjects`、`earlySingletonObjects`、`singletonFactories` 共同表达的是同一个 Bean 在生命周期中的不同可见状态。第三层工厂又让“早期可见”不是简单暴露 raw object，而是可以经过统一扩展点得到早期代理引用。

所以这个机制的本质可以概括为：

**利用单例 Bean “实例化”和“完整初始化”之间的时间窗口，受控地提前暴露引用，打断属性注入型依赖环。**

## 项目经验版

来源没有提供真实项目中的 Spring 版本、Bean 定义、AOP 配置或线上故障记录，不能虚构“我们项目曾经这样解决”。

真实排查时我会先做四件事：

1. 画出 Bean 依赖边，确认是属性/setter 注入环还是构造器环；
2. 确认涉及 Bean 的 scope，避免把 prototype 等场景误判成单例三级结构问题；
3. 如果存在事务、异步、AOP 等代理，检查循环依赖中的一方是否在早期阶段被代理，以及依赖方拿到的是 raw bean 还是 early proxy；
4. 优先判断能否通过拆职责、引入中间服务、事件或延迟查找等方式去掉环，再决定是否接受容器的循环引用支持。

如果问题只在“怎么让它启动”，直接依赖早期暴露往往会把更深的模块耦合问题留到后面。

## 常见追问

- 问：为什么构造器循环依赖解决不了？
  答：因为进入构造器时对象实例还没有创建完成，没有可放进早期暴露结构的对象。Spring 官方文档明确把构造器循环依赖列为不可解析场景。

- 问：一级、二级、三级分别是什么？
  答：常见面试说法对应 `singletonObjects`、`earlySingletonObjects`、`singletonFactories`。前两个存对象引用，第三个存能生成早期引用的 `ObjectFactory`。

- 问：为什么不能只用二级缓存，实例化后直接把 raw bean 放进去？
  答：这样会过早固定成 raw 引用，也失去按需调用 `getEarlyBeanReference` 的机会。第三层工厂让容器在真正需要时通过 `SmartInstantiationAwareBeanPostProcessor` 生成早期引用，有利于代理语义一致。

- 问：三级缓存是专门为 AOP 发明的吗？
  答：不能这样绝对化。它首先是单例早期引用的延迟工厂层；通过 `getEarlyBeanReference` 支持早期代理一致性是它的重要实现价值之一。

- 问：为什么早期引用会从三级进入二级？
  答：工厂被第一次调用后，具体早期引用已经生成；后续再访问应该复用同一个早期引用，而不是反复生成，所以进入 `earlySingletonObjects`。

- 问：最终什么时候进入一级？
  答：Bean 完成后正式注册为单例时进入 `singletonObjects`，早期暴露状态随后被清理。

- 问：prototype Bean 也有三级缓存吗？
  答：不能这样理解。这里讨论的是单例注册表和单例创建中的早期暴露机制，不能推广成 prototype 的通用循环依赖方案。

- 问：Spring Boot 的某个版本是不是默认禁止循环依赖？
  答：那属于 Spring Boot 的产品版本/配置策略问题，和这里解释的 Spring Framework 核心机制不是同一个层级；回答核心原理时应分开。

## 易错点

- 说“Spring 能解决所有循环依赖”。
- 把构造器循环也说成三级结构可以解决。
- 把三级结构解释成纯性能缓存。
- 认为三级一定存“代理对象”，忽略没有代理时也可能只是原对象早期引用。
- 不区分早期引用和最终初始化完成的 Bean。
- 把 Spring Boot 的默认配置策略混进 Spring Framework 核心机制。
- 把单例注册表逻辑推广到 prototype 或任意对象图。
- 为了展示项目经验，虚构线上 Bean 环、代理问题或故障数据。
- 只背“一级二级三级”名称，不解释生命周期时序和为什么第三层是工厂。
