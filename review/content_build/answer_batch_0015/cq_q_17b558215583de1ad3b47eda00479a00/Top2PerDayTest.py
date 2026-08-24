#!/usr/bin/env python3
import sqlite3

QUERY = """
WITH ranked AS (
    SELECT
        id,
        purchase_date,
        purchase_count,
        ROW_NUMBER() OVER (
            PARTITION BY purchase_date
            ORDER BY purchase_count DESC, id ASC
        ) AS rn
    FROM purchases
)
SELECT id, purchase_date, purchase_count
FROM ranked
WHERE rn <= 2
ORDER BY purchase_date ASC, rn ASC;
"""

conn = sqlite3.connect(":memory:")
conn.execute("""
CREATE TABLE purchases (
    id INTEGER PRIMARY KEY,
    purchase_date TEXT NOT NULL,
    purchase_count INTEGER NOT NULL
)
""")
rows = [
    (1, "2026-08-20", 10),
    (2, "2026-08-20", 8),
    (3, "2026-08-20", 10),
    (4, "2026-08-21", 5),
    (5, "2026-08-21", 7),
    (6, "2026-08-21", 6),
    (7, "2026-08-22", 1),
    (8, "2026-08-22", 1),
    (9, "2026-08-22", 1),
]
conn.executemany(
    "INSERT INTO purchases(id, purchase_date, purchase_count) VALUES (?, ?, ?)",
    rows,
)
actual = conn.execute(QUERY).fetchall()
expected = [
    (1, "2026-08-20", 10),
    (3, "2026-08-20", 10),
    (5, "2026-08-21", 7),
    (6, "2026-08-21", 6),
    (7, "2026-08-22", 1),
    (8, "2026-08-22", 1),
]
assert actual == expected, (actual, expected)

per_day = {}
for row in actual:
    per_day[row[1]] = per_day.get(row[1], 0) + 1
assert per_day == {
    "2026-08-20": 2,
    "2026-08-21": 2,
    "2026-08-22": 2,
}, per_day

print("PASS dates=3 rows=6 tie_policy=row_number id_tiebreak=true")
