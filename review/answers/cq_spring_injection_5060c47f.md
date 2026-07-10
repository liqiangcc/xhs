<!-- xhs-answer: {"schema_version":"answer.v1","canonical_id":"cq_spring_injection_5060c47f","version":2,"status":"needs_update","updated_at":"2026-07-11","quality_tier":"curated_audit_failed","audit_failure":"missing_evidence"} -->
# @Autowired 和 @Resource 的区别

## 核心结论

在 Spring 中，`@Autowired` 默认按类型解析，`@Resource` 默认按名称语义再回退到类型；两者由不同 BeanPostProcessor 处理。生产代码更推荐构造器注入，注解差异主要体现在多实现消歧和可选依赖。

## 1 分钟版

- `@Autowired` 是 Spring 注解，可配 `@Qualifier`、`@Primary`，还支持集合、Optional 等注入形式。
- `@Resource` 来自 Jakarta Annotations，指定 `name` 时按明确名称查找，常用于按名称消歧。
- 单一候选时二者效果常相同；多个同类型 Bean 时必须明确选择规则。
- 构造器注入让依赖不可变、便于测试，并能更早暴露循环依赖。

## 3 分钟版

AutowiredAnnotationBeanPostProcessor 解析 `@Autowired`，先按 `ResolvableType` 找候选，再结合 `@Primary`、优先级、Qualifier 和字段/参数名等规则消歧。CommonAnnotationBeanPostProcessor 处理 `@Resource`，遵循资源名称语义。Spring 6 / Boot 3 使用 `jakarta.annotation.Resource`，旧项目可能仍是 `javax.annotation.Resource`。字段注入虽然简短，却隐藏依赖、降低可测试性，也更容易形成循环依赖；构造器注入在只有一个构造器时可省略 `@Autowired`。

## 关键细节

- 多候选未能消歧会抛 `NoUniqueBeanDefinitionException`。
- `@Primary` 表示默认优先，`@Qualifier` 表示明确限定语义。
- `required=false` 或 Optional 可表达可选依赖，但应避免掩盖配置错误。
- 参数名消歧依赖编译元数据和 Spring 版本行为，关键依赖宜显式限定。

## 原理机制

容器实例化 Bean 后，相关 BeanPostProcessor 收集注入点，通过 BeanFactory 的依赖解析器选择候选并反射赋值或提供构造参数。是否按名称、类型或限定符取决于注解及解析策略。

## 项目经验版

项目映射提示：真实重构时可展示从字段注入改为构造器注入后，依赖边界、单元测试和循环依赖暴露如何改善；没有量化事实时不虚构收益数字。

## 常见追问

- 问：多个同类型 Bean 时怎么办？答：`@Autowired` 配合 `@Qualifier`/`@Primary`，或用 `@Resource(name=...)` 明确选择。
- 问：为什么推荐构造器注入？答：依赖显式、可设为 final、测试方便，并在创建阶段暴露缺失和循环依赖。
- 问：Boot 3 的 Resource 包名是什么？答：`jakarta.annotation.Resource`，不是旧的 `javax.annotation.Resource`。
- 问：一个构造器还要写 Autowired 吗？答：现代 Spring 中单构造器通常可省略。

## 易错点

- 不要只回答“一个按类型、一个按名称”而忽略回退和消歧规则。
- 不要认为字段名永远可靠地决定 Autowired 候选。
- 不要用可选注入掩盖本应启动失败的核心依赖。
