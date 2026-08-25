import sqlite3
from pathlib import Path

sql = Path(__file__).with_name('top_ten_students.sql').read_text(encoding='utf-8')

def run_case(students, scores):
    con = sqlite3.connect(':memory:')
    con.execute('create table students(student_id integer primary key, name text not null)')
    con.execute('create table scores(student_id integer primary key, score real not null)')
    con.executemany('insert into students(student_id,name) values(?,?)', students)
    con.executemany('insert into scores(student_id,score) values(?,?)', scores)
    actual = con.execute(sql).fetchall()
    names = dict(students)
    expected = [(sid, names[sid], float(score)) for sid, score in sorted(scores, key=lambda r: (-r[1], r[0]))[:10] if sid in names]
    assert actual == expected, (actual, expected)
    assert len(actual) <= 10
    assert len({r[0] for r in actual}) == len(actual)
    return actual

assert run_case([], []) == []
small_students = [(5,'E'),(1,'A'),(4,'D'),(2,'B'),(3,'C'),(6,'NoScore')]
small_scores = [(1,90),(2,95),(3,95),(4,70),(5,88)]
assert [r[0] for r in run_case(small_students, small_scores)] == [2,3,1,5,4]

students = [(i, f'S{i}') for i in range(1,15)]
scores = [(1,100),(2,99),(3,98),(4,97),(5,96),(6,95),(7,94),(8,93),(9,92),(10,91),(11,91),(12,90),(13,80)]
rows = run_case(students, scores)
assert len(rows) == 10
assert [r[0] for r in rows] == list(range(1,11)), rows
assert all(r[0] != 11 for r in rows), 'tie at cutoff must use student_id ASC and keep id=10 first'
assert all(r[0] != 14 for r in rows), 'student without score must be excluded by INNER JOIN'
print('PASS empty=0 small=5 top10=10 tie=cutoff-deterministic no-score=excluded')
