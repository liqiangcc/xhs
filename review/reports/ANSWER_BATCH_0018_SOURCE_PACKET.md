# Answer Batch 0018 — Repository Source Packet

This file is mechanically extracted from repository source only. It makes no answer-content inference and must be reviewed source-first before any candidate is authored.
Both caption text (`note_desc`) and image transcripts (`note_img_txt`) are included when present so that structured/tagged questions can be checked against the strongest repository-local source.

## `cq_q_28ddc5240672730f91363131ba8cc14e`

### Canonical record

```json
{
  "aliases": [
    "算法手撕：字符串模式匹配（Pattern Matching）。"
  ],
  "answer_status": "needs_update",
  "canonical_id": "cq_q_28ddc5240672730f91363131ba8cc14e",
  "canonical_title": "算法手撕：字符串模式匹配（Pattern Matching）。",
  "companies": [
    "未知"
  ],
  "frequency": 1,
  "primary_domain": {
    "l1": "操作系统",
    "l2": "其他"
  },
  "primary_entities": [
    "字符串匹配"
  ],
  "question_ids": [
    "28ddc5240672730f91363131ba8cc14e"
  ],
  "review_priority": "P2",
  "schema_version": "canonical_question.v1"
}
```

### Source hits (1)

#### Source 1: `68c2c62e000000001b01d168`

- tagged: `note_tagged/68c2c62e000000001b01d168.json`
- caption: `note_desc/68c2c62e000000001b01d168.txt`

Tagged question:

```json
{
  "question_id": "28ddc5240672730f91363131ba8cc14e",
  "original_question": "算法手撕：字符串模式匹配（Pattern Matching）。",
  "domain": {
    "l1": "计算机基础",
    "l2": "算法"
  },
  "question_type": "算法手撕_Coding",
  "cognitive_depth": "L1_Principle",
  "tech_entities": [
    "字符串匹配"
  ],
  "business_context": [],
  "is_valid_for_library": true
}
```

Caption text:

```text
1.自我介绍
2.项目拷打
2.1 项目里遇到什么困难，怎么解决的
3.八股
3.1 redis多级缓存一致性
3.2 本地缓存如何删除
3.3 雪崩、缓存穿透、缓存击穿
3.4redis过期策略
3.5消息队列如何保证可靠性
3.6mysql如何解决幻读问题
3.7 g1和cms区别
4.场景题
4.1大量数据的接口优化
4.2亿万级数据库的分库策略
5.反问
6.手撕两道题
6.1模式匹配
6.2topk高频词
#后端开发[话题]# #秋招[话题]# #面经[话题]#
```

## `cq_q_294cb4b4464c886329fda6efb26f3d5a`

### Canonical record

```json
{
  "aliases": [
    "算法：两个无序链表如何找出其值相等的节点,两个链表不相交"
  ],
  "answer_status": "needs_update",
  "canonical_id": "cq_q_294cb4b4464c886329fda6efb26f3d5a",
  "canonical_title": "算法：两个无序链表如何找出其值相等的节点,两个链表不相交",
  "companies": [
    "贝壳找房"
  ],
  "frequency": 1,
  "primary_domain": {
    "l1": "算法与数据结构",
    "l2": "链表"
  },
  "primary_entities": [
    "哈希表",
    "链表"
  ],
  "question_ids": [
    "294cb4b4464c886329fda6efb26f3d5a"
  ],
  "review_priority": "P2",
  "schema_version": "canonical_question.v1"
}
```

### Source hits (1)

#### Source 1: `6678d3f7000000001e013539`

- tagged: `note_tagged/6678d3f7000000001e013539.json`
- caption: `note_desc/6678d3f7000000001e013539.txt`
- image transcript: `note_img_txt/6678d3f7000000001e013539.txt`

Tagged question:

```json
{
  "question_id": "294cb4b4464c886329fda6efb26f3d5a",
  "original_question": "算法：两个无序链表如何找出其值相等的节点,两个链表不相交",
  "domain": {
    "l1": "算法与数据结构",
    "l2": "链表"
  },
  "question_type": "算法手撕_Coding",
  "cognitive_depth": "L3_Diagnostic",
  "tech_entities": [
    "链表",
    "哈希表"
  ],
  "business_context": [],
  "is_valid_for_library": true
}
```

Caption text:

```text
贝壳找房面试体验非常好，按点到达几分钟就安排面试，每一轮的结果几分钟也就会出来然后进行下一轮面试，三轮总耗时大概2个半小时

#面经[话题]#  #java面试[话题]#  #java社招[话题]#  #贝壳找房[话题]#  #后端面试[话题]#  #互联网大厂[话题]#  #计算机面试题[话题]#   #开发[话题]#
```

