#!/usr/bin/env python3
"""Freeze Batch 0053 repository source contexts before answer writing."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

ROOT = Path('.')
BATCH = '0053'
DATE = '2026-08-29'
CANONICALS = [
    'cq_q_e596a619cd124675cbe35a5a36c9acb2',
    'cq_q_e63e481809ed7fb71db27152107f821e',
    'cq_q_e6e5cff08ac25c3462fbbcfffe9a0f78',
    'cq_q_e8908b8b7c7de059394df439d1624a61',
    'cq_q_e8ce511f7de2564d49e3106ed54c7731',
    'cq_q_e96179b8accbba3099c34a7fcd2cf757',
    'cq_q_e96e830c897ca29052ba931638e8ff61',
    'cq_q_ea27d2a647ad7ed19a5fb6f9ab5b76d8',
    'cq_q_eaae17962ef4c12e3a382e102ff461c1',
    'cq_q_eaba609d7a28fdf408eb6f4924804982',
]


def run(*args: str) -> str:
    return subprocess.run(args, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, check=True).stdout


def main() -> int:
    out = ROOT / f'review/content_build/answer_batch_{BATCH}'
    out.mkdir(parents=True, exist_ok=True)
    rows = []
    seen_qids: set[str] = set()

    for cid in CANONICALS:
        ctx = json.loads(run('node', 'scripts/xhs.js', 'answer', 'context', '--canonical-id', cid, '--noWrite'))
        if not ctx.get('ok'):
            raise SystemExit(f'{cid}: context not ok')
        if ctx.get('canonical', {}).get('canonical_id') != cid:
            raise SystemExit(f'{cid}: canonical id drift')
        if ctx.get('answer_type') != 'coding':
            raise SystemExit(f"{cid}: answer type drift {ctx.get('answer_type')}")

        qids = ctx.get('canonical', {}).get('question_ids') or []
        if not qids:
            raise SystemExit(f'{cid}: no source questions')
        sources = ctx.get('source_questions') or []
        by_qid = {x.get('question_id'): x for x in sources}
        if set(qids) != set(by_qid):
            raise SystemExit(f'{cid}: source-question/context ownership mismatch')

        questions = []
        for qid in qids:
            if qid in seen_qids:
                raise SystemExit(f'{cid}: source question {qid} already owned by another batch canonical')
            seen_qids.add(qid)
            src = by_qid[qid]
            wording = src.get('original_question')
            if not isinstance(wording, str) or not wording.strip():
                raise SystemExit(f'{cid}/{qid}: empty source wording')
            if src.get('is_valid_for_library') is not True:
                raise SystemExit(f'{cid}/{qid}: source is not valid for library')
            questions.append({
                'question_id': qid,
                'original_question': wording,
                'is_valid_for_library': True,
            })

        cdir = out / cid
        cdir.mkdir(parents=True, exist_ok=True)
        (cdir / 'context.json').write_text(json.dumps(ctx, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
        rows.append({
            'canonical_id': cid,
            'answer_type': 'coding',
            'question_ids': qids,
            'source_questions': questions,
            'existing_candidate': (ROOT / f'review/candidates/answers/{cid}.md').exists(),
            'existing_evidence': (ROOT / f'review/evidence/{cid}.json').exists(),
        })

    inventory = {
        'schema_version': 'answer_batch_source_inventory.v1',
        'batch': BATCH,
        'checked_at': DATE,
        'canonical_count': len(CANONICALS),
        'source_question_count': len(seen_qids),
        'boundary_result': 'pass',
        'writer_rule': 'Writers must use these frozen repository contexts as the source boundary and must not reconstruct unpreserved external constraints from memory.',
        'canonicals': rows,
    }
    (out / 'source_inventory.json').write_text(json.dumps(inventory, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

    task = ROOT / f'tasks/answer-batches/TASK-20260711-0313-answer-batch-{BATCH}.md'
    text = task.read_text(encoding='utf-8')
    marker = '- [x] Batch 0053 repository source boundary frozen in `review/content_build/answer_batch_0053/source_inventory.json`; all 10 Canonicals resolve to valid Coding source contexts, with per-Canonical `context.json` snapshots. Candidate writing must remain source-bounded and independent review/promotion gates are still required.'
    if marker not in text:
        text = text.rstrip() + '\n\n## Source boundary\n\n' + marker + '\n'
    text = text.replace('- Status: `pending`', '- Status: `in_progress`', 1)
    task.write_text(text, encoding='utf-8')

    print(f'PASS batch={BATCH} canonicals={len(CANONICALS)} source_questions={len(seen_qids)}')
    for row in rows:
        source_text = ' | '.join(q['original_question'] for q in row['source_questions'])
        print(f"{row['canonical_id']}\t{source_text}")
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
