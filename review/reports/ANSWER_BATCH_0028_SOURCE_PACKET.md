# Answer Batch 0028 — Repository Source Packet

Mechanically extracted from repository source only; no answer-content inference is made.
Matching is limited to current Question id or a unique exact normalized wording match; fuzzy semantic matching is forbidden.

## `cq_q_59d52495f3df25f0d98935d5e7fa3191`

### Canonical record

```json
{
  "aliases": [
    "SQL：查询在同一天阅读至少两篇文章的用户 ID，并按 ID 升序排序"
  ],
  "answer_status": "needs_update",
  "canonical_id": "cq_q_59d52495f3df25f0d98935d5e7fa3191",
  "canonical_title": "SQL：查询在同一天阅读至少两篇文章的用户 ID，并按 ID 升序排序",
  "companies": [
    "美团"
  ],
  "frequency": 1,
  "primary_domain": {
    "l1": "数据库",
    "l2": "SQL优化"
  },
  "primary_entities": [
    "group by"
  ],
  "question_ids": [
    "59d52495f3df25f0d98935d5e7fa3191"
  ],
  "review_priority": "P2",
  "schema_version": "canonical_question.v1"
}
```

### Source hits (1)

#### Source 1: `67e54e14000000001b0399a0`

- matched by: `question_id`
- tagged: `note_tagged/67e54e14000000001b0399a0.json`
- caption: `note_desc/67e54e14000000001b0399a0.txt`
- image transcript: `note_img_txt/67e54e14000000001b0399a0.txt`

Tagged question:

```json
{
  "question_id": "59d52495f3df25f0d98935d5e7fa3191",
  "original_question": "SQL：查询在同一天阅读至少两篇文章的用户 ID，并按 ID 升序排序",
  "domain": {
    "l1": "数据库",
    "l2": "SQL"
  },
  "question_type": "算法手撕_Coding",
  "cognitive_depth": "L1_Principle",
  "tech_entities": [
    "group by"
  ],
  "business_context": [],
  "is_valid_for_library": true
}
```

Caption text:

```text
美团一面Java
（再次被捞）
面了一个半小时多[笑哭R]八股基本都说了代码sql没问题求进二面[捂脸R]

1.面试官自我介绍（介绍部门）
2.我自我介绍
3.项目结合八股文一起问了一个小时
什么是分库分表
了解读写分离吗 读多写少 高并发查询
我们的分表怎么写的
事务能保证跨库的一致性吗
分表写压力会分散吗

了解分布式事务吗用来解决什么问题
行锁怎么设计的
了解其它锁吗
项目的核心发钱设计解释
解释rocketmq作用 解释mq发送失败存入本地消息表xxl-job扫表
为什么要设计成异步
虚拟红包的概念
mq自身的重试机制 实现原理没答出来
什么业务场景下金额数据会被高频访问
redis的八股文：redis为什么比较快，redis的过期机制
缓存异常：解释缓存穿透雪崩击穿
缓存比预期的要慢可能会是什么问题
怎么去确认 怎么查到cpu和io的使用情况命令行
自己的项目做过压测吗 了解系统容量上限吗
怎么判断系统到达上限了
用一个场景说一下后续怎么优化（绕着db语句索引慢查询结构缓存说了一大堆）
微服务化是为了解决什么的

项目二ddd设计模式介绍 依赖关系介绍
日志监控统计设计 分钟计数法
对本地缓存了解多少
hashmap
了解其他数据结构吗
hashmap是怎么实现的 链表为什么换红黑树
你知道内存泄露吗
threadlocal为什么会导致内存泄露
内存回收机制 具体讲一下垃圾回收算法

手撕：
一个排序后合并区间
一个sql：查询在同一天阅读至少两篇文章的人的id，结果按照id升序排序
```

Image transcript:

```text
美团一面Java
(再次被捞)
```

## `cq_q_5a5db0e8391add20113a1ffec9c1e41b`

### Canonical record

```json
{
  "aliases": [
    "算法手撕：有序链表去除重复元素（保留/去除重复节点）。"
  ],
  "answer_status": "needs_update",
  "canonical_id": "cq_q_5a5db0e8391add20113a1ffec9c1e41b",
  "canonical_title": "算法手撕：有序链表去除重复元素（保留/去除重复节点）。",
  "companies": [
    "快手"
  ],
  "frequency": 1,
  "primary_domain": {
    "l1": "算法与数据结构",
    "l2": "其他"
  },
  "primary_entities": [
    "链表",
    "remove duplicates"
  ],
  "question_ids": [
    "5a5db0e8391add20113a1ffec9c1e41b"
  ],
  "review_priority": "P2",
  "schema_version": "canonical_question.v1"
}
```

### Source hits (1)

#### Source 1: `6826e4210000000003039d41`

- matched by: `question_id`
- tagged: `note_tagged/6826e4210000000003039d41.json`
- caption: `note_desc/6826e4210000000003039d41.txt`

Tagged question:

```json
{
  "question_id": "5a5db0e8391add20113a1ffec9c1e41b",
  "original_question": "算法手撕：有序链表去除重复元素（保留/去除重复节点）。",
  "domain": {
    "l1": "算法与数据结构",
    "l2": "算法基础"
  },
  "question_type": "手撕代码_Coding",
  "cognitive_depth": "L1_Principle",
  "tech_entities": [
    "链表",
    "remove duplicates"
  ],
  "business_context": [],
  "is_valid_for_library": true
}
```

Caption text:

```text
快手社招 java 一二面
📍面试公司：快手
👜面试岗位： java 开发

📖面试问题：

✅一面
1️⃣自我介绍+项目
2️⃣分层缓存架构
3️⃣数据如果只存在 redis 中可以吗
4️⃣DB 中的写压力
5️⃣MQ 有消息积压吗
6️⃣DB 的 TPS
7️⃣怎么分库分表的
8️⃣读写分离
9️⃣如果你们的redis中要新增一个数据，是怎么做的
🔟怎么做的异步重试
1️⃣1️⃣redis 中是什么形式来存的数据
1️⃣2️⃣如果突然有很多数据要写进redis了，有什么措施
1️⃣3️⃣如果缓存了 5 页数据，这个时候新增加了一条，会发生什么
1️⃣4️⃣每台实例上的本地缓存都要存储所有的数据信息吗
1️⃣5️⃣如果数据越来越多会对本地缓存造成什么影响
1️⃣6️⃣本地缓存淘汰策略
1️⃣7️⃣秒杀场景下单全流程
1️⃣8️⃣库存回刷
1️⃣9️⃣有一笔订单用户取消了，这个时候 redis 成功了但是数据库没成功，会发生什么
2️⃣0️⃣如果你们在凌晨对账同步的时候刚好碰上用户下单呢
2️⃣1️⃣被拦截的用户会看到什么报错
2️⃣2️⃣具体加了什么锁
2️⃣3️⃣分布式锁的原理是什么
2️⃣4️⃣回删完成后怎么解锁
2️⃣5️⃣锁的安全性怎么保证
2️⃣6️⃣为什么你们释放锁的时候需要用一个唯一的 id 做校验
2️⃣7️⃣threadLocal 怎么做到线程安全的
2️⃣8️⃣threadLocalMap 和 HashMap 的区别
2️⃣9️⃣ThreadLocal怎么避免内存泄漏
3️⃣0️⃣AtomicInteger 类，这个类是线程安全的吗，原理是什么
3️⃣1️⃣线程池调度机制
3️⃣2️⃣Synchronized 和 reentrantlock的区别
3️⃣3️⃣select * from t where a = 100 and b > 100 and b <= 1000 and c = 10，给这个 sql 创建索引
innodb 默认事务隔离级别
3️⃣4️⃣可重复读和读已提交的区别
✍🏻算法题：有序链表去除重复元素 给出1→2→3→3→4→4→5，返回1→2→5

🙌面试体验：面试节奏很和谐

因为篇幅限制
二面与其他详情请看图片
#后端开发[话题]# #计算机专业[话题]# #互联网大厂[话题]# #计算机[话题]# #互联网大厂实习[话题]# #java[话题]# #面经[话题]# #快手面试[话题]# #快手面经[话题]#
```

## `cq_q_5a87a04d4bc934eadb1cf42e28fcaed2`

### Canonical record

```json
{
  "aliases": [
    "算法：如何实现 IPv4 地址字符串与 32 位整数 (int) 之间的转换？"
  ],
  "answer_status": "needs_update",
  "canonical_id": "cq_q_5a87a04d4bc934eadb1cf42e28fcaed2",
  "canonical_title": "算法：如何实现 IPv4 地址字符串与 32 位整数 (int) 之间的转换？",
  "companies": [
    "滴滴"
  ],
  "frequency": 1,
  "primary_domain": {
    "l1": "算法与数据结构",
    "l2": "字符串"
  },
  "primary_entities": [],
  "question_ids": [
    "5a87a04d4bc934eadb1cf42e28fcaed2"
  ],
  "review_priority": "P2",
  "schema_version": "canonical_question.v1"
}
```

### Source hits (1)

#### Source 1: `67ed2207000000001c03db4e`

- matched by: `question_id`
- tagged: `note_tagged/67ed2207000000001c03db4e.json`
- caption: `note_desc/67ed2207000000001c03db4e.txt`
- image transcript: `note_img_txt/67ed2207000000001c03db4e.txt`

Tagged question:

```json
{
  "question_id": "5a87a04d4bc934eadb1cf42e28fcaed2",
  "original_question": "算法：如何实现 IPv4 地址字符串与 32 位整数 (int) 之间的转换？",
  "domain": {
    "l1": "算法",
    "l2": "字符串"
  },
  "question_type": "算法手撕_Coding",
  "cognitive_depth": "L2_Mechanism",
  "tech_entities": [],
  "business_context": [],
  "is_valid_for_library": true
}
```

Caption text:

```text
一面 50min
自我介绍怼项目 apollo流程介绍
客户端如何与服务端进行连接
业务端如何与客户端连接，需要的信息手撕
二叉树中序遍历
1-N的硬币，1-N个人从每个硬币走过，如果硬币编号可以整除人编号，硬币翻面，求最后被翻面朝上的硬币有哪些(说思路) sql redis应用场景跳表
设计模式
工厂，单例，责任链，策略模式应用场景二面15min
自我介绍策略模式 java
hashmap结构红黑树的限制条件 gc
说垃圾回收器 mysql索引失效索引结构
使用的框架，中间件三面50min
自我介绍进程和线程区别
多线程问题锁计网
http与tcp区别长连接与短连接
time wait，过多怎么办数据库
使用注意事项
什么情况不建议使用索引索引结构隔离级别幻读
快照读与当前读如何避免幻读手撕
100万个ip地址，如何存这些ip地址，需要加入ip地址及判断ip地址是否存在，如何做 ipv4转int兴趣爱好优点和缺点职业规划
#面经[话题]# #面试真题[话题]# #滴滴面试题[话题]# #java[话题]# #程序员[话题]# #计算机专业[话题]# #互联网大厂[话题]# #经验分享[话题]#
```

Image transcript:

```text
我将使用 `img_2_txt.sh` 脚本来识别图片中的文本。
我无法直接执行 shell 命令，因此无法使用 `img_2_txt.sh` 脚本进行图片文字识别。我的工具集中没有直接进行 OCR 的功能。

为了更好地理解情况，我将尝试读取 `img_2_txt.sh` 脚本的内容。
我已阅读 `img_2_txt.sh` 脚本，它似乎是一个协调器，调用另一个名为 `ai_parse_img_txt.sh` 的脚本进行实际的图像处理。由于我无法执行 shell 命令，因此我无法运行这些脚本，也无法直接执行 OCR（光学字符识别）。

我的工具集中没有 OCR 功能。我需要提取用户提供的特定图片中的文本，但我无法执行此操作。

我将尝试使用 `google_web_search` 查找如何在 Linux 命令行上执行 WebP 图像的 OCR，以查看是否有任何替代方法可以完成此任务。
`google_web_search` 没有提供关于如何在 Linux 命令行上对 WebP 图像执行 OCR 的结果。由于我无法执行 shell 命令，也无法通过其他工具实现 OCR，我无法完成用户请求的图片文字识别任务。

我将通过 `write_todos` 工具将此任务标记为已取消，以表明无法完成此操作。
任务已取消。由于工具限制，我无法完成请求。我现在等待用户的进一步指示。
```

## `cq_q_5aa1b6ca0f00362ffc20d3cf8bc5f266`

### Canonical record

```json
{
  "aliases": [
    "算法：轮转数组 (LeetCode 189)，要求 O(1) 空间复杂度，O(n) 时间复杂度"
  ],
  "answer_status": "needs_update",
  "canonical_id": "cq_q_5aa1b6ca0f00362ffc20d3cf8bc5f266",
  "canonical_title": "算法：轮转数组 (LeetCode 189)，要求 O(1) 空间复杂度，O(n) 时间复杂度",
  "companies": [
    "滴滴"
  ],
  "frequency": 1,
  "primary_domain": {
    "l1": "算法与数据结构",
    "l2": "双指针/滑动窗口"
  },
  "primary_entities": [
    "轮转",
    "数组",
    "原地操作"
  ],
  "question_ids": [
    "5aa1b6ca0f00362ffc20d3cf8bc5f266"
  ],
  "review_priority": "P2",
  "schema_version": "canonical_question.v1"
}
```

### Source hits (1)

#### Source 1: `66aa37d6000000000d0316b9`

- matched by: `question_id`
- tagged: `note_tagged/66aa37d6000000000d0316b9.json`
- caption: `note_desc/66aa37d6000000000d0316b9.txt`

Tagged question:

```json
{
  "question_id": "5aa1b6ca0f00362ffc20d3cf8bc5f266",
  "original_question": "算法：轮转数组 (LeetCode 189)，要求 O(1) 空间复杂度，O(n) 时间复杂度",
  "domain": {
    "l1": "算法",
    "l2": "数组"
  },
  "question_type": "算法手撕_Coding",
  "cognitive_depth": "L2_Mechanism",
  "tech_entities": [
    "数组",
    "轮转",
    "原地操作"
  ],
  "business_context": [],
  "is_valid_for_library": true
}
```

Caption text:

```text
1，自我介绍
2，Base地倾向 最好就是回答没有倾向 哪都能去 我当时头铁说不去北京
3，算法：lc189 轮转数组 要求：空间复杂度O(1)，时间复杂度O(n)
滴滴算法题特点：
1，在线写代码比较难用
2，我这两次面试的面试官都都没要求运行，他们就看代码看看对不对
4，算法看我用到了取模 就问我负数取模是正数还是负数
5，展开讲下sql调优
（1）数据量
（2）索引 （sql select本身）
分库有啥要注意的 跨表关联和分页怎么尽可能落到一个表里
6，引入一个新的中间件（消息队列）
对一些异常的场景，你如何去监控发现和保证数据的一致性
面试官给的例子：
如果这时候 binlog 消费的线程卡住了，或者说我队列的使用MQ，那个 MQ 进行消费的出现了一个耗时比较长的情况，缓存和数据库里面的信息肯定是不对等的。
Mq重试
函数超时kill
补齐方式：（这里大家看看还有没啥好的方案）
对账
打日志，人工
7，追问对账细节
问对账如何做
如果数据库和缓存有不同以谁为准
正常情况db为准 当然要参考那一行的version，以version大的为准
8，分布式锁需求上线后重点观察指标（被问了两次了，简历上有分布式锁的同学可以关注下）
1，setnx成功率
2，有没有两线程写冲突一条数据
反问环节：
细节就不说了哈哈，深入和面试官探讨了他们业务的发展历程 前景 打法 与竞对的区别等等，还是了解了蛮多的，在面试中进步！
后续会更新面经和offer情况，欢迎关注~

#提前批[话题]##滴滴[话题]# #后端开发[话题]# #面试求职[话题]# #校招[话题]#
```

## `cq_q_5b53dba65e5ceb49b026dad8fc1704cc`

### Canonical record