Image transcript:

```text
【贝壳找房】 Java岗
两个半小时 三轮连面

一面:

1. 算法:给一个整型数字,将其按三
位三位划分并加上逗号,就是12345678
变成12,345,678这样

2. 讲项目,项目是你自己一个人做的
吗,你是如何构思的,有没有一个完整
的需求分析过程,有对其做过压力测试
吗, qps能达到多少,瓶颈是在哪里,
还有没有可以优化的地方,有没有设置
多集群,接口隐藏是如何实现的, md5
使用到了哪里,如果要分布式该怎么做

3. 用redis实现的分布式session和原
生session有什么区别,各自优缺点

--- 图片 1 ---

4. 给你几个字段让你设计其属性
类型,大小,后分析哪些字段适合
建立索引,哪些不适合建立索引,
索引的选择性是什么意思

5. 最左前缀原则知道吗,给你一
个索引再给你一个查询条件判断是
否能用到索引,查询条件的顺序改
变能用到索引吗, where a=5 and
b>=5 c=5这种能否用到索引,为什
么,索引的结构是什么样的

6. redis和mysql有什么区别

7. redis既然是基于内存的那是不
是数据会很容易丢失,就说有持久
化,那么说一下两种持久化吧

--- 图片 2 ---

8. 再来一个算法,实现字符串转换
成整型需要考虑哪些条件,口述即可

9. 讲一下你对jvm了解哪些,讲一下
可达性分析, gcRoot引用,垃圾回收
算法

10. 再来一个算法,两个无序链表如
何找出其值相等的节点,两个链表不
相交

11. ARP协议是干什么的,什么时候会
用到这个协议,跟其同层的还有那些
协议

出去休息一下吧
5分钟后二面

--- 图片 3 ---

二面:

1. 为什么会想到做这个项目,是出于
什么来考虑的,讲一讲你觉得最能体
现你技术含量的地方,然后对项目里
的一些问题进行提问,指出漏洞

2. servlet知道不,讲一下生命周期,
servlet是单例的嘛,如何判断是单例
的,为什么要设计成单例的,是出于
什么情况考虑的

3. servlet和filter之间的关系是怎么
样的,随便说了一点,然后赶紧说自
己对原生servlet的用的很少都用框架
去了,转移话题

4. 死锁知道吗,写一个造成死锁的情
况的代码,卡住了不太会写,就说了
一下死锁的四个必要条件,然后面试
官给了一种情况问其会不会造成死锁

--- 图片 4 ---

5. 多线程有了解过吗, thread类里曾
经有stop()等一些方法,名字忘记
了,为什么这些方法现在被抛弃了?
不知道,面试官说是可能会造成死锁

6. jvm里新生代为什么会分成eden区和
survive区,为什么是8:1:1, 为什么
会有两个survive区? 是出于什么情况
考虑的?

7. syn锁, jvm里面分成偏向锁、轻量
级锁、重量级锁,其之间的转换过程
是怎么样的,各自适用场景是什么样
的,偏向锁情况产生竞争一定会膨胀
成轻量级锁吗,为什么只能单向转换,
比如偏向锁变成轻量级锁变成重量级
锁之后不会在竞争消失之后在回到偏
向锁,必须要重启jvm才行,是出于什
么情况考虑的

--- 图片 5 ---

二面最后:

面试官评价说:

我知道你都刷了很多题看了很多
基础,在问各种知识点你肯定也能哔
啦哔啦说出来,给你一个算法你也能
写出来,所以这些我就不想问了,我
想知道的是你思考问题的过程,知道
这些东西为什么要这么设计,背后的
原理。

然后出去等一下吧,这一轮你过了,
希望能之后见到你

--- 图片 6 ---

三面 (HR面) :

1. 我看你的学院是管理学院，为
什么会来做 java, 你们学院是偏
文还是偏理

2. 你做的项目是出于什么想法而
做的，是实习时的项目还是课程
设计

3. 为什么没有出去找实习

4. 你平常都有一些什么爱好

5. 你觉得对于你来说最有成就感
的一件事是什么,最挫败的是什
么时候

--- 图片 7 ---

6. 说一下你的优点和缺点

7. 工作地点的选择

8. 你有哪些欣赏的互联网公司

9. 你手机里有哪些app, 哪一个是你印象
最深刻的

10. 你对贝壳了解吗,知道我们的前身是
什么吗

11. 你如何看待贝壳的前景

12. 然后你还有什么问题

--- 图片 8 ---

整体感受:

贝壳找房面试体验非常好,
按点到达几分钟就安排面试,
每一轮的结果几分钟也就会
出来然后进行下一轮面试,
三轮总耗时大概 两个半小时

--- 图片 9 ---
```

