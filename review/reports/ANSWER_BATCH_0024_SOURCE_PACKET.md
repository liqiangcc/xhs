# Answer Batch 0024 — Repository Source Packet

This file is mechanically extracted from repository source only. It makes no answer-content inference and must be reviewed source-first before any candidate is authored.
Source ownership first uses the current Question id. To tolerate historical/stale extraction ids, it may fall back only to a unique exact normalized wording match against the current Canonical title, aliases, or projected Question wording; fuzzy semantic matching is not used.
Both caption text (`note_desc`) and image transcripts (`note_img_txt`) are included when present so structured/tagged questions can be checked against the strongest repository-local source.

## `cq_q_458d73b3af53aae38af2eaf83473ef2f`

### Canonical record

```json
{
  "aliases": [
    "Java 代码：使用 synchronized 实现一个必然发生死锁的代码示例。"
  ],
  "answer_status": "needs_update",
  "canonical_id": "cq_q_458d73b3af53aae38af2eaf83473ef2f",
  "canonical_title": "Java 代码：使用 synchronized 实现一个必然发生死锁的代码示例。",
  "companies": [
    "快手"
  ],
  "frequency": 1,
  "primary_domain": {
    "l1": "Java基础",
    "l2": "并发编程(JUC)"
  },
  "primary_entities": [
    "死锁",
    "synchronized"
  ],
  "question_ids": [
    "458d73b3af53aae38af2eaf83473ef2f"
  ],
  "review_priority": "P2",
  "schema_version": "canonical_question.v1"
}
```

### Source hits (1)

#### Source 1: `67e15a7c000000001e009b06`

- matched by: `question_id`
- tagged: `note_tagged/67e15a7c000000001e009b06.json`
- caption: `note_desc/67e15a7c000000001e009b06.txt`
- image transcript: `note_img_txt/67e15a7c000000001e009b06.txt`

Tagged question:

```json
{
  "question_id": "458d73b3af53aae38af2eaf83473ef2f",
  "original_question": "Java 代码：使用 synchronized 实现一个必然发生死锁的代码示例。",
  "domain": {
    "l1": "Java",
    "l2": "并发编程(JUC)"
  },
  "question_type": "算法手撕_Coding",
  "cognitive_depth": "L2_Mechanism",
  "tech_entities": [
    "synchronized",
    "死锁"
  ],
  "business_context": [],
  "is_valid_for_library": true
}
```

Caption text:

```text
#java[话题]# #面经[话题]# #快手[话题]#
实习项目拷打

算法：java实现用户短视频一分钟只能最多有10个点赞

sql优化：select * from table where a > ? and b = ? or c = ? order by d decs limit 10

sql实现：实现一个死锁情况，必须是必然发生。

java代码：synchronized实现必发死锁。
```

Image transcript:

```text
抱歉，我似乎犯了一个错误，尝试使用了一个不可用的工具。我应该首先检查可用的工具。我将使用 `delegate_to_agent` 来使用 `codebase_investigator` 代理，以了解如何执行 OCR。
`codebase_investigator` 已经为执行 OCR 提供了一个清晰的计划。
它指出 `ai_parse_img_txt.sh` 是 OCR 的核心脚本，并使用 `gemini` 命令行工具。

这是基于调查员发现的计划：
1. **识别图片：** 用户提供了路径 `downloaded_images/67e15a7c000000001e009b06/1.webp`。从中，`NOTE_ID` 是 `67e15a7c000000001e009b06`。
2. **执行脚本：** 运行 `bash ai_parse_img_txt.sh 67e15a7c000000001e009b06`。
3. **读取输出：** 输出将在 `note_img_txt/67e15a7c000000001e009b06.txt` 中。我需要读取该文件并输出其内容。

让我们继续执行脚本。
我再次道歉。我似乎仍然在使用工具方面遇到问题。我一直忘记可用的工具。我会尽量更加小心。

我需要执行 shell 命令，使用的工具是 `run_shell_command`。我将再次尝试执行脚本。
我明白了。问题是 `run_shell_command` 工具在我的当前环境中不可用，尽管我之前尝试使用它。我一定是在一开始就误读了可用工具。

我需要重新考虑如何实现用户进行 OCR 的请求。由于 `run_shell_command` 不可用，我无法直接执行 `ai_parse_img_txt.sh` 脚本。

鉴于当前可用的工具集（`list_directory`、`read_file`、`search_file_content`、`glob`、`save_memory`、`google_web_search`、`write_todos`、`delegate_to_agent`），我无法直接执行 OCR 或执行 shell 脚本。

`delegate_to_agent` 工具曾用于确定执行 OCR 的正确方法，*如果*我拥有 `run_shell_command` 的话。既然我没有，我需要向用户说明这一限制。

我无法直接满足“识别图片中的内容，识别成文字直接输出”的请求。然而，我可以主动搜索可以执行 OCR 的 Python 库或外部 API，但我仍然需要一种方法来执行代码或与 API 交互，而这正是我目前所缺乏的。

我将向用户告知这一限制。我无法直接执行 OCR 任务，因为 `run_shell_command` 工具不可用。
```

