SELECT name
FROM grades
GROUP BY name
HAVING SUM(
    CASE
        WHEN score <= 80 OR score IS NULL THEN 1
        ELSE 0
    END
) = 0;
