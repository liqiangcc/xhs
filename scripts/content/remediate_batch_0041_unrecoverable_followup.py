#!/usr/bin/env python3
"""Retire the remaining batch-0041 singleton questions whose strict task contract is not recoverable."""

from __future__ import annotations

import json
from pathlib import Path
import shutil

ROOT = Path('.')
REVIEW = ROOT / 'review/content_build/answer_batch_0041/recoverability_review.md'

TARGETS = [
    {
        'canonical_id': 'cq_q_a7016342ea74a55c817ed58e69009a64',
        'question_id': 'a7016342ea74a55c817ed58e69009a64',
        'expected': '算法实现：给定原数组为 [a...z]，编写一个简单的 Hash 算法将其映射为新的整数数组？',
        'source_note_id': '67d25ca8000000000b017d2a',
        'source_note': ROOT / 'note_tagged/67d25ca8000000000b017d2a.json',
        'expected_type': '算法手撕_Coding',
        'expected_entities': ['hash算法', '数组处理'],
        'raw_source': ROOT / 'note_desc/67d25ca8000000000b017d2a.txt',
        'raw_tokens': ['拍下来分享给面试java开发岗的各位。'],
        'review_tokens': [
            'cq_q_a7016342ea74a55c817ed58e69009a64',
            'fail closed / source-unrecoverable',
            'hash-table size/modulus',
            'strict-valid Coding answer cannot choose one mapping without fabricating the original task',
        ],
        'explanation': (
            '仓库保留的结构化题面只说把 [a...z] 通过“简单 Hash 算法”映射为整数数组；原始 note_desc 只有帖子说明，'
            '没有恢复哈希函数、表大小/模数、输出长度、碰撞规则、期望映射值、样例或可执行 oracle。序号编码、字符串哈希、'
            'Java 风格 hashCode 或桶下标等多种互不等价 contract 都符合现有文字，因此不能任选一种映射冒充原题。'
            'source-first recoverability review 已判定该 singleton 无法形成 strict-valid Coding 答案，应以 incomplete_or_unreadable fail-closed。'
        ),
    },
    {
        'canonical_id': 'cq_q_a811de1b146bd3b47f2f7ca524ac1c3b',
        'question_id': 'a811de1b146bd3b47f2f7ca524ac1c3b',
        'expected': '算法：手撕去重链表（Remove Duplicates from Sorted List），使用双指针实现。',
        'source_note_id': '67eb383d000000001c01d8fc',
        'source_note': ROOT / 'note_tagged/67eb383d000000001c01d8fc.json',
        'expected_type': '算法手撕_Coding',
        'expected_entities': ['链表', '双指针', '去重'],
        'raw_source': ROOT / 'note_desc/67eb383d000000001c01d8fc.txt',
        'raw_tokens': ['很简单的去重链表重复元素。（双指针）'],
        'review_tokens': [
            'cq_q_a811de1b146bd3b47f2f7ca524ac1c3b',
            'fail closed / source-unrecoverable',
            'Remove Duplicates from Sorted List',
            'raw source does not establish whether the list is sorted',
        ],
        'explanation': (
            '仓库原始面经只保留“很简单的去重链表重复元素。（双指针）”。后续 normalized Question 增加了 '
            '“Remove Duplicates from Sorted List”/有序链表身份，但原始文本没有证明链表有序，也没有说明是重复值保留一个还是全部删除、'
            '重复是否可能不相邻、返回值/原地修改 contract。多种不同链表题都符合原文，缺失语义会直接改变正确算法。'
            '因此不能把后续归一化标题升级为原始题面；source-first recoverability review 判定该 singleton 无法形成 strict-valid Coding 答案，'
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
    review_text = REVIEW.read_text(encoding='utf-8')
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
        if tagged_q.get('is_valid_for_library') is not True:
            raise SystemExit(f'{qid}: tagged source validity drifted')
        raw = target['raw_source'].read_text(encoding='utf-8')
        for token in target['raw_tokens']:
            if token not in raw:
                raise SystemExit(f'{qid}: original-note evidence token missing: {token}')
        for token in target['review_tokens']:
            if token not in review_text:
                raise SystemExit(f'{qid}: frozen recoverability-review token missing: {token}')

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

        if list(canonical.get('question_ids') or []) != [qid]:
            raise SystemExit(f'{qid}: expected singleton Canonical ownership')
        if int(canonical.get('frequency', 0)) != 1:
            raise SystemExit(f'{qid}: expected frequency=1')
        if row.get('canonical_id') != cid or row.get('is_valid_for_library') is not True:
            raise SystemExit(f'{qid}: active Question ownership/validity drifted before remediation')
        if row.get('original_question') != expected or row.get('source_note_id') != target['source_note_id']:
            raise SystemExit(f'{qid}: active Question source projection drifted')
        if (ROOT / 'review/candidates/answers' / f'{cid}.md').exists():
            raise SystemExit(f'{qid}: candidate exists; refuse to discard reviewed/staged work')

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
        for index, decision in enumerate(decisions):
            if (decision.get('source_note_id'), decision.get('source_question_index')) == ref:
                decisions[index] = replacement
                break
        else:
            decisions.append(replacement)

        canonicals = [item for item in canonicals if item.get('canonical_id') != cid]
        before = len(progress.get('items', []))
        progress['items'] = [item for item in progress.get('items', []) if item.get('canonical_id') != cid]
        if len(progress['items']) != before - 1:
            raise SystemExit(f'{qid}: expected exactly one ReviewProgress item to retire')

        active_answer = ROOT / 'review/answers' / f'{cid}.md'
        archived_answer = ROOT / 'review/archive/answers' / f'{cid}.md'
        if not active_answer.exists():
            raise SystemExit(f'{qid}: active long-tail baseline Answer missing')
        archived_answer.parent.mkdir(parents=True, exist_ok=True)
        if archived_answer.exists():
            if archived_answer.read_bytes() != active_answer.read_bytes():
                raise SystemExit(f'{qid}: existing archived Answer differs from active Answer')
            active_answer.unlink()
        else:
            shutil.move(str(active_answer), str(archived_answer))

        changed = True
        print(f'Retired remaining source-unrecoverable batch 0041 singleton: {cid}')

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