## `cq_q_297402fd71887dbeb07d182f057a1858`

### Canonical record

```json
{
  "aliases": [
    "算法手撕：大数相乘（Multiply Strings）。"
  ],
  "answer_status": "needs_update",
  "canonical_id": "cq_q_297402fd71887dbeb07d182f057a1858",
  "canonical_title": "算法手撕：大数相乘（Multiply Strings）。",
  "companies": [
    "腾讯"
  ],
  "frequency": 1,
  "primary_domain": {
    "l1": "操作系统",
    "l2": "其他"
  },
  "primary_entities": [
    "字符串"
  ],
  "question_ids": [
    "297402fd71887dbeb07d182f057a1858"
  ],
  "review_priority": "P2",
  "schema_version": "canonical_question.v1"
}
```

### Source hits (1)

#### Source 1: `68ca2ddb0000000013011bbb`

- tagged: `note_tagged/68ca2ddb0000000013011bbb.json`
- caption: `note_desc/68ca2ddb0000000013011bbb.txt`

Tagged question:

```json
{
  "question_id": "297402fd71887dbeb07d182f057a1858",
  "original_question": "算法手撕：大数相乘（Multiply Strings）。",
  "domain": {
    "l1": "计算机基础",
    "l2": "算法"
  },
  "question_type": "算法手撕_Coding",
  "cognitive_depth": "L1_Principle",
  "tech_entities": [
    "字符串"
  ],
  "business_context": [],
  "is_valid_for_library": true
}
```

Caption text:

```text
腾讯技术面经
1、自我介绍 3min
2、讲讲Java、Python、Go三者区别
3、Python比Java快吗，比Go快吗
4、讲讲解释型语言和编译型语言的区别
5、GMP模型
6、Redis ： 一台机器256GB，很多台机器，一共有1T数据，怎么存
7、Redis： 原来访问量1000w QPS，已经最高，现在2000w，怎么优化
8、除了读写分离呢？（可以加资源）
9、数组和链表的区别，体现在内存读取和cpu计算上
算法：大数相乘
#java面试[话题]# #java学习[话题]# #java[话题]# #后端开发[话题]# #计算机专业[话题]# #软件开发[话题]# #java八股文[话题]# #面经[话题]# #面试技巧[话题]# #java培训[话题]# #java白泽[话题]#
```

## `cq_q_2979c00d6ff6c1582ecb289775522412`

### Canonical record

```json
{
  "aliases": [
    "SQL：找出一个用户最长的连续登录天数/子序列?"
  ],
  "answer_status": "needs_update",
  "canonical_id": "cq_q_2979c00d6ff6c1582ecb289775522412",
  "canonical_title": "SQL：找出一个用户最长的连续登录天数/子序列?",
  "companies": [
    "美团"
  ],
  "frequency": 1,
  "primary_domain": {
    "l1": "数据库",
    "l2": "其他"
  },
  "primary_entities": [
    "窗口函数"
  ],
  "question_ids": [
    "2979c00d6ff6c1582ecb289775522412"
  ],
  "review_priority": "P2",
  "schema_version": "canonical_question.v1"
}
```

### Source hits (1)

#### Source 1: `6822deb7000000002100178b`

- tagged: `note_tagged/6822deb7000000002100178b.json`
- caption: `note_desc/6822deb7000000002100178b.txt`

Tagged question:

```json
{
  "question_id": "2979c00d6ff6c1582ecb289775522412",
  "original_question": "SQL：找出一个用户最长的连续登录天数/子序列?",
  "domain": {
    "l1": "数据库",
    "l2": "HQL"
  },
  "question_type": "算法手撕_Coding",
  "cognitive_depth": "L2_Mechanism",
  "tech_entities": [
    "窗口函数"
  ],
  "business_context": [],
  "is_valid_for_library": true
}
```

Caption text:

