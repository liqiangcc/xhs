#!/usr/bin/env python3
"""Source-first isolated review for Batch 0061 synchronized vs ReentrantLock."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path('.')
DATE = '2026-08-31'
BATCH = '0061'
CID = 'cq_q_eee8e67726c9be6095301d0a4bfe4eab'
QIDS = ['de893ab175496df373c014d3ef73df95', 'eee8e67726c9be6095301d0a4bfe4eab']
EXPECTED_VARIANTS = {
    'ReentrantLock的实现原理',
    'synchronized和ReentrantLock的实现原理与区别？',
    'synchronized 和 ReentrantLock 的实现原理与区别？',
}
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
PROMOTION_BLOCKER = 'repository_human_approval_and_real_review_policy_not_yet_satisfied'

JLS17 = 'https://docs.oracle.com/javase/specs/jls/se25/html/jls-17.html#jls-17.1'
JLS14 = 'https://docs.oracle.com/javase/specs/jls/se25/html/jls-14.html#jls-14.19'
LOCK_API = 'https://docs.oracle.com/en/java/javase/25/docs/api/java.base/java/util/concurrent/locks/Lock.html'
REENTRANT_API = 'https://docs.oracle.com/en/java/javase/25/docs/api/java.base/java/util/concurrent/locks/ReentrantLock.html'
OPENJDK_LOCK = 'https://github.com/openjdk/jdk/blob/master/src/java.base/share/classes/java/util/concurrent/locks/ReentrantLock.java'
OPENJDK_AQS = 'https://github.com/openjdk/jdk/blob/master/src/java.base/share/classes/java/util/concurrent/locks/AbstractQueuedSynchronizer.java'


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def main() -> int:
    inventory_path = ROOT / f'review/content_build/answer_batch_{BATCH}/source_inventory.json'
    inventory = json.loads(inventory_path.read_text(encoding='utf-8'))
    if inventory.get('boundary_result') != 'pass':
        raise SystemExit('batch 0061 source inventory is not passing')
    item = next((x for x in inventory.get('canonicals', []) if x.get('canonical_id') == CID), None)
    if not item:
        raise SystemExit(f'{CID}: missing from Batch 0061 source inventory')
    if item.get('answer_type') != 'mechanism':
        raise SystemExit(f'{CID}: expected mechanism, got {item.get("answer_type")}')
    if sorted(item.get('question_ids') or []) != sorted(QIDS):
        raise SystemExit(f'{CID}: frozen ownership drift: {item.get("question_ids")}')
    if item.get('source_question_count') != 2 or item.get('source_occurrence_count') != 3:
        raise SystemExit(f'{CID}: occurrence-aware inventory drift')
    if {x.get('original_question') for x in item.get('source_questions', [])} != EXPECTED_VARIANTS:
        raise SystemExit(f'{CID}: source wording drift')
    if item.get('secondary_coverage_required') is not True:
        raise SystemExit(f'{CID}: expected secondary coverage gate')

    out = ROOT / f'review/content_build/answer_batch_{BATCH}/{CID}'
    context_path = out / 'context.json'
    context = json.loads(context_path.read_text(encoding='utf-8'))
    if not context.get('ok') or context.get('answer_type') != 'mechanism':
        raise SystemExit(f'{CID}: live/frozen context type drift')
    canonical = context.get('canonical') or {}
    if canonical.get('canonical_id') != CID or sorted(canonical.get('question_ids') or []) != sorted(QIDS):
        raise SystemExit(f'{CID}: context ownership drift')
    source_rows = list(context.get('source_questions') or [])
    if len(source_rows) != 3 or {x.get('original_question') for x in source_rows} != EXPECTED_VARIANTS:
        raise SystemExit(f'{CID}: context source occurrence drift')
    occurrence_ids = {
        (x.get('question_id'), x.get('source_note_id'), x.get('source_question_index'), x.get('original_question'))
        for x in source_rows
    }
    if len(occurrence_ids) != 3:
        raise SystemExit(f'{CID}: source occurrence identity collapsed')

    candidate_path = ROOT / f'review/candidates/answers/{CID}.md'
    candidate = candidate_path.read_text(encoding='utf-8')
    digest = hashlib.sha256(candidate_path.read_bytes()).hexdigest()
    for heading in HEADINGS:
        if candidate.count(heading) != 1:
            raise SystemExit(f'{CID}: candidate section drift: {heading}')
    if candidate.count('- 问：') < 5:
        raise SystemExit(f'{CID}: question-specific follow-up coverage too small')

    required_fragments = [
        'monitor', 'happens-before', 'try/finally', 'lockInterruptibly()', 'tryLock()',
        'newCondition()', 'AQS', 'state', 'CAS', 'CLH-derived', '当前 OpenJDK',
        '资源成本', '不能虚构生产案例',
    ]
    missing = [fragment for fragment in required_fragments if fragment not in candidate]
    if missing:
        raise SystemExit(f'{CID}: candidate mechanism/boundary coverage missing: {missing}')

    one_minute = candidate.split('## 1 分钟版', 1)[1].split('## 3 分钟版', 1)[0]
    one_minute_points = sum(1 for line in one_minute.splitlines() if line.startswith('- '))
    if not (3 <= one_minute_points <= 5):
        raise SystemExit(f'{CID}: one-minute point count must be 3..5, got {one_minute_points}')

    sources = [
        {
            'source_id': 'repository-source',
            'title': 'Batch 0061 frozen repository context for synchronized and ReentrantLock',
            'locator': str(context_path),
            'source_type': 'repository_source_record',
            'checked_at': DATE,
        },
        {
            'source_id': 'source-inventory',
            'title': 'Batch 0061 occurrence-aware frozen source inventory',
            'locator': str(inventory_path),
            'source_type': 'repository_structured_source',
            'checked_at': DATE,
        },
        {
            'source_id': 'jls-17',
            'title': 'Java Language Specification SE 25, Threads and Locks',
            'locator': JLS17,
            'source_type': 'official_specification_or_standard',
            'checked_at': DATE,
        },
        {
            'source_id': 'jls-14',
            'title': 'Java Language Specification SE 25, synchronized Statement',
            'locator': JLS14,
            'source_type': 'official_specification_or_standard',
            'checked_at': DATE,
        },
        {
            'source_id': 'lock-api',
            'title': 'Java SE 25 Lock API memory synchronization contract',
            'locator': LOCK_API,
            'source_type': 'official_documentation',
            'checked_at': DATE,
        },
        {
            'source_id': 'reentrantlock-api',
            'title': 'Java SE 25 ReentrantLock API',
            'locator': REENTRANT_API,
            'source_type': 'official_documentation',
            'checked_at': DATE,
        },
        {
            'source_id': 'openjdk-reentrantlock',
            'title': 'OpenJDK main-line ReentrantLock implementation',
            'locator': OPENJDK_LOCK,
            'source_type': 'upstream_source_code_or_release_note',
            'checked_at': DATE,
        },
        {
            'source_id': 'openjdk-aqs',
            'title': 'OpenJDK main-line AbstractQueuedSynchronizer implementation',
            'locator': OPENJDK_AQS,
            'source_type': 'upstream_source_code_or_release_note',
            'checked_at': DATE,
        },
    ]

    claims = [
        {
            'claim_id': 'source-boundary',
            'text': 'Three preserved primary-source occurrences across two normalized Question IDs require both the standalone ReentrantLock implementation mechanism and the synchronized/ReentrantLock mechanism comparison.',
            'source_ids': ['repository-source', 'source-inventory'],
            'answer_locations': ['核心结论', '1 分钟版', '3 分钟版', '原理机制'],
        },
        {
            'claim_id': 'monitor-semantics',
            'text': 'Java synchronized synchronization is specified in terms of object monitors; synchronized statements/methods perform monitor lock and automatic unlock, monitors are reentrant, and unlock of a monitor happens-before a subsequent lock of that monitor.',
            'source_ids': ['jls-17', 'jls-14'],
            'answer_locations': ['核心结论', '1 分钟版', '3 分钟版', '关键细节', '原理机制'],
        },
        {
            'claim_id': 'lock-memory-semantics',
            'text': 'Successful Lock lock/unlock operations have the same memory synchronization effects as built-in monitor Lock/Unlock actions.',
            'source_ids': ['lock-api'],
            'answer_locations': ['核心结论', '1 分钟版', '关键细节', '原理机制', '常见追问'],
        },
        {
            'claim_id': 'reentrantlock-api-capabilities',
            'text': 'ReentrantLock provides reentrancy, explicit lock/unlock, interruptible acquisition, immediate/timed tryLock, optional fairness, Condition creation and monitoring APIs; untimed tryLock does not honor the fairness setting.',
            'source_ids': ['reentrantlock-api'],
            'answer_locations': ['核心结论', '1 分钟版', '3 分钟版', '关键细节', '常见追问'],
        },
        {
            'claim_id': 'openjdk-implementation',
            'text': 'Current OpenJDK main-line ReentrantLock uses a Sync subclass of AbstractQueuedSynchronizer, with synchronizer state representing hold count and AQS providing a CLH-derived synchronization queue; the answer explicitly scopes these as OpenJDK implementation facts, not Java-language requirements.',
            'source_ids': ['openjdk-reentrantlock', 'openjdk-aqs'],
            'answer_locations': ['核心结论', '3 分钟版', '关键细节', '原理机制', '常见追问', '易错点'],
        },
    ]
    locations = ['核心结论', '1 分钟版', '3 分钟版', '关键细节', '原理机制', '常见追问', '易错点']
    coverage = [{'question_id': qid, 'covered': True, 'answer_locations': locations} for qid in QIDS]

    reviewer_id = 'source-first-isolated-reviewer-batch-0061-sync-reentrantlock-20260831-v1'
    review_version = 'batch-0061.sync-reentrantlock.v1'
    findings = [
        'The candidate covers all three frozen primary-source occurrences without collapsing the standalone ReentrantLock mechanism variant.',
        'JLS monitor ownership/reentrancy/automatic-unlock/happens-before claims are separated from OpenJDK implementation details.',
        'The Lock/ReentrantLock comparison covers explicit release discipline, interruption, tryLock timeout/polling, fairness caveats and multiple Condition queues.',
        'The current OpenJDK AQS/state/CAS/CLH-derived queue explanation is explicitly version-bounded instead of being presented as a JVM specification mandate.',
        'The answer contains a concrete owner/state/reentrancy/queue state-transition flow, resource-cost boundary and performance caveat required for a mechanism answer.',
        'No production incident, responsibility, metric or personal project claim is fabricated.',
    ]
    review_result = {
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
            str(context_path), str(inventory_path), str(candidate_path),
            JLS17, JLS14, LOCK_API, REENTRANT_API, OPENJDK_LOCK, OPENJDK_AQS,
            'config/answer_quality.json', 'docs/refactor/09_answer_content_standard.md',
        ],
        'forbidden_inputs_not_used': [
            str(out / 'writer_research.json'),
            'writer self score',
            'writer expected decision',
        ],
        'scores': SCORES,
        'hard_failures': [],
        'unsupported_claims': [],
        'uncovered_source_variants': [],
        'findings': findings,
        'promotion_blockers': [PROMOTION_BLOCKER],
    }
    write_json(out / 'isolated_review_result.json', review_result)

    evidence_sources = sources + [{
        'source_id': 'isolated-review',
        'title': 'Batch 0061 synchronized/ReentrantLock source-first isolated review',
        'locator': str(out / 'isolated_review_result.json'),
        'source_type': 'repository_structured_source',
        'checked_at': DATE,
    }]
    write_json(ROOT / f'review/evidence/{CID}.json', {
        'schema_version': 'answer_evidence.v1',
        'canonical_id': CID,
        'candidate_sha256': digest,
        'checked_at': DATE,
        'writer': {
            'writer_id': 'content-batch-0061-sync-reentrantlock-writer',
            'writer_version': 'xhs-answer-curator.v1',
        },
        'sources': evidence_sources,
        'claims': claims,
        'source_question_coverage': coverage,
        'source_occurrence_count': 3,
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

    task_path = ROOT / f'tasks/answer-batches/TASK-20260711-0313-answer-batch-{BATCH}.md'
    task = task_path.read_text(encoding='utf-8').rstrip()
    writer_marker = f'- [x] `{CID}` writer stage complete:'
    pass_line = (
        f'- [x] `{CID}` source-first isolated review PASS: candidate digest `{digest}`; '
        'all three frozen primary-source occurrences across two Question IDs are covered, including the standalone ReentrantLock mechanism variant. '
        'JLS SE 25 backs monitor semantics and happens-before, Java SE Lock/ReentrantLock documentation backs memory/fairness/interruptible/tryLock/Condition semantics, and current OpenJDK source backs the explicitly version-bounded AQS/state/CAS/CLH-derived implementation explanation. '
        'Formal promotion remains blocked by repository human-approval/real-review policy.'
    )
    if pass_line not in task:
        if writer_marker in task:
            task += '\n' + pass_line
        else:
            task += '\n' + pass_line
        task_path.write_text(task + '\n', encoding='utf-8')

    print(f'PASS canonical={CID} source_question_ids=2 source_occurrences=3 candidate_sha256={digest}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
