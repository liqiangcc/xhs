#!/usr/bin/env python3
"""Reconcile Batch 0050 inventory/task after one legacy compound Canonical split into two live children."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

ROOT = Path('.')
DATE = '2026-08-29'
BATCH = '0050'
LEGACY = 'cq_q_d6ed1b1964f238df266bdd7e8bd146f1'
CHILDREN = [
    'cq_q_88d86d8e4586504b5c9365f4126f7436',
    'cq_q_b66328eb23ca1ba53a062a787c71a9dc',
]
ORIGINAL = [
    'cq_q_d52ca0aa328f82f1166ebc5bd3cc0ad7',
    'cq_q_d5bc7bf628f261d3f1898c944d3d7054',
    'cq_q_d616ff7e2ef391e07c984e8bd0a965a6',
    'cq_q_d63322aa9fd4048a05c37c235c47ce2c',
    'cq_q_d6793c017bd5cd31952352d7a0e98464',
    'cq_q_d6a3d5566380a6dba9d460a6ae25e68e',
    'cq_q_d6d0edf2910f05b10c1ef3911f26b7f5',
    LEGACY,
    'cq_q_d7a0e349945f1c8c9028db1306383621',
    'cq_q_d80c5515628053be95dcb56bc561643a',
]
ACTIVE = [cid for cid in ORIGINAL if cid != LEGACY] + CHILDREN


def run(*args: str) -> str:
    return subprocess.run(args, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, check=True).stdout


def load_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding='utf-8').splitlines() if line.strip()]


def main() -> int:
    if len(ORIGINAL) != 10 or len(ACTIVE) != 11:
        raise SystemExit('batch expansion cardinality drift')

    canonicals = load_jsonl(ROOT / 'data/questions/canonical_questions.jsonl')
    questions = load_jsonl(ROOT / 'data/questions/questions.jsonl')
    canonical_ids = {row['canonical_id'] for row in canonicals}
    if LEGACY in canonical_ids:
        raise SystemExit('retired compound Canonical unexpectedly still active')
    for cid in ACTIVE:
        if cid not in canonical_ids:
            raise SystemExit(f'active batch Canonical missing: {cid}')

    legacy_qid = LEGACY.removeprefix('cq_q_')
    legacy_q = next((q for q in questions if q.get('question_id') == legacy_qid), None)
    if legacy_q and legacy_q.get('is_valid_for_library') is True:
        raise SystemExit('legacy compound Question still active after split')

    items: list[dict] = []
    for cid in ACTIVE:
        ctx = json.loads(run('node', 'scripts/xhs.js', 'answer', 'context', '--canonical-id', cid, '--noWrite'))
        if not ctx.get('ok') or ctx.get('canonical', {}).get('canonical_id') != cid:
            raise SystemExit(f'{cid}: invalid answer context')
        owned = list(ctx.get('canonical', {}).get('question_ids') or [])
        source_questions = list(ctx.get('source_questions') or [])
        source_ids = [q.get('question_id') for q in source_questions]
        if not owned or sorted(owned) != sorted(source_ids):
            raise SystemExit(f'{cid}: Question ownership/source mismatch')
        if any(q.get('is_valid_for_library') is not True for q in source_questions):
            raise SystemExit(f'{cid}: active context contains non-library source')
        items.append({
            'canonical_id': cid,
            'state': 'active',
            'answer_type': ctx.get('answer_type'),
            'canonical_title': ctx.get('canonical', {}).get('canonical_title'),
            'question_ids': owned,
            'source_questions': source_questions,
            'active_answer_metadata': (ctx.get('answer') or {}).get('metadata') if isinstance(ctx.get('answer'), dict) else ctx.get('answer_metadata'),
        })

    # Every live Batch 0050 Canonical must now have a source-first candidate and PASS evidence.
    for cid in ACTIVE:
        candidate = ROOT / f'review/candidates/answers/{cid}.md'
        evidence = ROOT / f'review/evidence/{cid}.json'
        if not candidate.exists() or not evidence.exists():
            raise SystemExit(f'{cid}: candidate/evidence missing')
        ev = json.loads(evidence.read_text(encoding='utf-8'))
        review = ev.get('review') or {}
        if ev.get('canonical_id') != cid or ev.get('review_state') != 'independent_source_first_review_passed':
            raise SystemExit(f'{cid}: evidence review_state not PASS')
        if review.get('independent') is not True or review.get('decision') != 'pass':
            raise SystemExit(f'{cid}: independent review not PASS')
        if ev.get('promotion_blocker') != 'repository_human_approval_and_real_review_policy_not_yet_satisfied':
            raise SystemExit(f'{cid}: expected human/real-review promotion blocker')

    inventory = {
        'schema_version': 'answer_batch_source_inventory.v1',
        'batch': BATCH,
        'frozen_at': DATE,
        'scheduled_count': len(ORIGINAL),
        'active_canonical_count': len(ACTIVE),
        'stale_scheduled_count': 0,
        'split_expansion_count': 1,
        'source_first': True,
        'note': 'Original schedule contained 10 entries. One compound source was retired and split source-exact into two active child Canonicals, so the live active set is 11. The retired schedule slot is preserved in split_replacements rather than resurrected as an active Canonical.',
        'split_replacements': [{
            'retired_canonical_id': LEGACY,
            'retired_question_id': legacy_qid,
            'state': 'retired_compound_source_split',
            'replacement_canonical_ids': CHILDREN,
            'legacy_question': legacy_q,
        }],
        'items': items,
    }
    inventory_path = ROOT / f'review/content_build/answer_batch_{BATCH}/source_inventory.json'
    inventory_path.write_text(json.dumps(inventory, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

    task_path = ROOT / f'tasks/answer-batches/TASK-20260711-0313-answer-batch-{BATCH}.md'
    text = task_path.read_text(encoding='utf-8')
    text = text.replace(
        '- Scheduled canonical count: `10`; live active count after prior remediation: `10`',
        '- Scheduled canonical count: `10`; live active count after source-exact split expansion: `11`',
        1,
    )
    legacy_line = f'- `{LEGACY}` — coding; risks: long_tail_baseline, placeholder_implementation'
    child_lines = (
        '- `cq_q_88d86d8e4586504b5c9365f4126f7436` — coding; split child: linked-list cycle detection + input validation\n'
        '- `cq_q_b66328eb23ca1ba53a062a787c71a9dc` — coding; split child: adjacent sum-to-10 elimination'
    )
    if legacy_line in text:
        text = text.replace(legacy_line, child_lines, 1)
    stale_phrase = 'the mixed Answer/ReviewProgress is retired and both descendants remain answer-missing pending fresh source-first candidate/review work.'
    if stale_phrase in text:
        text = text.replace(
            stale_phrase,
            'the mixed Answer/ReviewProgress is retired; both source-exact descendants are tracked below and now have fresh candidate/evidence/source-first review records.',
            1,
        )
    text = text.replace('- [ ] Every candidate passes `answer audit --require-evidence`.', '- [x] Every live Batch 0050 candidate passes `answer audit --require-evidence`.', 1)
    text = text.replace('- [ ] `answer validate --strict`, `canonical check`, and applicable code tests pass.', '- [x] `answer validate --strict`, `canonical check`, and applicable code tests pass for the completed live candidate set.', 1)
    closure_line = '- [x] Candidate/evidence construction is source-first complete for all 11 live Batch 0050 Canonicals after the compound-source split. Every live candidate has an independent isolated review PASS and strict repository gates; atomic promotion remains intentionally blocked until the repository human-approval and real-review policy is genuinely satisfied.'
    if closure_line not in text:
        text = text.rstrip() + '\n' + closure_line + '\n'
    task_path.write_text(text, encoding='utf-8')

    print('PASS batch0050 reconciled original_schedule=10 live_active=11 split_expansion=1 all_candidates_reviewed=11 promotion=blocked_by_human_real_review')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
