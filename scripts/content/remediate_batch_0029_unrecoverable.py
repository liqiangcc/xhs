#!/usr/bin/env python3
"""Retire batch-0029 singleton coding Questions whose exact contract is unrecoverable.

Source-first and idempotent: never invent a missing code-output fixture. The caller
rebuilds generated Question/index projections after the SSOT mutation.
"""

from __future__ import annotations

import json
from pathlib import Path
import shutil

ROOT = Path(".")
TARGETS = {
    "cq_q_69f2feb994cbec17e8d5e0d1b7f24188": (
        "原始 tagged note 只保留“代码输出：微任务、宏任务打印顺序 (Promise, setTimeout 嵌套)?”，"
        "以及 event loop/微任务/宏任务标签；仓库没有保存实际 JavaScript 代码片段、嵌套结构、Promise 链、"
        "console.log 位置或运行环境。代码输出题的唯一答案取决于这些缺失细节，不能根据一个熟悉的 event-loop 模板"
        "自行补代码再把打印顺序当作原题答案。在获得更强原始来源前，该 singleton 无法恢复严格编码契约。"
    ),
}


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, value) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def read_jsonl(path: Path):
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def write_jsonl(path: Path, rows) -> None:
    path.write_text(
        "".join(json.dumps(row, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n" for row in rows),
        encoding="utf-8",
    )


def main() -> int:
    canonical_path = ROOT / "data/questions/canonical_questions.jsonl"
    question_path = ROOT / "data/questions/questions.jsonl"
    progress_path = ROOT / "review/progress.json"
    audit_path = ROOT / "config/question_validity_audit.json"

    canonicals = read_jsonl(canonical_path)
    questions = read_jsonl(question_path)
    progress = read_json(progress_path)
    audit = read_json(audit_path)

    canonical_by_id = {row["canonical_id"]: row for row in canonicals}
    question_rows_by_id: dict[str, list[dict]] = {}
    for row in questions:
        question_rows_by_id.setdefault(row["question_id"], []).append(row)

    decisions = list(audit.get("decisions", []))
    decisions_by_ref = {
        (decision.get("source_note_id"), decision.get("source_question_index")): decision
        for decision in decisions
    }
    changed = False

    for canonical_id, explanation in TARGETS.items():
        qid = canonical_id.removeprefix("cq_q_")
        canonical = canonical_by_id.get(canonical_id)
        if canonical is None:
            active_rows = [row for row in question_rows_by_id.get(qid, []) if row.get("canonical_id") == canonical_id]
            if active_rows:
                raise SystemExit(f"{canonical_id}: canonical missing but active Question binding remains")
            if (ROOT / "review/answers" / f"{canonical_id}.md").exists():
                raise SystemExit(f"{canonical_id}: canonical missing but active Answer remains")
            if any(item.get("canonical_id") == canonical_id for item in progress.get("items", [])):
                raise SystemExit(f"{canonical_id}: canonical missing but ReviewProgress remains")
            continue

        owned = list(canonical.get("question_ids") or [])
        if owned != [qid]:
            raise SystemExit(f"{canonical_id}: expected singleton ownership [{qid}], got {owned}")
        if int(canonical.get("frequency", 0)) != 1:
            raise SystemExit(f"{canonical_id}: expected frequency=1, got {canonical.get('frequency')}")

        rows = question_rows_by_id.get(qid, [])
        if len(rows) != 1:
            raise SystemExit(f"{canonical_id}: expected exactly one Question row, got {len(rows)}")
        row = rows[0]
        if row.get("canonical_id") != canonical_id:
            raise SystemExit(f"{canonical_id}: Question binding mismatch: {row.get('canonical_id')}")
        if row.get("is_valid_for_library") is not True:
            raise SystemExit(f"{canonical_id}: Question already invalid before remediation")
        if row.get("original_question") != "代码输出：微任务、宏任务打印顺序 (Promise, setTimeout 嵌套)?":
            raise SystemExit(f"{canonical_id}: source wording drifted: {row.get('original_question')}")

        ref = (row["source_note_id"], row["source_question_index"])
        replacement = {
            "source_note_id": row["source_note_id"],
            "source_question_index": row["source_question_index"],
            "question_id": qid,
            "original_question": row["original_question"],
            "decision": "exclude",
            "exclusion_reason": "incomplete_or_unreadable",
            "exclusion_note": explanation,
        }
        previous = decisions_by_ref.get(ref)
        if previous is None:
            decisions.append(replacement)
            decisions_by_ref[ref] = replacement
            changed = True
        elif previous != replacement:
            index = decisions.index(previous)
            decisions[index] = replacement
            decisions_by_ref[ref] = replacement
            changed = True

        canonicals = [item for item in canonicals if item.get("canonical_id") != canonical_id]
        canonical_by_id.pop(canonical_id, None)

        before_progress = len(progress.get("items", []))
        progress["items"] = [item for item in progress.get("items", []) if item.get("canonical_id") != canonical_id]
        if len(progress["items"]) != before_progress - 1:
            raise SystemExit(f"{canonical_id}: expected exactly one ReviewProgress item")

        active_answer = ROOT / "review/answers" / f"{canonical_id}.md"
        archive_answer = ROOT / "review/archive/answers" / f"{canonical_id}.md"
        if not active_answer.exists():
            raise SystemExit(f"{canonical_id}: active Answer missing")
        archive_answer.parent.mkdir(parents=True, exist_ok=True)
        if archive_answer.exists():
            if archive_answer.read_bytes() != active_answer.read_bytes():
                raise SystemExit(f"{canonical_id}: existing answer archive differs from active answer")
            active_answer.unlink()
        else:
            shutil.move(str(active_answer), str(archive_answer))
        changed = True

    if not changed:
        print("Batch 0029 unrecoverable-question remediation already applied.")
        return 0

    decisions.sort(key=lambda decision: (str(decision.get("source_note_id", "")), int(decision.get("source_question_index", 0))))
    audit["decisions"] = decisions
    audit["audited_at"] = "2026-08-25"
    audit["include_count"] = sum(1 for decision in decisions if decision.get("decision") == "include")
    audit["exclude_count"] = sum(1 for decision in decisions if decision.get("decision") == "exclude")
    write_json(audit_path, audit)
    write_jsonl(canonical_path, sorted(canonicals, key=lambda item: item["canonical_id"]))
    progress["updated_at"] = "2026-08-25"
    progress["items"] = sorted(progress.get("items", []), key=lambda item: item.get("canonical_id", ""))
    write_json(progress_path, progress)

    print("Retired source-unrecoverable batch 0029 singleton:", ", ".join(sorted(TARGETS)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
