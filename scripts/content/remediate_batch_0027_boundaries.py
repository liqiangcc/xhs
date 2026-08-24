#!/usr/bin/env python3
"""Apply the frozen source-first boundary dispositions for Answer Batch 0027.

The immutable repository source packet plus source_boundary_audit.md are the evidence
boundary. This mutation keeps nine recoverable Questions, narrows three inflated
formal prompts, repairs one real logic-puzzle validity/type classification, removes
solution-specific metadata that is not part of the source contract, and retires one
singleton whose exact coding task cannot be recovered.

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
TASK_PATH = ROOT / 'tasks/answer-batches/TASK-20260711-0313-answer-batch-0027.md'
BOUNDARY_PATH = ROOT / 'review/content_build/answer_batch_0027/source_boundary_audit.md'
SOURCE_PACKET_PATH = ROOT / 'review/reports/ANSWER_BATCH_0027_SOURCE_PACKET.json'

ORIGINAL_IDS = {
    'cq_q_555486cb901cc4cd56776f7eeaa0d5b5',
    'cq_q_5598debbce04bff1fcb9dbd8f09e9d68',
    'cq_q_55c3a35aaf4f76ce9aab78ea39d9fddc',
    'cq_q_55dffdc4ce650cf4146064792fc919ca',
    'cq_q_567ffeb91924fcb3677322177357773b',
    'cq_q_57aa151b635ea5536749fec03c6db22d',
    'cq_q_580b69f633d51b4f6c6262690a0fdf9c',
    'cq_q_58149c934c9b77f14e10c21cebff411c',
    'cq_q_5873d2a550ca02cc41b2862b6aefaa77',
    'cq_q_59c84ea33afa81784f39f85a824a2d94',
}

RETIRE = {
    'canonical_id': 'cq_q_5598debbce04bff1fcb9dbd8f09e9d68',
    'qid': '5598debbce04bff1fcb9dbd8f09e9d68',
    'note_path': ROOT / 'note_tagged/685d25970000000017036aec.json',
    'expected_original': '算法手撕：类似数组合并（Merge Array）的实现。',
    'explanation': (
        '最强原始 caption 只保留“写一个类似数组合并的题目”，没有输入是否有序、是否原地合并、容量、重复值语义、输出形式或唯一题号。'
        '当前结构化 Question 的 Merge Array / merge sort 细节属于派生扩写，无法据此形成可验证 Coding 合同，按 incomplete_or_unreadable fail closed。'
    ),
}

NORMALIZE = {
    'cq_q_58149c934c9b77f14e10c21cebff411c': {
        'note_path': ROOT / 'note_tagged/6692706200000000250167ff.json',
        'old_qid': '58149c934c9b77f14e10c21cebff411c',
        'old_text': '算法/手撕：利用数组实现高性能循环队列 (入队/出队逻辑及空间利用率优化)',
        'new_qid': '094694a29ed8e1276d4c392d99d56302',
        'new_text': '手写一个用数组实现的循环队列，只需要入队和出队；如何改进以避免浪费一个数组空间？',
        'entities': ['circular queue'],
    },
    'cq_q_5873d2a550ca02cc41b2862b6aefaa77': {
        'note_path': ROOT / 'note_tagged/67f67da2000000001200ed84.json',
        'old_qid': '5873d2a550ca02cc41b2862b6aefaa77',
        'old_text': '并发编程：如何实现两个线程交替打印 "A" 和 "B"（如打印 100 次）？请给出基于 `wait/notify` 或 `LockSupport` 的解决方案。',
        'new_qid': 'b1effe2d30fbefb17fab84fe768fbdac',
        'new_text': '两个线程交替打印abababab',
        'entities': ['线程同步'],
    },
    'cq_q_59c84ea33afa81784f39f85a824a2d94': {
        'note_path': ROOT / 'note_tagged/67c941e20000000029031ef6.json',
        'old_qid': '59c84ea33afa81784f39f85a824a2d94',
        'old_text': '算法：实现一个计算器（类似于 LeetCode 16.26），支持乘除法优先及括号处理',
        'new_qid': 'a49d8c5d9ec12aa92ccea9a5f2bb4302',
        'new_text': 'LeetCode 16.26 计算器：如何让乘除法优先计算？',
        'entities': ['中缀表达式'],
    },
}

PUZZLE = {
    'canonical_id': 'cq_q_580b69f633d51b4f6c6262690a0fdf9c',
    'qid': '580b69f633d51b4f6c6262690a0fdf9c',
    'note_path': ROOT / 'note_tagged/65d340a10000000007006ce8.json',
    'text': '逻辑智力：12 个小球中有一个质量异常 (不知轻重)，使用天平至少称重几次能保证找出该球？',
}

TOP_K = {
    'canonical_id': 'cq_q_567ffeb91924fcb3677322177357773b',
    'qid': '567ffeb91924fcb3677322177357773b',
    'note_path': ROOT / 'note_tagged/678bb5fd000000001b008919.json',
    'text': '海量数据处理：在亿级数据中寻找最大的 100 个数',
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


def rewrite_answer_title(cid: str, old_text: str, new_text: str, answer_type: str | None = None) -> None:
    path = ROOT / 'review/answers' / f'{cid}.md'
    if not path.exists():
        raise SystemExit(f'{cid}: active baseline Answer missing')
    text = path.read_text(encoding='utf-8')
    lines = text.splitlines()
    if not lines or not lines[0].startswith('<!-- xhs-answer: ') or not lines[0].endswith(' -->'):
        raise SystemExit(f'{cid}: malformed xhs-answer metadata')
    metadata = json.loads(lines[0][len('<!-- xhs-answer: '):-len(' -->')])
    if metadata.get('canonical_id') != cid:
        raise SystemExit(f'{cid}: answer metadata canonical mismatch')
    if answer_type:
        metadata['answer_type'] = answer_type
    lines[0] = '<!-- xhs-answer: ' + json.dumps(metadata, ensure_ascii=False, separators=(',', ':')) + ' -->'
    text = '\n'.join(lines) + ('\n' if text.endswith('\n') else '')
    if old_text != new_text:
        if old_text in text:
            text = text.replace(old_text, new_text)
        elif new_text not in text:
            raise SystemExit(f'{cid}: active Answer contains neither old nor normalized title')
    path.write_text(text, encoding='utf-8')


def verify_frozen_evidence() -> None:
    packet = read_json(SOURCE_PACKET_PATH)
    if packet.get('schema_version') != 'answer_batch_source_packet.v2' or packet.get('batch') != '0027':
        raise SystemExit('unexpected batch 0027 source packet identity')
    if packet.get('source_policy') != 'repository_source_only_exact_id_or_exact_normalized_wording_no_fuzzy_inference':
        raise SystemExit('unexpected batch 0027 source policy')
    entries = packet.get('canonicals') or []
    ids = {entry.get('canonical_id') for entry in entries}
    if len(entries) != 10 or ids != ORIGINAL_IDS:
        raise SystemExit(f'batch 0027 source packet drift: missing={sorted(ORIGINAL_IDS-ids)}, extra={sorted(ids-ORIGINAL_IDS)}')
    missing = [entry.get('canonical_id') for entry in entries if not entry.get('source_hits')]
    if missing:
        raise SystemExit(f'batch 0027 source packet has missing hits: {missing}')
    boundary = BOUNDARY_PATH.read_text(encoding='utf-8')
    disposition_ids = set(re.findall(r'^\| `(cq_q_[0-9a-f]{32})` \|', boundary, flags=re.MULTILINE))
    if disposition_ids != ORIGINAL_IDS:
        raise SystemExit('batch 0027 source-boundary audit no longer covers the original 10 members')


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


def normalize_puzzle(canonicals: list[dict], questions: list[dict], audit: dict) -> None:
    spec = PUZZLE
    note, note_id, source_index, tagged = find_tagged(spec['note_path'], {spec['qid']})
    if tagged.get('original_question') != spec['text']:
        raise SystemExit('12-ball puzzle source wording drifted')
    tagged['is_valid_for_library'] = True
    tagged.pop('invalid_reason', None)
    tagged['question_type'] = '八股文_Concept'
    write_json(spec['note_path'], note)
    rows = [row for row in questions if row.get('question_id') == spec['qid'] and row.get('canonical_id') == spec['canonical_id']]
    if len(rows) != 1:
        raise SystemExit('12-ball puzzle projected Question missing or duplicated')
    rows[0]['question_type'] = '八股文_Concept'
    set_validity_decision(audit, note_id, source_index, spec['qid'], spec['text'], 'include')
    rewrite_answer_title(spec['canonical_id'], spec['text'], spec['text'], answer_type='concept')
    if not any(row.get('canonical_id') == spec['canonical_id'] for row in canonicals):
        raise SystemExit('12-ball puzzle Canonical disappeared')


def normalize_top_k_entities(canonicals: list[dict], questions: list[dict]) -> None:
    spec = TOP_K
    note, _, _, tagged = find_tagged(spec['note_path'], {spec['qid']})
    if tagged.get('original_question') != spec['text']:
        raise SystemExit('Top-100 source wording drifted')
    tagged['tech_entities'] = ['Top K']
    write_json(spec['note_path'], note)
    canonical = next((row for row in canonicals if row.get('canonical_id') == spec['canonical_id']), None)
    if not canonical:
        raise SystemExit('Top-100 Canonical disappeared')
    canonical['primary_entities'] = ['Top K']
    rows = [row for row in questions if row.get('question_id') == spec['qid'] and row.get('canonical_id') == spec['canonical_id']]
    if len(rows) != 1:
        raise SystemExit('Top-100 projected Question missing or duplicated')
    rows[0]['tech_entities'] = ['Top K']


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
    set_validity_decision(audit, note_id, source_index, qid, spec['expected_original'], 'exclude', 'incomplete_or_unreadable', spec['explanation'])

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


def mark_task_remediated() -> None:
    task = TASK_PATH.read_text(encoding='utf-8')
    task = task.replace('- Source-recoverable after boundary audit: `9` (data remediation pending)', '- Active after source-boundary remediation: `9`')
    task = task.replace('- [ ] Apply and verify the frozen source-boundary remediation for all 10 original members.', '- [x] Apply and verify the frozen source-boundary remediation for all 10 original members.')
    marker = '- Source-first boundary conclusions are frozen in `review/content_build/answer_batch_0027/source_boundary_audit.md`: 9 recoverable active targets, 1 fail-closed exclusion, with three active wording/type normalizations required before candidate authoring. No answer has been promoted by this audit.'
    replacement = '- Source-first boundary conclusions are frozen in `review/content_build/answer_batch_0027/source_boundary_audit.md`: 9 recoverable active targets, 1 fail-closed exclusion; source-backed wording/type/metadata remediation has been applied and verified. No answer has been promoted by this boundary work.'
    if marker in task:
        task = task.replace(marker, replacement)
    elif replacement not in task:
        raise SystemExit('batch 0027 task progress marker drifted')
    TASK_PATH.write_text(task.rstrip() + '\n', encoding='utf-8')


def main() -> None:
    verify_frozen_evidence()
    canonicals = read_jsonl(CANONICAL_PATH)
    questions = read_jsonl(QUESTION_PATH)
    progress = read_json(PROGRESS_PATH)
    audit = read_json(VALIDITY_AUDIT_PATH)

    present = {row.get('canonical_id') for row in canonicals}
    missing_nonretired = (ORIGINAL_IDS - {RETIRE['canonical_id']}) - present
    if missing_nonretired:
        raise SystemExit(f'batch 0027 recoverable Canonicals already missing: {sorted(missing_nonretired)}')

    for cid, spec in NORMALIZE.items():
        normalize_prompt(cid, spec, canonicals, questions, audit)
    normalize_puzzle(canonicals, questions, audit)
    normalize_top_k_entities(canonicals, questions)
    retire_unrecoverable(canonicals, questions, progress, audit)
    refresh_audit_counts(audit)

    write_jsonl(CANONICAL_PATH, canonicals)
    write_jsonl(QUESTION_PATH, questions)
    write_json(PROGRESS_PATH, progress)
    write_json(VALIDITY_AUDIT_PATH, audit)
    mark_task_remediated()

    active_ids = {row.get('canonical_id') for row in canonicals}
    if RETIRE['canonical_id'] in active_ids:
        raise SystemExit('batch 0027 unrecoverable Canonical remains active')
    required = ORIGINAL_IDS - {RETIRE['canonical_id']}
    if not required <= active_ids:
        raise SystemExit('batch 0027 recoverable Canonical disappeared')
    print('PASS batch 0027 source-first remediation: original=10 active=9 retired=1 normalized_wording=3 repaired_type=1 normalized_metadata=1')


if __name__ == '__main__':
    main()
