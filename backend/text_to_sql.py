
import json

from backend.llm import generate_response
from backend.schema import get_database_schema


def generate_sql(user_question, table_name=None):

    schema = get_database_schema()

    # If a table is specified, use only that table's schema
    if table_name:
        if table_name not in schema:
            raise ValueError(f"Table '{table_name}' does not exist.")

        schema = {table_name: schema[table_name]}

    schema_text = json.dumps(schema, indent=2)

    prompt = f"""
You are an expert Text-to-SQL assistant.

Convert the user's natural language question
into a valid SQLite SQL query.

DATABASE SCHEMA:
{schema_text}

RULES:
1. Generate only SQLite-compatible SQL.
2. Generate only SELECT queries.
3. Never modify database data or structure.
4. Use only tables and columns in the provided schema.
5. Generate correct SQL based on the user's question.
6. Return only the SQL query.
7. Do not include Markdown or explanations.

USER QUESTION:
{user_question}

SQL QUERY:
"""

    sql_query = generate_response(prompt)

    return sql_query.strip()


if __name__ == "__main__":

    question = "Show total quantity sold by product"

    sql = generate_sql(
        question,
        table_name="sample_business_sales"
    )

    print("\nUser Question:")
    print(question)

    print("\nGenerated SQL:")
    print(sql)