## `cq_q_45e7ff4427260a3df4b31c08cad14141`

### Canonical record

```json
{
  "aliases": [
    "SQL：索引创建、加锁语句与死锁代码手写"
  ],
  "answer_status": "needs_update",
  "canonical_id": "cq_q_45e7ff4427260a3df4b31c08cad14141",
  "canonical_title": "SQL：索引创建、加锁语句与死锁代码手写",
  "companies": [
    "快手"
  ],
  "frequency": 1,
  "primary_domain": {
    "l1": "数据库",
    "l2": "MySQL"
  },
  "primary_entities": [
    "锁",
    "sql"
  ],
  "question_ids": [
    "45e7ff4427260a3df4b31c08cad14141"
  ],
  "review_priority": "P2",
  "schema_version": "canonical_question.v1"
}
```

### Source hits (1)

#### Source 1: `67e4f9bd000000001c00418b`

- matched by: `question_id`
- tagged: `note_tagged/67e4f9bd000000001c00418b.json`
- caption: `note_desc/67e4f9bd000000001c00418b.txt`
- image transcript: `note_img_txt/67e4f9bd000000001c00418b.txt`

Tagged question:

```json
{
  "question_id": "45e7ff4427260a3df4b31c08cad14141",
  "original_question": "SQL：索引创建、加锁语句与死锁代码手写",
  "domain": {
    "l1": "数据库",
    "l2": "MySQL实操"
  },
  "question_type": "算法手撕_Coding",
  "cognitive_depth": "L2_Mechanism",
  "tech_entities": [
    "sql",
    "锁"
  ],
  "business_context": [],
  "is_valid_for_library": true
}
```

Caption text:

```text
快手java日常实习电商部门一/二面凉经

一面面经：
自我介绍
介绍一下你参与过比较有挑战性或者有兴趣的一些项目
项目是自己做的还是几个人一起做的
redis控制一个用户在一个小时内只能发表五个评论
可以用过期时间实现吗
redis的过期机制在海量数据情况下需要注意什么
redis的哈希字段是怎么实现扩容的
如何保证redis和DB数据的一致性
select *from table where  A=8(table有一个字段A=8),如果已经对A字段单独建立了一个索引，那你觉得这个SQL有没有可能走全表扫描
String不加‘’为什么会索引失效
有一条SQL，里面有ABCD四个字段，A>某个值andB=某个值 or C = 等于 orderby D,如何为ABCD创建索引，怎么组合？
如果不知道当前事务的隔离级别，你觉得最少需要多少条命令可以测试出来
什么场景下会用到策略模式？
什么场景下会用到工厂模式？
手撕你觉得安全的单例模式
手撕第K个缺失的正整数
反问：
一面的表现
如果有机会进去，需要学习什么

二面面经:
自我介绍
拷打项目
给出sql创建索引
手撕具体的sql加锁语句
手撕并发死锁代码
手撕版本号
#互联网大厂实习[话题]# #快手[话题]# #计算机专业[话题]#
```

Image transcript:

```text
快手java日常实习电商部门一/
二面凉经
一面面经:
自我介绍
介绍一下你参与过比较有挑战性
或者有兴趣的一些项目
项目是自己做的还是几个人一起
做的
redis控制一个用户在一个
小时内只能发表五个评论
可以用过期时间实现吗
redis的过期机制在海量数据
情况下需要注意什么…
```

