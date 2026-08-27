#!/usr/bin/env python3
"""Retire the Batch 0045 singleton whose three SQL coding contracts are not recoverable."""

from __future__ import annotations

import json
import shutil
from pathlib import Path

ROOT = Path('.')
CID = 'cq_q_bacead7768fb94e10596031ff77a5c72'
QID = 'bacead7768fb94e10596031ff77a5c72'
EXPECTED = '算法：三个sql'
SOURCE_NOTE_ID = '67f7b754000000001d01c99b'
EXPLANATION = (
    '仓库现存源材料对该手撕环节只保留“手撕 / 三个sql / leetcode253 会议室”这一上下文；'
    'note_structured 与 note_tagged 均只把本题保存为“算法：三个sql”，没有三个 SQL 的任何具体题干、表结构、字段、'
    '输入数据、查询目标、过滤/聚合/排序约束、期望结果或数据库方言。仅凭“3 个 SQL”无法唯一还原任意一个可执行查询 contract；'
    '继续生成 JOIN、GROUP BY、窗口函数等具体 SQL 会把通用模板或猜测伪装成原题，因此该 singleton 应以 '
    'incomplete_or_unreadable fail-closed，并保留明确可解释的排除原因。'
)


def read_json(path: Path):
    return json.loads(path.read_text(encoding='utf-8'))


def write_json(path: Path, value) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def read_jsonl(path: Path):
    return [json.loads(line) for line in path.read_text(encoding='utf-8').splitlines() if line.strip()]


def write_jsonl(path: Path, rows) -> None:
    path.write_text(''.join(json.dumps(row, ensure_ascii=False, sort_keys=True, separators=(',', ':')) + '\n' for row in rows), encoding='utf-8')


def all_strings(value):
    if isinstance(value, str):
        yield value
    elif isinstance(value, list):
        for item in value:
            yield from all_strings(item)
    elif isinstance(value, dict):
        for item in value.values():
            yield from all_strings(item)


