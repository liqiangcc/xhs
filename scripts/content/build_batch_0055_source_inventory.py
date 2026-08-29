#!/usr/bin/env python3
"""Reconcile and freeze Batch 0055 repository source contexts before answer writing.

Batch task files are historical scheduling records. Normalization can later merge or
retire a scheduled cq_q_<question-id>. This builder therefore treats the current
Question row + current Canonical graph as SSOT and records every stale assignment
instead of failing merely because the old Canonical ID disappeared.
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

ROOT = Path('.')
BATCH = '0055'
DATE = '2026-08-29'
SCHEDULED = [
    'cq_q_f516fabf66777d45b8f1aaa4681359ce',
    'cq_q_f59bce25182f9cab55ea413875396272',
    'cq_q_f6b3c0ccc0d9a2d307d5313492db383c',
    'cq_q_f6ce37472bfc7f9e9c3526329451d8a2',
    'cq_q_f849810b0aa5477dc435d4829108f4dd',
    'cq_q_f90ba8d1c83d261d11b756321624b189',
    'cq_q_f93179fa829fa3c7b681999e73d6d2d6',
    'cq_q_f93a98e3386612980296c0088e13980a',
    'cq_q_f980b179e23abf160c16d1c8876345fd',
    'cq_q_fb4bb71d8c35b1ff7e2fca5c36799af6',
]


def command(*args: str) -> tuple[int, str]:
    proc = subprocess.run(args, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    return proc.returncode, proc.stdout


def load_context(cid: str) -> dict | None:
    code, out = command('node', 'scripts/xhs.js', 'answer', 'context', '--canonical-id', cid, '--noWrite')
    if code != 0:
        return None
    ctx = json.loads(out)
    if not ctx.get('ok') or ctx.get('canonical', {}).get('canonical_id') != cid:
        return None
    return ctx


def main() -> int:
    out = ROOT / f'review/content_build/answer_batch_{BATCH}'
    out.mkdir(parents=True, exist_ok=True)

    question_rows = {}
    with (ROOT / 'data/questions/questions.jsonl').open(encoding='utf-8') as handle:
        for raw in handle:
            raw = raw.strip()
            if raw:
                row = json.loads(raw)
                question_rows[row.get('question_id')] = row

    resolutions = []
    active_targets: dict[str, dict] = {}
    seen_source_qids: set[str] = set()

    for scheduled_cid in SCHEDULED:
        scheduled_qid = scheduled_cid.removeprefix('cq_q_')
        row = question_rows.get(scheduled_qid)
        if row is None:
            raise SystemExit(f'{scheduled_cid}: scheduled source Question row is missing')

        direct = load_context(scheduled_cid)
        if direct is not None:
            target_cid = scheduled_cid
            status = 'active_as_scheduled'
            ctx = direct
        else:
            current_cid = row.get('canonical_id')
            valid = row.get('is_valid_for_library') is True
            if not valid:
                resolutions.append({
                    'scheduled_canonical_id': scheduled_cid,
                    'scheduled_question_id': scheduled_qid,
                    'resolution': 'retired_invalid_or_noise',
                    'current_canonical_id': current_cid,
                    'question': {
                        'original_question': row.get('original_question'),
                        'is_valid_for_library': row.get('is_valid_for_library'),
                        'invalid_reason': row.get('invalid_reason'),
                        'exclusion_reason': row.get('exclusion_reason'),
                        'quality_issues': row.get('quality_issues'),
                    },
                })
                continue
            if not current_cid:
                raise SystemExit(f'{scheduled_cid}: valid Question lost Canonical ownership')
            ctx = load_context(current_cid)
            if ctx is None:
                raise SystemExit(f'{scheduled_cid}: remapped to unresolved current Canonical {current_cid}')
            target_cid = current_cid
            status = 'remapped_to_current_canonical'

        if ctx.get('answer_type') != 'coding':
            raise SystemExit(f"{scheduled_cid}: resolved target {target_cid} answer type drift {ctx.get('answer_type')}")
        qids = ctx.get('canonical', {}).get('question_ids') or []
        sources = ctx.get('source_questions') or []
        by_qid = {x.get('question_id'): x for x in sources}
        if not qids or set(qids) != set(by_qid):
            raise SystemExit(f'{target_cid}: source-question/context ownership mismatch')

        source_questions = []
        for qid in qids:
            src = by_qid[qid]
            wording = src.get('original_question')
            if not isinstance(wording, str) or not wording.strip():
                raise SystemExit(f'{target_cid}/{qid}: empty source wording')
            if src.get('is_valid_for_library') is not True:
                raise SystemExit(f'{target_cid}/{qid}: active Canonical owns invalid source')
            source_questions.append({
                'question_id': qid,
                'original_question': wording,
                'is_valid_for_library': True,
            })
            seen_source_qids.add(qid)

        cdir = out / target_cid
        cdir.mkdir(parents=True, exist_ok=True)
        (cdir / 'context.json').write_text(json.dumps(ctx, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
        active_targets[target_cid] = {
            'canonical_id': target_cid,
            'answer_type': 'coding',
            'question_ids': qids,
            'source_questions': source_questions,
            'existing_candidate': (ROOT / f'review/candidates/answers/{target_cid}.md').exists(),
            'existing_evidence': (ROOT / f'review/evidence/{target_cid}.json').exists(),
        }
        resolutions.append({
            'scheduled_canonical_id': scheduled_cid,
            'scheduled_question_id': scheduled_qid,
            'resolution': status,
            'current_canonical_id': target_cid,
            'question': {
                'original_question': row.get('original_question'),
                'is_valid_for_library': row.get('is_valid_for_library'),
            },
        })

    retired = [r for r in resolutions if r['resolution'] == 'retired_invalid_or_noise']
    remapped = [r for r in resolutions if r['resolution'] == 'remapped_to_current_canonical']
    inventory = {
        'schema_version': 'answer_batch_source_inventory.v1',
        'batch': BATCH,
        'checked_at': DATE,
        'scheduled_count': len(SCHEDULED),
        'active_canonical_count': len(active_targets),
        'retired_invalid_or_noise_count': len(retired),
        'remapped_count': len(remapped),
        'source_question_count': len(seen_source_qids),
        'boundary_result': 'pass',
        'writer_rule': 'Writers must use these frozen current repository contexts as the source boundary. Stale task Canonical IDs are not resurrected; invalid/noise Questions stay retired, and remapped Questions follow current Canonical ownership.',
        'scheduled_resolutions': resolutions,
        'canonicals': list(active_targets.values()),
    }
    (out / 'source_inventory.json').write_text(json.dumps(inventory, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

    task = ROOT / f'tasks/answer-batches/TASK-20260711-0313-answer-batch-{BATCH}.md'
    text = task.read_text(encoding='utf-8')
    marker = (
        f'- [x] Batch 0055 scheduling reconciled against the current Question/Canonical SSOT and frozen in '
        f'`review/content_build/answer_batch_0055/source_inventory.json`: {len(active_targets)} active Coding Canonicals, '
        f'{len(remapped)} stale assignments remapped to current ownership, and {len(retired)} invalid/noise assignments '
        'kept retired with repository-recorded explanation fields. Candidate writing must use only the frozen active contexts.'
    )
    if '## Source boundary' not in text:
        text = text.rstrip() + '\n\n## Source boundary\n\n' + marker + '\n'
    elif marker not in text:
        text = text.rstrip() + '\n' + marker + '\n'
    text = text.replace('- Status: `pending`', '- Status: `in_progress`', 1)
    task.write_text(text, encoding='utf-8')

    print(
        f'PASS batch={BATCH} scheduled={len(SCHEDULED)} active={len(active_targets)} '
        f'remapped={len(remapped)} retired={len(retired)} source_questions={len(seen_source_qids)}'
    )
    for resolution in resolutions:
        print(
            f"RESOLUTION\t{resolution['scheduled_canonical_id']}\t{resolution['resolution']}\t"
            f"{resolution.get('current_canonical_id') or '-'}\t{resolution['question'].get('original_question') or ''}"
        )
    for row in active_targets.values():
        source_text = ' | '.join(q['original_question'] for q in row['source_questions'])
        print(f"ACTIVE\t{row['canonical_id']}\t{source_text}")
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
