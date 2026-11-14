
from backend.text_to_sql import generate_sql
from backend.llm import generate_response
from backend.schema import get_database_schema
from backend.sql_validator import validate_sql
from backend.sql_executor import execute_sql

import json


def run_with_self_correction(user_question, max_attempts=2):

    print("\nGenerating SQL...")

    sql_query = generate_sql(user_question)

    for attempt in range(max_attempts):

        print(f"\nAttempt {attempt + 1}")
        print("Generated SQL:", sql_query)

        # Step 1: Validate SQL before execution
        is_valid, message = validate_sql(sql_query)

        if not is_valid:
            error_message = message
            print("Validation failed:", error_message)

        else:
            # Step 2: Execute validated SQL
            result = execute_sql(sql_query)

            if result["success"]:
                print("SQL executed successfully!")

                return {
                    "success": True,
                    "sql": sql_query,
                    "result": result
                }

            error_message = result["error"]
            print("Execution failed:", error_message)

        # Step 3: Ask Gemini to correct the SQL
        if attempt < max_attempts - 1:

            print("Asking Gemini to correct the SQL...")

            schema = get_database_schema()

            correction_prompt = f"""
You are an expert SQLite SQL developer.

The following SQL query has an error.

USER QUESTION:
{user_question}

DATABASE SCHEMA:
{json.dumps(schema, indent=2)}

INCORRECT SQL:
{sql_query}

ERROR:
{error_message}

Generate a corrected SQLite SELECT query.

Rules:
1. Generate only SELECT queries.
2. Use only existing tables and columns.
3. Use correct JOIN conditions.
4. Do not modify the database.
5. Return only the corrected SQL query.
"""

            sql_query = generate_response(correction_prompt).strip()

    return {
        "success": False,
        "sql": sql_query,
        "error": "Maximum correction attempts reached."
    }


if __name__ == "__main__":

    question = "Show the top 5 products by price"

    print("User Question:", question)

    response = run_with_self_correction(question)

    print("\nFinal Response:")
    print(response)
