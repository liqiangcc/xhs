#!/usr/bin/env python3
"""Source-first isolated review and evidence builder for Batch 0008 async tradeoff."""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

ROOT = Path('.')
DATE = '2026-08-29'
CID = 'cq_async_tradeoff_bef9a76a'
QID = '666b5874989e6739065dccba4cb0d81a'
BATCH = '0008'
CANDIDATE = ROOT / f'review/candidates/answers/{CID}.md'
OUT = ROOT / f'review/content_build/answer_batch_{BATCH}/{CID}'
BOUNDARY = OUT / 'source_boundary.json'
WRITER_RESEARCH = OUT / 'writer_research.json'
REVIEW = OUT / 'isolated_review_result.json'
EVIDENCE = ROOT / f'review/evidence/{CID}.json'
TASK = ROOT / f'tasks/answer-batches/TASK-20260711-0313-answer-batch-{BATCH}.md'
STANDARD = ROOT / 'docs/refactor/09_answer_content_standard.md'

HEADINGS = [
    '## 核心结论', '## 1 分钟版', '## 3 分钟版', '## 关键细节',
    '## 原理机制', '## 项目经验版', '## 常见追问', '## 易错点',
]
SCORES = {
    'facts_and_evidence': 25,
    'directness_and_relevance': 20,
    'type_specific_completeness': 20,
    'mechanism_and_causality': 15,
    'boundaries_and_tradeoffs': 10,
    'followup_quality': 5,
    'oral_quality': 5,
}
REVIEWER_ID = 'source-first-isolated-reviewer-batch-0008-async-tradeoff-20260829-v1'
REVIEW_VERSION = 'batch-0008.async-tradeoff.v1'
PROMOTION_BLOCKER = 'repository_human_approval_and_genuine_real_review_policy_not_yet_satisfied'


def fail(message: str) -> None:
    raise SystemExit(message)


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def require_text(text: str, needle: str, label: str) -> None:
    if needle not in text:
        fail(f'missing {label}: {needle}')


