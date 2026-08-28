#!/usr/bin/env python3
"""Split the mixed Batch 0050 cycle-detection/elimination source row into two source-exact Questions.

The current tagged row combines two independent coding contracts in one Question:
(1) linked-list cycle detection with input validation, and
(2) adjacent-sum-to-10 elimination returning the final sequence.
This remediation repairs only the source/Canonical ownership boundary. It retires
the mixed baseline answer/review state and leaves both descendants answer-missing
for fresh source-first answer work.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
import shutil

ROOT = Path('.')
NOTE_PATH = ROOT / 'note_tagged/67fd2286000000001d03b1bf.json'
STRUCTURED_PATH = ROOT / 'note_structured/67fd2286000000001d03b1bf.json'
CANONICAL_PATH = ROOT / 'data/questions/canonical_questions.jsonl'
QUESTION_PATH = ROOT / 'data/questions/questions.jsonl'
PROGRESS_PATH = ROOT / 'review/progress.json'
AUDIT_PATH = ROOT / 'config/question_validity_audit.json'
TASK_PATH = ROOT / 'tasks/answer-batches/TASK-20260711-0313-answer-batch-0050.md'
OUT_DIR = ROOT / 'review/content_build/answer_batch_0050'

SOURCE_NOTE_ID = '67fd2286000000001d03b1bf'
SOURCE_INDEX = 10
OLD_QID = 'd6ed1b1964f238df266bdd7e8bd146f1'
OLD_CANONICAL = f'cq_q_{OLD_QID}'
OLD_TEXT = '算法与 SQL：检测链表是否有环（要求检测入参合法性）；设计一个消消乐算法（相邻两数和为 10 则消除，返回最终序列）'
STRUCTURED_TEXT = '算法与 SQL：检测链表是否有环（要求检测入参合法性）；设计一个消消乐算法（相邻两数和为 10 则消除，返回最终序列）'
SPLITS = [
    {
        'text': '算法：检测链表是否有环（要求检测入参合法性）',
        'qid': '88d86d8e4586504b5c9365f4126f7436',
        'domain': {'l1': '算法', 'l2': '链表'},
        'entities': ['floyd cycle-finding', 'linked list'],
        'question_type': '算法手撕_Coding',
    },
    {
        'text': '算法：设计一个消消乐算法（相邻两数和为 10 则消除，返回最终序列）',
        'qid': 'b66328eb23ca1ba53a062a787c71a9dc',
        'domain': {'l1': '算法', 'l2': '栈'},
        'entities': ['stack', 'elimination game'],
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


def verify_source_evidence() -> None:
    structured = read_json(STRUCTURED_PATH)
    if structured.get('note_id') != SOURCE_NOTE_ID:
        raise SystemExit('structured source note identity drift')
    questions = list(structured.get('questions') or [])
    matches = [q for q in questions if q == STRUCTURED_TEXT]
    if matches != [STRUCTURED_TEXT]:
        raise SystemExit('structured source no longer contains the exact mixed coding line')
    if '检测链表是否有环' not in STRUCTURED_TEXT or '相邻两数和为 10 则消除' not in STRUCTURED_TEXT:
        raise SystemExit('required independent coding clauses missing from source')

    inventory = read_json(OUT_DIR / 'source_inventory.json')
    entries = list(inventory.get('entries') or inventory.get('canonicals') or [])
    serialized = json.dumps(inventory, ensure_ascii=False)
    if OLD_CANONICAL not in serialized or OLD_TEXT not in serialized:
        raise SystemExit('Batch 0050 frozen source inventory no longer contains the mixed Canonical/source text')

    for item in SPLITS:
        actual = question_id(item['text'])
        if actual != item['qid']:
            raise SystemExit(f"unexpected normalized id for {item['text']}: {actual}")


def split_tagged_source() -> None:
    note = read_json(NOTE_PATH)
    if note.get('note_id') != SOURCE_NOTE_ID:
        raise SystemExit('tagged source note identity drift')
    tagged = list(note.get('tagged_questions') or [])
    old_matches = [i for i, row in enumerate(tagged) if row.get('question_id') == OLD_QID or row.get('original_question') == OLD_TEXT]
    new_ids = {item['qid'] for item in SPLITS}
    split_matches = [row for row in tagged if row.get('question_id') in new_ids]

    if old_matches:
        if len(old_matches) != 1 or split_matches:
            raise SystemExit('legacy and split tagged Questions coexist unexpectedly')
        index = old_matches[0]
        if index != SOURCE_INDEX or index != len(tagged) - 1:
            raise SystemExit(f'legacy mixed source row drifted from expected final index {SOURCE_INDEX}: {index}')
        legacy = tagged[index]
        if legacy.get('original_question') != OLD_TEXT:
            raise SystemExit('legacy mixed source text drift')
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
            raise SystemExit('split source Question order/ids drifted')
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
            raise SystemExit('legacy mixed Canonical is not the expected singleton')
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


def retire_old_review_state() -> None:
    if PROGRESS_PATH.exists():
        progress = read_json(PROGRESS_PATH)
        changed = False
        if isinstance(progress, dict) and isinstance(progress.get('items'), list):
            before = len(progress['items'])
            progress['items'] = [row for row in progress['items'] if row.get('canonical_id') != OLD_CANONICAL]
            changed = len(progress['items']) != before
            if changed:
                progress['updated_at'] = DATE
                progress['items'] = sorted(progress['items'], key=lambda row: row.get('canonical_id', ''))
        elif isinstance(progress, list):
            before = len(progress)
            progress[:] = [row for row in progress if row.get('canonical_id') != OLD_CANONICAL]
            changed = len(progress) != before
        elif isinstance(progress, dict) and OLD_CANONICAL in progress:
            progress.pop(OLD_CANONICAL)
            changed = True
        if changed:
            write_json(PROGRESS_PATH, progress)

    archive_root = ROOT / 'review/archive'
    for source, relative in [
        (ROOT / 'review/answers' / f'{OLD_CANONICAL}.md', Path('answers') / f'{OLD_CANONICAL}.md'),
        (ROOT / 'review/candidates/answers' / f'{OLD_CANONICAL}.md', Path('candidates/answers') / f'{OLD_CANONICAL}.md'),
        (ROOT / 'review/evidence' / f'{OLD_CANONICAL}.json', Path('evidence') / f'{OLD_CANONICAL}.json'),
        (ROOT / 'review/evidence/answers' / f'{OLD_CANONICAL}.md', Path('evidence/answers') / f'{OLD_CANONICAL}.md'),
    ]:
        if not source.exists():
            continue
        destination = archive_root / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        if destination.exists():
            if destination.read_bytes() != source.read_bytes():
                raise SystemExit(f'conflicting archived artifact: {destination}')
            source.unlink()
        else:
            shutil.move(str(source), str(destination))


def preserve_validity_audit() -> None:
    if not AUDIT_PATH.exists():
        return
    audit = read_json(AUDIT_PATH)
    decisions = list(audit.get('decisions') or [])
    at_source = [d for d in decisions if d.get('source_note_id') == SOURCE_NOTE_ID and int(d.get('source_question_index', -1)) == SOURCE_INDEX]
    if not at_source:
        return
    if len(at_source) != 1 or at_source[0].get('decision') != 'include':
        raise SystemExit('unexpected validity-audit state for mixed source Question')
    first = at_source[0]
    first.update({
        'question_id': SPLITS[0]['qid'],
        'original_question': SPLITS[0]['text'],
        'exclusion_reason': None,
        'exclusion_note': None,
    })
    second_at_source = [d for d in decisions if d.get('source_note_id') == SOURCE_NOTE_ID and int(d.get('source_question_index', -1)) == SOURCE_INDEX + 1]
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
    audit['audited_at'] = DATE
    audit['include_count'] = sum(1 for d in decisions if d.get('decision') == 'include')
    audit['exclude_count'] = sum(1 for d in decisions if d.get('decision') == 'exclude')
    write_json(AUDIT_PATH, audit)


def write_boundary_record() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    payload = {
        'schema_version': 'source_question_split_review.v1',
        'reviewed_at': DATE,
        'source_note_id': SOURCE_NOTE_ID,
        'source_question_index': SOURCE_INDEX,
        'legacy_question_id': OLD_QID,
        'legacy_canonical_id': OLD_CANONICAL,
        'legacy_text': OLD_TEXT,
        'source_evidence': str(STRUCTURED_PATH),
        'decision': 'split',
        'rationale': 'The frozen structured source line contains two independent executable response contracts separated by a semicolon: linked-list cycle detection with input-validation requirements, and adjacent-sum-to-10 elimination returning a final sequence. They cannot share one strict-valid Coding answer boundary.',
        'descendants': [
            {'question_id': item['qid'], 'canonical_id': item['canonical_id'], 'original_question': item['text']}
            for item in SPLITS
        ],
        'promotion_state': 'answer_missing_pending_fresh_source_first_candidate_work',
    }
    write_json(OUT_DIR / 'compound_source_split_review.json', payload)


def mark_task_progress() -> None:
    task = TASK_PATH.read_text(encoding='utf-8')
    line = (
        '- [x] Split mixed `cq_q_d6ed1b1964f238df266bdd7e8bd146f1` source ownership into source-exact '
        '`cq_q_88d86d8e4586504b5c9365f4126f7436` (linked-list cycle detection with input validation) and '
        '`cq_q_b66328eb23ca1ba53a062a787c71a9dc` (adjacent-sum-to-10 elimination). The structured source proves two independent coding contracts in one legacy row; the mixed Answer/ReviewProgress is retired and both descendants remain answer-missing pending fresh source-first candidate/review work.'
    )
    if line not in task:
        task = task.rstrip() + '\n' + line + '\n'
    TASK_PATH.write_text(task, encoding='utf-8')


def main() -> None:
    verify_source_evidence()
    split_tagged_source()
    replace_canonical_ownership()
    retire_old_review_state()
    preserve_validity_audit()
    write_boundary_record()
    mark_task_progress()
    print('PASS split Batch 0050 compound source into cycle-detection and elimination Questions')


if __name__ == '__main__':
    main()
