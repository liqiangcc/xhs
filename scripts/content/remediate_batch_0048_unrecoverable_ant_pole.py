#!/usr/bin/env python3
"""Retire the Batch 0048 ant-on-pole singleton whose executable contract is not recoverable."""

from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

ROOT = Path('.')
DATE = '2026-08-28'
CID = 'cq_q_c6f3f5730684f3da4caf117889166356'
QID = 'c6f3f5730684f3da4caf117889166356'
EXPECTED = '算法：蚂蚁爬杆问题'
NOTE_ID = '66138d03000000001a00e8ca'
TAGGED_BLOB = 'e0836b730a222bac0e24f793270dd5c8fb3dc6b0'
DESC_BLOB = '25e248581a75edf8bc475001c36f67cdebd575fe'
IMAGE_BLOB = '5bf2d292b8fc135182b0adf2ada812f187b88a36'
EXPLANATION = (
    '仓库现存结构化题目和原始图片转写都只保留“蚂蚁爬杆问题”这一题名。'
    '没有杆长、蚂蚁数量与初始位置、方向/速度、相遇或碰撞规则，也没有说明要求最短时间、最长时间、最终位置或其他输出。'
    '“蚂蚁爬杆”存在多种彼此 contract 不兼容的经典变体；任意补出长度、位置、碰撞等条件都会把猜测伪装成原题。'
    '因此该 singleton 必须以 incomplete_or_unreadable fail-closed；保留原始 Question 与可解释 exclusion_note，'
    '但不再保留 Canonical、ReviewProgress 或活动 Answer。'
)


def read_json(path: Path):
    return json.loads(path.read_text(encoding='utf-8'))


def write_json(path: Path, value) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def read_jsonl(path: Path):
    return [json.loads(line) for line in path.read_text(encoding='utf-8').splitlines() if line.strip()]


def write_jsonl(path: Path, rows) -> None:
    path.write_text(''.join(json.dumps(row, ensure_ascii=False, sort_keys=True, separators=(',', ':')) + '\n' for row in rows), encoding='utf-8')


def git_blob(path: Path) -> str:
    return subprocess.check_output(['git', 'hash-object', str(path)], text=True).strip()


def validate_sources() -> None:
    tagged_path = ROOT / f'note_tagged/{NOTE_ID}.json'
    desc_path = ROOT / f'note_desc/{NOTE_ID}.txt'
    image_path = ROOT / f'note_img_txt/{NOTE_ID}.txt'
    if git_blob(tagged_path) != TAGGED_BLOB:
        raise SystemExit('tagged source changed; reassess source-first before exclusion')
    if git_blob(desc_path) != DESC_BLOB:
        raise SystemExit('note_desc changed; reassess source-first before exclusion')
    if git_blob(image_path) != IMAGE_BLOB:
        raise SystemExit('image-text source changed; reassess source-first before exclusion')
    tagged = read_json(tagged_path)
    q = next((x for x in tagged.get('tagged_questions', []) if x.get('question_id') == QID), None)
    if not q or q.get('original_question') != EXPECTED or q.get('question_type') != '算法手撕_Coding' or q.get('is_valid_for_library') is not True:
        raise SystemExit('exact tagged source wording/taxonomy drifted')
    image = image_path.read_text(encoding='utf-8')
    if '32. 蚂蚁爬杆问题' not in image:
        raise SystemExit('exact image-text provenance token missing')
    forbidden_detail_tokens = ['杆长为', '长度为', '蚂蚁数量', '初始位置', '最短时间', '最长时间', '速度为']
    if any(token in image for token in forbidden_detail_tokens):
        raise SystemExit('additional executable ant-pole details appeared; reassess instead of excluding')


def main() -> int:
    validate_sources()
    canonical_path = ROOT / 'data/questions/canonical_questions.jsonl'
    question_path = ROOT / 'data/questions/questions.jsonl'
    progress_path = ROOT / 'review/progress.json'
    audit_path = ROOT / 'config/question_validity_audit.json'
    canonicals = read_jsonl(canonical_path)
    questions = read_jsonl(question_path)
    progress = read_json(progress_path)
    audit = read_json(audit_path)
    decisions = list(audit.get('decisions', []))

    canonical = next((row for row in canonicals if row.get('canonical_id') == CID), None)
    qrows = [row for row in questions if row.get('question_id') == QID]
    if len(qrows) != 1:
        raise SystemExit(f'expected one Question projection row, got {len(qrows)}')
    qrow = qrows[0]

    if canonical is None:
        decision = next((d for d in decisions if d.get('question_id') == QID), None)
        if qrow.get('canonical_id') is not None or qrow.get('is_valid_for_library') is not False or qrow.get('exclusion_reason') != 'incomplete_or_unreadable' or not decision or decision.get('decision') != 'exclude':
            raise SystemExit('already-retired state is inconsistent')
        print('already retired fail-closed')
        return 0

    if list(canonical.get('question_ids') or []) != [QID] or int(canonical.get('frequency', 0)) != 1:
        raise SystemExit(f'expected singleton Canonical ownership, got {canonical.get("question_ids")}')
    if qrow.get('canonical_id') != CID or qrow.get('is_valid_for_library') is not True or qrow.get('original_question') != EXPECTED or qrow.get('source_note_id') != NOTE_ID:
        raise SystemExit('active Question projection drifted')
    candidate = ROOT / f'review/candidates/answers/{CID}.md'
    if candidate.exists():
        raise SystemExit('candidate exists; do not discard independently staged/reviewed work')

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
    audit['audited_at'] = DATE
    audit['include_count'] = sum(1 for d in decisions if d.get('decision') == 'include')
    audit['exclude_count'] = sum(1 for d in decisions if d.get('decision') == 'exclude')
    write_json(audit_path, audit)
    write_jsonl(canonical_path, sorted(canonicals, key=lambda row: row['canonical_id']))
    progress['updated_at'] = DATE
    progress['items'] = sorted(progress.get('items', []), key=lambda row: row.get('canonical_id', ''))
    write_json(progress_path, progress)
    print('Retired source-unrecoverable Batch 0048 ant-pole singleton')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
