#!/usr/bin/env python3
"""Apply source-first boundary dispositions for Answer Batch 0023.

This bounded mutation is conservative and repository-source-only:
- normalize the Linux process-termination Question to remove the unsupported
  requirement that the solution be a shell pipeline;
- correct the Python dict-values Question from Coding to Concept metadata;
- retire two singleton coding/command records whose strongest surviving source
  does not preserve a unique executable contract;
- leave the six source-qualified algorithm Questions active for candidate work.

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
TASK_PATH = ROOT / 'tasks/answer-batches/TASK-20260711-0313-answer-batch-0023.md'
BOUNDARY_PATH = ROOT / 'review/content_build/answer_batch_0023/source_boundary_audit.md'
SOURCE_PACKET_PATH = ROOT / 'review/reports/ANSWER_BATCH_0023_SOURCE_PACKET.json'

PROCESS_NORMALIZE = {
    'canonical_id': 'cq_q_449cb09687b14bdba2c6864c7787239f',
    'old_qid': '449cb09687b14bdba2c6864c7787239f',
    'old_text': "Linux 运维：请写出一个 Linux 命令管道，用于批量终止所有名字中包含 'abc' 的进程？",
    'new_text': 'Linux 命令：批量终止名字包含 abc 的进程',
    'new_title': 'Linux 命令：批量终止名字包含 abc 的进程',
    'new_qid': '55ee94f1cd20c8f85bc43f9f932f602f',
    'note_path': ROOT / 'note_tagged/68b154a8000000001c032fa1.json',
    'new_entities': ['linux命令', '进程管理'],
}

PYTHON_TYPE_FIX = {
    'canonical_id': 'cq_q_44ff2aad182c5458e01efb1d5e71d10f',
    'qid': '44ff2aad182c5458e01efb1d5e71d10f',
    'text': '取出字典中 value 值的方法有哪几种？',
    'note_path': ROOT / 'note_tagged/67eaad5d000000000b014631.json',
    'old_type': '算法手撕_Coding',
    'new_type': '八股文_Concept',
}

RETIRE = {
    'cq_q_454acf00cd919a7e95a309068e8eaf5a': {
        'expected_original': '手撕代码：斗地主发牌程序',
        'explanation': (
            '仓库最强来源只保留“斗地主发牌程序”这一题名，没有牌组定义、玩家/底牌数量、'
            '洗牌与发牌顺序、输入输出表示或需要实现的接口。不同实现合同并不等价，不能把任一'
            '常见教学示例擅自当成原题，因此按 incomplete_or_unreadable fail closed；等待更强来源后再恢复。'
        ),
    },
    'cq_q_454e063c3dff5366f28907955aa777e3': {
        'expected_original': 'Linux 命令：对于日志文件，查看出现频率前 10 的 URL',
        'explanation': (
            '三个重复仓库来源都只保留“对于日志文件，查看前10的URL，用什么命令”，没有说明“前10”'
            '是按出现频率、文件顺序还是其他指标，也没有保留日志格式或 URL 字段位置。当前 Canonical '
            '把“出现频率”补进题干属于超出来源的推断；在排序语义和解析字段均不唯一时无法给出唯一可验证'
            '的命令合同，因此按 incomplete_or_unreadable fail closed。'
        ),
    },
}

QUALIFIED = [
    'cq_q_3e7bd1708ff77403d01141eed87a0d38',
    'cq_q_3e94666b4738de5e0a5df40052329f18',
    'cq_q_3f45aeaf42ea66632927d3dfc96608bf',
    'cq_q_3f6b196a94cc495fb482d88305f9ab94',
    'cq_q_40513b5c52db7d66bb1432079733783c',
    'cq_q_458ab81f23e2fde622c12a1a85c8438a',
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


def verify_source_packet() -> None:
    packet = read_json(SOURCE_PACKET_PATH)
    if packet.get('schema_version') != 'answer_batch_source_packet.v2' or packet.get('batch') != '0023':
        raise SystemExit('unexpected batch 0023 source packet identity')
    if packet.get('source_policy') != 'repository_source_only_exact_id_or_exact_normalized_wording_no_fuzzy_inference':
        raise SystemExit('batch 0023 source packet predates legacy-id-tolerant exact matching')
    entries = packet.get('canonicals') or []
    if len(entries) != 10:
        raise SystemExit(f'expected 10 source-packet Canonicals, got {len(entries)}')
    missing = [entry.get('canonical_id') for entry in entries if not entry.get('source_hits')]
    if missing:
        raise SystemExit(f'batch 0023 source packet still has missing hits: {missing}')
    edit = next((entry for entry in entries if entry.get('canonical_id') == 'cq_q_3e94666b4738de5e0a5df40052329f18'), None)
    if not edit or not any(hit.get('match_basis') == 'normalized_original_question_exact' for hit in edit.get('source_hits') or []):
        raise SystemExit('edit-distance source was not recovered through the exact normalized-wording fallback')


def normalize_process_question(canonicals: list[dict], questions: list[dict], audit: dict) -> bool:
    spec = PROCESS_NORMALIZE
    cid = spec['canonical_id']
    old_qid = spec['old_qid']
    new_qid = spec['new_qid']
    if question_id(spec['new_text']) != new_qid:
        raise SystemExit('normalized process Question id drifted from expected digest')

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


def correct_python_type(canonicals: list[dict], questions: list[dict]) -> bool:
    spec = PYTHON_TYPE_FIX
    cid = spec['canonical_id']
    qid = spec['qid']
    changed = False

    note = read_json(spec['note_path'])
    matches = [q for q in note.get('tagged_questions', []) if q.get('question_id') == qid]
    if len(matches) != 1:
        raise SystemExit(f'{cid}: expected one Python source Question, got {len(matches)}')
    tagged = matches[0]
    if tagged.get('original_question') != spec['text']:
        raise SystemExit(f'{cid}: Python source wording drifted')
    if tagged.get('question_type') == spec['old_type']:
        tagged['question_type'] = spec['new_type']
        write_json(spec['note_path'], note)
        changed = True
    elif tagged.get('question_type') != spec['new_type']:
        raise SystemExit(f'{cid}: unexpected Python source question_type: {tagged.get("question_type")}')

    rows = [row for row in questions if row.get('question_id') == qid]
    if len(rows) != 1 or rows[0].get('canonical_id') != cid:
        raise SystemExit(f'{cid}: projected Python Question missing or misbound')
    if rows[0].get('question_type') == spec['old_type']:
        rows[0]['question_type'] = spec['new_type']
        changed = True
    elif rows[0].get('question_type') != spec['new_type']:
        raise SystemExit(f'{cid}: unexpected projected Python question_type: {rows[0].get("question_type")}')

    canonical = next((row for row in canonicals if row.get('canonical_id') == cid), None)
    if not canonical:
        raise SystemExit(f'{cid}: Canonical missing')
    if canonical.get('primary_domain') == {'l1': '其他', 'l2': '其他'}:
        canonical['primary_domain'] = {'l1': '其他', 'l2': 'Python'}
        changed = True
    elif canonical.get('primary_domain') != {'l1': '其他', 'l2': 'Python'}:
        raise SystemExit(f'{cid}: unexpected Canonical domain: {canonical.get("primary_domain")}')

    print(f'Corrected answer-type source metadata {cid}: {spec["old_type"]} -> {spec["new_type"]}')
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
        task = task.replace('- Canonical count: `10`', '- Original batch Canonical count: `10`\n- Active after source-boundary audit: `8`')
    replacements = {
        '- `cq_q_449cb09687b14bdba2c6864c7787239f` — coding; risks: long_tail_baseline, placeholder_implementation':
            '- `cq_q_449cb09687b14bdba2c6864c7787239f` — coding; normalized to source-backed process-termination wording without inventing a required shell pipeline.',
        '- `cq_q_44ff2aad182c5458e01efb1d5e71d10f` — coding; risks: long_tail_baseline, placeholder_implementation':
            '- `cq_q_44ff2aad182c5458e01efb1d5e71d10f` — concept; source-qualified Python dict API enumeration; corrected from erroneous Coding metadata.',
        '- `cq_q_454acf00cd919a7e95a309068e8eaf5a` — coding; risks: long_tail_baseline, placeholder_implementation':
            '- `cq_q_454acf00cd919a7e95a309068e8eaf5a` — retired fail-closed: source preserves only “斗地主发牌程序”, not an executable problem contract.',
        '- `cq_q_454e063c3dff5366f28907955aa777e3` — coding; risks: long_tail_baseline, placeholder_implementation':
            '- `cq_q_454e063c3dff5366f28907955aa777e3` — retired fail-closed: source says only “查看前10的URL”; ranking criterion and log field contract are unrecoverable.',
    }
    for old, new in replacements.items():
        if old in task:
            task = task.replace(old, new)
        elif new not in task:
            raise SystemExit(f'batch 0023 task line drifted: {old}')
    if '## Source-first boundary disposition' not in task:
        task = task.rstrip() + '''\n\n## Source-first boundary disposition\n\n- Repository source packet: `review/reports/ANSWER_BATCH_0023_SOURCE_PACKET.{json,md}` (10/10 source-hit coverage, including exact normalized-wording recovery for the stale edit-distance source id).\n- Boundary audit: 6 directly candidate-qualified, 1 recoverable wording normalization, 1 answer-type metadata correction, 2 source-unrecoverable singletons retired fail-closed.\n- Candidate/research work may proceed only for the 8 active Canonicals after the full integrity gates pass.\n'''
    TASK_PATH.write_text(task, encoding='utf-8')

    BOUNDARY_PATH.parent.mkdir(parents=True, exist_ok=True)
    BOUNDARY_PATH.write_text('''# Answer Batch 0023 — Source-first Boundary Audit

This audit was performed from `review/reports/ANSWER_BATCH_0023_SOURCE_PACKET.{json,md}` and the repository-local caption/image transcripts before candidate authoring. It separates source recoverability from answer correctness and fails closed when the surviving source cannot uniquely define an executable coding/command contract.

## Verdict

- Original batch Canonicals: 10
- Directly candidate-qualified: 6
- Recoverable wording normalization: 1
- Answer-type metadata correction: 1
- Source-unrecoverable / excluded: 2
- Active after boundary remediation: 8

## Dispositions

| Canonical | Disposition | Source-first reason |
| --- | --- | --- |
| `cq_q_3e7bd1708ff77403d01141eed87a0d38` | candidate-qualified | Caption preserves the full minimum-window contract: shortest substring of `S` containing every character of `T`, including duplicate multiplicity, or empty string if absent. |
| `cq_q_3e94666b4738de5e0a5df40052329f18` | candidate-qualified | The original tag carried a stale Question id, but an exact normalized wording match recovers the repository image transcript for LeetCode 72, including both words, the insert/delete/replace operations, and examples. |
| `cq_q_3f45aeaf42ea66632927d3dfc96608bf` | candidate-qualified | Caption explicitly identifies “字符串相乘，Leetcode43”; the stable problem identity is recoverable without inventing a different big-integer task. |
| `cq_q_3f6b196a94cc495fb482d88305f9ab94` | candidate-qualified | Caption states: from a given array choose three values as triangle sides and maximize perimeter. The objective and input object are preserved. |
| `cq_q_40513b5c52db7d66bb1432079733783c` | candidate-qualified | Image transcript explicitly records “手撕：排序链表”; this is a stable executable problem identity. |
| `cq_q_449cb09687b14bdba2c6864c7787239f` | normalize, then candidate-qualified | Source says only “Linux命令，批量终止名字包含abc的进程”. The current Canonical invents a mandatory `ps|grep|awk|xargs`-style pipeline. Normalize to the source-backed process-termination goal; the answer may compare safe command choices instead of pretending one pipeline was required. |
| `cq_q_44ff2aad182c5458e01efb1d5e71d10f` | reclassify Concept, then candidate-qualified | Caption explicitly asks how to obtain values from a Python dictionary. It is an API/enumeration question, not an algorithm-handwriting contract; the current Coding tag and placeholder Java implementation are classification debt. |
| `cq_q_454acf00cd919a7e95a309068e8eaf5a` | exclude / `incomplete_or_unreadable` | Source only says an interviewer gave a “斗地主发牌程序”. It does not preserve deck/player/bottom-card rules, shuffle/deal order, I/O representation, or requested interface, so common tutorial implementations cannot safely substitute for the interview contract. |
| `cq_q_454e063c3dff5366f28907955aa777e3` | exclude / `incomplete_or_unreadable` | Three repository captions all say only “对于日志文件，查看前10的URL，用什么命令”. None says “按出现频率”, and none preserves the log format or URL field. The current Canonical adds unsupported ranking semantics; a unique command contract cannot be reconstructed. |
| `cq_q_458ab81f23e2fde622c12a1a85c8438a` | candidate-qualified | Image transcript explicitly asks to implement equality comparison for two trees, return `1` when equal, another value otherwise, and state complexity. |

## Normalization

`cq_q_449cb09687b14bdba2c6864c7787239f` remains the Canonical identity, but its source Question is narrowed from the unsupported pipeline-specific wording to:

> Linux 命令：批量终止名字包含 abc 的进程

The normalized Question id is `55ee94f1cd20c8f85bc43f9f932f602f`. The source does not distinguish process-name matching from full-command-line matching, so the final answer must state that boundary when comparing commands; it must not claim the interview required a particular pipeline.

## Type correction

`cq_q_44ff2aad182c5458e01efb1d5e71d10f` keeps its Question identity and is reclassified from `算法手撕_Coding` to `八股文_Concept`. Its source asks for Python dictionary value-access methods and does not request a runnable algorithm or Java implementation. The answer-type audit must resolve this Canonical to `concept` before candidate authoring.

## Fail-closed exclusions

The two excluded singleton Canonicals are archived rather than answered. Each source row remains auditable through `config/question_validity_audit.json` with `incomplete_or_unreadable` and a specific explanation. Stronger future repository evidence may restore a unique contract through the normal migration path.

## Next gate

Only after repository projections are rebuilt and `check_question_coverage`, `canonical check`, `review integrity`, strict answer validation, full validation, unit tests, answer type audit, and all answer CI gates pass may batch 0023 candidate work begin.
''', encoding='utf-8')


def main() -> None:
    verify_source_packet()
    canonicals = read_jsonl(CANONICAL_PATH)
    questions = read_jsonl(QUESTION_PATH)
    progress = read_json(PROGRESS_PATH)
    audit = read_json(VALIDITY_AUDIT_PATH)

    active_ids = {row.get('canonical_id') for row in canonicals}
    expected = set(QUALIFIED) | {PROCESS_NORMALIZE['canonical_id'], PYTHON_TYPE_FIX['canonical_id']} | set(RETIRE)
    missing = sorted(expected - active_ids)
    if missing:
        # Idempotent reruns may legitimately find only the retired ids missing.
        unexpected = [cid for cid in missing if cid not in RETIRE]
        if unexpected:
            raise SystemExit(f'batch 0023 active inputs disappeared: {unexpected}')

    normalize_process_question(canonicals, questions, audit)
    correct_python_type(canonicals, questions)
    canonicals, _ = retire_unrecoverable(canonicals, questions, progress, audit)

    write_jsonl(CANONICAL_PATH, canonicals)
    write_jsonl(QUESTION_PATH, questions)
    write_json(PROGRESS_PATH, progress)
    write_json(VALIDITY_AUDIT_PATH, audit)
    update_task_and_boundary()

    final_ids = {row.get('canonical_id') for row in canonicals}
    for cid in QUALIFIED + [PROCESS_NORMALIZE['canonical_id'], PYTHON_TYPE_FIX['canonical_id']]:
        if cid not in final_ids:
            raise SystemExit(f'candidate-qualified Canonical disappeared: {cid}')
    leaked = sorted(set(RETIRE) & final_ids)
    if leaked:
        raise SystemExit(f'retired Canonicals remain active: {leaked}')


if __name__ == '__main__':
    main()