```text
一面侧重于java基础，数仓理论，大数据组件基础和结合项目的一些常见的优化
二面侧重于深挖项目，针对项目细节去问一些数据相关问题，并引申出一些具体的优化问题，数仓模型问题
三面侧重于对整体架构的理解和技术广度的发散问题

一面：
面试内容：
例行拷打项目，略
1.说说你对数据建模的理解
2.数仓如何分层和分层的好处
3.数仓分层和指标分类之间有什么关系
4.什么是总线矩阵
5.什么样的数仓是一个好数仓
6.什么方法可以落实上面说的数仓
7.缓慢变化维，除了拉链表还有哪些方式
8.什么情况下可以使用map join
9.如何解决大表join大表的数据倾斜
10.Java垃圾回收机制
11.SQL题：波峰波谷，连续三天
12.算法题：字符串最后一个字符长度
13.实习中最大成长点

二面：
面试内容：
日常拷打项目，略
1.算法题：链表节点k个一组翻转
2.算法题： 二 叉 树 遍历
3.SQL题：找 出 最 长 连 续 子 序 (row_number)
4.mapreduce运行过程 spark.shuffle.partitions 的调参 Spark小文件参数
5.怎么确定reduce的数量
6.bucket join优化的原理
7.怎么快速根据spark stage找到对应的代码 主题域划分
8.事实表怎么建模
9.数仓建模过程
10.事务的特性
11.进程和线程区别
12.mysql索引
13.索引的类型
14.索引的前缀原则
15.联合索引a b e 以下哪些可以命中索引
where a= xx and c=xx Where b = xx and c= xx

三面：
面试内容：
再日常先拷打项目
1.有没有用过多维分析引擎，在哪里使用了doris, doris作用是什么，讲一下对doris了解多少
2.学大数据相关的知识在哪学的，通过什么途径；遇到过什么问题
3.讲一下上面问题怎么解决的，调节参数是哪些；为什么这么调参；讲一下参数中增加内存为什么有用；reduce个数 是越大越好吗；调参后任务运行时长优化到多少
4.对数据治理的理解
... ...

💌本份面经由OfferShow精英群用户提供，未经允许，请勿转载
﻿#互联网大厂[话题]#﻿﻿#面经[话题]#﻿﻿#面试经验[话题]#﻿﻿#面试经历[话题]#﻿﻿#互联网大厂面经[话题]#﻿﻿#美团[话题]#﻿ ﻿#美团数据开发[话题]#﻿ ﻿#美团面试[话题]#﻿ ﻿#美团面经[话题]#﻿ ﻿#美团面试经验[话题]#﻿
```

## `cq_q_29ea4b45d754e65e5837153e52ba2abd`

### Canonical record

```json
{
  "aliases": [
    "算法手撕：多线程场景下的转账功能实现（原子性与死锁规避）。"
  ],
  "answer_status": "needs_update",
  "canonical_id": "cq_q_29ea4b45d754e65e5837153e52ba2abd",
  "canonical_title": "算法手撕：多线程场景下的转账功能实现（原子性与死锁规避）。",
  "companies": [
    "未知"
  ],
  "frequency": 1,
  "primary_domain": {
    "l1": "Java基础",
    "l2": "并发编程(JUC)"
  },
  "primary_entities": [
    "多线程",
    "死锁规避",
    "原子性"
  ],
  "question_ids": [
    "29ea4b45d754e65e5837153e52ba2abd"
  ],
  "review_priority": "P2",
  "schema_version": "canonical_question.v1"
}
```

### Source hits (1)

#### Source 1: `68b940e2000000001d00c624`

- tagged: `note_tagged/68b940e2000000001d00c624.json`
- caption: `note_desc/68b940e2000000001d00c624.txt`

Tagged question:

```json
{
  "question_id": "29ea4b45d754e65e5837153e52ba2abd",
  "original_question": "算法手撕：多线程场景下的转账功能实现（原子性与死锁规避）。",
  "domain": {
    "l1": "Java基础",
    "l2": "并发编程"
  },
  "question_type": "算法手撕_Coding",
  "cognitive_depth": "L3_Diagnostic",
  "tech_entities": [
    "多线程",
    "死锁规避",
    "原子性"
  ],
  "business_context": [
    "转账功能"
  ],
  "is_valid_for_library": true
}
```

Caption text:

