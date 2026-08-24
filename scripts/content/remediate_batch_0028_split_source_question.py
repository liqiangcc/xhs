#!/usr/bin/env python3
"""Split the mixed Answer Batch 0028 source row into two source-exact Questions.

The frozen source packet proves that one legacy tagged Question merged an algorithm
question (decimal string addition) and an unrelated SQL question. This slice repairs
only that source/data ownership boundary. It deliberately creates two candidate
Canonicals with answer_status=missing and performs no answer promotion or relation
merge. Fresh dedup relation discovery must run after this split lands.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
import shutil

ROOT = Path('.')
NOTE_PATH = ROOT / 'note_tagged/680859e1000000000f032ec6.json'
CANONICAL_PATH = ROOT / 'data/questions/canonical_questions.jsonl'
QUESTION_PATH = ROOT / 'data/questions/questions.jsonl'
PROGRESS_PATH = ROOT / 'review/progress.json'
AUDIT_PATH = ROOT / 'config/question_validity_audit.json'
TASK_PATH = ROOT / 'tasks/answer-batches/TASK-20260711-0313-answer-batch-0028.md'
SOURCE_PACKET_PATH = ROOT / 'review/reports/ANSWER_BATCH_0028_SOURCE_PACKET.json'
BOUNDARY_PATH = ROOT / 'review/content_build/answer_batch_0028/source_boundary_audit.md'

SOURCE_NOTE_ID = '680859e1000000000f032ec6'
SOURCE_INDEX = 6
OLD_QID = '5f1aa586172b1a82ebb8cdd65fb6927b'
OLD_CANONICAL = f'cq_q_{OLD_QID}'
OLD_TEXT = '算法与 SQL：1) 大数加法（字符串模拟）；2) SQL 查询学生学号、姓名及其所有课程的平均成绩（涉及 JOIN 与 GROUP BY）'
SPLITS = [
    {
        'text': '大数加法：给两个字符串，返回两个字符串的和，并以字符串形式返回，时间复杂度 O(n)；例如 "787"+"350"="1137"，"321"+""="321"',
        'qid': '37b2536da54c5df189dbb86c55a6bfa3',
        'domain': {'l1': '算法', 'l2': '字符串'},
        'entities': ['big number addition'],
        'question_type': '算法手撕_Coding',
    },
    {
        'text': 'SQL：从学生表和成绩表中，查询学生学号、姓名、平均成绩',
        'qid': 'e9c5bb8468fd0b37bd3f0abf72df80aa',
        'domain': {'l1': '数据库', 'l2': 'MySQL'},
        'entities': ['SQL'],
        'question_type': '算法手撕_Coding',
    },
]
for item in SPLITS:
    item['canonical_id'] = f"cq_q_{item['qid']}"


def normalize(text: str) -> str:
    return re.sub(r'[^\w\u4e00-\u9fa5]', '', str(text).lower())


def question_id(text: str) -> str:
    return hashlib.md5(normalize(text).encode('utf-8')).hexdigest()


def read_json(path: Path):
    return json.loads(path.read_text(encoding='utf-8'))


def write_json(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def read_jsonl(path: Path):
    return [json.loads(line) for line in path.read_text(encoding='utf-8').splitlines() if line.strip()]


def write_jsonl(path: Path, rows) -> None:
    path.write_text(
        ''.join(json.dumps(row, ensure_ascii=False, sort_keys=True, separators=(',', ':')) + '\n' for row in rows),
        encoding='utf-8',
    )


def verify_frozen_evidence() -> None:
    packet = read_json(SOURCE_PACKET_PATH)
    if packet.get('schema_version') != 'answer_batch_source_packet.v2' or packet.get('batch') != '0028':
        raise SystemExit('unexpected batch 0028 source packet identity')
    entry = next((row for row in packet.get('canonicals') or [] if row.get('canonical_id') == OLD_CANONICAL), None)
    if not entry or len(entry.get('source_hits') or []) != 1:
        raise SystemExit('mixed batch 0028 Canonical no longer has exactly one frozen source hit')
    hit = entry['source_hits'][0]
    if hit.get('note_id') != SOURCE_NOTE_ID:
        raise SystemExit('mixed batch 0028 source note drifted')
    caption = str(hit.get('note_desc') or '')
    required_fragments = [
        '大数加法，给两个字符串，返回两个字符串的和，并以字符串的形式返回',
        '时间复杂度O(n)',
        '"787"+"350"="1137"',
        '"321"+""=321',
        'SQL题',
        '从学生表和成绩表中，查询学生学号、姓名、平均成绩',
    ]
    missing = [fragment for fragment in required_fragments if fragment not in caption]
    if missing:
        raise SystemExit(f'frozen source does not preserve required split fragments: {missing}')
    boundary = BOUNDARY_PATH.read_text(encoding='utf-8')
    if f'| `{OLD_CANONICAL}` | split source Question before authoring |' not in boundary:
        raise SystemExit('frozen batch 0028 boundary no longer requires the mixed source split')


def split_source_row() -> None:
    for item in SPLITS:
        actual = question_id(item['text'])
        if actual != item['qid']:
            raise SystemExit(f"unexpected normalized id for {item['text']}: {actual}")

    note = read_json(NOTE_PATH)
    if note.get('note_id') != SOURCE_NOTE_ID:
        raise SystemExit(f"unexpected source note id: {note.get('note_id')}")
    tagged = list(note.get('tagged_questions') or [])
    old_matches = [i for i, row in enumerate(tagged) if row.get('question_id') == OLD_QID or row.get('original_question') == OLD_TEXT]
    new_ids = {item['qid'] for item in SPLITS}
    split_matches = [row for row in tagged if row.get('question_id') in new_ids]

    if old_matches:
        if len(old_matches) != 1 or split_matches:
            raise SystemExit('legacy and split tagged Questions coexist unexpectedly')
        index = old_matches[0]
        if index != SOURCE_INDEX or index != len(tagged) - 1:
            raise SystemExit(f'legacy source row drifted from expected final index {SOURCE_INDEX}: {index}')
        legacy = tagged[index]
        if legacy.get('original_question') != OLD_TEXT:
            raise SystemExit(f"legacy source text drifted: {legacy.get('original_question')!r}")
        replacements = []
        for item in SPLITS:
            row = dict(legacy)
            row['question_id'] = item['qid']
            row['original_question'] = item['text']
            row['domain'] = dict(item['domain'])
            row['question_type'] = item['question_type']
            row['tech_entities'] = list(item['entities'])
            row['business_context'] = []
            row['is_valid_for_library'] = True
            row.pop('invalid_reason', None)
            replacements.append(row)
        tagged[index:index + 1] = replacements
        note['tagged_questions'] = tagged
        write_json(NOTE_PATH, note)
    else:
        if len(split_matches) != 2:
            raise SystemExit('expected legacy mixed row or exactly two split source rows')
        ordered = tagged[SOURCE_INDEX:SOURCE_INDEX + 2]
        if [row.get('question_id') for row in ordered] != [item['qid'] for item in SPLITS]:
            raise SystemExit('split source Questions are not at expected final indexes')
        if [row.get('original_question') for row in ordered] != [item['text'] for item in SPLITS]:
            raise SystemExit('split source Question text drifted')


def replace_canonical_ownership() -> None:
    canonicals = read_jsonl(CANONICAL_PATH)
    by_id = {row.get('canonical_id'): row for row in canonicals}
    old = by_id.get(OLD_CANONICAL)
    existing_new = [by_id.get(item['canonical_id']) for item in SPLITS if by_id.get(item['canonical_id'])]
    if old is not None:
        if existing_new:
            raise SystemExit('legacy mixed Canonical and split Canonicals coexist unexpectedly')
        if list(old.get('question_ids') or []) != [OLD_QID] or int(old.get('frequency', 0)) != 1:
            raise SystemExit('legacy mixed Canonical is not expected singleton')
        canonicals = [row for row in canonicals if row.get('canonical_id') != OLD_CANONICAL]
        for item in SPLITS:
            record = dict(old)
            record['canonical_id'] = item['canonical_id']
            record['canonical_title'] = item['text']
            record['aliases'] = [item['text']]
            record['question_ids'] = [item['qid']]
            record['primary_entities'] = list(item['entities'])
            record['frequency'] = 1
            record['answer_status'] = 'missing'
            canonicals.append(record)
        write_jsonl(CANONICAL_PATH, sorted(canonicals, key=lambda row: row['canonical_id']))
    else:
        if len(existing_new) != 2:
            raise SystemExit('legacy mixed Canonical absent without both split Canonicals')
        for item in SPLITS:
            record = by_id[item['canonical_id']]
            if list(record.get('question_ids') or []) != [item['qid']] or record.get('canonical_title') != item['text']:
                raise SystemExit(f"split Canonical drifted: {item['canonical_id']}")


def retire_legacy_review_state() -> None:
    progress = read_json(PROGRESS_PATH)
    if isinstance(progress, dict) and isinstance(progress.get('items'), list):
        old_items = [row for row in progress['items'] if row.get('canonical_id') == OLD_CANONICAL]
        if old_items:
            if len(old_items) != 1:
                raise SystemExit(f'expected one legacy ReviewProgress item, got {len(old_items)}')
            progress['items'] = [row for row in progress['items'] if row.get('canonical_id') != OLD_CANONICAL]
            progress['updated_at'] = '2026-08-25'
            progress['items'] = sorted(progress['items'], key=lambda row: row.get('canonical_id', ''))
            write_json(PROGRESS_PATH, progress)
    elif isinstance(progress, list):
        progress[:] = [row for row in progress if row.get('canonical_id') != OLD_CANONICAL]
        write_json(PROGRESS_PATH, progress)
    elif isinstance(progress, dict):
        if OLD_CANONICAL in progress:
            progress.pop(OLD_CANONICAL)
            write_json(PROGRESS_PATH, progress)

    active_answer = ROOT / 'review/answers' / f'{OLD_CANONICAL}.md'
    archive_answer = ROOT / 'review/archive/answers' / f'{OLD_CANONICAL}.md'
    archive_answer.parent.mkdir(parents=True, exist_ok=True)
    if active_answer.exists():
        if archive_answer.exists():
            if archive_answer.read_bytes() != active_answer.read_bytes():
                raise SystemExit('existing legacy mixed Answer archive differs from active Answer')
            active_answer.unlink()
        else:
            shutil.move(str(active_answer), str(archive_answer))
    elif not archive_answer.exists():
        raise SystemExit('legacy mixed Answer is neither active nor archived')

    for base in [ROOT / 'review/candidates/answers', ROOT / 'review/evidence/answers']:
        item = base / f'{OLD_CANONICAL}.md'
        if item.exists():
            archive_base = ROOT / 'review/archive' / base.relative_to(ROOT / 'review')
            archive_base.mkdir(parents=True, exist_ok=True)
            destination = archive_base / item.name
            if destination.exists() and destination.read_bytes() != item.read_bytes():
                raise SystemExit(f'conflicting archived review artifact: {destination}')
            if destination.exists():
                item.unlink()
            else:
                shutil.move(str(item), str(destination))


def preserve_validity_audit() -> None:
    audit = read_json(AUDIT_PATH)
    decisions = list(audit.get('decisions') or [])
    at_source = [d for d in decisions if d.get('source_note_id') == SOURCE_NOTE_ID and d.get('source_question_index') == SOURCE_INDEX]
    if not at_source:
        return
    if len(at_source) != 1 or at_source[0].get('decision') != 'include':
        raise SystemExit('unexpected validity-audit state for legacy mixed Question')
    first = at_source[0]
    first.update({
        'question_id': SPLITS[0]['qid'],
        'original_question': SPLITS[0]['text'],
        'exclusion_reason': None,
        'exclusion_note': None,
    })
    second_at_source = [d for d in decisions if d.get('source_note_id') == SOURCE_NOTE_ID and d.get('source_question_index') == SOURCE_INDEX + 1]
    if not second_at_source:
        decisions.append({
            'source_note_id': SOURCE_NOTE_ID,
            'source_question_index': SOURCE_INDEX + 1,
            'question_id': SPLITS[1]['qid'],
            'original_question': SPLITS[1]['text'],
            'decision': 'include',
            'exclusion_reason': None,
            'exclusion_note': None,
        })
    elif len(second_at_source) != 1 or second_at_source[0].get('question_id') != SPLITS[1]['qid']:
        raise SystemExit('unexpected validity-audit state for second split Question')
    decisions.sort(key=lambda d: (str(d.get('source_note_id', '')), int(d.get('source_question_index', 0))))
    audit['decisions'] = decisions
    audit['audited_at'] = '2026-08-25'
    audit['include_count'] = sum(1 for d in decisions if d.get('decision') == 'include')
    audit['exclude_count'] = sum(1 for d in decisions if d.get('decision') == 'exclude')
    write_json(AUDIT_PATH, audit)


def mark_task_progress() -> None:
    task = TASK_PATH.read_text(encoding='utf-8')
    old_line = '- `cq_q_5f1aa586172b1a82ebb8cdd65fb6927b` — source split required: raw source contains two independent questions, big-number string addition and a student/grade average SQL query; the mixed Canonical boundary must be retired and split source-first.'
    new_line = (
        '- `cq_q_5f1aa586172b1a82ebb8cdd65fb6927b` — retired after source-first split into '
        '`cq_q_37b2536da54c5df189dbb86c55a6bfa3` (decimal string addition) and '
        '`cq_q_e9c5bb8468fd0b37bd3f0abf72df80aa` (student/grade average SQL). Both split Canonicals are answer-missing until fresh relation review and candidate work complete.'
    )
    if old_line in task:
        task = task.replace(old_line, new_line)
    elif new_line not in task:
        raise SystemExit('batch 0028 mixed-source task line drifted')
    progress_line = (
        '- [x] Split mixed `cq_q_5f1aa586172b1a82ebb8cdd65fb6927b` source ownership into source-exact '
        '`cq_q_37b2536da54c5df189dbb86c55a6bfa3` and `cq_q_e9c5bb8468fd0b37bd3f0abf72df80aa`; '
        'retire the mixed Answer/ReviewProgress and keep both descendants unpromoted pending fresh relation review.'
    )
    if progress_line not in task:
        task = task.rstrip() + '\n' + progress_line + '\n'
    TASK_PATH.write_text(task, encoding='utf-8')


def main() -> None:
    verify_frozen_evidence()
    split_source_row()
    replace_canonical_ownership()
    retire_legacy_review_state()
    preserve_validity_audit()
    mark_task_progress()
    print('PASS: batch 0028 mixed source Question split into two source-exact Questions')


if __name__ == '__main__':
    main()
