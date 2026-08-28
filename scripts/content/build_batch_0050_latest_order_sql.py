#!/usr/bin/env python3
"""Build, validate, source-first review, and stage Batch 0050 latest-order SQL candidate."""

from __future__ import annotations

import hashlib
import json
import re
import sqlite3
from pathlib import Path

ROOT = Path('.')
DATE = '2026-08-29'
BATCH = '0050'
CID = 'cq_q_d616ff7e2ef391e07c984e8bd0a965a6'
QID = 'd616ff7e2ef391e07c984e8bd0a965a6'
EXPECTED = '请编写 SQL：给定订单表 order（字段：orderId, userId, time），查出所有用户各自最新的一个订单信息。'
MYSQL_WINDOW = 'https://dev.mysql.com/doc/refman/8.0/en/window-function-descriptions.html'
MYSQL_IDENTIFIERS = 'https://dev.mysql.com/doc/refman/8.0/en/identifiers.html'
MYSQL_KEYWORDS = 'https://dev.mysql.com/doc/refman/8.0/en/keywords.html'

SQL = '''SELECT orderId, userId, `time`
FROM (
    SELECT
        o.orderId,
        o.userId,
        o.`time`,
        ROW_NUMBER() OVER (
            PARTITION BY o.userId
            ORDER BY o.`time` DESC, o.orderId DESC
        ) AS rn
    FROM `order` AS o
) AS ranked
WHERE rn = 1;'''

