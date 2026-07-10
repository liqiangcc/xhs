<!-- xhs-answer: {"schema_version":"answer.v1","canonical_id":"cq_bean_319a398d","version":2,"status":"ready","updated_at":"2026-07-10"} -->
# Spring Bean的生命周期是怎样的？

## 核心结论

Spring Bean 生命周期可以概括为：实例化、属性填充、Aware 回调、BeanPostProcessor 前置处理、初始化、BeanPostProcessor 后置处理、使用、销毁。面试要重点讲清楚 BeanPostProcessor 是扩展点，AOP 代理通常发生在初始化后的后置处理阶段。

## 1 分钟版

容器先根据 BeanDefinition 创建对象，再进行依赖注入；然后执行各种 Aware 接口回调，例如 BeanNameAware、ApplicationContextAware；接着执行 BeanPostProcessor 的 beforeInitialization；再调用初始化逻辑，包括 @PostConstruct、InitializingBean、init-method；之后执行 BeanPostProcessor 的 afterInitialization，AOP 代理常在这里生成；最后 Bean 被业务使用，容器关闭时执行 @PreDestroy、DisposableBean、destroy-method。

## 3 分钟版

完整链路从 BeanDefinition 开始。Spring 扫描或读取配置后形成 BeanDefinition，真正创建时先实例化对象，随后填充属性并解决依赖。依赖注入后，如果 Bean 实现了 Aware 系列接口，Spring 会把容器上下文、BeanName 等信息回调给它。初始化前后，BeanPostProcessor 可以统一增强 Bean，这是框架扩展的核心。初始化方法按注解、接口、配置顺序执行。初始化后置处理中可能返回代理对象，因此最终放入单例池、被业务拿到的对象不一定是原始对象。销毁阶段只对容器管理且可销毁的 Bean 生效。

## 关键细节

- BeanFactoryPostProcessor 处理 BeanDefinition，发生在 Bean 实例化之前。
- BeanPostProcessor 处理 Bean 实例，发生在初始化前后。
- 循环依赖与三级缓存、早期引用、AOP 代理有关。
- 原型 Bean 的销毁通常不由容器完整托管。

## 原理机制

- BeanDefinition 描述如何创建 Bean。
- 单例 Bean 创建后会进入单例池。
- AOP 代理通过后置处理器包装原始 Bean。
- 初始化回调顺序通常是 @PostConstruct、InitializingBean、init-method。

## 项目经验版

项目映射时可以从真实扩展点切入：是否使用 BeanPostProcessor 注册策略、包装客户端或注入监控；排查初始化问题时是否确认依赖注入、初始化异常以及最终对象是否被代理。没有实际案例时只保留排查清单，不声称做过统一增强。

## 常见追问

- 问：BeanFactoryPostProcessor 和 BeanPostProcessor 有什么区别？答：前者修改 BeanDefinition，发生在普通 Bean 实例化前；后者处理 Bean 实例，可在初始化前后包装或替换对象。
- 问：AOP 代理在生命周期哪个阶段生成？答：典型的自动代理创建器在初始化后置处理阶段返回代理；循环依赖时还可能通过早期引用提前暴露一致的代理对象。
- 问：Spring 如何解决单例循环依赖？答：通过单例创建中的早期引用与三级缓存处理 setter/字段注入的部分循环依赖；构造器循环依赖通常无法解决，prototype 也不适用该机制。
- 问：@PostConstruct 和 InitializingBean 顺序如何？答：通常先执行 @PostConstruct，再执行 afterPropertiesSet，最后执行配置的 init-method；它们位于 BeanPostProcessor 前后置回调之间。

## 易错点

- 不要把 BeanFactoryPostProcessor 和 BeanPostProcessor 混为一谈。
- 不要说所有 Bean 都会自动销毁，prototype Bean 需要业务自己处理。
- 不要忽略 AOP 代理导致“拿到的 Bean 不是原对象”。
