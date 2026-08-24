#!/usr/bin/env python3
"""Apply source-first boundary dispositions for Answer Batch 0020.

This bounded mutation is intentionally conservative:
- normalize one recoverable Question/Canonical whose source does not name Morris;
- retire two singleton coding records whose surviving repository source does not
  preserve enough contract to author an executable answer without invention.

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
TASK_PATH = ROOT / 'tasks/answer-batches/TASK-20260711-0313-answer-batch-0020.md'
BOUNDARY_PATH = ROOT / 'review/content_build/answer_batch_0020/source_boundary_audit.md'

NORMALIZE = {
    'canonical_id': 'cq_q_32099ab899a15a5d7ab610c1477860e1',
    'old_qid': '32099ab899a15a5d7ab610c1477860e1',
    'old_text': '算法：非递归且不使用额外栈空间，如何遍历二叉树？(Morris遍历)',
    'new_text': '非递归且不用额外空间(不用栈)，如何遍历二叉树',
    'new_title': '算法：非递归且不用额外空间（不用栈），如何遍历二叉树？',
    'note_path': ROOT / 'note_tagged/67432048000000000703084c.json',
    'new_entities': ['二叉树遍历'],
}

RETIRE = {
    'cq_q_3395e0de3268979e86446a8ad2eebb4b': {
        'expected_original': '算法：力扣 135. 分发糖果？',
        'explanation': (
            '仓库最强原始来源只保留“编程 / 分发糖果”，没有保留 LeetCode 编号、ratings 输入、'
            '相邻比较规则、每人至少一颗糖、最小总糖果数目标、样例或输入输出。结构化 Question/Canonical '
            '加入“力扣 135”属于未被来源证明的强化；仅凭熟悉标题映射到某道外部题会把推断伪装成原题。'
            '在没有更强仓库来源前应按 incomplete_or_unreadable 排除，而不是编造可执行契约。'
        ),
    },
    'cq_q_33d091345ac48812c61f235d00515560': {
        'expected_original': '算法 1：火柴拼三角形。给定一个火柴长度数组，判断是否能拼成一个等边或普通三角形，并找出最长周长',
        'explanation': (
            '仓库原始来源只保留“找到最长的区间火柴拼成一个三角形”，并记录滑动窗口与“如果可以打乱顺序怎么优化（排序）”追问。'
            '来源没有定义“最长”是区间长度还是周长、一个区间是否必须全部火柴参与、三角形选择规则、输入输出或边界；'
            '当前结构化标题额外加入“等边或普通三角形”和“最长周长”，这些细节无法由来源恢复。多个不同算法合同都与摘要兼容，'
            '因此必须 fail closed，不能凭当前 Canonical 生成看似确定的实现与测试。'
        ),
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


def normalize_recoverable(canonicals: list[dict], questions: list[dict], audit: dict) -> tuple[list[dict], list[dict], bool]:
    spec = NORMALIZE
    cid = spec['canonical_id']
    old_qid = spec['old_qid']
    new_qid = question_id(spec['new_text'])
    if new_qid != 'e281ba5785075b6f8ab305f1be5718c0':
        raise SystemExit(f'unexpected normalized Question id: {new_qid}')

    note = read_json(spec['note_path'])
    tagged_matches = [q for q in note.get('tagged_questions', []) if q.get('question_id') in {old_qid, new_qid}]
    if len(tagged_matches) != 1:
        raise SystemExit(f'{cid}: expected exactly one old/new tagged Question, got {len(tagged_matches)}')
    tagged = tagged_matches[0]
    changed = False
    if tagged.get('question_id') == old_qid:
        if tagged.get('original_question') != spec['old_text']:
            raise SystemExit(f'{cid}: tagged old text drifted: {tagged.get("original_question")!r}')
        tagged['question_id'] = new_qid
        tagged['original_question'] = spec['new_text']
        tagged['tech_entities'] = list(spec['new_entities'])
        changed = True
    else:
        if tagged.get('original_question') != spec['new_text']:
            raise SystemExit(f'{cid}: normalized tagged text drifted: {tagged.get("original_question")!r}')
    if changed:
        write_json(spec['note_path'], note)

    canonical_matches = [row for row in canonicals if row.get('canonical_id') == cid]
    if len(canonical_matches) != 1:
        raise SystemExit(f'{cid}: expected one Canonical, got {len(canonical_matches)}')
    canonical = canonical_matches[0]
    owned = list(canonical.get('question_ids') or [])
    if owned == [old_qid]:
        canonical['question_ids'] = [new_qid]
        changed = True
    elif owned != [new_qid]:
        raise SystemExit(f'{cid}: Canonical ownership drifted: {owned}')
    if canonical.get('canonical_title') != spec['new_title']:
        if canonical.get('canonical_title') != spec['old_text']:
            raise SystemExit(f'{cid}: Canonical title drifted: {canonical.get("canonical_title")!r}')
        canonical['canonical_title'] = spec['new_title']
        canonical['aliases'] = [spec['new_title']]
        canonical['primary_entities'] = list(spec['new_entities'])
        changed = True

    old_rows = [row for row in questions if row.get('question_id') == old_qid]
    new_rows = [row for row in questions if row.get('question_id') == new_qid]
    if old_rows and new_rows:
        raise SystemExit(f'{cid}: both old and normalized Question ids exist')
    row_matches = old_rows or new_rows
    if len(row_matches) != 1:
        raise SystemExit(f'{cid}: expected one old/new Question projection, got {len(row_matches)}')
    row = row_matches[0]
    if row.get('canonical_id') != cid:
        raise SystemExit(f'{cid}: Question projection binding drifted: {row.get("canonical_id")}')
    source_ref = (row.get('source_note_id'), row.get('source_question_index'))
    if row.get('question_id') == old_qid:
        if row.get('original_question') != spec['old_text']:
            raise SystemExit(f'{cid}: Question old text drifted: {row.get("original_question")!r}')
        row['question_id'] = new_qid
        row['original_question'] = spec['new_text']
        row['tech_entities'] = list(spec['new_entities'])
        changed = True
    elif row.get('original_question') != spec['new_text']:
        raise SystemExit(f'{cid}: Question normalized text drifted: {row.get("original_question")!r}')

    decisions = list(audit.get('decisions', []))
    matches = [d for d in decisions if (d.get('source_note_id'), d.get('source_question_index')) == source_ref]
    if len(matches) > 1:
        raise SystemExit(f'{cid}: duplicate validity-audit decisions for source ref')
    if matches:
        decision = matches[0]
        if decision.get('decision') != 'include':
            raise SystemExit(f'{cid}: normalized Question must remain included, got {decision.get("decision")}')
        if decision.get('question_id') == old_qid:
            decision['question_id'] = new_qid
            decision['original_question'] = spec['new_text']
            changed = True
        elif decision.get('question_id') != new_qid or decision.get('original_question') != spec['new_text']:
            raise SystemExit(f'{cid}: validity-audit decision drifted')

    answer_path = ROOT / 'review/answers' / f'{cid}.md'
    answer = answer_path.read_text(encoding='utf-8')
    if spec['old_text'] in answer:
        answer = answer.replace(spec['old_text'], spec['new_title'])
        answer_path.write_text(answer, encoding='utf-8')
        changed = True
    elif spec['new_title'] not in answer:
        raise SystemExit(f'{cid}: active Answer contains neither old nor normalized title')

    print(f'Normalized {cid}: {old_qid} -> {new_qid}')
    return canonicals, questions, changed


def retire_unrecoverable(canonicals: list[dict], questions: list[dict], progress: dict, audit: dict) -> tuple[list[dict], bool]:
    canonical_by_id = {row['canonical_id']: row for row in canonicals}
    question_rows_by_id: dict[str, list[dict]] = {}
    for row in questions:
        question_rows_by_id.setdefault(row['question_id'], []).append(row)

    decisions = list(audit.get('decisions', []))
    decisions_by_ref = {
        (decision.get('source_note_id'), decision.get('source_question_index')): decision
        for decision in decisions
    }
    changed = False

    for cid, spec in RETIRE.items():
        qid = cid.removeprefix('cq_q_')
        canonical = canonical_by_id.get(cid)
        if canonical is None:
            if any(row.get('canonical_id') == cid for row in questions):
                raise SystemExit(f'{cid}: Canonical missing but active Question binding remains')
            if (ROOT / 'review/answers' / f'{cid}.md').exists():
                raise SystemExit(f'{cid}: Canonical missing but active Answer remains')
            if any(item.get('canonical_id') == cid for item in progress.get('items', [])):
                raise SystemExit(f'{cid}: Canonical missing but ReviewProgress remains')
            continue

        if list(canonical.get('question_ids') or []) != [qid] or int(canonical.get('frequency', 0)) != 1:
            raise SystemExit(f'{cid}: expected singleton Canonical ownership before retirement')
        rows = question_rows_by_id.get(qid, [])
        if len(rows) != 1:
            raise SystemExit(f'{cid}: expected exactly one Question row, got {len(rows)}')
        row = rows[0]
        if row.get('canonical_id') != cid or row.get('is_valid_for_library') is not True:
            raise SystemExit(f'{cid}: Question binding/validity drifted before retirement')
        if row.get('original_question') != spec['expected_original']:
            raise SystemExit(f'{cid}: original Question drifted: {row.get("original_question")!r}')

        candidate = ROOT / 'review/candidates/answers' / f'{cid}.md'
        evidence = ROOT / 'review/evidence' / f'{cid}.json'
        if candidate.exists() or evidence.exists():
            raise SystemExit(f'{cid}: candidate/evidence appeared after source audit; independent re-review required before retirement')

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
        previous = decisions_by_ref.get(ref)
        if previous is None:
            decisions.append(replacement)
            decisions_by_ref[ref] = replacement
            changed = True
        elif previous != replacement:
            idx = decisions.index(previous)
            decisions[idx] = replacement
            decisions_by_ref[ref] = replacement
            changed = True

        canonicals = [item for item in canonicals if item.get('canonical_id') != cid]
        canonical_by_id.pop(cid, None)

        before = len(progress.get('items', []))
        progress['items'] = [item for item in progress.get('items', []) if item.get('canonical_id') != cid]
        if len(progress['items']) != before - 1:
            raise SystemExit(f'{cid}: expected exactly one ReviewProgress item')

        active_answer = ROOT / 'review/answers' / f'{cid}.md'
        archive_answer = ROOT / 'review/archive/answers' / f'{cid}.md'
        if not active_answer.exists():
            raise SystemExit(f'{cid}: active Answer missing')
        archive_answer.parent.mkdir(parents=True, exist_ok=True)
        if archive_answer.exists():
            if archive_answer.read_bytes() != active_answer.read_bytes():
                raise SystemExit(f'{cid}: existing answer archive differs from active answer')
            active_answer.unlink()
        else:
            shutil.move(str(active_answer), str(archive_answer))
        changed = True
        print(f'Retired source-unrecoverable singleton {cid}')

    audit['decisions'] = decisions
    return canonicals, changed


def update_docs() -> bool:
    changed = False
    task = TASK_PATH.read_text(encoding='utf-8')
    replacements = {
        '- Repository-only source-packet extraction is registered on `master` and must complete before any candidate is authored.':
            '- Repository-only source packet extracted successfully at `review/reports/ANSWER_BATCH_0020_SOURCE_PACKET.{json,md}`; source-hit coverage is 10/10.',
        '- Next gate after extraction: review all 10 Canonicals against `review/reports/ANSWER_BATCH_0020_SOURCE_PACKET.{json,md}`, classify each as source-supported, normalizable/splittable, or source-unrecoverable, and record an explicit boundary disposition before research/candidate work.':
            '- Source-first boundary audit completed at `review/content_build/answer_batch_0020/source_boundary_audit.md`: 7 were directly candidate-qualified, 1 recoverable source wording required normalization, and 2 singleton coding records are source-unrecoverable and excluded fail-closed.',
        '- `cq_q_32099ab899a15a5d7ab610c1477860e1` — coding; risks: long_tail_baseline, placeholder_implementation':
            '- `cq_q_32099ab899a15a5d7ab610c1477860e1` — coding; source wording normalized to remove inferred “Morris遍历”; candidate-qualified with traversal-order/API assumptions explicit.',
        '- `cq_q_3395e0de3268979e86446a8ad2eebb4b` — coding; risks: long_tail_baseline, placeholder_implementation':
            '- `cq_q_3395e0de3268979e86446a8ad2eebb4b` — retired source-first; retained source only says “编程 / 分发糖果” and does not prove LeetCode 135 or a unique executable contract.',
        '- `cq_q_33d091345ac48812c61f235d00515560` — coding; risks: long_tail_baseline, placeholder_implementation':
            '- `cq_q_33d091345ac48812c61f235d00515560` — retired source-first; retained fire-match/triangle summary omits the objective and executable contract while the structured title added unsupported details.',
        '- [ ] Every source Question has an explicit source-first boundary disposition before candidate authoring.':
            '- [x] Every source Question has an explicit source-first boundary disposition before candidate authoring.',
    }
    for old, new in replacements.items():
        if old in task:
            task = task.replace(old, new)
            changed = True
        elif new not in task:
            raise SystemExit(f'batch task drifted; missing expected text: {old}')
    marker = '## Remediation progress\n'
    section = '''## Remediation progress

- [x] `cq_q_32099ab899a15a5d7ab610c1477860e1` is normalized from the derived “(Morris遍历)” source wording to the repository-preserved non-recursive/no-extra-stack traversal question. The solution technique may be discussed in the candidate, but is no longer presented as recovered prompt text.
- [x] `cq_q_3395e0de3268979e86446a8ad2eebb4b` and `cq_q_33d091345ac48812c61f235d00515560` are excluded as `incomplete_or_unreadable`; their active placeholder Answers are archived, singleton Canonicals retired, ReviewProgress removed, and validity-audit decisions explain exactly what source contract is missing.
'''
    if marker not in task:
        task = task.rstrip() + '\n\n' + section
        changed = True
    TASK_PATH.write_text(task, encoding='utf-8')

    boundary = BOUNDARY_PATH.read_text(encoding='utf-8')
    applied = '''
## Applied remediation

- `cq_q_32099ab899a15a5d7ab610c1477860e1`: normalized to the repository-preserved wording “非递归且不用额外空间(不用栈)，如何遍历二叉树”; the Canonical remains stable while Question ownership moves to the normalized Question hash. “Morris遍历” is now treated only as a researched solution technique.
- `cq_q_3395e0de3268979e86446a8ad2eebb4b`: after fail-closed recheck, retired as source-unrecoverable. “分发糖果” alone does not uniquely justify importing LeetCode 135 semantics.
- `cq_q_33d091345ac48812c61f235d00515560`: retired as source-unrecoverable for the ambiguity already documented above.

Post-remediation answerable set: `8` active source-supported Canonicals. No source-boundary blocker remains for those eight; candidate work must still preserve each record's explicit assumptions and evidence gates.
'''
    if '## Applied remediation' not in boundary:
        BOUNDARY_PATH.write_text(boundary.rstrip() + '\n' + applied, encoding='utf-8')
        changed = True
    return changed


def main() -> int:
    canonicals = read_jsonl(CANONICAL_PATH)
    questions = read_jsonl(QUESTION_PATH)
    progress = read_json(PROGRESS_PATH)
    audit = read_json(VALIDITY_AUDIT_PATH)

    canonicals, questions, normalized_changed = normalize_recoverable(canonicals, questions, audit)
    canonicals, retired_changed = retire_unrecoverable(canonicals, questions, progress, audit)
    docs_changed = update_docs()
    changed = normalized_changed or retired_changed or docs_changed

    if not changed:
        print('Batch 0020 source-boundary remediation already applied.')
        return 0

    decisions = list(audit.get('decisions', []))
    decisions.sort(key=lambda decision: (str(decision.get('source_note_id', '')), int(decision.get('source_question_index', 0))))
    audit['decisions'] = decisions
    audit['audited_at'] = '2026-08-24'
    audit['include_count'] = sum(1 for decision in decisions if decision.get('decision') == 'include')
    audit['exclude_count'] = sum(1 for decision in decisions if decision.get('decision') == 'exclude')
    write_json(VALIDITY_AUDIT_PATH, audit)
    write_jsonl(CANONICAL_PATH, sorted(canonicals, key=lambda row: row['canonical_id']))
    write_jsonl(QUESTION_PATH, sorted(questions, key=lambda row: (row.get('source_note_id', ''), int(row.get('source_question_index', 0)), row.get('question_id', ''))))
    progress['updated_at'] = '2026-08-24'
    progress['items'] = sorted(progress.get('items', []), key=lambda item: item.get('canonical_id', ''))
    write_json(PROGRESS_PATH, progress)

    print('Applied Answer Batch 0020 source-boundary remediation.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
