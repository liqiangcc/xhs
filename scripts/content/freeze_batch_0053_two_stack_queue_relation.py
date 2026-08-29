#!/usr/bin/env python3
"""Freeze source-first contexts for the Batch 0053 two-stack queue relation before deciding merge/split."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

ROOT = Path('.')
DATE = '2026-08-29'
BATCH = '0053'
TARGET_CID = 'cq_q_eaae17962ef4c12e3a382e102ff461c1'
TARGET_QID = 'eaae17962ef4c12e3a382e102ff461c1'
TARGET_EXPECTED = '编程题: 用两个栈模拟队列 (实现push、pop、count)'
ADJACENT_CID = 'cq_q_36ab1630843f456fa940c19962292fbe'


def run(*args: str) -> str:
    return subprocess.run(args, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, check=True).stdout


def main() -> int:
    out = ROOT / f'review/content_build/answer_batch_{BATCH}/two_stack_queue_relation'
    out.mkdir(parents=True, exist_ok=True)

    target = json.loads(run('node', 'scripts/xhs.js', 'answer', 'context', '--canonical-id', TARGET_CID, '--noWrite'))
    adjacent = json.loads(run('node', 'scripts/xhs.js', 'answer', 'context', '--canonical-id', ADJACENT_CID, '--noWrite'))

    if not target.get('ok') or target.get('canonical', {}).get('canonical_id') != TARGET_CID:
        raise SystemExit('target context drift')
    if target.get('canonical', {}).get('question_ids') != [TARGET_QID]:
        raise SystemExit(f"target ownership drift: {target.get('canonical', {}).get('question_ids')}")
    src = next((x for x in target.get('source_questions', []) if x.get('question_id') == TARGET_QID), None)
    if not src or src.get('original_question') != TARGET_EXPECTED or src.get('is_valid_for_library') is not True:
        raise SystemExit('target source wording/validity drift')

    if not adjacent.get('ok') or adjacent.get('canonical', {}).get('canonical_id') != ADJACENT_CID:
        raise SystemExit('adjacent context missing/drifted')
    adjacent_qids = adjacent.get('canonical', {}).get('question_ids') or []
    if not adjacent_qids:
        raise SystemExit('adjacent canonical has no source questions')
    adjacent_sources = adjacent.get('source_questions') or []
    if set(adjacent_qids) != {x.get('question_id') for x in adjacent_sources}:
        raise SystemExit('adjacent context ownership mismatch')
    for item in adjacent_sources:
        if item.get('is_valid_for_library') is not True or not str(item.get('original_question') or '').strip():
            raise SystemExit('adjacent source wording/validity incomplete')

    (out / 'target_context.json').write_text(json.dumps(target, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    (out / 'adjacent_context.json').write_text(json.dumps(adjacent, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

    packet = {
        'schema_version': 'canonical_relation_source_packet.v1',
        'checked_at': DATE,
        'batch': BATCH,
        'review_state': 'source_packet_frozen_relation_decision_pending',
        'rule': 'No relation decision is made from title/entity similarity alone. Review the exact preserved source questions before deciding same/related/distinct.',
        'target': {
            'canonical_id': TARGET_CID,
            'canonical_title': target.get('canonical', {}).get('canonical_title'),
            'answer_type': target.get('answer_type'),
            'questions': [
                {'question_id': x.get('question_id'), 'original_question': x.get('original_question')}
                for x in target.get('source_questions', [])
            ],
        },
        'adjacent': {
            'canonical_id': ADJACENT_CID,
            'canonical_title': adjacent.get('canonical', {}).get('canonical_title'),
            'answer_type': adjacent.get('answer_type'),
            'questions': [
                {'question_id': x.get('question_id'), 'original_question': x.get('original_question')}
                for x in adjacent_sources
            ],
        },
    }
    (out / 'source_relation_packet.json').write_text(json.dumps(packet, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

    md = [
        '# Batch 0053 Two-Stack Queue Source Relation Packet',
        '',
        'This packet freezes current repository source contexts before any same/related/distinct decision.',
        '',
        f'- Target Canonical: `{TARGET_CID}`',
        f'- Target source: `{TARGET_EXPECTED}`',
        f'- Adjacent Canonical: `{ADJACENT_CID}`',
        f"- Adjacent title: `{adjacent.get('canonical', {}).get('canonical_title')}`",
        '- Relation decision: `pending_source_first_review`',
        '',
        '## Adjacent preserved source questions',
        '',
    ]
    for item in adjacent_sources:
        md.append(f"- `{item.get('question_id')}` — {item.get('original_question')}")
    md += [
        '',
        '## Rule',
        '',
        'Do not create a second formal answer or merge Canonicals merely from title/taxonomy similarity. The next bounded slice must compare these exact source contracts first.',
        '',
    ]
    (out / 'source_relation_packet.md').write_text('\n'.join(md), encoding='utf-8')

    task = ROOT / f'tasks/answer-batches/TASK-20260711-0313-answer-batch-{BATCH}.md'
    text = task.read_text(encoding='utf-8')
    note = '- [x] `cq_q_eaae17962ef4c12e3a382e102ff461c1` two-stack-queue normalization safeguard: exact repository contexts for this Canonical and adjacent `cq_q_36ab1630843f456fa940c19962292fbe` are frozen in `review/content_build/answer_batch_0053/two_stack_queue_relation/`; relation remains `pending_source_first_review`, so no duplicate answer or merge is allowed until the next source-first relation slice.'
    if note not in text:
        text = text.rstrip() + '\n' + note + '\n'
    task.write_text(text, encoding='utf-8')

    print(json.dumps(packet, ensure_ascii=False, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