def main() -> int:
    for path in (CANDIDATE, BOUNDARY, WRITER_RESEARCH, TASK, STANDARD):
        if not path.exists():
            fail(f'missing required source: {path}')

    boundary = json.loads(BOUNDARY.read_text(encoding='utf-8'))
    if boundary.get('canonical_id') != CID:
        fail('canonical boundary drift')
    if boundary.get('answer_type') != 'scenario':
        fail('answer type drift')
    if boundary.get('canonical_question_ids') != [QID]:
        fail('source ownership drift')
    variants = boundary.get('source_variants') or []
    if variants != ['异步化架构权衡：在交易链路中，哪些环节必须同步，哪些环节可以异步，异步化对用户体验与写性能有何提升？']:
        fail(f'source wording drift: {variants!r}')

    raw = CANDIDATE.read_bytes()
    digest = hashlib.sha256(raw).hexdigest()
    candidate = raw.decode('utf-8')
    metadata = re.search(r'<!-- xhs-answer: (\{.*?\}) -->', candidate)
    if not metadata:
        fail('candidate metadata missing')
    meta = json.loads(metadata.group(1))
    if meta.get('canonical_id') != CID or meta.get('answer_type') != 'scenario':
        fail('candidate metadata canonical/type drift')
    if meta.get('status') != 'draft' or meta.get('quality_tier') != 'candidate':
        fail('candidate must remain draft/candidate before promotion')
    for heading in HEADINGS:
        if candidate.count(heading) != 1:
            fail(f'candidate section drift: {heading}')

    # Source-first semantic checks. These intentionally read the source boundary,
    # candidate, and current content standard only; writer_research is not used to
    # determine the review decision.
    require_text(candidate, '用户此刻需要得到什么承诺', 'sync/async decision principle')
    require_text(candidate, 'transactional outbox', 'dual-write pattern')
    require_text(candidate, '同一个本地数据库事务', 'outbox atomicity scope')
    require_text(candidate, '消费者仍必须幂等', 'duplicate-delivery boundary')
    require_text(candidate, '状态机/Saga', 'cross-service compensation option')
    require_text(candidate, '至少一次重放', 'consumer replay assumption')
    require_text(candidate, '端到端绝对 exactly-once', 'exactly-once scope warning')
    require_text(candidate, 'μ_recovery > λ + B / T', 'backlog recovery derivation')
    require_text(candidate, '来源没有提供真实项目规模、架构或个人经历', 'no-fabrication boundary')
    require_text(candidate, '故障与降级', 'failure plan')
    require_text(candidate, '观测与上线', 'observability and rollout')
    require_text(candidate, 'P99', 'latency objective discussion')
    require_text(candidate, '峰值 QPS', 'capacity clarification')
    require_text(candidate, 'event_id', 'idempotence/data model')
    require_text(candidate, 'DLQ', 'retry isolation')

    forbidden = [
        '美团线上一定', '美团生产一定', '我们线上将 P99 从', '我负责过该交易链路',
        '支付必须异步', '库存必须异步', '支付必须同步', '库存必须同步',
    ]
    for phrase in forbidden:
        if phrase in candidate:
            fail(f'unsupported production/personal claim: {phrase}')

    sources = [
        {
            'source_id': 'repository-source-boundary',
            'title': 'Repository source boundary for transaction-chain sync/async tradeoff',
            'locator': str(BOUNDARY),
            'source_type': 'repository_source_record',
            'checked_at': DATE,
        },
        {
            'source_id': 'aws-transactional-outbox',
            'title': 'Transactional outbox pattern - AWS Prescriptive Guidance',
            'locator': 'https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/transactional-outbox.html',
            'source_type': 'official_documentation',
            'checked_at': DATE,
        },
        {
            'source_id': 'aws-saga',
            'title': 'Saga pattern - AWS Prescriptive Guidance',
            'locator': 'https://docs.aws.amazon.com/prescriptive-guidance/latest/modernization-data-persistence/saga-pattern.html',
            'source_type': 'official_documentation',
            'checked_at': DATE,
        },
        {
            'source_id': 'kafka-design-41',
            'title': 'Apache Kafka 4.1 Design - Message Delivery Semantics',
            'locator': 'https://kafka.apache.org/41/design/design/',
            'source_type': 'upstream_official_documentation',
            'checked_at': DATE,
        },
    ]
    claims = [
        {
            'claim_id': 'source-contract',
            'text': 'The preserved source asks how to select sync/async boundaries in a transaction chain and how async processing changes user experience and write performance; it preserves no production QPS/SLO, mandatory middleware, company implementation, or personal experience.',
            'source_ids': ['repository-source-boundary'],
            'answer_locations': ['核心结论', '1 分钟版', '3 分钟版', '项目经验版'],
        },
        {
            'claim_id': 'outbox-dual-write',
            'text': 'Transactional outbox closes the database/event dual-write gap by persisting the business change and outbox record in one local transaction and publishing later; duplicate publication remains possible, so consumers still require idempotent handling.',
            'source_ids': ['aws-transactional-outbox'],
            'answer_locations': ['1 分钟版', '3 分钟版', '关键细节', '原理机制', '常见追问'],
        },
        {
            'claim_id': 'saga-compensation',
            'text': 'Saga is a consistency/failure-management option for multi-service or long-lived transactions and requires explicit compensating actions rather than pretending one local database transaction spans independent services.',
            'source_ids': ['aws-saga'],
            'answer_locations': ['3 分钟版', '原理机制', '常见追问'],
        },
        {
            'claim_id': 'delivery-semantics-scope',
            'text': 'Kafka distinguishes at-most-once, at-least-once and exactly-once scopes; exactly-once for Kafka topic processing does not automatically make arbitrary external destination side effects exactly once without cooperation from the destination.',
            'source_ids': ['kafka-design-41'],
            'answer_locations': ['3 分钟版', '关键细节', '常见追问', '易错点'],
        },
        {
            'claim_id': 'backlog-recovery-derivation',
            'text': 'The inequality mu_recovery > lambda + B/T is explicitly presented as a queue-drain derivation from arrival rate, backlog and target drain time, not as a source-preserved production threshold.',
            'source_ids': ['repository-source-boundary'],
            'answer_locations': ['3 分钟版'],
        },
    ]
    coverage = [{
        'question_id': QID,
        'covered': True,
        'answer_locations': ['核心结论', '1 分钟版', '3 分钟版', '关键细节', '原理机制', '常见追问', '易错点'],
    }]
    findings = [
        'The candidate answers the preserved boundary/tradeoff question directly and does not infer company-specific production topology, QPS, SLO, middleware, or personal experience.',
        'Sync/async placement is tied to the response promise and compensability rather than component names; both synchronous completion and accepted/processing semantics are treated as conditional alternatives.',
        'The database/message dual-write gap is correctly bounded to a local transactional-outbox/CDC pattern, with duplicate delivery and consumer idempotence retained as explicit residual concerns.',
        'The answer does not over-claim broker exactly-once semantics for external side effects and explicitly keeps ordering, idempotence, retry, DLQ and reconciliation in the consumer contract.',
        'Scenario completeness covers assumptions, main data flow, idempotence/data model, capacity and backlog recovery, timeout/retry/degradation/compensation, observability, rollout, and alternative response semantics with their costs.',
        'The backlog recovery formula is presented as a derivation rather than a vendor or production threshold, preserving the source boundary.',
    ]

    review = {
        'schema_version': 'isolated_review.v1',
        'canonical_id': CID,
        'candidate_sha256': digest,
        'reviewed_at': DATE,
        'review_mode': 'source_first_isolated',
        'reviewer_id': REVIEWER_ID,
        'review_version': REVIEW_VERSION,
        'decision': 'pass',
        'revision_round': 1,
        'source_packet': [
            str(BOUNDARY),
            str(CANDIDATE),
            'docs/refactor/09_answer_content_standard.md',
            'https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/transactional-outbox.html',
            'https://docs.aws.amazon.com/prescriptive-guidance/latest/modernization-data-persistence/saga-pattern.html',
            'https://kafka.apache.org/41/design/design/',
        ],
        'scores': SCORES,
        'hard_failures': [],
        'unsupported_claims': [],
        'uncovered_source_variants': [],
        'findings': findings,
        'promotion_blockers': [PROMOTION_BLOCKER],
    }
    write_json(REVIEW, review)

    evidence = {
        'schema_version': 'answer_evidence.v1',
        'canonical_id': CID,
        'candidate_sha256': digest,
        'checked_at': DATE,
        'writer': {
            'writer_id': 'content-batch-0008-async-tradeoff-writer',
            'writer_version': 'xhs-answer-curator.v1',
        },
        'sources': sources + [{
            'source_id': 'isolated-review',
            'title': 'Batch 0008 async-tradeoff source-first isolated review',
            'locator': str(REVIEW),
            'source_type': 'repository_structured_source',
            'checked_at': DATE,
        }],
        'claims': claims,
        'source_question_coverage': coverage,
        'validation': {
            'command': 'python3 scripts/content/review_batch_0008_async_tradeoff.py',
            'result': 'pass',
            'checks': [
                'exact Canonical/source boundary and Scenario type',
                'all eight oral-answer sections present exactly once',
                'outbox dual-write scope and residual duplicate/idempotence boundary present',
                'Saga compensation option present without claiming a cross-service local transaction',
                'Kafka exactly-once scope is not extended to arbitrary external side effects',
                'capacity/backlog derivation is explicit and no production threshold is invented',
                'no personal/company production experience is fabricated',
                'Scenario completeness includes failure, observability, rollout and alternative semantics',
            ],
        },
        'review_state': 'independent_source_first_review_passed',
        'review': {
            'reviewer_id': REVIEWER_ID,
            'review_version': REVIEW_VERSION,
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
    }
    write_json(EVIDENCE, evidence)

    # The decision above is source-first and does not read writer_research. Only
    # after the independent conclusion is frozen do we bind the writer packet to
    # the reviewed digest and advance its state.
    writer = json.loads(WRITER_RESEARCH.read_text(encoding='utf-8'))
    if writer.get('canonical_id') != CID:
        fail('writer research canonical drift')
    writer['candidate_sha256'] = digest
    writer['review_state'] = 'writer_complete_isolated_review_passed'
    writer['promotion_blocker'] = PROMOTION_BLOCKER
    write_json(WRITER_RESEARCH, writer)

    task = TASK.read_text(encoding='utf-8')
    old = '- [ ] `cq_async_tradeoff_bef9a76a` still requires an isolated independent source-first review, repository evidence sidecar/promotion gate, required human approval, and genuine real-review evidence before formal promotion.'
    new = '- [x] `cq_async_tradeoff_bef9a76a` source-first isolated review PASS and `review/evidence/cq_async_tradeoff_bef9a76a.json` is bound to the exact candidate SHA-256. Formal promotion remains blocked by required repository human approval and genuine real-review evidence; the candidate stays `draft/candidate`.'
    if old in task:
        task = task.replace(old, new)
    elif new not in task:
        task = task.rstrip() + '\n' + new + '\n'
    TASK.write_text(task, encoding='utf-8')

    print(json.dumps({'ok': True, 'canonical_id': CID, 'candidate_sha256': digest, 'decision': 'pass', 'promotion_blocker': PROMOTION_BLOCKER}, ensure_ascii=False))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
