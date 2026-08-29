#!/usr/bin/env python3
"""Retire Batch 0055 singleton coding records whose executable contracts are not recoverable from repository source."""

from __future__ import annotations

import json
import re
import shutil
from pathlib import Path

ROOT = Path('.')
DATE = '2026-08-29'
TARGETS = [
    {
        'cid':'cq_q_f980b179e23abf160c16d1c8876345fd',
        'qid':'f980b179e23abf160c16d1c8876345fd',
        'expected':'算法手撕：原创业务场景算法题。',
        'note_id':'68b99dbc000000001c03e220',
        'raw_phrase':'原创算法题',
        'raw_line_re':r'^\s*\d+[、.]\s*原创算法题\s*$',
        'explanation':(
            '仓库原始 note 只保留“一面 / 2、原创算法题”这一事实，没有该原创算法题的业务场景、题干、输入输出、数据范围、样例、约束、'
            '目标函数或期望结果；note_structured/note_tagged 虽将其归纳为“算法手撕：原创业务场景算法题。”，也没有增加任何可执行 contract。'
            '在缺失这些源约束时选择数组、图、动态规划、贪心或任意业务模型都会把猜测伪装成原题，因此该 singleton 必须以 '
            'incomplete_or_unreadable fail-closed，并保留明确可解释的排除原因。'
        ),
        'verify_tokens':['原创算法题','业务场景','输入输出','无法唯一还原','fail-closed'],
        'progress_line':'- [x] `cq_q_f980b179e23abf160c16d1c8876345fd` retired fail-closed as source-unrecoverable: the raw note preserves only “2、原创算法题”; no business scenario, statement, inputs/outputs, constraints, examples, objective, or expected result survives. Choosing any concrete algorithm would fabricate the original interview problem. The invalid Question remains explainable with `incomplete_or_unreadable`, while its generated long-tail baseline is archived and Canonical/ReviewProgress reachability is removed.'
    },
    {
        'cid':'cq_q_fb4bb71d8c35b1ff7e2fca5c36799af6',
        'qid':'fb4bb71d8c35b1ff7e2fca5c36799af6',
        'expected':'算法：数据库sql操作 出了两个题',
        'note_id':'67e12cfa000000001d02777a',
        'raw_phrase':'数据库sql操作 出了两个题',
        'raw_line_re':r'^\s*数据库sql操作\s*出了两个题\s*$',
        'explanation':(
            '仓库原始 note 对该环节只保留“数据库sql操作 出了两个题”，没有两个 SQL 题中任意一个的题干、表结构、字段、样例数据、'
            '查询目标、过滤/关联/聚合/窗口/排序约束、期望结果或数据库方言；note_structured/note_tagged 也没有补回这些信息。'
            '仅凭“两个 SQL 题”无法唯一还原任何可执行查询 contract；继续生成 JOIN、GROUP BY、窗口函数等具体 SQL 会把通用模板或猜测'
            '伪装成原题，因此该 singleton 必须以 incomplete_or_unreadable fail-closed，并保留明确可解释的排除原因。'
        ),
        'verify_tokens':['两个 SQL','表结构','查询目标','无法唯一还原','fail-closed'],
        'progress_line':'- [x] `cq_q_fb4bb71d8c35b1ff7e2fca5c36799af6` retired fail-closed as source-unrecoverable: the raw note preserves only “数据库sql操作 出了两个题” and none of the two SQL statements, schemas, columns, sample rows, query goals, filters/joins/aggregations/windows/order rules, expected results, or dialect. Inventing concrete SQL would fabricate the interview questions. The invalid Question remains explainable with `incomplete_or_unreadable`, while its generated long-tail baseline is archived and Canonical/ReviewProgress reachability is removed.'
    },
]


def read_json(path: Path):
    return json.loads(path.read_text(encoding='utf-8'))


def write_json(path: Path, value) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def read_jsonl(path: Path):
    return [json.loads(line) for line in path.read_text(encoding='utf-8').splitlines() if line.strip()]


def write_jsonl(path: Path, rows) -> None:
    path.write_text(''.join(json.dumps(row, ensure_ascii=False, sort_keys=True, separators=(',', ':')) + '\n' for row in rows), encoding='utf-8')


def find_desc(raw: object, note_id: str) -> str:
    if isinstance(raw, dict):
        if raw.get('noteId') == note_id and isinstance(raw.get('desc'), str):
            return raw['desc']
        for value in raw.values():
            found = find_desc(value, note_id)
            if found:
                return found
    elif isinstance(raw, list):
        for value in raw:
            found = find_desc(value, note_id)
            if found:
                return found
    return ''