```json
{
  "aliases": [
    "算法：数字拆分"
  ],
  "answer_status": "needs_update",
  "canonical_id": "cq_q_5b53dba65e5ceb49b026dad8fc1704cc",
  "canonical_title": "算法：数字拆分",
  "companies": [
    "腾讯(WXG)"
  ],
  "frequency": 1,
  "primary_domain": {
    "l1": "算法与数据结构",
    "l2": "其他"
  },
  "primary_entities": [
    "动态规划",
    "整数拆分"
  ],
  "question_ids": [
    "5b53dba65e5ceb49b026dad8fc1704cc"
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
  "question_id": "5b53dba65e5ceb49b026dad8fc1704cc",
  "original_question": "算法：数字拆分",
  "domain": {
    "l1": "算法",
    "l2": "数学"
  },
  "question_type": "算法手撕_Coding",
  "cognitive_depth": "L2_Mechanism",
  "tech_entities": [
    "整数拆分",
    "动态规划"
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

## `cq_q_5d39b5ae05a488c7436cbfa9b21e746c`

### Canonical record

```json
{
  "aliases": [
    "如何实现单链表的翻转？"
  ],
  "answer_status": "needs_update",
  "canonical_id": "cq_q_5d39b5ae05a488c7436cbfa9b21e746c",
  "canonical_title": "如何实现单链表的翻转？",
  "companies": [
    "浪潮"
  ],
  "frequency": 1,
  "primary_domain": {
    "l1": "其他",
    "l2": "其他"
  },
  "primary_entities": [
    "链表反转"
  ],
  "question_ids": [
    "5d39b5ae05a488c7436cbfa9b21e746c"
  ],
  "review_priority": "P2",
  "schema_version": "canonical_question.v1"
}
```

### Source hits (1)

#### Source 1: `66b32698000000001e01c75e`

- matched by: `question_id`
- tagged: `note_tagged/66b32698000000001e01c75e.json`
- caption: `note_desc/66b32698000000001e01c75e.txt`

Tagged question:

```json
{
  "question_id": "5d39b5ae05a488c7436cbfa9b21e746c",
  "original_question": "如何实现单链表的翻转？",
  "domain": {
    "l1": "其他",
    "l2": "算法"
  },
  "question_type": "算法手撕_Coding",
  "cognitive_depth": "L2_Mechanism",
  "tech_entities": [
    "链表反转"
  ],
  "business_context": [],
  "is_valid_for_library": true
}
```

Caption text:

```text
浪潮提前批
1．什么是面向对象
2．深拷贝和浅拷贝
3．并行和并发
4．对于高并发问题怎么解决
5．实习中有交易系统，高并发如何解决的
6.Java垃圾回收机制
7．了解 python 吗， python 中的 lamda 表达式（函数式编程）
8.Lamda表达式中的列表推导式
9．数据库索引有哪些
10．数据库的锁
11．熟悉的数据结构
12．如何翻转链表实现
13．冒泡排序的原理
14．前端会吗，用过 vue 的话什么是双向绑定
15．怎么样让子组件给父组件传递数据16.CSS的盒子模型， parding 和 margin 的区别
16.CSS的盒子模型， parding 和 margin 的区别
17.Css选择器
18．数据库设计的三个范式
19．随机梯度下降和梯度下降的区别20．为什么选择浪潮，了解这个公司吗
21．手上有没有其他 offer
#面经[话题]# #后端面试[话题]# #java后端[话题]# #浪潮[话题]# #25届提前批[话题]# #后端开发[话题]#
```

## `cq_q_5e21e188af5c4a9ffdb5eaf97cc39c97`

### Canonical record

```json
{
  "aliases": [
    "如何实现一个深拷贝函数?"
  ],
  "answer_status": "needs_update",
  "canonical_id": "cq_q_5e21e188af5c4a9ffdb5eaf97cc39c97",
  "canonical_title": "如何实现一个深拷贝函数?",
  "companies": [
    "百度"
  ],
  "frequency": 1,
  "primary_domain": {
    "l1": "其他",
    "l2": "其他"
  },
  "primary_entities": [
    "递归",
    "深拷贝",
    "json.parse"
  ],
  "question_ids": [
    "5e21e188af5c4a9ffdb5eaf97cc39c97"
  ],
  "review_priority": "P2",
  "schema_version": "canonical_question.v1"
}
```

### Source hits (1)

#### Source 1: `67d8d9fc00000000090144c3`

- matched by: `question_id`
- tagged: `note_tagged/67d8d9fc00000000090144c3.json`
- caption: `note_desc/67d8d9fc00000000090144c3.txt`
- image transcript: `note_img_txt/67d8d9fc00000000090144c3.txt`

Tagged question:

```json
{
  "question_id": "5e21e188af5c4a9ffdb5eaf97cc39c97",
  "original_question": "如何实现一个深拷贝函数?",
  "domain": {
    "l1": "其他",
    "l2": "其他"
  },
  "question_type": "算法手撕_Coding",
  "cognitive_depth": "L2_Mechanism",
  "tech_entities": [
    "深拷贝",
    "递归",
    "json.parse"
  ],
  "business_context": [],
  "is_valid_for_library": true
}
```

Caption text:

```text
#前端面试[话题]# #面试题[话题]# #前端[话题]# #前端入门[话题]# #前端找工作[话题]# #前端知识[话题]# #大厂前端[话题]# #前端面试题[话题]# #前端开发[话题]# #前端开发工程师[话题]#
```

Image transcript:

```text
```
3.13百度前端面经

百度前端面试一面

题目
1. 解释事件循环机制及宏任务/微任务执行顺序
2. 如何实现一个深拷贝函数?
3. 请描述Vue3的响应式原理与Vue2的区别
4. CSS实现垂直居中的五种方法
5. 手写Promise.all的实现

百度前端二面

题目
1. 浏览器缓存机制及缓存策略优化
2. 如何实现前端性能监控系统?
3. 说说Webpack的HMR原理
4. 实现一个函数防抖的TypeScript版本
5. React Fiber的调度机制是怎样的?
6. 如何解决跨域问题? CORS的预检请求是什么?
7. 从输入URL到页面展示的完整过程

百度前端三面

题目
1. 前端工程化建设的具体实践方案
2. 微前端架构的优缺点及实现方案
3. 如何设计一个可维护的React组件库?
4. 前端安全防护措施(XSS/CSRF)
5. 大规模表单页面的性能优化策略
6. 说说Service Worker的缓存策略
```
```
3. Vue3响应式原理与Vue2的区别

特性 Vue2 Vue3
实现方式 Object.defineProperty Proxy
数组监听 需重写数组方法(如 直接监听数组索引和长度变化
push)
新增/删除属性 需Vue.set/Vue.delete 自动检测
性能优化 初始化递归遍历对象 惰性响应(按需触发
getter)
依赖收集 通过Dep和Watcher类 通过effect和
track / trigger
代码结构 选项式 API 组合式 API + 响应式模块化

4. CSS实现垂直居中的五种方法

1. Flex 布局
.parent {
display: flex;
align-items: center;
justify-content: center;
}

2. Grid 布局
.parent {
display: grid;
place-items: center;
}

3. 绝对定位+Transform
.child {
position: absolute;
top: 50%;
```
```
4. Table-Cell
.parent {
display: table-cell;
vertical-align: middle;
text-align: center;
}
.child {
display: inline-block;
}

5. Line-Height (单行文本)
.parent {
height: 100px;
line-height: 100px;
text-align: center;
}

5. 手写Promise.all的实现
Promise.myAll = function (promises) {
return new Promise((resolve, reject) => {
const results = [];
let count = 0;
for (let i = 0; i < promises.length; i++) {
Promise.resolve(promises[i])
.then((res) => {
results[i] = res;
count++;
if (count === promises.length) resolve(results);
})
.catch(reject); // 任一 Promise 失败则立即 reject
}
if (promises.length === 0) resolve(results); // 处理空数组
});
};

核心逻辑:
1. 遍历传入的Promise数组,用Promise.resolve包裹保证非Promise值。
2. 通过计数器统计完成的Promise数量,全部完成后返回结果数组。
3. 任一Promise失败则立即终止。

二面答案:

1. 浏览器缓存机制和缓存策略优化
浏览器缓存机制:
分为强缓存和**协商缓存”,优先级:强缓存>协商缓存。
·强缓存:
。Cache-Control(优先级高):如 max-age=3600(单位秒)、no-cache(强制协
商缓存)、no-store(不缓存)。
。Expires(HTTP/1.0):绝对时间,可能因时区或系统时间误差。

·协商缓存:
。ETag/If-None-Match(优先级高):文件内容哈希值,精确判断资源变化。
。Last-Modified/If-Modified-Since:最后修改时间,精度为秒,可能因时间误差
效。
```
```
11
});

6. 接收响应:
。解析状态码(如200、304)、响应头(缓存相关字段)、响应体(HTML)。

7. 渲染流程:
。解析HTML:构建DOM树,遇到CSS/JS会阻塞或并行下载。
。解析CSS:生成CSSOM树。
。合成Render Tree:结合DOM和CSSOM,排除不可见节点。
。布局(Layout):计算节点几何位置。
。绘制(Painting):将布局结果转换为屏幕像素。
。合成(Composite):层合并,GPU加速。

8. 加载后续资源:
。解析到、等标签时触发资源加载。

9. 交互阶段:
。JS监听事件(如点击),触发重新渲染(可能引发重排或重绘)。

优化点:
。DNS预解析()、HTTP/2多路复用、资源预加载、服务瑞
染(SSR)。

三面答案

1. 前端工程化建设的具体实践方案
核心实践:
·模块化开发:
。使用ES Module或CommonJS规范拆分代码,结合Monorepo(如Lerna、Turborepo)管
理多包依赖。
·规范化工具链:
。代码规范:ESLint+Prettier+Husky(Git Hooks)确保代码一致性。
```
```
14
12
});

·Network First:优先请求网络,失败时返回缓存(适合动态内容)。
·Stale-While-Revalidate:先返回缓存,同时后台更新缓存。
·预缓存:在install阶段缓存关键资源。
·运行时缓存:动态缓存按需资源(如API响应)。

7. 首屏加载时间优化
·资源压缩:Brotli/Gzip压缩文本资源,WebP图片格式。
·代码分割:
。React.lazy + Suspense 实现路由懒加载。
。Webpack 导入(Dynamic Import)。
·预加载/预渲染:
。

·CDN加速:静态资源分发至边缘节点。
·减少关键资源:内联关键CSS,延迟非必要JS(如埋点脚本)。

8. Node.js 事件循环与浏览器事件循环的区别
特性 浏览器事件循环 Node.js 事件循环
阶段划分 宏任务/微任务 6个阶段(Timers→
Pending→Idle/Prepare→
Poll→Check→Close)
任务优先级 微任务(Promise)优先 按阶段顺序执行,
process.nextTick 优先
```
```
优缺点:
·技术栈无关,子应用独立开发部署。
·渐进式升级,降低单体巨石应用维护成本。
·团队自治,提升开发效率。

缺点:
·通信复杂度高(CustomEvent、Props、状态管理库)。
·公共依赖冗余(如重复加载React)。
·性能损耗(子应用加载时间、样式隔离成本)。

实现方案:
·qiankun:基于路由的微前端框架,通过JS沙箱和样式隔离实现子应用独立运行。
·Module Federation (Webpack 5):动态加载远程模块,共享依赖。
·iframe:简单隔离但通信困难,适用于低耦合场景。
```
```
10
2. JSONP:利用 <script> 标签跨域特性,需服务端返回回调函数包裹的数据。
3. 代理服务器:前端请求同域代理,代理转发到目标服务器(如Nginx反向代理)。
4. postMessage:跨窗口通信,适用于iframe或新窗口。
5. WebSocket:协议本身支持跨域。

CORS 预检请求:
·触发条件:非简单请求(如PUT、DELETE、自定义头、Content-Type 非
application/x-www-form-urlencoded)。
·过程:浏览器先发送OPTIONS请求,携带Origin、Access-Control-Request-
Method 等头,服务器返回允许的方法和头字段后,再发送实际请求。

7. 从输入URL到页面展示的完整过程

1. URL 解析:
。检查输入是否是URL,否则调用搜索引擎。
。解析协议、域名、端口等。

2. DNS查询:
。浏览器缓存→系统缓存→路由器缓存→ISP DNS服务器→递归查询。

3. 建立 TCP 连接:
。三次握手(SYN→SYN-ACK→ACK),若是HTTPS则进行TLS握手(协商密钥、证书验
证)。

4. 发送HTTP请求:
。请求头携带Cookie、User-Agent、Accept等信息。

5. 服务器处理请求:
。反向代理(如Nginx)转发请求到应用服务器,生成响应。
```
```
2
7. 如何实现首屏加载时间优化?
8. Node.js事件循环与浏览器事件循环的区别
9. 前端灰度发布的实现方案
10. 解释Chrome V8引擎的垃圾回收机制

参考答案

一面:

1. 事件循环机制及宏任务/微任务执行顺序
事件循环机制:
JavaScript是单线程的,通过事件循环处理异步任务。事件循环的核心是调用栈、任务队列(宏任务
队列和微任务队列)。执行流程如下:
1. 执行同步代码,直到调用栈为空。
2. 检查微任务队列,依次执行所有微任务(如Promise.then、MutationObserver)。
3. 当微任务队列清空后,执行一个宏任务(如setTimeout、setInterval、I/O操作)。
4. 重复上述过程。

执行顺序:
·微任务优先级高于宏任务。每次事件循环中,先执行所有微任务,再执行一个宏任务。
·示例:
1 setTimeout(() => console.log('宏任务'), 0);
2 Promise.resolve().then(() => console.log('微任务'));
3 // 输出顺序:微任务→宏任务

2. 实现深拷贝函数
```
```
16
最高
I/O 处理 基于 Web APIs(如DOM、 基于 libuv 的异步I/O(文
XHR) 件、网络)
并行能力 Web Worker多线程 Cluster 模块多进程

9. 前端灰度发布的实现方案
·按用户分流:
。用户ID或设备Hash取模,控制百分比(如10%用户看到新功能)。
·按路由分发:Nginx配置不同路径指向新旧版本服务。
·特性开关(Feature Toggle):
。后端接口返回新旧标志位,前端动态渲染对应功能模块。
。结合LaunchDarkly等平台动态控制开关状态。
·AB测试:通过埋点数据对比新旧版本转化率,逐步全量。

10. Chrome V8引擎的垃圾回收机制
分代回收策略:
·新生代(Young Generation):
。Scavenge算法:将内存分为From和To空间,存活对象从From复制到To,清空From。
。对象晋升:多次存活的对象移至老生代。
·老生代(Old Generation):
。标记-清除(Mark-Sweep):遍历标记活动对象,清除未标记对象。
。标记-整理(Mark-Compact):清除后整理内存碎片。
·增量标记与并行回收:
。增量标记:将标记任务拆分为小段,避免长时间阻塞主线程。
。并行回收:利用多线程加速垃圾回收过程。
```
```
7
缓存策略优化:

1. 静态资源:设置长缓存(如 max-age=31536000),通过文件名哈希(如 main.
[hash].js)实现版本控制。
2. 动态资源:使用 no-cache 或短 max-age,配合 ETag 验证。
3. 避免缓存污染:区分公共库(单独域名)、业务代码和用户数据。
4. Service Worker:精细化控制缓存逻辑,支持离线访问。

2. 如何实现前端性能监控系统?
核心步骤:
1. 数据采集:
。性能指标:通过 Performance API 获取 FP/FCP/LCP(首次渲染/首次内容渲染/最大内
容渲染)、CLS(布局偏移)、TTI(可交互时间)。
。资源加载:performance.getEntriesByType('resource')获取资源加载耗时。
。错误监控:监听 window.onerror 和 unhandledrejection 捕获 JS 错误和未处理的
Promise异常。
。用户行为:路由切换、点击事件等。

2. 数据上报:
。方式:navigator.sendBeacon (页面卸载时可靠上报)或 XMLHttpRequest。
。优化:合并上报请求、本地缓存失败请求、采样率控制。

3. 数据存储与分析:
。使用日志系统(如ELK)存储,聚合分析慢加载、高错误率等场景。
。可视化展示(如Grafana仪表盘)。

3. Webpack的HMR原理
HMR (Hot Module Replacement):
```
```
13
3. 如何设计一个可维护的 React 组件库?
设计原则:
·原子化设计:按功能拆分基础组件(Button/Input)和复合组件(Form/Table)。
·类型安全:使用TypeScript定义Props和接口。
·文档驱动:
。Storybook可视化调试,生成组件文档。
。提供Playground示例和API描述。
·样式方案:
。CSS-in-JS (Styled-components/Emotion)或CSS Modules避免全局污染。
。主题化:通过Context或CSS Variables支持主题切换。
·测试覆盖:
。单元测试(Jest+React Testing Library)验证交互逻辑。
。快照测试确保UI一致性。
·发布管理:
。语义化版本(SemVer),通过Changesets管理版本日志。

4. 前端安全防护措施(XSS/CSRF)
XSS (跨站脚本攻击)防护:
·输入过滤:对用户输入的 <>等字符转义(如 he.js 库)。
·输出编码:根据上下文使用不同编码(HTML/JS/URL)。
·CSP (内容安全策略):通过HTTP头限制脚本来源,如:

1 Content-Security-Policy: script-src 'self' https://trusted.cdn.com

·HttpOnly Cookie:防止JS读取敏感Cookie。
```
```
8
1. 建立通信:Webpack Dev Server 通过WebSocket与客户端建立连接。
2. 文件变更:Webpack 监听文件变化,重新编译生成差异化的模块补丁(Chunk)。
3. 推送更新:通过WebSocket向客户端发送hash和chunk消息。
4. 客户端处理:
。客户端收到消息后,通过JSONP请求新的模块代码([hash].hot-update.json和
[hash].hot-update.js)。
。使用HMR Runtime对比新旧模块,替换更新的模块。
。若模块接受更新(如通过module.hot.accept声明),执行回调函数,否则刷新页面。

关键点:局部更新、状态保留、依赖关系管理。

4. 函数防抖的TypeScript版本
function debounce(func: T,
delay: number,
immediate?: boolean
): (...args: Parameters) => void {
let timeoutId: ReturnType<typeof setTimeout> | null = null;
return function (this: unknown, ...args: Parameters) {
if (immediate && !timeoutId) {
func.apply(this, args);
}
if (timeoutId) {
clearTimeout(timeoutId);
}
timeoutId = setTimeout(() => {
if (!immediate) {
func.apply(this, args);
}
timeoutId = null;
}, delay);
};
}
```
```
17
优化点:
·避免全局变量、及时解除引用、慎用闭包。
```
```
9
特性:
·支持立即执行(immediate参数)。
·泛型类型保持原函数类型推断。
·清除定时器,确保最后一次触发。

5. React Fiber的调度机制
核心目标:实现增量渲染和任务优先级调度,解决同步递归渲染导致的卡顿问题。

关键机制:
1. Fiber节点:将组件树拆解为链表结构的Fiber节点,每个节点保存组件类型、状态、副作用等信
息。
2. 可中断与恢复:
。使用requestIdleCallback(或polyfill)在浏览器空闲时间段分片执行任务。
。通过循环模拟递归,保留当前处理进度,允许中断后恢复。
3. 优先级调度:
。任务分为同步、高优先级(用户交互)、低优先级(数据请求)等。
。高优先级任务可打断低优先级任务,抢占执行。
4. 双缓存技术:
。内存中构建新的Fiber树(workInProgress),完成后替换当前树,减少页面抖动。

6. 跨域解决方案与CORS预检请求

跨域解决方案:
1. CORS (主流方案):服务器端设置响应头(如Access-Control-Allow-Origin:* )。
```
```

## `cq_q_5f1aa586172b1a82ebb8cdd65fb6927b`

### Canonical record

```json
{
  "aliases": [
    "算法与 SQL：1) 大数加法（字符串模拟）；2) SQL 查询学生学号、姓名及其所有课程的平均成绩（涉及 JOIN 与 GROUP BY）"
  ],
  "answer_status": "needs_update",
  "canonical_id": "cq_q_5f1aa586172b1a82ebb8cdd65fb6927b",
  "canonical_title": "算法与 SQL：1) 大数加法（字符串模拟）；2) SQL 查询学生学号、姓名及其所有课程的平均成绩（涉及 JOIN 与 GROUP BY）",
  "companies": [
    "美团"
  ],
  "frequency": 1,
  "primary_domain": {
    "l1": "算法与数据结构",
    "l2": "字符串"
  },
  "primary_entities": [
    "big number addition",
    "sql aggregate",
    "string simulation"
  ],
  "question_ids": [
    "5f1aa586172b1a82ebb8cdd65fb6927b"
  ],
  "review_priority": "P2",
  "schema_version": "canonical_question.v1"
}
```

### Source hits (1)

#### Source 1: `680859e1000000000f032ec6`

- matched by: `question_id`
- tagged: `note_tagged/680859e1000000000f032ec6.json`
- caption: `note_desc/680859e1000000000f032ec6.txt`
- image transcript: `note_img_txt/680859e1000000000f032ec6.txt`

Tagged question:

```json
{
  "question_id": "5f1aa586172b1a82ebb8cdd65fb6927b",
  "original_question": "算法与 SQL：1) 大数加法（字符串模拟）；2) SQL 查询学生学号、姓名及其所有课程的平均成绩（涉及 JOIN 与 GROUP BY）",
  "domain": {
    "l1": "算法",
    "l2": "字符串"
  },
  "question_type": "算法手撕_Coding",
  "cognitive_depth": "L2_Mechanism",
  "tech_entities": [
    "string simulation",
    "big number addition",
    "sql aggregate"
  ],
  "business_context": [],
  "is_valid_for_library": true
}
```

Caption text:

```text
✅算法题+SQL题
算法题
大数加法，给两个字符串，返回两个字符串的和，并以字符串的形式返回,时间复杂度O(n)。
例如:"787"+"350"="1137" (787+350=1137)、"321"+""=321(321+0=321)

