
import sqlglot
from sqlglot import exp


def validate_sql(sql_query):

    try:
        # Parse the SQL query
        parsed_queries = sqlglot.parse(sql_query, read="sqlite")

        # Reject empty or multiple SQL statements
        if len(parsed_queries) != 1 or parsed_queries[0] is None:
            return False, "Only one SQL statement is allowed."

        parsed = parsed_queries[0]

        # Allow only SELECT queries
        if not isinstance(parsed, exp.Select):
            return False, "Only SELECT queries are allowed."

        return True, "SQL query is safe."

    except Exception as error:
        return False, f"Invalid SQL query: {error}"


if __name__ == "__main__":

    test_queries = [
        "SELECT * FROM products;",
        "DROP TABLE products;",
        "DELETE FROM products;",
        "UPDATE products SET price = 100;"
    ]

    for query in test_queries:

        is_valid, message = validate_sql(query)

        print("\nQuery:", query)
        print("Valid:", is_valid)
        print("Message:", message)
