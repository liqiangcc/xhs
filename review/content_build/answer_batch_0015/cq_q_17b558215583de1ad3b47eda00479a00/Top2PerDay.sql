WITH ranked AS (
    SELECT
        id,
        purchase_date,
        purchase_count,
        ROW_NUMBER() OVER (
            PARTITION BY purchase_date
            ORDER BY purchase_count DESC, id ASC
        ) AS rn
    FROM purchases
)
SELECT id, purchase_date, purchase_count
FROM ranked
WHERE rn <= 2
ORDER BY purchase_date ASC, rn ASC;