def main() -> int:
    canonical_path = ROOT / 'data/questions/canonical_questions.jsonl'
    question_path = ROOT / 'data/questions/questions.jsonl'
    progress_path = ROOT / 'review/progress.json'
    audit_path = ROOT / 'config/question_validity_audit.json'
    canonicals = read_jsonl(canonical_path)
    questions = read_jsonl(question_path)
    progress = read_json(progress_path)
    audit = read_json(audit_path)
    decisions = list(audit.get('decisions', []))

    active_cids = {row.get('canonical_id') for row in canonicals}
    question_by_id = {row.get('question_id'): row for row in questions}
    progress_ids = {row.get('canonical_id') for row in progress.get('items', [])}

    retire = []
    for target in TARGETS:
        cid, qid, note_id = target['cid'], target['qid'], target['note_id']
        tagged = read_json(ROOT / f'note_tagged/{note_id}.json')
        structured = read_json(ROOT / f'note_structured/{note_id}.json')
        raw = read_json(ROOT / f'note_json/{note_id}.json')
        tagged_q = next((q for q in tagged.get('tagged_questions', []) if q.get('question_id') == qid), None)
        if tagged_q is None or tagged_q.get('original_question') != target['expected'] or tagged_q.get('is_valid_for_library') is not True:
            raise SystemExit(f'{qid}: exact tagged source wording/validity missing or drifted')
        if target['expected'] not in structured.get('questions', []):
            raise SystemExit(f'{qid}: structured source wording missing or drifted')
        desc = find_desc(raw, note_id)
        if not desc:
            raise SystemExit(f'{qid}: raw note description missing')
        lines = [line.strip() for line in desc.splitlines() if line.strip()]
        matches = [line for line in lines if target['raw_phrase'].lower() in line.lower()]
        if len(matches) != 1 or re.fullmatch(target['raw_line_re'], matches[0], flags=re.IGNORECASE) is None:
            raise SystemExit(f'{qid}: raw source line gained detail or drifted: {matches}')

        qrow = question_by_id.get(qid)
        if qrow is None or qrow.get('original_question') != target['expected'] or qrow.get('source_note_id') != note_id:
            raise SystemExit(f'{qid}: Question projection missing/source drifted')
        canonical = next((row for row in canonicals if row.get('canonical_id') == cid), None)
        if canonical is None:
            if qrow.get('canonical_id') is not None or qrow.get('is_valid_for_library') is not False or qrow.get('exclusion_reason') != 'incomplete_or_unreadable':
                raise SystemExit(f'{qid}: already-retired state inconsistent')
            continue
        if list(canonical.get('question_ids') or []) != [qid] or int(canonical.get('frequency', 0)) != 1:
            raise SystemExit(f'{cid}: expected singleton Canonical ownership')
        if qrow.get('canonical_id') != cid or qrow.get('is_valid_for_library') is not True:
            raise SystemExit(f'{qid}: active projection drifted')
        if cid not in progress_ids:
            raise SystemExit(f'{cid}: expected active ReviewProgress item')
        if (ROOT / f'review/candidates/answers/{cid}.md').exists():
            raise SystemExit(f'{cid}: candidate exists; do not discard independently staged work')
        if (ROOT / f'review/evidence/{cid}.json').exists():
            raise SystemExit(f'{cid}: evidence exists; manual source-first reassessment required')
        retire.append(target)

    if not retire:
        print('Batch 0055 unrecoverable source singletons already retired fail-closed')
        return 0

    for target in retire:
        cid, qid = target['cid'], target['qid']
        qrow = question_by_id[qid]
        replacement = {
            'source_note_id': qrow['source_note_id'],
            'source_question_index': qrow['source_question_index'],
            'question_id': qid,
            'original_question': qrow['original_question'],
            'decision': 'exclude',
            'exclusion_reason': 'incomplete_or_unreadable',
            'exclusion_note': target['explanation'],
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
            raise SystemExit(f'{cid}: expected exactly one ReviewProgress item to retire')

        active_answer = ROOT / f'review/answers/{cid}.md'
        archived_answer = ROOT / f'review/archive/answers/{cid}.md'
        if not active_answer.exists():
            raise SystemExit(f'{cid}: active generated long-tail baseline Answer missing')
        archived_answer.parent.mkdir(parents=True, exist_ok=True)
        if archived_answer.exists():
            if archived_answer.read_bytes() != active_answer.read_bytes():
                raise SystemExit(f'{cid}: existing archived Answer differs from active Answer')
            active_answer.unlink()
        else:
            shutil.move(str(active_answer), str(archived_answer))

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
    print('Retired Batch 0055 source-unrecoverable singletons: ' + ', '.join(t['cid'] for t in retire))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
