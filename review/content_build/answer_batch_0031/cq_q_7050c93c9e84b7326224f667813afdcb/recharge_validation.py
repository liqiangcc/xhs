import sqlite3
from decimal import Decimal
con=sqlite3.connect(':memory:')
con.execute('create table recharge_record(id integer primary key, user_id integer not null, amount text not null, status integer not null, paid_at text)')
rows=[
  (1,10,'50.00',1,'2026-07-25 00:00:00'),
  (2,10,'25.50',1,'2026-08-24 23:59:59'),
  (3,20,'75.50',1,'2026-08-01 12:00:00'),
  (4,30,'1000.00',2,'2026-08-10 12:00:00'),
  (5,40,'999.00',1,'2026-07-24 23:59:59'),
  (6,50,'999.00',1,'2026-08-25 00:00:00'),
]
con.executemany('insert into recharge_record values(?,?,?,?,?)',rows)
start='2026-07-25 00:00:00'; end='2026-08-25 00:00:00'
q='''select user_id, sum(cast(amount as numeric)) total_amount from recharge_record where status=1 and paid_at>=? and paid_at<? group by user_id order by total_amount desc,user_id asc limit 1'''
top=con.execute(q,(start,end)).fetchone()
assert top[0]==10 and Decimal(str(top[1]))==Decimal('75.5'),top
included=[r[0] for r in con.execute('select id from recharge_record where status=1 and paid_at>=? and paid_at<? order by id',(start,end))]
assert included==[1,2,3],included
assert con.execute(q,('2099-01-01','2099-02-01')).fetchone() is None
print('PASS top-user=10 total=75.5 start-inclusive=yes end-exclusive=yes failed-excluded=yes old-excluded=yes empty-window=yes')
