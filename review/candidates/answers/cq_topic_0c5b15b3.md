<!-- xhs-answer: {"schema_version":"answer.v1","canonical_id":"cq_topic_0c5b15b3","version":2,"status":"draft","updated_at":"2026-08-18","quality_tier":"candidate","answer_type":"scenario"} -->
# 搜索引擎如何避免全量扫描并高效检索？

## 核心结论

避免全量扫描的核心是写入时把文档分析为 term，并建立 term 到有序 docID 列表的倒排索引；查询把关键词按兼容的 analyzer 转成 term，只枚举命中的 postings，再做 tenant/ACL/状态过滤、相关度排序和 TopK。工程上还要把索引当成可从权威源重建的检索副本，用路由、分片基准、版本控制和可回滚重建保证规模化后的正确性。

## 1 分钟版

- **索引结构**：写入把 text 分析成 term，建立 `term -> postings(docID...)`；查询只读取命中 term 的 postings，不逐文档扫描正文。
- **主链路**：权威源变更 → 版本化索引 worker → bulk 写入；查询则走 analyzer → terms → postings → tenant/ACL/status filter → TopK。
- **扩展与一致性**：先用 routing 缩小分片扇出；乱序写用 source_version 或 Elasticsearch `_seq_no`/`_primary_term` 防旧写覆盖新写，失败可从 checkpoint 重放。
- **验证与恢复**：容量用真实语料测 `index_bytes/doc` 和单分片 QPS；重建新索引后做对账和 query 集验证，再原子切 alias，异常立即回旧索引。

## 3 分钟版

先限定场景：假设 1 亿文档、平均原文 2KB、峰值 2 万 QPS、60 秒内可见、查询 P99 目标 150ms，并要求 tenant 绝不串读。这些数字只是设计输入，不是 Elasticsearch 默认值。容量不套固定膨胀倍数，而是用代表性语料实测 `index_bytes/doc`、单分片持续 QPS、写入/merge P99；例如查询侧至少按 `ceil(20000 / (0.6 * qps_shard))` 估算分片吞吐，再加副本、重建余量并压测热点租户和高频 term。

写路径把数据库或不可变事件日志作为权威源。事件携带 `source_id`、`source_version` 和 payload，worker 只接受不旧于当前版本的更新，失败不提前确认 offset，并能从 checkpoint 重放。若并发控制交给 Elasticsearch，则使用读取到的 `_seq_no` 与 `_primary_term` 作为条件写入，避免旧变更覆盖新变更。定期按 `source_id/version` 对账，保证索引最终能从权威源重新构造。

查询路径是 `query text → search analyzer → terms → term dictionary → postings candidate docIDs → tenant/ACL/status filter → scorer/sorter → TopK`。倒排索引省掉的是“逐文档检查关键词”这一步，不代表查询成本恒定：高频 term、复杂 filter、排序和跨分片 fan-out 仍会放大候选与 CPU/IO。ACL 必须成为服务端查询不变量，并覆盖按 ID 读取路径，因为 alias filter 只作用于 Query DSL。

重建和发布采用新索引：先回放权威源，比较文档数、抽样版本和离线 query 集，再用 aliases API 的单个多动作请求原子切换；旧索引保留到回滚窗口结束。监控索引滞后、重放积压、写失败、P50/P95/P99、零结果率、候选数、慢分片、权限拒绝和 snapshot 成功率。灰度时先镜像查询比较 TopK、P99 与权限结果；若 P99 超目标、滞后超目标、权限异常或对账失败，就停止扩大并切回旧 alias。

灾备时先恢复权威源和事件日志，再按恢复目标重建索引；snapshot 用于加速恢复索引和集群状态，但不替代业务权威源。规模较小且事务一致性优先时，可以考虑数据库全文索引；托管搜索能减少集群运维，但会增加成本、网络和供应商边界。最终选型由检索能力、规模、SLO、恢复目标和团队运维能力共同决定。

## 关键细节

- Lucene 10.3 的 term dictionary 加 postings 提供 term 到有序文档列表的查找；postings 不能高效反查单个文档的所有 term。
- Elasticsearch text 字段在索引和全文查询时经过 analyzer；通常使用相同 analyzer，独立 `search_analyzer` 只针对明确需求并须测试。
- Elasticsearch aliases API 可在一个原子操作内执行多项 add/remove；alias filter 仅适用于 Query DSL，不适用于按 ID 取文档。
- Elasticsearch 的 `_seq_no`/`_primary_term` 可用于乐观并发控制；snapshot 可恢复集群数据/配置，但恢复前要验证仓库、版本兼容和容量。
- 100M 文档、2KB、20k QPS、60 秒可见延迟、150ms P99、60% 利用率均是本题容量假设，不应伪装成产品默认值。

## 原理机制

倒排索引把 term 指向包含该 term 的有序文档列表，因此查询可以从 term dictionary 直接进入候选 postings，而不从每篇文档重新比对关键词。写时 analyzer 与查时 analyzer 产生不兼容 token 会造成漏召回或无关匹配，所以 analyzer、同义词和 mapping 的变化要通过新索引或经过 query 集验证的 search analyzer 发布。分片解决容量和并行度，但跨分片查询会增加 fan-out；routing 的作用是让可确定归属的请求只访问相关分片。别名原子切换只保证应用指向的索引切换，不自动证明语料、权限或相关性正确，因此必须与版本对账、离线 query 集和灰度指标一起使用。

## 项目经验版

项目映射提示：把示例数字替换为真实规模和 SLO，补齐个人决策、压测证据、回滚与复盘；不使用未经确认的项目成果。

## 常见追问

- **问：倒排索引为什么能避免全量扫描？** 答：term dictionary 定位 term 后只读取包含该 term 的 postings；高频词仍可能有巨大候选集，后续 filter 和排序也有成本。
- **问：分词器更新为什么会导致旧数据漏召回？** 答：旧文档 token 已按旧 analyzer 落盘，新 query 若产生不同 token 就可能无法匹配；应通过版本化新索引重建，或使用经过 query 集验证的 search analyzer。
- **问：乱序事件怎样避免旧索引覆盖新索引？** 答：业务事件带 source_version，worker 比较后拒绝旧版本；若由 Elasticsearch 执行并发保护，使用读取到的 `_seq_no` 和 `_primary_term` 作条件写入。
- **问：集群丢失时为什么不能只恢复快照？** 答：快照能恢复索引和部分集群状态，但业务新鲜度与权威事实仍取决于源数据；应能从权威源和事件日志重建，并通过对账和 query 集验证。

## 易错点

- 不要把倒排索引说成任何条件下 O(1)；高频词、过滤、排序、聚合和跨分片都会增加成本。
- 不要把 alias filter 当作完整 ACL；按 ID 读取不应用该 filter。
- 不要把 snapshot 或索引写成功当作业务权威提交；必须说明权威源、事件重放、恢复目标和对账。
- 不要因增加分片就假设热点消失；routing key、高频 term 和热点租户仍可能集中。
