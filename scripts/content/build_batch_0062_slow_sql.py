#!/usr/bin/env python3
"""Build the source-bounded Batch 0062 slow-SQL diagnosis scenario candidate."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path('.')
DATE = '2026-08-31'
BATCH = '0062'
CID = 'cq_q_004333ab8f1c0f22014765e4e6f7abb0'
QID = '004333ab8f1c0f22014765e4e6f7abb0'
EXPECTED_QUESTION = '慢 SQL 优化：如何发现慢 SQL？如何进行优化？有哪些优化指令和工具？'


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def main() -> int:
    batch_dir = ROOT / f'review/content_build/answer_batch_{BATCH}'
    inventory_path = batch_dir / 'source_inventory.json'
    inventory = json.loads(inventory_path.read_text(encoding='utf-8'))
    item = next((x for x in inventory.get('canonicals', []) if x.get('canonical_id') == CID), None)
    if inventory.get('boundary_result') != 'pass' or not item:
        raise SystemExit(f'{CID}: frozen batch source inventory missing or invalid')
    if item.get('answer_type') != 'scenario':
        raise SystemExit(f'{CID}: current answer type drifted: {item.get("answer_type")}')
    if item.get('question_ids') != [QID] or item.get('source_question_count') != 1 or item.get('source_occurrence_count') != 1:
        raise SystemExit(f'{CID}: source ownership/occurrence drift')
    if {x.get('original_question') for x in item.get('source_questions', [])} != {EXPECTED_QUESTION}:
        raise SystemExit(f'{CID}: source wording drift')

    out = batch_dir / CID
    context_path = out / 'context.json'
    context = json.loads(context_path.read_text(encoding='utf-8'))
    if not context.get('ok') or context.get('answer_type') != 'scenario':
        raise SystemExit(f'{CID}: frozen context/type invalid')
    if (context.get('canonical') or {}).get('question_ids') != [QID]:
        raise SystemExit(f'{CID}: frozen context ownership drift')
    rows = list(context.get('source_questions') or [])
    if len(rows) != 1 or rows[0].get('original_question') != EXPECTED_QUESTION:
        raise SystemExit(f'{CID}: frozen source occurrence drift')

    primary_path = out / 'primary_source_research.json'
    primary = {
        'schema_version': 'answer_primary_source_research.v1',
        'canonical_id': CID,
        'checked_at': DATE,
        'source_boundary': {
            'context_locator': str(context_path),
            'answer_type': 'scenario',
            'question_ids': [QID],
            'preserved_question_intent': 'Explain how to discover and optimize slow SQL, including practical diagnostic commands and tools, without inventing a production schema, workload, latency threshold, or personal incident.'
        },
        'sources': [
            {
                'source_id': 'mysql-84-slow-query-log',
                'title': 'MySQL 8.4 Reference Manual: The Slow Query Log',
                'source_type': 'official_documentation',
                'locator': 'https://dev.mysql.com/doc/refman/8.4/en/slow-query-log.html',
                'checked_at': DATE,
                'anchors': [
                    'slow_query_log controls whether the slow query log is enabled',
                    'long_query_time participates in deciding whether a statement is logged',
                    'slow log entries expose execution context such as Query_time, Lock_time, Rows_sent and Rows_examined',
                    'log_queries_not_using_indexes can additionally log statements that do not use indexes for row lookups, subject to its own controls'
                ]
            },
            {
                'source_id': 'mysql-84-statement-digests',
                'title': 'MySQL 8.4 Reference Manual: Performance Schema Statement Digests and Sampling',
                'source_type': 'official_documentation',
                'locator': 'https://dev.mysql.com/doc/refman/8.4/en/performance-schema-statement-digests.html',
                'checked_at': DATE,
                'anchors': [
                    'statement normalization groups structurally similar SQL by digest while replacing literal values with parameter markers',
                    'events_statements_summary_by_digest aggregates statements per SCHEMA_NAME and DIGEST',
                    'digest summaries expose execution frequency plus wait, lock, row and index-use characteristics',
                    'QUERY_SAMPLE_TEXT stores a representative sampled statement for a digest'
                ]
            },
            {
                'source_id': 'mysql-84-sys-statement-analysis',
                'title': 'MySQL 8.4 Reference Manual: statement_analysis and x$statement_analysis Views',
                'source_type': 'official_documentation',
                'locator': 'https://dev.mysql.com/doc/refman/8.4/en/sys-statement-analysis.html',
                'checked_at': DATE,
                'anchors': [
                    'statement_analysis lists normalized statements with aggregated statistics',
                    'rows are sorted by descending total latency by default',
                    'the view exposes fields such as full_scan, exec_count, latency, rows examined, temporary-table and sorting statistics'
                ]
            },
            {
                'source_id': 'mysql-84-explain',
                'title': 'MySQL 8.4 Reference Manual: EXPLAIN Statement',
                'source_type': 'official_documentation',
                'locator': 'https://dev.mysql.com/doc/refman/8.4/en/explain.html',
                'checked_at': DATE,
                'anchors': [
                    'EXPLAIN shows optimizer plan information for supported statements',
                    'EXPLAIN ANALYZE actually runs the statement and reports iterator estimates alongside actual first-row/total timing, rows and loop counts',
                    'EXPLAIN ANALYZE always uses TREE output and therefore must be treated as an executing diagnostic, not a harmless plan-only command'
                ]
            },
            {
                'source_id': 'mysql-84-optimizer-trace',
                'title': 'MySQL 8.4 Reference Manual: Optimizer Trace Typical Usage',
                'source_type': 'official_documentation',
                'locator': 'https://dev.mysql.com/doc/refman/8.4/en/optimizer-tracing-typical-usage.html',
                'checked_at': DATE,
                'anchors': [
                    'SET optimizer_trace="enabled=ON" enables tracing for the current session',
                    'after executing a traceable statement, INFORMATION_SCHEMA.OPTIMIZER_TRACE exposes the trace',
                    'optimizer tracing is session-local and should be disabled after the diagnostic is complete'
                ]
            },
            {
                'source_id': 'mysql-84-index-optimization',
                'title': 'MySQL 8.4 Reference Manual: Optimization and Indexes',
                'source_type': 'official_documentation',
                'locator': 'https://dev.mysql.com/doc/refman/8.4/en/optimization-indexes.html',
                'checked_at': DATE,
                'anchors': [
                    'indexes can accelerate row lookup for query predicates',
                    'unnecessary indexes consume space and add work to inserts, updates and deletes',
                    'index design is a balance rather than an instruction to add an index for every queried column'
                ]
            }
        ],
        'claims': [
            {
                'claim_id': 'discover-by-impact-not-one-off-anecdote',
                'text': 'Slow-SQL diagnosis should start from production-observable statement populations: slow-query logging and Performance Schema/sys digest aggregation can reveal frequently executed or high-latency statement families, rows examined, lock time, scans and representative SQL instead of optimizing whichever query happened to be noticed first.',
                'source_ids': ['mysql-84-slow-query-log', 'mysql-84-statement-digests', 'mysql-84-sys-statement-analysis'],
                'source_anchors': ['Query_time/Lock_time/Rows_examined', 'events_statements_summary_by_digest aggregation', 'statement_analysis aggregated statistics']
            },
            {
                'claim_id': 'plan-estimate-actual-diagnosis',
                'text': 'After selecting a representative statement and realistic parameters/data distribution, EXPLAIN is used to inspect the chosen plan; where it is safe to execute the statement, EXPLAIN ANALYZE can compare estimates with actual iterator timings, returned rows and loop counts, making cardinality or row-amplification mismatches visible.',
                'source_ids': ['mysql-84-explain'],
                'source_anchors': ['EXPLAIN plan information', 'EXPLAIN ANALYZE actual timing, rows and loops']
            },
            {
                'claim_id': 'optimizer-trace-is-deep-reasoning-tool',
                'text': 'When the visible plan is not enough to explain why the optimizer selected or rejected an access path, MySQL 8.4 optimizer trace can be enabled for the current session, the target statement executed, and INFORMATION_SCHEMA.OPTIMIZER_TRACE inspected before tracing is disabled.',
                'source_ids': ['mysql-84-optimizer-trace'],
                'source_anchors': ['enable optimizer_trace', 'execute traceable statement', 'inspect INFORMATION_SCHEMA.OPTIMIZER_TRACE']
            },
            {
                'claim_id': 'index-is-one-remediation-with-write-cost',
                'text': 'An index can reduce lookup work when it matches the query access pattern, but adding indexes blindly is not a complete optimization strategy because unnecessary indexes consume space and increase insert/update/delete maintenance work. Query rewrite, access-pattern reduction, data-model changes or caching/materialization are alternatives with different consistency and operational costs.',
                'source_ids': ['mysql-84-index-optimization'],
                'source_anchors': ['indexes improve lookup', 'unnecessary indexes waste space and add DML cost']
            },
            {
                'claim_id': 'verify-before-after-and-bound-executing-tools',
                'text': 'Optimization is not complete when EXPLAIN merely looks different. The change must be verified under representative parameters/data/concurrency with before/after latency, rows examined/returned, lock behavior, CPU/IO and regression monitoring; executing diagnostics such as EXPLAIN ANALYZE must be bounded because they run the statement.',
                'source_ids': ['mysql-84-explain', 'mysql-84-sys-statement-analysis', 'mysql-84-statement-digests'],
                'source_anchors': ['EXPLAIN ANALYZE runs the statement', 'aggregated latency and rows-examined statistics', 'digest-level workload profile']
            }
        ],
        'writer_constraints': [
            'Keep the source as a MySQL slow-SQL diagnostic scenario; do not invent table names, index definitions, QPS, data size, SLO, company topology or a personal production incident.',
            'Use a closed diagnostic loop: discover -> rank impact -> reproduce representative case -> explain/measure -> classify root cause -> choose the smallest remediation -> verify/canary/rollback -> monitor regression.',
            'Make MySQL 8.4 the explicit version boundary for named commands and system views. Do not present version-sensitive defaults as universal production configuration.',
            'Treat slow query log, Performance Schema digest summaries and sys.statement_analysis as complementary discovery tools, not mutually exclusive replacements.',
            'State explicitly that EXPLAIN ANALYZE executes the statement; use it only when execution side effects and cost are acceptable.',
            'Use optimizer_trace only as a deeper reason-analysis tool after ordinary plan evidence is insufficient, and keep its session-local lifecycle explicit.',
            'Do not reduce optimization to adding indexes. Cover query shape, cardinality/selectivity, joins, sorting/temp work, rows examined versus returned, lock waits, large result sets/pagination and alternative architecture choices.',
            'Every index recommendation needs its DML/storage/rollout cost and a verification plan.',
            'Scenario completeness must include assumptions, diagnostic data flow, capacity/bottleneck framing, consistency/side-effect boundary, timeout/retry/degradation stance, observability/load test/rollout, rollback and at least one alternative with cost.',
            'Project experience section must remain a project-mapping checklist because no real user project facts were supplied.'
        ],
        'research_state': 'primary_sources_frozen_candidate_written',
        'next_gate': 'validate the source-bounded slow-SQL scenario candidate, then perform isolated source-first review and evidence/promotion gates'
    }
    write_json(primary_path, primary)

    candidate_path = ROOT / f'review/candidates/answers/{CID}.md'
    candidate_path.parent.mkdir(parents=True, exist_ok=True)
    candidate = '''<!-- xhs-answer: {"schema_version":"answer.v1","canonical_id":"cq_q_004333ab8f1c0f22014765e4e6f7abb0","version":1,"status":"draft","updated_at":"2026-08-31","answer_type":"scenario","quality_tier":"candidate"} -->
# 慢 SQL 优化：如何发现慢 SQL？如何进行优化？有哪些优化指令和工具？

## 核心结论

我会把慢 SQL 当成一个**证据驱动的闭环排障问题**，而不是看到慢就先加索引：先从慢查询日志、Performance Schema / `sys.statement_analysis` 找到“影响最大的 SQL 家族”，再拿代表性参数和数据分布看 `EXPLAIN`；在确认可以安全执行时用 `EXPLAIN ANALYZE` 对比估算与实际；必要时再用 `optimizer_trace` 解释优化器为什么选择或放弃某条路径。修复可能是索引、SQL 改写、减少扫描/返回数据、调整数据模型或引入缓存/汇总，但最后都必须用相同 workload 做前后对比、灰度和回滚验证。

下面命令与系统视图按 **MySQL 8.4** 表述；实际环境先确认版本、参数权限和生产执行风险。

## 1 分钟版

1. **先发现，不猜**：确认慢查询日志配置；同时用 Performance Schema digest 或 `sys.statement_analysis` 按 SQL 结构聚合，优先看总延迟、执行次数、扫描、锁等待、临时表/排序等高影响项。
2. **再定位执行路径**：拿真实 SQL 结构、代表性绑定值、表统计和数据分布跑 `EXPLAIN`；安全条件允许时跑 `EXPLAIN ANALYZE`，重点比较 estimated rows 和 actual rows/time/loops。
3. **按根因选修复**：索引不匹配、扫描/回表过多、JOIN 放大、排序/临时表、锁等待、一次返回太多、分页方式或 SQL 写法都可能是瓶颈；不要把“加索引”当唯一答案。
4. **优化要算代价**：新增索引会增加空间和写入维护成本；缓存/汇总会引入一致性与失效问题；强制 hint 可能把当前数据分布下的偶然最优固化成未来风险。
5. **最后证明有效**：同数据规模、代表性参数和并发下比较 P95/P99、rows examined/returned、CPU/IO、锁等待和吞吐，灰度上线并保留回滚，再持续按 digest 观察是否回归。

## 3 分钟版

### 1. 先定义“慢”和排查边界

我先确认四件事：MySQL 版本、业务 SLO/超时、读写比例与并发、目标 SQL 的数据量和参数分布。题目没有给具体阈值，所以不会把“超过 1 秒”之类数字硬编码成通用定义；真正要解决的是“哪些 SQL 对当前业务延迟和数据库资源贡献最大”。

发现层可以并行用三类信号：

```sql
SHOW VARIABLES LIKE 'slow_query_log';
SHOW VARIABLES LIKE 'long_query_time';
SELECT * FROM sys.statement_analysis LIMIT 20;
```

慢查询日志适合保留满足配置条件的慢语句上下文；Performance Schema 会把结构相同、字面值不同的语句归一化成 digest，`events_statements_summary_by_digest` 和 `sys.statement_analysis` 可以从“SQL 家族”维度看执行次数、延迟、rows examined、扫描、锁、排序/临时表等特征。这样能区分：

```text
单次极慢但极少执行
vs
单次不算最慢但每秒大量执行
```

优先级应看整体业务影响，而不是只看单次耗时排行榜。

### 2. 冻结代表性 case，再看执行计划

拿到目标 digest 后，固定：SQL 结构、代表性绑定值、表结构/索引、统计信息、数据量级和当时并发背景。然后：

```sql
EXPLAIN FORMAT=TREE
SELECT ...;
```

重点看“从哪里读、怎么 join、预计读多少行、在哪过滤/排序/聚合”。如果只是估算计划还解释不了问题，并且语句可以安全执行：

```sql
EXPLAIN ANALYZE
SELECT ...;
```

MySQL 8.4 的 `EXPLAIN ANALYZE` **会真正执行语句**，并给 iterator 的 actual time、rows、loops。因此它非常适合发现这类信号：

```text
estimated rows 远小于 actual rows
某个 iterator 被循环执行很多次
大量扫描后只返回很少数据
首行很快但总执行时间很长
```

但正因为它会执行，不能把它当成生产上对任意重型 SQL / 写 SQL 都可无脑运行的只读命令；要先评估副作用、资源成本和隔离环境。

### 3. 普通 EXPLAIN 不够时，再看 optimizer_trace

如果问题变成“为什么优化器没有选我以为会选的索引/Join 路径”，再进入更深一层：

```sql
SET optimizer_trace='enabled=ON';

SELECT ...;

SELECT TRACE
FROM INFORMATION_SCHEMA.OPTIMIZER_TRACE\G

SET optimizer_trace='enabled=OFF';
```

在 MySQL 8.4 中 optimizer trace 是当前 session 的诊断信息。它的价值不是替代 `EXPLAIN`，而是帮助回答“候选访问路径如何被考虑、为什么某个选择被接受/拒绝”。排完要关闭，避免把深度诊断长期当常规采集。

### 4. 根据证据把根因归类

我通常按下面顺序判断：

```text
访问行数是否过大？
 -> 条件是否能尽早过滤？索引是否匹配真实过滤/join/order 模式？

rows examined >> rows returned？
 -> 是否扫描过多、回表过多、过滤太晚、一次取了不需要的列/行？

join/子查询是否放大？
 -> 驱动侧规模、关联键、重复行、相关子查询循环次数是否导致乘法效应？

排序/聚合/临时结果是否成为主成本？
 -> 是否能减少输入集、调整索引/SQL 形状，或把昂贵汇总从在线链路移走？

锁时间是否明显？
 -> 这是并发/事务边界问题，单纯改 SELECT 索引可能治标不治本。

单条 SQL 已经合理但业务仍超预算？
 -> 看请求是否 N+1、批量是否可合并、是否需要分页/异步化/缓存/预计算。
```

这里“索引”只是一个分支。MySQL 官方文档也明确提醒：不必要的索引会占空间，并增加 INSERT/UPDATE/DELETE 的维护成本。

### 5. 修复方案要和根因一一对应

**索引方案**：根据真实过滤、JOIN、排序和返回列设计候选索引，然后重新看计划和实际 workload；不要“WHERE 里每个列都建一个索引”。

**SQL 改写**：减少无用列/行、让选择性高的约束尽早生效、避免不必要重复查询/相关子查询、控制一次性结果集；任何改写先保证结果语义一致。

**数据模型/架构**：高成本聚合如果本质上是在线实时计算过重，可以评估汇总表、物化结果、缓存或搜索/分析系统。但这会引入数据新鲜度、一致性、失效和补偿成本，不能为了“SQL 快”就忽略语义。

**Hint/强制索引**：可以作为非常明确且已验证的局部手段，但不是首选通用方案。数据分布和版本变化后，被固定的执行路径可能反而变差，所以必须有监控和撤销策略。

### 6. 上线不是结束：做 before/after 闭环

我会保留同一批代表性参数，对比：

```text
P50/P95/P99 latency
exec_count / throughput
rows examined / rows returned
lock time
CPU / IO
buffer/cache hit signals
temporary/sort work
error / timeout rate
```

索引类变更还要看写入延迟、存储空间和 DDL 发布影响。先在测试/影子 workload 验证，再灰度；上线后继续看同一 digest 的 latency、扫描量和执行次数。若 SLO、资源或业务结果出现回退，按预先准备的 SQL/索引/配置回滚方案恢复。

### 7. 超时、重试、降级和一致性怎么处理

慢 SQL 已经让数据库接近饱和时，客户端“失败就自动重试”可能进一步增加压力，所以重试必须服从剩余 deadline、错误类型和幂等边界，不能拿重试掩盖慢 SQL。可降级到缓存/旧数据/简化查询时，要先声明允许的数据新鲜度和一致性；写链路或强一致查询不能为了低延迟悄悄改语义。

诊断动作本身也要守边界：计划查看优先使用不执行语句的 `EXPLAIN`；会执行目标语句的工具放在可控环境，写 SQL 的验证要有隔离、事务/回滚和数据校验。灾备不是慢 SQL 的直接修复手段，但容量降级、只读副本或故障切换环境下仍应确认优化方案不会依赖单一节点的偶然缓存状态。

## 关键细节

- **版本边界**：这里的命令和视图按 MySQL 8.4 核对；云厂商分支、MariaDB 或旧版本应重新确认。
- **慢日志只是入口**：`long_query_time` 是配置条件，不等于业务 SLO；业务是否“慢”仍要结合调用链目标和并发影响。
- **digest 比单条文本更适合看总体影响**：字面值不同但结构相同的 SQL 可被归一化聚合，避免把同一模式拆成成千上万条孤立样本。
- **`EXPLAIN` 和 `EXPLAIN ANALYZE` 不一样**：后者会执行语句；生产使用前先评估副作用和资源占用。
- **估算行数 vs 实际行数**：差距很大时，应继续检查统计信息、数据倾斜、条件相关性和访问路径，而不是只盯着 `type` 字段背结论。
- **rows examined / returned 是很有用的放大信号**：大量扫描只返回少量结果，通常值得继续追查过滤和访问路径。
- **锁等待不是“加索引万能药”**：要同时看事务时长、锁范围、访问顺序和并发冲突。
- **新增索引有写放大**：空间、DML 维护和发布成本都要进入方案评估。
- **缓存/汇总是架构换成本**：查询变快的同时引入一致性、新鲜度、失效和补偿问题。
- **验证必须同口径**：换数据集、换参数、只比较一次本地执行，都不足以证明线上 workload 改善。

## 原理机制

整个链路本质是把“慢”逐层缩小为可证伪的因果链：

```text
业务延迟/数据库资源异常
  -> statement digest / slow-log 找到高影响 SQL 家族
  -> 冻结代表性参数 + schema + statistics
  -> EXPLAIN 得到优化器估算路径
  -> EXPLAIN ANALYZE（安全时）得到实际 iterator 行数/时间/循环
  -> 对比 estimate vs actual + rows examined/returned + lock/IO/CPU
  -> 定位扫描、join 放大、排序聚合、锁、返回集或调用模式根因
  -> 选择索引 / SQL / 数据模型 / 缓存等最小修复
  -> 同 workload 前后验证 + 灰度 + rollback
  -> digest 持续监控防止回归
```

为什么不能第一步就加索引？因为“慢”可能来自完全不同的资源路径。若根因是锁等待、一次返回百万行、N+1 调用或业务本身要求大规模实时聚合，新增一个索引甚至可能没有触及主成本，还增加写入和存储负担。先建立可观测证据，再修改，是为了让“变化 -> 指标改善”的因果关系能够被验证。

## 项目经验版

来源没有提供我的真实项目、表结构、数据规模或优化结果，所以这里不虚构“我线上把 SQL 从 3 秒优化到 50 ms”。真实项目中可以按下面清单映射自己的事实：

```text
背景：哪个接口/任务慢，业务 SLO 是什么？
发现：slow log / digest / APM 哪个信号先暴露问题？
证据：原 plan、actual rows/time、rows examined、锁/IO/CPU 是什么？
根因：扫描、join、排序、锁、调用模式还是数据模型？
方案：索引/SQL/缓存/汇总中为什么选这一项？替代方案为什么没选？
验证：相同 workload 前后 P95/P99、吞吐、rows examined、资源变化是多少？
代价：新增索引写放大、缓存一致性、DDL 风险怎么处理？
上线：如何灰度、监控、回滚，之后是否发生 plan 回归？
```

有这些真实数据后，再组织成 STAR/项目故事；没有证据时只讲诊断方法，不编造指标。

## 常见追问

- 问：**发现慢 SQL 只开 slow query log 就够了吗？** 答：不够。慢日志适合保留达到配置条件的语句，而 digest/sys 聚合更适合看“同一种 SQL 执行了多少次、累计影响多大”；两者和 APM/业务 SLO 结合才能确定优先级。
- 问：**`EXPLAIN ANALYZE` 为什么比 `EXPLAIN` 更有价值，也更危险？** 答：它能给 actual time、rows、loops，能直接检查优化器估算和真实执行的偏差；但它会真正执行语句，因此不能把重型或有副作用的语句当成无风险计划查看。
- 问：**什么情况下看 `optimizer_trace`？** 答：当普通执行计划已经告诉你“选了什么”，但还需要回答“为什么没选另一个索引/路径”时再看；它是更深的决策证据，不是所有慢 SQL 的第一步。
- 问：**为什么不能看到全表扫描就直接建索引？** 答：是否值得用索引要结合过滤比例、返回规模、排序/join、数据分布和写入成本；小表或高返回比例下全扫未必是主问题，新增索引也有 DML 与空间成本。
- 问：**加完索引 `EXPLAIN` 变好就算完成了吗？** 答：不算。还要在代表性参数、数据规模和并发下看实际 P95/P99、rows examined、CPU/IO、锁和写入开销，并灰度观察 digest 是否真实改善。
- 问：**慢 SQL 超时后可以自动重试吗？** 答：不能默认重试。数据库已经过载时重试可能放大压力；只有错误可重试、剩余 deadline 足够且业务操作满足幂等/安全重放边界时才考虑受控重试。
- 问：**缓存是不是最终解决方案？** 答：不是。缓存是在读延迟/数据库负载与数据新鲜度、一致性、失效复杂度之间交换成本；只有访问模式允许时才是候选，而且源 SQL/数据模型的问题仍需要确认。

## 易错点

- 一上来就背“建索引、避免 `SELECT *`”，没有先说如何找到真正高影响 SQL 和证明根因。
- 把 `long_query_time` 配置值当作所有业务统一的慢 SQL 定义。
- 只看一次 `EXPLAIN` 的 `type/key` 就下结论，不看 estimated/actual rows、loops、rows examined 和真实参数分布。
- 忘记 `EXPLAIN ANALYZE` 会执行语句，在生产直接对昂贵或有副作用 SQL 使用。
- 把 optimizer trace 当持续监控，而不是需要时开启、当前 session 内查看、结束后关闭的深度诊断工具。
- 看到索引没用就强制 `FORCE INDEX`，却没有验证数据分布变化、版本升级和未来回归风险。
- 只优化读延迟，不评估新增索引对写入、空间和 DDL 发布的成本。
- 用缓存、从库或重试把压力暂时移走，却没有定义一致性、新鲜度、幂等和过载边界。
- 本地单次从 200 ms 变 20 ms 就宣布成功，没有同 workload、多参数、并发和灰度后的线上证据。
'''
    candidate_path.write_text(candidate, encoding='utf-8')

    headings = ['## 核心结论', '## 1 分钟版', '## 3 分钟版', '## 关键细节', '## 原理机制', '## 项目经验版', '## 常见追问', '## 易错点']
    text = candidate_path.read_text(encoding='utf-8')
    for heading in headings:
        if text.count(heading) != 1:
            raise SystemExit(f'{CID}: candidate section drift: {heading}')
    if text.count('- 问：') < 5:
        raise SystemExit(f'{CID}: follow-up coverage too small')
    required = ['MySQL 8.4', 'slow_query_log', 'long_query_time', 'sys.statement_analysis', 'Performance Schema', 'EXPLAIN ANALYZE', 'optimizer_trace', 'INFORMATION_SCHEMA.OPTIMIZER_TRACE', 'rows examined', 'P95/P99', '回滚', '一致性']
    missing = [x for x in required if x not in text]
    if missing:
        raise SystemExit(f'{CID}: missing scenario diagnostics: {missing}')
    fabricated = ['我负责过', '我在线上', '实际线上我们', '我们项目中', '我把 SQL 从']
    if any(x in text for x in fabricated):
        raise SystemExit(f'{CID}: fabricated project experience risk')

    digest = hashlib.sha256(candidate_path.read_bytes()).hexdigest()
    writer_path = out / 'writer_research.json'
    writer = {
        'schema_version': 'answer_writer_research.v1',
        'canonical_id': CID,
        'candidate_sha256': digest,
        'checked_at': DATE,
        'review_state': 'writer_complete_isolated_review_pending',
        'sources': [
            {
                'source_id': 'repository-source',
                'title': 'Batch 0062 frozen slow-SQL source context',
                'locator': str(context_path),
                'source_type': 'repository_source_record',
                'checked_at': DATE
            },
            {
                'source_id': 'primary-source-research',
                'title': 'Batch 0062 slow-SQL MySQL 8.4 primary-source research packet',
                'locator': str(primary_path),
                'source_type': 'primary_source_research_record',
                'checked_at': DATE
            }
        ],
        'claims': [
            {
                'claim_id': 'source-boundary',
                'text': 'The single frozen source asks how to discover and optimize slow SQL and which commands/tools to use; it provides no concrete schema, workload, latency threshold, company topology or personal incident, so the answer keeps those as explicit assumptions rather than invented facts.',
                'source_ids': ['repository-source'],
                'answer_locations': ['核心结论', '1 分钟版', '3 分钟版', '项目经验版']
            },
            {
                'claim_id': 'discovery-loop',
                'text': 'The candidate combines slow-query logging with Performance Schema digest/sys aggregation to rank statement families by workload impact before selecting a representative SQL case.',
                'source_ids': ['primary-source-research'],
                'answer_locations': ['核心结论', '1 分钟版', '3 分钟版', '原理机制', '常见追问']
            },
            {
                'claim_id': 'plan-and-actual-analysis',
                'text': 'The candidate separates plan-only EXPLAIN from executing EXPLAIN ANALYZE, uses actual rows/time/loops to check estimate mismatch, and explicitly bounds the side-effect/resource risk of executing diagnostics.',
                'source_ids': ['primary-source-research'],
                'answer_locations': ['核心结论', '1 分钟版', '3 分钟版', '关键细节', '常见追问', '易错点']
            },
            {
                'claim_id': 'optimizer-trace-boundary',
                'text': 'The candidate uses optimizer_trace only as a deeper, session-local reason-analysis tool after ordinary plan evidence is insufficient and shows the enable/inspect/disable lifecycle.',
                'source_ids': ['primary-source-research'],
                'answer_locations': ['3 分钟版', '关键细节', '常见追问', '易错点']
            },
            {
                'claim_id': 'remediation-tradeoffs',
                'text': 'The candidate treats indexing as one remediation among SQL rewrite, access-pattern reduction, data-model changes, caching or precomputation, and carries DML/storage/consistency/rollout cost into the choice.',
                'source_ids': ['primary-source-research'],
                'answer_locations': ['1 分钟版', '3 分钟版', '关键细节', '原理机制', '常见追问']
            },
            {
                'claim_id': 'verification-and-operations',
                'text': 'The candidate closes the loop with representative before/after workload metrics, canary rollout, rollback, digest regression monitoring, deadline/retry overload boundaries and explicit no-fabrication project mapping.',
                'source_ids': ['primary-source-research'],
                'answer_locations': ['1 分钟版', '3 分钟版', '项目经验版', '常见追问', '易错点']
            }
        ],
        'source_question_coverage': [
            {
                'question_id': QID,
                'covered': True,
                'answer_locations': ['核心结论', '1 分钟版', '3 分钟版', '关键细节', '原理机制', '常见追问']
            }
        ],
        'promotion_blocker': 'isolated_independent_review_not_yet_performed'
    }
    write_json(writer_path, writer)

    task_path = ROOT / 'tasks/answer-batches/TASK-20260711-0313-answer-batch-0062.md'
    task = task_path.read_text(encoding='utf-8')
    progress = f'- [x] `{CID}` writer stage complete: the frozen slow-SQL scenario source is covered by a MySQL 8.4 bounded diagnostic loop using slow-query log, Performance Schema/sys digest aggregation, EXPLAIN versus executing EXPLAIN ANALYZE, session-local optimizer_trace, root-cause-specific remediation tradeoffs, representative before/after verification, canary/rollback and no fabricated project metrics. Independent source-first review is still pending, so this is not a promotion or PASS claim.'
    if progress not in task:
        marker = '## Progress\n'
        if marker not in task:
            raise SystemExit(f'{CID}: task progress marker missing')
        task = task.replace(marker, marker + '\n' + progress + '\n', 1)
        task_path.write_text(task, encoding='utf-8')

    print(f'PASS writer {CID} digest={digest} primary={primary_path} writer={writer_path}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
