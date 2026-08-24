SELECT student_name,
       SUM(score) AS total_score
FROM student_scores
GROUP BY student_name
ORDER BY student_name;