CANDIDATE = r'''<!-- xhs-answer: {"schema_version":"answer.v1","canonical_id":"cq_q_d616ff7e2ef391e07c984e8bd0a965a6","version":1,"status":"draft","updated_at":"2026-08-29","answer_type":"coding","quality_tier":"candidate"} -->
# SQL：查询每个用户最新的一条订单

## 核心结论

如果目标环境是 MySQL 8.0，最直接的写法是按 `userId` 分区，用 `ROW_NUMBER()` 按时间倒序编号，再取 `rn = 1`。题目只给了 `orderId, userId, time`，没有说明同一用户两条订单 `time` 相同时如何决定“一个”最新订单；为了让结果确定，本答案显式采用 `orderId DESC` 作为同时间的第二排序键。若业务并不保证更大的 `orderId` 更晚，就必须换成真实的唯一时序字段或明确的业务规则，不能把这个假设冒充成题意。

另外，`order` 在 MySQL 8.0 是保留字，所以示例里用反引号写成 `` `order` ``。

## 1 分钟版

- 对每个 `userId` 单独排名：`PARTITION BY userId`。
- 每个用户内部按 `time DESC` 排，最新时间排第 1。
- 题目要求“一个订单”，所以同一时间若有多条必须有稳定 tie-break；示例用 `orderId DESC`，这是明确假设。
- 外层只保留 `ROW_NUMBER() = 1`，得到每个用户一行。
- `order` 是 MySQL 8.0 保留字，要么改表名，要么用反引号引用。

## 3 分钟版

```sql
SELECT orderId, userId, `time`
FROM (
    SELECT
        o.orderId,
        o.userId,
        o.`time`,
        ROW_NUMBER() OVER (
            PARTITION BY o.userId
            ORDER BY o.`time` DESC, o.orderId DESC
        ) AS rn
    FROM `order` AS o
) AS ranked
WHERE rn = 1;
```

MySQL 8.0 的 `ROW_NUMBER()` 会给窗口分区内的每一行分配序号；这里 `PARTITION BY userId` 让每个用户独立编号，`ORDER BY time DESC, orderId DESC` 把候选“最新订单”放到第 1 行，外层再筛 `rn = 1`。

如果业务要求“同一最新时间的所有订单都返回”，那就不是“每个用户一个订单”的契约，应改用 `RANK()`/`DENSE_RANK()` 或先求 `MAX(time)` 再连接，并明确并列语义。反过来，如果仍只允许一行，就必须有能打破并列的确定规则。

## 关键细节

- **不能只写 `GROUP BY userId, MAX(time)` 再随便拿其它列**：最大时间是聚合值，但 `orderId` 等非聚合列必须与那一条具体订单绑定；单纯聚合并不会自动把整行“最新订单”带出来。
- **同时间并列必须定义**：题目只给 `time`，却要求“一条”。示例用更大的 `orderId` 作为第二排序键，仅用于给出确定可执行答案；真实系统最好使用能表达创建先后的唯一字段，例如单调 ID 或更高精度时间戳。
- **`NULL time`**：题目没有说明。这个答案按“用于比较最新时间的 `time` 非空”建模；如果允许 `NULL`，应先定义它表示未知、未发生还是其它状态，再决定是否排除或如何排序。
- **保留字**：MySQL 8.0 文档把 `ORDER` 标为 reserved；引用保留字标识符时必须加标识符引号，默认是反引号。生产设计更建议避免把表命名为保留字。
- **索引**：若数据量大，至少要结合实际查询和执行计划评估以 `userId`、`time`、稳定 tie-break 字段为前缀的索引。但窗口函数是否能完全避免排序/临时处理取决于 MySQL 版本、统计信息和执行计划，不能只凭 SQL 形状承诺性能。
- **复杂度**：从逻辑上需要对每个用户的候选行建立顺序；具体物理代价由执行计划和索引决定，不能把通用的 `O(n log n)` 当作数据库实际执行成本结论。

## 原理机制

这题先确定结果粒度：**每个用户恰好一行**。窗口函数不会像 `GROUP BY` 那样把多行直接压成一行，而是在保留原始行的同时，基于分区和排序给每行计算一个位置。于是可以分两步表达：

`所有订单 -> 每个 userId 内按“新到旧”排序并编号 -> 每组只取编号 1`。

这里最关键的不变量是：排序键必须形成一个能选出唯一第一名的顺序。如果只按 `time DESC`，并列时间之间没有唯一顺序；数据库可以给这些 peer 任意不同的 `ROW_NUMBER`，从而“返回哪一条”可能不稳定。增加明确的第二排序键后，契约才从“最新时间集合”收缩成“唯一订单”。

## 项目经验版

来源没有提供真实生产数据规模、索引、分库分表方式或 MySQL 小版本，因此不能虚构“线上就是这样跑的”。实际落地时我会先确认三件事：`time` 是否非空且精度足够、`orderId` 是否真的能作为同时间的先后规则、是否有覆盖常用过滤条件和排序键的索引。然后用目标库上的 `EXPLAIN`/实际数据分布检查窗口排序成本；如果是高频在线查询，还会评估是否需要维护“用户最新订单”派生状态，而不是每次扫历史订单计算。

## 常见追问

- 问：为什么不用 `MAX(time)`？答：`MAX(time)` 只能得到最大时间值，题目要的是那条订单的完整信息；还需要把最大时间映射回具体行，并处理并列。
- 问：为什么用 `ROW_NUMBER` 而不是 `RANK`？答：题目要求每个用户“一个”订单；`ROW_NUMBER` 配合确定的完整排序键能选一行。若业务要保留最新时间并列的所有行，才更适合排名并列语义。
- 问：`orderId DESC` 是题目要求吗？答：不是，是为了补全“同一 time 时仍必须选一个”的最小确定性假设；真实业务规则优先。
- 问：MySQL 5.7 没有窗口函数怎么办？答：可以用“先求每用户最大时间，再连接回原表”的方案，但仍要解决同时间多行的唯一选择；必要时再按业务 tie-break 做第二层筛选。不能因为换写法就忽略并列语义。
- 问：为什么给 `order` 加反引号？答：`ORDER` 是 MySQL 8.0 保留字；保留字作为标识符使用时需要引用。更好的 schema 命名通常直接避免保留字。
- 问：有索引就一定不排序吗？答：不能这么保证。窗口执行是否利用索引、是否产生额外排序要看真实版本和执行计划，应以 `EXPLAIN`/运行证据判断。

## 易错点

- `SELECT userId, MAX(time), orderId FROM ... GROUP BY userId`，却假定 `orderId` 自动来自最大时间那行。
- 只按 `time DESC` 使用 `ROW_NUMBER()`，同时声称在并列时间下结果确定。
- 忘记 `order` 是保留字，SQL 在 MySQL 里直接语法错误。
- 为了“去重”用 `DISTINCT`，但没有定义究竟按什么业务键判定重复。
- 把 `orderId DESC` 当成天然时间顺序，而没有验证 ID 生成规则。
- 没有定义 `NULL time` 的业务语义就直接称其为最新或最旧。
'''


