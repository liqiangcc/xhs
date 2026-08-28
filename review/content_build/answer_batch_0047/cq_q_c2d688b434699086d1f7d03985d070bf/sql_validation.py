#!/usr/bin/env python3
import sqlite3

SQL = """
SELECT
    student_name,
    MAX(score) AS max_score
FROM student_scores
WHERE student_name LIKE '张%'
GROUP BY student_name
ORDER BY student_name
"""

con = sqlite3.connect(':memory:')
con.execute('create table student_scores(student_name text not null, subject_name text not null, score real)')
con.executemany(
    'insert into student_scores values(?,?,?)',
    [
        ('张三', '语文', 88),
        ('张三', '数学', 95),
        ('张三', '英语', 95),
        ('张四', '语文', 60),
        ('李四', '数学', 100),
        ('王五', '英语', 99),
    ],
)
rows = con.execute(SQL).fetchall()
expected = [('张三', 95.0), ('张四', 60.0)]
assert rows == expected, (rows, expected)

con2 = sqlite3.connect(':memory:')
con2.execute('create table student_scores(student_name text not null, subject_name text not null, score real)')
con2.executemany('insert into student_scores values(?,?,?)', [('李四', '数学', 100), ('王五', '英语', 99)])
assert con2.execute(SQL).fetchall() == []

print('PASS zhang-prefix=filtered grouped-max=95,60 non-zhang=excluded tie=max-value no-zhang=empty')
