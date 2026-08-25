SELECT
    s.student_id,
    s.name,
    sc.score
FROM students AS s
JOIN scores AS sc
  ON sc.student_id = s.student_id
ORDER BY sc.score DESC, s.student_id ASC
LIMIT 10;
