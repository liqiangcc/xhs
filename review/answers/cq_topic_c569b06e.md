<!-- xhs-answer: {"schema_version":"answer.v1","canonical_id":"cq_topic_c569b06e","version":1,"status":"ready","updated_at":"2026-07-01"} -->
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

项目里比较字符串、枚举外的业务对象、ID 包装类时，我会明确使用 equals 或 Objects.equals，避免空指针。自定义值对象会用不可变字段实现 equals 和 hashCode，保证放入集合后行为稳定。

## 常见追问

- String 为什么不能用 `==` 比较内容？
- equals 和 hashCode 有什么关系？
- Integer 用 `==` 为什么有时返回 true？
- Objects.equals 有什么好处？

## 易错点

- 不要说 `==` 永远比较地址，基本类型比较的是值。
- 不要忘记 Object 默认 equals 仍是引用比较。
- 不要重写 equals 后漏掉 hashCode。
