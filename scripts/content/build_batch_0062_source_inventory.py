#!/usr/bin/env python3
"""Reconcile and freeze Batch 0062 repository source contexts before answer writing."""
from __future__ import annotations

import json
import subprocess
from pathlib import Path

ROOT = Path('.')
BATCH = '0062'
DATE = '2026-08-31'
SCHEDULED_TYPES = {
    'cq_q_61d48051e02806afb811f793afd4a269': 'coding',
    'cq_q_6a7c7f58ad4a4828e2c984b668d7ba32': 'coding',
    'cq_q_6c5a986936f3d831fd8dc544ccd71910': 'coding',
    'cq_q_9e1c6fe7d0d269300c71151cd8c24a81': 'coding',
    'cq_q_ad98fcd2a28e860ad42d11065af2caea': 'coding',
    'cq_q_d0b70d126320ddd7e4a234f0f3c6066f': 'coding',
    'cq_q_e1cbd1e9e8df435dfb30e81ea69018c8': 'coding',
    'cq_q_ffe5f2da4a3ce9f56c51bce699ab1b13': 'coding',
    'cq_q_004333ab8f1c0f22014765e4e6f7abb0': 'coding',
    'cq_q_00bc3ebd89c0d03aae8db0a36cd747e2': 'coding',
}
TYPE_OVERRIDE_ALLOWED = {'cq_q_004333ab8f1c0f22014765e4e6f7abb0'}
PERSONAL_FACT_REQUIRED: set[str] = set()
SECONDARY_COVERAGE_REQUIRED: set[str] = set()
VALID_TYPES = {'coding', 'mechanism', 'concept', 'scenario', 'project', 'behavior'}


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


