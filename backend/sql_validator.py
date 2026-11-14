
import sqlglot
from sqlglot import exp


def validate_sql(sql_query):

    try:
        # Reject empty queries
        if not sql_query or not sql_query.strip():
            return False, "SQL query cannot be empty."

        # Parse using PostgreSQL dialect
        parsed_queries = sqlglot.parse(
            sql_query,
            read="postgres"
        )

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
        "SELECT product, SUM(sales) FROM neon_test GROUP BY product;",
        "DROP TABLE products;",
        "DELETE FROM products;",
        "UPDATE products SET price = 100;",
        "INSERT INTO products VALUES (1, 'Laptop');"
    ]

    for query in test_queries:

        is_valid, message = validate_sql(query)

        print("\nQuery:", query)
        print("Valid:", is_valid)
        print("Message:", message)