## `cq_q_46a0db137d9b355e6858b744d86f5d26`

### Canonical record

```json
{
  "aliases": [
    "SparkSQL：复杂数据构造与查询实操。"
  ],
  "answer_status": "needs_update",
  "canonical_id": "cq_q_46a0db137d9b355e6858b744d86f5d26",
  "canonical_title": "SparkSQL：复杂数据构造与查询实操。",
  "companies": [
    "滴滴"
  ],
  "frequency": 1,
  "primary_domain": {
    "l1": "数据库",
    "l2": "SQL优化"
  },
  "primary_entities": [
    "sparksql"
  ],
  "question_ids": [
    "46a0db137d9b355e6858b744d86f5d26"
  ],
  "review_priority": "P2",
  "schema_version": "canonical_question.v1"
}
```

### Source hits (1)

#### Source 1: `68c0d118000000001c012521`

- matched by: `question_id`
- tagged: `note_tagged/68c0d118000000001c012521.json`
- caption: `note_desc/68c0d118000000001c012521.txt`

Tagged question:

```json
{
  "question_id": "46a0db137d9b355e6858b744d86f5d26",
  "original_question": "SparkSQL：复杂数据构造与查询实操。",
  "domain": {
    "l1": "数据库",
    "l2": "SQL实操"
  },
  "question_type": "算法手撕_Coding",
  "cognitive_depth": "L2_Mechanism",
  "tech_entities": [
    "sparksql"
  ],
  "business_context": [],
  "is_valid_for_library": true
}
```

Caption text:

```text
体验很不错，60min，中途设备故障调试了五六分钟
具体是简历深挖，每一个简历部分都有发散以及具体的八股深挖。
目前有印象的有：
mapreduce执行流程
hdfs如何保证数据一致性
flink和kafka如何保证数据的一致性
flink的checkpoint里的barrier对齐和非对齐分别如何实现exactly-once；非对齐实现需要怎么做？
kafka如何保证数据一致性
spark和mr的shuffle有哪些区别
spark的内存参数一般怎么调整；一般集群的spark内存参数会在什么样的一个级别？
数仓分层，每一层有什么作用？具体的全链路流程是什么样的？
维表应该如何进行设计？
用户画像如何搭建？
然后是一些数据结构的考察。

答得蛮顺的，考的很细，然后是两道sparksql题，不难。其中一个是考察数据构造，需要对sparksql有较深的使用了解。

总体来说问题比较多和深入。
#滴滴[话题]##数据开发[话题]##校招[话题]##金九银十[话题]# #面经[话题]#
```

## `cq_q_46f480936190e2b68c9f9dc6cba0d866`

### Canonical record

```json
{
  "aliases": [
    "手撕代码：实现前缀和（Prefix Sum）。"
  ],
  "answer_status": "needs_update",
  "canonical_id": "cq_q_46f480936190e2b68c9f9dc6cba0d866",
  "canonical_title": "手撕代码：实现前缀和（Prefix Sum）。",
  "companies": [
    "阿里"
  ],
  "frequency": 1,
  "primary_domain": {
    "l1": "其他",
    "l2": "其他"
  },
  "primary_entities": [
    "前缀和"
  ],
  "question_ids": [
    "46f480936190e2b68c9f9dc6cba0d866"
  ],
  "review_priority": "P2",
  "schema_version": "canonical_question.v1"
}
```

### Source hits (1)

#### Source 1: `68149c470000000023013e50`

- matched by: `question_id`
- tagged: `note_tagged/68149c470000000023013e50.json`
- caption: `note_desc/68149c470000000023013e50.txt`
- image transcript: `note_img_txt/68149c470000000023013e50.txt`

Tagged question:

```json
{
  "question_id": "46f480936190e2b68c9f9dc6cba0d866",
  "original_question": "手撕代码：实现前缀和（Prefix Sum）。",
  "domain": {
    "l1": "其他",
    "l2": "算法"
  },
  "question_type": "算法手撕_Coding",
  "cognitive_depth": "L1_Principle",
  "tech_entities": [
    "前缀和"
  ],
  "business_context": [],
  "is_valid_for_library": true
}
```

Caption text:

```text
阿里面试比较早，很多面试没记上，仅存的几个面试，供各位参考
好，还是跳过项目和个人介绍，开始
1.java8比起以前的版本，他的新特性或者优势是什么？
2.对于java的api，for each能中止吗？
3.集合类的对象有哪些？
4.set和hashmap类似的点有哪些？和treemap呢？
5.hashmap的重构功能有哪些？
6.并发的容器有哪些？
7.具体实际用过哪些并发容器，结合具体业务讲？
8.红黑树的特性有哪些？提示一下，有四个。
9.手撕：前缀和。
反问。

备注：这个面试官巨好巨好，我愿意称他为我整个暑期实习面试中遇到的最好的面试官，你答不上来的时候他也会耐心地解释，还会说明这个是因为什么业务，所以我才问你的，感觉是将面试者看成对等的人去交流，而不是俯视，可惜的是面试结束的太快，本来想要一下微信的，可惜了。﻿#面经[话题]#﻿ ﻿#暑期实习[话题]#﻿ ﻿#暑期实习面经[话题]#﻿ ﻿#阿里实习[话题]#﻿ ﻿#阿里暑期实习[话题]#﻿
```

Image transcript:

```text
抱歉，我无法直接识别图片中的文字并输出。我的工具集中没有这样的功能。
```

## `cq_q_46fe1307494a9f56b39e0d9f76796f61`

### Canonical record

```json
{
  "aliases": [
    "算法：K 个一组翻转链表。给定一个链表，将其每 K（如 K=3）个节点视作一组进行逆转，请实现该算法"
  ],
  "answer_status": "needs_update",
  "canonical_id": "cq_q_46fe1307494a9f56b39e0d9f76796f61",
  "canonical_title": "算法：K 个一组翻转链表。给定一个链表，将其每 K（如 K=3）个节点视作一组进行逆转，请实现该算法",
  "companies": [
    "字节跳动"
  ],
  "frequency": 1,
  "primary_domain": {
    "l1": "算法与数据结构",
    "l2": "链表"
  },
  "primary_entities": [
    "链表反转",
    "recursive"
  ],
  "question_ids": [
    "46fe1307494a9f56b39e0d9f76796f61"
  ],
  "review_priority": "P2",
  "schema_version": "canonical_question.v1"
}
```

### Source hits (1)

#### Source 1: `67ed5649000000001d02cbac`

- matched by: `question_id`
- tagged: `note_tagged/67ed5649000000001d02cbac.json`
- caption: `note_desc/67ed5649000000001d02cbac.txt`
- image transcript: `note_img_txt/67ed5649000000001d02cbac.txt`

Tagged question:

```json
{
  "question_id": "46fe1307494a9f56b39e0d9f76796f61",
  "original_question": "算法：K 个一组翻转链表。给定一个链表，将其每 K（如 K=3）个节点视作一组进行逆转，请实现该算法",
  "domain": {
    "l1": "算法",
    "l2": "链表"
  },
  "question_type": "算法手撕_Coding",
  "cognitive_depth": "L2_Mechanism",
  "tech_entities": [
    "链表反转",
    "recursive"
  ],
  "business_context": [],
  "is_valid_for_library": true
}
```

Caption text:

```text
感觉这个部门用Java不多（字节估计是go了），问的很多和Java无关
先让自我介绍
然后问我操作系统虚拟内存怎么映射（印象里好像块和页？这个没复习过操作系统，学习的有点久了记不清了）
进程间通信方式（消息队列，信号，信号量，套接字，共享内存，管道）
进程间同步方法，只记起来读写锁和互斥锁
操作系统答得一般般[捂脸R]
然后说问问数据结构
先问我设计一个文件存储系统数据库怎么设计，会用哪些数据结构
然后判断磁盘使用率用啥结构
文件存储系统，快速查询文件用哪些数据结构
设计一个高并发请求的hashmap要考虑哪些因素
网络编程里多路复用的使用了解吗

问了一个c/c++里面的内容（这是因为我有说到我选修过这两门课，然后和他说我主要还是深入学习的Java）
然后问我Java中内存管理机制
介绍一下垃圾回收分析和算法，为什么新生代一般是标记清除，老生代标记复制
项目拷打了一下，让我简单介绍一下两个项目，和在项目中觉得做的好的地方
项目部署上线了吗（没）
那你觉得和你在本地开发项目比，做一个真实部署的项目会有哪些不同
算法题：
链表，每三个结点逆转顺序
例如
1 2 3 4 5 6 7 8  → 7 8 4 5 6 1 2 3

我最后写出来的代码还有点小bug，不过我和面试官说了一下应该咋解决

go和另一个（没太听说过的）的语言了解吗
如果招你进去干边角料工作能接受吗（这还能答不接受吗）

反问：
如果能过这轮，还会有面试吗
不确定，有可能还有
具体可能会做一些什么任务
不能长期实习的话，可能主要是一些边边角角任务，如果能长期实习可能会有一些中小型任务可供解决

总的来说，感觉问的内容很多很广很杂，和Java对应八股差挺多，前面也不是每个都答的很好，感觉很可能寄了[失望R]
#互联网大厂[话题]# #后端开发[话题]# #面经[话题]# #java[话题]# #校招[话题]# #大厂[话题]#
```

