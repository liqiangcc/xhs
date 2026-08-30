<!-- xhs-answer: {"schema_version":"answer.v1","canonical_id":"cq_q_6bd7f5149d6bbae7bab2f3c693efe008","version":1,"status":"draft","updated_at":"2026-08-30","answer_type":"concept","quality_tier":"candidate"} -->
# Redis 有哪些数据类型？

## 核心结论

这道面试题先答**经典五种基础类型**最稳妥：

```text
String
List
Hash
Set
Sorted Set（ZSet）
```

它们分别对应：单值/字节序列、顺序序列、字段-值对象、无序去重集合、按 score 排序的去重集合。

但要补一个版本边界：**现代 Redis 不止这五种。** 官方当前文档还包含 Stream，以及 Bitmap、Bitfield、Geospatial 等专门数据结构/能力，并持续加入新的数据类型。因此不要把“Redis 永远只有五种数据类型”说成绝对事实。

面试中可以按“**经典五种先答完整 → 每种说数据模型和典型场景 → 再补现代扩展**”的顺序回答。

## 1 分钟版

- **String**：最基础的值类型，本质是字节序列。适合缓存单值、序列化对象、计数器；`INCR` 一类命令能做原子计数。
- **List**：有序序列，适合按两端 push/pop、保存最近记录、简单生产者/消费者队列等场景。
- **Hash**：field-value 集合，适合保存一个对象的多个字段，例如用户资料或一组计数器。
- **Set**：无序、元素唯一，适合去重、成员判断以及集合交并差等关系运算。
- **Sorted Set / ZSet**：元素唯一，同时每个 member 关联 score 并按 score 排序，适合排行榜、按权重/时间排序的集合。

然后补一句：Redis 5.0 已有 **Stream** 这种追加日志型结构，支持消息 ID、范围读取和 Consumer Group；当前 Redis 文档还列出 Bitmap、Bitfield、Geospatial 等专门类型/能力，所以“经典五种”是面试基础分类，不是现代 Redis 的完整清单。

## 3 分钟版

### 1. String：最基础的字节序列

String 是 Redis 最基础的 value 类型，可以保存文本、数字的字符串表示、序列化对象或二进制内容。

典型场景：

```text
页面/对象缓存
计数器
简单状态位
分布式锁中的 token 值
```

String 的一个关键特点是很多数值操作由 Redis 命令直接提供，比如 `INCR` / `INCRBY`，所以“String”不等于只能保存普通文本。

### 2. List：有顺序的序列

List 表达的是一个**有序元素序列**。常见操作围绕头尾插入、弹出和区间读取。

适合：

- 最新 N 条记录；
- 简单任务队列；
- 需要保留插入顺序的序列。

选择 List 前要问清是否需要随机按下标高效访问、是否需要消息确认/消费组等高级消息语义；如果需要后者，Stream 通常更贴近问题模型。

### 3. Hash：一个 key 下面的字段集合

Hash 是 field-value 的记录结构：

```text
user:1001
  name -> Alice
  age  -> 26
  city -> Chengdu
```

它适合表达一个简单对象，能单独读写某个字段，而不必每次把整个对象序列化成一个 String 再整体覆盖。

### 4. Set：唯一成员集合

Set 的核心语义是：

```text
无序
+
member 唯一
```

因此很适合：

- 标签去重；
- 黑白名单/成员判断；
- 共同关注、共同好友等交集场景；
- 并集、差集等集合关系运算。

如果业务还要求“按分数排序”，那就不是普通 Set，而更适合 Sorted Set。

### 5. Sorted Set / ZSet：唯一成员 + score 排序

Sorted Set 仍然保证 member 唯一，但每个 member 关联一个 score，并按 score 维护顺序。

常见场景：

- 排行榜；
- 权重队列；
- 按时间戳或优先级排序的数据；
- 需要按排名或 score 范围查询的集合。

所以 Set 和 ZSet 的关键差异不是“一个能去重一个不能”，而是 ZSet 在唯一成员基础上增加了 score 与有序访问语义。

### 6. 为什么现在不能只说“Redis 就五种类型”？

“String、List、Hash、Set、ZSet”是最经典、最常见的面试基础分类，而且当前这组原题的实体也明确指向这五种。

但 Redis 后续版本继续增加数据结构。最常见的补充是 **Stream**：它从 Redis 5.0 开始提供追加日志式的数据模型，有唯一 entry ID、范围查询和 Consumer Group，适合事件流、通知、传感器数据等场景。

当前 Redis 官方数据类型文档还包含 Bitmap、Bitfield、Geospatial，以及更多专门/较新的类型。因此回答时应区分：

```text
经典五种基础类型
≠
当前 Redis 全部可用数据类型/结构的完整集合
```

## 关键细节

