#!/usr/bin/env python3
"""Retire batch-0018 singleton questions whose coding contract cannot be recovered.

This script is intentionally source-bounded and idempotent. It updates only the
Question/Canonical SSOT, ReviewProgress, the validity audit, and active/archive
answer placement. Generated Question/index projections are rebuilt by the
calling workflow after this script exits successfully.
"""

from __future__ import annotations

import json
from pathlib import Path
import shutil

ROOT = Path(".")
TARGETS = {
    "cq_q_28ddc5240672730f91363131ba8cc14e": (
        "原始仓库来源只保留“模式匹配”，没有说明是普通子串查找、KMP、通配符、正则表达式或其他模式语义，"
        "也没有输入、输出、示例或约束。当前结构化层的“字符串模式匹配（Pattern Matching）”仍不足以唯一恢复编码契约；"
        "在没有更强来源前不能猜测一个熟悉算法并把它当作原题。"
    ),
    "cq_q_2979c00d6ff6c1582ecb289775522412": (
        "原始 note_desc 只保留“SQL题：找出最长连续子序 (row_number)”。仓库没有表结构、分区键、排序列、连续单位、重复值规则或期望输出；"
        "结构化层扩写出的“一个用户最长连续登录天数/子序列”没有原文支撑。即使 row_number 暗示 gaps-and-islands 技巧，也不足以恢复一条严格 SQL 契约。"
    ),
    "cq_q_2a09d0d7980006e66439a361880bc83d": (
        "原始来源要求“输入一个字符串，输出所有字符组合”，并追问拷贝构造、移动构造、拷贝赋值、移动赋值；"
        "来源没有说明“所有字符组合”究竟指排列、组合、子集/子序列、是否去重或输出顺序。当前 Canonical 将其扩写成“全排列组合”且元数据偏 Java，"
        "与 C++ copy/move 语义信号也不一致。缺少更强题面时无法唯一恢复一个严格编码目标。"
    ),
    "cq_q_2bd82e0bd4203f85f02cca39fb7a67e2": (
        "原始 note_desc 只保留“SQL:最大连续问题”，没有表、列、连续单位、分组维度、重复规则或期望投影。"
        "结构化层扩写出的 Max Consecutive Days、ROW_NUMBER 自减抵消法、用户活跃/签到场景和递归 CTE 等信息均没有原文证据，不能据此构造正式 SQL 答案。"
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
            active_rows = [
                row for row in question_rows_by_id.get(qid, []) if row.get("canonical_id") == canonical_id
            ]
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
        progress["items"] = [
            item for item in progress.get("items", []) if item.get("canonical_id") != canonical_id
        ]
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
        print("Batch 0018 unrecoverable-question remediation already applied.")
        return 0

    decisions.sort(key=lambda decision: (str(decision.get("source_note_id", "")), int(decision.get("source_question_index", 0))))
    audit["decisions"] = decisions
    audit["audited_at"] = "2026-08-23"
    audit["include_count"] = sum(1 for decision in decisions if decision.get("decision") == "include")
    audit["exclude_count"] = sum(1 for decision in decisions if decision.get("decision") == "exclude")
    write_json(audit_path, audit)
    write_jsonl(canonical_path, sorted(canonicals, key=lambda item: item["canonical_id"]))
    progress["updated_at"] = "2026-08-23"
    progress["items"] = sorted(progress.get("items", []), key=lambda item: item.get("canonical_id", ""))
    write_json(progress_path, progress)

    print("Retired source-unrecoverable batch 0018 singletons:", ", ".join(sorted(TARGETS)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