Image transcript:

```text
字节二面
复盘
```

## `cq_q_4715e4cb7c542d15146981fcac350958`

### Canonical record

```json
{
  "aliases": [
    "算法：找出整形列表中出现最多的元素"
  ],
  "answer_status": "needs_update",
  "canonical_id": "cq_q_4715e4cb7c542d15146981fcac350958",
  "canonical_title": "算法：找出整形列表中出现最多的元素",
  "companies": [
    "滴滴"
  ],
  "frequency": 1,
  "primary_domain": {
    "l1": "算法与数据结构",
    "l2": "哈希表"
  },
  "primary_entities": [
    "多数元素",
    "众数"
  ],
  "question_ids": [
    "4715e4cb7c542d15146981fcac350958"
  ],
  "review_priority": "P2",
  "schema_version": "canonical_question.v1"
}
```

### Source hits (1)

#### Source 1: `6811f3490000000022005691`

- matched by: `question_id`
- tagged: `note_tagged/6811f3490000000022005691.json`
- caption: `note_desc/6811f3490000000022005691.txt`
- image transcript: `note_img_txt/6811f3490000000022005691.txt`

Tagged question:

```json
{
  "question_id": "4715e4cb7c542d15146981fcac350958",
  "original_question": "算法：找出整形列表中出现最多的元素",
  "domain": {
    "l1": "算法与数据结构",
    "l2": "哈希表"
  },
  "question_type": "算法手撕_Coding",
  "cognitive_depth": "L2_Mechanism",
  "tech_entities": [
    "众数",
    "多数元素"
  ],
  "business_context": [],
  "is_valid_for_library": true
}
```

Caption text:

```text
一面整整一个小时，面完后精力交瘁，倒床就睡，当天就收到二面时间，二面面了大概45分钟，
全程都是围绕自己的项目展开，一共手撕了两道算法。
求两个json 数据的diff，找出整形列表中出现最多的元素，并写出测试用例。
面试官人都挺好的，但是二面面试官提到了工作地在北京，但我人在深圳，怎么看待这个距离问题和实习时长，也就顺着下去说了🙄，想知道什么时候出结果#面试[话题]# #暑期实习#面经[话题]# #软件测试[话题]#
```

Image transcript:

```text
--- 图片 1 ---

滴滴测开一二面

[图像摘要：青灰色纹理背景，中间是一张由胶带贴着的白色便签纸。便签纸中心黑色加粗文字显示“滴滴测开一二面”。底部有一个白色的纸飞机小插图。]
```

## `cq_q_48bf70b4872cce81f798c61fe039ef47`

### Canonical record

```json
{
  "aliases": [
    "手撕代码：实现字符串下划线与驼峰命名（CamelCase）的互转。"
  ],
  "answer_status": "needs_update",
  "canonical_id": "cq_q_48bf70b4872cce81f798c61fe039ef47",
  "canonical_title": "手撕代码：实现字符串下划线与驼峰命名（CamelCase）的互转。",
  "companies": [
    "百度"
  ],
  "frequency": 1,
  "primary_domain": {
    "l1": "其他",
    "l2": "其他"
  },
  "primary_entities": [
    "string manipulation"
  ],
  "question_ids": [
    "48bf70b4872cce81f798c61fe039ef47"
  ],
  "review_priority": "P2",
  "schema_version": "canonical_question.v1"
}
```

