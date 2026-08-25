import pathlib
import sqlite3

HERE = pathlib.Path(__file__).resolve().parent
SQL = (HERE / "metric.sql").read_text(encoding="utf-8")

con = sqlite3.connect(":memory:")
con.executescript(
    """
    create table users(user_id integer primary key, segment text not null);
    create table orders(order_id integer primary key, user_id integer not null, status text not null, created_at text not null);
    create table order_items(order_id integer not null, quantity integer not null, unit_price_cents integer not null);
    """
)
con.executemany("insert into users values(?,?)", [(1, "gold"), (2, "gold"), (3, "silver"), (4, "bronze")])
con.executemany(
    "insert into orders values(?,?,?,?)",
    [
        (10, 1, "paid", "2026-08-02"),
        (11, 1, "cancelled", "2026-08-03"),
        (12, 2, "paid", "2026-08-04"),
        (13, 3, "paid", "2026-08-10"),
        (14, 3, "paid", "2026-09-02"),
        (15, 4, "paid", "2026-08-15"),
    ],
)
con.executemany(
    "insert into order_items values(?,?,?)",
    [
        (10, 2, 500), (10, 1, 1000),
        (11, 100, 9999),
        (12, 3, 500),
        (13, 1, 700), (13, 2, 100),
        (14, 10, 900),
    ],
)

rows = con.execute(SQL, {"start_at": "2026-08-01", "end_at": "2026-09-01"}).fetchall()
expected = [("gold", 2, 3500), ("silver", 1, 900)]
assert rows == expected, (rows, expected)

# The raw joined detail rows demonstrate the fan-out trap: gold has 3 item rows but only 2 paid orders.
raw_gold = con.execute(
    """
    select count(*) as item_rows, count(distinct o.order_id) as orders,
           sum(i.quantity * i.unit_price_cents) as revenue
    from orders o
    join order_items i on i.order_id=o.order_id
    join users u on u.user_id=o.user_id
    where o.status='paid' and o.created_at >= ? and o.created_at < ? and u.segment='gold'
    """,
    ("2026-08-01", "2026-09-01"),
).fetchone()
assert raw_gold == (3, 2, 3500), raw_gold

# Cancelled and out-of-window orders must not contribute; paid order with no items is excluded by declared inner-join contract.
assert all(row[0] != "bronze" for row in rows)
assert con.execute("select count(*) from orders where order_id=11 and status='cancelled'").fetchone()[0] == 1
assert con.execute("select count(*) from orders where order_id=14 and created_at >= '2026-09-01'").fetchone()[0] == 1

print("PASS gold-orders=2 gold-item-rows=3 gold-revenue=3500 silver-orders=1 silver-revenue=900 cancelled=excluded out-window=excluded no-items=excluded")
