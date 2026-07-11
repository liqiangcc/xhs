<!-- xhs-answer: {"schema_version":"answer.v1","canonical_id":"cq_q_74d36d6bdeee0a5c1894daee54b67ce8","version":1,"status":"draft","updated_at":"2026-07-11","quality_tier":"candidate","answer_type":"scenario"} -->
# 依赖冲突：在大型 Maven 项目中，如何排查并解决类路径（Classpath）冲突（如同一类加载器加载不同版本 jar）？

## 核心结论

把 Maven 类路径冲突当作一次可回放的构建—发布—运行时排障：先固定失败的 JDK、命令、镜像与完整堆栈；再用 `dependency:tree` 得到构建时 mediation 结果，用最终 artifact 和运行中类的定义 loader/可选 CodeSource 观察实际定义来源，二者一致后才在根 POM 的 dependencyManagement 或错误传递边修复。Maven 的最近定义规则不能替代运行时 classloader 证据。

## 1 分钟版

- 保存证据：异常签名、调用方/缺失方法、JDK 21、Maven 版本、有效 POM、dependency tree、最终 JAR 清单、镜像 digest 和启动 classpath。
- 构建图：运行 `mvn dependency:tree -Dverbose`，定位所有 GA 路径与 mediation 结果；同一 artifact 的权威版本由根 dependencyManagement/BOM 固定。
- 运行态：记录 `getClassLoader()`；只有 ProtectionDomain/CodeSource 非空时才将其 location 作为来源线索，并同时核对 fat JAR、容器共享库、shading 与模块路径。
- 修复与验证：排除错误传递边或升级兼容版本，重建镜像并覆盖冲突 API；灰度发布，异常立即回滚上一个已验证 artifact。

## 3 分钟版

假设一个 100 模块 Maven 构建在 CI 每日 50 次、每次最多 10 个并发任务；目标是依赖冲突在 30 分钟内可定位、修复后构建与核心集成测试在 20 分钟内完成，且同一可发布镜像只含一份已批准的关键库版本。这是排障 SLO，不是 Maven 默认指标。容量按并行诊断任务的日志、依赖树和镜像体积预算：保留每次失败的有效 POM、tree、JAR 清单和 digest，至少覆盖回滚窗口；不要用本机 `.m2` 状态作为唯一证据。

数据流是 `源码/POM → Maven 解析依赖图 → mediation 后 classpath → 打包产物/镜像 → 进程 ClassLoader 定义类 → 调用点链接`。诊断记录使用 `build_id, git_sha, pom_digest, jdk, artifact_digest, class_name, loader_id, code_source_location?, tree_path, result`；同一 build_id 的采样和修复提交必须绑定，避免把另一镜像的观察混入本次结论。Maven 的 dependency mechanism 规定同一 artifact 的版本按 nearest definition 调解，同深度时先声明者胜出；dependency plugin 的 tree goal 可输出依赖树和 verbose 信息。运行时再记录 `Class.getClassLoader()`；Java SE 21 默认 `loadClass` 的顺序是已加载、父 loader、findClass，但自定义 loader 可以覆写行为。

修复先在根 POM 的 dependencyManagement/BOM 收敛兼容版本，或在错误传递边 exclusion；不能用删除本机缓存或手工复制 JAR 代替。CI 超时或仓库暂不可用时保留完整日志、以同一 git SHA 和仓库快照重试；生产出现 LinkageError 时停止扩大、摘除新实例并回滚到上一个通过依赖门禁的镜像。若修复后出现不兼容，补偿是恢复上一个 POM/BOM 锁定版本并对受影响请求重放或人工核对；灾备保留源码、POM、内部 artifact repository、构建产物与镜像 digest，能够在干净 worker 重建。观测 dependency tree diff、重复类、artifact digest、构建失败率、启动/LinkageError、加载器与 CodeSource 采样；先在预发重建和压测，再灰度。替代方案是 shading 或插件/容器隔离 loader：可共存不兼容库，但增加重定位、跨 loader 类型边界和运维成本，优先升级或替换依赖。 先澄清规模、QPS、数据量、一致性、延迟和故障目标，再画主链路，补齐幂等、容量、降级、对账、观测和替代方案。