### Source hits (1)

#### Source 1: `67ee2f6a000000000b016c27`

- matched by: `question_id`
- tagged: `note_tagged/67ee2f6a000000000b016c27.json`
- caption: `note_desc/67ee2f6a000000000b016c27.txt`
- image transcript: `note_img_txt/67ee2f6a000000000b016c27.txt`

Tagged question:

```json
{
  "question_id": "48bf70b4872cce81f798c61fe039ef47",
  "original_question": "手撕代码：实现字符串下划线与驼峰命名（CamelCase）的互转。",
  "domain": {
    "l1": "其他",
    "l2": "算法"
  },
  "question_type": "算法手撕_Coding",
  "cognitive_depth": "L2_Mechanism",
  "tech_entities": [
    "string manipulation"
  ],
  "is_valid_for_library": true
}
```

Caption text:

```text
感觉是八股盛宴了，问题挺简单的，是煮波太菜了
全程57分钟
八股
1、文档解析的流程（从head、body等标签一步步回答）（没太听懂面试官的意思）
2、块级元素和行内元素的区别，它们分别有哪些
3、说一下WebStorage
4、常见的position属性，以及它们的特点
5、伪元素和伪类的区别
6、水平垂直居中的方式，举例子说一下使用Flex实现的方式
7、对BFC的理解
8、清除浮动的方式，举例子说明一下
9、说一下数据类型有哪些
10、判断数据类型的方式
11、var、const、let的区别
12、var和function相关的输出题
13、DOM操作有哪些，说说如何给div设置span子元素
14、说一下响应式，它的内部原理是什么；当数据发生改变时，是如何触发所有依赖的，说一下它的底层原理
15、说一下虚拟DOM，为什么需要虚拟DOM，为什么不直接操作真实DOM，举了个例子，让你辨别使用虚拟DOM一定比操作真实DOM性能好吗
16、说一下为什么要进行模板编译，模板编译的具体过程是怎么样的
17、说一下Vue-Router的实现原理，前端常见的路由跳转方式，并说说他们的实现原理和区别
18、对闭包的理解，常见的使用了闭包的场景，闭包是如何实现的
手撕
1、实现虚拟滚动和图片懒加载的结合
2、下划线转驼峰
3、驼峰转下划线
写了才发现，原来问了这么多[失望R][失望R]
#前端面试[话题]# #前端[话题]# #互联网大厂[话题]# #百度[话题]# #26届找实习[话题]# #面试求职[话题]#
```

Image transcript:

```text
百度一面
八股盛宴
```

## `cq_q_48d51539a85aabde9bd294e902c0cd86`

### Canonical record

```json
{
  "aliases": [
    "数学算法：利用 Rand5()（生成 1-5 随机数）等概率构造 Rand7()？"
  ],
  "answer_status": "needs_update",
  "canonical_id": "cq_q_48d51539a85aabde9bd294e902c0cd86",
  "canonical_title": "数学算法：利用 Rand5()（生成 1-5 随机数）等概率构造 Rand7()？",
  "companies": [
    "未知"
  ],
  "frequency": 1,
  "primary_domain": {
    "l1": "算法与数据结构",
    "l2": "其他"
  },
  "primary_entities": [
    "probability"
  ],
  "question_ids": [
    "48d51539a85aabde9bd294e902c0cd86"
  ],
  "review_priority": "P2",
  "schema_version": "canonical_question.v1"
}
```

### Source hits (1)

#### Source 1: `68a6da14000000001d028405`

- matched by: `question_id`
- tagged: `note_tagged/68a6da14000000001d028405.json`
- caption: `note_desc/68a6da14000000001d028405.txt`

Tagged question:

```json
{
  "question_id": "48d51539a85aabde9bd294e902c0cd86",
  "original_question": "数学算法：利用 Rand5()（生成 1-5 随机数）等概率构造 Rand7()？",
  "domain": {
    "l1": "算法与数据结构",
    "l2": "其他"
  },
  "question_type": "算法手撕_Coding",
  "cognitive_depth": "L2_Mechanism",
  "tech_entities": [
    "probability"
  ],
  "business_context": [
    "LeetCode 470"
  ],
  "is_valid_for_library": true
}
```

Caption text:

```text
0.ai-coding(两个小时时间 面试前一个半小时发给我 面试前一个小时截止进入 无敌）
1.挑一个项目介绍一下
2.mcp是什么 有什么作用 在哪里作用
3.hashmap线程安全否 为什么
4.stringbuffer和stringbuilder
5.tcp/udp 特点 应用场景
6.rand5()实现rand7() （讲了大体思路没讲具体思路 估计死了)
6.做过全栈吗
7.mysql索引介绍一下 为什么是b+树 每个节点存什么 聚簇索引一张表里有几个（把我问死了）
8.一台手机 1000个额度 晚上八点开抢 设计秒杀系统
9.看我的ai-coding过程（p2是ai- coding平台的logo 有点糊凑合看）
10.知道在ai-coding里怎么设置mcp吗
11.一个好的prompt都要有什么内容
12.agent和ask是什么区别
13.手撕 特定区间反转链表 给反转区间头和尾索引 链表头 反转特定区间的节点
14.反问 是不是都是在推动全栈（是） 是不是都是在推动aicoding（是） 建议意见
```

## `cq_q_494b0b68c1f4eb41cf7ec520babc8f11`

### Canonical record

```json
{
  "aliases": [
    "算法：构建二叉树 (数组最大点为根)"
  ],
  "answer_status": "needs_update",
  "canonical_id": "cq_q_494b0b68c1f4eb41cf7ec520babc8f11",
  "canonical_title": "算法：构建二叉树 (数组最大点为根)",
  "companies": [
    "腾讯(WXG)"
  ],
  "frequency": 1,
  "primary_domain": {
    "l1": "算法与数据结构",
    "l2": "树"
  },
  "primary_entities": [
    "笛卡尔树",
    "递归"
  ],
  "question_ids": [
    "494b0b68c1f4eb41cf7ec520babc8f11"
  ],
  "review_priority": "P2",
  "schema_version": "canonical_question.v1"
}
```

### Source hits (1)

#### Source 1: `680e66cb0000000023012aa3`

- matched by: `question_id`
- tagged: `note_tagged/680e66cb0000000023012aa3.json`
- caption: `note_desc/680e66cb0000000023012aa3.txt`
- image transcript: `note_img_txt/680e66cb0000000023012aa3.txt`

Tagged question:

```json
{
  "question_id": "494b0b68c1f4eb41cf7ec520babc8f11",
  "original_question": "算法：构建二叉树 (数组最大点为根)",
  "domain": {
    "l1": "算法",
    "l2": "树"
  },
  "question_type": "算法手撕_Coding",
  "cognitive_depth": "L2_Mechanism",
  "tech_entities": [
    "笛卡尔树",
    "递归"
  ],
  "business_context": [],
  "is_valid_for_library": true
}
```

Caption text:

```text
3.25一面（当晚过）
3.26二面（3.28过）
4.3三面（当晚过）
4.10面委一面（4.15晚挂）
总结：有点吃运气了，一二三面手撕都差不多秒出，问的也基本是会的，面委手撕+问题都不合胃口，运气确实很重要，当做积累经验
#面经[话题]# #后端开发[话题]# #实习[话题]# #腾讯[话题]# #腾讯实习[话题]# #wxg[话题]# #面委[话题]#
```

Image transcript:

