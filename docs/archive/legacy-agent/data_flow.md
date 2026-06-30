# 面试题库系统 — 数据流转架构 (Data Flow)

> Historical note: this document is archived for context. The current execution plan lives in `docs/refactor/`.

基于前面确定的 3 个核心用例，系统的底层数据就像水流一样，经过层层过滤和浓缩，最终变成你在聊天框里看到的高质量面试题。

整体数据流分为 4 个主阶段：**[原始沉淀] ➔ [AI 提纯] ➔ [脚本浓缩] ➔ [Agent 交互]**

---

## 全景数据流转图

```mermaid
graph TD
    %% 阶段1：原始数据
    subgraph Phase 1: 原始数据沉积区
        A1[原始爬虫结果 note_json/*.json] -->|提取描述文本| B1(note_desc/*.txt)
        A2[杂乱的面经正文，混合了寒暄<br>经验分享和面试题] -.-> B1
    end

    %% 阶段2：AI 提纯
    subgraph Phase 2: AI 萃取车间 (Skill 1 工作流)
        B1 -->|触发 Agent 批量扫描| C1{Gemini大模型<br>结构化提取}
        C1 -->|生成标准JSON| D1(note_structured/*.json)
        
        %% 数据结构展示
        D2[数据形态:<br>- note_id: 123...<br>- company: 百度<br>- round: 一面<br>- questions: ['Q1', 'Q2']] -.-> D1
    end

    %% 阶段3：程序浓缩
    subgraph Phase 3: 程序化降噪与聚合
        D1 -->|触发 Python 去重脚本| E1[聚合处理器<br>文本清洗+相似度计算]
        E1 -->|合并相似问题| F1[(question_bank.json<br>高频题库中心)]
        
        %% 数据结构展示
        F2[数据形态:<br>- 题目: HashMap扩容机制<br>- 频率: 45次<br>- 来源: [百度一面, 阿里二面...]<br>- 标签: JVM/集合] -.-> F1
    end

    %% 阶段4：互动输出
    subgraph Phase 4: 前台交互区 (Skill 2 工作流)
        F1 -->|Agent 实时检索读取| G1((你和 Agent 的对话框))
        G2[你的指令:<br>'复习 JVM'<br>'百度高频题'] -->|发送| G1
        G1 -->|Agent 基于题库出题<br>并生成全真解析| G3[你的屏幕终端]
    end
```

---

## 核心环节数据形态变化 (Data Mutation)

为了让你更直观地看到数据是怎样被“洗干净”的，下面演示一个真实的流转截面：

### 1. 爬到的原始文本 (`note_desc/xxx.txt`)
> "今天去了西二旗百度大厦面试，氛围还不错。面试官是个光头大佬。一开始让我手撕了一个反转链表，然后问了 HashMap 为啥不能并发？如果死锁了你怎么排查？最后问了对加班怎么看。"

### 2. AI 萃取后的单点数据 (`note_structured/xxx.json`)
*(去除了废话，提取了骨架，丢弃了闲聊)*
```json
{
  "note_id": "xxx",
  "meta": { "company": "百度", "position": "Java", "round": "未注明" },
  "questions": [
    "算法：反转链表",
    "HashMap 为什么不能并发？",
    "死锁了如何排查？"
  ]
}
```

### 3. 去重后的中央题库 (`question_bank.json`)
*(当系统处理了 1000 篇面经后，相似问题被合并，形成排行榜)*
```json
{
  "Hashmap线程安全问题": {
    "frequency": 87,
    "tags": ["Java核心", "并发"],
    "sources": [
      {"company": "百度", "note_id": "xxx"},
      {"company": "美团", "note_id": "yyy"}
    ]
  },
  "线上死锁排查": {
    "frequency": 42,
    "tags": ["JVM", "线上监控"],
    "sources": [...]
  }
}
```

### 4. Agent 终端展现 (最终呈现给你的样子)
*你：帮我推一道百度最爱考的并发题。*
**Agent：**
> “没问题。百度考得最多的是并发表里的老熟人（排在第一位，共出现87次）：
> **‘HashMap 为什么不能在多线程下安全使用？’**
> 
> 请尝试回答。给出你的答案后，我会为你提供‘一句话破题’和底层深度剖析。”
