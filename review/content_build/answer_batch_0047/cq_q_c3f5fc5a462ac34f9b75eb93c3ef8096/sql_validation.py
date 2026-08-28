#!/usr/bin/env python3
import sqlite3

SQL = """
WITH user_purchase AS (
    SELECT user_id, SUM(quantity) AS purchase_qty
    FROM purchase_events
    GROUP BY user_id
),
ranked AS (
    SELECT
        user_id,
        purchase_qty,
        PERCENT_RANK() OVER (ORDER BY purchase_qty DESC) AS pct_rank
    FROM user_purchase
)
SELECT user_id, purchase_qty
FROM ranked
WHERE pct_rank <= 0.25
ORDER BY purchase_qty DESC, user_id
"""


def run(values):
    con = sqlite3.connect(':memory:')
    con.execute('create table purchase_events(user_id text not null, quantity integer not null)')
    con.executemany('insert into purchase_events values(?,?)', values)
    return con.execute(SQL).fetchall()

baseline = [(f'u{i}', q) for i, q in enumerate([100, 90, 80, 70, 60, 50, 40, 30], start=1)]
assert run(baseline) == [('u1', 100), ('u2', 90)]

tied_top = [('u1', 100), ('u2', 100), ('u3', 80), ('u4', 70), ('u5', 60), ('u6', 50), ('u7', 40), ('u8', 30)]
assert run(tied_top) == [('u1', 100), ('u2', 100)]

multi_rows = [('u1', 40), ('u1', 60), ('u2', 45), ('u2', 45), ('u3', 80), ('u4', 70), ('u5', 60), ('u6', 50), ('u7', 40), ('u8', 30)]
assert run(multi_rows) == [('u1', 100), ('u2', 90)]

assert run([('solo', 7)]) == [('solo', 7)]

print('PASS user-grain=aggregated top25=2of8 ties=preserved multi-row=sum single-user=included')
