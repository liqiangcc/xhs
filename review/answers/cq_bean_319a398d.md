<!-- xhs-answer: {"schema_version":"answer.v1","canonical_id":"cq_bean_319a398d","version":1,"status":"ready","updated_at":"2026-06-30"} -->
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

项目中常用 BeanPostProcessor 做统一增强，例如自动注册策略类、包装客户端、注入监控埋点。排查 Bean 初始化问题时，重点看依赖注入是否完成、初始化方法是否抛异常、最终注入的是代理对象还是原始对象。

## 常见追问

- BeanFactoryPostProcessor 和 BeanPostProcessor 区别是什么？
- AOP 代理在生命周期哪个阶段生成？
- Spring 如何解决单例循环依赖？
- @PostConstruct 和 InitializingBean 顺序如何？

## 易错点

- 不要把 BeanFactoryPostProcessor 和 BeanPostProcessor 混为一谈。
- 不要说所有 Bean 都会自动销毁，prototype Bean 需要业务自己处理。
- 不要忽略 AOP 代理导致“拿到的 Bean 不是原对象”。