SQL题
从学生表和成绩表中，查询学生学号、姓名、平均成绩

✅Java八股
1️⃣说一下HashMap和ConcurrentHashMap的区别?
2️⃣说一下创建线程有哪些方式？
3️⃣刚才你提及了线程池，你觉得用线程池有什么好处？
4️⃣刚你提到了线程池的一些参数，核心线程数和最大线程数，它们各自的作用是什么呢？
5️⃣什么时候请求才会被拒绝呢？会直接拒绝掉吗？还是放到什么里面？那么队列满了怎么办呢？
6️⃣用过MySQL吗？说一下MySQL为什么要用B+树用作索引结构？
7️⃣说一下TCP三次握手的过程吧
8️⃣平时用过消息队列吗？
9️⃣有了解过微服务吗？RPC这个概念有了解过吗？
🔟对JVM了解吗？OK那说一下垃圾回收，就说一下内存区域有哪些划分？
1️⃣1️⃣知道Full GC是什么意思吗？
1️⃣2️⃣JVM内存区域里面堆、栈、方法区的概念了解吗？

✅简历项目
简历项目为1-13,中间穿插一个场景题
1️⃣我看你有提到缓存的一些概念，说一下缓存穿透、缓存击穿、缓存雪崩这三个问题和什么情况下会触发？
2️⃣前面有提到缓存穿透可以存一个空值，那么存一个空值会带来什么负面影响？
3️⃣用什么方法可以避免缓存中存放长期没有用的数据？
4️⃣利用分布式锁解决缓存击穿的问题，说一下具体场景、和怎么实现的？
5️⃣我看你用分布式锁用的Redission，而不是用原生的Redis，Redission有什么优势和特点？
6️⃣说一下为什么用SortedSet来做点赞排行榜？有什么好处？SortedSet对你这种场景而言有没有其他的优势？了解原理吗？了解SortedSet底层用到了哪些比较核心的技术？

