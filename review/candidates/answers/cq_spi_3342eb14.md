<!-- xhs-answer: {"schema_version":"answer.v1","canonical_id":"cq_spi_3342eb14","version":1,"status":"draft","updated_at":"2026-07-11","answer_type":"mechanism","quality_tier":"candidate"} -->
# Java SPI 的原理和用途是什么？

## 核心结论

Java SPI 是“服务类型由框架/调用方定义，provider 在运行时由 `ServiceLoader` 发现”的扩展机制。应用调用 `ServiceLoader.load(服务接口)`，再通过 iterator 或 stream 获取服务实例；classpath 下 provider 由 `META-INF/services/<服务接口全限定名>` 声明，模块路径下用 `uses` / `provides` 声明。它让调用方依赖服务抽象而非具体实现，但发现、实例化和配置错误都发生在运行时。

## 1 分钟版

- 定义服务接口，例如 `CodecFactory`；provider 可由公有无参构造器直接提供实例，也可在命名模块中由公有静态无参 `provider()` 方法返回服务实例。
- classpath JAR：在 `META-INF/services/接口全限定名` 文件逐行写 provider 类名；模块：consumer 写 `uses`，provider 写 `provides ... with ...`。
- `ServiceLoader.load` 创建 loader；iterator 懒发现并实例化 provider，stream 可先检查/过滤 provider 再 `get`。
- 用途是可插拔实现；边界是实现选择不明确、类加载器可见性和配置错误会在运行时暴露。

## 3 分钟版

SPI 的参与者是服务类型、provider、服务声明、类加载器/模块层和 `ServiceLoader` 缓存。入口是 `ServiceLoader.load(Service.class)`；loader 查找模块声明或 classpath 的 provider-configuration 文件，随后在 iterator/stream 驱动下按需定位和实例化实现。

Java SE 21 文档规定：模块 consumer 用 `uses` 声明服务，provider module 用 `provides` 声明实现；classpath provider 的声明文件位于 `META-INF/services`，文件名是服务接口的完全限定二进制名，内容是一行一个 provider 类名。这样新增实现通常不需修改调用方代码。

发现和实例化是懒的：loader 缓存已加载 provider，后续 iterator 会先产出缓存元素，再按需加载剩余 provider；`reload()` 清空缓存。`stream()` 返回 `Provider`，可在不实例化实现的情况下查看类型并筛选。配置文件格式、provider 不可加载或实例化失败等问题会触发 `ServiceConfigurationError`，因此 SPI 不是编译期安全的依赖注入。

## 关键细节

- provider-configuration 文件必须 UTF-8；空行、首尾空白和 `#` 后注释按 JDK 规则处理，重复 provider 会忽略。
- 模块 provider 不必导出实现包；consumer 通过服务类型而非实现类调用。
- `ServiceLoader` 缓存已加载 provider；运行时新增 provider 先要对所用 class loader 可见，再对既有 loader 调用 `reload()` 并丢弃旧 iterator/stream 后重新发现。

## 原理机制

状态为 `declared → loader created → provider metadata located → provider instantiated → cached`。懒加载降低“创建 loader 就实例化全部实现”的启动成本，但把配置和构造错误推迟到迭代/加载点。`ServiceLoader` 实例不能由多个线程并发安全使用；调用方应限制其访问，定义选择规则（能力、优先级、唯一性）并在启动期校验必要 provider，否则多个实现的选择会变成隐式行为。

## 项目经验版

项目映射提示：列出服务接口、provider JAR/模块、类加载器边界、选择策略、启动校验和错误处理。没有事实时不要虚构 Dubbo/JDBC 插件故障。

## 常见追问

- 问：SPI 与直接 `new` 的差别？答：调用方只依赖接口，provider 由运行时声明发现，扩展不需要改调用方。
- 问：为什么有时找不到 provider？答：检查 `META-INF/services` 路径/文件名、类可见性、模块 `uses/provides` 和使用的 class loader。
- 问：SPI 是否会立即创建所有实现？答：不会，JDK 文档规定 iterator/stream 按需发现和实例化，并缓存已加载 provider。
- 问：配置错了怎么办？答：定位、加载或实例化 provider 时会出现 `ServiceConfigurationError`，应在启动验证阶段尽早暴露。

## 易错点

- 不要把 Java SPI 与 Spring SPI 或 Dubbo SPI 的扩展规则混为一谈。
- 不要忽略模块路径和 classpath 的声明方式不同。
- 不要假设多个 provider 自带优先级或自动选出唯一实现。
- 不要在安全敏感场景加载不受信任的 provider。
