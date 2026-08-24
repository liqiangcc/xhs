#!/usr/bin/env python3
"""Apply source-first boundary dispositions for Answer Batch 0021.

This bounded mutation is intentionally conservative:
- retire one singleton coding record whose surviving source only says
  "二叉树相关操作" and therefore does not preserve an executable contract;
- normalize one recoverable package-interval question whose structured wording
  incorrectly prescribed Difference Array / Sweep Line even though the source
  only asks for the best time/space-complexity solution.

Generated Question/index projections are rebuilt by the calling workflow.
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
TASK_PATH = ROOT / 'tasks/answer-batches/TASK-20260711-0313-answer-batch-0021.md'
BOUNDARY_PATH = ROOT / 'review/content_build/answer_batch_0021/source_boundary_audit.md'

NORMALIZE = {
    'canonical_id': 'cq_q_3a1c2667429257c4fbe7e2d8d8012096',
    'old_qid': '3a1c2667429257c4fbe7e2d8d8012096',
    'old_text': '算法场景建模：假设一个城市有1亿个包裹的存取记录（存入时间与取出时间）。如何找出全天包裹堆积量最高的时间点及持续时长？要求给出基于差分数组（Difference Array）或扫描线算法（Sweep Line）的最优时间与空间复杂度方案',
    'new_text': '给定一天内1亿个包裹的存入和取出时间，如何找出未取出包裹数最多的时间段及持续时长？方案的时间和空间复杂度是多少？',
    'new_title': '算法：给定一天内 1 亿个包裹的存入和取出时间，如何找出未取出包裹数最多的时间段及持续时长？时间和空间复杂度是多少？',
    'new_qid': 'f2d52be391d5a320a5460d80e4256278',
    'note_path': ROOT / 'note_tagged/68b81a39000000001c034f47.json',
    'new_entities': ['存取时间区间', '区间峰值'],
}

RETIRE = {
    'cq_q_36adef6f4fb0a868fca32118d03969a5': {
        'expected_original': '算法：二叉树相关操作',
        'explanation': (
            '仓库最强原始来源在“算法题”下只保留“二叉树相关操作”，没有说明要实现遍历、深度、'
            '构造、查找、路径、平衡、序列化或其它哪一种具体操作，也没有输入输出、约束或边界。'
            '不同二叉树题目的可执行合同互不等价；为该标题生成任意一种实现都会把推断伪装成原题。'
            '因此按 incomplete_or_unreadable fail closed，等待更强来源后再恢复。'
        ),
    },
}

QUALIFIED = [
    'cq_q_37245bc43848028f006b2e4eaea7500c',
    'cq_q_37772fa23763570fb8d04764450230d3',
    'cq_q_377898b5b67a6219eaa583c6d2e21081',
    'cq_q_37b42623861093a397be5bff1ee3fad6',
    'cq_q_37c73385b683ba395f0d066744d02f37',
    'cq_q_37ffe67ab69164654b0a19aa57b410df',
    'cq_q_39a734b5a5602f2d965f9e2f35a50514',
    'cq_q_3a314d375a1b0bdf127953e8614906e0',
]


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


def normalize_recoverable(canonicals: list[dict], questions: list[dict], audit: dict) -> bool:
    spec = NORMALIZE
    cid = spec['canonical_id']
    old_qid = spec['old_qid']
    new_qid = spec['new_qid']
    if question_id(spec['new_text']) != new_qid:
        raise SystemExit('normalized Question id drifted from expected digest')

    changed = False
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
        tagged['tech_entities'] = list(spec['new_entities'])
        write_json(spec['note_path'], note)
        changed = True
    elif tagged.get('original_question') != spec['new_text']:
        raise SystemExit(f'{cid}: normalized tagged wording drifted')

    canonical_matches = [row for row in canonicals if row.get('canonical_id') == cid]
    if len(canonical_matches) != 1:
        raise SystemExit(f'{cid}: expected one Canonical')
    canonical = canonical_matches[0]
    owned = list(canonical.get('question_ids') or [])
    if owned == [old_qid]:
        canonical['question_ids'] = [new_qid]
        changed = True
    elif owned != [new_qid]:
        raise SystemExit(f'{cid}: Canonical ownership drifted: {owned}')
    old_title = spec['old_text']
    if canonical.get('canonical_title') == old_title:
        canonical['canonical_title'] = spec['new_title']
        canonical['aliases'] = [spec['new_title']]
        canonical['primary_entities'] = list(spec['new_entities'])
        changed = True
    elif canonical.get('canonical_title') != spec['new_title']:
        raise SystemExit(f'{cid}: Canonical title drifted')

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
        row['tech_entities'] = list(spec['new_entities'])
        changed = True
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
            changed = True
        elif decision.get('question_id') != new_qid or decision.get('original_question') != spec['new_text']:
            raise SystemExit(f'{cid}: validity-audit normalization drifted')

    answer_path = ROOT / 'review/answers' / f'{cid}.md'
    answer = answer_path.read_text(encoding='utf-8')
    if spec['old_text'] in answer:
        answer_path.write_text(answer.replace(spec['old_text'], spec['new_title']), encoding='utf-8')
        changed = True
    elif spec['new_title'] not in answer:
        raise SystemExit(f'{cid}: active Answer contains neither old nor normalized title')

    print(f'Normalized source boundary {cid}: {old_qid} -> {new_qid}')
    return changed


def retire_unrecoverable(canonicals: list[dict], questions: list[dict], progress: dict, audit: dict) -> tuple[list[dict], bool]:
    changed = False
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
        if row.get('canonical_id') != cid or row.get('is_valid_for_library') is not True:
            raise SystemExit(f'{cid}: Question binding/validity drifted')
        if row.get('original_question') != spec['expected_original']:
            raise SystemExit(f'{cid}: original Question wording drifted')
        if (ROOT / 'review/candidates/answers' / f'{cid}.md').exists() or (ROOT / 'review/evidence' / f'{cid}.json').exists():
            raise SystemExit(f'{cid}: candidate/evidence appeared after source extraction; re-review before retirement')

        ref = (row['source_note_id'], row['source_question_index'])
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
            changed = True
        elif previous != replacement:
            decisions[decisions.index(previous)] = replacement
            by_ref[ref] = replacement
            changed = True

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
        changed = True
        print(f'Retired source-unrecoverable singleton {cid}')

    audit['decisions'] = decisions
    return canonicals, changed


def update_task_and_boundary() -> None:
    task = TASK_PATH.read_text(encoding='utf-8')
    if 'Active after source-boundary audit' not in task:
        task = task.replace('- Canonical count: `10`', '- Original batch Canonical count: `10`\n- Active after source-boundary audit: `9`')
    task = task.replace(
        '- `cq_q_36adef6f4fb0a868fca32118d03969a5` — coding; risks: long_tail_baseline, placeholder_implementation',
        '- `cq_q_36adef6f4fb0a868fca32118d03969a5` — retired fail-closed: source only says “二叉树相关操作”; executable contract is unrecoverable.',
    )
    task = task.replace(
        '- `cq_q_3a1c2667429257c4fbe7e2d8d8012096` — coding; risks: long_tail_baseline, placeholder_implementation',
        '- `cq_q_3a1c2667429257c4fbe7e2d8d8012096` — coding; normalized to source-preserving package interval peak wording; removed inferred prescribed algorithms.',
    )
    marker = '## Source-first boundary disposition'
    if marker not in task:
        task += (
            '\n## Source-first boundary disposition\n\n'
            '- Repository source packet: `review/reports/ANSWER_BATCH_0021_SOURCE_PACKET.{json,md}` (10/10 source-hit coverage).\n'
            '- Boundary audit: 8 directly candidate-qualified, 1 recoverable normalization, 1 source-unrecoverable singleton retired fail-closed.\n'
            '- Candidate/research work may proceed only for the 9 active Canonicals after the full integrity gates pass.\n'
        )
    TASK_PATH.write_text(task.rstrip() + '\n', encoding='utf-8')

    BOUNDARY_PATH.parent.mkdir(parents=True, exist_ok=True)
    BOUNDARY_PATH.write_text(
        '''# Answer Batch 0021 — Source-first Boundary Audit

This audit was performed from `review/reports/ANSWER_BATCH_0021_SOURCE_PACKET.{json,md}` and the repository-local caption/image transcripts before candidate authoring. It deliberately separates source recoverability from answer correctness.

## Verdict

- Original batch Canonicals: 10
- Directly candidate-qualified: 8
- Recoverable normalization: 1
- Source-unrecoverable / excluded: 1
- Active after boundary remediation: 9

## Dispositions

| Canonical | Disposition | Source-first reason |
| --- | --- | --- |
| `cq_q_36adef6f4fb0a868fca32118d03969a5` | exclude / `incomplete_or_unreadable` | Strongest source only says “二叉树相关操作”; no concrete operation or executable contract survives. |
| `cq_q_37245bc43848028f006b2e4eaea7500c` | candidate-qualified | Source explicitly asks to implement a singly linked-list structure with CRUD. |
| `cq_q_37772fa23763570fb8d04764450230d3` | candidate-qualified | Source explicitly asks to use C to distinguish current system 32-bit vs 64-bit; answer must state the process-vs-OS observability limitation. |
| `cq_q_377898b5b67a6219eaa583c6d2e21081` | candidate-qualified | Source preserves the positive-integer transition rules and minimum-operation objective. |
| `cq_q_37b42623861093a397be5bff1ee3fad6` | candidate-qualified | Source explicitly says “LC 25. K 个一组翻转链表”, making the problem identity recoverable. |
| `cq_q_37c73385b683ba395f0d066744d02f37` | candidate-qualified | Source explicitly asks for multi-threaded array sorting; implementation must state thread-count/merge assumptions rather than invent them as source facts. |
| `cq_q_37ffe67ab69164654b0a19aa57b410df` | candidate-qualified | Source explicitly names topological sort; representation/API details must be stated as answer-side assumptions. |
| `cq_q_39a734b5a5602f2d965f9e2f35a50514` | candidate-qualified | Source explicitly asks for pairs summing to 10 in an increasing array. |
| `cq_q_3a1c2667429257c4fbe7e2d8d8012096` | normalize, then candidate-qualified | Source asks for the maximum outstanding-package time interval and time/space complexity, but does not prescribe Difference Array or Sweep Line. Prescribing those methods in the Question was unsupported enrichment. |
| `cq_q_3a314d375a1b0bdf127953e8614906e0` | candidate-qualified | Source question directly asks for the first common node of two intersecting singly linked lists. |

## Normalization

`cq_q_3a1c2667429257c4fbe7e2d8d8012096` remains the Canonical identity, while its source Question is normalized from the derived solution-prescribing wording to:

> 给定一天内1亿个包裹的存入和取出时间，如何找出未取出包裹数最多的时间段及持续时长？方案的时间和空间复杂度是多少？

The normalized Question id is `f2d52be391d5a320a5460d80e4256278`. `Difference Array` / `Sweep Line` may be evaluated as answer strategies, but they are not source facts and therefore are removed from Question/Canonical metadata.

## Fail-closed exclusion

`cq_q_36adef6f4fb0a868fca32118d03969a5` is archived rather than answered. The source phrase “二叉树相关操作” is a category fragment, not a recoverable coding contract. The exclusion is recorded in `config/question_validity_audit.json` with an explicit explanation so source rows remain auditable.

## Next gate

Only after repository projections are rebuilt and `check_question_coverage`, `canonical check`, `review integrity`, strict answer validation, full validation, unit tests, and all answer CI gates pass may batch 0021 candidate work begin.
''',
        encoding='utf-8',
    )


def main() -> int:
    canonicals = read_jsonl(CANONICAL_PATH)
    questions = read_jsonl(QUESTION_PATH)
    progress = read_json(PROGRESS_PATH)
    audit = read_json(VALIDITY_AUDIT_PATH)

    normalize_recoverable(canonicals, questions, audit)
    canonicals, _ = retire_unrecoverable(canonicals, questions, progress, audit)
    update_task_and_boundary()

    decisions = list(audit.get('decisions', []))
    decisions.sort(key=lambda d: (str(d.get('source_note_id', '')), int(d.get('source_question_index', 0))))
    audit['decisions'] = decisions
    audit['audited_at'] = '2026-08-24'
    audit['include_count'] = sum(1 for d in decisions if d.get('decision') == 'include')
    audit['exclude_count'] = sum(1 for d in decisions if d.get('decision') == 'exclude')
    write_json(VALIDITY_AUDIT_PATH, audit)
    write_jsonl(CANONICAL_PATH, sorted(canonicals, key=lambda row: row['canonical_id']))
    write_jsonl(QUESTION_PATH, sorted(questions, key=lambda row: (row.get('source_note_id', ''), int(row.get('source_question_index', 0)), row.get('question_id', ''))))
    progress['updated_at'] = '2026-08-24'
    progress['items'] = sorted(progress.get('items', []), key=lambda item: item.get('canonical_id', ''))
    write_json(PROGRESS_PATH, progress)

    active = {row.get('canonical_id') for row in canonicals}
    for cid in QUALIFIED + [NORMALIZE['canonical_id']]:
        if cid not in active:
            raise SystemExit(f'candidate-qualified Canonical unexpectedly absent after remediation: {cid}')
    if next(iter(RETIRE)) in active:
        raise SystemExit('retired Canonical still active after remediation')

    print('Applied Answer Batch 0021 source-boundary remediation.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
