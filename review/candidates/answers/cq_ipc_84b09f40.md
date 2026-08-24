<!-- xhs-answer: {"schema_version":"answer.v1","canonical_id":"cq_ipc_84b09f40","version":1,"status":"draft","updated_at":"2026-08-17","answer_type":"concept","quality_tier":"candidate"} -->
# 进程间通信（IPC）有哪些方式？

## 核心结论

限定 Linux/POSIX 本机 IPC，可以按“传什么、谁负责同步、端点语义是什么”来区分：`pipe()` 提供单向进程间数据通道；POSIX message queue 以消息为单位收发；POSIX shared memory 让多个进程映射同一共享对象，但访问顺序要由 semaphore 等同步机制协调；signal 更适合事件通知；AF_UNIX/AF_LOCAL socket 提供本机进程端点，并按 `SOCK_STREAM`、`SOCK_DGRAM`、Linux `SOCK_SEQPACKET` 给出不同的连接与消息边界语义。不要把这些机制只按“谁更快”排序，先匹配通信契约。

## 1 分钟版

- 管道：`pipe()` 返回读端和写端两个 fd，是单向 IPC 数据通道；写入内容由内核缓冲，读端再取出。
- POSIX 消息队列：队列有名称，通过 `mq_open` 打开，用 `mq_send`/`mq_receive` 传消息；接收按消息优先级处理。
- POSIX 共享内存：`shm_open` 创建/打开对象，通常配合 `ftruncate` 和 `mmap` 映射；共享数据本身不等于同步，进程通常还要用 semaphore 等机制协调。
- 信号：`kill` 可向进程发送信号，`sigqueue` 可给实时信号附带数据；它是通知机制，不应当作通用业务消息队列。
- AF_UNIX socket：只在本机进程间通信；`SOCK_STREAM` 是面向连接的流，`SOCK_DGRAM` 是保留消息边界的数据报，Linux `SOCK_SEQPACKET` 面向连接并保留消息边界与顺序。

## 3 分钟版

先看数据模型。`pipe()` 的契约是“读端 + 写端”的单向数据通道：发送方写入，数据进入内核缓冲，接收方从读端读取。本文只使用当前 `pipe(2)` 证据支持的管道契约，不把 FIFO/命名管道的额外语义混进来；如果题目专门追问 FIFO，应单独补对应的一手文档再回答。

POSIX message queue 的单位是消息而不是共享内存区域。进程通过队列名称调用 `mq_open`，再用 `mq_send`/`mq_receive` 发送和接收；Linux `mq_overview(7)` 还规定优先级更高的消息先被交付。因此它适合需要明确“队列 + 消息”契约的场景，但容量、阻塞方式等细节仍应按具体 API 和配置核验，不能从“消息队列”四个字外推。

POSIX shared memory 走另一条路径：`shm_open` 得到共享内存对象，调整大小后通过 `mmap` 映射到进程地址空间。多个进程能看到同一共享对象，不代表并发访问自动正确；`shm_overview(7)` 明确说明通常需要 semaphore 等同步机制。POSIX semaphore 用 `sem_wait`/`sem_post` 协调进程或线程；process-shared 的 unnamed semaphore 可以放在共享内存中。因此这里要把“共享数据”和“同步协议”分成两个职责。

signal 用于通知。`signal(7)` 记录了向指定进程发送信号的 `kill`，以及给实时信号附带数据的 `sigqueue`；接收既可以通过异步 handler，也可以使用同步接收相关 API。回答时应把它与 POSIX message queue 区分：前者首先是信号/事件语义，后者是命名队列中的消息收发。

AF_UNIX/AF_LOCAL 是本机 socket family。Linux `unix(7)` 区分三类：`SOCK_STREAM` 是面向连接的字节流，不保留消息边界；`SOCK_DGRAM` 是数据报语义并保留消息边界；Linux 的 `SOCK_SEQPACKET` 面向连接，同时保留消息边界并按发送顺序交付。AF_UNIX 还支持通过 ancillary data 传递文件描述符或进程凭据。选择 socket 时不能只说“socket 可双向”，还要明确所选 type 的边界和连接语义。

## 关键细节

- 本答案的证据边界是 Linux/POSIX 本机 IPC；跨主机网络通信不是这里的比较对象。
- 管道只依据 `pipe(2)` 说明单向数据通道、读写 fd 与内核缓冲；不在没有 FIFO 一手证据时扩展命名管道结论。
- POSIX message queue 保留“消息”这一数据单元，并带优先级；这和管道的数据通道语义不同。
- 共享内存负责共享数据，semaphore 负责同步；二者经常组合，但不能把 semaphore 说成业务负载传输通道。
- AF_UNIX 三种 type 要分开：stream 面向连接且无消息边界，datagram 保留消息边界，seqpacket 面向连接并保留消息边界与顺序。

## 原理机制

可以把五类机制映射成五条状态路径：

1. pipe：`pipe() → read fd/write fd → writer 写入内核缓冲 → reader 读取`。
2. message queue：`队列名称 → mq_open → mq_send(message, priority) → mq_receive`。
3. shared memory：`shm_open → ftruncate → mmap → 多进程读写共享对象`，旁边还必须有独立同步协议，例如 `sem_wait/sem_post`。
4. signal：`发送信号 → 内核投递 → handler 或同步等待 API 接收`。
5. AF_UNIX socket：`创建本机 socket → 按 type 建立对应端点关系 → 依 stream/datagram/seqpacket 契约收发`。

这五条路径的核心差别不是 API 名字，而是数据边界、连接形态和同步责任分别落在哪里。

## 项目经验版

项目映射时记录真实通信双方、是否仅本机、消息或共享数据的大小与频率、是否需要消息边界、同步方案、权限和资源清理方式，再做压测和故障验证。没有实测证据时不要宣称“共享内存一定最快”或“某类 socket 一定零丢失”。

## 常见追问

- 问：共享内存为什么还要信号量？答：共享内存只提供共同可见的数据区域；访问顺序与互斥仍需同步。Linux POSIX shared-memory 文档明确说明进程通常要借 semaphore 等机制协调。
- 问：消息队列与管道最直接的区别是什么？答：这里的 POSIX message queue 明确以消息为单位并有优先级；`pipe()` 的一手契约是单向数据通道。不要给管道补上当前证据没有证明的 FIFO 细节。
- 问：AF_UNIX 的三种 type 有什么区别？答：`SOCK_STREAM` 面向连接、无消息边界；`SOCK_DGRAM` 保留数据报边界；Linux `SOCK_SEQPACKET` 面向连接并保留消息边界和顺序。
- 问：信号能代替消息队列吗？答：不能直接等同。signal 的主契约是信号投递/通知；POSIX message queue 的主契约是命名队列中的消息发送与接收。

## 易错点

- 不要在没有对应一手证据时把 FIFO/命名管道细节塞进普通 `pipe()` 结论。
- 不要把 semaphore 当成承载业务消息的数据通道。
- 不要把 AF_UNIX 三种 socket type 混称成同一种“可靠字节流”。
- 不要把共享内存映射等同于并发正确性；同步协议必须单独设计。
- 不要把本文的 Linux/POSIX 本机边界外推到跨主机网络 IPC。
