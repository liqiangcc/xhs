# Tech Entities 数据质量预警分析

## 1. 大小写不一致 (Case Inconsistency)
发现了 136 组因为大小写不同而被拆分的相同实体：
| 统一小写 | 变体及次数 |
|---|---|
| synchronized | synchronized(129), Synchronized(21) |
| volatile | volatile(69), Volatile(6) |
| undo log | undo log(18), Undo Log(39), Undo log(1) |
| elasticsearch | Elasticsearch(42), ElasticSearch(3) |
| explain | Explain(18), EXPLAIN(21), explain(2) |
| epoll | epoll(31), Epoll(8) |
| redo log | redo log(10), Redo Log(28), Redo log(1) |
| zookeeper | Zookeeper(26), ZooKeeper(11) |
| websocket | WebSocket(35), Websocket(1) |
| ioc | IoC(17), IOC(18) |
| cglib | Cglib(1), CGLIB(28), CGLib(2), CGlib(1) |
| binlog | binlog(7), Binlog(25) |
| arthas | Arthas(29), arthas(1) |
| zset | ZSet(21), Zset(2), zSet(1), zset(1), ZSET(4) |
| next-key lock | Next-Key Lock(24), Next-key Lock(5) |
| jstack | jstack(26), Jstack(2) |
| classloader | ClassLoader(27), Classloader(1) |
| hashtable | HashTable(12), Hashtable(10), hashtable(3) |
| top | top(22), Top(1), TOP(2) |
| redlock | Redlock(21), RedLock(2) |
| ... | 还有 116 组未展示 |

## 2. 疑似同义词 / 翻译不统一 (Synonyms)
同一概念有多种不同的写法，导致统计被分散，例如：
- B+树(111) / B+ Tree(48) / B+tree(2)
- 限流(43) / Rate Limiting(5)
- 分布式锁(89) / Distributed Lock(7)
- 同步(10) / 并发控制(6) / 锁(8)

## 3. 实体异常：长度过长 (Length > 25)
发现了 42 个过长的实体，可能是之前大模型把一整句话或描述当成了标签：
- `ConcurrentModificationException`
- `Best Time to Buy and Sell Stock`
- `Concurrency vs Parallelism`
- `LengthFieldBasedFrameDecoder`
- `HandlerMethodReturnValueHandler`
- `RequestMappingHandlerMapping`
- `ThreadPool Parameter Design`
- `Elasticsearch Index Mapping`
- `Architectural Extensibility`
- `Horizontal Privilege Escalation`
- ... 等，共 42 个

## 4. 包含特殊字符或标点的实体
发现了 312 个包含异常标点的实体：
- `快表 (TLB)`
- `跳表 (SkipList)`
- `间隙锁(Gap Lock)`
- `@Transactional`
- `TCP/IP`
- `O(1)随机访问`
- `SSL/TLS`
- `磁盘I/O`
- `key_len`
- `REQUIRES_NEW`
- ... 共 312 个

## 5. 空实体问题
9621 道题目中，有 120 道题的 `tech_entities` 是空的，缺少标签关联。
