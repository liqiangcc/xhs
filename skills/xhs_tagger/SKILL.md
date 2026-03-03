name: xhs_tagger
description: 输入 note_id，读取 note_structured 下的预处理 JSON，对题目进行多维度知识图谱化打标，并将带 ID 的题库输出到 note_tagged 目录中。
---

# 面试题多维度标签打标技能 (XHS Question Tagger)

## 技能描述
你现在扮演一个**资深的高级架构师和技术面试官**。
你的任务是根据提供的 `note_id`，读取已完成结构化提取的面试题 JSON（`note_structured/{note_id}.json`），对其中的每一道题目进行深度的多维度知识图谱化标定（包括领域、题型、ATLP认知深度、技术实体等），最后将结果输出到 `note_tagged/{note_id}.json` 中。

---

## 执行工作流 (Workflow)

当用户请求执行打标任务并提供 `note_id` 时（如命令：`使用 xhs_tagger 处理 65af99a...`），请严格遵循以下步骤：

1. **检查幂等性 (Idempotency Check)**：
   - 检查目标文件 `note_tagged/{note_id}.json` 是否已存在。
   - 如果已存在（且用户未指定“强制重刷”），告知用户“已完成打标”并跳过。
2. **读取数据源**：
   - 读取 `note_structured/{note_id}.json`。
   - 提取文件中的 `questions` 数组，以及全部元数据字段（`company`, `position`, `round`, `level`, `year`, `date`）作为打标上下文。
   - 如果 `questions` 为空，输出为空数组结束任务。
3. **逐题计算 Hash 与打标**：
   - **生成 question_id**：你**不能**自己心算或猜测 MD5 值。你**必须**使用 `run_command` 工具调用 Python 来计算真实的 MD5 哈希。对每道题执行以下命令（将 `{q}` 替换为原始问题文本）：
     ```bash
     python -c "import hashlib,re; q='{q}'; n=re.sub(r'[^\w\u4e00-\u9fa5]','',q.lower()); print(hashlib.md5(n.encode('utf-8')).hexdigest())"
     ```
     你也可以一次性批量计算所有题目的 Hash，将多个问题写入一个临时 Python 脚本后执行。将命令返回的 32 位小写十六进制字符串作为该题的 `question_id`。
   - **多维度分析**：根据上文定义的分类树，为这道题分配 Domain、Question Type、Cognitive Depth、Tech Entities 等字段。
4. **落地 JSON (Output)**：
   - 将组装好的新 JSON 使用 `write_to_file` 工具写入目标路径 `note_tagged/{note_id}.json`。
   - 在对话框中简要汇报成功打标的题目数量和主要考察的领域（Entity）。

---

## 标签约束契约 (Schema)

生成的 `note_tagged/{note_id}.json` 必须严格遵守如下格式：

```json
{
  "note_id": "{note_id}",
  "source": "小红书",          // 从 structured 原样继承
  "company": "推断的公司名",    // 从 structured 原样继承
  "position": "职位方向",      // 从 structured 原样继承（如 Java后端、前端）
  "round": "面试轮次",         // 从 structured 原样继承（如 一面、HR面）
  "level": "推断的层级分类",    // 从 structured 原样继承（如 校招、社招）
  "year": 2024,                // 从 structured 原样继承
  "date": "未知",              // 从 structured 原样继承
  "tagged_questions": [
    {
      "question_id": "c1f7a8b9d2e43de9f...", // 根据上述规则计算的 MD5
      "original_question": "HashMap 为什么不能并发？",
      "domain": {
        "l1": "Java基础",      //【强枚举】只能从 [Java基础, Spring生态, 数据库, 缓存, 中间件, 操作系统, 计算机网络, 系统设计, 算法与数据结构, 云原生与工程化, 其他] 中选
        "l2": "集合框架"       //【半枚举】参见下方「domain.l2 枚举映射表」，不在列表中时填 "其他"
      },
      "question_type": "原理深度_UnderTheHood", //【强枚举】只能选: [八股文_Concept, 原理深度_UnderTheHood, 场景设计_Scenario, 算法手撕_Coding, 项目深挖_Project, 行为软技_Behavioral]
      "cognitive_depth": "L2_Mechanism",        //【强枚举】基于 ATLP 体系。指代认知深度，只能选: [L1_Principle, L2_Mechanism, L3_Diagnostic, N_A]
      "tech_entities": [                        // 标准化技术实体提取
        "HashMap",
        "并发安全",
        "死链"
      ],
      "business_context": [],   // 场景和项目题，提炼业务场景，如 ["高并发", "电商秒杀"]，无则留空
      "is_valid_for_library": true  // 判断该题是否具有通用复习价值
    }
  ]
}
```

