<!-- xhs-answer: {"schema_version":"answer.v1","canonical_id":"cq_bean_319a398d","version":1,"status":"draft","updated_at":"2026-07-11","answer_type":"mechanism","quality_tier":"candidate"} -->
# Spring Bean 的生命周期是怎样的？

## 核心结论

不要把 Bean 生命周期背成一串脱离边界的固定名词。以 Spring Framework 7.0.8 中容器创建一个普通 Bean 的典型路径看：先依据 BeanDefinition 实例化并完成属性/依赖填充，再执行 `Aware` 回调；随后由 `BeanPostProcessor` 围住初始化回调，初始化回调的相对顺序是 `@PostConstruct`、`InitializingBean.afterPropertiesSet()`、自定义 init 方法，之后的后置处理还可能返回代理对象。容器关闭时，对受其完整管理的 Bean 执行 `@PreDestroy`、`DisposableBean.destroy()`、自定义 destroy 方法；prototype Bean 是关键例外，Spring 不负责调用其配置的销毁回调。

## 1 分钟版

- 先分两层：`BeanFactoryPostProcessor` 改的是 BeanDefinition/配置元数据，发生在普通 Bean 实例化前；它不是每个 Bean 的实例生命周期回调。
- 创建阶段：实例化 → 填充普通属性和依赖 → `Aware` 回调；`BeanNameAware` 的回调在普通属性填充后、初始化回调前。
- 初始化阶段：`BeanPostProcessor` 在初始化回调前后介入；同一 Bean 同时配置多种初始化机制且方法名不同，Spring 7 文档给出的顺序是 `@PostConstruct` → `afterPropertiesSet()` → 自定义 init。
- 销毁阶段：关闭容器时对应顺序是 `@PreDestroy` → `destroy()` → 自定义 destroy；但 prototype 只完成创建/初始化，后续资源释放由客户端负责。

## 3 分钟版

生命周期的入口不是“new 了一个对象”，而是容器按 BeanDefinition 创建和管理对象。若配置了 `BeanFactoryPostProcessor`，它先读取或修改配置元数据；此时提前 `getBean()` 会造成过早实例化，可能绕过后续 Bean 后处理。

对一个由容器创建的普通 Bean，容器先实例化对象，再填充普通属性和依赖。实现 `BeanNameAware`、`BeanFactoryAware`、`ApplicationContextAware` 等接口是向 Bean 提供容器基础设施的回调；其中 `BeanNameAware` 明确发生在普通属性填充之后、初始化回调之前。

初始化不只是一种钩子。`BeanPostProcessor` 会在容器初始化方法之前和之后都收到回调；若同一 Bean 同时使用多种且方法名不同的机制，Spring 7.0.8 的顺序是 `@PostConstruct`、`afterPropertiesSet()`、自定义 init 方法。后置处理后的返回对象才是容器继续使用的对象，因此它是理解代理、注入注解等扩展点的关键位置，而不能只背接口顺序。

容器销毁受完整管理的 Bean 时，组合机制的顺序为 `@PreDestroy`、`DisposableBean.destroy()`、自定义 destroy 方法。作用域会改变这个边界：prototype 对象每次请求都会创建，Spring 只负责实例化、配置和初始化，不记录它以便在以后执行销毁回调；调用方必须释放其昂贵资源。初始化回调运行在 singleton 创建锁中，适合校验配置和准备数据结构，不应在其中进行可能触发外部 Bean 访问的活动，以免产生初始化死锁。

## 关键细节

- `InitializingBean` / `DisposableBean` 分别暴露 `afterPropertiesSet()` / `destroy()`；Spring 文档建议优先使用不耦合 Spring 接口的 `@PostConstruct` / `@PreDestroy` 或配置的普通方法。
- 若多个生命周期机制指向同一个方法名，Spring 只调用一次；上述顺序只适用于配置为不同方法名的情况。
- `BeanPostProcessor` 面向对象实例，在初始化回调前后都被容器调用；`ApplicationContext` 会自动探测配置中实现该接口的 Bean 并注册它们。
- singleton 是默认 scope，每个 Spring IoC 容器中同一 BeanDefinition 对应一个共享实例；prototype 每次请求创建新实例，销毁回调不由 Spring 管理。

## 原理机制

可以按“元数据 → 实例 → 初始化产物 → 销毁”理解：

1. `BeanFactoryPostProcessor` 先处理 BeanDefinition；它修改的是蓝图而非普通对象实例。
2. 容器按蓝图实例化对象，填充属性/依赖，并把 Bean 名称或容器引用等基础设施通过 `Aware` 回调交给对象。
3. `BeanPostProcessor` 在初始化回调前后运行；初始化机制按已声明的组合顺序执行，后置处理可以把原对象替换为另一个返回对象，因此代理边界在这里形成。
4. 对单例等由容器持续管理的对象，关闭容器触发销毁回调以清理资源；对 prototype，容器交付对象后不再跟踪，资源释放责任随之转给调用方。

这条链路的成本和风险主要在扩展点：后处理器会参与每个适用 Bean 的创建；初始化中做长时间 I/O 或访问尚未完全初始化的外部 Bean 会扩大启动时间并可能制造死锁。应把初始化回调限制为配置校验和局部数据结构准备，把长期后台任务交给明确的 `Lifecycle`/`SmartLifecycle` 管理。

## 项目经验版

项目映射提示：列出实际 Bean 的 scope、使用的初始化/销毁钩子、是否有 `BeanPostProcessor` 或代理、关闭测试如何验证资源释放，以及初始化是否依赖外部服务。没有这些事实时，不要虚构“启动变慢”或“连接泄漏”的事故。

## 常见追问

- 问：`BeanFactoryPostProcessor` 和 `BeanPostProcessor` 最本质的区别？答：前者处理配置元数据并发生在普通 Bean 实例化前；后者处理每个已创建的对象实例，并围住初始化回调。
- 问：为什么 `@PostConstruct` 里不宜调用别的 Bean 做复杂工作？答：Spring 7 文档说明它在 singleton 创建锁内运行，Bean 要在该回调返回后才视为完全初始化；外部 Bean 访问会带来初始化死锁风险。
- 问：prototype Bean 的 `@PreDestroy` 会在关闭容器时自动执行吗？答：不会。Spring 对 prototype 完成实例化、配置和初始化后不再记录它；调用方要清理资源。
- 问：多个初始化钩子都会执行吗？答：方法名不同会依次执行 `@PostConstruct`、`afterPropertiesSet()`、自定义 init；若是同一个方法名，Spring 只调用一次。

## 易错点

- 不要把 `BeanFactoryPostProcessor` 当成“每个 Bean 初始化前的钩子”；它处理的是配置元数据。
- 不要把 `@PostConstruct`、`afterPropertiesSet()`、自定义 init 说成三选一或任意顺序；组合时有文档定义的顺序和同名去重规则。
- 不要把 singleton 的销毁流程外推到 prototype；prototype 的销毁资源由客户端负责。
- 不要把生命周期回调与后台任务启动混为一谈；初始化回调有创建锁和死锁边界。
