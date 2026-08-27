#!/usr/bin/env python3
"""Retire batch-0041 singleton questions whose actual interview task contract is not recoverable."""

from __future__ import annotations

import json
from pathlib import Path
import shutil

ROOT = Path('.')

TARGETS = [
    {
        'canonical_id': 'cq_q_a6ed4f0f01d44463de7f8af046ccd001',
        'question_id': 'a6ed4f0f01d44463de7f8af046ccd001',
        'expected': '算法：力扣 Hot 100 题目。',
        'source_note_id': '68c4148e000000001d025dca',
        'source_note': ROOT / 'note_tagged/68c4148e000000001d025dca.json',
        'expected_type': '算法手撕_Coding',
        'expected_entities': [],
        'expected_tagged_valid': True,
        'additional_source': ROOT / 'note_desc/68c4148e000000001d025dca.txt',
        'additional_tokens': ['最后手撕', '力扣hot100', 'hot100困难题变种'],
        'explanation': (
            '仓库原始面经只保留“一面最后手撕力扣 hot100”，二面也只写“hot100 困难题变种”，没有保存具体题号、题干、输入输出、'
            '约束、样例、期望结果或变种规则。Hot 100 中不同题目的 contract 和正确实现完全不同，二面的“困难题变种”也不能反推出是哪道题。'
            '因此不能任选一道 Hot 100 题来伪造原始面试答案；该 singleton 无法恢复 strict-valid Coding 答案，应以 incomplete_or_unreadable fail-closed。'
        ),
    },
    {
        'canonical_id': 'cq_q_a70af552af23eb909cd728cbd46fdbac',
        'question_id': 'a70af552af23eb909cd728cbd46fdbac',
        'expected': '算法实现：求最大收益（类买卖股票的最佳时机）。',
        'source_note_id': '67f91841000000000901700f',
        'source_note': ROOT / 'note_tagged/67f91841000000000901700f.json',
        'expected_type': '算法手撕_Coding',
        'expected_entities': ['动态规划'],
        'expected_tagged_valid': True,
        'additional_source': ROOT / 'note_desc/67f91841000000000901700f.txt',
        'additional_tokens': ['一道最大收益的算法题'],
        'explanation': (
            '仓库原始面经只保留“一道最大收益的算法题”；结构化 Question 中“类买卖股票的最佳时机”和“动态规划”是后续归类摘要，'
            '并没有原始题干来证明交易次数、手续费、冷冻期、持仓限制、输入输出、约束、样例或期望结果。股票 I/II/III/IV、含手续费/冷冻期等题目'
            '都会被概括为“最大收益”，但状态与答案不同。不能把归类推测升级为原始 contract，因此该 singleton 无法恢复 strict-valid Coding 答案，'
            '应以 incomplete_or_unreadable fail-closed。'
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
        if tagged_q.get('question_type') != target['expected_type']:
            raise SystemExit(f'{qid}: source type drifted: {tagged_q.get("question_type")}')
        if tagged_q.get('tech_entities') != target['expected_entities']:
            raise SystemExit(f'{qid}: source entities drifted: {tagged_q.get("tech_entities")}')
        if tagged_q.get('is_valid_for_library') is not target['expected_tagged_valid']:
            raise SystemExit(f'{qid}: tagged source validity drifted: {tagged_q.get("is_valid_for_library")}')
        additional = target['additional_source'].read_text(encoding='utf-8')
        for token in target['additional_tokens']:
            if token not in additional:
                raise SystemExit(f'{qid}: original-note evidence token missing: {token}')

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
        print(f'Retired source-unrecoverable batch 0041 singleton: {cid}')

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
