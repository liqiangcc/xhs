#!/usr/bin/env python3
"""Reconcile and freeze Batch 0056 repository source contexts before answer writing.

The batch task is only a historical schedule. Current Question rows, Canonical graph,
and current answer-type audit are the SSOT: stale scheduled Canonicals may have been
merged, split, retired, or explicitly reclassified. This builder follows current
ownership, keeps invalid/noise records retired, records allowed historical type
overrides, and freezes exact repository source wording for the next source-first slice.
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

ROOT = Path('.')
BATCH = '0056'
DATE = '2026-08-29'
SCHEDULED_TYPES = {
    'cq_q_fbb2e34022cf1f4d0e2ba1a92b1688aa': 'coding',
    'cq_q_fc030f5d732ab198236441d05ebb7eff': 'coding',
    'cq_q_fd5f836465b9d8c2f7c54c5d5a262e9d': 'coding',
    'cq_q_fe3172f9067bf094daf0310e95ad6fd8': 'coding',
    'cq_q_fedafeab2f6110ead792af233549b58c': 'coding',
    'cq_q_ff9548e89dda56f74db92a45062a08aa': 'coding',
    'cq_q_ffea95ccbbb749dac2669e262c61f5d5': 'coding',
    'cq_q_01c2da5dde2dcb36ad3f9d17b210ab5c': 'mechanism',
    'cq_q_7d7a2efb76976df46319df21283287c6': 'mechanism',
    'cq_q_7daa5cfddb93ce44e349bd4978214d71': 'mechanism',
}
# The task explicitly marks these historical mechanism classifications with
# `source_type_overridden`; current answer context/type audit is authoritative.
TYPE_OVERRIDE_ALLOWED = {
    'cq_q_01c2da5dde2dcb36ad3f9d17b210ab5c',
    'cq_q_7d7a2efb76976df46319df21283287c6',
    'cq_q_7daa5cfddb93ce44e349bd4978214d71',
}


def command(*args: str) -> tuple[int, str]:
    proc = subprocess.run(args, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    return proc.returncode, proc.stdout


def load_context(cid: str) -> dict | None:
    code, out = command('node', 'scripts/xhs.js', 'answer', 'context', '--canonical-id', cid, '--noWrite')
    if code != 0:
        return None
    try:
        ctx = json.loads(out)
    except json.JSONDecodeError:
        return None
    if not ctx.get('ok') or ctx.get('canonical', {}).get('canonical_id') != cid:
        return None
    return ctx


def main() -> int:
    out = ROOT / f'review/content_build/answer_batch_{BATCH}'
    out.mkdir(parents=True, exist_ok=True)

    question_rows: dict[str, dict] = {}
    with (ROOT / 'data/questions/questions.jsonl').open(encoding='utf-8') as handle:
        for raw in handle:
            raw = raw.strip()
            if raw:
                row = json.loads(raw)
                question_rows[row.get('question_id')] = row

    resolutions: list[dict] = []
    active_targets: dict[str, dict] = {}
    seen_source_qids: set[str] = set()

    for scheduled_cid, scheduled_type in SCHEDULED_TYPES.items():
        scheduled_qid = scheduled_cid.removeprefix('cq_q_')
        row = question_rows.get(scheduled_qid)
        if row is None:
            raise SystemExit(f'{scheduled_cid}: scheduled source Question row is missing')

        direct = load_context(scheduled_cid)
        if direct is not None:
            target_cid = scheduled_cid
            ownership_resolution = 'active_as_scheduled'
            ctx = direct
        else:
            current_cid = row.get('canonical_id')
            valid = row.get('is_valid_for_library') is True
            if not valid:
                resolutions.append({
                    'scheduled_canonical_id': scheduled_cid,
                    'scheduled_question_id': scheduled_qid,
                    'scheduled_answer_type': scheduled_type,
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
            ownership_resolution = 'remapped_to_current_canonical'

        actual_type = ctx.get('answer_type')
        if actual_type == scheduled_type:
            type_resolution = 'scheduled_type_matches_current_audit'
        elif scheduled_cid in TYPE_OVERRIDE_ALLOWED:
            if actual_type not in {'coding', 'mechanism', 'concept', 'scenario', 'project', 'behavior'}:
                raise SystemExit(f'{scheduled_cid}: current answer type is invalid: {actual_type}')
            type_resolution = 'historical_type_overridden_by_current_audit'
        else:
            raise SystemExit(
                f'{scheduled_cid}: resolved target {target_cid} answer type drift; '
                f'scheduled={scheduled_type} current={actual_type} without source_type_overridden marker'
            )

        qids = list(ctx.get('canonical', {}).get('question_ids') or [])
        sources = list(ctx.get('source_questions') or [])
        by_qid = {x.get('question_id'): x for x in sources}
        if not qids or set(qids) != set(by_qid):
            raise SystemExit(f'{target_cid}: source-question/context ownership mismatch')
        if scheduled_qid not in qids:
            raise SystemExit(f'{scheduled_cid}: resolved Canonical {target_cid} no longer owns scheduled source Question')

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

        existing = active_targets.get(target_cid)
        if existing is not None:
            if existing['answer_type'] != actual_type or existing['question_ids'] != qids:
                raise SystemExit(f'{target_cid}: duplicate schedule resolution disagrees on current context')
        else:
            cdir = out / target_cid
            cdir.mkdir(parents=True, exist_ok=True)
            (cdir / 'context.json').write_text(json.dumps(ctx, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
            active_targets[target_cid] = {
                'canonical_id': target_cid,
                'answer_type': actual_type,
                'canonical_title': ctx.get('canonical', {}).get('canonical_title'),
                'question_ids': qids,
                'source_questions': source_questions,
                'existing_candidate': (ROOT / f'review/candidates/answers/{target_cid}.md').exists(),
                'existing_evidence': (ROOT / f'review/evidence/{target_cid}.json').exists(),
            }

        resolutions.append({
            'scheduled_canonical_id': scheduled_cid,
            'scheduled_question_id': scheduled_qid,
            'scheduled_answer_type': scheduled_type,
            'current_answer_type': actual_type,
            'type_resolution': type_resolution,
            'resolution': ownership_resolution,
            'current_canonical_id': target_cid,
            'question': {
                'original_question': row.get('original_question'),
                'is_valid_for_library': row.get('is_valid_for_library'),
            },
        })

    retired = [r for r in resolutions if r['resolution'] == 'retired_invalid_or_noise']
    remapped = [r for r in resolutions if r['resolution'] == 'remapped_to_current_canonical']
    type_overrides = [r for r in resolutions if r.get('type_resolution') == 'historical_type_overridden_by_current_audit']
    current_type_counts: dict[str, int] = {}
    for item in active_targets.values():
        current_type_counts[item['answer_type']] = current_type_counts.get(item['answer_type'], 0) + 1

    inventory = {
        'schema_version': 'answer_batch_source_inventory.v1',
        'batch': BATCH,
        'checked_at': DATE,
        'scheduled_count': len(SCHEDULED_TYPES),
        'active_canonical_count': len(active_targets),
        'retired_invalid_or_noise_count': len(retired),
        'remapped_count': len(remapped),
        'source_question_count': len(seen_source_qids),
        'historical_type_override_count': len(type_overrides),
        'boundary_result': 'pass',
        'scheduled_type_counts': {
            'coding': sum(1 for x in SCHEDULED_TYPES.values() if x == 'coding'),
            'mechanism': sum(1 for x in SCHEDULED_TYPES.values() if x == 'mechanism'),
        },
        'current_type_counts': dict(sorted(current_type_counts.items())),
        'writer_rule': (
            'Writers must use these frozen current repository contexts as the source boundary. '
            'Stale task Canonical IDs are not resurrected; invalid/noise Questions stay retired; '
            'remapped Questions follow current Canonical ownership; and entries historically marked '
            '`source_type_overridden` use the current answer-type audit rather than stale task typing.'
        ),
        'scheduled_resolutions': resolutions,
        'canonicals': list(active_targets.values()),
    }
    (out / 'source_inventory.json').write_text(json.dumps(inventory, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

    task = ROOT / f'tasks/answer-batches/TASK-20260711-0313-answer-batch-{BATCH}.md'
    text = task.read_text(encoding='utf-8')
    marker = (
        f'- [x] Batch 0056 scheduling reconciled against the current Question/Canonical/type SSOT and frozen in '
        f'`review/content_build/answer_batch_0056/source_inventory.json`: {len(active_targets)} active Canonicals, '
        f'{len(remapped)} stale assignments remapped to current ownership, {len(retired)} invalid/noise assignments '
        f'kept retired, and {len(type_overrides)} historical `source_type_overridden` classifications resolved by the '
        'current answer-type audit. Candidate writing must use only the frozen current source packets.'
    )
    if '## Source boundary' not in text:
        text = text.rstrip() + '\n\n## Source boundary\n\n' + marker + '\n'
    elif marker not in text:
        text = text.rstrip() + '\n' + marker + '\n'
    text = text.replace('- Status: `pending`', '- Status: `in_progress`', 1)
    task.write_text(text, encoding='utf-8')

    print(
        f'PASS batch={BATCH} scheduled={len(SCHEDULED_TYPES)} active={len(active_targets)} '
        f'remapped={len(remapped)} retired={len(retired)} type_overrides={len(type_overrides)} '
        f'source_questions={len(seen_source_qids)} current_types={dict(sorted(current_type_counts.items()))}'
    )
    for resolution in resolutions:
        print(
            f"RESOLUTION\t{resolution['scheduled_canonical_id']}\t{resolution['scheduled_answer_type']}\t"
            f"{resolution.get('current_answer_type') or '-'}\t{resolution.get('type_resolution') or '-'}\t"
            f"{resolution['resolution']}\t{resolution.get('current_canonical_id') or '-'}\t"
            f"{resolution['question'].get('original_question') or ''}"
        )
    for item in active_targets.values():
        source_text = ' | '.join(q['original_question'] for q in item['source_questions'])
        print(f"ACTIVE\t{item['canonical_id']}\t{item['answer_type']}\t{source_text}")
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
