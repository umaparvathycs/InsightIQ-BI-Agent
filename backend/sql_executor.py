
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


def execute_sql(sql_query):

    try:
        with engine.connect() as connection:

            # Start a read-only transaction
            connection.execute(
                text("SET TRANSACTION READ ONLY")
            )

            # Execute the generated SQL query
            result = connection.execute(
                text(sql_query)
            )

            # Fetch maximum 100 rows
            rows = result.fetchmany(100)

            # Get column names
            columns = list(result.keys())

            return {
                "success": True,
                "columns": columns,
                "rows": [tuple(row) for row in rows],
                "row_count": len(rows)
            }

    except Exception as error:

        return {
            "success": False,
            "error": str(error)
        }


if __name__ == "__main__":

    query = "SELECT * FROM products LIMIT 5"

    print("Executing SQL query...\n")

    result = execute_sql(query)

    print(result)