```text
一面
1.针对项目经历进行深入探讨
2.在团队中的角色以及负责的模块
3.遇到过的线上问题，分析及解决过程
4.项目中性能优化的具体策略
5.项目中分布式事务的实现方式
6.所使用的RPC框架
7.是否了解公司内部框架的设计原理
8.缓存数据同步方案
9.状态同步方案
10.分库分表的相关经验
11.编码测试：多线程场景下的转账功能实现

二面
12. 自我介绍
13. 介绍工作或实习经历
14. 描述所在团队的订单量级、订单系统架构，以及个人负责的模块，并系统性地阐述
15. 系统上线前后的流程差异
16. 主订单与子订单的关系，是否存在重构可能性及优化方式
17. 所使用服务器的配置参数
18. 涉及的领域范围，领域划分的思路及边界界定
19. 使用的RPC框架及其底层原理
20. 算法题：合并链表

三面
1.自我介绍
2.介绍具有挑战性的项目经历
3.订单系统的处理量级
4.子订单与主订单的协同机制
5.可能出现的数据不一致问题及解决方案
6.资金存储位置，对交易链路的了解与介绍
7.数据存储方案的设计思路
8.如有机会加入，感兴趣的技术或业务方向

#面试[话题]# #互联网大厂[话题]# #面试技巧[话题]# #java[话题]# #计算机专业[话题]# #程序员的出路[话题]# #校招[话题]# #求职季[话题]# #大模型[话题]# #面经[话题]#
```

## `cq_q_2a09d0d7980006e66439a361880bc83d`

### Canonical record

```json
{
  "aliases": [
    "算法/OOP：面向对象实现字符串全排列组合功能？"
  ],
  "answer_status": "needs_update",
  "canonical_id": "cq_q_2a09d0d7980006e66439a361880bc83d",
  "canonical_title": "算法/OOP：面向对象实现字符串全排列组合功能？",
  "companies": [
    "未知"
  ],
  "frequency": 1,
  "primary_domain": {
    "l1": "Java基础",
    "l2": "其他"
  },
  "primary_entities": [
    "全排列",
    "oop"
  ],
  "question_ids": [
    "2a09d0d7980006e66439a361880bc83d"
  ],
  "review_priority": "P2",
  "schema_version": "canonical_question.v1"
}
```

### Source hits (1)

#### Source 1: `68cbd296000000000e00c123`

- tagged: `note_tagged/68cbd296000000000e00c123.json`
- caption: `note_desc/68cbd296000000000e00c123.txt`

Tagged question:

```json
{
  "question_id": "2a09d0d7980006e66439a361880bc83d",
  "original_question": "算法/OOP：面向对象实现字符串全排列组合功能？",
  "domain": {
    "l1": "计算机语言",
    "l2": "Java"
  },
  "question_type": "算法手撕_Coding",
  "cognitive_depth": "L2_Mechanism",
  "tech_entities": [
    "全排列",
    "oop"
  ],
  "business_context": [],
  "is_valid_for_library": true
}
```

Caption text:

```text
本来看了很多面经，都是拷打八股和项目，结果我聊了半小时的科研，问的很细，还有解决了什么问题、具体的实现流程、输入输出的具体参数设置、遇到的最难的工程问题等等

手撕：用面向对象的思想写一个solution，实现一个功能：输入一个字符串，输出所有字符组合
追问：写出这个类的拷贝构造、移动构造、拷贝赋值、移动赋值

感觉面试官不是很想理我，淡淡的[哭惹R][哭惹R]

#面经[话题]# #大厂[话题]# #后端开发[话题]# #互联网大厂[话题]# #校招[话题]# #面试求职[话题]# #面试[话题]# #秋招人的精神状态[话题]# #秋招[话题]# #面试问题[话题]#
```

## `cq_q_2a97bfeb868fc672fcabeb1182608de4`

### Canonical record

```json
{
  "aliases": [
    "算法：手写实现二叉树的右视图（Right Side View）"
  ],
  "answer_status": "needs_update",
  "canonical_id": "cq_q_2a97bfeb868fc672fcabeb1182608de4",
  "canonical_title": "算法：手写实现二叉树的右视图（Right Side View）",
  "companies": [
    "百度"
  ],
  "frequency": 1,
  "primary_domain": {
    "l1": "算法与数据结构",
    "l2": "树"
  },
  "primary_entities": [
    "right side view"
  ],
  "question_ids": [
    "2a97bfeb868fc672fcabeb1182608de4"
  ],
  "review_priority": "P2",
  "schema_version": "canonical_question.v1"
}
```

### Source hits (1)

#### Source 1: `67e7d5c3000000000900da5a`

- tagged: `note_tagged/67e7d5c3000000000900da5a.json`
- caption: `note_desc/67e7d5c3000000000900da5a.txt`
- image transcript: `note_img_txt/67e7d5c3000000000900da5a.txt`

Tagged question:

