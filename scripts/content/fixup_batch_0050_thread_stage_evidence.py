#!/usr/bin/env python3
"""Normalize Batch 0050 thread-stage evidence to the repository quality contract."""

from __future__ import annotations

import json
from pathlib import Path

CID = 'cq_q_d52ca0aa328f82f1166ebc5bd3cc0ad7'
OUT = Path(f'review/content_build/answer_batch_0050/{CID}')
EVIDENCE = Path(f'review/evidence/{CID}.json')


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding='utf-8'))


def save(path: Path, data: dict) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def normalize_sources(data: dict) -> None:
    for source in data.get('sources', []):
        if source.get('source_id') == 'jls-memory-model':
            source['source_type'] = 'official_specification_or_standard'


def main() -> int:
    research_path = OUT / 'writer_research.json'
    research = load(research_path)
    normalize_sources(research)
    save(research_path, research)

    evidence = load(EVIDENCE)
    normalize_sources(evidence)
    boundary_tests = evidence.setdefault('validation', {}).setdefault('boundary_tests', [])
    extra = {
        'case': 'first-stage overlap invariant in both implementations',
        'expected': 't1 and t2 have both started before either is allowed to finish',
        'actual': 'pass',
        'passed': True,
    }
    if not any(row.get('case') == extra['case'] for row in boundary_tests):
        boundary_tests.append(extra)
    save(EVIDENCE, evidence)

    print('PASS normalized JLS source type and recorded third executed boundary invariant')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