## 关键细节

- 保存证据：异常签名、调用方/缺失方法、JDK 21、Maven 版本、有效 POM、dependency tree、最终 JAR 清单、镜像 digest 和启动 classpath。
- 构建图：运行 `mvn dependency:tree -Dverbose`，定位所有 GA 路径与 mediation 结果；同一 artifact 的权威版本由根 dependencyManagement/BOM 固定。
- 运行态：记录 `getClassLoader()`；只有 ProtectionDomain/CodeSource 非空时才将其 location 作为来源线索，并同时核对 fat JAR、容器共享库、shading 与模块路径。
- 修复与验证：排除错误传递边或升级兼容版本，重建镜像并覆盖冲突 API；灰度发布，异常立即回滚上一个已验证 artifact。
- Maven mediation 只定义构建依赖图的版本选择；同名类的最终定义仍取决于部署物和运行时 classloader。
- Java SE 21 的 `Class.getClassLoader()` 可能为 null（例如 bootstrap）；`getProtectionDomain()` 可用于取得域，但 CodeSource 或 location 可能为空或不是 JAR，必须按实际值处理。
- 默认 loadClass 委派顺序只适用于 Java SE 21 API 的默认实现；自定义 loader 或容器策略要单独验证。
- 无兼容版本时不要把两个 major version 放进同一普通 classpath；用升级、替换、拆分或受控隔离，并增加集成测试。

## 原理机制

入口按容量预算接收流量，核心链路用分区/缓存/异步扩展，持久层维护最终不变量，补偿与对账让故障状态收敛。 核心状态机是 `依赖声明图 → Maven mediation 后构建 classpath → 打包清单 → 运行时 ClassLoader 定义的 Class → 调用点`。`dependency:tree` 只验证前两步；镜像/JAR 清单验证打包步；ClassLoader、ProtectionDomain 和可能存在的 CodeSource location 是运行时观察，不能单独保证 location 是 JAR 或不为空。Java SE 21 默认 ClassLoader 先查已加载、再委派父 loader、最后 findClass；被覆写的 loader、JPMS、shading、应用服务器共享库会改变或补充该链路。成本来自解析大依赖图、重建镜像与环境采样，收益是每一步都有同一 build_id 的可审计证据。

## 项目经验版

项目映射提示：把示例数字替换为真实规模和 SLO，补齐个人决策、压测证据、回滚与复盘；不使用未经确认的项目成果。

## 常见追问

- 问：dependency:tree 已收敛，为什么还会 NoSuchMethodError？答：tree 只说明 Maven 的构建图；检查最终 JAR/镜像和运行时 loader，容器或 shading 可能加入另一份类。
- 问：CodeSource 能否直接证明类来自某个 JAR？答：不能绝对证明；先判断 ProtectionDomain、CodeSource 和 location 是否存在，再把它与部署物清单和 loader 一起作为观察证据。
- 问：nearest definition 能解决所有冲突吗？答：不能，它只选择构建图中的一个版本；如果调用方需要不同 major API，应先找兼容组合或隔离边界。
- 问：怎样验证修复没有回归？答：干净 worker 重建，比较 dependency tree/重复类/镜像 digest，运行覆盖冲突 API 的集成测试并在灰度观察 LinkageError。

## 易错点

- 不要只罗列组件而没有数据流和容量。
- 不要只设计成功路径，必须说明超时、重试、降级和对账。
- 不要把 Maven 的 nearest definition 误说成运行时 classloader 的选择顺序。
- 不要把 CodeSource location 当作必然存在的 JAR 路径。
- 不要只改 IDE 或本机缓存；必须复查最终 artifact、镜像和干净环境。
- 不要在没有隔离设计和测试时强行混用不兼容 major version。