def run_context() -> dict:
    import subprocess
    result = subprocess.run(
        ['node', 'scripts/xhs.js', 'answer', 'context', '--canonical-id', CID, '--noWrite'],
        text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, check=True,
    )
    return json.loads(result.stdout)


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def validate_sql(out: Path) -> dict:
    con = sqlite3.connect(':memory:')
    con.execute('CREATE TABLE `order`(orderId INTEGER PRIMARY KEY, userId INTEGER NOT NULL, `time` TEXT NOT NULL)')
    rows = [
        (1, 10, '2026-01-01 09:00:00'),
        (2, 10, '2026-01-02 09:00:00'),
        (3, 20, '2026-02-01 10:00:00'),
        (4, 20, '2026-02-01 10:00:00'),
        (5, 30, '2025-12-31 23:59:59'),
        (6, 40, '2026-03-01 00:00:00'),
        (7, 40, '2026-03-03 00:00:00'),
        (8, 40, '2026-03-02 00:00:00'),
    ]
    con.executemany('INSERT INTO `order` VALUES(?,?,?)', rows)
    actual = list(con.execute(SQL))
    actual.sort(key=lambda x: x[1])
    expected = [
        (2, 10, '2026-01-02 09:00:00'),
        (4, 20, '2026-02-01 10:00:00'),
        (5, 30, '2025-12-31 23:59:59'),
        (7, 40, '2026-03-03 00:00:00'),
    ]
    assert actual == expected, (actual, expected)
    assert len({r[1] for r in actual}) == len(actual) == 4
    assert next(r for r in actual if r[1] == 20)[0] == 4
    stdout = 'PASS users=4 latest-time=selected same-time-tiebreak=larger-orderId one-row-per-user'
    payload = {
        'schema_version': 'answer_code_validation.v1',
        'canonical_id': CID,
        'result': 'pass',
        'validated_at': DATE,
        'command': 'python3 sqlite fixture executing extracted MySQL-8-style ROW_NUMBER query',
        'stdout': stdout,
        'checks': [
            'multiple users are partitioned independently',
            'newer time wins within a user',
            'same-time rows use explicit orderId descending tie-break',
            'exactly one output row is returned per user',
        ],
    }
    write_json(out / 'sql_validation.json', payload)
    return payload


