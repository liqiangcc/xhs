#!/usr/bin/env python3
"""Retire the batch-0034 singleton whose coding contract is not recoverable.

Source-first and fail-closed: the repository preserves only a statement that the
programming question involved hash data usage, not the actual input/output task.
Do not manufacture a familiar hash-table problem to satisfy answer coverage.
"""

from __future__ import annotations

import json
from pathlib import Path
import shutil

ROOT = Path('.')
CANONICAL_ID = 'cq_q_7c5bf4177c81ec6f1ac1f79b8738af2c'
QUESTION_ID = '7c5bf4177c81ec6f1ac1f79b8738af2c'
EXPECTED = '编程题：涉及到哈希（Hash）数据应用。 '
SOURCE_NOTE = ROOT / 'note_tagged/663a19f8000000001e03232e.json'
EXPLANATION = (
    '原始 tagged note 只保留“编程题：涉及到哈希（Hash）数据应用。”以及 hash table 标签，'
    '没有保存实际编程题的输入、输出、样例、约束、冲突处理、键值语义或要实现的操作。'
    '两数之和、频次统计、去重、LRU 辅助索引、开放寻址等大量不同题目都可以使用 Hash，'
    '但它们的 contract 和正确实现完全不同；因此不能根据“涉及 Hash”自行补一道熟悉题目。'
    '在获得更强原始来源前，该 singleton 无法恢复 strict-valid Coding 答案，应以可解释的 incomplete_or_unreadable 记录 fail-closed。'
)


def read_json(path: Path):
    return json.loads(path.read_text(encoding='utf-8'))


def write_json(path: Path, value) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def read_jsonl(path: Path):
    return [json.loads(line) for line in path.read_text(encoding='utf-8').splitlines() if line.strip()]


def write_jsonl(path: Path, rows) -> None:
    path.write_text(''.join(json.dumps(row, ensure_ascii=False, sort_keys=True, separators=(',', ':')) + '\n' for row in rows), encoding='utf-8')


def main() -> int:
    tagged = read_json(SOURCE_NOTE)
    tagged_q = next((q for q in tagged.get('tagged_questions', []) if q.get('question_id') == QUESTION_ID), None)
    if tagged_q is None or tagged_q.get('original_question') != EXPECTED:
        raise SystemExit(f'{QUESTION_ID}: exact tagged source wording missing or drifted')
    if tagged_q.get('question_type') != '算法手撕_Coding':
        raise SystemExit(f'{QUESTION_ID}: source type drifted: {tagged_q.get("question_type")}')
    if tagged_q.get('tech_entities') != ['hash table']:
        raise SystemExit(f'{QUESTION_ID}: expected only hash-table entity, got {tagged_q.get("tech_entities")}')

    canonical_path = ROOT / 'data/questions/canonical_questions.jsonl'
    question_path = ROOT / 'data/questions/questions.jsonl'
    progress_path = ROOT / 'review/progress.json'
    audit_path = ROOT / 'config/question_validity_audit.json'

    canonicals = read_jsonl(canonical_path)
    questions = read_jsonl(question_path)
    progress = read_json(progress_path)
    audit = read_json(audit_path)

    canonical = next((row for row in canonicals if row.get('canonical_id') == CANONICAL_ID), None)
    if canonical is None:
        active = [row for row in questions if row.get('question_id') == QUESTION_ID and row.get('canonical_id') == CANONICAL_ID]
        if active:
            raise SystemExit('canonical missing while active Question binding remains')
        if (ROOT / 'review/answers' / f'{CANONICAL_ID}.md').exists():
            raise SystemExit('canonical missing while active Answer remains')
        if any(item.get('canonical_id') == CANONICAL_ID for item in progress.get('items', [])):
            raise SystemExit('canonical missing while ReviewProgress remains')
        print('Batch 0034 hash-only singleton already retired.')
        return 0

    owned = list(canonical.get('question_ids') or [])
    if owned != [QUESTION_ID]:
        raise SystemExit(f'expected singleton ownership [{QUESTION_ID}], got {owned}')
    if int(canonical.get('frequency', 0)) != 1:
        raise SystemExit(f'expected frequency=1, got {canonical.get("frequency")}')

    rows = [row for row in questions if row.get('question_id') == QUESTION_ID]
    if len(rows) != 1:
        raise SystemExit(f'expected one Question row, got {len(rows)}')
    row = rows[0]
    if row.get('canonical_id') != CANONICAL_ID or row.get('is_valid_for_library') is not True:
        raise SystemExit('active Question ownership/validity drifted before remediation')
    if row.get('original_question') != EXPECTED:
        raise SystemExit(f'Question projection wording drifted: {row.get("original_question")!r}')
    if row.get('source_note_id') != '663a19f8000000001e03232e':
        raise SystemExit(f'unexpected source note: {row.get("source_note_id")}')

    ref = (row['source_note_id'], row['source_question_index'])
    replacement = {
        'source_note_id': row['source_note_id'],
        'source_question_index': row['source_question_index'],
        'question_id': QUESTION_ID,
        'original_question': row['original_question'],
        'decision': 'exclude',
        'exclusion_reason': 'incomplete_or_unreadable',
        'exclusion_note': EXPLANATION,
    }
    decisions = list(audit.get('decisions', []))
    found = False
    for index, decision in enumerate(decisions):
        if (decision.get('source_note_id'), decision.get('source_question_index')) == ref:
            decisions[index] = replacement
            found = True
            break
    if not found:
        decisions.append(replacement)

    canonicals = [item for item in canonicals if item.get('canonical_id') != CANONICAL_ID]
    before = len(progress.get('items', []))
    progress['items'] = [item for item in progress.get('items', []) if item.get('canonical_id') != CANONICAL_ID]
    if len(progress['items']) != before - 1:
        raise SystemExit('expected exactly one ReviewProgress item to retire')

    active_answer = ROOT / 'review/answers' / f'{CANONICAL_ID}.md'
    archived_answer = ROOT / 'review/archive/answers' / f'{CANONICAL_ID}.md'
    if not active_answer.exists():
        raise SystemExit('active long-tail Answer missing')
    archived_answer.parent.mkdir(parents=True, exist_ok=True)
    if archived_answer.exists():
        if archived_answer.read_bytes() != active_answer.read_bytes():
            raise SystemExit('existing archived Answer differs from active Answer')
        active_answer.unlink()
    else:
        shutil.move(str(active_answer), str(archived_answer))

    candidate = ROOT / 'review/candidates/answers' / f'{CANONICAL_ID}.md'
    if candidate.exists():
        raise SystemExit('unexpected candidate exists; do not discard reviewed work automatically')

    decisions.sort(key=lambda d: (str(d.get('source_note_id', '')), int(d.get('source_question_index', 0))))
    audit['decisions'] = decisions
    audit['audited_at'] = '2026-08-26'
    audit['include_count'] = sum(1 for d in decisions if d.get('decision') == 'include')
    audit['exclude_count'] = sum(1 for d in decisions if d.get('decision') == 'exclude')
    write_json(audit_path, audit)
    write_jsonl(canonical_path, sorted(canonicals, key=lambda item: item['canonical_id']))
    progress['updated_at'] = '2026-08-26'
    progress['items'] = sorted(progress.get('items', []), key=lambda item: item.get('canonical_id', ''))
    write_json(progress_path, progress)

    print(f'Retired source-unrecoverable batch 0034 singleton: {CANONICAL_ID}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
