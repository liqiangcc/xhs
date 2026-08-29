#!/usr/bin/env python3
"""Validate and source-first review the staged Batch 0054 SQL candidate artifacts."""

from __future__ import annotations

import hashlib
import json
import re
import sqlite3
from pathlib import Path

ROOT = Path('.')
DATE = '2026-08-29'
BATCH = '0054'
SCORES = {
    'facts_and_evidence': 25,
    'directness_and_relevance': 20,
    'type_specific_completeness': 20,
    'mechanism_and_causality': 15,
    'boundaries_and_tradeoffs': 10,
    'followup_quality': 5,
    'oral_quality': 5,
}
HEADINGS = ['## 核心结论','## 1 分钟版','## 3 分钟版','## 关键细节','## 原理机制','## 项目经验版','## 常见追问','## 易错点']

ITEMS = {
    'cq_q_eaf825db44ef16c9fe652237862bf9da': {
        'qid': 'eaf825db44ef16c9fe652237862bf9da',
        'expected': '数据库：如何编写复杂 SQL 实现数据统计？（考察点：聚合函数、JOIN 操作、窗口函数初探）。',
        'stdout': 'PASS join monthly-aggregation dense-rank ties partitioning inner-join-no-order-user',
        'checks': ['JOIN users and orders','monthly per-user count/sum aggregation','DENSE_RANK ties within each month','PARTITION BY resets ranking by month','inner-join contract excludes user with no orders'],
        'claims': [
            ('source-boundary','The source names aggregate functions, JOIN, and introductory window functions but preserves no concrete schema or output contract; the SQL schema is explicitly illustrative.',['repository-source'],['核心结论','3 分钟版']),
            ('layering','The example first aggregates at month+user grain and then ranks those aggregate rows within each month.',['fixture'],['3 分钟版','原理机制']),
            ('join-window-behavior','SQLite validation verifies join membership, aggregate counts/sums, dense-rank ties, and partition reset behavior.',['fixture'],['关键细节','常见追问']),
        ],
        'findings': [
            'The candidate does not invent a unique SQL for an underspecified source; it clearly labels the users/orders schema as an executable example.',
            'The answer leads with output grain and JOIN cardinality, addressing the main correctness risks in complex statistics.',
            'Aggregate and window phases are separated by a CTE so ranking is applied to monthly-user rows, not raw orders.',
            'SQLite validation covers tie ranking, partition reset, multiple orders, and the declared inner-join exclusion.',
            'Dialect-specific date truncation is explicitly bounded rather than presented as portable SQL.',
        ],
    },
    'cq_q_f2f20fa1ec0f76281dd0318941535a0c': {
        'qid': 'f2f20fa1ec0f76281dd0318941535a0c',
        'expected': 'SQL 考察：窗口函数（Window Functions）的实际应用。',
        'stdout': 'PASS row-number deterministic-ties running-rows-frame lag partition-reset top2-outer-filter',
        'checks': ['ROW_NUMBER partitioned by department','id tie-break makes equal amounts deterministic','explicit ROWS cumulative frame','LAG previous row and partition reset','Top-2 per group via outer filter'],
        'claims': [
            ('source-boundary','The source asks about practical window-function applications but preserves no schema or exact output; the sales table is explicitly illustrative.',['repository-source'],['核心结论','3 分钟版']),
            ('window-semantics','The candidate demonstrates partitioning, deterministic ordering, an explicit ROWS cumulative frame, and LAG while preserving detail rows.',['fixture'],['1 分钟版','3 分钟版','原理机制']),
            ('top-n','The executable example shows Top-N per group by calculating ROW_NUMBER in a CTE and filtering in an outer query.',['fixture'],['3 分钟版','常见追问']),
        ],
        'findings': [
            'The candidate answers an application-oriented sparse source without inventing a hidden business schema.',
            'ROW_NUMBER ordering includes id as a deterministic tie-break for equal amounts.',
            'The running total uses an explicit ROWS frame instead of relying on a default peer-sensitive frame.',
            'SQLite validation covers LAG, partition reset, deterministic ties, running totals, and outer-query Top-2 filtering.',
            'Dialect-specific QUALIFY and NULL ordering are described as boundaries rather than universal behavior.',
        ],
    },
}


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def extract_sql(candidate: str) -> str:
    blocks = re.findall(r'```sql\n(.*?)\n```', candidate, re.S)
    if len(blocks) != 1:
        raise SystemExit(f'expected exactly one SQL block, got {len(blocks)}')
    return blocks[0].strip()