def source_occurrence_key(src: dict) -> tuple:
    return (
        src.get('question_id'),
        src.get('source_note_id'),
        src.get('source_question_index'),
        src.get('original_question'),
    )


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
    seen_occurrences: set[tuple] = set()

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
            if row.get('is_valid_for_library') is not True:
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
        elif scheduled_cid in TYPE_OVERRIDE_ALLOWED and actual_type in VALID_TYPES:
            type_resolution = 'source_type_risk_resolved_by_current_audit'
        else:
            raise SystemExit(f'{scheduled_cid}: answer type drift without task override: {scheduled_type} -> {actual_type}')

        qids = list(ctx.get('canonical', {}).get('question_ids') or [])
        sources = list(ctx.get('source_questions') or [])
        source_qids = {x.get('question_id') for x in sources}
        if not qids or set(qids) != source_qids:
            raise SystemExit(f'{target_cid}: source-question/context ownership mismatch: qids={qids} source_qids={sorted(source_qids)}')
        if scheduled_qid not in qids:
            raise SystemExit(f'{scheduled_cid}: resolved Canonical {target_cid} no longer owns scheduled source Question')

        frozen_sources: list[dict] = []
        local_occurrences: set[tuple] = set()
        for src in sources:
            qid = src.get('question_id')
            wording = src.get('original_question')
            if qid not in qids:
                raise SystemExit(f'{target_cid}: source occurrence references non-owned Question {qid}')
            if not isinstance(wording, str) or not wording.strip():
                raise SystemExit(f'{target_cid}/{qid}: empty source wording')
            if src.get('is_valid_for_library') is not True:
                raise SystemExit(f'{target_cid}/{qid}: active Canonical owns invalid source occurrence')
            key = source_occurrence_key(src)
            if key in local_occurrences:
                raise SystemExit(f'{target_cid}/{qid}: duplicate primary-source occurrence identity')
            local_occurrences.add(key)
            seen_occurrences.add(key)
            seen_source_qids.add(qid)
            frozen_sources.append({
                'question_id': qid,
                'original_question': wording,
                'is_valid_for_library': True,
                'source_note_id': src.get('source_note_id'),
                'source_question_index': src.get('source_question_index'),
            })

        if target_cid not in active_targets:
            cdir = out / target_cid
            cdir.mkdir(parents=True, exist_ok=True)
            (cdir / 'context.json').write_text(json.dumps(ctx, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
            active_targets[target_cid] = {
                'canonical_id': target_cid,
                'answer_type': actual_type,
                'canonical_title': ctx.get('canonical', {}).get('canonical_title'),
                'question_ids': qids,
                'source_questions': frozen_sources,
                'source_question_count': len(set(qids)),
                'source_occurrence_count': len(frozen_sources),
                'existing_candidate': (ROOT / f'review/candidates/answers/{target_cid}.md').exists(),
                'existing_evidence': (ROOT / f'review/evidence/{target_cid}.json').exists(),
                'personal_fact_verification_required': scheduled_cid in PERSONAL_FACT_REQUIRED,
                'secondary_coverage_required': scheduled_cid in SECONDARY_COVERAGE_REQUIRED,
            }
        else:
            existing = active_targets[target_cid]
            if set(existing['question_ids']) != set(qids) or {source_occurrence_key(x) for x in existing['source_questions']} != {source_occurrence_key(x) for x in frozen_sources}:
                raise SystemExit(f'{target_cid}: multiple scheduled entries resolved to inconsistent frozen source packets')

        scheduled_occurrences = [x for x in frozen_sources if x['question_id'] == scheduled_qid]
        resolutions.append({
            'scheduled_canonical_id': scheduled_cid,
            'scheduled_question_id': scheduled_qid,
            'scheduled_answer_type': scheduled_type,
            'current_answer_type': actual_type,
            'type_resolution': type_resolution,
            'resolution': ownership_resolution,
            'current_canonical_id': target_cid,
            'personal_fact_verification_required': scheduled_cid in PERSONAL_FACT_REQUIRED,
            'secondary_coverage_required': scheduled_cid in SECONDARY_COVERAGE_REQUIRED,
            'question': {
                'original_question': row.get('original_question'),
                'source_occurrence_count': len(scheduled_occurrences),
                'source_wording_variants': sorted({x['original_question'] for x in scheduled_occurrences}),
                'is_valid_for_library': row.get('is_valid_for_library'),
            },
        })

    retired = [r for r in resolutions if r['resolution'] == 'retired_invalid_or_noise']
    remapped = [r for r in resolutions if r['resolution'] == 'remapped_to_current_canonical']
    type_overrides = [r for r in resolutions if r.get('type_resolution') == 'source_type_risk_resolved_by_current_audit']
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
        'source_occurrence_count': len(seen_occurrences),
        'source_type_resolution_count': len(type_overrides),
        'personal_fact_target_count': sum(1 for x in active_targets.values() if x['personal_fact_verification_required']),
        'secondary_coverage_target_count': sum(1 for x in active_targets.values() if x['secondary_coverage_required']),
        'boundary_result': 'pass',
        'scheduled_type_counts': {t: sum(1 for x in SCHEDULED_TYPES.values() if x == t) for t in sorted(set(SCHEDULED_TYPES.values()))},
        'current_type_counts': dict(sorted(current_type_counts.items())),
        'writer_rule': (
            'Writers must use these frozen current repository contexts as the source boundary. A normalized Question ID may have multiple primary-source occurrences; '
            'source_questions and source_occurrence_count preserve every occurrence and writers/reviewers must not collapse them by question_id alone. '
            'Stale task Canonical IDs are not resurrected; invalid/noise Questions stay retired; remapped Questions follow current Canonical ownership; '
            'task entries carrying source-type risk follow the current answer-type audit.'
        ),
        'scheduled_resolutions': resolutions,
        'canonicals': list(active_targets.values()),
    }
    (out / 'source_inventory.json').write_text(json.dumps(inventory, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

    task = ROOT / f'tasks/answer-batches/TASK-20260711-0313-answer-batch-{BATCH}.md'
    text = task.read_text(encoding='utf-8')
    marker = (
        f'- [x] Batch {BATCH} scheduling reconciled against the current Question/Canonical/type SSOT and frozen in '
        f'`review/content_build/answer_batch_{BATCH}/source_inventory.json`: {len(active_targets)} active Canonicals, '
        f'{len(remapped)} stale assignments remapped to current ownership, {len(retired)} invalid/noise assignments kept retired, '
        f'{len(type_overrides)} source-type task entries resolved by the current answer-type audit, '
        f'{len(seen_source_qids)} normalized source Questions across {len(seen_occurrences)} primary-source occurrences. '
        'Candidate writing must use only the frozen current source packets and preserve every source occurrence.'
    )
    if '## Source boundary' not in text:
        text = text.rstrip() + '\n\n## Source boundary\n\n' + marker + '\n'
    elif marker not in text:
        text = text.rstrip() + '\n' + marker + '\n'
    text = text.replace('- Status: `pending`', '- Status: `in_progress`', 1)
    task.write_text(text, encoding='utf-8')

    print(f'PASS batch={BATCH} scheduled={len(SCHEDULED_TYPES)} active={len(active_targets)} remapped={len(remapped)} retired={len(retired)} type_resolutions={len(type_overrides)} source_questions={len(seen_source_qids)} source_occurrences={len(seen_occurrences)} current_types={dict(sorted(current_type_counts.items()))}')
    for resolution in resolutions:
        print(f"RESOLUTION\t{resolution['scheduled_canonical_id']}\t{resolution['scheduled_answer_type']}\t{resolution.get('current_answer_type') or '-'}\t{resolution.get('type_resolution') or '-'}\t{resolution['resolution']}\t{resolution.get('current_canonical_id') or '-'}\t{resolution['question'].get('original_question') or ''}")
    for item in active_targets.values():
        source_text = ' | '.join(q['original_question'] for q in item['source_questions'])
        print(f"ACTIVE\t{item['canonical_id']}\t{item['answer_type']}\tqids={item['source_question_count']}\toccurrences={item['source_occurrence_count']}\t{source_text}")
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
