#!/usr/bin/env python3
"""Apply source-first boundary dispositions for Answer Batch 0024.

Conservative repository-source-only mutation:
- keep six coding Questions active where the source preserves a stable problem identity;
- retire four singleton records whose source does not preserve a unique executable contract
  or whose extracted Canonical contradicts the source;
- archive retired Answers and remove their ReviewProgress;
- persist explicit fail-closed validity decisions.

Generated Question/index/type projections are rebuilt by the calling workflow.
"""

from __future__ import annotations

import json
from pathlib import Path
import shutil

ROOT = Path('.')
CANONICAL_PATH = ROOT / 'data/questions/canonical_questions.jsonl'
QUESTION_PATH = ROOT / 'data/questions/questions.jsonl'
PROGRESS_PATH = ROOT / 'review/progress.json'
VALIDITY_AUDIT_PATH = ROOT / 'config/question_validity_audit.json'
TASK_PATH = ROOT / 'tasks/answer-batches/TASK-20260711-0313-answer-batch-0024.md'
BOUNDARY_PATH = ROOT / 'review/content_build/answer_batch_0024/source_boundary_audit.md'
SOURCE_PACKET_PATH = ROOT / 'review/reports/ANSWER_BATCH_0024_SOURCE_PACKET.json'

QUALIFIED = {
    'cq_q_458d73b3af53aae38af2eaf83473ef2f': (
        'Caption explicitly requires Java synchronized code that deterministically reaches a deadlock.'
    ),
    'cq_q_4715e4cb7c542d15146981fcac350958': (
        'Caption explicitly asks to find the most frequent element in an integer list and write tests; '
        'tie behavior is not preserved and must remain an answer-level stated assumption.'
    ),
    'cq_q_48bf70b4872cce81f798c61fe039ef47': (
        'Caption explicitly lists both underscore-to-camel and camel-to-underscore implementations.'
    ),
    'cq_q_48d51539a85aabde9bd294e902c0cd86': (
        'Caption explicitly asks rand5() to rand7(), preserving the stable equal-probability construction problem identity.'
    ),
    'cq_q_494b0b68c1f4eb41cf7ec520babc8f11': (
        'Image transcript explicitly states building a binary tree with the array maximum as root and recursively doing left/right.'
    ),
    'cq_q_496dcfbf2235c39f2f484c991f151e76': (
        'Caption explicitly asks to build a binary tree from preorder and inorder traversals.'
    ),
}

