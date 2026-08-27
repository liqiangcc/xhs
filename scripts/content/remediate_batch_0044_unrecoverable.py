#!/usr/bin/env python3
"""Retire the Batch 0044 coding singleton whose actual LeetCode/DP contract is not recoverable."""

from __future__ import annotations

import json
import shutil
from pathlib import Path

ROOT = Path('.')
CID = 'cq_q_b83fcd37847eaf3324471d85ead2a95f'
QID = 'b83fcd37847eaf3324471d85ead2a95f'
EXPECTED = '算法：力扣原题，动态规划。'
SOURCE_NOTE_ID = '65d0ebb0000000000b00f620'
EXPLANATION = (
    '仓库现存原始材料只保留“算法：力扣原题，动态规划。”这一泛化描述；note_desc 仅记录该次小米面试因部门主要使用 Scala、候选人缺少相关经验而挂，'
    '没有补充具体 LeetCode 题号、完整题干、输入输出、约束、样例、期望结果或变形规则。动态规划覆盖大量互不等价的题目，无法从“力扣原题 + 动态规划”'
    '反推出唯一可执行 contract。继续生成某一道 DP 解法会把猜测伪装成原题，因此该 singleton 应以 incomplete_or_unreadable fail-closed，并保留可解释排除原因。'
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
    source_path = ROOT / f'note_tagged/{SOURCE_NOTE_ID}.json'
    desc_path = ROOT / f'note_desc/{SOURCE_NOTE_ID}.txt'
    tagged = read_json(source_path)
    tagged_q = next((q for q in tagged.get('tagged_questions', []) if q.get('question_id') == QID), None)
    if tagged_q is None or tagged_q.get('original_question') != EXPECTED:
        raise SystemExit('exact tagged source wording missing or drifted')
    if tagged_q.get('question_type') != '算法手撕_Coding' or tagged_q.get('tech_entities') != ['动态规划'] or tagged_q.get('is_valid_for_library') is not True:
        raise SystemExit('tagged source taxonomy/validity drifted')
    desc = desc_path.read_text(encoding='utf-8')
    if 'Scala' not in desc or '没有相关经验' not in desc:
        raise SystemExit('note_desc provenance drifted')
    if any(token in desc for token in ['LeetCode', '力扣', '动态规划', '题号', '输入', '输出', '样例']):
        raise SystemExit('note_desc now contains possible problem-contract evidence; manual source-first reassessment required')

    canonical_path = ROOT / 'data/questions/canonical_questions.jsonl'
    question_path = ROOT / 'data/questions/questions.jsonl'
    progress_path = ROOT / 'review/progress.json'
    audit_path = ROOT / 'config/question_validity_audit.json'
    canonicals = read_jsonl(canonical_path)
    questions = read_jsonl(question_path)
    progress = read_json(progress_path)
    audit = read_json(audit_path)

    canonical = next((row for row in canonicals if row.get('canonical_id') == CID), None)
    qrows = [row for row in questions if row.get('question_id') == QID]
    if len(qrows) != 1:
        raise SystemExit(f'expected one Question projection row, got {len(qrows)}')
    qrow = qrows[0]

    if canonical is None:
        if qrow.get('canonical_id') is not None or qrow.get('is_valid_for_library') is not False or qrow.get('exclusion_reason') != 'incomplete_or_unreadable':
            raise SystemExit('already-retired state is inconsistent')
        print('Batch 0044 unrecoverable singleton already retired fail-closed')
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
    print(f'Retired source-unrecoverable batch 0044 singleton: {CID}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
