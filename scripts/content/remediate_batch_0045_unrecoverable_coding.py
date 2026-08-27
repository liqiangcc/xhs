#!/usr/bin/env python3
"""Retire Batch 0045 singleton coding Questions whose executable contracts are not recoverable."""

from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

ROOT = Path('.')
DATE = '2026-08-28'

SPECS = [
    {
        'canonical_id': 'cq_q_bc13ebbe774e5778175dc8ab0fd760ed',
        'question_id': 'bc13ebbe774e5778175dc8ab0fd760ed',
        'expected': '编程题：涉及到 HashMap 累加应用。',
        'source_note_id': '66d046c9000000001f01cde0',
        'tagged_blob': '1525bc9b8b2f84361e92b3d839d1268b113370c3',
        'desc_blob': 'addb120d96630a454bf373959cd00071f307b185',
        'image_blob': None,
        'image_required_tokens': [],
        'explanation': (
            '仓库现存材料只保留“编程题：涉及到 HashMap 累加应用。”以及紧随其后的追问：刚刚的 HashMap 在累加过程中若 Integer 溢出会如何处理。'
            '这些信息只能证明原编程题使用了 HashMap 做某种累加，无法唯一恢复输入结构、Map 的 key/value 含义、累加目标、返回值、边界条件、样例或复杂度约束。'
            '用“两数之和、词频统计、前缀和、分组计数”等任一具体题目补全都会把猜测伪装成原题，因此该 singleton 必须以 incomplete_or_unreadable fail-closed；'
            '独立的 Integer 溢出追问仍作为其自身 Question 保留，不受本次排除影响。'
        ),
        'required_note_tokens': ['coding', 'hashmap', 'Integer溢出'],
    },
    {
        'canonical_id': 'cq_q_bcee79935af85edcb001b4ffafcc3004',
        'question_id': 'bcee79935af85edcb001b4ffafcc3004',
        'expected': '场景：一维数组转二维数组',
        'source_note_id': '6803483d000000001d019393',
        'tagged_blob': '6ea4f29e6f02ce731e10e84f1cc81d48051b66bb',
        'desc_blob': 'bcf3d499376fe6082cb09a2f452a71f229c74bba',
        'image_blob': 'd5c51371af6e91393f650733b63620a2e6390c63',
        'image_required_tokens': ['12.手撕代码', '场景题：一维数组转二维', '算法题：版本号比较'],
        'explanation': (
            '仓库现存结构化题目和图片转写都只保留“场景：一维数组转二维（数组）”。图片转写进一步确认它只是京东一面“手撕代码”下的场景题，紧邻另一个独立的版本号比较算法题，并未补充二维形状、行数/列数、每组长度、末组处理、填充值、索引映射、输入输出样例或 API 契约。'
            '一维转二维可以按固定列数分块、按固定行数分配、按矩阵尺寸 reshape、按业务 key 分组等，结果互不等价；仅凭当前完整仓库证据无法恢复唯一可执行 contract。'
            '继续生成某一种 reshape/chunk 实现会把假设冒充成原题，因此该 singleton 应以 incomplete_or_unreadable fail-closed，并保留可解释排除原因。'
        ),
        'required_note_tokens': ['一面问的问题都是根据项目来的', '二面总体在聊天'],
    },
]


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


def git_blob(path: Path) -> str:
    return subprocess.check_output(['git', 'hash-object', str(path)], text=True).strip()


def validate_sources(spec: dict) -> None:
    note_id = spec['source_note_id']
    tagged_path = ROOT / f'note_tagged/{note_id}.json'
    desc_path = ROOT / f'note_desc/{note_id}.txt'
    if git_blob(tagged_path) != spec['tagged_blob']:
        raise SystemExit(f"{spec['question_id']}: tagged source changed; reassess source-first before exclusion")
    if git_blob(desc_path) != spec['desc_blob']:
        raise SystemExit(f"{spec['question_id']}: note_desc changed; reassess source-first before exclusion")
    tagged = read_json(tagged_path)
    tagged_q = next((q for q in tagged.get('tagged_questions', []) if q.get('question_id') == spec['question_id']), None)
    if tagged_q is None or tagged_q.get('original_question') != spec['expected']:
        raise SystemExit(f"{spec['question_id']}: exact tagged source wording missing or drifted")
    if tagged_q.get('question_type') != '算法手撕_Coding' or tagged_q.get('is_valid_for_library') is not True:
        raise SystemExit(f"{spec['question_id']}: tagged source taxonomy/validity drifted")
    desc = desc_path.read_text(encoding='utf-8')
    for token in spec['required_note_tokens']:
        if token not in desc:
            raise SystemExit(f"{spec['question_id']}: expected provenance token missing: {token}")

    image_text = ROOT / f'note_img_txt/{note_id}.txt'
    expected_image_blob = spec.get('image_blob')
    if expected_image_blob is None:
        if image_text.exists() and image_text.read_text(encoding='utf-8').strip():
            raise SystemExit(f"{spec['question_id']}: unexpected image-text evidence exists; reassess before fail-closed exclusion")
    else:
        if not image_text.exists() or git_blob(image_text) != expected_image_blob:
            raise SystemExit(f"{spec['question_id']}: image-text evidence missing or changed; reassess source-first")
        image = image_text.read_text(encoding='utf-8')
        for token in spec.get('image_required_tokens', []):
            if token not in image:
                raise SystemExit(f"{spec['question_id']}: expected image provenance token missing: {token}")


