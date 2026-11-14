
import sqlite3
import random
from pathlib import Path
from datetime import date, timedelta
from faker import Faker

# Initialize Faker and random seed
fake = Faker()
Faker.seed(42)
random.seed(42)

# Database location
BASE_DIR = Path(__file__).resolve().parent.parent
DB_DIR = BASE_DIR / "database"
DB_DIR.mkdir(exist_ok=True)

DB_PATH = DB_DIR / "business.db"


def create_database():

    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")
    cursor = conn.cursor()

    # Reset existing sample tables so rerunning creates fresh data
    cursor.executescript("""
    DROP TABLE IF EXISTS payments;
    DROP TABLE IF EXISTS order_items;
    DROP TABLE IF EXISTS orders;
    DROP TABLE IF EXISTS employees;
    DROP TABLE IF EXISTS products;
    DROP TABLE IF EXISTS customers;

    CREATE TABLE customers (
        customer_id INTEGER PRIMARY KEY,
        name TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        city TEXT NOT NULL,
        country TEXT NOT NULL,
        registration_date DATE NOT NULL
    );

    CREATE TABLE products (
        product_id INTEGER PRIMARY KEY,
        product_name TEXT NOT NULL,
        category TEXT NOT NULL,
        price REAL NOT NULL CHECK(price >= 0),
        stock INTEGER NOT NULL CHECK(stock >= 0)
    );

    CREATE TABLE employees (
        employee_id INTEGER PRIMARY KEY,
        name TEXT NOT NULL,
        department TEXT NOT NULL,
        salary REAL NOT NULL,
        city TEXT NOT NULL
    );

    CREATE TABLE orders (
        order_id INTEGER PRIMARY KEY,
        customer_id INTEGER NOT NULL,
        employee_id INTEGER NOT NULL,
        order_date DATE NOT NULL,
        status TEXT NOT NULL,
        FOREIGN KEY(customer_id) REFERENCES customers(customer_id),
        FOREIGN KEY(employee_id) REFERENCES employees(employee_id)
    );

    CREATE TABLE order_items (
        item_id INTEGER PRIMARY KEY,
        order_id INTEGER NOT NULL,
        product_id INTEGER NOT NULL,
        quantity INTEGER NOT NULL CHECK(quantity > 0),
        unit_price REAL NOT NULL,
        FOREIGN KEY(order_id) REFERENCES orders(order_id),
        FOREIGN KEY(product_id) REFERENCES products(product_id)
    );

    CREATE TABLE payments (
        payment_id INTEGER PRIMARY KEY,
        order_id INTEGER NOT NULL UNIQUE,
        amount REAL NOT NULL CHECK(amount >= 0),
        payment_method TEXT NOT NULL,
        payment_status TEXT NOT NULL,
        payment_date DATE NOT NULL,
        FOREIGN KEY(order_id) REFERENCES orders(order_id)
    );
    """)

    # 1. Generate customers
    customers = []

    for i in range(1, 101):
        customers.append((
            i,
            fake.name(),
            f"customer{i}@example.com",
            fake.city(),
            fake.country(),
            fake.date_between(
                start_date="-3y",
                end_date="today"
            ).isoformat()
        ))

    cursor.executemany("""
        INSERT INTO customers
        VALUES (?, ?, ?, ?, ?, ?)
    """, customers)

    # 2. Generate products
    categories = [
        "Electronics",
        "Clothing",
        "Furniture",
        "Books",
        "Home Appliances"
    ]

    products = []

    for i in range(1, 31):
        products.append((
            i,
            fake.unique.word().capitalize() + " " +
            random.choice(["Pro", "Plus", "Basic", "Premium"]),
            random.choice(categories),
            round(random.uniform(100, 50000), 2),
            random.randint(10, 500)
        ))

    cursor.executemany("""
        INSERT INTO products
        VALUES (?, ?, ?, ?, ?)
    """, products)

    # 3. Generate employees
    departments = [
        "Sales",
        "Marketing",
        "Finance",
        "IT",
        "Operations"
    ]

    employees = []

    for i in range(1, 21):
        employees.append((
            i,
            fake.name(),
            random.choice(departments),
            random.randint(25000, 100000),
            fake.city()
        ))

    cursor.executemany("""
        INSERT INTO employees
        VALUES (?, ?, ?, ?, ?)
    """, employees)

    # 4. Generate orders and order items
    order_statuses = [
        "Completed",
        "Delivered",
        "Pending",
        "Cancelled"
    ]

    orders = []
    order_items = []
    payments = []

    payment_methods = [
        "UPI",
        "Credit Card",
        "Debit Card",
        "Net Banking"
    ]

    payment_statuses = [
        "Paid",
        "Pending",
        "Failed",
        "Refunded"
    ]

    for order_id in range(1, 501):

        customer_id = random.randint(1, 100)
        employee_id = random.randint(1, 20)

        order_date = fake.date_between(
            start_date="-2y",
            end_date="today"
        )

        order_status = random.choice(order_statuses)

        orders.append((
            order_id,
            customer_id,
            employee_id,
            order_date.isoformat(),
            order_status
        ))

        # Add 1 to 4 products to each order
        selected_products = random.sample(
            range(1, 31),
            random.randint(1, 4)
        )

        total_amount = 0

        for product_id in selected_products:

            product_price = products[product_id - 1][3]
            quantity = random.randint(1, 5)

            line_total = product_price * quantity
            total_amount += line_total

            order_items.append((
                len(order_items) + 1,
                order_id,
                product_id,
                quantity,
                product_price
            ))

        # One payment record per order
        payments.append((
            order_id,
            order_id,
            round(total_amount, 2),
            random.choice(payment_methods),
            random.choice(payment_statuses),
            (order_date + timedelta(
                days=random.randint(0, 5)
            )).isoformat()
        ))

    cursor.executemany("""
        INSERT INTO orders
        VALUES (?, ?, ?, ?, ?)
    """, orders)

    cursor.executemany("""
        INSERT INTO order_items
        VALUES (?, ?, ?, ?, ?)
    """, order_items)

    cursor.executemany("""
        INSERT INTO payments
        VALUES (?, ?, ?, ?, ?, ?)
    """, payments)

    conn.commit()

    # Display database statistics
    print("\nDATABASE CREATED SUCCESSFULLY!")

    tables = [
        "customers",
        "products",
        "employees",
        "orders",
        "order_items",
        "payments"
    ]

    for table in tables:
        count = cursor.execute(
            f"SELECT COUNT(*) FROM {table}"
        ).fetchone()[0]

        print(f"{table}: {count} records")

    conn.close()

    print(f"\nDatabase location: {DB_PATH}")


if __name__ == "__main__":
    create_database()