RETIRE = {
    'cq_q_45e7ff4427260a3df4b31c08cad14141': {
        'expected_original': 'SQL：索引创建、加锁语句与死锁代码手写',
        'explanation': (
            '仓库来源把“给出 SQL 创建索引”“手撕具体 SQL 加锁语句”“手撕并发死锁代码”列为三个独立二面题，'
            '但当前抽取把它们合成一个 Canonical。来源没有保留表结构、索引目标、加锁对象/事务上下文或死锁场景，'
            '无法恢复一个语义边界单一且可唯一验证的可执行合同；因此按 incomplete_or_unreadable fail closed，'
            '不能用通用 SQL 示例替代原题。'
        ),
        'task_note': 'retired fail-closed: source is three separate under-specified prompts, not one executable SQL contract.',
    },
    'cq_q_46a0db137d9b355e6858b744d86f5d26': {
        'expected_original': 'SparkSQL：复杂数据构造与查询实操。',
        'explanation': (
            '仓库来源只说明面试有“两道 SparkSQL 题”，其中一道考察数据构造，没有保存具体输入数据、目标结果、'
            '表/字段结构或查询约束。当前 Canonical 的“复杂数据构造与查询实操”是类别概括而不是可执行题目，'
            '无法唯一恢复原题，因此按 incomplete_or_unreadable fail closed。'
        ),
        'task_note': 'retired fail-closed: source preserves only the existence/category of two SparkSQL tasks, not their executable contracts.',
    },
    'cq_q_46f480936190e2b68c9f9dc6cba0d866': {
        'expected_original': '手撕代码：实现前缀和（Prefix Sum）。',
        'explanation': (
            '仓库来源只保留“手撕：前缀和”这一题名，没有说明是一维/二维、构造数组还是区间查询、输入输出接口、'
            '是否需要动态更新等合同。前缀和是一类技术而非唯一题目；直接选择任一常见模板会超出来源，'
            '因此按 incomplete_or_unreadable fail closed。'
        ),
        'task_note': 'retired fail-closed: “前缀和” names a technique but source preserves no unique input/output contract.',
    },
    'cq_q_46fe1307494a9f56b39e0d9f76796f61': {
        'expected_original': '算法：K 个一组翻转链表。给定一个链表，将其每 K（如 K=3）个节点视作一组进行逆转，请实现该算法',
        'explanation': (
            '仓库来源文字写“链表，每三个结点逆转顺序”，但唯一保留示例把 '
            '1 2 3 4 5 6 7 8 变为 7 8 4 5 6 1 2 3；这并不是当前 Canonical 所声称的标准 K 个一组节点反转'
            '（该操作会得到 3 2 1 6 5 4 7 8）。来源 wording 与示例支持的变换语义冲突，也没有更多样例定义余数组、'
            '组内/组间顺序和一般 K 的规则。不能把 LeetCode 25 或自创“反转分组顺序”合同擅自代入，'
            '因此按 incomplete_or_unreadable fail closed。'
        ),
        'task_note': 'retired fail-closed: source example contradicts standard K-group node reversal and does not uniquely define the intended transform.',
    },
}


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
    if packet.get('schema_version') != 'answer_batch_source_packet.v2' or packet.get('batch') != '0024':
        raise SystemExit('unexpected batch 0024 source packet identity')
    if packet.get('source_policy') != 'repository_source_only_exact_id_or_exact_normalized_wording_no_fuzzy_inference':
        raise SystemExit('unexpected batch 0024 source policy')
    entries = packet.get('canonicals') or []
    if len(entries) != 10:
        raise SystemExit(f'expected 10 source-packet Canonicals, got {len(entries)}')
    ids = {entry.get('canonical_id') for entry in entries}
    expected = set(QUALIFIED) | set(RETIRE)
    if ids != expected:
        raise SystemExit(f'batch 0024 source-packet identity drift: missing={sorted(expected-ids)}, extra={sorted(ids-expected)}')
    missing = [entry.get('canonical_id') for entry in entries if not entry.get('source_hits')]
    if missing:
        raise SystemExit(f'batch 0024 source packet has missing hits: {missing}')


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
        if row.get('canonical_id') != cid or row.get('is_valid_for_library') is not True:
            raise SystemExit(f'{cid}: Question binding/validity drifted')
        if row.get('original_question') != spec['expected_original']:
            raise SystemExit(f'{cid}: original Question wording drifted: {row.get("original_question")!r}')

        candidate = ROOT / 'review/candidates/answers' / f'{cid}.md'
        evidence = ROOT / 'review/evidence' / f'{cid}.json'
        audit_candidate = ROOT / 'review/candidates/audits' / f'{cid}.json'
        if candidate.exists() or evidence.exists() or audit_candidate.exists():
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
            '- Original batch Canonical count: `10`\n- Active after source-boundary audit: `6`',
        )

    for cid, spec in RETIRE.items():
        old = f'- `{cid}` — coding; risks: long_tail_baseline, placeholder_implementation'
        new = f'- `{cid}` — {spec["task_note"]}'
        if old in task:
            task = task.replace(old, new)
        elif new not in task:
            raise SystemExit(f'batch 0024 task line drifted: {cid}')

    if '## Source-first boundary disposition' not in task:
        task = task.rstrip() + "\n\n## Source-first boundary disposition\n\n"
        task += "- Repository source packet: `review/reports/ANSWER_BATCH_0024_SOURCE_PACKET.{json,md}` (10/10 source-hit coverage).\n"
        task += "- Boundary audit: 6 directly candidate-qualified and 4 source-unrecoverable singleton records retired fail-closed.\n"
        task += "- Candidate/research work may proceed only for the 6 active Canonicals after the full integrity gates pass.\n"
    TASK_PATH.write_text(task, encoding='utf-8')

    BOUNDARY_PATH.parent.mkdir(parents=True, exist_ok=True)
    rows = [
        '# Answer Batch 0024 — Source-first Boundary Audit',
        '',
        'This audit was performed from `review/reports/ANSWER_BATCH_0024_SOURCE_PACKET.{json,md}` and the repository-local caption/image transcripts before candidate authoring. It separates source recoverability from answer correctness and fails closed when the surviving source cannot uniquely define an executable coding contract.',
        '',
        '## Verdict',
        '',
        '- Original batch Canonicals: 10',
        '- Directly candidate-qualified: 6',
        '- Source-unrecoverable / excluded: 4',
        '- Active after boundary remediation: 6',
        '',
        '## Dispositions',
        '',
        '| Canonical | Disposition | Source-first reason |',
        '| --- | --- | --- |',
    ]
    for cid, reason in QUALIFIED.items():
        rows.append(f'| `{cid}` | candidate-qualified | {reason} |')
    for cid, spec in RETIRE.items():
        rows.append(f'| `{cid}` | exclude / `incomplete_or_unreadable` | {spec["explanation"]} |')
    rows.extend([
        '',
        '## Fail-closed exclusions',
        '',
        'The four excluded singleton Canonicals are archived rather than answered. Each source row remains auditable through `config/question_validity_audit.json` with `incomplete_or_unreadable` and a specific explanation. Stronger future repository evidence may restore a unique contract through the normal migration path.',
        '',
        'In particular, `cq_q_46fe1307494a9f56b39e0d9f76796f61` is not silently normalized to LeetCode 25: the preserved example contradicts standard K-group node reversal, so choosing that well-known problem would be an unsupported semantic substitution.',
        '',
        '## Candidate constraints',
        '',
        '- `cq_q_4715e4cb7c542d15146981fcac350958`: the source does not define tie behavior; a candidate must state its tie assumption rather than claim the interviewer required one.',
        '- `cq_q_494b0b68c1f4eb41cf7ec520babc8f11`: the source preserves the maximum-as-root recursive construction; any duplicate-value convention must be stated as an implementation assumption.',
        '- `cq_q_496dcfbf2235c39f2f484c991f151e76`: a candidate may state the usual unique-value prerequisite for unique reconstruction, but must not attribute that prerequisite to the source.',
        '- `cq_q_458d73b3af53aae38af2eaf83473ef2f`: the image transcript is tool-dialogue noise; the caption is the authoritative repository-local evidence for the deadlock prompt.',
        '',
        '## Next gate',
        '',
        'Only after repository projections are rebuilt and `check_question_coverage`, `canonical check`, `review integrity`, strict answer validation, full validation, unit tests, answer type audit, and all answer CI gates pass may batch 0024 candidate work begin.',
        '',
    ])
    BOUNDARY_PATH.write_text('\n'.join(rows), encoding='utf-8')