def main() -> int:
    for spec in SPECS:
        validate_sources(spec)

    canonical_path = ROOT / 'data/questions/canonical_questions.jsonl'
    question_path = ROOT / 'data/questions/questions.jsonl'
    progress_path = ROOT / 'review/progress.json'
    audit_path = ROOT / 'config/question_validity_audit.json'
    canonicals = read_jsonl(canonical_path)
    questions = read_jsonl(question_path)
    progress = read_json(progress_path)
    audit = read_json(audit_path)
    decisions = list(audit.get('decisions', []))

    changed = False
    for spec in SPECS:
        cid = spec['canonical_id']
        qid = spec['question_id']
        canonical = next((row for row in canonicals if row.get('canonical_id') == cid), None)
        qrows = [row for row in questions if row.get('question_id') == qid]
        if len(qrows) != 1:
            raise SystemExit(f'{qid}: expected one Question projection row, got {len(qrows)}')
        qrow = qrows[0]

        if canonical is None:
            decision = next((d for d in decisions if d.get('question_id') == qid), None)
            if (
                qrow.get('canonical_id') is not None
                or qrow.get('is_valid_for_library') is not False
                or qrow.get('exclusion_reason') != 'incomplete_or_unreadable'
                or not decision
                or decision.get('decision') != 'exclude'
                or decision.get('exclusion_reason') != 'incomplete_or_unreadable'
            ):
                raise SystemExit(f'{qid}: already-retired state is inconsistent')
            print(f'{qid}: already retired fail-closed')
            continue

        if list(canonical.get('question_ids') or []) != [qid] or int(canonical.get('frequency', 0)) != 1:
            raise SystemExit(f'{qid}: expected singleton Canonical ownership, got {canonical.get("question_ids")}')
        if (
            qrow.get('canonical_id') != cid
            or qrow.get('is_valid_for_library') is not True
            or qrow.get('original_question') != spec['expected']
            or qrow.get('source_note_id') != spec['source_note_id']
        ):
            raise SystemExit(f'{qid}: active Question projection drifted')

        candidate = ROOT / f'review/candidates/answers/{cid}.md'
        if candidate.exists():
            raise SystemExit(f'{qid}: candidate exists; do not discard independently staged/reviewed work')

        replacement = {
            'source_note_id': qrow['source_note_id'],
            'source_question_index': qrow['source_question_index'],
            'question_id': qid,
            'original_question': qrow['original_question'],
            'decision': 'exclude',
            'exclusion_reason': 'incomplete_or_unreadable',
            'exclusion_note': spec['explanation'],
        }
        ref = (qrow['source_note_id'], qrow['source_question_index'])
        for i, decision in enumerate(decisions):
            if (decision.get('source_note_id'), decision.get('source_question_index')) == ref:
                decisions[i] = replacement
                break
        else:
            decisions.append(replacement)

        canonicals = [row for row in canonicals if row.get('canonical_id') != cid]
        before = len(progress.get('items', []))
        progress['items'] = [row for row in progress.get('items', []) if row.get('canonical_id') != cid]
        if len(progress['items']) != before - 1:
            raise SystemExit(f'{qid}: expected exactly one ReviewProgress item to retire')

        active_answer = ROOT / f'review/answers/{cid}.md'
        archived_answer = ROOT / f'review/archive/answers/{cid}.md'
        if not active_answer.exists():
            raise SystemExit(f'{qid}: active long-tail baseline Answer missing')
        archived_answer.parent.mkdir(parents=True, exist_ok=True)
        if archived_answer.exists():
            if archived_answer.read_bytes() != active_answer.read_bytes():
                raise SystemExit(f'{qid}: existing archived Answer differs from active Answer')
            active_answer.unlink()
        else:
            shutil.move(str(active_answer), str(archived_answer))
        changed = True
        print(f'Retired source-unrecoverable Batch 0045 singleton: {qid}')

    if not changed:
        return 0

    decisions.sort(key=lambda d: (str(d.get('source_note_id', '')), int(d.get('source_question_index', 0))))
    audit['decisions'] = decisions
    audit['audited_at'] = DATE
    audit['include_count'] = sum(1 for d in decisions if d.get('decision') == 'include')
    audit['exclude_count'] = sum(1 for d in decisions if d.get('decision') == 'exclude')
    write_json(audit_path, audit)
    write_jsonl(canonical_path, sorted(canonicals, key=lambda row: row['canonical_id']))
    progress['updated_at'] = DATE
    progress['items'] = sorted(progress.get('items', []), key=lambda row: row.get('canonical_id', ''))
    write_json(progress_path, progress)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
