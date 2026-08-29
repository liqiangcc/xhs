#!/usr/bin/env python3
"""Initialize ReviewProgress for active split-child Canonicals that currently have none.

Independent candidate review is not treated as user oral-review telemetry, so the new
items intentionally start in the same `new` state as an unreviewed Canonical.
"""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path('.')
DATE = '2026-08-29'
TARGETS = [
    'cq_q_88d86d8e4586504b5c9365f4126f7436',
    'cq_q_b66328eb23ca1ba53a062a787c71a9dc',
]


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding='utf-8').splitlines() if line.strip()]


def main() -> int:
    canonical_ids = {row['canonical_id'] for row in read_jsonl(ROOT / 'data/questions/canonical_questions.jsonl')}
    progress_path = ROOT / 'review/progress.json'
    progress = json.loads(progress_path.read_text(encoding='utf-8'))
    items = list(progress.get('items', []))
    by_id = {row.get('canonical_id'): row for row in items}

    added = []
    for cid in TARGETS:
        if cid not in canonical_ids:
            raise SystemExit(f'{cid}: active Canonical missing')
        candidate = ROOT / f'review/candidates/answers/{cid}.md'
        evidence = ROOT / f'review/evidence/{cid}.json'
        if not candidate.exists() or not evidence.exists():
            raise SystemExit(f'{cid}: expected completed candidate/evidence before progress initialization')
        ev = json.loads(evidence.read_text(encoding='utf-8'))
        review = ev.get('review') or {}
        if ev.get('review_state') != 'independent_source_first_review_passed' or review.get('independent') is not True or review.get('decision') != 'pass':
            raise SystemExit(f'{cid}: source-first review evidence not PASS')
        existing = by_id.get(cid)
        if existing is not None:
            # Idempotence is safe only if an actual review still has not been recorded.
            if existing.get('review_count', 0) != 0 or existing.get('last_reviewed_at') is not None:
                raise SystemExit(f'{cid}: ReviewProgress now contains real review telemetry; do not overwrite')
            continue
        item = {
            'canonical_id': cid,
            'confidence': 0.5,
            'difficulty': 3,
            'last_reviewed_at': None,
            'level': 0,
            'mistake_count': 0,
            'next_review_at': DATE,
            'review_count': 0,
            'status': 'new',
            'updated_at': DATE,
        }
        items.append(item)
        by_id[cid] = item
        added.append(cid)

    progress['updated_at'] = DATE
    progress['items'] = sorted(items, key=lambda row: row.get('canonical_id', ''))
    progress_path.write_text(json.dumps(progress, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'ok': True, 'added': added, 'targets': TARGETS, 'real_review_telemetry_added': False}, ensure_ascii=False))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
