#!/usr/bin/env python3
"""Retire batch-0040 Coding singletons whose actual task contract is not recoverable."""

from __future__ import annotations

import json
from pathlib import Path
import shutil

ROOT = Path('.')

TARGETS = [
    {
        'canonical_id': 'cq_q_a53dd025bbdbfb8d46f36e82e4941af1',
        'question_id': 'a53dd025bbdbfb8d46f36e82e4941af1',
        'expected': '算法：自选 LeetCode 中等或困难题目现场完成',
        'source_note_id': '67ac22840000000028036c65',
        'source_note': ROOT / 'note_tagged/67ac22840000000028036c65.json',
        'expected_entities': ['leetcode'],
        'expected_tagged_valid': False,
        'explanation': (
            '仓库原始 tagged source 只保留“自选 LeetCode 中等或困难题目现场完成”，并且该 source row 本身已经标记为 '
            'is_valid_for_library=false；没有保存候选人实际选择的题目、题号、输入输出、约束、样例或期望结果。不同中等/困难题的 '
            'contract 和正确实现完全不同，不能替原始面试记录擅自挑选一道题补全。因此该 singleton 无法恢复 strict-valid Coding 答案，'
            '应以 incomplete_or_unreadable 记录 fail-closed。'
        ),
    },
    {
        'canonical_id': 'cq_q_a64d35ce4f90aa4b9addd876cac99df6',
        'question_id': 'a64d35ce4f90aa4b9addd876cac99df6',
        'expected': 'SQL 实战：编写一个涵盖复杂关联（Join）与时间窗口聚合的大数据查询语句。',
        'source_note_id': '688e4c28000000002501c44a',
        'source_note': ROOT / 'note_tagged/688e4c28000000002501c44a.json',
        'expected_entities': ['sql join', 'time window aggregation'],
        'expected_tagged_valid': True,
        'explanation': (
            '仓库只保留“复杂关联（Join）与时间窗口聚合的大数据查询”这一题型摘要，没有保存业务目标、表结构、字段、关联键、时间字段、'
            '窗口定义、聚合指标、过滤条件、输入输出、样例或期望结果。不同 join grain、窗口边界与指标口径会产生不同且互不等价的 SQL；'
            '不能自行制造 schema 和业务语义来生成一个看似可运行的查询。因此该 singleton 无法恢复 strict-valid Coding 答案，应以 '
            'incomplete_or_unreadable 记录 fail-closed。'
        ),
    },
    {
        'canonical_id': 'cq_q_a65a65d6ea6cb59d8a43c748dff80fa6',
        'question_id': 'a65a65d6ea6cb59d8a43c748dff80fa6',
        'expected': '算法：涉及“状态变换”的复杂题目（推测为动态规划或有限状态自动机相关）',
        'source_note_id': '66e2c6af0000000026031373',
        'source_note': ROOT / 'note_tagged/66e2c6af0000000026031373.json',
        'expected_entities': ['动态规划', '状态机'],
        'expected_tagged_valid': True,
        'explanation': (
            '仓库只保留“涉及状态变换的复杂题目”，且括号中的动态规划/有限状态自动机只是来源记录自己的推测；没有保存状态定义、'
            '转移规则、目标函数、输入输出、约束、样例或期望结果。股票状态机、字符串自动机、区间 DP 等完全不同的问题都可能被这种摘要描述，'
            '不能把推测扩张成具体题目。因此该 singleton 无法恢复 strict-valid Coding 答案，应以 incomplete_or_unreadable 记录 fail-closed。'
        ),
    },
]


def read_json(path: Path):
    return json.loads(path.read_text(encoding='utf-8'))


def write_json(path: Path, value) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def read_jsonl(path: Path):
    return [json.loads(line) for line in path.read_text(encoding='utf-8').splitlines() if line.strip()]


def write_jsonl(path: Path, rows) -> None:
    path.write_text(
        ''.join(json.dumps(row, ensure_ascii=False, sort_keys=True, separators=(',', ':')) + '\n' for row in rows),
        encoding='utf-8',
    )


