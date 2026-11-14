
import sqlite3
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "database" / "business.db"


def execute_sql(sql_query):

    try:
        # Open database in read-only mode
        connection = sqlite3.connect(
            f"file:{DB_PATH.as_posix()}?mode=ro",
            uri=True
        )

        # Enable read-only query mode
        connection.execute("PRAGMA query_only = ON")

        # Execute SQL query
        cursor = connection.execute(sql_query)

        # Fetch results
        rows = cursor.fetchmany(100)

        # Get column names
        columns = [
            description[0]
            for description in cursor.description
        ]

        connection.close()

        return {
            "success": True,
            "columns": columns,
            "rows": rows,
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
