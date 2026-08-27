import sqlite3

con = sqlite3.connect(':memory:')
con.execute('create table students(student_id integer primary key, name text not null)')
con.execute('create table scores(student_id integer not null, course_id integer not null, score integer not null, primary key(student_id, course_id))')
con.executemany('insert into students values(?,?)', [
    (1,'Alice'), (2,'Bob'), (3,'Cara'), (4,'Dan'), (5,'Eve')
])
con.executemany('insert into scores values(?,?,?)', [
    (1,101,60), (1,102,70),
    (2,101,59), (2,102,100),
    (3,101,100),
    (5,101,60), (5,102,60),
])
sql = '''
SELECT s.name
FROM students AS s
JOIN scores AS sc ON sc.student_id = s.student_id
GROUP BY s.student_id, s.name
HAVING MIN(sc.score) >= 60
ORDER BY s.student_id;
'''
rows = [r[0] for r in con.execute(sql)]
expected = ['Alice','Cara','Eve']
assert rows == expected, (rows, expected)
assert 'Bob' not in rows
assert 'Dan' not in rows
print('PASS included=Alice,Cara,Eve below60=excluded no-course=excluded boundary60=included')