```json
{
  "question_id": "2a97bfeb868fc672fcabeb1182608de4",
  "original_question": "算法：手写实现二叉树的右视图（Right Side View）",
  "domain": {
    "l1": "算法",
    "l2": "树"
  },
  "question_type": "算法手撕_Coding",
  "cognitive_depth": "L2_Mechanism",
  "tech_entities": [
    "right side view"
  ],
  "business_context": [],
  "is_valid_for_library": true
}
```

Caption text:

```text
1. 实习项目难点与解决
问题背景+解决思路+最终效果

2. Redis高并发优化
项目中如何使用Redis的？现在如果并发很大，Redis扛不住的话可以怎么优化？

3. 多层缓存一致性
多层缓存的数据一致性怎么解决？还有其他方案吗？

4. MySQL索引原理
讲讲MySQL的索引的原理，其他引擎或者是其他数据库的索引有没有了解？

5. MySQL主从延迟处理
MySql主从同步有延迟应该怎么处理？

6. MySQL查询压力优化
如果MySQL查询压力大怎么做？

7. 慢SQL排查与优化
慢sql是怎么排查和优化的？

8. 高效索引创建
如何创建正确高效的索引？

9. 大索引数据量问题
索引数据量庞大会造成什么问题？从数据插入和更新的角度来说一下？

10. RabbitMQ vs Kafka
RabbitMQ跟Kafka的区别是什么？

11.  Kafka延迟消息实现
Kafka能实现延迟消息吗？怎么实现？

12. MQ消息消费保证
MQ怎么保证消息消费的？

13. MQ宕机处理
MQ宕机了怎么办？

14. MQ队列满处理
MQ队列满了怎么办？

15. Golang内存泄漏排查
Golang内存泄漏的场景有哪些，怎么排查和优化？

16. 文档去重推荐
场景题：我们现在给用户推荐文档，如何保证用户所被推荐的文档不是重复推荐？

17. 二叉树右视图

#互联网大厂实习[话题]# #互联网大厂[话题]##百度[话题]# #百度实习[话题]#  #职场[话题]# #后端开发[话题]# #大厂面试题[话题]# #面经[话题]# #实习日记[话题]# #找实习[话题]# #春招[话题]#
```

Image transcript:

```text
抱歉，我无法识别图片中的内容并将其转换为文本，因为我没有可用的工具来执行图像识别任务。
```

## `cq_q_2bd82e0bd4203f85f02cca39fb7a67e2`

### Canonical record

```json
{
  "aliases": [
    "SQL进阶：编写SQL查询最大连续天数/次数问题（Max Consecutive Days），详述ROW_NUMBER自减抵消法的实现逻辑"
  ],
  "answer_status": "needs_update",
  "canonical_id": "cq_q_2bd82e0bd4203f85f02cca39fb7a67e2",
  "canonical_title": "SQL进阶：编写SQL查询最大连续天数/次数问题（Max Consecutive Days），详述ROW_NUMBER自减抵消法的实现逻辑",
  "companies": [
    "美团"
  ],
  "frequency": 1,
  "primary_domain": {
    "l1": "数据库",
    "l2": "数据库原理"
  },
  "primary_entities": [
    "递归cte",
    "sql高级查询"
  ],
  "question_ids": [
    "2bd82e0bd4203f85f02cca39fb7a67e2"
  ],
  "review_priority": "P2",
  "schema_version": "canonical_question.v1"
}
```

### Source hits (1)

#### Source 1: `689d4879000000001c008cde`

- tagged: `note_tagged/689d4879000000001c008cde.json`
- caption: `note_desc/689d4879000000001c008cde.txt`

Tagged question:

```json
{
  "question_id": "2bd82e0bd4203f85f02cca39fb7a67e2",
  "original_question": "SQL进阶：编写SQL查询最大连续天数/次数问题（Max Consecutive Days），详述ROW_NUMBER自减抵消法的实现逻辑",
  "domain": {
    "l1": "工程实践",
    "l2": "数据库基础"
  },
  "question_type": "算法手撕_Coding",
  "cognitive_depth": "L2_Mechanism",
  "tech_entities": [
    "sql高级查询",
    "递归cte"
  ],
  "business_context": [
    "分析用户连续活跃天数/签到链路"
  ],
  "is_valid_for_library": true
}
```

Caption text:

```text
一面（40min➕，比较简单，面试官和善）
1.深挖项目，项目架构选型，不同数据为什么存储在不同位置等之类的问题
2.MR工作流程
3.Hive和Spark的区别
4.细挖简历，比如说说简历中复杂SQL的难点在哪里，如何解决
5.认识什么告警类型，都如何处理
6.数据倾斜如何定位，如何解决
7.数仓分层以及分层作用
8.DWS层和DWM层的区别
9.spark的driver,task,job,stage之间的联系
场景题，对直播中的金额数据如何进行数据质量的一个检测
手撕算法:最大子数组和
SQL:最大连续问题

二面（50min➕，主要难在项目拷打，八股很简单）
1.深挖项目非常细节的点，从数据源接入到模型落地的流程和具体实施都问了一遍，有没有出现过比较难解决的问题，特别细节，项目拷打30min左右
2.数仓分层理论
3.数据倾斜解决
4.spark性能优化
5.spark的完整工作流程
6.spark宽窄依赖是什么意思以及宽窄依赖作用
7.说说你个人对数据仓库的理解
8.了解Kappa架构吗，说说
SQL:一道平均数开窗题目

HR面（45min，以为是纯聊天也没有准备啥，没想到问了技术问题）
1.拷打实习，细挖实习的一些内容，产出，实习碰到的难题，如何解决，这里没有准备周到，卡壳了挺多的[哭惹R]
2.处理数据格式的时候出现过什么问题，如何解决
3.有没有出现过数据倾斜等情况，如何解决，你提到的方案是你都用过的吗
4.有没有和mt意见不和的情况如何解决，我说了没有[哭惹R][哭惹R]
5.相比其他候选人你的优势是什么
6.形容一下你自己是什么样的人
7.之前实习干的都是边缘活吗
8.主要做离线还是实时
9.实习犯的错误多吗，举一个犯错的例子，如何解决
10.实习和项目有没有复盘过，说说复盘了什么内容
总的来说，hr面主要拷打实习的产出和实习的一些细节

还有一些其他问题忘记了，想起来再补#互联网大厂[话题]# #大数据开发[话题]#
```

## `cq_q_2c267f2f448a08e8b1f1e1590ce6df72`

### Canonical record

```json
{
  "aliases": [
    "算法：判断树B是否是树A的子结构 ：输入两颗二叉树，判断B是否是A的子结构"
  ],
  "answer_status": "needs_update",
  "canonical_id": "cq_q_2c267f2f448a08e8b1f1e1590ce6df72",
  "canonical_title": "算法：判断树B是否是树A的子结构 ：输入两颗二叉树，判断B是否是A的子结构",
  "companies": [
    "字节跳动"
  ],
  "frequency": 1,
  "primary_domain": {
    "l1": "算法与数据结构",
    "l2": "树"
  },
  "primary_entities": [
    "递归",
    "二叉树",
    "二分查找",
    "子结构"
  ],
  "question_ids": [
    "2c267f2f448a08e8b1f1e1590ce6df72"
  ],
  "review_priority": "P2",
  "schema_version": "canonical_question.v1"
}
```

### Source hits (1)

#### Source 1: `6842998a000000000303f15c`

- tagged: `note_tagged/6842998a000000000303f15c.json`
- caption: `note_desc/6842998a000000000303f15c.txt`

Tagged question:

```json
{
  "question_id": "2c267f2f448a08e8b1f1e1590ce6df72",
  "original_question": "算法：判断树B是否是树A的子结构 ：输入两颗二叉树，判断B是否是A的子结构",
  "domain": {
    "l1": "算法",
    "l2": "树"
  },
  "question_type": "算法手撕_Coding",
  "cognitive_depth": "L2_Mechanism",
  "tech_entities": [
    "二分查找",
    "二叉树",
    "子结构",
    "递归"
  ],
  "business_context": [],
  "is_valid_for_library": true
}
```

Caption text:

```text
字节跳动后端开发三面面经
时间线：
5.23投递
5.26约一面
5.28一面
5.30约了6.3二面
6.4约了6.5三面
三面面试官迟到了5分钟，问八股和项目只有15~20分钟的样子，然后两道算法题，写完第一道算法题后，感觉面试官也是想拖时间，就给了第二道算法题，写完后相互提问快十分钟。
1、讲一下进程、线程、协程（一面和三面面试官都问了这个，可能是因为字节用go开发的原因）
2、用协程做高并发需要注意什么？
3、协程是用户态的如何被操作系统调度？
4、讲一下CAS？
5、项目中使用MySQL、MQ、Redis是怎么考虑的？
6、项目中的压测是如何做的？
7、如何确定你测试得到的TPS是机器的性能瓶颈呢？
8、为什么想到用“采用布隆过滤器判断短链接是否已存在，替代传统分布式锁+查询数据库方案”？
算法题：
1、判断树B是否是树A的子结构 ：输入两颗二叉树，判断B是否是A的子结构
2、接雨水 力扣
问答环节：
1、问了我觉得自己最大的优点是什么？追问让我举例说说。
2、你觉得自己有什么缺点吗？
3、做过基于大模型的项目吗？
4、讲一下MCP？
#后端开发[话题]# #java[话题]# #面经[话题]# #暑期实习[话题]#
```

