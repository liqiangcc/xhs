import sqlite3
con=sqlite3.connect(':memory:')
con.execute('create table reads(user_id integer not null, article_id integer not null, read_date text not null)')
con.executemany('insert into reads values(?,?,?)',[
  (1,101,'2026-01-01'),(1,102,'2026-01-01'),(1,103,'2026-01-02'),
  (2,201,'2026-01-01'),(2,201,'2026-01-01'),
  (3,301,'2026-01-03'),(3,302,'2026-01-03'),(3,302,'2026-01-03'),
  (4,401,'2026-01-01'),(4,402,'2026-01-02'),
  (5,501,'2026-01-01'),(5,502,'2026-01-01'),(5,503,'2026-01-02'),(5,504,'2026-01-02')])
sql='''SELECT DISTINCT user_id FROM (SELECT user_id, read_date FROM reads GROUP BY user_id, read_date HAVING COUNT(DISTINCT article_id) >= 2) AS qualified_user_days ORDER BY user_id ASC'''
rows=[r[0] for r in con.execute(sql)]
assert rows==[1,3,5], rows
assert 2 not in rows, 'duplicate reads of one article must not qualify'
assert 4 not in rows, 'different days must not be merged'
assert rows.count(5)==1, 'multiple qualifying days must not duplicate the user'
print('PASS users=1,3,5 duplicate-event=excluded cross-day=excluded final-user-dedup=verified')
