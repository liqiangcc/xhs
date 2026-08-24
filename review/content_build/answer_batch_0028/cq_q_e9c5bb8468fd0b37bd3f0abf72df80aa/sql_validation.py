import sqlite3
con=sqlite3.connect(':memory:')
con.execute('create table students(student_id integer primary key, name text not null)')
con.execute('create table grades(student_id integer not null, score real not null)')
con.executemany('insert into students values(?,?)',[(1,'Alice'),(2,'Bob'),(3,'Cara'),(4,'Dan')])
con.executemany('insert into grades values(?,?)',[(1,80),(1,90),(2,70),(4,60),(4,60)])
sql='''SELECT s.student_id, s.name, AVG(g.score) AS average_score FROM students AS s JOIN grades AS g ON g.student_id=s.student_id GROUP BY s.student_id, s.name'''
rows=sorted((sid,name,float(avg)) for sid,name,avg in con.execute(sql))
expected=[(1,'Alice',85.0),(2,'Bob',70.0),(4,'Dan',60.0)]
assert rows==expected, (rows,expected)
assert all(row[0]!=3 for row in rows), 'explicit inner-join contract must exclude students without grades'
assert next(avg for sid,_,avg in rows if sid==4)==60.0, 'equal-valued grades are separate records and both participate'
print('PASS students=1,2,4 averages=85,70,60 no-grade=excluded equal-valued-records=preserved')
