#!/usr/bin/env python3
"""Retire the stale ReviewProgress row left by Batch 0060 CMS/G1 canonical consolidation.

The source-first normalization merged legacy canonical
cq_q_7960226d99224c6c8d4411110ff10c8b into survivor
cq_q_d3fea003c007b50735b8e695473de9ac.  ReviewProgress is keyed by
canonical_id, so the retired canonical must not remain in review/progress.json.

This remediation is intentionally conservative: it only removes the stale row
when it contains zero real-review telemetry.  Any non-default historical review
state is treated as a hard stop instead of silently discarding evidence.
"""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path('.')
PROGRESS_PATH = ROOT / 'review/progress.json'
OUT_PATH = ROOT / 'review/content_build/answer_batch_0060/stale_review_progress_retirement.json'
OLD_CANONICAL = 'cq_q_7960226d99224c6c8d4411110ff10c8b'
SURVIVOR_CANONICAL = 'cq_q_d3fea003c007b50735b8e695473de9ac'
DATE = '2026-08-30'


def read_json(path: Path):
    return json.loads(path.read_text(encoding='utf-8'))


def write_json(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def is_zero_real_review(row: dict) -> bool:
    return (
        row.get('status') == 'new'
        and row.get('review_count') == 0
        and row.get('last_reviewed_at') is None
        and row.get('mistake_count') == 0
    )


def main() -> None:
    progress = read_json(PROGRESS_PATH)
    if not isinstance(progress, dict) or not isinstance(progress.get('items'), list):
        raise SystemExit('unexpected ReviewProgress schema')

    items = list(progress['items'])
    old_rows = [row for row in items if row.get('canonical_id') == OLD_CANONICAL]
    survivor_rows = [row for row in items if row.get('canonical_id') == SURVIVOR_CANONICAL]

    if len(survivor_rows) != 1:
        raise SystemExit(f'survivor ReviewProgress count must be exactly one, got {len(survivor_rows)}')

    if not old_rows:
        if OUT_PATH.exists():
            record = read_json(OUT_PATH)
            if record.get('decision') != 'retired_zero_telemetry_stale_progress':
                raise SystemExit('existing retirement record has unexpected decision')
            print('PASS stale Batch 0060 ReviewProgress already retired')
            return
        raise SystemExit('stale ReviewProgress absent without retirement record')

    if len(old_rows) != 1:
        raise SystemExit(f'stale ReviewProgress count must be exactly one, got {len(old_rows)}')

    old = old_rows[0]
    survivor = survivor_rows[0]
    if not is_zero_real_review(old):
        raise SystemExit(f'refuse to drop non-default real-review telemetry: {old}')

    progress['items'] = sorted(
        [row for row in items if row.get('canonical_id') != OLD_CANONICAL],
        key=lambda row: row.get('canonical_id', ''),
    )
    progress['updated_at'] = DATE
    write_json(PROGRESS_PATH, progress)

    record = {
        'schema_version': 'review_progress_retirement.v1',
        'reviewed_at': DATE,
        'retired_canonical_id': OLD_CANONICAL,
        'survivor_canonical_id': SURVIVOR_CANONICAL,
        'decision': 'retired_zero_telemetry_stale_progress',
        'reason': 'Batch 0060 source-first CMS/G1 duplicate normalization retired the legacy canonical; its ReviewProgress row contained no real review telemetry, so keeping it would violate ReviewProgress-to-Canonical referential integrity.',
        'retired_progress_snapshot': old,
        'survivor_progress_snapshot': survivor,
        'telemetry_preservation': 'No review_count, last_reviewed_at, mistake_count, or non-new status was discarded. Survivor ReviewProgress is left unchanged.',
    }
    write_json(OUT_PATH, record)
    print('PASS retired zero-telemetry stale Batch 0060 ReviewProgress row')


if __name__ == '__main__':
    main()