✅场景题目
1️⃣围绕点赞的，当数据量很大时候，到百万级别，用SortedSet实现点赞排行榜有可能遇到什么问题，你能想到的？你可以考虑一下他是基于什么实现的，可能有什么问题，从这个角度去想？

下面依然是简历项目问题7-13
因为字数限制，这里就没放，具体题目详情和个人回答请看图片

✅个人情况
1️⃣你平时是怎么学习的？
2️⃣简历中的这些项目是你自己自发的一个项目？还是什么情况呢？

✅反问

1️⃣针对于这次面试，给我一些建议

2️⃣这次面试结果多久通知

#互联网大厂[话题]# #后端开发[话题]# #计算机专业[话题]#  #java[话题]# #互联网大厂[话题]# #暑期实习[话题]# #美团面经[话题]#
```

Image transcript:

```text
很抱歉，我无法直接识别图片中的文字内容并输出。我没有内置的OCR（光学字符识别）功能。
```

## `cq_q_5f591ff5674d612dc10f87d07c1e820f`

### Canonical record

```json
{
  "aliases": [
    "算法手撕：二叉树节点存储代价计算（到达叶子节点的最大路径开销）。"
  ],
  "answer_status": "needs_update",
  "canonical_id": "cq_q_5f591ff5674d612dc10f87d07c1e820f",
  "canonical_title": "算法手撕：二叉树节点存储代价计算（到达叶子节点的最大路径开销）。",
  "companies": [
    "百度"
  ],
  "frequency": 1,
  "primary_domain": {
    "l1": "操作系统",
    "l2": "其他"
  },
  "primary_entities": [
    "二叉树"
  ],
  "question_ids": [
    "5f591ff5674d612dc10f87d07c1e820f"
  ],
  "review_priority": "P2",
  "schema_version": "canonical_question.v1"
}
```

### Source hits (1)

#### Source 1: `68c3747b000000001c0112fd`

- matched by: `question_id`
- tagged: `note_tagged/68c3747b000000001c0112fd.json`
- caption: `note_desc/68c3747b000000001c0112fd.txt`

Tagged question:

```json
{
  "question_id": "5f591ff5674d612dc10f87d07c1e820f",
  "original_question": "算法手撕：二叉树节点存储代价计算（到达叶子节点的最大路径开销）。",
  "domain": {
    "l1": "计算机基础",
    "l2": "算法"
  },
  "question_type": "算法手撕_Coding",
  "cognitive_depth": "L1_Principle",
  "tech_entities": [
    "二叉树"
  ],
  "business_context": [],
  "is_valid_for_library": true
}
```

Caption text:

```text
百度C++一二面
一面
你了解你的岗位吗
问项目
智能指针，协程
rtos和linux调度的区别
tcp/ip协议，socket是处于什么层
手撕lru缓存
对百度处境的看法
用过什么百度产品

