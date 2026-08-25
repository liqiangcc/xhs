import sqlite3

con=sqlite3.connect(':memory:')
con.execute('create table order_detail(dt text not null, product_id text not null, quantity integer not null)')
target='2026-08-25'
other='2026-08-24'
for i in range(1,106):
    product=f'P{i:03d}'
    total=105 if i in (104,105) else i
    first=total//2
    second=total-first
    con.execute('insert into order_detail values(?,?,?)',(target,product,first))
    con.execute('insert into order_detail values(?,?,?)',(target,product,second))
    con.execute('insert into order_detail values(?,?,?)',(other,product,10000))

sql='''
WITH product_sales AS (
    SELECT product_id, SUM(quantity) AS sales
    FROM order_detail
    WHERE dt = ?
    GROUP BY product_id
)
SELECT product_id, sales
FROM product_sales
ORDER BY sales DESC, product_id ASC
LIMIT 100
'''
rows=con.execute(sql,(target,)).fetchall()
assert len(rows)==100, len(rows)
assert rows[0]==('P104',105), rows[:3]
assert rows[1]==('P105',105), rows[:3]
assert rows[2]==('P103',103), rows[:3]
assert rows[-1]==('P006',6), rows[-3:]
ids={r[0] for r in rows}
assert 'P005' not in ids and 'P006' in ids
assert all(rows[i][1] >= rows[i+1][1] for i in range(len(rows)-1))
assert con.execute(sql,(other,)).fetchone()==('P001',10000)
empty=con.execute(sql,('2099-01-01',)).fetchall()
assert empty==[]
print('PASS rows=100 aggregation=yes date-isolation=yes descending=yes deterministic-tie=yes cutoff=P006 empty-date=zero')
