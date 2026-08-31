#!/usr/bin/env python3
"""Source-first isolated review for the Batch 0062 slow-SQL scenario candidate."""
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
HEADINGS = ['## 核心结论', '## 1 分钟版', '## 3 分钟版', '## 关键细节', '## 原理机制', '## 项目经验版', '## 常见追问', '## 易错点']
SCORES = {
    'facts_and_evidence': 24,
    'directness_and_relevance': 20,
    'type_specific_completeness': 19,
    'mechanism_and_causality': 15,
    'boundaries_and_tradeoffs': 10,
    'followup_quality': 5,
    'oral_quality': 4,
}
PROMOTION_BLOCKER = 'repository_human_approval_and_real_review_policy_not_yet_satisfied'


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def main() -> int:
    out = ROOT / f'review/content_build/answer_batch_{BATCH}/{CID}'
    context_path = out / 'context.json'
    inventory_path = ROOT / f'review/content_build/answer_batch_{BATCH}/source_inventory.json'
    primary_path = out / 'primary_source_research.json'
    candidate_path = ROOT / f'review/candidates/answers/{CID}.md'

    # Reviewer isolation: source/context, primary sources, candidate and quality contract only.
    context = json.loads(context_path.read_text(encoding='utf-8'))
    inventory = json.loads(inventory_path.read_text(encoding='utf-8'))
    primary = json.loads(primary_path.read_text(encoding='utf-8'))
    candidate = candidate_path.read_text(encoding='utf-8')
    digest = hashlib.sha256(candidate_path.read_bytes()).hexdigest()

    if not context.get('ok') or context.get('answer_type') != 'scenario' or (context.get('canonical') or {}).get('canonical_id') != CID:
        raise SystemExit(f'{CID}: context/type drift')
    if (context.get('canonical') or {}).get('question_ids') != [QID]:
        raise SystemExit(f'{CID}: canonical ownership drift')
    rows = list(context.get('source_questions') or [])
    if len(rows) != 1 or rows[0].get('original_question') != EXPECTED_QUESTION:
        raise SystemExit(f'{CID}: source wording/occurrence drift')
    inv = next((x for x in inventory.get('canonicals', []) if x.get('canonical_id') == CID), None)
    if inventory.get('boundary_result') != 'pass' or not inv or inv.get('answer_type') != 'scenario' or inv.get('source_occurrence_count') != 1:
        raise SystemExit(f'{CID}: frozen inventory drift')
    if primary.get('schema_version') != 'answer_primary_source_research.v1' or primary.get('canonical_id') != CID or primary.get('source_boundary', {}).get('answer_type') != 'scenario':
        raise SystemExit(f'{CID}: primary-source packet drift')

    source_ids = {x.get('source_id') for x in primary.get('sources', [])}
    required_sources = {
        'mysql-84-slow-query-log',
        'mysql-84-statement-digests',
        'mysql-84-sys-statement-analysis',
        'mysql-84-explain',
        'mysql-84-optimizer-trace',
        'mysql-84-index-optimization',
    }
    if not required_sources.issubset(source_ids):
        raise SystemExit(f'{CID}: primary-source coverage missing: {sorted(required_sources - source_ids)}')

    for heading in HEADINGS:
        if candidate.count(heading) != 1:
            raise SystemExit(f'{CID}: section drift {heading}')
    if candidate.count('- 问：') < 5:
        raise SystemExit(f'{CID}: topic-specific followups insufficient')
    required_markers = [
        'MySQL 8.4', 'slow_query_log', 'long_query_time', 'sys.statement_analysis',
        'Performance Schema', 'EXPLAIN FORMAT=TREE', 'EXPLAIN ANALYZE',
        '会真正执行语句', 'optimizer_trace', 'INFORMATION_SCHEMA.OPTIMIZER_TRACE',
        'estimated rows', 'actual rows', 'rows examined', 'P95/P99', '灰度', '回滚',
        '新增索引有写放大', '一致性', '重试', '缓存/汇总',
    ]
    missing = [x for x in required_markers if x not in candidate]
    if missing:
        raise SystemExit(f'{CID}: scenario mechanism/boundary coverage missing: {missing}')
    if any(x in candidate for x in ['我负责过', '我在线上', '实际线上我们', '我们项目中', '我把 SQL 从']):
        raise SystemExit(f'{CID}: fabricated experience risk')
    if '来源没有提供我的真实项目' not in candidate:
        raise SystemExit(f'{CID}: explicit personal-fact boundary missing')

    findings = [
        'The single frozen source asks for a practical slow-SQL discovery/optimization method plus commands/tools; it does not provide a schema, data volume, QPS, latency threshold or personal production incident, and the candidate keeps those absent facts explicit instead of inventing them.',
        'The MySQL 8.4 primary-source packet supports the discovery layer: slow-query logging exposes configured slow statements, statement digests group structurally similar SQL, and sys.statement_analysis provides normalized aggregated statistics for workload-level prioritization.',
        'The answer provides a connected diagnostic data flow rather than a tool list: discover and rank statement families, freeze a representative case, inspect EXPLAIN, compare estimates with actual iterator evidence using EXPLAIN ANALYZE when execution is safe, then use optimizer_trace only when the optimizer decision itself needs deeper explanation.',
        'The EXPLAIN ANALYZE boundary is explicit and materially correct for MySQL 8.4: the candidate states that it actually executes the statement and therefore must not be treated as a universally harmless production plan-inspection command.',
        'Remediation is root-cause-specific rather than index-only. Indexes, query rewriting, access-pattern reduction, data-model changes, caching or precomputation are presented as alternatives with DML/storage, consistency/freshness and rollout costs; unnecessary-index cost is directly supported by the MySQL index documentation.',
        'Scenario completeness is adequate for this diagnostic question: assumptions/version boundary, end-to-end diagnostic flow, workload-impact/capacity framing, side-effect/idempotency/consistency boundaries, timeout/retry/degradation stance, observability, representative before/after load validation, canary rollout and rollback are all present without turning disaster recovery into a fake SQL fix.',
        'The answer closes the causal loop with comparable before/after metrics including tail latency, rows examined/returned, lock behavior and CPU/IO, and it requires continued digest monitoring after rollout rather than declaring success from a prettier EXPLAIN alone.',
        'The one-minute answer has five topic-specific oral points and the followups test slow-log-versus-digest discovery, EXPLAIN ANALYZE execution risk, optimizer_trace use, index tradeoffs, verification, retries and cache consistency. The three-minute section is longer than literal recital length, so oral quality is scored 4/5 rather than 5/5.',
    ]

    reviewer_id = 'source-first-isolated-reviewer-batch-0062-slow-sql-20260831-v1'
    review_version = 'batch-0062.slow-sql-scenario.v1'
    review_path = out / 'isolated_review_result.json'
    write_json(review_path, {
        'schema_version': 'isolated_review.v1',
        'canonical_id': CID,
        'candidate_sha256': digest,
        'reviewed_at': DATE,
        'review_mode': 'source_first_isolated',
        'reviewer_id': reviewer_id,
        'review_version': review_version,
        'decision': 'pass',
        'revision_round': 1,
        'source_packet': [
            str(context_path),
            str(inventory_path),
            str(primary_path),
            str(candidate_path),
            'docs/refactor/09_answer_content_standard.md',
            'config/answer_quality.json',
        ],
        'forbidden_inputs_not_used': [
            str(out / 'writer_research.json'),
            'writer self score',
            'writer rationale',
            'writer expected decision',
        ],
        'scores': SCORES,
        'hard_failures': [],
        'unsupported_claims': [],
        'uncovered_source_variants': [],
        'findings': findings,
        'promotion_blockers': [PROMOTION_BLOCKER],
    })

    evidence_sources = [
        {
            'source_id': 'repository-source',
            'title': 'Batch 0062 frozen slow-SQL source context',
            'locator': str(context_path),
            'source_type': 'repository_source_record',
            'checked_at': DATE,
        },
        {
            'source_id': 'primary-source-packet',
            'title': 'Batch 0062 frozen slow-SQL MySQL 8.4 primary-source research packet',
            'locator': str(primary_path),
            'source_type': 'repository_structured_source',
            'checked_at': DATE,
        },
    ]
    for src in primary.get('sources', []):
        evidence_sources.append({
            'source_id': src['source_id'],
            'title': src['title'],
            'locator': src['locator'],
            'source_type': src['source_type'],
            'checked_at': src['checked_at'],
        })
    evidence_sources.append({
        'source_id': 'isolated-review',
        'title': 'Fresh Batch 0062 slow-SQL isolated source-first review',
        'locator': str(review_path),
        'source_type': 'repository_structured_source',
        'checked_at': DATE,
    })

    evidence_path = ROOT / f'review/evidence/{CID}.json'
    claims = [
        {
            'claim_id': 'source-boundary-and-version',
            'text': 'The frozen source asks how to find and optimize slow SQL and which commands/tools to use but supplies no schema, scale, QPS, threshold or personal incident; the candidate uses MySQL 8.4 as the explicit command/documentation boundary and does not invent missing production facts.',
            'source_ids': ['repository-source', 'primary-source-packet', 'isolated-review'],
            'answer_locations': ['核心结论', '1 分钟版', '3 分钟版', '关键细节', '项目经验版'],
        },
        {
            'claim_id': 'discover-and-prioritize-by-workload',
            'text': 'Slow-query logging plus Performance Schema digest aggregation and sys.statement_analysis provide complementary statement-level and normalized workload-level evidence, allowing high-impact SQL families to be prioritized using execution frequency, latency, rows/scans/locks and a representative sample instead of one-off anecdotes.',
            'source_ids': ['mysql-84-slow-query-log', 'mysql-84-statement-digests', 'mysql-84-sys-statement-analysis', 'isolated-review'],
            'answer_locations': ['核心结论', '1 分钟版', '3 分钟版', '关键细节', '原理机制', '常见追问'],
        },
        {
            'claim_id': 'explain-estimate-versus-actual',
            'text': 'EXPLAIN provides optimizer plan information, while MySQL 8.4 EXPLAIN ANALYZE executes the statement and reports actual iterator timing, rows and loops alongside estimates; the candidate uses that distinction to diagnose estimate/row-amplification mismatch and to bound production execution risk.',
            'source_ids': ['mysql-84-explain', 'isolated-review'],
            'answer_locations': ['核心结论', '1 分钟版', '3 分钟版', '关键细节', '常见追问', '易错点'],
        },
        {
            'claim_id': 'optimizer-trace-deep-diagnosis',
            'text': 'For cases where the selected plan is visible but the optimizer choice still needs explanation, optimizer_trace can be enabled for the current MySQL 8.4 session, the statement executed, INFORMATION_SCHEMA.OPTIMIZER_TRACE inspected and tracing disabled afterward.',
            'source_ids': ['mysql-84-optimizer-trace', 'isolated-review'],
            'answer_locations': ['3 分钟版', '关键细节', '常见追问', '易错点'],
        },
        {
            'claim_id': 'root-cause-remediation-tradeoffs',
            'text': 'Indexing is one remediation path, not a universal answer: unnecessary indexes consume storage and add insert/update/delete maintenance work, so query rewrite, reduced access, data-model changes, cache or precomputation must be compared by root cause and by consistency/freshness/operational cost.',
            'source_ids': ['mysql-84-index-optimization', 'primary-source-packet', 'isolated-review'],
            'answer_locations': ['1 分钟版', '3 分钟版', '关键细节', '原理机制', '常见追问', '易错点'],
        },
        {
            'claim_id': 'verification-rollout-and-overload-boundary',
            'text': 'A slow-SQL fix is complete only after representative before/after workload verification and controlled rollout: tail latency, rows examined/returned, lock behavior and CPU/IO are compared, index write/storage cost and cache consistency are included, retries are not used to amplify overload, and rollback plus digest regression monitoring remain available.',
            'source_ids': ['mysql-84-statement-digests', 'mysql-84-sys-statement-analysis', 'mysql-84-explain', 'mysql-84-index-optimization', 'isolated-review'],
            'answer_locations': ['1 分钟版', '3 分钟版', '关键细节', '原理机制', '项目经验版', '常见追问', '易错点'],
        },
    ]
    write_json(evidence_path, {
        'schema_version': 'answer_evidence.v1',
        'canonical_id': CID,
        'candidate_sha256': digest,
        'checked_at': DATE,
        'writer': {
            'writer_id': 'content-batch-0062-slow-sql-writer',
            'writer_version': 'xhs-answer-curator.v1',
        },
        'sources': evidence_sources,
        'claims': claims,
        'source_question_coverage': [{
            'question_id': QID,
            'covered': True,
            'answer_locations': ['核心结论', '1 分钟版', '3 分钟版', '关键细节', '原理机制', '常见追问'],
        }],
        'source_occurrence_count': 1,
        'review_state': 'independent_source_first_review_passed',
        'review': {
            'reviewer_id': reviewer_id,
            'review_version': review_version,
            'independent': True,
            'decision': 'pass',
            'revision_round': 1,
            'scores': SCORES,
            'hard_failures': [],
            'unsupported_claims': [],
            'uncovered_source_variants': [],
            'findings': findings,
        },
        'promotion_blocker': PROMOTION_BLOCKER,
    })

    task_path = ROOT / 'tasks/answer-batches/TASK-20260711-0313-answer-batch-0062.md'
    task = task_path.read_text(encoding='utf-8')
    review_line = f'- [x] `{CID}` source-first isolated review PASS: candidate digest `{digest}`; the single frozen slow-SQL source remains source-exact, MySQL 8.4 primary documentation supports slow-log/digest/sys discovery plus EXPLAIN/EXPLAIN ANALYZE and optimizer_trace boundaries, and the candidate closes diagnosis through root-cause-specific remediation, before/after verification, canary/rollback and overload/consistency tradeoffs without fabricated project metrics. Formal promotion remains blocked by repository human-approval/real-review policy.'
    if review_line not in task:
        writer_prefix = f'- [x] `{CID}` writer stage complete:'
        lines = task.splitlines()
        idx = next((i for i, line in enumerate(lines) if line.startswith(writer_prefix)), None)
        if idx is None:
            raise SystemExit(f'{CID}: writer progress line missing')
        lines.insert(idx + 1, review_line)
        task_path.write_text('\n'.join(lines) + '\n', encoding='utf-8')

    print(f'PASS review {CID} digest={digest} score={sum(SCORES.values())} evidence={evidence_path}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
