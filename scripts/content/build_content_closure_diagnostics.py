#!/usr/bin/env python3
"""Build a current repository-local content-closure diagnostic snapshot.

This does not declare S10/S11 completion. It inventories active Canonicals,
Question reachability, formal Answer metadata, staged reviewed candidates, and
batch scheduling so the next bounded content slice can be selected from current
state instead of stale thresholds.
"""

from __future__ import annotations

import json
import re
from collections import Counter
from pathlib import Path

ROOT = Path('.')
DATE = '2026-08-29'
ANSWER_META = re.compile(r'^<!-- xhs-answer: (\{.*?\}) -->')
CID_RE = re.compile(r'`(cq_[A-Za-z0-9_]+)`')


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding='utf-8').splitlines() if line.strip()]


def answer_meta(path: Path) -> dict | None:
    if not path.exists():
        return None
    first = path.read_text(encoding='utf-8').splitlines()[0] if path.stat().st_size else ''
    m = ANSWER_META.match(first)
    if not m:
        return {'parse_error': True}
    try:
        return json.loads(m.group(1))
    except json.JSONDecodeError:
        return {'parse_error': True}


def main() -> int:
    canonicals = read_jsonl(ROOT / 'data/questions/canonical_questions.jsonl')
    questions = read_jsonl(ROOT / 'data/questions/questions.jsonl')
    progress = json.loads((ROOT / 'review/progress.json').read_text(encoding='utf-8')).get('items', [])
    progress_ids = {row.get('canonical_id') for row in progress}
    canonical_ids = {row['canonical_id'] for row in canonicals}

    scheduled: set[str] = set()
    task_paths = sorted((ROOT / 'tasks/answer-batches').glob('TASK-*-answer-batch-*.md'))
    for task in task_paths:
        for cid in CID_RE.findall(task.read_text(encoding='utf-8')):
            scheduled.add(cid)

    valid_questions = [q for q in questions if q.get('is_valid_for_library') is True]
    invalid_questions = [q for q in questions if q.get('is_valid_for_library') is False]
    valid_question_anomalies = [
        {'question_id': q.get('question_id'), 'canonical_id': q.get('canonical_id'), 'reason': 'valid_question_missing_active_canonical'}
        for q in valid_questions
        if not q.get('canonical_id') or q.get('canonical_id') not in canonical_ids
    ]
    invalid_question_anomalies = [
        {'question_id': q.get('question_id'), 'canonical_id': q.get('canonical_id'), 'reason': 'invalid_question_not_explainably_excluded'}
        for q in invalid_questions
        if q.get('canonical_id') is not None or not q.get('exclusion_reason')
    ]

    rows = []
    formal_status = Counter()
    formal_tier = Counter()
    answer_type = Counter()
    needs_curated = []
    reviewed_candidates = []
    unscheduled_needs_candidate = []
    missing_progress = []
    missing_formal_answer = []
    parse_errors = []

    for canonical in sorted(canonicals, key=lambda x: x['canonical_id']):
        cid = canonical['canonical_id']
        formal_path = ROOT / f'review/answers/{cid}.md'
        candidate_path = ROOT / f'review/candidates/answers/{cid}.md'
        evidence_path = ROOT / f'review/evidence/{cid}.json'
        formal = answer_meta(formal_path)
        candidate = answer_meta(candidate_path)
        evidence = json.loads(evidence_path.read_text(encoding='utf-8')) if evidence_path.exists() else None
        reviewed = bool(
            candidate
            and evidence
            and evidence.get('canonical_id') == cid
            and evidence.get('review_state') == 'independent_source_first_review_passed'
            and (evidence.get('review') or {}).get('independent') is True
            and (evidence.get('review') or {}).get('decision') == 'pass'
            and not (evidence.get('review') or {}).get('hard_failures')
        )
        if formal is None:
            missing_formal_answer.append(cid)
            formal_status['missing'] += 1
            formal_tier['missing'] += 1
        elif formal.get('parse_error'):
            parse_errors.append({'canonical_id': cid, 'path': str(formal_path)})
            formal_status['parse_error'] += 1
            formal_tier['parse_error'] += 1
        else:
            formal_status[str(formal.get('status'))] += 1
            formal_tier[str(formal.get('quality_tier'))] += 1
            answer_type[str(formal.get('answer_type'))] += 1
        if cid not in progress_ids:
            missing_progress.append(cid)

        is_curated_ready = bool(formal and not formal.get('parse_error') and formal.get('status') == 'ready' and formal.get('quality_tier') == 'curated')
        if not is_curated_ready:
            needs_curated.append(cid)
            if reviewed:
                reviewed_candidates.append(cid)
            elif cid not in scheduled:
                unscheduled_needs_candidate.append(cid)

        rows.append({
            'canonical_id': cid,
            'canonical_title': canonical.get('canonical_title'),
            'formal_status': None if not formal else formal.get('status'),
            'formal_quality_tier': None if not formal else formal.get('quality_tier'),
            'formal_answer_type': None if not formal else formal.get('answer_type'),
            'candidate_exists': candidate_path.exists(),
            'candidate_quality_tier': None if not candidate else candidate.get('quality_tier'),
            'independent_source_first_review_passed': reviewed,
            'promotion_blocker': None if not evidence else evidence.get('promotion_blocker'),
            'has_review_progress': cid in progress_ids,
            'scheduled_in_answer_batch_task': cid in scheduled,
        })

    snapshot = {
        'schema_version': 'content_closure_diagnostics.v1',
        'checked_at': DATE,
        'note': 'Repository-local diagnostic only. S10/S11/final-review completion must be proven by their canonical gates and is not inferred from these counts.',
        'counts': {
            'active_canonicals': len(canonicals),
            'questions': len(questions),
            'valid_questions': len(valid_questions),
            'invalid_questions': len(invalid_questions),
            'answer_batch_task_files': len(task_paths),
            'scheduled_canonical_ids_seen_in_batch_tasks': len(scheduled),
            'canonicals_needing_curated_ready_formal_answer': len(needs_curated),
            'reviewed_candidates_awaiting_promotion_or_real_review': len(reviewed_candidates),
            'unscheduled_canonicals_needing_candidate_or_remediation': len(unscheduled_needs_candidate),
            'missing_review_progress': len(missing_progress),
            'missing_formal_answer': len(missing_formal_answer),
            'valid_question_reachability_anomalies': len(valid_question_anomalies),
            'invalid_question_explainability_anomalies': len(invalid_question_anomalies),
            'answer_metadata_parse_errors': len(parse_errors),
        },
        'formal_status_counts': dict(sorted(formal_status.items())),
        'formal_quality_tier_counts': dict(sorted(formal_tier.items())),
        'formal_answer_type_counts': dict(sorted(answer_type.items())),
        'next_unscheduled_canonical_ids': unscheduled_needs_candidate[:50],
        'reviewed_candidate_ids_awaiting_promotion_or_real_review': reviewed_candidates,
        'missing_review_progress_ids': missing_progress,
        'missing_formal_answer_ids': missing_formal_answer,
        'valid_question_reachability_anomalies': valid_question_anomalies,
        'invalid_question_explainability_anomalies': invalid_question_anomalies,
        'answer_metadata_parse_errors': parse_errors,
        'canonicals': rows,
    }
    out = ROOT / 'review/content_build/closure/current_state.json'
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(snapshot, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(snapshot['counts'], ensure_ascii=False, sort_keys=True))
    print('next_unscheduled=' + ','.join(unscheduled_needs_candidate[:20]))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
