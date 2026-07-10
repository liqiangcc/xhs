<!-- xhs-answer: {"schema_version":"answer.v1","canonical_id":"cq_topic_c569b06e","version":2,"status":"ready","updated_at":"2026-07-10","quality_tier":"curated"} -->
# ==和equals的区别

## 核心结论

在 Java 中，`==` 比较的是两个操作数是否相同；对基本类型比较值，对引用类型比较对象地址引用。equals 是对象方法，默认也比较引用，但很多类会重写它来比较业务值。

## 1 分钟版

基本类型如 int、long 用 `==` 比较数值。对象引用用 `==` 比较是否指向同一个对象。Object 的 equals 默认实现等价于 `==`，但 String、Integer、BigDecimal 等类通常重写了 equals，用来比较内容或业务含义。所以字符串内容比较应该用 equals，而不是 `==`。

## 3 分钟版

equals 的语义取决于类的实现，但应该满足自反、对称、传递、一致和非 null 比较返回 false。重写 equals 时必须同时重写 hashCode，否则对象放入 HashMap、HashSet 等集合后会出现查找异常。包装类型还要注意缓存和拆箱，比如 Integer 在一定范围内可能复用对象，导致 `==` 结果看起来不稳定；业务代码不要依赖这种缓存行为。

## 关键细节

- 基本类型 `==` 比较值。
- 引用类型 `==` 比较引用地址是否相同。
- equals 默认比较引用，重写后可比较内容。
- 重写 equals 必须同步重写 hashCode。

## 原理机制

- `==` 是语言运算符，语义由操作数类型决定。
- equals 是虚方法，运行时根据实际对象类型分派。
- 哈希集合依赖 hashCode 定位桶，再用 equals 判断相等。

## 项目经验版

项目映射提示：真实代码中比较字符串、包装 ID 和值对象时应展示 `Objects.equals`、空值策略以及不可变的 `equals/hashCode` 字段。若对象放入 HashSet/HashMap 后会修改参与 hash 的字段，应先修正模型而不是依赖偶然行为。

## 常见追问

- 问：String 为什么不能用 `==` 比内容？答：`==` 比较引用是否同一对象，字符串池只会让部分引用偶然相同；内容应使用 equals。
- 问：equals 和 hashCode 什么关系？答：equals 为 true 的对象必须 hashCode 相同，否则基于哈希的集合无法正确定位；反过来 hash 相同不代表相等。
- 问：Integer 用 `==` 为什么有时 true？答：自动装箱可能复用缓存对象，超出缓存或显式 new 后引用不同；业务值比较用 equals 或拆箱。
- 问：Objects.equals 有什么好处？答：它对两个 null 返回 true、单边 null 返回 false，可避免直接调用实例 equals 的空指针。

## 易错点

- 不要说 `==` 永远比较地址，基本类型比较的是值。
- 不要忘记 Object 默认 equals 仍是引用比较。
- 不要重写 equals 后漏掉 hashCode。
