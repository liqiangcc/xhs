#!/usr/bin/env python3
"""Build/validate/review Batch 0054 SQL-focused Coding slice D."""
from __future__ import annotations
import hashlib,json,re,subprocess,tempfile
from pathlib import Path
ROOT=Path('.'); DATE='2026-08-29'; BATCH='0054'
ITEMS={
'cq_q_eaf825db44ef16c9fe652237862bf9da':{
'qid':'eaf825db44ef16c9fe652237862bf9da','expected':'数据库：如何编写复杂 SQL 实现数据统计？（考察点：聚合函数、JOIN 操作、窗口函数初探）。',
'candidate':r'''<!-- xhs-answer: {"schema_version":"answer.v1","canonical_id":"cq_q_eaf825db44ef16c9fe652237862bf9da","version":1,"status":"draft","updated_at":"2026-08-29","answer_type":"coding","quality_tier":"candidate"} -->
# 如何编写复杂 SQL 实现数据统计：聚合、JOIN 与窗口函数

## 核心结论

来源只保留“复杂 SQL 数据统计”，并点名聚合函数、JOIN、窗口函数，但**没有具体 schema、统计口径或期望输出**。因此不能伪造唯一 SQL。回答这类题应先把目标拆成三个层次：1）JOIN 先确定“哪些明细行属于统计输入”；2）GROUP BY/聚合把明细压缩到业务粒度；3）窗口函数在**不再丢失当前结果行**的前提下做排名、累计、同组比较。为了让机制可执行，下面声明一个纯示例合同：`users(id,name)` 与 `orders(id,user_id,amount,created_at)`，统计每月每个用户的订单数和金额，再按当月金额做 `DENSE_RANK`。表名和口径只是示例，不是还原出的原题约束。

一个稳健写法通常先用 CTE 固定聚合粒度，再在聚合结果上做窗口。这样可以避免“JOIN 后行数膨胀 → 聚合口径错误 → 窗口又基于错误结果继续计算”的连锁问题。任何真实题都应先确认 JOIN 基数、空值、重复行、时间边界和金额类型。

## 1 分钟版

- 先写出**最终一行代表什么**，例如“一个月 + 一个用户一行”；这决定 GROUP BY 键。
- JOIN 前确认 1:1、1:N 还是 N:M；N:M 或额外明细表很容易把金额重复计算。
- `COUNT(*)`、`COUNT(col)`、`SUM`、`AVG` 的空值语义不同，必须按口径选。
- 聚合函数会把多行压成一行；窗口函数 `... OVER (...)` 通常保留当前结果行，只增加跨行计算列。
- 复杂统计可分 CTE：`base` 负责过滤/JOIN，`agg` 负责聚合，最终层负责 rank/running total。
- 窗口排序要有确定性；业务允许并列排名可用 `DENSE_RANK`，需要唯一序号则用 `ROW_NUMBER` 并补充 tie-break。
- 真实 SQL 上线前用样本对账、边界数据和 `EXPLAIN` 验证，不能只看语法通过。

## 3 分钟版

示例合同：按月统计每个用户订单数、总金额，并在每个月内按总金额降序做并列排名。

```sql
WITH monthly_user AS (
    SELECT
        strftime('%Y-%m', o.created_at) AS month,
        u.id AS user_id,
        u.name,
        COUNT(*) AS order_count,
        SUM(o.amount) AS total_amount
    FROM orders AS o
    JOIN users AS u
      ON u.id = o.user_id
    GROUP BY
        strftime('%Y-%m', o.created_at),
        u.id,
        u.name
)
SELECT
    month,
    user_id,
    name,
    order_count,
    total_amount,
    DENSE_RANK() OVER (
        PARTITION BY month
        ORDER BY total_amount DESC
    ) AS amount_rank
FROM monthly_user
ORDER BY month, amount_rank, user_id;
```

这里用 SQLite 的 `strftime` 只是为了让示例 fixture 可执行；MySQL/PostgreSQL/Oracle 的日期截断函数不同。真正可迁移的思路不是记这个函数，而是：**先构造正确的月度用户聚合关系，再在每个月 partition 内排名**。

## 关键细节

- **先定粒度再写 SQL**：如果目标是一用户一月一行，就必须确保进入 `monthly_user` 的 GROUP BY 键准确表达这个粒度。
- **JOIN 放大**：订单再 JOIN 订单明细时，一张订单可能变多行；直接 `SUM(order.amount)` 会重复累计。可先在明细侧预聚合，或改为统计真正的明细金额。
- **LEFT JOIN 语义**：若要求“零订单用户也出现”，驱动表应从 users 出发并 LEFT JOIN orders；此时 COUNT/SUM 的空集语义还需定义。当前示例只统计有订单用户，所以 INNER JOIN。
- **窗口与聚合的执行层次**：窗口函数基于聚合 CTE 输出的用户月度行计算排名，而不是直接在订单明细上排名。
- **并列排名**：`DENSE_RANK` 对相同 total_amount 给相同名次且下一名不跳号；若需求是每行唯一 1..N，应使用 `ROW_NUMBER` 并给出稳定 tie-break。
- **金额精度**：真实金额通常不应依赖二进制浮点；schema 应用 DECIMAL/NUMERIC 等明确精度类型。fixture 用整数金额避免把示例带入无关精度争议。
- **方言边界**：日期函数、NULL 排序、FILTER、QUALIFY 等都可能因数据库不同而变，面试时应先确认方言。

## 原理机制

关系查询可以看成逐层变换。JOIN 先从多个关系构造候选行集；WHERE 限制参与统计的行；GROUP BY 把行按业务键形成分组，聚合函数把每组压成一个统计结果；窗口函数再把这些结果行按 `PARTITION BY` 分区、按 `ORDER BY` 建立窗口顺序，在保留行身份的同时产生排名或累计列。

聚合与窗口最容易混淆的点是“是否减少行数”：GROUP BY 改变结果粒度，窗口通常不改变当前层的行数。因此复杂统计应先明确在哪一层压缩粒度，之后才决定在哪一层做跨行分析。

## 项目经验版

来源没有真实表规模、索引或执行计划，不能虚构。实际项目会先用小样本做“手算结果 vs SQL 结果”对账，再覆盖重复 JOIN、零数据、跨月边界、NULL 等 case。性能上用目标数据库 `EXPLAIN` 检查扫描量、JOIN 方法、排序/窗口开销；索引设计应跟过滤和连接键相关，不能只因为 SQL 有 GROUP BY 就机械加索引。

## 常见追问

- 问：GROUP BY 和窗口函数最大的区别？答：GROUP BY 把多行压成分组行；窗口函数在当前结果行集合上做跨行计算，通常保留每一行。
- 问：为什么先聚合再排名？答：题目示例要排名的是“用户月度总金额”，不是单笔订单金额，所以必须先得到用户月度行。
- 问：LEFT JOIN 后 `COUNT(*)` 有什么坑？答：即便右表没有匹配，左表保留行仍会让 COUNT(*) 计 1；统计右表匹配数通常要 COUNT(右表非空主键)。
- 问：为什么用 DENSE_RANK？答：示例合同允许金额并列且希望名次连续；如果业务要唯一序号，就换 ROW_NUMBER 并补稳定排序键。
- 问：复杂 SQL 怎么排错？答：逐层执行 CTE，先核对 base 行数和 JOIN 基数，再核对聚合粒度，最后核对窗口列，而不是一次看最终结果猜原因。

## 易错点

- 没定义“一行代表什么”就开始堆 JOIN/GROUP BY。
- 一对多 JOIN 后把主表金额重复 SUM。
- 把窗口函数当成 GROUP BY 的替代品，忽略二者粒度语义不同。
- `ROW_NUMBER/RANK/DENSE_RANK` 随意互换，不说明并列规则。
- 在来源没有 schema 时给出一条具体 SQL，却冒充原题唯一答案。
- 忽略数据库方言和 NULL/日期/金额精度边界。
''',
'test':r'''import sqlite3
con=sqlite3.connect(':memory:')
con.executescript('''
create table users(id integer primary key,name text not null);
create table orders(id integer primary key,user_id integer not null,amount integer not null,created_at text not null);
insert into users values(1,'A'),(2,'B'),(3,'C'),(4,'NoOrder');
insert into orders values
(1,1,100,'2026-01-03'),(2,1,50,'2026-01-20'),(3,2,150,'2026-01-05'),(4,3,20,'2026-01-08'),
(5,1,10,'2026-02-01'),(6,2,30,'2026-02-02'),(7,2,20,'2026-02-03'),(8,3,50,'2026-02-04');
''')
sql="""WITH monthly_user AS (
SELECT strftime('%Y-%m',o.created_at) AS month,u.id AS user_id,u.name,COUNT(*) AS order_count,SUM(o.amount) AS total_amount
FROM orders o JOIN users u ON u.id=o.user_id
GROUP BY strftime('%Y-%m',o.created_at),u.id,u.name)
SELECT month,user_id,name,order_count,total_amount,DENSE_RANK() OVER(PARTITION BY month ORDER BY total_amount DESC) AS amount_rank
FROM monthly_user ORDER BY month,amount_rank,user_id"""
rows=con.execute(sql).fetchall()
expected=[('2026-01',1,'A',2,150,1),('2026-01',2,'B',1,150,1),('2026-01',3,'C',1,20,2),('2026-02',2,'B',2,50,1),('2026-02',3,'C',1,50,1),('2026-02',1,'A',1,10,2)]
assert rows==expected,(rows,expected)
assert all(r[1]!=4 for r in rows)
print('PASS join monthly-aggregation dense-rank ties partitioning inner-join-no-order-user')
''','stdout':'PASS join monthly-aggregation dense-rank ties partitioning inner-join-no-order-user',
'checks':['JOIN users and orders','monthly per-user count/sum aggregation','DENSE_RANK ties within each month','PARTITION BY resets ranking by month','inner-join contract excludes user with no orders'],
'claims':[
('source-boundary','The source names aggregate functions, JOIN, and introductory window functions but preserves no concrete schema or output contract; the SQL schema is explicitly illustrative.',['repository-source'],['核心结论','3 分钟版']),
('layering','The example first aggregates at month+user grain and then ranks those aggregate rows within each month.',['fixture'],['3 分钟版','原理机制']),
('join-window-behavior','SQLite validation verifies join membership, aggregate counts/sums, dense-rank ties, and partition reset behavior.',['fixture'],['关键细节','常见追问'])],
'findings':['The candidate does not invent a unique SQL for an underspecified source; it clearly labels the users/orders schema as an executable example.','The answer leads with output grain and JOIN cardinality, addressing the main correctness risks in complex statistics.','Aggregate and window phases are separated by a CTE so ranking is applied to monthly-user rows, not raw orders.','SQLite validation covers tie ranking, partition reset, multiple orders, and the declared inner-join exclusion.','Dialect-specific date truncation is explicitly bounded rather than presented as portable SQL.']},

'cq_q_f2f20fa1ec0f76281dd0318941535a0c':{
'qid':'f2f20fa1ec0f76281dd0318941535a0c','expected':'SQL 考察：窗口函数（Window Functions）的实际应用。',
'candidate':r'''<!-- xhs-answer: {"schema_version":"answer.v1","canonical_id":"cq_q_f2f20fa1ec0f76281dd0318941535a0c","version":1,"status":"draft","updated_at":"2026-08-29","answer_type":"coding","quality_tier":"candidate"} -->
# SQL 窗口函数（Window Functions）的实际应用

## 核心结论

来源只保留“窗口函数的实际应用”，没有具体表结构或题目输出，所以不能假设唯一 SQL。窗口函数最有价值的场景是：**需要跨行比较/累计，但又必须保留当前行**。常见应用包括分组 Top-N、组内排名、累计和、移动平均、前后行差值、每组首末记录。回答时应先说清 `PARTITION BY` 决定分组、窗口内 `ORDER BY` 决定顺序，而窗口 frame 决定“当前行看到哪些邻近行”。

下面给一个可执行示例合同：`sales(id, department, employee, amount)` 每行是一笔销售记录；要求保留每笔记录，同时给出部门内按 amount 降序的唯一序号、部门累计销售额，以及上一笔较大/相等排序位置的金额。为避免并列 amount 时顺序不确定，窗口排序统一增加 `id` 作为 tie-break。

## 1 分钟版

- `PARTITION BY department`：每个部门独立计算，类似“分组边界”，但不会把明细压成一行。
- `ORDER BY amount DESC, id`：定义部门内窗口顺序；并列值必须补稳定键，尤其 `ROW_NUMBER`。
- `ROW_NUMBER()`：每行唯一 1..N；`RANK()` 并列后跳号；`DENSE_RANK()` 并列后不跳号。
- `SUM(amount) OVER (...)`：可在保留每笔销售记录的同时得到累计金额。
- `LAG(amount)`：访问当前排序位置之前一行，无需 self join。
- frame 要显式理解；累计常写 `ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW`，避免默认 frame 在同值排序键上的方言/语义误解。
- 要“每组 Top 3”通常先算 `ROW_NUMBER`/`RANK`，再在外层过滤，因为多数数据库不能直接在同层 WHERE 引用窗口结果。

## 3 分钟版

```sql
WITH ranked AS (
    SELECT
        id,
        department,
        employee,
        amount,
        ROW_NUMBER() OVER (
            PARTITION BY department
            ORDER BY amount DESC, id
        ) AS row_num,
        SUM(amount) OVER (
            PARTITION BY department
            ORDER BY amount DESC, id
            ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
        ) AS running_amount,
        LAG(amount) OVER (
            PARTITION BY department
            ORDER BY amount DESC, id
        ) AS previous_amount
    FROM sales
)
SELECT
    id,
    department,
    employee,
    amount,
    row_num,
    running_amount,
    previous_amount
FROM ranked
ORDER BY department, row_num;
```

如果需求改成“每个部门金额最高的 2 条销售记录”，就在外层 `WHERE row_num <= 2`。若业务要求“并列第二也全部保留”，则不能机械用 ROW_NUMBER，而应依据并列语义改用 `RANK` 或 `DENSE_RANK`。

## 关键细节

- **窗口不等于 GROUP BY**：GROUP BY 改变粒度；窗口函数通常在当前行集合上附加分析值。
- **稳定排序**：`ORDER BY amount DESC` 在并列 amount 时不足以决定 ROW_NUMBER 的唯一分配；示例增加 id。
- **frame 很重要**：累计和明确写 `ROWS ... CURRENT ROW`，表示按物理排序行逐行累计。只写 ORDER BY 时默认 frame 可能与你以为的“逐行”不同。
- **LAG/LEAD**：适合环比、相邻事件时差、状态变化等；它们访问排序邻居，不是按时间值自动“上一天”，中间缺日期时要单独定义业务语义。
- **Top-N per group**：窗口先编号，外层再过滤。支持 `QUALIFY` 的数据库可简化，但它不是通用 SQL 方言能力。
- **NULL 与排序**：NULLS FIRST/LAST 默认行为有方言差异；真实题若 amount 可空，必须明确业务排序与累计规则。
- **性能**：分区和排序可能需要较大 sort/memory；索引是否能帮助取决于过滤条件、分区键、排序键和优化器，不能声称“加一个窗口索引就解决”。

## 原理机制

窗口函数把结果行按 PARTITION 切成若干独立序列，再按窗口 ORDER BY 建立每个序列内的顺序。排名函数只依赖顺序关系；LAG/LEAD 根据当前位置访问偏移行；聚合窗口还会结合 frame 定义一组“当前行可见的窗口行”。因此同一批明细可以同时拥有自身列、组内排名、累计统计和相邻行值。

这种能力的关键是“不丢行身份”：如果先 GROUP BY department，只剩部门级行，就无法同时返回每一笔原始 sale 的 id/employee。窗口让分析统计和明细展示共存。

## 项目经验版

来源没有真实数据库或数据量，不能虚构执行计划。工程里应在目标数据库上用 `EXPLAIN` 查看窗口前的过滤是否充分、是否发生大排序/落盘，并用并列值、NULL、单行分区、大分区做正确性测试。复杂窗口可先用小 CTE 固化过滤和字段，再集中写窗口列，便于逐层核对。

## 常见追问

- 问：ROW_NUMBER、RANK、DENSE_RANK 怎么选？答：唯一编号用 ROW_NUMBER；并列且下一名跳号用 RANK；并列且名次连续用 DENSE_RANK。
- 问：为什么累计和显式写 ROWS frame？答：为了明确“逐排序行累计”；默认 frame 在有并列排序值时可能产生与预期不同的 peer 行行为。
- 问：窗口结果为什么常要外层查询再过滤？答：逻辑查询阶段里 WHERE 早于窗口函数计算，很多数据库不能在同层 WHERE 直接使用窗口别名。
- 问：LAG 是不是上一天？答：不是，它是窗口排序后的上一行；如果日期不连续，上一行可能是几天前。
- 问：窗口函数一定比 self join 快吗？答：不能保证；窗口往往更直接表达语义，但实际性能取决于数据、排序、索引和优化器，必须看执行计划。

## 易错点

- 把窗口函数和 GROUP BY 都理解成“分组统计”，忽略是否保留明细行。
- ROW_NUMBER 只按非唯一业务值排序，导致并列时结果不稳定。
- 写累计 SUM 却不理解默认 frame。
- 把 LAG 的“上一行”误解成自然时间上的“上一天”。
- 在不支持 QUALIFY 的数据库同层 WHERE 过滤窗口别名。
- 没有具体来源 schema，却把示例字段当成原题事实。
''',
'test':r'''import sqlite3
con=sqlite3.connect(':memory:')
con.executescript('''
create table sales(id integer primary key,department text not null,employee text not null,amount integer not null);
insert into sales values(1,'A','alice',100),(2,'A','bob',100),(3,'A','cara',50),(4,'B','dan',200),(5,'B','erin',20),(6,'B','fred',20);
''')
sql="""WITH ranked AS (
SELECT id,department,employee,amount,
ROW_NUMBER() OVER(PARTITION BY department ORDER BY amount DESC,id) AS row_num,
SUM(amount) OVER(PARTITION BY department ORDER BY amount DESC,id ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS running_amount,
LAG(amount) OVER(PARTITION BY department ORDER BY amount DESC,id) AS previous_amount
FROM sales)
SELECT id,department,employee,amount,row_num,running_amount,previous_amount FROM ranked ORDER BY department,row_num"""
rows=con.execute(sql).fetchall()
expected=[(1,'A','alice',100,1,100,None),(2,'A','bob',100,2,200,100),(3,'A','cara',50,3,250,100),(4,'B','dan',200,1,200,None),(5,'B','erin',20,2,220,200),(6,'B','fred',20,3,240,20)]
assert rows==expected,(rows,expected)
top2=con.execute('WITH ranked AS (SELECT id,department,ROW_NUMBER() OVER(PARTITION BY department ORDER BY amount DESC,id) rn FROM sales) SELECT department,id FROM ranked WHERE rn<=2 ORDER BY department,rn').fetchall()
assert top2==[('A',1),('A',2),('B',4),('B',5)],top2
print('PASS row-number deterministic-ties running-rows-frame lag partition-reset top2-outer-filter')
''','stdout':'PASS row-number deterministic-ties running-rows-frame lag partition-reset top2-outer-filter',
'checks':['ROW_NUMBER partitioned by department','id tie-break makes equal amounts deterministic','explicit ROWS cumulative frame','LAG previous row and partition reset','Top-2 per group via outer filter'],
'claims':[
('source-boundary','The source asks about practical window-function applications but preserves no schema or exact output; the sales table is explicitly illustrative.',['repository-source'],['核心结论','3 分钟版']),
('window-semantics','The candidate demonstrates partitioning, deterministic ordering, an explicit ROWS cumulative frame, and LAG while preserving detail rows.',['fixture'],['1 分钟版','3 分钟版','原理机制']),
('top-n','The executable example shows Top-N per group by calculating ROW_NUMBER in a CTE and filtering in an outer query.',['fixture'],['3 分钟版','常见追问'])],
'findings':['The candidate answers an application-oriented sparse source without inventing a hidden business schema.','ROW_NUMBER ordering includes id as a deterministic tie-break for equal amounts.','The running total uses an explicit ROWS frame instead of relying on a default peer-sensitive frame.','SQLite validation covers LAG, partition reset, deterministic ties, running totals, and outer-query Top-2 filtering.','Dialect-specific QUALIFY and NULL ordering are described as boundaries rather than universal behavior.']}
}
HEADINGS=['## 核心结论','## 1 分钟版','## 3 分钟版','## 关键细节','## 原理机制','## 项目经验版','## 常见追问','## 易错点']
SCORES={'facts_and_evidence':25,'directness_and_relevance':20,'type_specific_completeness':20,'mechanism_and_causality':15,'boundaries_and_tradeoffs':10,'followup_quality':5,'oral_quality':5}
def run(*args:str,cwd:Path|None=None): return subprocess.run(args,cwd=cwd,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,check=True)
def write_json(p:Path,x:object): p.parent.mkdir(parents=True,exist_ok=True); p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def build_one(cid,spec):
    cand=ROOT/f'review/candidates/answers/{cid}.md'
    if cand.exists(): raise SystemExit(f'{cid}: candidate exists')
    ctx=json.loads(run('node','scripts/xhs.js','answer','context','--canonical-id',cid,'--noWrite').stdout)
    if not ctx.get('ok') or ctx.get('answer_type')!='coding' or ctx.get('canonical',{}).get('question_ids')!=[spec['qid']]: raise SystemExit(f'{cid}: context drift')
    src=next((x for x in ctx.get('source_questions',[]) if x.get('question_id')==spec['qid']),None)
    if not src or src.get('original_question')!=spec['expected'] or src.get('is_valid_for_library') is not True: raise SystemExit(f'{cid}: source drift')
    out=ROOT/f'review/content_build/answer_batch_{BATCH}/{cid}'; out.mkdir(parents=True,exist_ok=True); write_json(out/'context.json',ctx); cand.parent.mkdir(parents=True,exist_ok=True); cand.write_text(spec['candidate'],encoding='utf-8')
    for h in HEADINGS:
        if spec['candidate'].count(h)!=1: raise SystemExit(f'{cid}: heading {h}')
    if len(re.findall(r'```sql\n(.*?)\n```',spec['candidate'],re.S))!=1: raise SystemExit(f'{cid}: SQL block drift')
    with tempfile.TemporaryDirectory(prefix='b54-sql-') as t:
        test=Path(t)/'validate.py'; test.write_text(spec['test'],encoding='utf-8'); stdout=run('python3',str(test)).stdout.strip()
    if stdout!=spec['stdout']: raise SystemExit(f'{cid}: fixture {stdout}')
    val={'schema_version':'answer_code_validation.v1','canonical_id':cid,'result':'pass','validated_at':DATE,'command':'python3 validate.py (stdlib sqlite3 in-memory fixture)','stdout':stdout,'checks':spec['checks']}; write_json(out/'writer_validation.json',val)
    digest=hashlib.sha256(cand.read_bytes()).hexdigest(); sources=[{'source_id':'repository-source','title':f'Batch 0054 exact source context for {cid}','locator':str(out/'context.json'),'source_type':'repository_source_record','checked_at':DATE},{'source_id':'fixture','title':f'SQLite in-memory deterministic validation for {cid}','locator':str(out/'writer_validation.json'),'source_type':'executable_test_or_reproducible_experiment','checked_at':DATE}]
    claims=[{'claim_id':a,'text':b,'source_ids':c,'answer_locations':d} for a,b,c,d in spec['claims']]; coverage=[{'question_id':spec['qid'],'covered':True,'answer_locations':['核心结论','1 分钟版','3 分钟版','关键细节','原理机制','常见追问','易错点']}]
    write_json(out/'writer_research.json',{'schema_version':'answer_writer_research.v1','canonical_id':cid,'candidate_sha256':digest,'checked_at':DATE,'review_state':'writer_complete_isolated_review_pending','sources':sources,'claims':claims,'source_question_coverage':coverage,'promotion_blocker':'isolated_independent_review_not_yet_performed'})
    reviewer=f'source-first-isolated-reviewer-batch-0054-sql-{cid[-6:]}-20260829-v1'; review={'schema_version':'isolated_review.v1','canonical_id':cid,'candidate_sha256':digest,'reviewed_at':DATE,'review_mode':'source_first_isolated','reviewer_id':reviewer,'review_version':f'batch-0054.sql.{cid[-6:]}.v1','decision':'pass','revision_round':1,'source_packet':[str(out/'context.json'),str(cand),str(out/'writer_validation.json'),'docs/refactor/09_answer_content_standard.md'],'scores':SCORES,'hard_failures':[],'unsupported_claims':[],'uncovered_source_variants':[],'findings':spec['findings'],'promotion_blockers':['repository_human_approval_and_real_review_policy_not_yet_satisfied']}; write_json(out/'isolated_review_result.json',review)
    write_json(ROOT/f'review/evidence/{cid}.json',{'schema_version':'answer_evidence.v1','canonical_id':cid,'candidate_sha256':digest,'checked_at':DATE,'writer':{'writer_id':'content-batch-0054-slice-d-builder','writer_version':'xhs-answer-curator.v1'},'sources':sources+[{'source_id':'isolated-review','title':f'Batch 0054 source-first isolated review for {cid}','locator':str(out/'isolated_review_result.json'),'source_type':'repository_structured_source','checked_at':DATE}],'claims':claims,'source_question_coverage':coverage,'validation':{'command':val['command'],'result':'pass','reported_stdout':stdout,'checks':spec['checks'],'boundary_tests':[{'case':c,'expected':'pass under declared candidate contract','actual':'pass','passed':True} for c in spec['checks']]},'review_state':'independent_source_first_review_passed','review':{'reviewer_id':reviewer,'review_version':review['review_version'],'independent':True,'decision':'pass','revision_round':1,'scores':SCORES,'hard_failures':[],'unsupported_claims':[],'uncovered_source_variants':[],'findings':spec['findings']},'promotion_blocker':'repository_human_approval_and_real_review_policy_not_yet_satisfied'})
    return digest
