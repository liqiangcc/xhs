#!/usr/bin/env python3
"""Retire the batch-0034 SQL singleton whose concrete query contract is not recoverable.

Source-first and fail-closed: the repository preserves only a generic request to
write a SQL query involving complex window aggregation and a large-table join.
It does not preserve the schema, keys, target metric, grouping/window semantics,
dialect, samples, expected rows, or scale/skew contract needed for a strict-valid
Coding answer. Do not manufacture a familiar analytics query to satisfy coverage.
"""

from __future__ import annotations

import json
from pathlib import Path
import shutil

ROOT = Path('.')
CANONICAL_ID = 'cq_q_7d04809b2086ccc4aa1ff84aa977aa3e'
QUESTION_ID = '7d04809b2086ccc4aa1ff84aa977aa3e'
EXPECTED = 'SQL 实战：编写涵盖复杂窗口聚合与大表关联的大数据查询语句。'
SOURCE_NOTE = ROOT / 'note_tagged/6890a2a7000000002501b027.json'
EXPLANATION = (
    '原始 tagged note 只保留“SQL 实战：编写涵盖复杂窗口聚合与大表关联的大数据查询语句。”、'
    'sql window functions/join 标签和“业务指标统计”场景，没有保存实际表结构、关联键、目标指标、'
    '过滤条件、聚合口径、窗口 PARTITION/ORDER 规则、期望输出、样例、SQL 方言、数据规模或倾斜约束。'
    '用户留存、TopN、累计指标、去重、会话化等大量不同查询都可以同时使用窗口函数和大表 JOIN，'
    '但它们的输入、输出、正确 SQL 与性能边界完全不同；因此不能根据这些泛化标签自行补一道熟悉 SQL 题。'
    '在获得更强原始来源前，该 singleton 无法恢复 strict-valid Coding 答案，应以可解释的 incomplete_or_unreadable 记录 fail-closed。'
)


def read_json(path: Path):
    return json.loads(path.read_text(encoding='utf-8'))


def write_json(path: Path, value) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def read_jsonl(path: Path):
    return [json.loads(line) for line in path.read_text(encoding='utf-8').splitlines() if line.strip()]


def write_jsonl(path: Path, rows) -> None:
    path.write_text(
        ''.join(
            json.dumps(row, ensure_ascii=False, sort_keys=True, separators=(',', ':')) + '\n'
            for row in rows
        ),
        encoding='utf-8',
    )


def main() -> int:
    tagged = read_json(SOURCE_NOTE)
    tagged_q = next((q for q in tagged.get('tagged_questions', []) if q.get('question_id') == QUESTION_ID), None)
    if tagged_q is None or tagged_q.get('original_question') != EXPECTED:
        raise SystemExit(f'{QUESTION_ID}: exact tagged source wording missing or drifted')
    if tagged_q.get('question_type') != '算法手撕_Coding':
        raise SystemExit(f'{QUESTION_ID}: source type drifted: {tagged_q.get("question_type")}')
    if tagged_q.get('tech_entities') != ['sql window functions', 'join']:
        raise SystemExit(f'{QUESTION_ID}: expected only window/join entities, got {tagged_q.get("tech_entities")}')
    if tagged_q.get('business_context') != ['业务指标统计']:
        raise SystemExit(f'{QUESTION_ID}: business context drifted: {tagged_q.get("business_context")}')

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
        active = [
            row for row in questions
            if row.get('question_id') == QUESTION_ID and row.get('canonical_id') == CANONICAL_ID
        ]
        if active:
            raise SystemExit('canonical missing while active Question binding remains')
        if (ROOT / 'review/answers' / f'{CANONICAL_ID}.md').exists():
            raise SystemExit('canonical missing while active Answer remains')
        if any(item.get('canonical_id') == CANONICAL_ID for item in progress.get('items', [])):
            raise SystemExit('canonical missing while ReviewProgress remains')
        print('Batch 0034 generic SQL singleton already retired.')
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
    if row.get('source_note_id') != '6890a2a7000000002501b027':
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

    print(f'Retired source-unrecoverable batch 0034 SQL singleton: {CANONICAL_ID}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
