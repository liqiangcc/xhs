<!-- xhs-answer: {"schema_version":"answer.v1","canonical_id":"cq_spi_3342eb14","version":1,"status":"ready","updated_at":"2026-07-10"} -->
# Java SPI 的原理和用途是什么？

## 核心结论

Java SPI 是面向接口的运行时扩展发现机制：服务提供方在 `META-INF/services/接口全名` 中声明实现类，使用方通过 `ServiceLoader` 延迟发现并实例化，实现调用方与实现包解耦。

## 1 分钟版

- API 模块只定义服务接口，provider 模块实现接口并提供配置文件。
- `ServiceLoader.load` 通常结合线程上下文 ClassLoader 查找多个 classpath/JAR 中的配置。
- 遍历 ServiceLoader 时才按需加载和实例化实现，单个 provider 构造失败可能在遍历时暴露。
- 适合 JDBC 驱动、日志适配、编译器插件等扩展点，不适合作为完整依赖注入和生命周期管理容器。

## 3 分钟版

SPI 的关键是依赖倒置：框架依赖接口，具体实现反向注册给框架。JDK 9 模块系统还可用 `uses` 与 `provides ... with ...` 声明服务。原生 ServiceLoader 的能力较轻：缺少名称/优先级、条件装配、作用域和复杂依赖管理；多个实现的选择需要调用方定义规则。类加载器隔离环境下，服务接口与实现必须能由兼容的 ClassLoader 看到，否则会出现找不到实现或类型不兼容。

## 关键细节

- 配置文件名必须是接口的二进制全名，内容是一行一个实现类全名。
- provider 通常需要可访问的无参构造或符合当前 JDK 的 provider 方法约定。
- ServiceLoader 实例不是为并发修改设计的，缓存与 reload 要明确。
- 发现实现不等于选中实现，冲突和排序策略由上层负责。

## 原理机制

ServiceLoader 使用 ClassLoader 枚举服务配置资源，解析类名、校验实现关系，并在迭代/stream 访问时创建 provider。线程上下文 ClassLoader 让上层框架有机会加载由下层应用或容器提供的实现。

## 项目经验版

项目映射提示：若系统确有支付、存储或规则插件，可说明接口边界、provider 注册、版本兼容、冲突选择和隔离测试。没有真实插件化实践时，只给出最小 demo 和选型边界。

## 常见追问

- 问：SPI 与 Spring Bean 有什么区别？答：SPI 负责发现实现；Spring 还管理依赖、生命周期、作用域和条件装配。
- 问：为什么常用线程上下文 ClassLoader？答：父加载器加载的框架可借它看到应用层或容器提供的实现。
- 问：多个实现如何选择？答：原生 SPI 不规定，应由调用方按配置、注解或能力协商选择。
- 问：什么时候不该用 SPI？答：实现集合固定、需要复杂依赖注入或严格插件隔离时，可用显式工厂、DI 容器或专用插件框架。

## 易错点

- 不要把 SPI 说成自动选择“最优实现”。
- 不要忽略类加载器和重复 provider 的问题。
- 不要把 provider 的初始化副作用放在不可控构造阶段。
