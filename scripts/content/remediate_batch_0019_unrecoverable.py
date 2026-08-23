#!/usr/bin/env python3
"""Retire batch-0019 singleton questions whose coding contract is absent from source.

The operation is source-bounded, fail-closed, and idempotent. It updates only
Question/Canonical ownership, ReviewProgress, the validity audit, and active /
archive answer placement. Generated Question/index projections are rebuilt by
the calling workflow after this script succeeds.
"""

from __future__ import annotations

import json
from pathlib import Path
import shutil

ROOT = Path(".")
TARGETS = {
    "cq_q_2dcc4ae8850241c339c211516c55b307": {
        "expected_original": "算法手撕：Java 实现 Shell 脚本的目录递归遍历功能。",
        "explanation": (
            "仓库原始来源只保留“给一个shell脚本(遍历目录)，用java实现相关功能”，但没有保存被给出的 Shell 脚本正文。"
            "因此无法恢复遍历顺序、过滤规则、符号链接处理、输出格式、错误处理或其他脚本行为；"
            "当前结构化标题把括号中的“遍历目录”扩展成了一个确定的递归遍历契约。缺少脚本原文时不能编造等价 Java 实现。"
        ),
    },
    "cq_q_2e11155d7a78e8fda6758fc98aa44029": {
        "expected_original": "SQL 实操题。",
        "explanation": (
            "仓库最强来源只保留“一道sql”，没有表结构、字段、样例数据、期望结果、SQL 方言、约束或完整题面。"
            "“SQL 实操题”只能证明面试中存在一题 SQL，不能唯一恢复可回答的 SQL 编码契约；在没有更强来源前必须排除，不能虚构题目。"
        ),
    },
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

    for canonical_id, spec in TARGETS.items():
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
        if row.get("original_question") != spec["expected_original"]:
            raise SystemExit(
                f"{canonical_id}: original question drifted: {row.get('original_question')!r} != {spec['expected_original']!r}"
            )

        ref = (row["source_note_id"], row["source_question_index"])
        replacement = {
            "source_note_id": row["source_note_id"],
            "source_question_index": row["source_question_index"],
            "question_id": qid,
            "original_question": row["original_question"],
            "decision": "exclude",
            "exclusion_reason": "incomplete_or_unreadable",
            "exclusion_note": spec["explanation"],
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
        print("Batch 0019 source-unrecoverable remediation already applied.")
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

    print("Retired source-unrecoverable batch 0019 singletons:", ", ".join(sorted(TARGETS)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
