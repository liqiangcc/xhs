#!/usr/bin/env python3
"""Retire stale Batch 0060 state left by CMS/G1 canonical consolidation.

The source-first normalization merged legacy canonical
cq_q_7960226d99224c6c8d4411110ff10c8b into survivor
cq_q_d3fea003c007b50735b8e695473de9ac. ReviewProgress and formal Answer
artifacts are keyed by canonical_id, so artifacts for the retired canonical must
not survive the merge.

This remediation is intentionally conservative. It removes ReviewProgress only
when it has zero real-review telemetry, and removes the orphan formal Answer
only when it is the untouched generated long-tail baseline. Any curated,
reviewed, candidate, evidence-backed, or otherwise non-default state fails
closed instead of discarding evidence.
"""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

ROOT = Path('.')
PROGRESS_PATH = ROOT / 'review/progress.json'
OUT_PATH = ROOT / 'review/content_build/answer_batch_0060/stale_review_progress_retirement.json'
CANONICALS_PATH = ROOT / 'data/questions/canonical_questions.jsonl'
OLD_CANONICAL = 'cq_q_7960226d99224c6c8d4411110ff10c8b'
SURVIVOR_CANONICAL = 'cq_q_d3fea003c007b50735b8e695473de9ac'
OLD_ANSWER_PATH = ROOT / 'review/answers' / f'{OLD_CANONICAL}.md'
OLD_CANDIDATE_PATH = ROOT / 'review/candidates/answers' / f'{OLD_CANONICAL}.md'
OLD_EVIDENCE_PATH = ROOT / 'review/evidence' / f'{OLD_CANONICAL}.json'
DATE = '2026-08-30'


def read_json(path: Path):
    return json.loads(path.read_text(encoding='utf-8'))


def write_json(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding='utf-8').splitlines() if line.strip()]


def is_zero_real_review(row: dict) -> bool:
    return (
        row.get('status') == 'new'
        and row.get('review_count') == 0
        and row.get('last_reviewed_at') is None
        and row.get('mistake_count') == 0
    )


def parse_answer_metadata(text: str) -> dict:
    first = text.splitlines()[0] if text else ''
    match = re.fullmatch(r'<!-- xhs-answer: (\{.*\}) -->', first)
    if not match:
        raise SystemExit('orphan formal Answer has invalid metadata header')
    return json.loads(match.group(1))


def verify_canonical_consolidation() -> None:
    canonicals = read_jsonl(CANONICALS_PATH)
    ids = {row.get('canonical_id') for row in canonicals}
    if OLD_CANONICAL in ids:
        raise SystemExit('retired CMS/G1 canonical still exists; refuse artifact retirement')
    if SURVIVOR_CANONICAL not in ids:
        raise SystemExit('CMS/G1 survivor canonical missing; refuse artifact retirement')


def retire_orphan_baseline_answer() -> dict | None:
    if OLD_CANDIDATE_PATH.exists() or OLD_EVIDENCE_PATH.exists():
        raise SystemExit('retired canonical has candidate/evidence state; manual source-first preservation required')
    if not OLD_ANSWER_PATH.exists():
        return None

    text = OLD_ANSWER_PATH.read_text(encoding='utf-8')
    metadata = parse_answer_metadata(text)
    expected = {
        'schema_version': 'answer.v1',
        'canonical_id': OLD_CANONICAL,
        'version': 1,
        'status': 'needs_update',
        'quality_tier': 'long_tail_baseline',
        'generator_version': 'long_tail.v1',
    }
    mismatches = {key: {'expected': value, 'actual': metadata.get(key)} for key, value in expected.items() if metadata.get(key) != value}
    if mismatches:
        raise SystemExit(f'refuse to retire non-default orphan Answer: {mismatches}')

    snapshot = {
        'path': str(OLD_ANSWER_PATH),
        'sha256': hashlib.sha256(text.encode('utf-8')).hexdigest(),
        'metadata': metadata,
        'retirement_class': 'generated_long_tail_baseline_without_candidate_or_evidence',
    }
    OLD_ANSWER_PATH.unlink()
    return snapshot


def main() -> None:
    verify_canonical_consolidation()
    progress = read_json(PROGRESS_PATH)
    if not isinstance(progress, dict) or not isinstance(progress.get('items'), list):
        raise SystemExit('unexpected ReviewProgress schema')

    items = list(progress['items'])
    old_rows = [row for row in items if row.get('canonical_id') == OLD_CANONICAL]
    survivor_rows = [row for row in items if row.get('canonical_id') == SURVIVOR_CANONICAL]
    if len(survivor_rows) != 1:
        raise SystemExit(f'survivor ReviewProgress count must be exactly one, got {len(survivor_rows)}')

    existing_record = read_json(OUT_PATH) if OUT_PATH.exists() else None
    if existing_record and existing_record.get('decision') != 'retired_zero_telemetry_stale_progress':
        raise SystemExit('existing retirement record has unexpected decision')

    retired_progress = None
    if old_rows:
        if len(old_rows) != 1:
            raise SystemExit(f'stale ReviewProgress count must be exactly one, got {len(old_rows)}')
        retired_progress = old_rows[0]
        if not is_zero_real_review(retired_progress):
            raise SystemExit(f'refuse to drop non-default real-review telemetry: {retired_progress}')
        progress['items'] = sorted(
            [row for row in items if row.get('canonical_id') != OLD_CANONICAL],
            key=lambda row: row.get('canonical_id', ''),
        )
        progress['updated_at'] = DATE
        write_json(PROGRESS_PATH, progress)
    elif not existing_record:
        raise SystemExit('stale ReviewProgress absent without retirement record')

    retired_answer = retire_orphan_baseline_answer()
    if existing_record and retired_progress is None and retired_answer is None:
        if not existing_record.get('retired_orphan_answer_snapshot'):
            raise SystemExit('existing retirement record predates orphan Answer retirement but Answer is already absent')
        print('PASS stale Batch 0060 ReviewProgress and orphan baseline Answer already retired')
        return

    survivor = survivor_rows[0]
    record = {
        'schema_version': 'canonical_artifact_retirement.v2',
        'reviewed_at': DATE,
        'retired_canonical_id': OLD_CANONICAL,
        'survivor_canonical_id': SURVIVOR_CANONICAL,
        'decision': 'retired_zero_telemetry_stale_progress',
        'reason': 'Batch 0060 source-first CMS/G1 duplicate normalization retired the legacy canonical. Its ReviewProgress contained no real review telemetry and its formal Answer was only an untouched generated long-tail baseline with no candidate/evidence, so retaining either artifact would violate Canonical referential integrity.',
        'retired_progress_snapshot': retired_progress or existing_record.get('retired_progress_snapshot'),
        'survivor_progress_snapshot': survivor,
        'retired_orphan_answer_snapshot': retired_answer or existing_record.get('retired_orphan_answer_snapshot'),
        'telemetry_preservation': 'No review_count, last_reviewed_at, mistake_count, curated Answer, candidate, or evidence was discarded. Survivor ReviewProgress and survivor Answer artifacts are left unchanged.',
    }
    if not record['retired_progress_snapshot'] or not record['retired_orphan_answer_snapshot']:
        raise SystemExit('retirement audit record would be incomplete')
    write_json(OUT_PATH, record)
    print('PASS retired zero-telemetry stale ReviewProgress and orphan long-tail baseline Answer')


if __name__ == '__main__':
    main()
