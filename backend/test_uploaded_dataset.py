
from backend.text_to_sql import generate_sql
from backend.sql_executor import execute_sql


question = "Show total quantity sold by product"

print("\nUser Question:")
print(question)

print("\nGenerating SQL...")
sql_query = generate_sql(
    question,
    table_name="sample_business_sales"
)

print("\nGenerated SQL:")
print(sql_query)

print("\nExecuting SQL...")
result = execute_sql(sql_query)

print("\n========== RESULTS ==========")

if result["success"]:
    print("Columns:", result["columns"])

    for row in result["rows"]:
        print(row)

    print("\nTotal rows:", result["row_count"])

else:
    print("Execution Error:", result["error"])
