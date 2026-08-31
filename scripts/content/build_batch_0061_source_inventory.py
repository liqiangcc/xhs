#!/usr/bin/env python3
"""Reconcile and freeze Batch 0061 repository source contexts before answer writing."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

ROOT = Path('.')
BATCH = '0061'
DATE = '2026-08-31'
SCHEDULED_TYPES = {
    'cq_q_eee8e67726c9be6095301d0a4bfe4eab': 'concept',
    'cq_q_000581e8c2ca04ba277408fc68f61bce': 'behavior',
    'cq_q_05b816cca1029a3e9b9932ceb1e0d9eb': 'coding',
    'cq_q_0616abe7f8861fde19fda29ad5b2b305': 'coding',
    'cq_q_1d62a5e5748bc0cf6fba59fa1d4655aa': 'coding',
    'cq_q_206301f6679d9047d406eb16ef08be5c': 'coding',
    'cq_q_22745d1a56145d782dbda254186e9d75': 'coding',
    'cq_q_35c2d83b04a38c71b4cca1e3ed3f401b': 'coding',
    'cq_q_501a3a0fb13e9816cbe7dde18673c074': 'coding',
    'cq_q_5fec9f875255be5ae3fa636523b24956': 'coding',
}
# The task explicitly marks this entry as carrying mixed-source/type risk.
TYPE_OVERRIDE_ALLOWED = {
    'cq_q_eee8e67726c9be6095301d0a4bfe4eab',
}
PERSONAL_FACT_REQUIRED = {
    'cq_q_000581e8c2ca04ba277408fc68f61bce',
}
SECONDARY_COVERAGE_REQUIRED = {
    'cq_q_eee8e67726c9be6095301d0a4bfe4eab',
    'cq_q_000581e8c2ca04ba277408fc68f61bce',
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


def occurrence_key(src: dict) -> tuple[str, str, str, str]:
    """Return a stable primary-source occurrence identity.

    A normalized Question ID may intentionally occur in more than one source note.
    The inventory must therefore never use question_id alone as the source-row key.
    """
    return (
        str(src.get('question_id') or ''),
        str(src.get('source_note_id') or ''),
        str(src.get('source_question_index') if src.get('source_question_index') is not None else ''),
        str(src.get('original_question') or ''),
    )


def main() -> int:
    out = ROOT / f'review/content_build/answer_batch_{BATCH}'
    out.mkdir(parents=True, exist_ok=True)

    question_rows_by_id: dict[str, list[dict]] = {}
    with (ROOT / 'data/questions/questions.jsonl').open(encoding='utf-8') as handle:
        for raw in handle:
            raw = raw.strip()
            if raw:
                row = json.loads(raw)
                question_rows_by_id.setdefault(row.get('question_id'), []).append(row)

    resolutions: list[dict] = []
    active_targets: dict[str, dict] = {}
    seen_source_qids: set[str] = set()
    seen_source_occurrences: set[tuple[str, str, str, str]] = set()

    for scheduled_cid, scheduled_type in SCHEDULED_TYPES.items():
        scheduled_qid = scheduled_cid.removeprefix('cq_q_')
        scheduled_rows = question_rows_by_id.get(scheduled_qid) or []
        if not scheduled_rows:
            raise SystemExit(f'{scheduled_cid}: scheduled source Question row is missing')
        # Scheduled rows sharing one normalized Question ID must agree on current
        # ownership/validity. Wording may differ across primary-source occurrences.
        current_cids = {row.get('canonical_id') for row in scheduled_rows}
        validity = {row.get('is_valid_for_library') for row in scheduled_rows}
        if len(current_cids) != 1:
            raise SystemExit(f'{scheduled_cid}: source occurrences disagree on Canonical ownership: {sorted(current_cids)}')
        if len(validity) != 1:
            raise SystemExit(f'{scheduled_cid}: source occurrences disagree on validity: {sorted(validity, key=str)}')
        row = scheduled_rows[0]

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
                    'personal_fact_verification_required': scheduled_cid in PERSONAL_FACT_REQUIRED,
                    'secondary_coverage_required': scheduled_cid in SECONDARY_COVERAGE_REQUIRED,
                    'question': {
                        'original_question': row.get('original_question'),
                        'source_occurrence_count': len(scheduled_rows),
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
            type_resolution = 'source_type_risk_resolved_by_current_audit'
        else:
            raise SystemExit(f'{scheduled_cid}: answer type drift without task override: {scheduled_type} -> {actual_type}')

        qids = list(ctx.get('canonical', {}).get('question_ids') or [])
        sources = list(ctx.get('source_questions') or [])
        source_qids = {x.get('question_id') for x in sources}
        if not qids or set(qids) != source_qids:
            raise SystemExit(
                f'{target_cid}: source-question/context ownership mismatch: '
                f'canonical={sorted(qids)} source={sorted(source_qids)}'
            )
        if scheduled_qid not in qids:
            raise SystemExit(f'{scheduled_cid}: resolved Canonical {target_cid} no longer owns scheduled source Question')

        source_questions = []
        for src in sources:
            qid = src.get('question_id')
            wording = src.get('original_question')
            if not isinstance(wording, str) or not wording.strip():
                raise SystemExit(f'{target_cid}/{qid}: empty source wording')
            if src.get('is_valid_for_library') is not True:
                raise SystemExit(f'{target_cid}/{qid}: active Canonical owns invalid source')
            rows = question_rows_by_id.get(qid) or []
            matched = any(
                candidate.get('canonical_id') == target_cid
                and candidate.get('is_valid_for_library') is True
                and candidate.get('original_question') == wording
                and candidate.get('source_note_id') == src.get('source_note_id')
                and candidate.get('source_question_index') == src.get('source_question_index')
                for candidate in rows
            )
            if not matched:
                raise SystemExit(
                    f'{target_cid}/{qid}/{src.get("source_note_id")}/{src.get("source_question_index")}: '
                    'source occurrence/context mismatch'
                )
            occurrence = {
                'question_id': qid,
                'original_question': wording,
                'is_valid_for_library': True,
                'source_note_id': src.get('source_note_id'),
                'source_question_index': src.get('source_question_index'),
            }
            source_questions.append(occurrence)
            seen_source_qids.add(qid)
            seen_source_occurrences.add(occurrence_key(src))

        if target_cid not in active_targets:
            cdir = out / target_cid
            cdir.mkdir(parents=True, exist_ok=True)
            (cdir / 'context.json').write_text(
                json.dumps(ctx, ensure_ascii=False, indent=2) + '\n', encoding='utf-8'
            )
            active_targets[target_cid] = {
                'canonical_id': target_cid,
                'answer_type': actual_type,
                'canonical_title': ctx.get('canonical', {}).get('canonical_title'),
                'question_ids': qids,
                'source_questions': source_questions,
                'source_question_count': len(set(qids)),
                'source_occurrence_count': len(source_questions),
                'existing_candidate': (ROOT / f'review/candidates/answers/{target_cid}.md').exists(),
                'existing_evidence': (ROOT / f'review/evidence/{target_cid}.json').exists(),
                'personal_fact_verification_required': scheduled_cid in PERSONAL_FACT_REQUIRED,
                'secondary_coverage_required': scheduled_cid in SECONDARY_COVERAGE_REQUIRED,
            }
        else:
            # Multiple scheduled rows may converge on one current Canonical. Preserve the strictest risk flags.
            active_targets[target_cid]['personal_fact_verification_required'] = (
                active_targets[target_cid]['personal_fact_verification_required']
                or scheduled_cid in PERSONAL_FACT_REQUIRED
            )
            active_targets[target_cid]['secondary_coverage_required'] = (
                active_targets[target_cid]['secondary_coverage_required']
                or scheduled_cid in SECONDARY_COVERAGE_REQUIRED
            )

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
                'source_occurrence_count': len(scheduled_rows),
                'source_wording_variants': sorted({x.get('original_question') for x in scheduled_rows if x.get('original_question')}),
                'is_valid_for_library': row.get('is_valid_for_library'),
            },
        })

    retired = [r for r in resolutions if r['resolution'] == 'retired_invalid_or_noise']
    remapped = [r for r in resolutions if r['resolution'] == 'remapped_to_current_canonical']
    type_overrides = [
        r for r in resolutions if r.get('type_resolution') == 'source_type_risk_resolved_by_current_audit'
    ]
    current_type_counts: dict[str, int] = {}
    for item in active_targets.values():
        current_type_counts[item['answer_type']] = current_type_counts.get(item['answer_type'], 0) + 1

    personal_targets = sum(
        1 for x in active_targets.values() if x['personal_fact_verification_required']
    )
    secondary_targets = sum(
        1 for x in active_targets.values() if x['secondary_coverage_required']
    )
    inventory = {
        'schema_version': 'answer_batch_source_inventory.v1',
        'batch': BATCH,
        'checked_at': DATE,
        'scheduled_count': len(SCHEDULED_TYPES),
        'active_canonical_count': len(active_targets),
        'retired_invalid_or_noise_count': len(retired),
        'remapped_count': len(remapped),
        'source_question_count': len(seen_source_qids),
        'source_occurrence_count': len(seen_source_occurrences),
        'source_type_resolution_count': len(type_overrides),
        'personal_fact_target_count': personal_targets,
        'secondary_coverage_target_count': secondary_targets,
        'boundary_result': 'pass',
        'scheduled_type_counts': {
            t: sum(1 for x in SCHEDULED_TYPES.values() if x == t)
            for t in sorted(set(SCHEDULED_TYPES.values()))
        },
        'current_type_counts': dict(sorted(current_type_counts.items())),
        'writer_rule': (
            'Writers must use these frozen current repository contexts as the source boundary. '
            'A normalized Question ID may have multiple primary-source occurrences; source_questions and '
            'source_occurrence_count preserve every occurrence and writers/reviewers must not collapse them by '
            'question_id alone. Stale task Canonical IDs are not resurrected; invalid/noise Questions stay retired; '
            'remapped Questions follow current Canonical ownership; task entries carrying mixed-source/type risk follow '
            'the current answer-type audit. Personal-fact-sensitive targets require explicit verification before personal '
            'claims, and secondary-coverage targets must close the flagged secondary source variants before review.'
        ),
        'scheduled_resolutions': resolutions,
        'canonicals': list(active_targets.values()),
    }
    (out / 'source_inventory.json').write_text(
        json.dumps(inventory, ensure_ascii=False, indent=2) + '\n', encoding='utf-8'
    )

    task = ROOT / f'tasks/answer-batches/TASK-20260711-0313-answer-batch-{BATCH}.md'
    text = task.read_text(encoding='utf-8')
    marker = (
        f'- [x] Batch {BATCH} scheduling reconciled against the current Question/Canonical/type SSOT and frozen in '
        f'`review/content_build/answer_batch_{BATCH}/source_inventory.json`: {len(active_targets)} active Canonicals, '
        f'{len(remapped)} stale assignments remapped to current ownership, {len(retired)} invalid/noise assignments kept retired, '
        f'{len(type_overrides)} mixed-source/type task entries resolved by the current answer-type audit, '
        f'{len(seen_source_qids)} normalized source Questions across {len(seen_source_occurrences)} primary-source occurrences, '
        f'{personal_targets} personal-fact-sensitive targets, and {secondary_targets} secondary-coverage targets. '
        'Candidate writing must use only the frozen current source packets, preserve every source occurrence, and preserve these risk gates.'
    )
    text = text.replace('- Status: `pending`', '- Status: `in_progress`', 1)
    if '## Source boundary' not in text:
        text = text.rstrip() + '\n\n## Source boundary\n\n' + marker + '\n'
    elif marker not in text:
        text = text.rstrip() + '\n' + marker + '\n'
    task.write_text(text, encoding='utf-8')

    print(
        f'PASS batch={BATCH} scheduled={len(SCHEDULED_TYPES)} active={len(active_targets)} '
        f'remapped={len(remapped)} retired={len(retired)} type_resolutions={len(type_overrides)} '
        f'personal={personal_targets} secondary={secondary_targets} source_questions={len(seen_source_qids)} '
        f'source_occurrences={len(seen_source_occurrences)} current_types={dict(sorted(current_type_counts.items()))}'
    )
    for resolution in resolutions:
        print(
            f"RESOLUTION\t{resolution['scheduled_canonical_id']}\t{resolution['scheduled_answer_type']}\t"
            f"{resolution.get('current_answer_type') or '-'}\t{resolution.get('type_resolution') or '-'}\t"
            f"{resolution['resolution']}\t{resolution.get('current_canonical_id') or '-'}\t"
            f"personal={resolution.get('personal_fact_verification_required', False)}\t"
            f"secondary={resolution.get('secondary_coverage_required', False)}\t"
            f"occurrences={resolution['question'].get('source_occurrence_count', 0)}\t"
            f"{resolution['question'].get('original_question') or ''}"
        )
    for item in active_targets.values():
        source_text = ' | '.join(q['original_question'] for q in item['source_questions'])
        print(
            f"ACTIVE\t{item['canonical_id']}\t{item['answer_type']}\t"
            f"personal={item['personal_fact_verification_required']}\t"
            f"secondary={item['secondary_coverage_required']}\t"
            f"questions={item['source_question_count']}\toccurrences={item['source_occurrence_count']}\t{source_text}"
        )
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
