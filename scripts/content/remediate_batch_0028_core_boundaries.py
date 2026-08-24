#!/usr/bin/env python3
"""Apply the non-relational frozen source-boundary dispositions for Answer Batch 0028.

This bounded slice intentionally handles only two source-backed wording normalizations
and one source-unrecoverable singleton retirement. Relation decisions and the mixed
source-question split are separate slices because they require fresh post-mutation
Canonical state and must not be smuggled into this direct source-normalization step.

Generated Question/index/type projections are rebuilt by the calling workflow.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
import shutil

ROOT = Path('.')
CANONICAL_PATH = ROOT / 'data/questions/canonical_questions.jsonl'
QUESTION_PATH = ROOT / 'data/questions/questions.jsonl'
PROGRESS_PATH = ROOT / 'review/progress.json'
VALIDITY_AUDIT_PATH = ROOT / 'config/question_validity_audit.json'
TASK_PATH = ROOT / 'tasks/answer-batches/TASK-20260711-0313-answer-batch-0028.md'
BOUNDARY_PATH = ROOT / 'review/content_build/answer_batch_0028/source_boundary_audit.md'
SOURCE_PACKET_PATH = ROOT / 'review/reports/ANSWER_BATCH_0028_SOURCE_PACKET.json'

ORIGINAL_IDS = {
    'cq_q_59d52495f3df25f0d98935d5e7fa3191',
    'cq_q_5a5db0e8391add20113a1ffec9c1e41b',
    'cq_q_5a87a04d4bc934eadb1cf42e28fcaed2',
    'cq_q_5aa1b6ca0f00362ffc20d3cf8bc5f266',
    'cq_q_5b53dba65e5ceb49b026dad8fc1704cc',
    'cq_q_5d39b5ae05a488c7436cbfa9b21e746c',
    'cq_q_5e21e188af5c4a9ffdb5eaf97cc39c97',
    'cq_q_5f1aa586172b1a82ebb8cdd65fb6927b',
    'cq_q_5f591ff5674d612dc10f87d07c1e820f',
    'cq_q_5f9a6152ed410f9a6b42f5f0ab7aa0a5',
}

NORMALIZE = {
    'cq_q_5a5db0e8391add20113a1ffec9c1e41b': {
        'note_path': ROOT / 'note_tagged/6826e4210000000003039d41.json',
        'old_qid': '5a5db0e8391add20113a1ffec9c1e41b',
        'old_text': '算法手撕：有序链表去除重复元素（保留/去除重复节点）。',
        'new_qid': 'fcd6c7cbfba95b407ed6dfd83adeb926',
        'new_text': '有序链表去除重复元素：给出1→2→3→3→4→4→5，返回1→2→5',
        'entities': ['链表', 'remove duplicates'],
    },
    'cq_q_5a87a04d4bc934eadb1cf42e28fcaed2': {
        'note_path': ROOT / 'note_tagged/67ed2207000000001c03db4e.json',
        'old_qid': '5a87a04d4bc934eadb1cf42e28fcaed2',
        'old_text': '算法：如何实现 IPv4 地址字符串与 32 位整数 (int) 之间的转换？',
        'new_qid': 'be5212d5e7ffdfedf22de7bae65f3f78',
        'new_text': 'IPv4 转 int',
        'entities': ['IPv4'],
    },
}

RETIRE = {
    'canonical_id': 'cq_q_5b53dba65e5ceb49b026dad8fc1704cc',
    'qid': '5b53dba65e5ceb49b026dad8fc1704cc',
    'note_path': ROOT / 'note_tagged/680e66cb0000000023012aa3.json',
    'expected_original': '算法：数字拆分',
    'explanation': (
        '最强原始 caption 只保留“数字拆分”，没有输入、输出、目标、示例、约束或唯一题号。'
        '当前“整数拆分/动态规划”等标签属于派生解释，不能据此恢复唯一 Coding 合同，按 incomplete_or_unreadable fail closed。'
    ),
}


def normalize_text(text: str) -> str:
    return re.sub(r'[^\w\u4e00-\u9fa5]', '', str(text).lower())


def question_id(text: str) -> str:
    return hashlib.md5(normalize_text(text).encode('utf-8')).hexdigest()


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


def find_tagged(note_path: Path, qids: set[str]) -> tuple[dict, str, int, dict]:
    note = read_json(note_path)
    matches = [(index, row) for index, row in enumerate(note.get('tagged_questions') or []) if row.get('question_id') in qids]
    if len(matches) != 1:
        raise SystemExit(f'{note_path}: expected exactly one tagged Question in {sorted(qids)}, got {len(matches)}')
    index, row = matches[0]
    return note, str(note.get('note_id') or note_path.stem), index, row


def set_validity_decision(audit: dict, note_id: str, source_index: int, qid: str, text: str, decision: str, reason=None, note=None) -> None:
    decisions = audit.setdefault('decisions', [])
    matches = [d for d in decisions if d.get('source_note_id') == note_id and d.get('source_question_index') == source_index]
    if len(matches) > 1:
        raise SystemExit(f'duplicate validity decisions for {note_id}[{source_index}]')
    payload = {
        'source_note_id': note_id,
        'source_question_index': source_index,
        'question_id': qid,
        'original_question': text,
        'decision': decision,
        'exclusion_reason': reason,
        'exclusion_note': note,
    }
    if matches:
        matches[0].clear()
        matches[0].update(payload)
    else:
        decisions.append(payload)


def rewrite_answer_title(cid: str, old_text: str, new_text: str) -> None:
    path = ROOT / 'review/answers' / f'{cid}.md'
    if not path.exists():
        raise SystemExit(f'{cid}: active baseline Answer missing')
    text = path.read_text(encoding='utf-8')
    if old_text in text:
        text = text.replace(old_text, new_text)
    elif new_text not in text:
        raise SystemExit(f'{cid}: active Answer contains neither old nor normalized title')
    path.write_text(text, encoding='utf-8')


def verify_frozen_evidence() -> None:
    packet = read_json(SOURCE_PACKET_PATH)
    if packet.get('schema_version') != 'answer_batch_source_packet.v2' or packet.get('batch') != '0028':
        raise SystemExit('unexpected batch 0028 source packet identity')
    if packet.get('source_policy') != 'repository_source_only_exact_id_or_exact_normalized_wording_no_fuzzy_inference':
        raise SystemExit('unexpected batch 0028 source policy')
    entries = packet.get('canonicals') or []
    ids = {entry.get('canonical_id') for entry in entries}
    if len(entries) != 10 or ids != ORIGINAL_IDS:
        raise SystemExit(f'batch 0028 source packet drift: missing={sorted(ORIGINAL_IDS-ids)}, extra={sorted(ids-ORIGINAL_IDS)}')
    missing = [entry.get('canonical_id') for entry in entries if not entry.get('source_hits')]
    if missing:
        raise SystemExit(f'batch 0028 source packet has missing hits: {missing}')
    boundary = BOUNDARY_PATH.read_text(encoding='utf-8')
    disposition_ids = set(re.findall(r'^\| `(cq_q_[0-9a-f]{32})` \|', boundary, flags=re.MULTILINE))
    if disposition_ids != ORIGINAL_IDS:
        raise SystemExit('batch 0028 source-boundary audit no longer covers the original 10 members')


def normalize_prompt(cid: str, spec: dict, canonicals: list[dict], questions: list[dict], audit: dict) -> None:
    if question_id(spec['new_text']) != spec['new_qid']:
        raise SystemExit(f'{cid}: normalized Question id drifted')
    note, note_id, source_index, tagged = find_tagged(spec['note_path'], {spec['old_qid'], spec['new_qid']})
    if tagged.get('question_id') == spec['old_qid']:
        if tagged.get('original_question') != spec['old_text']:
            raise SystemExit(f'{cid}: old tagged wording drifted: {tagged.get("original_question")}')
        tagged['question_id'] = spec['new_qid']
        tagged['original_question'] = spec['new_text']
        tagged['tech_entities'] = list(spec['entities'])
        tagged['is_valid_for_library'] = True
        tagged.pop('invalid_reason', None)
        write_json(spec['note_path'], note)
    elif tagged.get('original_question') != spec['new_text']:
        raise SystemExit(f'{cid}: normalized tagged wording drifted')

    canonical = next((row for row in canonicals if row.get('canonical_id') == cid), None)
    if not canonical:
        raise SystemExit(f'{cid}: Canonical missing')
    qids = list(canonical.get('question_ids') or [])
    if qids == [spec['old_qid']]:
        canonical['question_ids'] = [spec['new_qid']]
    elif qids != [spec['new_qid']]:
        raise SystemExit(f'{cid}: Canonical ownership drifted: {qids}')
    if canonical.get('canonical_title') == spec['old_text']:
        canonical['canonical_title'] = spec['new_text']
        canonical['aliases'] = [spec['new_text']]
    elif canonical.get('canonical_title') != spec['new_text']:
        raise SystemExit(f'{cid}: Canonical title drifted')
    canonical['primary_entities'] = list(spec['entities'])

    old_rows = [row for row in questions if row.get('question_id') == spec['old_qid']]
    new_rows = [row for row in questions if row.get('question_id') == spec['new_qid']]
    if old_rows and new_rows:
        raise SystemExit(f'{cid}: both old and normalized projected Questions exist')
    rows = old_rows or new_rows
    if len(rows) != 1 or rows[0].get('canonical_id') != cid:
        raise SystemExit(f'{cid}: projected Question missing or misbound')
    row = rows[0]
    if row.get('question_id') == spec['old_qid']:
        row['question_id'] = spec['new_qid']
        row['original_question'] = spec['new_text']
    elif row.get('original_question') != spec['new_text']:
        raise SystemExit(f'{cid}: normalized projected Question wording drifted')
    row['tech_entities'] = list(spec['entities'])

    existing = [d for d in audit.get('decisions') or [] if d.get('source_note_id') == note_id and d.get('source_question_index') == source_index]
    if existing:
        set_validity_decision(audit, note_id, source_index, spec['new_qid'], spec['new_text'], 'include')
    rewrite_answer_title(cid, spec['old_text'], spec['new_text'])


def retire_unrecoverable(canonicals: list[dict], questions: list[dict], progress, audit: dict) -> None:
    spec = RETIRE
    cid, qid = spec['canonical_id'], spec['qid']
    canonical = next((row for row in canonicals if row.get('canonical_id') == cid), None)
    if canonical is None:
        return
    if list(canonical.get('question_ids') or []) != [qid] or int(canonical.get('frequency', 0)) != 1:
        raise SystemExit(f'{cid}: retirement is only safe for the expected singleton Canonical')
    note, note_id, source_index, tagged = find_tagged(spec['note_path'], {qid})
    if tagged.get('original_question') != spec['expected_original']:
        raise SystemExit(f'{cid}: tagged wording drifted')
    tagged['is_valid_for_library'] = False
    tagged['invalid_reason'] = 'incomplete_or_unreadable'
    write_json(spec['note_path'], note)
    set_validity_decision(
        audit,
        note_id,
        source_index,
        qid,
        spec['expected_original'],
        'exclude',
        'incomplete_or_unreadable',
        spec['explanation'],
    )

    canonicals[:] = [row for row in canonicals if row.get('canonical_id') != cid]
    questions[:] = [row for row in questions if row.get('canonical_id') != cid and row.get('question_id') != qid]
    if isinstance(progress, dict) and isinstance(progress.get('items'), list):
        progress['items'] = [row for row in progress['items'] if row.get('canonical_id') != cid]
    elif isinstance(progress, list):
        progress[:] = [row for row in progress if row.get('canonical_id') != cid]
    elif isinstance(progress, dict):
        progress.pop(cid, None)

    active = ROOT / 'review/answers' / f'{cid}.md'
    archived = ROOT / 'review/archive/answers' / f'{cid}.md'
    archived.parent.mkdir(parents=True, exist_ok=True)
    if active.exists():
        if archived.exists():
            raise SystemExit(f'{cid}: both active and archived Answer exist before retirement')
        shutil.move(str(active), str(archived))
    elif not archived.exists():
        raise SystemExit(f'{cid}: neither active nor archived Answer exists')

    for base in [ROOT / 'review/candidates/answers', ROOT / 'review/evidence/answers']:
        item = base / f'{cid}.md'
        if item.exists():
            archive_base = ROOT / 'review/archive' / base.relative_to(ROOT / 'review')
            archive_base.mkdir(parents=True, exist_ok=True)
            shutil.move(str(item), str(archive_base / item.name))


def refresh_audit_counts(audit: dict) -> None:
    source_invalid = 0
    for path in sorted((ROOT / 'note_tagged').glob('*.json')):
        try:
            note = read_json(path)
        except Exception:
            continue
        for row in note.get('tagged_questions') or []:
            if row.get('is_valid_for_library') is False:
                source_invalid += 1
    decisions = audit.get('decisions') or []
    audit['source_invalid_row_count'] = source_invalid
    audit['include_count'] = sum(1 for row in decisions if row.get('decision') == 'include')
    audit['exclude_count'] = sum(1 for row in decisions if row.get('decision') == 'exclude')
    audit['audited_at'] = '2026-08-25'


def mark_task_progress() -> None:
    task = TASK_PATH.read_text(encoding='utf-8')
    marker = '- Boundary remediation is now the only permitted next slice for this batch: narrow `cq_q_5a5...` and `cq_q_5a87...`, fail-close `cq_q_5b53...`, resolve linked-list and deep-copy relations explicitly, and split `cq_q_5f1...` into two source-exact Questions before any answer research/writing begins.'
    replacement = '- Non-relational boundary remediation is applied for `cq_q_5a5...`, `cq_q_5a87...`, and `cq_q_5b53...`: the two source-backed prompts are narrowed and the unrecoverable singleton is fail-closed with an explicit audit reason. Relation decisions and the mixed-source split remain pending; no answer was promoted.'
    if marker in task:
        task = task.replace(marker, replacement)
    elif replacement not in task:
        raise SystemExit('batch 0028 task progress marker drifted')
    progress_line = '- [x] Apply and verify the non-relational boundary slice: normalize linked-list duplicate-removal and IPv4 conversion wording, and retire the source-unrecoverable `数字拆分` singleton.'
    if progress_line not in task:
        task = task.rstrip() + '\n' + progress_line + '\n'
    TASK_PATH.write_text(task, encoding='utf-8')


def main() -> None:
    verify_frozen_evidence()
    canonicals = read_jsonl(CANONICAL_PATH)
    questions = read_jsonl(QUESTION_PATH)
    progress = read_json(PROGRESS_PATH)
    audit = read_json(VALIDITY_AUDIT_PATH)

    present = {row.get('canonical_id') for row in canonicals}
    required_before = ORIGINAL_IDS - {RETIRE['canonical_id']}
    missing = required_before - present
    if missing:
        raise SystemExit(f'batch 0028 non-retired Canonicals already missing: {sorted(missing)}')

    for cid, spec in NORMALIZE.items():
        normalize_prompt(cid, spec, canonicals, questions, audit)
    retire_unrecoverable(canonicals, questions, progress, audit)
    refresh_audit_counts(audit)
    mark_task_progress()

    write_jsonl(CANONICAL_PATH, canonicals)
    write_jsonl(QUESTION_PATH, questions)
    write_json(PROGRESS_PATH, progress)
    write_json(VALIDITY_AUDIT_PATH, audit)

    print('PASS: batch 0028 non-relational source-boundary slice applied')


if __name__ == '__main__':
    main()
