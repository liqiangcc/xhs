<!-- xhs-answer: {"schema_version":"answer.v1","canonical_id":"cq_spring_bean_conflict_fb864867","version":1,"status":"ready","updated_at":"2026-07-10"} -->
# Spring 中同名 Bean 冲突发生在哪个阶段？

## 核心结论

Spring 同名 Bean 是否报错取决于 BeanDefinition 注册阶段的覆盖策略和来源；冲突通常在容器 refresh 的定义解析/注册阶段暴露，而不是等到业务方法调用。

## 1 分钟版

- 组件扫描、@Bean、XML 等最终都注册 BeanDefinition，同名时由 registry 与覆盖配置决定。
- Spring Boot 默认覆盖策略随版本演进，回答需绑定实际 Boot/Spring 配置。
- 同类型多个不同名 Bean 属于依赖解析冲突，通常在创建注入点时抛 NoUniqueBeanDefinitionException。

## 3 分钟版

要区分同名定义覆盖和同类型候选歧义。排查时查看 Bean 名生成、配置类顺序、条件装配和 Condition Report，而不是只改注入字段名。 按“目标—核心数据结构—主流程—保证机制—开销—版本边界”复述，并指出失败或退化路径。

## 关键细节

- 组件扫描、@Bean、XML 等最终都注册 BeanDefinition，同名时由 registry 与覆盖配置决定。
- Spring Boot 默认覆盖策略随版本演进，回答需绑定实际 Boot/Spring 配置。
- 同类型多个不同名 Bean 属于依赖解析冲突，通常在创建注入点时抛 NoUniqueBeanDefinitionException。

## 原理机制

入口触发状态变化，核心结构保存中间状态，协调/恢复路径处理并发与故障；实际语义需绑定版本和配置。 Spring 同名 Bean 是否报错取决于 BeanDefinition 注册阶段的覆盖策略和来源；冲突通常在容器 refresh 的定义解析/注册阶段暴露，而不是等到业务方法调用。

## 项目经验版

项目映射提示：填写真实版本、配置、规模、观测指标与故障演练；只阅读源码时不包装成线上实践。

## 常见追问

- 问：同名和同类型冲突一样吗？答：不一样，同名发生在定义注册；同类型多候选发生在依赖解析。
- 问：怎么显式选择候选？答：使用 @Qualifier、@Primary 或明确 @Resource(name)。
- 问：为何版本敏感？答：Boot 的默认覆盖行为和错误提示随版本/配置变化，应查当前环境。

## 易错点

- 不要跳过状态变化和失败路径。
- 不要脱离版本、配置和负载讨论性能。
- 不要在未确认版本时绝对回答一定覆盖或一定报错。
