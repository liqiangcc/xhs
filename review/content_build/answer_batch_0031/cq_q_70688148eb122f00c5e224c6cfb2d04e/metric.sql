WITH paid_orders AS (
    SELECT order_id, user_id
    FROM orders
    WHERE status = 'paid'
      AND created_at >= :start_at
      AND created_at <  :end_at
),
order_amount AS (
    SELECT
        p.order_id,
        p.user_id,
        SUM(i.quantity * i.unit_price_cents) AS revenue_cents
    FROM paid_orders AS p
    JOIN order_items AS i
      ON i.order_id = p.order_id
    GROUP BY p.order_id, p.user_id
)
SELECT
    u.segment,
    COUNT(*) AS paid_order_count,
    SUM(a.revenue_cents) AS revenue_cents
FROM order_amount AS a
JOIN users AS u
  ON u.user_id = a.user_id
GROUP BY u.segment
ORDER BY u.segment;