二面
自我介绍之后
一直手撕
1.strcpy函数，不知道数组大小n
2.不使用递归遍历二叉树
3.二叉树的层数
4.二叉树节点存储代价，到达叶子节点的最大代价
追问：可以这样迭代的算底层假设是什么（先计算上一层，再计算下层）
——-
想到再补充
#秋招人的精神状态[话题]# #秋招提前批[话题]# #校招[话题]# #面试求职[话题]# #面试题[话题]#
```

## `cq_q_5f9a6152ed410f9a6b42f5f0ab7aa0a5`

### Canonical record

```json
{
  "aliases": [
    "算法/手撕：实现节流（Throttle）函数。"
  ],
  "answer_status": "needs_update",
  "canonical_id": "cq_q_5f9a6152ed410f9a6b42f5f0ab7aa0a5",
  "canonical_title": "算法/手撕：实现节流（Throttle）函数。",
  "companies": [
    "腾讯"
  ],
  "frequency": 1,
  "primary_domain": {
    "l1": "其他",
    "l2": "其他"
  },
  "primary_entities": [
    "节流"
  ],
  "question_ids": [
    "5f9a6152ed410f9a6b42f5f0ab7aa0a5"
  ],
  "review_priority": "P2",
  "schema_version": "canonical_question.v1"
}
```

### Source hits (1)

#### Source 1: `68c2f9a8000000001d02803d`

- matched by: `question_id`
- tagged: `note_tagged/68c2f9a8000000001d02803d.json`
- caption: `note_desc/68c2f9a8000000001d02803d.txt`

Tagged question:

```json
{
  "question_id": "5f9a6152ed410f9a6b42f5f0ab7aa0a5",
  "original_question": "算法/手撕：实现节流（Throttle）函数。",
  "domain": {
    "l1": "前端",
    "l2": "JavaScript基础"
  },
  "question_type": "算法手撕_Coding",
  "cognitive_depth": "L1_Principle",
  "tech_entities": [
    "节流"
  ],
  "business_context": [],
  "is_valid_for_library": true
}
```

Caption text:

```text
csig，一个小时后已过，大概率聊了二十几分钟，主要围绕做过的东西

1.介绍项目
2.echarts和three.js的实现原理是什么？实现echarts之类的数据可视化功能，除了canvas还有什么？
3.项目中大模型相关的SSE是怎么做的？
4.Websocket中1xx相关的状态码代表什么意思
5.tailwind和其他样式方案的区别
6.缓存和懒加载是怎么实现的？不使用lazy这个属性来实现懒加载，怎么做？控制缓存的http头有哪些
7.事件循环机制，nodejs和浏览器环境的有什么区别
8.路由的实现有什么方案，react router是如何实现的？history方案是基于哪些api，hash方案的监听是基于哪个api
9.手撕：节流，分割银行卡号；判断是否为对称二叉树

#前端[话题]# #前端面试[话题]# #面经[话题]# #前端面试题[话题]# #面试题[话题]# #校招[话题]# #腾讯[话题]# #腾讯校招[话题]# #互联网大厂[话题]# #秋招[话题]#
```