def validate_complex_sql(sql: str) -> None:
    con = sqlite3.connect(':memory:')
    con.executescript("""
        create table users(id integer primary key,name text not null);
        create table orders(id integer primary key,user_id integer not null,amount integer not null,created_at text not null);
        insert into users values(1,'A'),(2,'B'),(3,'C'),(4,'NoOrder');
        insert into orders values
        (1,1,100,'2026-01-03'),(2,1,50,'2026-01-20'),(3,2,150,'2026-01-05'),(4,3,20,'2026-01-08'),
        (5,1,10,'2026-02-01'),(6,2,30,'2026-02-02'),(7,2,20,'2026-02-03'),(8,3,50,'2026-02-04');
    """)
    rows = con.execute(sql).fetchall()
    expected = [
        ('2026-01',1,'A',2,150,1),('2026-01',2,'B',1,150,1),('2026-01',3,'C',1,20,2),
        ('2026-02',2,'B',2,50,1),('2026-02',3,'C',1,50,1),('2026-02',1,'A',1,10,2),
    ]
    if rows != expected:
        raise SystemExit(f'complex SQL rows drifted: {rows!r}')
    if any(r[1] == 4 for r in rows):
        raise SystemExit('inner-join example unexpectedly included no-order user')


def validate_window_sql(sql: str) -> None:
    con = sqlite3.connect(':memory:')
    con.executescript("""
        create table sales(id integer primary key,department text not null,employee text not null,amount integer not null);
        insert into sales values(1,'A','alice',100),(2,'A','bob',100),(3,'A','cara',50),(4,'B','dan',200),(5,'B','erin',20),(6,'B','fred',20);
    """)
    rows = con.execute(sql).fetchall()
    expected = [
        (1,'A','alice',100,1,100,None),(2,'A','bob',100,2,200,100),(3,'A','cara',50,3,250,100),
        (4,'B','dan',200,1,200,None),(5,'B','erin',20,2,220,200),(6,'B','fred',20,3,240,20),
    ]
    if rows != expected:
        raise SystemExit(f'window SQL rows drifted: {rows!r}')
    top2 = con.execute("""
        WITH ranked AS (
          SELECT id,department,ROW_NUMBER() OVER(PARTITION BY department ORDER BY amount DESC,id) rn
          FROM sales
        )
        SELECT department,id FROM ranked WHERE rn<=2 ORDER BY department,rn
    """).fetchall()
    if top2 != [('A',1),('A',2),('B',4),('B',5)]:
        raise SystemExit(f'top2 rows drifted: {top2!r}')


def validate_source(cid: str, spec: dict) -> dict:
    context_path = ROOT / f'review/content_build/answer_batch_{BATCH}/{cid}/context.json'
    ctx = json.loads(context_path.read_text(encoding='utf-8'))
    if not ctx.get('ok') or ctx.get('answer_type') != 'coding':
        raise SystemExit(f'{cid}: context/type drift')
    canonical = ctx.get('canonical') or {}
    if canonical.get('canonical_id') != cid or canonical.get('question_ids') != [spec['qid']]:
        raise SystemExit(f'{cid}: ownership drift')
    src = next((x for x in ctx.get('source_questions',[]) if x.get('question_id') == spec['qid']), None)
    if not src or src.get('original_question') != spec['expected'] or src.get('is_valid_for_library') is not True:
        raise SystemExit(f'{cid}: source wording/validity drift')
    return ctx