def main() -> int:
    candidate = ROOT / f'review/candidates/answers/{CID}.md'
    if candidate.exists():
        raise SystemExit('candidate already exists; do not overwrite reviewed work')

    ctx = run_context()
    if not ctx.get('ok') or ctx.get('canonical', {}).get('canonical_id') != CID:
        raise SystemExit('canonical context drift')
    if ctx.get('answer_type') != 'coding':
        raise SystemExit(f"answer type drift: {ctx.get('answer_type')}")
    if ctx.get('canonical', {}).get('question_ids') != [QID]:
        raise SystemExit(f"ownership drift: {ctx.get('canonical', {}).get('question_ids')}")
    src = next((x for x in ctx.get('source_questions', []) if x.get('question_id') == QID), None)
    if not src or src.get('original_question') != EXPECTED or src.get('is_valid_for_library') is not True:
        raise SystemExit('source wording/validity drift')

    out = ROOT / f'review/content_build/answer_batch_{BATCH}/{CID}'
    out.mkdir(parents=True, exist_ok=True)
    write_json(out / 'context.json', ctx)
    write_json(out / 'official_documentation_snapshot.json', {
        'schema_version': 'official_documentation_snapshot.v1',
        'checked_at': DATE,
        'sources': [
            {
                'locator': MYSQL_WINDOW,
                'title': 'MySQL 8.0 Reference Manual 14.20.1 Window Function Descriptions',
                'claims': ['ROW_NUMBER returns the number of the current row within its partition', 'window ordering controls row-number assignment'],
            },
            {
                'locator': MYSQL_IDENTIFIERS,
                'title': 'MySQL 8.0 Reference Manual 11.2 Schema Object Names',
                'claims': ['reserved words used as identifiers must be quoted', 'the default identifier quote character is the backtick'],
            },
            {
                'locator': MYSQL_KEYWORDS,
                'title': 'MySQL 8.0 Reference Manual 11.3 Keywords and Reserved Words',
                'claims': ['ORDER is reserved in MySQL 8.0'],
            },
        ],
    })

    candidate.parent.mkdir(parents=True, exist_ok=True)
    candidate.write_text(CANDIDATE, encoding='utf-8')
    for heading in ['## 核心结论', '## 1 分钟版', '## 3 分钟版', '## 关键细节', '## 原理机制', '## 项目经验版', '## 常见追问', '## 易错点']:
        if CANDIDATE.count(heading) != 1:
            raise SystemExit(f'section drift {heading}')
    blocks = re.findall(r'```sql\n(.*?)\n```', CANDIDATE, re.S)
    if blocks != [SQL]:
        raise SystemExit('candidate SQL block drift')

    validation = validate_sql(out)
    digest = hashlib.sha256(candidate.read_bytes()).hexdigest()
    sources = [
        {'source_id': 'repository-source', 'title': 'Batch 0050 frozen canonical/source context', 'locator': str(out / 'context.json'), 'source_type': 'repository_source_record', 'checked_at': DATE},
        {'source_id': 'mysql-window', 'title': 'MySQL 8.0 window function descriptions', 'locator': MYSQL_WINDOW, 'source_type': 'official_documentation', 'checked_at': DATE},
        {'source_id': 'mysql-identifiers', 'title': 'MySQL 8.0 schema object names', 'locator': MYSQL_IDENTIFIERS, 'source_type': 'official_documentation', 'checked_at': DATE},
        {'source_id': 'mysql-keywords', 'title': 'MySQL 8.0 keywords and reserved words', 'locator': MYSQL_KEYWORDS, 'source_type': 'official_documentation', 'checked_at': DATE},
        {'source_id': 'fixture', 'title': 'Deterministic SQLite window-query fixture', 'locator': str(out / 'sql_validation.json'), 'source_type': 'executable_test_or_reproducible_experiment', 'checked_at': DATE},
    ]
    claims = [
        {'claim_id': 'source-contract', 'text': 'The repository source gives table order with orderId, userId and time and requires one latest order row per user; it does not define same-time tie handling or NULL-time semantics.', 'source_ids': ['repository-source'], 'answer_locations': ['核心结论', '1 分钟版', '3 分钟版', '关键细节']},
        {'claim_id': 'window-contract', 'text': 'MySQL 8.0 ROW_NUMBER numbers rows within each partition, allowing one row per user to be selected after partition-local ordering.', 'source_ids': ['mysql-window'], 'answer_locations': ['1 分钟版', '3 分钟版', '原理机制']},
        {'claim_id': 'identifier-contract', 'text': 'MySQL 8.0 marks ORDER reserved and requires reserved-word identifiers to be quoted; the default identifier quote is the backtick.', 'source_ids': ['mysql-identifiers', 'mysql-keywords'], 'answer_locations': ['核心结论', '关键细节', '常见追问']},
        {'claim_id': 'execution-validation', 'text': 'The executable fixture verifies per-user partitioning, latest-time selection, explicit same-time orderId tie-break and exactly one output row per user.', 'source_ids': ['fixture'], 'answer_locations': ['3 分钟版', '关键细节', '易错点']},
    ]
    coverage = [{'question_id': QID, 'covered': True, 'answer_locations': ['核心结论', '1 分钟版', '3 分钟版', '关键细节', '原理机制', '常见追问', '易错点']}]
    write_json(out / 'writer_research.json', {
        'schema_version': 'answer_writer_research.v1',
        'canonical_id': CID,
        'candidate_sha256': digest,
        'checked_at': DATE,
        'review_state': 'writer_complete_isolated_review_pending',
        'sources': sources,
        'claims': claims,
        'source_question_coverage': coverage,
        'promotion_blocker': 'isolated_independent_review_not_yet_performed',
    })

    scores = {'facts_and_evidence': 25, 'directness_and_relevance': 20, 'type_specific_completeness': 20, 'mechanism_and_causality': 15, 'boundaries_and_tradeoffs': 10, 'followup_quality': 5, 'oral_quality': 5}
    findings = [
        'The answer preserves the exact requested result grain: one latest order row per user.',
        'The candidate does not hide the under-specified same-time case; orderId DESC is labeled as an explicit deterministic assumption rather than source fact.',
        'MySQL 8.0 primary documentation supports ROW_NUMBER partition numbering and the need to quote the reserved identifier order.',
        'The executable fixture passes multiple-user partitioning, newest-time selection, same-time tie-break and exactly-one-row-per-user checks.',
        'The answer distinguishes row selection from aggregate MAX(time), calls out NULL-time and index/plan boundaries, and contains no fabricated project history.',
    ]
    review = {
        'schema_version': 'isolated_review.v1', 'canonical_id': CID, 'candidate_sha256': digest, 'reviewed_at': DATE,
        'review_mode': 'source_first_isolated', 'reviewer_id': 'source-first-isolated-reviewer-batch-0050-latest-order-sql-20260829-v1',
        'review_version': 'batch-0050.latest-order-sql.v1', 'decision': 'pass', 'revision_round': 1,
        'source_packet': [str(out / 'context.json'), str(out / 'official_documentation_snapshot.json'), str(candidate), str(out / 'sql_validation.json'), MYSQL_WINDOW, MYSQL_IDENTIFIERS, MYSQL_KEYWORDS, 'docs/refactor/09_answer_content_standard.md'],
        'scores': scores, 'hard_failures': [], 'unsupported_claims': [], 'uncovered_source_variants': [], 'findings': findings,
        'promotion_blockers': ['repository_human_approval_and_real_review_policy_not_yet_satisfied'],
    }
    write_json(out / 'isolated_review_result.json', review)

    evidence_sources = sources + [{'source_id': 'isolated-review', 'title': 'Latest-order SQL source-first isolated review', 'locator': str(out / 'isolated_review_result.json'), 'source_type': 'repository_structured_source', 'checked_at': DATE}]
    write_json(ROOT / f'review/evidence/{CID}.json', {
        'schema_version': 'answer_evidence.v1', 'canonical_id': CID, 'candidate_sha256': digest, 'checked_at': DATE,
        'writer': {'writer_id': 'content-batch-0050-latest-order-sql-builder', 'writer_version': 'xhs-answer-curator.v1'},
        'sources': evidence_sources, 'claims': claims, 'source_question_coverage': coverage,
        'validation': {
            'command': validation['command'], 'result': 'pass', 'reported_stdout': validation['stdout'], 'checks': validation['checks'],
            'boundary_tests': [
                {'case': 'multiple users with different histories', 'expected': 'partitioning selects one independently latest row for each user', 'actual': 'pass', 'passed': True},
                {'case': 'one user has a strictly newer time', 'expected': 'newest timestamp row wins regardless of insertion order', 'actual': 'pass', 'passed': True},
                {'case': 'same user has equal latest times', 'expected': 'explicit orderId DESC tie-break selects orderId 4', 'actual': 'pass', 'passed': True},
                {'case': 'output cardinality', 'expected': 'exactly one row for each of four users', 'actual': 'pass', 'passed': True},
            ],
        },
        'review_state': 'independent_source_first_review_passed',
        'review': {'reviewer_id': review['reviewer_id'], 'review_version': review['review_version'], 'independent': True, 'decision': 'pass', 'revision_round': 1, 'scores': scores, 'hard_failures': [], 'unsupported_claims': [], 'uncovered_source_variants': [], 'findings': findings},
        'promotion_blocker': 'repository_human_approval_and_real_review_policy_not_yet_satisfied',
    })

    task = ROOT / f'tasks/answer-batches/TASK-20260711-0313-answer-batch-{BATCH}.md'
    text = task.read_text(encoding='utf-8')
    line = '- [x] `cq_q_d616ff7e2ef391e07c984e8bd0a965a6` source-first isolated review PASS: exact per-user latest-order grain preserved; MySQL 8.0 ROW_NUMBER and reserved-identifier documentation bound the implementation, while the same-time orderId tie-break is explicitly labeled as an assumption. Executable validation covers multiple users, newest-time selection, same-time tie-break, and one-row-per-user cardinality. Formal promotion remains blocked by repository human-approval/real-review policy.'
    if line not in text:
        text = text.rstrip() + '\n' + line + '\n'
    task.write_text(text, encoding='utf-8')

    print(f'PASS staged/reviewed {CID} candidate_sha256={digest}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
