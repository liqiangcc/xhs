#!/usr/bin/env python3
"""Freeze live source-first inventory for answer Batch 0051 and start the bounded task."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

ROOT = Path('.')
DATE = '2026-08-29'
BATCH = '0051'
IDS = [
    'cq_q_d844028ab6d4d5a63633365fcbc2f8cf',
    'cq_q_d8b3faa942da8d28e12fdfba2f4b8484',
    'cq_q_d93cde9e42e0a0b9afc1cdaf23fecf4c',
    'cq_q_d9617ce6ae5f4ede30ddabf9bd41f2c1',
    'cq_q_daa47706c03d0fd5463d00a57b8760ac',
    'cq_q_dbf0ec3aa331be76bfefa26a39750ce7',
    'cq_q_dbf9d916d20b5087fd78e10563bd8091',
    'cq_q_dc192e205c8fbcf5673927a9d9382f41',
    'cq_q_dca65995f5b060544336e01733cfd30d',
    'cq_q_de135a9fa2470b236d45bad96e81b6de',
]


def load_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding='utf-8').splitlines() if line.strip()]


def run_context(cid: str) -> dict:
    r = subprocess.run(
        ['node', 'scripts/xhs.js', 'answer', 'context', '--canonical-id', cid, '--noWrite'],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=True,
    )
    return json.loads(r.stdout)


def main() -> int:
    if len(IDS) != 10 or len(set(IDS)) != 10:
        raise SystemExit('Batch 0051 schedule cardinality drift')
    canonicals = load_jsonl(ROOT / 'data/questions/canonical_questions.jsonl')
    questions = load_jsonl(ROOT / 'data/questions/questions.jsonl')
    canonical_ids = {x['canonical_id'] for x in canonicals}
    items: list[dict] = []
    allowed = {'coding', 'concept', 'mechanism', 'scenario', 'project', 'behavior'}

    for cid in IDS:
        if cid not in canonical_ids:
            qid = cid.removeprefix('cq_q_')
            q = next((x for x in questions if x.get('question_id') == qid), None)
            if q and q.get('is_valid_for_library') is True and q.get('canonical_id') == cid:
                raise SystemExit(f'{cid}: missing Canonical while active Question still owns it')
            items.append({
                'canonical_id': cid,
                'state': 'stale_task_entry_absent_from_canonical_ssot',
                'source_question': {
                    'question_id': q.get('question_id'),
                    'original_question': q.get('original_question'),
                    'is_valid_for_library': q.get('is_valid_for_library'),
                    'canonical_id': q.get('canonical_id'),
                    'invalid_reason': q.get('invalid_reason') or q.get('exclusion_reason'),
                } if q else None,
            })
            continue

        ctx = run_context(cid)
        if not ctx.get('ok') or ctx.get('canonical', {}).get('canonical_id') != cid:
            raise SystemExit(f'{cid}: invalid context')
        answer_type = ctx.get('answer_type')
        if answer_type not in allowed:
            raise SystemExit(f'{cid}: unsupported answer type {answer_type}')
        owned = list(ctx.get('canonical', {}).get('question_ids') or [])
        source_questions = list(ctx.get('source_questions') or [])
        source_ids = [q.get('question_id') for q in source_questions]
        if not source_questions:
            raise SystemExit(f'{cid}: no source Questions')
        if sorted(owned) != sorted(source_ids):
            raise SystemExit(f'{cid}: ownership/source mismatch')
        if any(q.get('is_valid_for_library') is not True for q in source_questions):
            raise SystemExit(f'{cid}: active context includes invalid source')
        items.append({
            'canonical_id': cid,
            'state': 'active',
            'answer_type': answer_type,
            'canonical_title': ctx.get('canonical', {}).get('canonical_title'),
            'question_ids': owned,
            'source_questions': source_questions,
            'active_answer_metadata': (ctx.get('answer') or {}).get('metadata') if isinstance(ctx.get('answer'), dict) else ctx.get('answer_metadata'),
        })

    active = [x for x in items if x['state'] == 'active']
    stale = [x for x in items if x['state'] != 'active']
    inventory = {
        'schema_version': 'answer_batch_source_inventory.v1',
        'batch': BATCH,
        'frozen_at': DATE,
        'scheduled_count': len(IDS),
        'active_canonical_count': len(active),
        'stale_scheduled_count': len(stale),
        'source_first': True,
        'note': 'Live-state-aware inventory. Stale scheduled IDs are not resurrected. Active entries freeze exact Question ownership and answer type before any drafting.',
        'items': items,
    }
    out = ROOT / f'review/content_build/answer_batch_{BATCH}/source_inventory.json'
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(inventory, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

    task = ROOT / f'tasks/answer-batches/TASK-20260711-0313-answer-batch-{BATCH}.md'
    text = task.read_text(encoding='utf-8')
    text = text.replace('- Status: `pending`', '- Status: `in_progress`', 1)
    text = text.replace('- Canonical count: `10`', f'- Scheduled canonical count: `10`; live active count after prior remediation: `{len(active)}`', 1)
    line = f'- [x] Live-state-aware source-first inventory frozen in `review/content_build/answer_batch_{BATCH}/source_inventory.json`: {len(active)} scheduled Canonicals remain active and {len(stale)} stale scheduled entries are preserved as explicit non-resurrected history. Active entries freeze exact source Questions and current answer types before drafting.'
    if '## Progress' not in text:
        text = text.rstrip() + '\n\n## Progress\n'
    if line not in text:
        text = text.rstrip() + '\n' + line + '\n'
    task.write_text(text, encoding='utf-8')

    print(f'PASS batch0051 source inventory scheduled={len(IDS)} active={len(active)} stale={len(stale)}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
