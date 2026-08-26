#!/usr/bin/env python3
import pathlib
import re
import sqlite3

CID = "cq_q_910472ffdcfb2d2541ca198b952df943"
ROOT = pathlib.Path(__file__).resolve().parents[4]
candidate = (ROOT / "review" / "candidates" / "answers" / f"{CID}.md").read_text(encoding="utf-8")
blocks = re.findall(r"```sql\n([\s\S]*?)\n```", candidate)
if len(blocks) != 2:
    raise SystemExit(f"expected schema block plus query block, got {len(blocks)}")
sql = blocks[1]

required = [
    "LAG(dt, 1)", "LAG(metric, 1)", "LAG(dt, 2)", "LAG(metric, 2)",
    "julianday(prev_dt) - julianday(prev2_dt) = 1",
    "julianday(dt) - julianday(prev_dt) = 1",
    "prev2_metric < prev_metric", "prev_metric < metric",
    "prev2_metric > prev_metric", "prev_metric > metric",
]
for marker in required:
    if marker not in sql:
        raise SystemExit(f"query missing {marker}")

con = sqlite3.connect(":memory:")
con.execute("CREATE TABLE daily_metric(dt TEXT PRIMARY KEY, metric REAL NOT NULL)")
rows = [
    ("2026-01-01", 1), ("2026-01-02", 2), ("2026-01-03", 3), ("2026-01-04", 4),
    ("2026-01-05", 4), ("2026-01-06", 3), ("2026-01-07", 2),
    ("2026-01-09", 10), ("2026-01-10", 9), ("2026-01-11", 8),
]
con.executemany("INSERT INTO daily_metric VALUES(?,?)", rows)
actual = list(con.execute(sql))
expected = [
    ("2026-01-01", "2026-01-02", "2026-01-03", "up"),
    ("2026-01-02", "2026-01-03", "2026-01-04", "up"),
    ("2026-01-05", "2026-01-06", "2026-01-07", "down"),
    ("2026-01-09", "2026-01-10", "2026-01-11", "down"),
]
assert actual == expected, (actual, expected)
assert not any(row[0] == "2026-01-06" and row[2] == "2026-01-09" for row in actual), "gap crossed"
assert len([row for row in actual if row[3] == "up"]) == 2, "four-day rise must produce two windows"

print("PASS windows=4 up=2 down=2 four_day_rise=two_windows equality=breaks missing_day=breaks strict_monotonic=pass")
