
import sqlite3
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "database" / "business.db"


def test_database():

    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")
    cursor = conn.cursor()

    print("\n========== DATABASE TESTING ==========\n")

    # 1. Check tables
    print("1. AVAILABLE TABLES:")

    cursor.execute("""
        SELECT name
        FROM sqlite_master
        WHERE type = 'table'
        AND name NOT LIKE 'sqlite_%'
    """)

    tables = cursor.fetchall()

    for table in tables:
        print("-", table[0])

    # 2. Check record counts
    print("\n2. RECORD COUNTS:")

    for (table_name,) in tables:
        count = cursor.execute(
            f"SELECT COUNT(*) FROM {table_name}"
        ).fetchone()[0]

        print(f"{table_name}: {count}")

    # 3. Test customer and order relationship
    print("\n3. CUSTOMER ORDER DETAILS:")

    cursor.execute("""
        SELECT
            c.name,
            o.order_id,
            o.status,
            o.order_date
        FROM customers c
        JOIN orders o
        ON c.customer_id = o.customer_id
        LIMIT 5
    """)

    for row in cursor.fetchall():
        print(row)

    # 4. Test product revenue
    print("\n4. TOP 5 PRODUCTS BY REVENUE:")

    cursor.execute("""
        SELECT
            p.product_name,
            SUM(oi.quantity * oi.unit_price) AS revenue
        FROM products p
        JOIN order_items oi
        ON p.product_id = oi.product_id
        JOIN orders o
        ON oi.order_id = o.order_id
        WHERE o.status != 'Cancelled'
        GROUP BY p.product_id, p.product_name
        ORDER BY revenue DESC
        LIMIT 5
    """)

    for row in cursor.fetchall():
        print(row)

    # 5. Check foreign key integrity
    print("\n5. FOREIGN KEY CHECK:")

    cursor.execute("PRAGMA foreign_key_check")
    errors = cursor.fetchall()

    if not errors:
        print("SUCCESS: No foreign key violations!")
    else:
        print("ERROR:", errors)

    conn.close()

    print("\n========== TESTING COMPLETED ==========")


if __name__ == "__main__":
    test_database()