### domain.l2 枚举映射表

| l1 | l2 候选值 |
|---|---|
| Java基础 | 集合框架, 并发编程(JUC), JVM, IO/NIO, 语言特性, Lambda/Stream, 设计模式, 反射与动态代理, 其他 |
| Spring生态 | Spring Core, Spring Boot, Spring MVC, Spring Cloud(Nacos/Gateway/Feign/Sentinel), Spring Security, MyBatis, 其他 |
| 数据库 | MySQL, PostgreSQL, 列式/时序数据库(HBase/ClickHouse), MongoDB, 分库分表, 读写分离, SQL优化, 数据库原理, 其他 |
| 缓存 | Redis, Memcached, 本地缓存, 缓存策略, 其他 |
| 中间件 | Kafka, RocketMQ, RabbitMQ, ZooKeeper, 搜索引擎(Elasticsearch等), Nginx, 分布式任务调度, Dubbo/gRPC, Netty, 其他 |
| 操作系统 | 进程与线程, 内存管理, 文件系统, Linux命令, 其他 |
| 计算机网络 | TCP/IP, HTTP/HTTPS, DNS, 网络安全, 其他 |
| 系统设计 | 分布式架构, 微服务治理, 高可用, 高并发, 分布式事务, 数据一致性, 限流熔断降级, 分布式ID与幂等, 架构模式(DDD/MVC), 其他 |
| 算法与数据结构 | 排序, 树, 图, 动态规划, 字符串, 链表, 栈与队列, 哈希表, 二分查找, 双指针/滑动窗口, 回溯, 贪心, BFS/DFS, 其他 |
| 云原生与工程化 | Docker, Kubernetes, CI/CD, Git, 安全(认证鉴权), 线上排障与性能调优, 其他 |
| 其他 | HR面, 项目管理, 大数据, 其他 |

> **⚠️ 分类防呆原则 (LLM Priority Rules)**：
> 1. 如果提干中有 Spring/Spring Boot/MyBatis 绑定字眼，**优先强制落入** `Spring生态`。
> 2. 如果问题涉及线上 CPU 飙高死锁排查、OOM 内存溢出分析排障工具（如 Arthas/jstack），**优先强制落入** `云原生与工程化 -> 线上排障与性能调优`。
> 3. 如果是多个组件组合使用的架构设计题（如：如何用 Redis 和 MQ 保证秒杀不超卖），**禁止**只选单个存储组件，必须落入大局 `系统设计`。

### is_valid_for_library 判定标准

| 判定 | 典型示例 | 理由 |
|------|----------|------|
| ✅ `true` | `"ConcurrentHashMap 底层原理"` | 通用技术知识点，有复习价值 |
| ✅ `true` | `"场景：高并发秒杀如何设计？"` | 经典架构设计题 |
| ❌ `false` | `"项目介绍"` / `"自我介绍"` | 无技术实质，过于泛化 |
| ❌ `false` | `"HR：目前的规划"` | 纯个人向软技能，不具通用复习价值 |
| ❌ `false` | `"你项目里为什么用 RocketMQ 而不用 Kafka？"` | 纯项目追问，无法脱离简历上下文复习 |

