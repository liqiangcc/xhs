#!/usr/bin/env python3
"""Apply source-first boundary dispositions for Answer Batch 0022.

This bounded mutation is intentionally conservative:
- retire three singleton coding records whose strongest repository source does
  not preserve an executable problem contract;
- normalize one recoverable string-extraction Question so its wording matches
  the source/image evidence instead of inventing a generic "specified substring"
  contract;
- keep the remaining six source-qualified Canonicals active for candidate work.

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
TASK_PATH = ROOT / 'tasks/answer-batches/TASK-20260711-0313-answer-batch-0022.md'
BOUNDARY_PATH = ROOT / 'review/content_build/answer_batch_0022/source_boundary_audit.md'

NORMALIZE = {
    'canonical_id': 'cq_q_3bf259d7b6e7b206848ba45de660e99a',
    'old_qid': '3bf259d7b6e7b206848ba45de660e99a',
    'old_text': '编程实现：给定字符串（如 "ab12cd34"），编写代码提取其中的指定子串（如 "12"）。要求口述或编写正则表达式方案',
    'new_text': '编程实现：给定字符串，提取第一个连续数字子串；例如输入 "ab12cd34"，输出 "12"。',
    'new_title': '编程实现：提取字符串中的第一个连续数字子串（例如 ab12cd34 -> 12）',
    'new_qid': '5f1229da81132a7214d064e2a8fc0b4c',
    'note_path': ROOT / 'note_tagged/67ef221f000000001b03ae6a.json',
    'new_entities': ['正则表达式', '字符串扫描'],
}

RETIRE = {
    'cq_q_3bd9ce7e8b983c0e09e7b573588a0d3a': {
        'expected_original': '算法：股票卖出的最佳时机（贪心/动归）。',
        'explanation': (
            '仓库最强来源只保留“类似于股票卖出的最佳时机”，并提到现场用 for 循环、又讲了动归思路；'
            '没有保留交易次数、是否允许重复交易、手续费、冷冻期等决定状态机与最优解的核心约束。'
            '这些变体的可执行合同互不等价，因此不能把任一 LeetCode 版本擅自当成原题；按 '
            'incomplete_or_unreadable fail closed，等待更强来源后再恢复。'
        ),
    },
    'cq_q_3de03dc6dea1f4c4fa3022b5283db2ea': {
        'expected_original': '算法：[200，1，100，2，90，3，80，4]奇数递增，偶数递减的链表排序',
        'explanation': (
            '仓库来源只保留样例和“奇数递增，偶数递减的链表排序”这一短句；没有说明“奇数/偶数”'
            '指节点位置还是节点值，也没有明确输入不变量、最终排序方向和期望输出。样例本身也不足以唯一消除这些歧义。'
            '为其补写任一常见奇偶链表题都会把推断伪装成原题，因此按 incomplete_or_unreadable fail closed。'
        ),
    },
    'cq_q_3e406e6dedb661f2b0b02d4355917de0': {
        'expected_original': '算法：贪心+双指针',
        'explanation': (
            '仓库最强来源仅记录“代码题（贪心加双指针）”，没有题目对象、输入、输出、目标函数或约束。'
            '“贪心+双指针”是解法类别而不是可执行问题合同，无法 source-first 还原具体题目；'
            '按 incomplete_or_unreadable fail closed，等待更强来源后再恢复。'
        ),
    },
}

QUALIFIED = [
    'cq_q_3aa1637d60f1dbea7bb4279a4ae3f6a1',
    'cq_q_3ae198b1c39ab778836b9d3b8bd106b0',
    'cq_q_3c1de47a37045804edd3e2e78ec3856d',
    'cq_q_3c7d96b17f91a649fa290bd93958f08c',
    'cq_q_3d550dfc40061007739e893f666d49f2',
    'cq_q_3e0fe4f12f951128a2a1fb250199dcd6',
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
    if canonical.get('canonical_title') == spec['old_text']:
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
        task = task.replace('- Canonical count: `10`', '- Original batch Canonical count: `10`\n- Active after source-boundary audit: `7`')
    replacements = {
        '- `cq_q_3bd9ce7e8b983c0e09e7b573588a0d3a` — coding; risks: long_tail_baseline, placeholder_implementation':
            '- `cq_q_3bd9ce7e8b983c0e09e7b573588a0d3a` — retired fail-closed: source only says “类似于股票卖出的最佳时机”; exact transaction contract is unrecoverable.',
        '- `cq_q_3bf259d7b6e7b206848ba45de660e99a` — coding; risks: long_tail_baseline, placeholder_implementation':
            '- `cq_q_3bf259d7b6e7b206848ba45de660e99a` — coding; normalized to source/image-backed “extract first continuous digit substring” wording.',
        '- `cq_q_3de03dc6dea1f4c4fa3022b5283db2ea` — coding; risks: long_tail_baseline, placeholder_implementation':
            '- `cq_q_3de03dc6dea1f4c4fa3022b5283db2ea` — retired fail-closed: odd/even linked-list wording lacks an unambiguous executable contract.',
        '- `cq_q_3e406e6dedb661f2b0b02d4355917de0` — coding; risks: long_tail_baseline, placeholder_implementation':
            '- `cq_q_3e406e6dedb661f2b0b02d4355917de0` — retired fail-closed: source only preserves the solution category “贪心+双指针”, not a problem statement.',
    }
    for before, after in replacements.items():
        task = task.replace(before, after)
    marker = '## Source-first boundary disposition'
    if marker not in task:
        task += (
            '\n## Source-first boundary disposition\n\n'
            '- Repository source packet: `review/reports/ANSWER_BATCH_0022_SOURCE_PACKET.{json,md}` (10/10 source-hit coverage).\n'
            '- Boundary audit: 6 directly candidate-qualified, 1 recoverable normalization, 3 source-unrecoverable singletons retired fail-closed.\n'
            '- Candidate/research work may proceed only for the 7 active Canonicals after the full integrity gates pass.\n'
        )
    TASK_PATH.write_text(task.rstrip() + '\n', encoding='utf-8')

    BOUNDARY_PATH.parent.mkdir(parents=True, exist_ok=True)
    BOUNDARY_PATH.write_text(
        '''# Answer Batch 0022 — Source-first Boundary Audit

This audit was performed from `review/reports/ANSWER_BATCH_0022_SOURCE_PACKET.{json,md}` and the repository-local caption/image transcripts before candidate authoring. It separates source recoverability from answer correctness and fails closed when the surviving source cannot uniquely define an executable coding contract.

## Verdict

- Original batch Canonicals: 10
- Directly candidate-qualified: 6
- Recoverable normalization: 1
- Source-unrecoverable / excluded: 3
- Active after boundary remediation: 7

## Dispositions

| Canonical | Disposition | Source-first reason |
| --- | --- | --- |
| `cq_q_3aa1637d60f1dbea7bb4279a4ae3f6a1` | candidate-qualified | Image transcript preserves the exact JavaScript closure code, including the `where = "inside"` line and the “comment this line out” variation; answer can analyze lexical lookup without inventing missing input. |
| `cq_q_3ae198b1c39ab778836b9d3b8bd106b0` | candidate-qualified | Caption explicitly names LeetCode 63 / “不同路径 II”, making the obstacle-grid problem identity recoverable. |
| `cq_q_3bd9ce7e8b983c0e09e7b573588a0d3a` | exclude / `incomplete_or_unreadable` | Source says only “类似于股票卖出的最佳时机” and mentions a loop/DP discussion; transaction count and other state-defining constraints are absent, so no unique executable variant can be restored. |
| `cq_q_3bf259d7b6e7b206848ba45de660e99a` | normalize, then candidate-qualified | Caption says input `ab12cd34`, output `12`, solved with regex; image transcript shows `\\d+` + first `matcher.find()`. The current “specified substring” wording is broader than the source and is normalized to “first continuous digit substring”. |
| `cq_q_3c1de47a37045804edd3e2e78ec3856d` | candidate-qualified | Source explicitly asks “二维数组找 target”. No sorted-row/column property survives, so the answer must treat the matrix as arbitrary unless it clearly labels sorted-matrix approaches as variants. |
| `cq_q_3c7d96b17f91a649fa290bd93958f08c` | candidate-qualified | Source explicitly asks for the number of leaf-node pairs in a tree whose distance is less than a specified `distance`; tree-DP implementation can preserve that strict boundary. |
| `cq_q_3d550dfc40061007739e893f666d49f2` | candidate-qualified | Source gives both tables/columns and the exact requirement: users who bought at least two distinct products. |
| `cq_q_3de03dc6dea1f4c4fa3022b5283db2ea` | exclude / `incomplete_or_unreadable` | Source preserves only the sample plus “奇数递增，偶数递减的链表排序”; it does not define whether odd/even means positions or values, the input invariant, or the required final order, so common interview variants cannot be safely substituted. |
| `cq_q_3e0fe4f12f951128a2a1fb250199dcd6` | candidate-qualified | Source directly names “对称二叉树”; this is a stable, executable problem identity. |
| `cq_q_3e406e6dedb661f2b0b02d4355917de0` | exclude / `incomplete_or_unreadable` | Strongest source only records “代码题（贪心加双指针）”; it preserves a technique category but no problem object, input/output, objective or constraints. |

## Normalization

`cq_q_3bf259d7b6e7b206848ba45de660e99a` remains the Canonical identity. Its source Question is normalized from the unsupported generic “提取指定子串” wording to:

> 编程实现：给定字符串，提取第一个连续数字子串；例如输入 "ab12cd34"，输出 "12"。

The normalized Question id is `5f1229da81132a7214d064e2a8fc0b4c`. This wording is supported by both the caption and image transcript. A regex implementation is source-backed; a linear character scan may be discussed as an alternative, but neither should expand the Question beyond extracting the first continuous digit run.

## Fail-closed exclusions

The three excluded singleton Canonicals are archived rather than answered. Each source row remains auditable through `config/question_validity_audit.json` with `incomplete_or_unreadable` and a specific explanation. If stronger repository evidence later restores a unique executable contract, the source row can be re-included through the normal migration path.

## Next gate

Only after repository projections are rebuilt and `check_question_coverage`, `canonical check`, `review integrity`, strict answer validation, full validation, unit tests, and all answer CI gates pass may batch 0022 candidate work begin.
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
    for cid in RETIRE:
        if cid in active:
            raise SystemExit(f'retired Canonical still active after remediation: {cid}')

    print('Applied Answer Batch 0022 source-boundary remediation.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
