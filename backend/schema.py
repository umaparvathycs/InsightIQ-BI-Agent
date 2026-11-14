
import sqlite3
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "database" / "business.db"


def get_database_schema():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    schema = {}

    cursor.execute("""
        SELECT name
        FROM sqlite_master
        WHERE type = 'table'
        AND name NOT LIKE 'sqlite_%'
    """)

    tables = cursor.fetchall()

    for (table_name,) in tables:
        cursor.execute(f'PRAGMA table_info("{table_name}")')
        columns = cursor.fetchall()

        cursor.execute(f'PRAGMA foreign_key_list("{table_name}")')
        foreign_keys = cursor.fetchall()

        schema[table_name] = {
            "columns": [
                {
                    "name": column[1],
                    "type": column[2],
                    "primary_key": bool(column[5])
                }
                for column in columns
            ],
            "foreign_keys": [
                {
                    "column": fk[3],
                    "references_table": fk[2],
                    "references_column": fk[4]
                }
                for fk in foreign_keys
            ]
        }

    conn.close()
    return schema


if __name__ == "__main__":
    database_schema = get_database_schema()

    for table, details in database_schema.items():
        print(f"\nTable: {table}")
        print("Columns:")

        for column in details["columns"]:
            print(f"  - {column['name']} ({column['type']})")

        print("Foreign Keys:")

        for fk in details["foreign_keys"]:
            print(f"  - {fk}")
