import sqlite3
con=sqlite3.connect(':memory:')
con.execute('create table login_log(user_id text not null, login_time text not null)')
con.executemany('insert into login_log values(?,?)',[
    ('u1','2026-01-01 08:00:00'),('u1','2026-01-01 09:00:00'),('u2','2026-01-01 10:00:00'),
    ('u1','2026-01-02 07:00:00'),('u3','2026-01-02 12:00:00'),('u3','2026-01-02 13:00:00'),
    ('u2','2026-01-03 06:00:00'),('u3','2026-01-03 07:00:00'),('u4','2026-01-03 08:00:00'),
])
q1='''WITH daily_users AS (SELECT DISTINCT user_id, DATE(login_time) AS login_date FROM login_log), first_login AS (SELECT user_id, MIN(DATE(login_time)) AS first_date FROM login_log GROUP BY user_id) SELECT d.login_date, SUM(CASE WHEN d.login_date=f.first_date THEN 1 ELSE 0 END), SUM(CASE WHEN d.login_date>f.first_date THEN 1 ELSE 0 END) FROM daily_users d JOIN first_login f ON f.user_id=d.user_id GROUP BY d.login_date ORDER BY d.login_date'''
q2='''WITH daily_users AS (SELECT DISTINCT user_id, DATE(login_time) AS login_date FROM login_log) SELECT d.login_date, SUM(CASE WHEN NOT EXISTS (SELECT 1 FROM daily_users p WHERE p.user_id=d.user_id AND p.login_date<d.login_date) THEN 1 ELSE 0 END), SUM(CASE WHEN EXISTS (SELECT 1 FROM daily_users p WHERE p.user_id=d.user_id AND p.login_date<d.login_date) THEN 1 ELSE 0 END) FROM daily_users d GROUP BY d.login_date ORDER BY d.login_date'''
expected=[('2026-01-01',2,0),('2026-01-02',1,1),('2026-01-03',1,2)]
rows1=list(con.execute(q1)); rows2=list(con.execute(q2))
assert rows1==expected,(rows1,expected); assert rows2==expected,(rows2,expected); assert rows1==rows2
active=list(con.execute("select DATE(login_time),count(distinct user_id) from login_log group by DATE(login_time) order by 1"))
assert [(d,n+o) for d,n,o in rows1]==active
print('PASS days=3 expected=2/0,1/1,1/2 same-day-duplicates=deduped min-date=not-exists-equivalent active-invariant=pass')