def main() -> None:
    verify_source_packet()
    canonicals = read_jsonl(CANONICAL_PATH)
    questions = read_jsonl(QUESTION_PATH)
    progress = read_json(PROGRESS_PATH)
    audit = read_json(VALIDITY_AUDIT_PATH)

    active_ids = {row.get('canonical_id') for row in canonicals}
    expected = set(QUALIFIED) | set(RETIRE)
    missing = sorted(expected - active_ids)
    unexpected = [cid for cid in missing if cid not in RETIRE]
    if unexpected:
        raise SystemExit(f'batch 0024 active inputs disappeared: {unexpected}')

    canonicals = retire_unrecoverable(canonicals, questions, progress, audit)

    write_jsonl(CANONICAL_PATH, canonicals)
    write_json(PROGRESS_PATH, progress)
    write_json(VALIDITY_AUDIT_PATH, audit)
    update_task_and_boundary()

    final_ids = {row.get('canonical_id') for row in canonicals}
    for cid in QUALIFIED:
        if cid not in final_ids:
            raise SystemExit(f'candidate-qualified Canonical disappeared: {cid}')
    leaked = sorted(set(RETIRE) & final_ids)
    if leaked:
        raise SystemExit(f'retired Canonicals remain active: {leaked}')


if __name__ == '__main__':
    main()