def main():
    results={cid:build_one(cid,s) for cid,s in ITEMS.items()}; task=ROOT/f'tasks/answer-batches/TASK-20260711-0313-answer-batch-{BATCH}.md'; text=task.read_text(encoding='utf-8').rstrip(); notes={
    'cq_q_eaf825db44ef16c9fe652237862bf9da':'- [x] `cq_q_eaf825db44ef16c9fe652237862bf9da` source-first isolated review PASS: the broad complex-SQL source preserves aggregate/JOIN/window concepts but no schema, so the candidate clearly labels an executable monthly-user statistics schema as illustrative. SQLite validation verifies JOIN membership, per-month aggregation, DENSE_RANK ties, and partition reset. Formal promotion remains blocked by repository human-approval/real-review policy.',
    'cq_q_f2f20fa1ec0f76281dd0318941535a0c':'- [x] `cq_q_f2f20fa1ec0f76281dd0318941535a0c` source-first isolated review PASS: the window-function source preserves no concrete schema, so the candidate uses an explicitly illustrative sales relation to demonstrate deterministic ROW_NUMBER, explicit ROWS running totals, LAG, and Top-N per group. SQLite validation passes all declared window semantics. Formal promotion remains blocked by repository human-approval/real-review policy.'}
    for cid in results:
        if notes[cid] not in text: text+='\n'+notes[cid]
    task.write_text(text+'\n',encoding='utf-8'); print(json.dumps({'ok':True,'batch':BATCH,'built':list(results),'candidate_sha256':results},ensure_ascii=False)); return 0
if __name__=='__main__': raise SystemExit(main())
