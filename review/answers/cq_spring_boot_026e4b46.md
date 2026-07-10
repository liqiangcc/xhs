<!-- xhs-answer: {"schema_version":"answer.v1","canonical_id":"cq_spring_boot_026e4b46","version":2,"status":"needs_update","updated_at":"2026-07-11","quality_tier":"curated_audit_failed","audit_failure":"missing_evidence"} -->
# Spring Boot 自动配置的原理是什么？

## 核心结论

Spring Boot 自动配置不是“自动扫描所有类”，而是导入一组候选配置类，再由 classpath、Bean、配置属性和应用类型等条件决定哪些配置生效；用户自定义 Bean 通常可让默认配置退让。

## 1 分钟版

- `@SpringBootApplication` 组合了配置类、组件扫描和自动配置启用能力。
- Boot 3.x 从自动配置 imports 文件加载候选类；旧版本常见 `spring.factories`，不能混为一谈。
- `@ConditionalOnClass`、`@ConditionalOnMissingBean`、`@ConditionalOnProperty` 等条件决定是否注册 Bean。
- `@ConfigurationProperties` 把外部配置绑定为类型安全对象；失败原因可通过 Condition Evaluation Report 查看。

## 3 分钟版

启动时 Spring 先解析主配置类，自动配置选择器收集、过滤并排序候选配置，再把满足条件的配置类交给容器。典型例子是：classpath 有 DataSource 类、存在连接配置且用户没有自定义 DataSource 时，Boot 才提供默认 Bean。自动配置通过“约定 + 条件 + 后退”降低样板代码，并不替代 Spring 容器。排查时要区分候选未导入、条件未命中、属性绑定失败、Bean 被覆盖以及初始化异常；开启 debug 或读取条件报告比猜测执行顺序可靠。

## 关键细节

- Boot 2.7/3.x 推荐 `META-INF/spring/...AutoConfiguration.imports` 声明自动配置。
- 自动配置类之间可声明 before/after 顺序，但 Bean 依赖仍由容器解析。
- `@ConditionalOnMissingBean` 的搜索范围和检查时机会影响退让结果。
- 自定义 starter 应拆分依赖、属性类和自动配置，并提供条件测试。

## 原理机制

候选配置导入后仍走 Spring 配置类解析和 BeanDefinition 注册流程。条件在指定阶段读取 BeanFactory、Environment、ResourceLoader 和 ClassLoader 等信息，只有匹配的配置才参与后续实例化。

## 项目经验版

项目映射提示：若真实封装过 starter，可讲清默认值、启用条件、用户覆盖点、版本兼容和 `ApplicationContextRunner` 测试；不要把“引入依赖即可用”当成原理说明。

## 常见追问

- 问：自动配置如何让用户配置优先？答：常通过 `@ConditionalOnMissingBean` 或配置属性提供默认实现，检测到用户 Bean 后退让。
- 问：Boot 3 还主要靠 `spring.factories` 加载自动配置吗？答：自动配置候选主要使用 AutoConfiguration.imports；`spring.factories` 仍可能承载其他扩展机制。
- 问：如何排查某配置没生效？答：查看条件评估报告，逐项检查 class、property、Bean 和应用类型条件。
- 问：自动配置与组件扫描一样吗？答：不一样；前者导入已声明的候选配置，后者按包路径发现组件。

## 易错点

- 不要把 `@SpringBootApplication` 简化成单一注解作用。
- 不要套用旧版本加载文件结论而不注明版本。
- 不要只背注解名，必须说明条件化注册和退让机制。