## `cq_q_2d08f15b8ffa1ba609ca2b53d287984e`

### Canonical record

```json
{
  "aliases": [
    "算法：二叉树中序遍历"
  ],
  "answer_status": "needs_update",
  "canonical_id": "cq_q_2d08f15b8ffa1ba609ca2b53d287984e",
  "canonical_title": "算法：二叉树中序遍历",
  "companies": [
    "滴滴"
  ],
  "frequency": 1,
  "primary_domain": {
    "l1": "算法与数据结构",
    "l2": "树"
  },
  "primary_entities": [
    "二叉树",
    "in-order traversal"
  ],
  "question_ids": [
    "2d08f15b8ffa1ba609ca2b53d287984e"
  ],
  "review_priority": "P2",
  "schema_version": "canonical_question.v1"
}
```

### Source hits (1)

#### Source 1: `666c3aee000000000e03140b`

- tagged: `note_tagged/666c3aee000000000e03140b.json`
- caption: `note_desc/666c3aee000000000e03140b.txt`
- image transcript: `note_img_txt/666c3aee000000000e03140b.txt`

Tagged question:

```json
{
  "question_id": "2d08f15b8ffa1ba609ca2b53d287984e",
  "original_question": "算法：二叉树中序遍历",
  "domain": {
    "l1": "算法",
    "l2": "树"
  },
  "question_type": "算法手撕_Coding",
  "cognitive_depth": "L2_Mechanism",
  "tech_entities": [
    "二叉树",
    "in-order traversal"
  ],
  "is_valid_for_library": true
}
```

Caption text:

```text
一面50min
自我介绍
怼项目
apollo
流程介绍
客户端如何与服务端进行连接
业务端如何与客户端连接，需要的信息手撕
二叉树中序遍历
1-N的硬币，1-N个人从每个硬币走过，如果硬币编号可以整除人编号，硬币翻面，求最后被翻面朝上的硬币有哪些(说思路)
sql
redis
应用场景
跳表
设计模式
工厂，单例，责任链，策略模式应用场景
二面 15min
自我介绍
策略模式
java
hashmap结构
红黑树的限制条件
gc
说垃圾回收器
mysql
索引失效
索引结构
使用的框架，中间件
三面 50min
自我介绍
进程和线程区别
多线程问题锁
计网
http与tcp区别
长连接与短连接
time wait，过多怎么办
数据库
使用注意事项
什么情况不建议使用索引
索引结构
隔离级别
幻读
快照读与当前读如何避免幻读
手撕
100万个ip地址，如何存这些ip地址，需要加入ip地址及判断ip地址是否存在，如何做
ipv4转int
兴趣爱好
优点和缺点
职业规划
#面经[话题]# #滴滴面试题[话题]# #互联网大厂[话题]# #Java[话题]# #经验分享[话题]#
```

Image transcript:

```text
滴滴 Java岗-差点被赛码网搞崩心态
一面 50min

自我介绍
怼项目
apollo
流程介绍
客户端如何与服务端进行连接
业务端如何与客户端连接,需要的信息
手撕
二叉树中序遍历
1-N的硬币,1-N个人从每个硬币走过,如果硬币
编号可以整除人编号,硬币翻面,求最后被翻面朝
上的硬币有哪些 (说思路)
sql
redis
应用场景
跳表
设计模式
工厂,单例,责任链,策略模式应用场景

二面 15min

自我介绍
策略模式
java
hashmap结构
红黑树的限制条件
gc
说垃圾回收器
mysql
索引失效
索引结构
使用的框架,中间件
三面 50min

自我介绍
进程和线程
区别
多线程问题
锁
计网
http与tcp区别
长连接与短连接
time wait,过多怎么办
数据库
使用注意事项
什么情况不建议使用索引
索引结构
隔离级别
幻读
快照读与当前读如何避免幻读
手撕
100万个ip地址,如何存这些ip地址,需要加入ip
地址及判断ip地址是否存在,如何做
ipv4转int
兴趣爱好
优点和缺点
职业规划
```
