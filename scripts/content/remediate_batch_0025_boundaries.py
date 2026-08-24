#!/usr/bin/env python3
"""Apply source-first boundary dispositions for Answer Batch 0025.

Repository-source-only bounded mutation:
- narrow one inflated topological-sort Question to the wording actually preserved by source;
- reclassify one coin-flip reasoning prompt from Coding to Concept because source asks only for reasoning;
- retire two singleton Questions whose source cannot recover a unique executable contract;
- leave the remaining six source-qualified coding Questions active.

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
TASK_PATH = ROOT / 'tasks/answer-batches/TASK-20260711-0313-answer-batch-0025.md'
BOUNDARY_PATH = ROOT / 'review/content_build/answer_batch_0025/source_boundary_audit.md'
SOURCE_PACKET_PATH = ROOT / 'review/reports/ANSWER_BATCH_0025_SOURCE_PACKET.json'

TOPO_NORMALIZE = {
    'canonical_id': 'cq_q_497537f6fc79fb11fe854f142aa59d1e',
    'old_qid': '497537f6fc79fb11fe854f142aa59d1e',
    'old_text': '算法手撕：图的拓扑排序（Topological Sort）及其在依赖管理场景下的应用。',
    'new_text': '算法题：图的拓扑排序',
    'new_qid': 'f458a6a9baa833f5bcd4c2465098be0d',
    'note_path': ROOT / 'note_tagged/68bdb040000000001d00a613.json',
    'new_domain': {'l1': '算法与数据结构', 'l2': '图'},
    'new_entities': ['拓扑排序'],
}

COIN_TYPE_FIX = {
    'canonical_id': 'cq_q_4ba0bfbd9b87d9415d9724ee0db55ff6',
    'qid': '4ba0bfbd9b87d9415d9724ee0db55ff6',
    'text': '逻辑题：1-N个硬币翻面问题 (整除规律分析)',
    'note_path': ROOT / 'note_tagged/666c3aee000000000e03140b.json',
    'old_type': '算法手撕_Coding',
    'new_type': '八股文_Concept',
}

QUALIFIED = {
    'cq_q_4b3ef4f6983ba06fff2fe65aeb96f0a7': (
        'Caption explicitly asks to implement a stack with one queue and requires only one sub-operation to be O(n).'
    ),
    'cq_q_4d49a2c53d787ce1d520075e3493152e': (
        'Image transcript explicitly records the binary-tree longest-distance/diameter coding problem.'
    ),
    'cq_q_4d502e2e2c294d9f9dd468cff39c0162': (
        'Caption explicitly asks for the median of two unsorted arrays that may contain duplicates.'
    ),
    'cq_q_4e2e32002bd212ba6a2a232d0761421e': (
        'Image transcript preserves int[] a, k <= a.length, and the requirement to return the k smallest values.'
    ),
    'cq_q_4ef5329ef53731815f32df4a2942c8d2': (
        'Caption explicitly asks to rebuild a tree from inorder/postorder traversals and print preorder non-recursively.'
    ),
    'cq_q_4f3244bca47814cd02291ecda86cad4c': (
        'Caption explicitly asks to implement a stack using two queues.'
    ),
}

RETIRE = {
    'cq_q_4b55831a928b320f47710e2de666045e': {
        'expected_original': '算法：实现一道简单算法题。',
        'explanation': (
            '仓库最强来源只保留“手撕：一道简单题”，没有题目、输入、输出、约束、样例或稳定的问题标识；'
            'source packet 还显示原 tagged Question 已明确 is_valid_for_library=false。'
            '无法从“简单题”唯一恢复任何可执行合同，因此按 incomplete_or_unreadable fail closed。'
        ),
        'task_note': 'retired fail-closed: source preserves only “一道简单题” and no executable problem identity.',
    },
    'cq_q_4f04a54536a8856b265b4cfb49f1325a': {
        'expected_original': '算法：找出字符串中出现次数最多的字母，并对该字母前面的数字进行求和。',
        'explanation': (
            '来源只重复题名“找出字符串中出现次数最多的字母，并对前面的数字求和”，没有保留字符串语法。'
            '无法判断数字是单个数字还是多位整数、数字与字母如何配对、连续数字/无数字如何处理、并列最高频字母如何选择；'
            '这些差异会改变解析与输出，当前材料不足以得到唯一可验证实现，因此按 incomplete_or_unreadable fail closed。'
        ),
        'task_note': 'retired fail-closed: source lacks the string grammar and tie rules needed for a unique parser/algorithm contract.',
    },
}


def normalize_text(text: str) -> str:
    return re.sub(r'[^\w\u4e00-\u9fa5]', '', str(text).lower())


def question_id(text: str) -> str:
    return hashlib.md5(normalize_text(text).encode('utf-8')).hexdigest()


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


def verify_source_packet() -> None:
    packet = read_json(SOURCE_PACKET_PATH)
    if packet.get('schema_version') != 'answer_batch_source_packet.v2' or packet.get('batch') != '0025':
        raise SystemExit('unexpected batch 0025 source packet identity')
    if packet.get('source_policy') != 'repository_source_only_exact_id_or_exact_normalized_wording_no_fuzzy_inference':
        raise SystemExit('unexpected batch 0025 source policy')
    entries = packet.get('canonicals') or []
    if len(entries) != 10:
        raise SystemExit(f'expected 10 source-packet Canonicals, got {len(entries)}')
    expected = set(QUALIFIED) | {TOPO_NORMALIZE['canonical_id'], COIN_TYPE_FIX['canonical_id']} | set(RETIRE)
    ids = {entry.get('canonical_id') for entry in entries}
    if ids != expected:
        raise SystemExit(f'batch 0025 source-packet drift: missing={sorted(expected-ids)}, extra={sorted(ids-expected)}')
    missing = [entry.get('canonical_id') for entry in entries if not entry.get('source_hits')]
    if missing:
        raise SystemExit(f'batch 0025 source packet has missing hits: {missing}')


def normalize_topological_sort(canonicals: list[dict], questions: list[dict], audit: dict) -> None:
    spec = TOPO_NORMALIZE
    cid = spec['canonical_id']
    old_qid = spec['old_qid']
    new_qid = spec['new_qid']
    if question_id(spec['new_text']) != new_qid:
        raise SystemExit('normalized topological-sort Question id drifted')

    note = read_json(spec['note_path'])
    matches = [q for q in note.get('tagged_questions', []) if q.get('question_id') in {old_qid, new_qid}]
    if len(matches) != 1:
        raise SystemExit(f'{cid}: expected one old/new tagged Question, got {len(matches)}')
    tagged = matches[0]
    if tagged.get('question_id') == old_qid:
        if tagged.get('original_question') != spec['old_text']:
            raise SystemExit(f'{cid}: tagged old wording drifted')
        tagged['question_id'] = new_qid
        tagged['original_question'] = spec['new_text']
        tagged['domain'] = {'l1': '计算机基础', 'l2': '算法'}
        tagged['tech_entities'] = list(spec['new_entities'])
        write_json(spec['note_path'], note)
    elif tagged.get('original_question') != spec['new_text']:
        raise SystemExit(f'{cid}: normalized tagged wording drifted')

    canonical = next((row for row in canonicals if row.get('canonical_id') == cid), None)
    if not canonical:
        raise SystemExit(f'{cid}: Canonical missing')
    owned = list(canonical.get('question_ids') or [])
    if owned == [old_qid]:
        canonical['question_ids'] = [new_qid]
    elif owned != [new_qid]:
        raise SystemExit(f'{cid}: Canonical ownership drifted: {owned}')
    if canonical.get('canonical_title') == spec['old_text']:
        canonical['canonical_title'] = spec['new_text']
        canonical['aliases'] = [spec['new_text']]
        canonical['primary_domain'] = dict(spec['new_domain'])
        canonical['primary_entities'] = list(spec['new_entities'])
    elif canonical.get('canonical_title') != spec['new_text']:
        raise SystemExit(f'{cid}: Canonical title drifted')
    else:
        canonical['primary_domain'] = dict(spec['new_domain'])
        canonical['primary_entities'] = list(spec['new_entities'])

    old_rows = [row for row in questions if row.get('question_id') == old_qid]
    new_rows = [row for row in questions if row.get('question_id') == new_qid]
    if old_rows and new_rows:
        raise SystemExit(f'{cid}: both old and normalized Question rows exist')
    rows = old_rows or new_rows
    if len(rows) != 1:
        raise SystemExit(f'{cid}: expected one old/new Question row, got {len(rows)}')
    row = rows[0]
    if row.get('canonical_id') != cid:
        raise SystemExit(f'{cid}: Question binding drifted')
    source_ref = (row.get('source_note_id'), row.get('source_question_index'))
    if row.get('question_id') == old_qid:
        if row.get('original_question') != spec['old_text']:
            raise SystemExit(f'{cid}: projected old wording drifted')
        row['question_id'] = new_qid
        row['original_question'] = spec['new_text']
        row['domain'] = {'l1': '计算机基础', 'l2': '算法'}
        row['tech_entities'] = list(spec['new_entities'])
    elif row.get('original_question') != spec['new_text']:
        raise SystemExit(f'{cid}: normalized projected wording drifted')

    decisions = list(audit.get('decisions', []))
    matches = [d for d in decisions if (d.get('source_note_id'), d.get('source_question_index')) == source_ref]
    if len(matches) > 1:
        raise SystemExit(f'{cid}: duplicate validity-audit decisions')
    if matches:
        decision = matches[0]
        if decision.get('decision') != 'include':
            raise SystemExit(f'{cid}: recoverable Question must remain included')
        if decision.get('question_id') == old_qid:
            decision['question_id'] = new_qid
            decision['original_question'] = spec['new_text']
        elif decision.get('question_id') != new_qid or decision.get('original_question') != spec['new_text']:
            raise SystemExit(f'{cid}: validity-audit normalization drifted')

    answer_path = ROOT / 'review/answers' / f'{cid}.md'
    answer = answer_path.read_text(encoding='utf-8')
    if spec['old_text'] in answer:
        answer_path.write_text(answer.replace(spec['old_text'], spec['new_text']), encoding='utf-8')
    elif spec['new_text'] not in answer:
        raise SystemExit(f'{cid}: active Answer contains neither old nor normalized title')

    print(f'Normalized source boundary {cid}: {old_qid} -> {new_qid}')


def correct_coin_type(canonicals: list[dict], questions: list[dict]) -> None:
    spec = COIN_TYPE_FIX
    cid = spec['canonical_id']
    qid = spec['qid']

    note = read_json(spec['note_path'])
    matches = [q for q in note.get('tagged_questions', []) if q.get('question_id') == qid]
    if len(matches) != 1:
        raise SystemExit(f'{cid}: expected one coin source Question, got {len(matches)}')
    tagged = matches[0]
    if tagged.get('original_question') != spec['text']:
        raise SystemExit(f'{cid}: coin source wording drifted')
    if tagged.get('question_type') == spec['old_type']:
        tagged['question_type'] = spec['new_type']
        write_json(spec['note_path'], note)
    elif tagged.get('question_type') != spec['new_type']:
        raise SystemExit(f'{cid}: unexpected source question_type: {tagged.get("question_type")}')

    rows = [row for row in questions if row.get('question_id') == qid]
    if len(rows) != 1 or rows[0].get('canonical_id') != cid:
        raise SystemExit(f'{cid}: projected coin Question missing or misbound')
    if rows[0].get('question_type') == spec['old_type']:
        rows[0]['question_type'] = spec['new_type']
    elif rows[0].get('question_type') != spec['new_type']:
        raise SystemExit(f'{cid}: unexpected projected coin question_type: {rows[0].get("question_type")}')

    if not any(row.get('canonical_id') == cid for row in canonicals):
        raise SystemExit(f'{cid}: Canonical missing')
    print(f'Corrected source type {cid}: {spec["old_type"]} -> {spec["new_type"]}')


def retire_unrecoverable(canonicals: list[dict], questions: list[dict], progress: dict, audit: dict) -> list[dict]:
    decisions = list(audit.get('decisions', []))
    by_ref = {(d.get('source_note_id'), d.get('source_question_index')): d for d in decisions}

    for cid, spec in RETIRE.items():
        qid = cid.removeprefix('cq_q_')
        canonical = next((row for row in canonicals if row.get('canonical_id') == cid), None)
        if canonical is None:
            if any(row.get('canonical_id') == cid for row in questions):
                raise SystemExit(f'{cid}: Canonical absent but Question binding remains')
            if (ROOT / 'review/answers' / f'{cid}.md').exists():
                raise SystemExit(f'{cid}: Canonical absent but active Answer remains')
            continue

        if list(canonical.get('question_ids') or []) != [qid] or int(canonical.get('frequency', 0)) != 1:
            raise SystemExit(f'{cid}: expected singleton Canonical before retirement')
        rows = [row for row in questions if row.get('question_id') == qid]
        if len(rows) != 1:
            raise SystemExit(f'{cid}: expected one Question row, got {len(rows)}')
        row = rows[0]
        if row.get('canonical_id') != cid:
            raise SystemExit(f'{cid}: Question binding drifted')
        if row.get('original_question') != spec['expected_original']:
            raise SystemExit(f'{cid}: original Question wording drifted')

        if (ROOT / 'review/candidates/answers' / f'{cid}.md').exists() or (ROOT / 'review/evidence' / f'{cid}.json').exists() or (ROOT / 'review/candidates/audits' / f'{cid}.json').exists():
            raise SystemExit(f'{cid}: candidate/evidence appeared after source extraction; re-review before retirement')

        ref = (row.get('source_note_id'), row.get('source_question_index'))
        if None in ref:
            raise SystemExit(f'{cid}: projected Question lacks stable source locator')
        replacement = {
            'source_note_id': row['source_note_id'],
            'source_question_index': row['source_question_index'],
            'question_id': qid,
            'original_question': row['original_question'],
            'decision': 'exclude',
            'exclusion_reason': 'incomplete_or_unreadable',
            'exclusion_note': spec['explanation'],
        }
        previous = by_ref.get(ref)
        if previous is None:
            decisions.append(replacement)
            by_ref[ref] = replacement
        elif previous != replacement:
            decisions[decisions.index(previous)] = replacement
            by_ref[ref] = replacement

        canonicals = [item for item in canonicals if item.get('canonical_id') != cid]

        before = len(progress.get('items', []))
        progress['items'] = [item for item in progress.get('items', []) if item.get('canonical_id') != cid]
        if len(progress['items']) != before - 1:
            raise SystemExit(f'{cid}: expected exactly one ReviewProgress item')

        active = ROOT / 'review/answers' / f'{cid}.md'
        archive = ROOT / 'review/archive/answers' / f'{cid}.md'
        if not active.exists():
            raise SystemExit(f'{cid}: active Answer missing')
        archive.parent.mkdir(parents=True, exist_ok=True)
        if archive.exists():
            if archive.read_bytes() != active.read_bytes():
                raise SystemExit(f'{cid}: existing archive differs from active Answer')
            active.unlink()
        else:
            shutil.move(str(active), str(archive))
        print(f'Retired source-unrecoverable singleton {cid}')

    audit['decisions'] = decisions
    return canonicals


def update_task_and_boundary() -> None:
    task = TASK_PATH.read_text(encoding='utf-8')
    if 'Active after source-boundary audit' not in task:
        task = task.replace(
            '- Canonical count: `10`',
            '- Original batch Canonical count: `10`\n- Active after source-boundary audit: `8`',
        )

    replacements = {
        TOPO_NORMALIZE['canonical_id']:
            'coding; normalized to source-backed topological-sort wording without inventing a dependency-management subtask.',
        COIN_TYPE_FIX['canonical_id']:
            'concept; source asks for divisibility/parity reasoning, not code; corrected from erroneous Coding metadata.',
    }
    for cid, suffix in replacements.items():
        old = f'- `{cid}` — coding; risks: long_tail_baseline, placeholder_implementation'
        new = f'- `{cid}` — {suffix}'
        if old in task:
            task = task.replace(old, new)
        elif new not in task:
            raise SystemExit(f'batch 0025 task line drifted: {cid}')

    for cid, spec in RETIRE.items():
        old = f'- `{cid}` — coding; risks: long_tail_baseline, placeholder_implementation'
        new = f'- `{cid}` — {spec["task_note"]}'
        if old in task:
            task = task.replace(old, new)
        elif new not in task:
            raise SystemExit(f'batch 0025 task line drifted: {cid}')

    if '## Source-first boundary disposition' not in task:
        task = task.rstrip() + "\n\n## Source-first boundary disposition\n\n"
        task += "- Repository source packet: `review/reports/ANSWER_BATCH_0025_SOURCE_PACKET.{json,md}` (10/10 source-hit coverage, including exact normalized-wording recovery for the stale simple-algorithm id).\n"
        task += "- Boundary audit: 6 directly candidate-qualified, 1 recoverable wording normalization, 1 answer-type metadata correction, and 2 source-unrecoverable singleton records retired fail-closed.\n"
        task += "- Candidate/research work may proceed only for the 8 active Canonicals after the full integrity gates pass.\n"
    TASK_PATH.write_text(task, encoding='utf-8')

    BOUNDARY_PATH.parent.mkdir(parents=True, exist_ok=True)
    rows = [
        '# Answer Batch 0025 — Source-first Boundary Audit',
        '',
        'This audit was performed from `review/reports/ANSWER_BATCH_0025_SOURCE_PACKET.{json,md}` and repository-local caption/image transcripts before candidate authoring. It fails closed when the source cannot uniquely define an executable contract and removes unsupported detail from generated Canonical wording.',
        '',
        '## Verdict',
        '',
        '- Original batch Canonicals: 10',
        '- Directly candidate-qualified: 6',
        '- Recoverable wording normalization: 1',
        '- Answer-type metadata correction: 1',
        '- Source-unrecoverable / excluded: 2',
        '- Active after boundary remediation: 8',
        '',
        '## Dispositions',
        '',
        '| Canonical | Disposition | Source-first reason |',
        '| --- | --- | --- |',
        f'| `{TOPO_NORMALIZE["canonical_id"]}` | normalize, then candidate-qualified | Caption preserves only “算法题：图的拓扑排序”. The current dependency-management application clause is generated detail not present in source, so the Question is narrowed to the stable topological-sort problem identity. |',
        f'| `{COIN_TYPE_FIX["canonical_id"]}` | reclassify Concept, then candidate-qualified | Caption fully preserves the 1..N coin/divisibility flipping rule and explicitly says “说思路”; this is a parity/divisor reasoning problem, not a handwriting-code request. |',
    ]
    for cid, reason in QUALIFIED.items():
        rows.append(f'| `{cid}` | candidate-qualified | {reason} |')
    for cid, spec in RETIRE.items():
        rows.append(f'| `{cid}` | exclude / `incomplete_or_unreadable` | {spec["explanation"]} |')
    rows.extend([
        '',
        '## Normalization',
        '',
        f'`{TOPO_NORMALIZE["canonical_id"]}` keeps its Canonical identity but its source Question is narrowed to `算法题：图的拓扑排序`; normalized Question id: `{TOPO_NORMALIZE["new_qid"]}`. The final answer may explain dependency-management as an example only if clearly labeled as an application, not as part of the recovered interview contract.',
        '',
        '## Type correction',
        '',
        f'`{COIN_TYPE_FIX["canonical_id"]}` keeps its Question identity and is reclassified from `{COIN_TYPE_FIX["old_type"]}` to `{COIN_TYPE_FIX["new_type"]}`. Its source asks for the reasoning and final set of face-up coins, not runnable code.',
        '',
        '## Fail-closed exclusions',
        '',
        'The two excluded singleton Canonicals are archived rather than answered. Each source row remains auditable through `config/question_validity_audit.json` with a specific `incomplete_or_unreadable` explanation.',
        '',
        '## Candidate constraints',
        '',
        '- The one-queue stack source does not say which operation must be O(n); a candidate may choose push-heavy or pop-heavy and must state that choice.',
        '- The unsorted-two-array median source allows duplicates and explicitly rejected relying only on the sorted-array LeetCode 4 contract; a candidate must solve the unsorted input stated by source.',
        '- The top-k-smallest source gives `k <= a.length`; empty-array behavior is outside source and should be stated as an API assumption if covered.',
        '',
        '## Next gate',
        '',
        'Only after Question/index/type projections are rebuilt and all coverage, canonical, review-integrity, strict answer, unit, semantic/evidence/code/coverage gates pass may batch 0025 candidate work begin.',
        '',
    ])
    BOUNDARY_PATH.write_text('\n'.join(rows), encoding='utf-8')


def main() -> None:
    verify_source_packet()
    canonicals = read_jsonl(CANONICAL_PATH)
    questions = read_jsonl(QUESTION_PATH)
    progress = read_json(PROGRESS_PATH)
    audit = read_json(VALIDITY_AUDIT_PATH)

    expected = set(QUALIFIED) | {TOPO_NORMALIZE['canonical_id'], COIN_TYPE_FIX['canonical_id']} | set(RETIRE)
    active_ids = {row.get('canonical_id') for row in canonicals}
    missing = sorted(expected - active_ids)
    unexpected = [cid for cid in missing if cid not in RETIRE]
    if unexpected:
        raise SystemExit(f'batch 0025 active inputs disappeared: {unexpected}')

    normalize_topological_sort(canonicals, questions, audit)
    correct_coin_type(canonicals, questions)
    canonicals = retire_unrecoverable(canonicals, questions, progress, audit)

    write_jsonl(CANONICAL_PATH, canonicals)
    write_jsonl(QUESTION_PATH, questions)
    write_json(PROGRESS_PATH, progress)
    write_json(VALIDITY_AUDIT_PATH, audit)
    update_task_and_boundary()

    final_ids = {row.get('canonical_id') for row in canonicals}
    for cid in set(QUALIFIED) | {TOPO_NORMALIZE['canonical_id'], COIN_TYPE_FIX['canonical_id']}:
        if cid not in final_ids:
            raise SystemExit(f'candidate-qualified Canonical disappeared: {cid}')
    leaked = sorted(set(RETIRE) & final_ids)
    if leaked:
        raise SystemExit(f'retired Canonicals remain active: {leaked}')


if __name__ == '__main__':
    main()