- **先说数据模型，再说命令。** 面试官问“有哪些类型”，重点是 String/List/Hash/Set/ZSet 分别表达什么，不是背一串命令名。
- **String 是字节序列。** 它既能保存普通文本，也能用于计数和二进制数据。
- **List 有序但不去重。** 如果只需要两端操作和顺序队列，它很自然；更复杂的消息确认/消费组语义应考虑 Stream。
- **Hash 是 field-value 记录。** 它适合对象字段级读写，不等同于“Java HashMap 的所有语义”。
- **Set 保证 member 唯一。** 它擅长成员判断和集合运算。
- **ZSet 同样保证 member 唯一。** 区别是额外有 score，并按 score 排序。
- **Stream 是现代 Redis 的重要补充。** 它是追加日志式结构，支持 entry ID、范围读取和 Consumer Group。
- **Bitmap / Bitfield 不要机械塞进经典五种。** 当前官方文档会把它们作为 Redis 数据类型/专门能力讨论，但它们的底层值语义与 String 命令体系有关；面试回答应先说明分类口径。
- **Geospatial 也是专门能力。** 不应为了凑“类型数量”把所有功能名字混成同一层级。
- **版本敏感。** Redis 当前数据类型目录会继续演进，所以不要背一个永远固定的“总数”。

## 原理机制

选择 Redis 数据类型，本质不是选一个“命令前缀”，而是把业务数据映射到最合适的**数据模型和访问模式**：

```text
一个值/计数？
→ String

有顺序的一列元素？
→ List

一个对象的多个字段？
→ Hash

只关心唯一成员和集合关系？
→ Set

既要唯一成员又要排序/排名？
→ Sorted Set

需要追加日志、消息 ID、历史范围和消费组？
→ Stream
```

这个判断会直接影响后续操作复杂度、内存形态、是否能原子完成目标以及是否需要额外业务逻辑。

因此“为什么不能全部用 String 序列化 JSON？”的答案是：当然可以把很多东西编码成 String，但一旦业务需要字段级更新、集合成员判断、排名、队列或流式消费，使用 Redis 原生数据模型通常能把这些语义交给服务端原子命令，而不是每次把整个对象取回应用层反序列化、修改再写回。

## 项目经验版

来源没有提供真实 Redis 项目、内存规模、命中率或性能数据，因此不能编造“线上用了某种类型节省了多少内存”。

真实设计时可以按访问模式做映射：

```text
先写清业务实体和读写动作
→ 是否要求唯一/有序/排名/字段级更新/流式消费
→ 选择最贴合的数据类型
→ 再检查单 key 大小、热点、命令复杂度和过期策略
→ 用真实数据量与压测验证
```

例如用户资料若频繁按字段更新，可以评估 Hash；排行榜天然对应 ZSet；需要消息 ID、待确认消息和 Consumer Group 时应优先评估 Stream，而不是因为“List 可以 push/pop”就默认把 List 当完整消息系统。

## 常见追问

- 问：Redis 基本数据类型通常指哪五种？  
  答：String、List、Hash、Set、Sorted Set（ZSet）。这是经典面试口径，但现代 Redis 的完整数据类型集合不止五种。

- 问：Set 和 ZSet 有什么区别？  
  答：两者 member 都唯一；ZSet 额外给每个 member 一个 score，并按 score 排序，因此能做排名和 score 范围查询。

- 问：Hash 和把整个对象存成 JSON String 有什么区别？  
  答：Hash 能对单个 field 做服务端字段级读写；序列化 String 通常需要应用层整体编码/解码。若需要嵌套 JSON 等更复杂语义，应再评估当前 Redis 的 JSON 能力，而不是把 Hash 说成任意嵌套对象。

- 问：List 和 Stream 怎么选？  
  答：List 适合简单有序队列和两端操作；Stream 是日志式结构，带 entry ID、历史读取和 Consumer Group，更适合需要消息消费状态与流式处理语义的场景。

- 问：Bitmap 是不是独立于 String 的“第六种经典类型”？  
  答：不要这么背。Bitmap 有独立的数据类型文档和命令语义，但其位操作建立在字符串值上。面试中先说明“经典五种”的口径，再把 Bitmap 作为专门结构/能力补充更准确。

- 问：为什么排行榜常用 ZSet？  
  答：因为 member 唯一且天然关联 score，Redis 能按 score/rank 维护和查询顺序，正好匹配“用户 + 分数 + 排名”的数据模型。

- 问：Redis 现在到底一共有多少种数据类型？  
  答：不要给一个脱离版本的永久数字。官方当前数据类型目录已经超过经典五种，而且仍会随版本增加；面试应先答经典核心，再按当前版本补充 Stream、Bitmap/Bitfield、Geospatial 等。

## 易错点

- 直接说“Redis 只有五种数据类型”，把经典面试分类误写成现代 Redis 的完整事实。
- 只背 String/List/Hash/Set/ZSet 名字，却说不出每种表达的数据模型。
- 把 Set 说成可以自然维护排名；需要 score 排序时应想到 ZSet。
- 把 ZSet 说成允许重复 member；它和 Set 一样要求 member 唯一，只是多了 score。
- 把 List 当成具备 Stream Consumer Group、pending/ack 等全部消息语义。
- 把 Hash 说成能无边界表达任意层级嵌套对象。
- 把 Bitmap、Bitfield、Geospatial、Stream 等所有概念和经典五种混在同一口径里硬数数量。
- 背内部编码实现却不带 Redis 版本，容易把旧版本 ziplist 等细节当成当前通用事实。
- 虚构线上命中率、内存节省比例或公司具体用法来填“项目经验”。
