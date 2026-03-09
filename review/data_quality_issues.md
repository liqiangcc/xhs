# Tech Entities 数据质量预警分析

## 1. 大小写不一致 (Case Inconsistency)
发现了 10 组因为大小写不同而被拆分的相同实体：
| 统一小写 | 变体及次数 |
|---|---|
| b+树 | B+树(111), b+树(57) |
| tcp | TCP(126), tcp(12) |
| https | HTTPS(61), https(32) |
| gc | GC(53), gc(1) |
| select | select(15), Select(1) |
| 磁盘io | 磁盘io(5), 磁盘IO(10) |
| hash | Hash(10), hash(1) |
| xss | XSS(3), Xss(1) |
| service | service(2), Service(1) |
| async | async(1), Async(2) |

## 2. 疑似同义词 / 翻译不统一 (Synonyms)
同一概念有多种不同的写法，导致统计被分散，例如：
- B+树(111) / B+ Tree(48) / B+tree(2)
- 限流(43) / Rate Limiting(5)
- 分布式锁(89) / Distributed Lock(7)
- 同步(10) / 并发控制(6) / 锁(8)

## 3. 实体异常：长度过长 (Length > 25)
发现了 32 个过长的实体，可能是之前大模型把一整句话或描述当成了标签：
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
- ... 等，共 32 个

## 4. 包含特殊字符或标点的实体
发现了 148 个包含异常标点的实体：
- `b+树`
- `O(1)随机访问`
- `key_len`
- `REQUIRES_NEW`
- `display:none`
- `async/await`
- `possible_keys`
- `ODS/DWD/DWS`
- `TIME_WAIT`
- `==`
- ... 共 148 个

## 5. 空实体问题
9621 道题目中，有 120 道题的 `tech_entities` 是空的，缺少标签关联。