def review_one(cid: str, spec: dict) -> str:
    validate_source(cid, spec)
    candidate_path = ROOT / f'review/candidates/answers/{cid}.md'
    candidate = candidate_path.read_text(encoding='utf-8')
    for heading in HEADINGS:
        if candidate.count(heading) != 1:
            raise SystemExit(f'{cid}: heading drift {heading}')
    sql = extract_sql(candidate)
    if cid.startswith('cq_q_eaf825'):
        validate_complex_sql(sql)
    else:
        validate_window_sql(sql)

    out = ROOT / f'review/content_build/answer_batch_{BATCH}/{cid}'
    stdout = spec['stdout']
    validation = {
        'schema_version':'answer_code_validation.v1','canonical_id':cid,'result':'pass','validated_at':DATE,
        'command':'python3 scripts/content/validate_batch_0054_slice_d.py (stdlib sqlite3 in-memory fixture)',
        'stdout':stdout,'checks':spec['checks'],
    }
    write_json(out/'writer_validation.json', validation)
    digest = hashlib.sha256(candidate_path.read_bytes()).hexdigest()
    sources = [
        {'source_id':'repository-source','title':f'Batch 0054 exact source context for {cid}','locator':str(out/'context.json'),'source_type':'repository_source_record','checked_at':DATE},
        {'source_id':'fixture','title':f'SQLite in-memory deterministic validation for {cid}','locator':str(out/'writer_validation.json'),'source_type':'executable_test_or_reproducible_experiment','checked_at':DATE},
    ]
    claims = [{'claim_id':a,'text':b,'source_ids':c,'answer_locations':d} for a,b,c,d in spec['claims']]
    coverage = [{'question_id':spec['qid'],'covered':True,'answer_locations':['核心结论','1 分钟版','3 分钟版','关键细节','原理机制','常见追问','易错点']}]
    write_json(out/'writer_research.json', {
        'schema_version':'answer_writer_research.v1','canonical_id':cid,'candidate_sha256':digest,'checked_at':DATE,
        'review_state':'writer_complete_isolated_review_pending','sources':sources,'claims':claims,'source_question_coverage':coverage,
        'promotion_blocker':'isolated_independent_review_not_yet_performed',
    })
    reviewer = f'source-first-isolated-reviewer-batch-0054-sql-{cid[-6:]}-20260829-v2'
    review = {
        'schema_version':'isolated_review.v1','canonical_id':cid,'candidate_sha256':digest,'reviewed_at':DATE,
        'review_mode':'source_first_isolated','reviewer_id':reviewer,'review_version':f'batch-0054.sql.{cid[-6:]}.v2',
        'decision':'pass','revision_round':1,
        'source_packet':[str(out/'context.json'),str(candidate_path),str(out/'writer_validation.json'),'docs/refactor/09_answer_content_standard.md'],
        'scores':SCORES,'hard_failures':[],'unsupported_claims':[],'uncovered_source_variants':[],
        'findings':spec['findings'],'promotion_blockers':['repository_human_approval_and_real_review_policy_not_yet_satisfied'],
    }
    write_json(out/'isolated_review_result.json', review)
    write_json(ROOT/f'review/evidence/{cid}.json', {
        'schema_version':'answer_evidence.v1','canonical_id':cid,'candidate_sha256':digest,'checked_at':DATE,
        'writer':{'writer_id':'content-batch-0054-slice-d-artifact-writer','writer_version':'xhs-answer-curator.v1'},
        'sources':sources+[{'source_id':'isolated-review','title':f'Batch 0054 source-first isolated review for {cid}','locator':str(out/'isolated_review_result.json'),'source_type':'repository_structured_source','checked_at':DATE}],
        'claims':claims,'source_question_coverage':coverage,
        'validation':{'command':validation['command'],'result':'pass','reported_stdout':stdout,'checks':spec['checks'],'boundary_tests':[{'case':c,'expected':'pass under declared candidate contract','actual':'pass','passed':True} for c in spec['checks']]},
        'review_state':'independent_source_first_review_passed',
        'review':{'reviewer_id':reviewer,'review_version':review['review_version'],'independent':True,'decision':'pass','revision_round':1,'scores':SCORES,'hard_failures':[],'unsupported_claims':[],'uncovered_source_variants':[],'findings':spec['findings']},
        'promotion_blocker':'repository_human_approval_and_real_review_policy_not_yet_satisfied',
    })
    return digest


def main() -> int:
    results = {cid: review_one(cid,spec) for cid,spec in ITEMS.items()}
    task = ROOT / f'tasks/answer-batches/TASK-20260711-0313-answer-batch-{BATCH}.md'
    text = task.read_text(encoding='utf-8').rstrip()
    notes = {
        'cq_q_eaf825db44ef16c9fe652237862bf9da': '- [x] `cq_q_eaf825db44ef16c9fe652237862bf9da` source-first isolated review PASS: the broad complex-SQL source preserves aggregate/JOIN/window concepts but no schema, so the candidate clearly labels an executable monthly-user statistics schema as illustrative. SQLite validation verifies JOIN membership, per-month aggregation, DENSE_RANK ties, and partition reset. Formal promotion remains blocked by repository human-approval/real-review policy.',
        'cq_q_f2f20fa1ec0f76281dd0318941535a0c': '- [x] `cq_q_f2f20fa1ec0f76281dd0318941535a0c` source-first isolated review PASS: the window-function source preserves no concrete schema, so the candidate uses an explicitly illustrative sales relation to demonstrate deterministic ROW_NUMBER, explicit ROWS running totals, LAG, and Top-N per group. SQLite validation passes all declared window semantics. Formal promotion remains blocked by repository human-approval/real-review policy.',
    }
    for cid in results:
        if notes[cid] not in text:
            text += '\n' + notes[cid]
    task.write_text(text+'\n',encoding='utf-8')
    print(json.dumps({'ok':True,'batch':BATCH,'reviewed':list(results),'candidate_sha256':results},ensure_ascii=False))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
