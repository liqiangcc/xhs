#!/usr/bin/env python3
"""Apply source-first boundary dispositions for Answer Batch 0026.

The frozen repository source packet is the evidence boundary. This mutation:
- keeps seven directly source-recoverable coding Questions active;
- narrows one inflated List<User> -> Map prompt to the wording preserved by the raw caption;
- retires two singleton pseudo-Questions whose strongest repository source does not
  preserve a unique executable problem identity;
- preserves the frozen pre-remediation source packet as historical evidence.

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
TASK_PATH = ROOT / 'tasks/answer-batches/TASK-20260711-0313-answer-batch-0026.md'
BOUNDARY_PATH = ROOT / 'review/content_build/answer_batch_0026/source_boundary_audit.md'
SOURCE_PACKET_PATH = ROOT / 'review/reports/ANSWER_BATCH_0026_SOURCE_PACKET.json'

QUALIFIED = {
    'cq_q_4fc0d124be6bf13d0fcfe8b0394a23a1': (
        'Raw caption explicitly records “实现虚拟滚动和图片懒加载的结合”; the answer may state its component/API assumptions instead of inventing a hidden judge contract.'
    ),
    'cq_q_50d730f280e48c997fa9f9e662eb95ac': (
        'Image transcript preserves LeetCode 5, the longest-palindromic-substring statement, length bound, and examples.'
    ),
    'cq_q_50ef484fd29fe4ba23065db1b1439c74': (
        'Raw caption explicitly records deleting duplicate nodes from a linked list. Because “duplicate” can mean keep-one or delete-all, the formal answer must surface and handle both standard contracts rather than silently choosing one.'
    ),
    'cq_q_51683d4359a08f525adc2fead28a44aa': (
        'Image transcript explicitly asks to partition intervals into the minimum number of groups with no overlap inside a group. Endpoint-touch semantics must be declared in the answer.'
    ),
    'cq_q_53686d4f6b7cd986269f67826d29b4ba': (
        'Raw caption explicitly records deleting a node from a binary-search tree.'
    ),
    'cq_q_54e8509938a2d444e8bbc86d62206ef8': (
        'Raw caption explicitly asks to validate whether an arbitrary input string conforms to IPv4 rules.'
    ),
    'cq_q_54f9a2d007c671b36e91b98db69f6c2d': (
        'Raw caption explicitly asks for overlapping date intervals and states an O(n) target. A correct answer must distinguish general unsorted input from the extra ordering/bounded-domain assumptions needed for linear time.'
    ),
}

LIST_TO_MAP = {
    'canonical_id': 'cq_q_5438416849074df945e61753490c7651',
    'old_qid': '5438416849074df945e61753490c7651',
    'old_text': 'Java 8 实践：给定 List<User>，请写出三种及以上将该 List 转换为以 UserId 为 Key 的 Map 的方法（含 Stream API 实现）？',
    'new_text': '有一个List<User>，将他转成Map，其中key为userId有哪些方法？',
    'new_qid': '1b2ac49f86449f68b3129303853bd5bc',
    'note_path': ROOT / 'note_tagged/68afac2a000000001d026e35.json',
    'domain': {'l1': 'Java基础', 'l2': '语言特性'},
    'entities': ['java 8 stream', 'collectors.tomap'],
}

RETIRE = {
    'cq_q_53e13c85c2e7c270c46b64027dbd64f6': {
        'note_path': ROOT / 'note_tagged/67aef7c100000000170382ee.json',
        'expected_original': '算法：回溯算法中的搜索空间剪枝与元素去重逻辑 (如子集、排列 II)',
        'explanation': (
            '最强原始 caption 只说明“一面回溯题思路正确但未去重，算法未 AC”，没有保留题目、输入输出、约束或题号。'
            '当前结构化 Question 进一步具体化成“子集、排列 II / 搜索空间剪枝与去重”，这些细节无法由原始来源唯一恢复；'
            '因此不能据此生成可验证 Coding 合同，按 incomplete_or_unreadable fail closed。'
        ),
        'task_note': 'retired fail-closed: raw source only says an unspecified backtracking problem failed deduplication; the concrete coding contract is unrecoverable.',
    },
    'cq_q_542633986c66e30d8935d192f98137be': {
        'note_path': ROOT / 'note_tagged/66adb99a0000000009015abb.json',
        'expected_original': '算法：常见中等难度手撕题',
        'explanation': (
            '最强原始 caption 仅保留“手撕 mid，常见题”（三面另有“mid-hard 手撕，不是很常见”），没有任何具体题目身份、输入输出、约束或样例。'
            '“常见中等难度手撕题”不是可唯一还原的问题，无法形成确定性 Coding 合同，按 incomplete_or_unreadable fail closed。'
        ),
        'task_note': 'retired fail-closed: source only preserves “手撕 mid，常见题” without a concrete problem identity.',
    },
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


def tagged_ref(note_path: Path, qid: str) -> tuple[str, int, dict]:
    note = read_json(note_path)
    matches = [(index, row) for index, row in enumerate(note.get('tagged_questions') or []) if row.get('question_id') == qid]
    if len(matches) != 1:
        raise SystemExit(f'{note_path}: expected one tagged Question {qid}, got {len(matches)}')
    index, row = matches[0]
    return str(note.get('note_id') or note_path.stem), index, row


def verify_source_packet() -> None:
    packet = read_json(SOURCE_PACKET_PATH)
    if packet.get('schema_version') != 'answer_batch_source_packet.v2' or packet.get('batch') != '0026':
        raise SystemExit('unexpected batch 0026 source packet identity')
    if packet.get('source_policy') != 'repository_source_only_exact_id_or_exact_normalized_wording_no_fuzzy_inference':
        raise SystemExit('unexpected batch 0026 source policy')
    entries = packet.get('canonicals') or []
    expected = set(QUALIFIED) | {LIST_TO_MAP['canonical_id']} | set(RETIRE)
    ids = {entry.get('canonical_id') for entry in entries}
    if len(entries) != 10 or ids != expected:
        raise SystemExit(f'batch 0026 source packet drift: missing={sorted(expected-ids)}, extra={sorted(ids-expected)}')
    missing = [entry.get('canonical_id') for entry in entries if not entry.get('source_hits')]
    if missing:
        raise SystemExit(f'batch 0026 source packet has missing hits: {missing}')


def normalize_list_to_map(canonicals: list[dict], questions: list[dict], audit: dict) -> None:
    spec = LIST_TO_MAP
    cid = spec['canonical_id']
    if question_id(spec['new_text']) != spec['new_qid']:
        raise SystemExit('List<User> normalized Question id drifted')

    note = read_json(spec['note_path'])
    matches = [(i, q) for i, q in enumerate(note.get('tagged_questions') or []) if q.get('question_id') in {spec['old_qid'], spec['new_qid']}]
    if len(matches) != 1:
        raise SystemExit(f'{cid}: expected one old/new tagged Question, got {len(matches)}')
    source_index, tagged = matches[0]
    source_note_id = str(note.get('note_id') or spec['note_path'].stem)
    if tagged.get('question_id') == spec['old_qid']:
        if tagged.get('original_question') != spec['old_text']:
            raise SystemExit(f'{cid}: inflated tagged wording drifted')
        tagged['question_id'] = spec['new_qid']
        tagged['original_question'] = spec['new_text']
        tagged['domain'] = {'l1': 'Java基础', 'l2': 'Java基础'}
        tagged['question_type'] = '算法手撕_Coding'
        tagged['tech_entities'] = list(spec['entities'])
        write_json(spec['note_path'], note)
    elif tagged.get('original_question') != spec['new_text']:
        raise SystemExit(f'{cid}: normalized tagged wording drifted')

    canonical = next((row for row in canonicals if row.get('canonical_id') == cid), None)
    if not canonical:
        raise SystemExit(f'{cid}: Canonical missing')
    if list(canonical.get('question_ids') or []) == [spec['old_qid']]:
        canonical['question_ids'] = [spec['new_qid']]
    elif list(canonical.get('question_ids') or []) != [spec['new_qid']]:
        raise SystemExit(f'{cid}: Canonical ownership drifted: {canonical.get("question_ids")}')
    if canonical.get('canonical_title') == spec['old_text']:
        canonical['canonical_title'] = spec['new_text']
        canonical['aliases'] = [spec['new_text']]
    elif canonical.get('canonical_title') != spec['new_text']:
        raise SystemExit(f'{cid}: Canonical title drifted')
    canonical['primary_domain'] = dict(spec['domain'])
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
        row['domain'] = {'l1': 'Java基础', 'l2': 'Java基础'}
        row['tech_entities'] = list(spec['entities'])
    elif row.get('original_question') != spec['new_text']:
        raise SystemExit(f'{cid}: normalized projected Question wording drifted')

    for decision in audit.get('decisions') or []:
        if decision.get('source_note_id') == source_note_id and decision.get('source_question_index') == source_index:
            if decision.get('decision') != 'include':
                raise SystemExit(f'{cid}: recoverable List<User> prompt must remain included')
            decision['question_id'] = spec['new_qid']
            decision['original_question'] = spec['new_text']

    answer_path = ROOT / 'review/answers' / f'{cid}.md'
    if not answer_path.exists():
        raise SystemExit(f'{cid}: active baseline Answer missing')
    answer = answer_path.read_text(encoding='utf-8')
    if spec['old_text'] in answer:
        answer_path.write_text(answer.replace(spec['old_text'], spec['new_text']), encoding='utf-8')
    elif spec['new_text'] not in answer:
        raise SystemExit(f'{cid}: active Answer contains neither old nor normalized wording')


def ensure_exclusion_decision(audit: dict, note_id: str, source_index: int, qid: str, original: str, explanation: str) -> None:
    decisions = audit.setdefault('decisions', [])
    matches = [d for d in decisions if d.get('source_note_id') == note_id and d.get('source_question_index') == source_index]
    if len(matches) > 1:
        raise SystemExit(f'duplicate validity decisions for {note_id}[{source_index}]')
    payload = {
        'source_note_id': note_id,
        'source_question_index': source_index,
        'question_id': qid,
        'original_question': original,
        'decision': 'exclude',
        'exclusion_reason': 'incomplete_or_unreadable',
        'exclusion_note': explanation,
    }
    if matches:
        matches[0].clear()
        matches[0].update(payload)
    else:
        decisions.append(payload)


def retire_unrecoverable(canonicals: list[dict], questions: list[dict], progress: dict, audit: dict) -> None:
    for cid, spec in RETIRE.items():
        qid = cid.removeprefix('cq_q_')
        canonical = next((row for row in canonicals if row.get('canonical_id') == cid), None)
        if canonical is None:
            continue
        if list(canonical.get('question_ids') or []) != [qid] or int(canonical.get('frequency', 0)) != 1:
            raise SystemExit(f'{cid}: retirement is only safe for the expected singleton Canonical')

        note = read_json(spec['note_path'])
        matches = [(i, q) for i, q in enumerate(note.get('tagged_questions') or []) if q.get('question_id') == qid]
        if len(matches) != 1:
            raise SystemExit(f'{cid}: expected one tagged source Question, got {len(matches)}')
        source_index, tagged = matches[0]
        if tagged.get('original_question') != spec['expected_original']:
            raise SystemExit(f'{cid}: source wording drifted: {tagged.get("original_question")}')
        tagged['is_valid_for_library'] = False
        tagged['invalid_reason'] = 'incomplete_or_unreadable'
        write_json(spec['note_path'], note)
        note_id = str(note.get('note_id') or spec['note_path'].stem)
        ensure_exclusion_decision(audit, note_id, source_index, qid, spec['expected_original'], spec['explanation'])

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
            candidate = base / f'{cid}.md'
            if candidate.exists():
                archive_base = ROOT / 'review/archive' / base.relative_to(ROOT / 'review')
                archive_base.mkdir(parents=True, exist_ok=True)
                shutil.move(str(candidate), str(archive_base / candidate.name))


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


def write_task() -> None:
    task = TASK_PATH.read_text(encoding='utf-8')
    task = re.sub(r'- Status: `[^`]+`', '- Status: `pending`', task, count=1)
    task = task.replace('- Canonical count: `10`', '- Original batch Canonical count: `10`\n- Active after source-boundary audit: `8`')
    replacements = {
        '- `cq_q_53e13c85c2e7c270c46b64027dbd64f6` — coding; risks: long_tail_baseline, placeholder_implementation':
            '- `cq_q_53e13c85c2e7c270c46b64027dbd64f6` — retired fail-closed: raw source only says an unspecified backtracking problem failed deduplication; the concrete coding contract is unrecoverable.',
        '- `cq_q_542633986c66e30d8935d192f98137be` — coding; risks: long_tail_baseline, placeholder_implementation':
            '- `cq_q_542633986c66e30d8935d192f98137be` — retired fail-closed: source only preserves “手撕 mid，常见题” without a concrete problem identity.',
        '- `cq_q_5438416849074df945e61753490c7651` — coding; risks: long_tail_baseline, placeholder_implementation':
            '- `cq_q_5438416849074df945e61753490c7651` — coding; normalized to raw-caption wording: List<User> → Map keyed by userId, without inventing “three or more” or mandatory Stream API requirements.',
    }
    for old, new in replacements.items():
        if old in task:
            task = task.replace(old, new)
        elif new not in task:
            raise SystemExit(f'task wording drift: missing {old}')
    if '## Source-first boundary disposition' not in task:
        task += (
            '\n## Source-first boundary disposition\n\n'
            '- Repository source packet: `review/reports/ANSWER_BATCH_0026_SOURCE_PACKET.{json,md}` (10/10 source-hit coverage).\n'
            '- Boundary audit: 7 directly candidate-qualified, 1 source-backed wording normalization, and 2 source-unrecoverable singleton pseudo-Questions retired fail-closed.\n'
            '- Candidate/research work may proceed only for the 8 active Canonicals after the full integrity gates pass.\n'
        )
    TASK_PATH.write_text(task.rstrip() + '\n', encoding='utf-8')


def write_boundary() -> None:
    lines = [
        '# Answer Batch 0026 — Source-First Boundary Audit',
        '',
        '- Evidence boundary: frozen `review/reports/ANSWER_BATCH_0026_SOURCE_PACKET.{json,md}` only, with raw caption/image text preferred over derived tagged wording.',
        '- Audit rule: preserve real recoverable Questions; normalize only source-inflated wording; fail closed when no unique executable problem identity can be recovered.',
        '- Result: original 10 Canonicals → 8 active, 2 excluded as `incomplete_or_unreadable`.',
        '',
        '| Canonical | Disposition | Source-first basis |',
        '| --- | --- | --- |',
    ]
    for cid in sorted(QUALIFIED):
        lines.append(f'| `{cid}` | candidate-qualified | {QUALIFIED[cid]} |')
    lines.append(
        f'| `{LIST_TO_MAP["canonical_id"]}` | normalize + candidate-qualified | Raw caption asks only “{LIST_TO_MAP["new_text"]}”; derived wording added unsupported “three or more” and mandatory Stream API constraints. Canonical identity is retained while source Question wording/id is narrowed. |'
    )
    for cid in sorted(RETIRE):
        lines.append(f'| `{cid}` | exclude — incomplete_or_unreadable | {RETIRE[cid]["explanation"]} |')
    lines += [
        '',
        '## Guardrails for the next stage',
        '',
        '- `cq_q_50ef...`: do not silently choose between “deduplicate while keeping one” and “delete all values that repeat”; a formal answer must surface both contracts or explicitly require clarification.',
        '- `cq_q_51683...`: state whether touching endpoints overlap before presenting a greedy implementation.',
        '- `cq_q_54f9...`: do not claim O(n) for arbitrary unsorted intervals; explain the ordering/bounded-domain condition that makes the requested linear bound achievable.',
        '- No answer is promoted by this boundary remediation. Candidate authoring, isolated review, evidence/code gates and pilot approval remain separate stages.',
        '',
    ]
    BOUNDARY_PATH.parent.mkdir(parents=True, exist_ok=True)
    BOUNDARY_PATH.write_text('\n'.join(lines), encoding='utf-8')


def main() -> None:
    verify_source_packet()
    canonicals = read_jsonl(CANONICAL_PATH)
    questions = read_jsonl(QUESTION_PATH)
    progress = read_json(PROGRESS_PATH)
    audit = read_json(VALIDITY_AUDIT_PATH)

    expected_active = set(QUALIFIED) | {LIST_TO_MAP['canonical_id']} | set(RETIRE)
    present = {row.get('canonical_id') for row in canonicals}
    if not expected_active <= present:
        already_retired = set(RETIRE) - present
        if already_retired != set(RETIRE):
            raise SystemExit(f'batch 0026 active-set drift before remediation: missing={sorted(expected_active-present)}')

    normalize_list_to_map(canonicals, questions, audit)
    retire_unrecoverable(canonicals, questions, progress, audit)
    refresh_audit_counts(audit)
    write_jsonl(CANONICAL_PATH, canonicals)
    write_jsonl(QUESTION_PATH, questions)
    write_json(PROGRESS_PATH, progress)
    write_json(VALIDITY_AUDIT_PATH, audit)
    write_task()
    write_boundary()

    active_ids = {row.get('canonical_id') for row in canonicals}
    if set(RETIRE) & active_ids:
        raise SystemExit('retired batch 0026 Canonicals remain active')
    required = set(QUALIFIED) | {LIST_TO_MAP['canonical_id']}
    if not required <= active_ids:
        raise SystemExit('qualified batch 0026 Canonical disappeared')
    print('PASS batch 0026 source-first remediation: original=10 active=8 retired=2 normalized=1')


if __name__ == '__main__':
    main()
