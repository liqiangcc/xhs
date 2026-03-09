# Tech Entities 数据质量预警分析

## 1. 大小写不一致 (Case Inconsistency)
发现了 0 组因为大小写不同而被拆分的相同实体：
| 统一小写 | 变体及次数 |
|---|---|

## 2. 疑似同义词 / 翻译不统一 (Synonyms)
同一概念有多种不同的写法，导致统计被分散，例如：
- B+树(111) / B+ Tree(48) / B+tree(2)
- 限流(43) / Rate Limiting(5)
- 分布式锁(89) / Distributed Lock(7)
- 同步(10) / 并发控制(6) / 锁(8)

## 3. 实体异常：长度过长 (Length > 25)
发现了 32 个过长的实体，可能是之前大模型把一整句话或描述当成了标签：
- `concurrentmodificationexception`
- `best time to buy and sell stock`
- `concurrency vs parallelism`
- `lengthfieldbasedframedecoder`
- `handlermethodreturnvaluehandler`
- `requestmappinghandlermapping`
- `threadpool parameter design`
- `elasticsearch index mapping`
- `architectural extensibility`
- `horizontal privilege escalation`
- ... 等，共 32 个

## 4. 包含特殊字符或标点的实体
发现了 165 个包含异常标点的实体：
- `b+树`
- `o(1)随机访问`
- `b+树索引`
- `key_len`
- `requires_new`
- `display:none`
- `async/await`
- `possible_keys`
- `ods/dwd/dws`
- `time_wait`
- ... 共 165 个

## 5. 空实体问题
9621 道题目中，有 120 道题的 `tech_entities` 是空的，缺少标签关联。
