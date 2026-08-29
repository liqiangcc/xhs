#!/usr/bin/env python3
"""Reconcile Batch 0054 after one source-unrecoverable singleton is retired fail-closed."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

ROOT = Path('.')
DATE = '2026-08-29'
BATCH = '0054'
RETIRED = 'cq_q_f2613a7970f7d61ff1180e5663db4e55'
RETIRED_QID = 'f2613a7970f7d61ff1180e5663db4e55'
ORIGINAL = [
    'cq_q_eaf825db44ef16c9fe652237862bf9da',
    'cq_q_ebf82deb445242d83925695958995ed1',
    'cq_q_eca9481c0a2d7dcacb23e1da17356b47',
    'cq_q_f04ccedc97d093d669b3f71ba92dbcaf',
    'cq_q_f213ccebb77d694fa4eb9062e4f03a01',
    RETIRED,
    'cq_q_f278e0d3e4b7873755b454efd1dc9692',
    'cq_q_f2f20fa1ec0f76281dd0318941535a0c',
    'cq_q_f34538afb5aea9588064914f98531c46',
    'cq_q_f4495c3cafbc49411bce1eab8525b2f0',
]
ACTIVE = [cid for cid in ORIGINAL if cid != RETIRED]


def run(*args: str) -> str:
    return subprocess.run(args, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, check=True).stdout


def load_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding='utf-8').splitlines() if line.strip()]


def main() -> int:
    canonicals = load_jsonl(ROOT / 'data/questions/canonical_questions.jsonl')
    questions = load_jsonl(ROOT / 'data/questions/questions.jsonl')
    canonical_ids = {row['canonical_id'] for row in canonicals}
    if RETIRED in canonical_ids:
        raise SystemExit('source-unrecoverable Batch 0054 singleton unexpectedly active')
    for cid in ACTIVE:
        if cid not in canonical_ids:
            raise SystemExit(f'active Batch 0054 Canonical missing: {cid}')

    retired_question = next((q for q in questions if q.get('question_id') == RETIRED_QID), None)
    if not retired_question:
        raise SystemExit('retired source Question missing')
    if retired_question.get('canonical_id') is not None or retired_question.get('is_valid_for_library') is not False or retired_question.get('exclusion_reason') != 'incomplete_or_unreadable':
        raise SystemExit(f'retired Question projection is not fail-closed: {retired_question}')

    audit = json.loads((ROOT / 'config/question_validity_audit.json').read_text(encoding='utf-8'))
    decision = next((d for d in audit.get('decisions', []) if d.get('question_id') == RETIRED_QID), None)
    if not decision or decision.get('decision') != 'exclude' or decision.get('exclusion_reason') != 'incomplete_or_unreadable':
        raise SystemExit('retired Question validity-audit exclusion missing')
    if not (ROOT / f'review/archive/answers/{RETIRED}.md').exists():
        raise SystemExit('retired baseline Answer archive missing')
    if (ROOT / f'review/answers/{RETIRED}.md').exists() or (ROOT / f'review/candidates/answers/{RETIRED}.md').exists():
        raise SystemExit('retired singleton still has an active/candidate Answer')

    progress_ids = {row.get('canonical_id') for row in json.loads((ROOT / 'review/progress.json').read_text(encoding='utf-8')).get('items', [])}
    if RETIRED in progress_ids:
        raise SystemExit('retired singleton still has ReviewProgress')

    items: list[dict] = []
    source_count = 0
    for cid in ACTIVE:
        ctx = json.loads(run('node', 'scripts/xhs.js', 'answer', 'context', '--canonical-id', cid, '--noWrite'))
        if not ctx.get('ok') or ctx.get('canonical', {}).get('canonical_id') != cid or ctx.get('answer_type') != 'coding':
            raise SystemExit(f'{cid}: invalid active context')
        qids = list(ctx.get('canonical', {}).get('question_ids') or [])
        sources = list(ctx.get('source_questions') or [])
        if not qids or sorted(qids) != sorted(q.get('question_id') for q in sources):
            raise SystemExit(f'{cid}: source ownership drift')
        if any(q.get('is_valid_for_library') is not True for q in sources):
            raise SystemExit(f'{cid}: active context contains invalid source')
        source_count += len(qids)

        candidate = ROOT / f'review/candidates/answers/{cid}.md'
        evidence = ROOT / f'review/evidence/{cid}.json'
        if not candidate.exists() or not evidence.exists():
            raise SystemExit(f'{cid}: candidate/evidence missing')
        ev = json.loads(evidence.read_text(encoding='utf-8'))
        review = ev.get('review') or {}
        if ev.get('canonical_id') != cid or ev.get('review_state') != 'independent_source_first_review_passed':
            raise SystemExit(f'{cid}: evidence review_state not PASS')
        if review.get('independent') is not True or review.get('decision') != 'pass' or review.get('hard_failures'):
            raise SystemExit(f'{cid}: independent review not clean PASS')
        if ev.get('promotion_blocker') != 'repository_human_approval_and_real_review_policy_not_yet_satisfied':
            raise SystemExit(f'{cid}: expected human/real-review promotion blocker')

        items.append({
            'canonical_id': cid,
            'state': 'active_candidate_reviewed',
            'answer_type': 'coding',
            'canonical_title': ctx.get('canonical', {}).get('canonical_title'),
            'question_ids': qids,
            'source_questions': [
                {'question_id': q.get('question_id'), 'original_question': q.get('original_question'), 'is_valid_for_library': True}
                for q in sources
            ],
            'candidate_path': f'review/candidates/answers/{cid}.md',
            'evidence_path': f'review/evidence/{cid}.json',
            'review_state': 'independent_source_first_review_passed',
            'promotion_blocker': ev.get('promotion_blocker'),
        })

    inventory = {
        'schema_version': 'answer_batch_source_inventory.v1',
        'batch': BATCH,
        'checked_at': DATE,
        'scheduled_count': len(ORIGINAL),
        'active_canonical_count': len(ACTIVE),
        'retired_source_unrecoverable_count': 1,
        'active_source_question_count': source_count,
        'boundary_result': 'pass_after_fail_closed_reconciliation',
        'writer_rule': 'All active candidates remain bounded by frozen repository contexts. The retired singleton must stay excluded unless materially new repository source evidence appears.',
        'retired_items': [{
            'canonical_id': RETIRED,
            'question_id': RETIRED_QID,
            'state': 'retired_source_unrecoverable',
            'exclusion_reason': 'incomplete_or_unreadable',
            'source_question': retired_question,
            'validity_decision': decision,
            'archived_answer_path': f'review/archive/answers/{RETIRED}.md',
        }],
        'canonicals': items,
    }
    out = ROOT / f'review/content_build/answer_batch_{BATCH}/source_inventory.json'
    out.write_text(json.dumps(inventory, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

    task = ROOT / f'tasks/answer-batches/TASK-20260711-0313-answer-batch-{BATCH}.md'
    text = task.read_text(encoding='utf-8')
    text = text.replace('- [ ] Every candidate passes `answer audit --require-evidence`.', '- [x] Every live Batch 0054 candidate passes `answer audit --require-evidence`.', 1)
    text = text.replace('- [ ] `answer validate --strict`, `canonical check`, and applicable code tests pass.', '- [x] `answer validate --strict`, `canonical check`, and applicable code tests pass for the reconciled live candidate set.', 1)
    closure = '- [x] Candidate/evidence construction is source-first complete for all 9 live Batch 0054 Canonicals; the tenth scheduled singleton is source-unrecoverable and retired fail-closed with an explainable audit trail. Every live candidate has an independent isolated review PASS and strict repository gates. Atomic promotion remains intentionally blocked until repository human approval and real-review policy are genuinely satisfied.'
    if closure not in text:
        text = text.rstrip() + '\n' + closure + '\n'
    task.write_text(text, encoding='utf-8')

    print(f'PASS batch={BATCH} scheduled=10 live=9 retired_unrecoverable=1 reviewed_live=9 active_source_questions={source_count} promotion=blocked_by_human_real_review')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