---

## 示例 (Few-Shot Example)

以下示例基于真实数据 `note_structured/65af99a0000000002c037638.json`（京东科技 · 校招 · Java后端），展示 4 种典型题型的标准打标输出。

**输入**（萃取阶段已生成的 `questions` 数组中的 4 道题）：
```
"Redis 有哪些集群模式？"
"ConcurrentHashMap 底层原理"
"场景：高并发秒杀如何设计？"
"HR：为什么选择京东？"
```

**标准输出**（`tagged_questions` 数组中对应的 4 个对象）：

```json
[
  {
    "question_id": "25cce32833b12a6614779ef8a4ae258c",
    "original_question": "Redis 有哪些集群模式？",
    "domain": { "l1": "缓存", "l2": "Redis" },
    "question_type": "八股文_Concept",
    "cognitive_depth": "L1_Principle",
    "tech_entities": ["Redis", "主从复制", "哨兵模式 (Sentinel)", "分片集群 (Cluster)"],
    "business_context": [],
    "is_valid_for_library": true
  },
  {
    "question_id": "7cd087dd8a1dba0e15f94bc8a5357413",
    "original_question": "ConcurrentHashMap 底层原理",
    "domain": { "l1": "Java基础", "l2": "并发编程(JUC)" },
    "question_type": "原理深度_UnderTheHood",
    "cognitive_depth": "L2_Mechanism",
    "tech_entities": ["ConcurrentHashMap", "CAS", "synchronized", "分段锁"],
    "business_context": [],
    "is_valid_for_library": true
  },
  {
    "question_id": "4a574c6a8650c3f47097acaeb75cf311",
    "original_question": "场景：高并发秒杀如何设计？",
    "domain": { "l1": "系统设计", "l2": "分布式架构" },
    "question_type": "场景设计_Scenario",
    "cognitive_depth": "L3_Diagnostic",
    "tech_entities": ["Redis", "消息队列", "限流", "库存扣减"],
    "business_context": ["高并发", "电商秒杀"],
    "is_valid_for_library": true
  },
  {
    "question_id": "10fcba77d4b792dec861fd5918cd0e01",
    "original_question": "HR：为什么选择京东？",
    "domain": { "l1": "其他", "l2": "HR面" },
    "question_type": "行为软技_Behavioral",
    "cognitive_depth": "N_A",
    "tech_entities": [],
    "business_context": [],
    "is_valid_for_library": false
  }
]
```

**要点解读**：
- `Redis 有哪些集群模式？` → 纯知识记忆，标 `L1_Principle`，实体提取出 3 种集群模式
- `ConcurrentHashMap 底层原理` → 考察源码级机制，标 `L2_Mechanism`，归入 `并发编程(JUC)` 而非 `集合框架`
- `场景：高并发秒杀如何设计？` → 前缀 `场景：` 直接锁定为 `场景设计_Scenario`，深度 `L3_Diagnostic`，`business_context` 必须填写
- `HR：为什么选择京东？` → 前缀 `HR：` 直接锁定为 `行为软技_Behavioral`，`is_valid_for_library: false`

---

## 注意事项与原则
* **严禁篡改原题**：`original_question` 必须 100% 保留 `note_structured` 中的原话（包括"算法："、"场景："前缀）。
* **前缀即信号**：如果 `original_question` 以 `算法：` 开头 → `question_type` 必须为 `算法手撕_Coding`；以 `场景：` 开头 → `场景设计_Scenario`；以 `HR：` 开头 → `行为软技_Behavioral`。
* **实体一致性**：`tech_entities` 请尽量使用业界官方标准名称（如将 k8s 统一为 Kubernetes，zookeeper/Zk 统一为 ZooKeeper），切勿提取口语化的动宾短语。
* **Hash一致性**：必须通过 `run_command` 调用 Python 计算真实的 MD5，严禁自行猜测。
