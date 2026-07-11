<!-- xhs-answer: {"schema_version":"answer.v1","canonical_id":"cq_spring_injection_5060c47f","version":1,"status":"draft","updated_at":"2026-07-11","answer_type":"concept","quality_tier":"candidate"} -->
# @Autowired 和 @Resource 的区别

## 核心结论

`@Autowired` 是 Spring 的依赖注入注解，Spring 7 文档以类型匹配为核心，并通过 `@Primary`、`@Qualifier` 等处理多候选；`@Resource` 是 Jakarta/JSR-250 注解。Spring 7 中，`@Resource(name="...")` 按指定 bean 名解析，不走 primary 类型回退；只有未显式指定 name 时，才先由字段名或 setter 属性名推导默认名称，并在文档限定的情形回退到 primary 类型匹配。不要把“@Resource 永远只按名称”或“@Autowired 只按类型”背成绝对规则。

## 1 分钟版

- 来源：`@Autowired` 属于 Spring；`@Resource` 属于 `jakarta.annotation` 标准注解，Spring 为其提供支持。
- 注入点：`@Autowired` 可用于构造器、字段、setter/配置方法和参数；`@Resource` 的 Spring 文档重点支持字段与 bean 属性 setter。
- 解析：`@Autowired` 从类型候选开始，多个候选用 `@Primary` 或 `@Qualifier` 缩小；`@Resource(name="...")` 明确按 bean 名称，不走类型回退。
- 选择：新 Spring 代码优先构造器注入配合 `@Autowired` 语义/`@Qualifier`；已有 Jakarta EE 风格或明确名称绑定可用 `@Resource`，但需写清版本和容器行为。

## 3 分钟版

两者的共同目标是让容器解析依赖，区别在注解来源、可用注入点和解析语义。Spring 7 的 `@Autowired` 标记构造器、字段、setter 或配置方法由 Spring DI 注入；`required` 默认 true。单构造器场景甚至不必标注 `@Autowired`，但这是 Spring 的版本化行为，不应推广成所有 Spring 版本的规则。

`@Autowired` 的候选解析以类型为基础：多个相同类型 Bean 时，用 `@Primary` 给单值注入点选择优先候选，或用 `@Qualifier` 在类型候选中继续筛选。字段名可能在没有其他解析指示时参与候选匹配，但不能把它误说成 `@Autowired` 的主语义是“按名称”。

Spring 7 支持 `jakarta.annotation.Resource`。带 `name` 时按 bean 名称解析，不再尝试 primary 类型匹配；不写 name 时，字段取字段名、setter 取属性名，先尝试该默认名称。只有这个未显式 name 的路径在默认名称找不到时，Spring 文档才说明可回退到 primary 类型匹配和若干已知可解析依赖。因此选型应根据需要表达的是“类型 + 限定条件”还是“指定名称”；本文结论以 Spring Framework 7.0.8 为界，其他版本应核对对应文档和容器配置。

## 关键细节

- Spring 7 文档中，`@Autowired(required=false)` 可表达可选注入；`Optional`、`@Nullable` 也可覆盖默认的必需性语义。
- 有多个同类型候选时，不要靠字段名碰巧匹配；用 `@Qualifier` 或 `@Primary` 显式表达选择。
- `@Resource(name="orderService")` 的 name 是 Spring `ApplicationContext` 解析的 bean 名；它不是自动等价于任意 JNDI 名称。
- 本文以 Spring Framework 7.0.8 文档中的 `jakarta.annotation.Resource` 为准；使用其他 Spring 版本时，先核对该版本的注解包与解析规则。

## 原理机制

容器在注入点处理注解并解析候选 Bean。`@Autowired` 先按声明类型形成候选集，再用 primary/qualifier 等元数据消除歧义；`@Resource` 有显式 name 时按该名称解析，未显式 name 时先从字段或属性名得到默认名称，只有默认名称解析不到时才进入 Spring 文档限定的 primary 类型/已知可解析依赖回退。解析失败或候选不唯一时，应让启动失败暴露配置问题，而不是依赖偶然名称。

## 项目经验版

项目映射提示：列出接口的多个实现、最终使用的 `@Qualifier`/`@Primary`/bean name、Spring Framework 与 Jakarta 版本，以及启动测试结果。没有这些事实时，不要编造某次注入失败或升级兼容事故。

## 常见追问

- 问：两个同类型 Bean 时只写 `@Autowired` 会怎样？答：需用 `@Primary` 或 `@Qualifier` 等消除单值注入歧义；不要依赖未声明的偶然顺序。
- 问：`@Resource` 不写 name 一定只按字段名吗？答：Spring 7 文档说明它先以字段/属性名作为默认名称；仅在未显式 name 且默认名称找不到的限定路径，才可回退到 primary 类型匹配或已知可解析依赖。显式 `name` 不走这条回退。
- 问：为什么偏好构造器注入？答：它让必需依赖在对象创建时显式可见；若只声明单构造器，当前 Spring 文档说明可不标 `@Autowired`。
- 问：`@Autowired` 能注入集合吗？答：Spring 文档支持数组、Collection 和 Map 的类型匹配集合注入；多实现顺序与选择规则仍要显式管理。

## 易错点

- 不要把 `@Resource` 的 Spring 支持与任意 JNDI 直查混为一谈。
- 不要把 `@Autowired` 说成只支持字段注入，或把字段名匹配当成其主语义。
- 不要在多个候选 Bean 时依赖名称巧合；使用 `@Qualifier`/`@Primary` 表达意图。
- 不要把 Spring 7 的 `jakarta.annotation.Resource` 规则外推到其他 Spring 版本；先核对对应版本文档。
