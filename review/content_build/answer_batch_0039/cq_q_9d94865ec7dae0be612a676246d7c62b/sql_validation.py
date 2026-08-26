import sqlite3
con=sqlite3.connect(':memory:')
con.execute('create table students(student_id integer primary key, name text not null)')
con.execute('create table scores(student_id integer not null, subject_id text not null, score integer not null, unique(student_id, subject_id))')
con.executemany('insert into students values(?,?)',[(1,'Alice'),(2,'Bob'),(3,'Cara'),(4,'Dan'),(5,'Eve')])
con.executemany('insert into scores values(?,?,?)',[
    (1,'a',90),(1,'b',85),(1,'c',70),
    (2,'a',95),(2,'b',80),(2,'c',50),
    (3,'a',100),(3,'b',99),(3,'c',98),
    (4,'a',81),(4,'b',79),(4,'c',60),
    (5,'a',80),(5,'b',80),(5,'c',80),
])
sql='''WITH per_student AS (
  SELECT s.student_id,s.name,
    SUM(CASE WHEN sc.score >= 80 THEN 1 ELSE 0 END) AS high_score_subjects,
    SUM(CASE WHEN sc.score >= :pass_score THEN 1 ELSE 0 END) AS passed_subjects
  FROM students AS s JOIN scores AS sc ON sc.student_id=s.student_id
  GROUP BY s.student_id,s.name
), ranked AS (
  SELECT student_id,name,high_score_subjects,passed_subjects,
    ROW_NUMBER() OVER (ORDER BY high_score_subjects DESC, student_id ASC) AS rn
  FROM per_student
) SELECT name,passed_subjects FROM ranked WHERE rn <= 3 ORDER BY rn'''
rows=list(con.execute(sql,{'pass_score':60}))
expected=[('Cara',3),('Eve',3),('Alice',3)]
assert rows==expected,(rows,expected)
rows70=list(con.execute(sql,{'pass_score':70}))
expected70=[('Cara',3),('Eve',3),('Alice',3)]
assert rows70==expected70,(rows70,expected70)
high=dict(con.execute('SELECT student_id,SUM(CASE WHEN score >= 80 THEN 1 ELSE 0 END) FROM scores GROUP BY student_id'))
assert high[2]==2 and high[5]==3, high
print('PASS top3=Cara,Eve,Alice includes-score-80 stable-tie-break pass-score-parameterized student-grain')
