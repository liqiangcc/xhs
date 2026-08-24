import sqlite3
from pathlib import Path

query = Path('student_total_score.sql').read_text(encoding='utf-8')
connection = sqlite3.connect(':memory:')
connection.execute('CREATE TABLE student_scores (student_name TEXT NOT NULL, subject_name TEXT NOT NULL, score INTEGER)')
connection.executemany(
    'INSERT INTO student_scores(student_name, subject_name, score) VALUES (?, ?, ?)',
    [
        ('Alice', 'Math', 90),
        ('Alice', 'Chinese', 80),
        ('Bob', 'Math', 70),
        ('Bob', 'Chinese', None),
        ('Carol', 'Math', None),
        ('Dave', 'Math', 60),
        ('Dave', 'English', 60),
        ('Dave', 'Physics', 60),
    ],
)
rows = connection.execute(query).fetchall()
expected = [
    ('Alice', 170),
    ('Bob', 70),
    ('Carol', None),
    ('Dave', 180),
]
if rows != expected:
    raise AssertionError(f'expected={expected!r}, actual={rows!r}')
print('PASS fixture_rows=8 groups=4 null_score_semantics=verified')