def main() -> int:
    canonical_path = ROOT / 'data/questions/canonical_questions.jsonl'
    question_path = ROOT / 'data/questions/questions.jsonl'
    progress_path = ROOT / 'review/progress.json'
    audit_path = ROOT / 'config/question_validity_audit.json'

    canonicals = read_jsonl(canonical_path)
    questions = read_jsonl(question_path)
    progress = read_json(progress_path)
    audit = read_json(audit_path)
    decisions = list(audit.get('decisions', []))
    changed = False

    for target in TARGETS:
        cid = target['canonical_id']
        qid = target['question_id']
        expected = target['expected']

        tagged = read_json(target['source_note'])
        tagged_q = next((q for q in tagged.get('tagged_questions', []) if q.get('question_id') == qid), None)
        if tagged_q is None or tagged_q.get('original_question') != expected:
            raise SystemExit(f'{qid}: exact tagged source wording missing or drifted')
        if tagged_q.get('question_type') != '算法手撕_Coding':
            raise SystemExit(f'{qid}: source type drifted: {tagged_q.get("question_type")}')
        if tagged_q.get('tech_entities') != target['expected_entities']:
            raise SystemExit(f'{qid}: source entities drifted: {tagged_q.get("tech_entities")}')
        if tagged_q.get('is_valid_for_library') is not target['expected_tagged_valid']:
            raise SystemExit(f'{qid}: tagged source validity drifted: {tagged_q.get("is_valid_for_library")}')

        canonical = next((row for row in canonicals if row.get('canonical_id') == cid), None)
        rows = [row for row in questions if row.get('question_id') == qid]
        if len(rows) != 1:
            raise SystemExit(f'{qid}: expected one Question projection row, got {len(rows)}')
        row = rows[0]

        if canonical is None:
            if row.get('canonical_id') is not None or row.get('is_valid_for_library') is not False:
                raise SystemExit(f'{qid}: Canonical missing while Question is still active')
            if row.get('exclusion_reason') != 'incomplete_or_unreadable':
                raise SystemExit(f'{qid}: retired Question lacks explainable exclusion reason')
            if (ROOT / 'review/answers' / f'{cid}.md').exists():
                raise SystemExit(f'{qid}: Canonical missing while active Answer remains')
            if any(item.get('canonical_id') == cid for item in progress.get('items', [])):
                raise SystemExit(f'{qid}: Canonical missing while ReviewProgress remains')
            print(f'{qid}: already retired fail-closed')
            continue

        owned = list(canonical.get('question_ids') or [])
        if owned != [qid]:
            raise SystemExit(f'{qid}: expected singleton ownership [{qid}], got {owned}')
        if int(canonical.get('frequency', 0)) != 1:
            raise SystemExit(f'{qid}: expected frequency=1, got {canonical.get("frequency")}')
        if row.get('canonical_id') != cid or row.get('is_valid_for_library') is not True:
            raise SystemExit(f'{qid}: active Question ownership/validity drifted before remediation')
        if row.get('original_question') != expected:
            raise SystemExit(f'{qid}: Question projection wording drifted: {row.get("original_question")!r}')
        if row.get('source_note_id') != target['source_note_id']:
            raise SystemExit(f'{qid}: unexpected source note: {row.get("source_note_id")}')

        candidate = ROOT / 'review/candidates/answers' / f'{cid}.md'
        if candidate.exists():
            raise SystemExit(f'{qid}: candidate exists; do not discard independently staged/reviewed work')

        ref = (row['source_note_id'], row['source_question_index'])
        replacement = {
            'source_note_id': row['source_note_id'],
            'source_question_index': row['source_question_index'],
            'question_id': qid,
            'original_question': row['original_question'],
            'decision': 'exclude',
            'exclusion_reason': 'incomplete_or_unreadable',
            'exclusion_note': target['explanation'],
        }
        found = False
        for index, decision in enumerate(decisions):
            if (decision.get('source_note_id'), decision.get('source_question_index')) == ref:
                decisions[index] = replacement
                found = True
                break
        if not found:
            decisions.append(replacement)

        canonicals = [item for item in canonicals if item.get('canonical_id') != cid]
        before = len(progress.get('items', []))
        progress['items'] = [item for item in progress.get('items', []) if item.get('canonical_id') != cid]
        if len(progress['items']) != before - 1:
            raise SystemExit(f'{qid}: expected exactly one ReviewProgress item to retire')

        active_answer = ROOT / 'review/answers' / f'{cid}.md'
        archived_answer = ROOT / 'review/archive/answers' / f'{cid}.md'
        if not active_answer.exists():
            raise SystemExit(f'{qid}: active long-tail Answer missing')
        archived_answer.parent.mkdir(parents=True, exist_ok=True)
        if archived_answer.exists():
            if archived_answer.read_bytes() != active_answer.read_bytes():
                raise SystemExit(f'{qid}: existing archived Answer differs from active Answer')
            active_answer.unlink()
        else:
            shutil.move(str(active_answer), str(archived_answer))

        changed = True
        print(f'Retired source-unrecoverable batch 0040 singleton: {cid}')

    if not changed:
        return 0

    decisions.sort(key=lambda d: (str(d.get('source_note_id', '')), int(d.get('source_question_index', 0))))
    audit['decisions'] = decisions
    audit['audited_at'] = '2026-08-27'
    audit['include_count'] = sum(1 for d in decisions if d.get('decision') == 'include')
    audit['exclude_count'] = sum(1 for d in decisions if d.get('decision') == 'exclude')
    write_json(audit_path, audit)
    write_jsonl(canonical_path, sorted(canonicals, key=lambda item: item['canonical_id']))
    progress['updated_at'] = '2026-08-27'
    progress['items'] = sorted(progress.get('items', []), key=lambda item: item.get('canonical_id', ''))
    write_json(progress_path, progress)

    return 0


if __name__ == '__main__':
    raise SystemExit(main())
