import sqlite3

con = sqlite3.connect(':memory:')
con.execute('CREATE TABLE income_records(user_id INTEGER, income NUMERIC, month TEXT)')
con.executemany(
    'INSERT INTO income_records VALUES (?, ?, ?)',
    [
        (1, 400, '2026-01'),
        (1, 700, '2026-01'),
        (1, 1000, '2026-02'),
        (2, 600, '2026-01'),
        (2, 500, '2026-01'),
        (2, 300, '2026-02'),
        (2, 900, '2026-02'),
        (3, 800, '2026-01'),
    ],
)

sql = '''
SELECT
    user_id,
    month,
    SUM(income) AS monthly_income
FROM income_records
GROUP BY user_id, month
HAVING SUM(income) > 1000
ORDER BY user_id, month
'''

rows = con.execute(sql).fetchall()
expected = [
    (1, '2026-01', 1100),
    (2, '2026-01', 1100),
    (2, '2026-02', 1200),
]
assert rows == expected, (rows, expected)
assert (1, '2026-02', 1000) not in rows, 'strict > 1000 boundary must exclude exactly 1000'
assert all(not (row[0] == 3 and row[1] == '2026-01') for row in rows), '800 total must be excluded'
print('PASS grouped-by-user-month sums=1100,1100,1200 exact-1000=excluded below-threshold=excluded')
