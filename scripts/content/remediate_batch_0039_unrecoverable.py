#!/usr/bin/env python3
"""Retire batch-0039 Coding singletons whose actual task contract is not recoverable."""

from __future__ import annotations

import json
from pathlib import Path
import shutil

ROOT = Path('.')

TARGETS = [
    {
        'canonical_id': 'cq_q_9d1fe69784d38442ce450a365ab6f042',
        'question_id': '9d1fe69784d38442ce450a365ab6f042',
        'expected': 'SQL：实现一道开窗函数（Window Function）相关的业务逻辑题',
        'source_note_id': '68386f88000000002101b420',
        'source_note': ROOT / 'note_tagged/68386f88000000002101b420.json',
        'expected_entities': ['sql', 'window function'],
        'explanation': (
            '仓库只保留“实现一道开窗函数（Window Function）相关的业务逻辑题”这一摘要，没有保存业务目标、表结构、字段、'
            '分区键、排序键、窗口 frame、输入输出、样例或期望结果。ROW_NUMBER/RANK、累计和、移动平均、LAG/LEAD 等完全不同的'
            'SQL 都属于 Window Function 题，但 contract 和正确查询不同；因此不能自行选择一种窗口业务逻辑来补全原题。获得更强原始来源前，'
            '该 singleton 无法恢复 strict-valid Coding 答案，应以 incomplete_or_unreadable 记录 fail-closed。'
        ),
    },
    {
        'canonical_id': 'cq_q_9f2a41bf521ace2121a4799543ced3bf',
        'question_id': '9f2a41bf521ace2121a4799543ced3bf',
        'expected': '算法：给定单子信息，寻找最短配送路线（贪心算法实现）',
        'source_note_id': '6680d411000000001e0109af',
        'source_note': ROOT / 'note_tagged/6680d411000000001e0109af.json',
        'expected_entities': ['贪心算法', '路径规划'],
        'explanation': (
            '仓库只保留“给定单子信息，寻找最短配送路线（贪心算法实现）”这一摘要，没有保存订单/站点的数据模型、起终点、距离或时间成本、'
            '容量/时间窗等约束、是否要求全局最优、贪心选择规则、输入输出、样例和 tie-break。最近邻、区间调度、带时间窗配送等都可能被描述为'
            '“贪心配送”，而且一般最短路线问题并不能仅凭任意贪心保证全局最优；因此不能自行制造一个可运行 contract。获得更强原始来源前，'
            '该 singleton 无法恢复 strict-valid Coding 答案，应以 incomplete_or_unreadable 记录 fail-closed。'
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
        print(f'Retired source-unrecoverable batch 0039 singleton: {cid}')

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