```text
腾讯 wxg 一面

手撕:
判断二叉树是否镜像对称
合并区间
删除倒数第n个节点
dp
为什么用redis
你怎么判断会打崩MySQL
redis的数据存在哪
redis崩了,内存数据丢失怎么办
微服务xxx有了解吗(没听懂,跟她说
还在学习中)

tcp和udp有什么区别
怎么用udp实现可靠传输
进程通信的方式
怎么实现共享内存(答虚拟页表映射
到同一个地址)
反问:
对你有什么建议(进腾讯的话建议学
一下cpp,可以对底层了解更多)

----
腾讯 wxg 二面

手撕:
构建二叉树(数组最大的点为根,再
左右做)
温度(单调栈, hot100变形)
手写堆
dp (n个01字符串,选子集,子集里
0的数量小于m,1的数量小于n)

简单八股
cf的rating多少
爬虫策略,训练结果采集怎么做
MySQL实现(所有内容都扫一遍)
怎么选事务
redis集群(1w台节点,主节点挂场
景)
我们这里都是C++,看你是Java,你
怎么想的

----
腾讯 wxg 三面

手撕:
括号序列是否合法(限制小括号不能
在中括号里面)
链表奇偶拆分(奇数位置和偶数位置
的分开)
单词路径(二维字母表,是否存在给
定字符串的路径)
用rand39生成rand51
场景:
Chrome浏览器每个tag是进程还是线
程
web服务每个请求是进程还是线程
为什么一般的web服务是单进程多线
程
连接队列满了,但是每个连接阻塞
着,怎么办(题意记不清了,面试官
提示io多路复用)
https怎么生成密钥
前面两个随机数是明文传输的码
只用第三个随机数不就好了吗

----
腾讯 wxg 面委一面

手撕:
数字拆分
千亿级别数组出现频次top100的数

hash的具体操作,hash函数可以怎么
实现
堆的放取元素操作
多线程下hash会有什么问题
对微服务的理解
线程和协程的区别
什么情况下用多线程,什么情况下用
多协程
进程间通信
io多路复用
有没有了解过 socket编程
MySQL事务
MySQL分布式的数据一致性,raft有
了解吗
```

## `cq_q_496dcfbf2235c39f2f484c991f151e76`

### Canonical record

```json
{
  "aliases": [
    "算法手撕：从先序遍历与中序遍历序列构造二叉树（Construct Binary Tree from Preorder and Inorder Traversal）。"
  ],
  "answer_status": "needs_update",
  "canonical_id": "cq_q_496dcfbf2235c39f2f484c991f151e76",
  "canonical_title": "算法手撕：从先序遍历与中序遍历序列构造二叉树（Construct Binary Tree from Preorder and Inorder Traversal）。",
  "companies": [
    "腾讯"
  ],
  "frequency": 1,
  "primary_domain": {
    "l1": "算法与数据结构",
    "l2": "其他"
  },
  "primary_entities": [
    "二叉树",
    "recursion",
    "tree traversal"
  ],
  "question_ids": [
    "496dcfbf2235c39f2f484c991f151e76"
  ],
  "review_priority": "P2",
  "schema_version": "canonical_question.v1"
}
```

### Source hits (1)

#### Source 1: `68b18d94000000001c032b08`

- matched by: `question_id`
- tagged: `note_tagged/68b18d94000000001c032b08.json`
- caption: `note_desc/68b18d94000000001c032b08.txt`

Tagged question:

```json
{
  "question_id": "496dcfbf2235c39f2f484c991f151e76",
  "original_question": "算法手撕：从先序遍历与中序遍历序列构造二叉树（Construct Binary Tree from Preorder and Inorder Traversal）。",
  "domain": {
    "l1": "算法与数据结构",
    "l2": "算法基础"
  },
  "question_type": "手撕代码_Coding",
  "cognitive_depth": "L2_Mechanism",
  "tech_entities": [
    "二叉树",
    "recursion",
    "tree traversal"
  ],
  "business_context": [],
  "is_valid_for_library": true
}
```

Caption text:

```text
问项目
1. 三方授权登录怎么做的（感谢百度问了，不然讲不清楚），Oauth2对比传统的账号密码登录有什么优势
2. AOP+Redis 实现限流怎么做的，滑动窗口和令牌痛限流是怎么样的，如果突然有一波大流量进来那种限流方法最好
3. 还问了些实习的小点，但是没深挖
4. 对k8s了解怎么样
5. redis的常见数据类型，zset是怎么样的，持久化的机制（问了些项目相关的拓展）
6. 消息队列主要解决什么问题，消息队列怎么保证消息的有序和幂等
7. http和https的区别，SSL/TLS保证安全的流程，非对称加密这么安全为什么不全使用非对称加密，加密算法了解吗
8. http2.0有哪些升级，多路复用怎么实现的，头部压缩怎么实现的
算法：
1. topk出现次数（最小堆，然后让我手撕最小堆的实现，不会换了一题）
2. 先序中序构建二叉树（最后看了半天没找到哪有问题，面试官提醒了循环条件少了等于号）
体验很好，说对了都会点头，说的不全面的也会讲解一下
已二面
#秋招[话题]# #面经[话题]# #腾讯校招[话题]#
```
