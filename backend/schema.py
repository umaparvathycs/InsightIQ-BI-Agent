
import os
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import create_engine, text


BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise ValueError("DATABASE_URL environment variable is not configured.")

DATABASE_URL = DATABASE_URL.replace(
    "postgresql://",
    "postgresql+psycopg2://",
    1
)

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True
)


def get_database_schema():
    schema = {}

    with engine.connect() as conn:

        # Get all user-created tables
        tables = conn.execute(text("""
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = current_schema()
            AND table_type = 'BASE TABLE'
            ORDER BY table_name
        """)).fetchall()

        for (table_name,) in tables:

            # Get columns and primary key information
            columns = conn.execute(text("""
                SELECT
                    c.column_name,
                    c.data_type,
                    CASE
                        WHEN pk.column_name IS NOT NULL THEN TRUE
                        ELSE FALSE
                    END AS is_primary_key
                FROM information_schema.columns c
                LEFT JOIN (
                    SELECT
                        kcu.table_name,
                        kcu.column_name
                    FROM information_schema.table_constraints tc
                    JOIN information_schema.key_column_usage kcu
                        ON tc.constraint_name = kcu.constraint_name
                        AND tc.table_schema = kcu.table_schema
                        AND tc.table_name = kcu.table_name
                    WHERE tc.constraint_type = 'PRIMARY KEY'
                    AND tc.table_schema = current_schema()
                ) pk
                    ON c.table_name = pk.table_name
                    AND c.column_name = pk.column_name
                WHERE c.table_schema = current_schema()
                AND c.table_name = :table_name
                ORDER BY c.ordinal_position
            """), {"table_name": table_name}).fetchall()

            # Get foreign key information
            foreign_keys = conn.execute(text("""
                SELECT
                    kcu.column_name,
                    ccu.table_name AS references_table,
                    ccu.column_name AS references_column
                FROM information_schema.table_constraints tc
                JOIN information_schema.key_column_usage kcu
                    ON tc.constraint_name = kcu.constraint_name
                    AND tc.table_schema = kcu.table_schema
                JOIN information_schema.constraint_column_usage ccu
                    ON tc.constraint_name = ccu.constraint_name
                    AND tc.table_schema = ccu.constraint_schema
                WHERE tc.constraint_type = 'FOREIGN KEY'
                AND tc.table_schema = current_schema()
                AND tc.table_name = :table_name
            """), {"table_name": table_name}).fetchall()

            schema[table_name] = {
                "columns": [
                    {
                        "name": column[0],
                        "type": column[1],
                        "primary_key": bool(column[2])
                    }
                    for column in columns
                ],
                "foreign_keys": [
                    {
                        "column": fk[0],
                        "references_table": fk[1],
                        "references_column": fk[2]
                    }
                    for fk in foreign_keys
                ]
            }

    return schema


if __name__ == "__main__":

    database_schema = get_database_schema()

    for table, details in database_schema.items():

        print(f"\nTable: {table}")
        print("Columns:")

        for column in details["columns"]:
            print(
                f"  - {column['name']} ({column['type']})"
            )

        print("Foreign Keys:")

        for fk in details["foreign_keys"]:
            print(f"  - {fk}")