def main() -> int:
    tagged_path = ROOT / f'note_tagged/{SOURCE_NOTE_ID}.json'
    structured_path = ROOT / f'note_structured/{SOURCE_NOTE_ID}.json'
    raw_path = ROOT / f'note_json/{SOURCE_NOTE_ID}.json'
    tagged = read_json(tagged_path)
    structured = read_json(structured_path)
    raw = read_json(raw_path)

    tagged_q = next((q for q in tagged.get('tagged_questions', []) if q.get('question_id') == QID), None)
    if tagged_q is None or tagged_q.get('original_question') != EXPECTED:
        raise SystemExit('exact tagged source wording missing or drifted')
    if tagged_q.get('question_type') != '算法手撕_Coding' or tagged_q.get('tech_entities') != ['sql查询'] or tagged_q.get('is_valid_for_library') is not True:
        raise SystemExit('tagged source taxonomy/validity drifted')
    questions = structured.get('questions', [])
    if EXPECTED not in questions or '算法：leetcode253 会议室' not in questions:
        raise SystemExit('structured source context drifted')

    raw_mentions = [s for s in all_strings(raw) if '三个sql' in s.lower()]
    if not raw_mentions:
        raise SystemExit('raw note no longer contains the preserved three-SQL wording')
    if not any('手撕' in s and 'leetcode253' in s.lower() for s in raw_mentions):
        raise SystemExit('raw note hand-coding context drifted; manual source-first reassessment required')
    contract_tokens = ['select ', ' from ', ' join ', ' where ', ' group by ', ' having ', ' order by ', '表结构', '字段名', '查询出', '统计出']
    for text in raw_mentions:
        normalized = ' ' + text.lower().replace('\n', ' ') + ' '
        # The note can mention unrelated MySQL concepts elsewhere; only the string that actually contains
        # “三个sql” is relevant. If that same source string later gains a concrete SQL contract, stop.
        if any(token in normalized for token in contract_tokens):
            raise SystemExit('raw source now contains possible SQL-contract evidence; manual source-first reassessment required')

    canonical_path = ROOT / 'data/questions/canonical_questions.jsonl'
    question_path = ROOT / 'data/questions/questions.jsonl'
    progress_path = ROOT / 'review/progress.json'
    audit_path = ROOT / 'config/question_validity_audit.json'
    canonicals = read_jsonl(canonical_path)
    projected_questions = read_jsonl(question_path)
    progress = read_json(progress_path)
    audit = read_json(audit_path)

    canonical = next((row for row in canonicals if row.get('canonical_id') == CID), None)
    qrows = [row for row in projected_questions if row.get('question_id') == QID]
    if len(qrows) != 1:
        raise SystemExit(f'expected one Question projection row, got {len(qrows)}')
    qrow = qrows[0]

    if canonical is None:
        if qrow.get('canonical_id') is not None or qrow.get('is_valid_for_library') is not False or qrow.get('exclusion_reason') != 'incomplete_or_unreadable':
            raise SystemExit('already-retired state is inconsistent')
        print('Batch 0045 unrecoverable SQL singleton already retired fail-closed')
        return 0

    if list(canonical.get('question_ids') or []) != [QID] or int(canonical.get('frequency', 0)) != 1:
        raise SystemExit(f'expected singleton Canonical ownership, got {canonical.get("question_ids")} frequency={canonical.get("frequency")}')
    if qrow.get('canonical_id') != CID or qrow.get('is_valid_for_library') is not True or qrow.get('original_question') != EXPECTED or qrow.get('source_note_id') != SOURCE_NOTE_ID:
        raise SystemExit('active Question projection drifted')
    candidate = ROOT / f'review/candidates/answers/{CID}.md'
    if candidate.exists():
        raise SystemExit('candidate exists; do not discard independently staged/reviewed work')

    decisions = list(audit.get('decisions', []))
    replacement = {
        'source_note_id': qrow['source_note_id'],
        'source_question_index': qrow['source_question_index'],
        'question_id': QID,
        'original_question': qrow['original_question'],
        'decision': 'exclude',
        'exclusion_reason': 'incomplete_or_unreadable',
        'exclusion_note': EXPLANATION,
    }
    ref = (qrow['source_note_id'], qrow['source_question_index'])
    for i, decision in enumerate(decisions):
        if (decision.get('source_note_id'), decision.get('source_question_index')) == ref:
            decisions[i] = replacement
            break
    else:
        decisions.append(replacement)

    canonicals = [row for row in canonicals if row.get('canonical_id') != CID]
    before = len(progress.get('items', []))
    progress['items'] = [row for row in progress.get('items', []) if row.get('canonical_id') != CID]
    if len(progress['items']) != before - 1:
        raise SystemExit('expected exactly one ReviewProgress item to retire')

    active_answer = ROOT / f'review/answers/{CID}.md'
    archived_answer = ROOT / f'review/archive/answers/{CID}.md'
    if not active_answer.exists():
        raise SystemExit('active long-tail baseline Answer missing')
    archived_answer.parent.mkdir(parents=True, exist_ok=True)
    if archived_answer.exists():
        if archived_answer.read_bytes() != active_answer.read_bytes():
            raise SystemExit('existing archived Answer differs from active Answer')
        active_answer.unlink()
    else:
        shutil.move(str(active_answer), str(archived_answer))

    decisions.sort(key=lambda d: (str(d.get('source_note_id', '')), int(d.get('source_question_index', 0))))
    audit['decisions'] = decisions
    audit['audited_at'] = '2026-08-28'
    audit['include_count'] = sum(1 for d in decisions if d.get('decision') == 'include')
    audit['exclude_count'] = sum(1 for d in decisions if d.get('decision') == 'exclude')
    write_json(audit_path, audit)
    write_jsonl(canonical_path, sorted(canonicals, key=lambda row: row['canonical_id']))
    progress['updated_at'] = '2026-08-28'
    progress['items'] = sorted(progress.get('items', []), key=lambda row: row.get('canonical_id', ''))
    write_json(progress_path, progress)
    print(f'Retired source-unrecoverable batch 0045 SQL singleton: {CID}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
