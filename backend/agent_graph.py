
from typing import TypedDict, Any, Optional
import json

from langgraph.graph import StateGraph, START, END

from backend.text_to_sql import generate_sql
from backend.llm import generate_response
from backend.schema import get_database_schema
from backend.sql_validator import validate_sql
from backend.sql_executor import execute_sql


# 1. Define the agent's state
class AgentState(TypedDict, total=False):

    user_question: str
    table_name: Optional[str]
    sql_query: str
    is_valid: bool
    error: str
    result: dict[str, Any]
    success: bool
    attempts: int
    max_attempts: int


# 2. Generate SQL using Gemini
def generate_sql_node(state: AgentState):

    print("\nGenerating SQL using Gemini...")

    sql_query = generate_sql(
        state["user_question"],
        table_name=state.get("table_name")
    )

    return {
        "sql_query": sql_query,
        "attempts": 0,
        "success": False,
        "error": ""
    }


# 3. Validate generated SQL
def validate_sql_node(state: AgentState):

    print("\nValidating SQL...")

    is_valid, message = validate_sql(state["sql_query"])

    print(message)

    return {
        "is_valid": is_valid,
        "error": "" if is_valid else message
    }


# 4. Execute validated SQL
def execute_sql_node(state: AgentState):

    print("\nExecuting SQL...")

    result = execute_sql(state["sql_query"])

    if result["success"]:

        print("SQL executed successfully!")

        return {
            "result": result,
            "success": True,
            "error": ""
        }

    print("Execution error:", result["error"])

    return {
        "result": result,
        "success": False,
        "error": result["error"]
    }


# 5. Correct SQL when an error occurs
def correction_node(state: AgentState):

    print("\nGemini is correcting the SQL...")

    schema = get_database_schema()

    table_name = state.get("table_name")

    if table_name:
        if table_name not in schema:
            raise ValueError(f"Table '{table_name}' does not exist.")

        schema = {table_name: schema[table_name]}

    prompt = f"""
You are an expert PostgreSQL SQL developer.

USER QUESTION:
{state['user_question']}

DATABASE SCHEMA:
{json.dumps(schema, indent=2)}

INCORRECT SQL:
{state['sql_query']}

ERROR:
{state['error']}

Rules:
1. Generate only PostgreSQL SELECT queries.
2. Use only tables and columns in the provided schema.
3. Use correct JOIN conditions when needed.
4. Do not modify the database.
5. Return only SQL without Markdown or explanations.

CORRECTED SQL:
"""

    corrected_sql = generate_response(prompt).strip()

    print("Corrected SQL:", corrected_sql)

    return {
        "sql_query": corrected_sql,
        "attempts": state["attempts"] + 1,
        "success": False
    }


# 6. Decide what happens after validation
def route_after_validation(state: AgentState):

    if state["is_valid"]:
        return "execute"

    if state["attempts"] < state["max_attempts"]:
        return "correct"

    return "end"


# 7. Decide what happens after execution
def route_after_execution(state: AgentState):

    if state["success"]:
        return "end"

    if state["attempts"] < state["max_attempts"]:
        return "correct"

    return "end"


# 8. Build the LangGraph workflow
workflow = StateGraph(AgentState)

workflow.add_node("generate_sql", generate_sql_node)
workflow.add_node("validate_sql", validate_sql_node)
workflow.add_node("execute_sql", execute_sql_node)
workflow.add_node("correct_sql", correction_node)

workflow.add_edge(START, "generate_sql")

workflow.add_edge("generate_sql", "validate_sql")

workflow.add_conditional_edges(
    "validate_sql",
    route_after_validation,
    {
        "execute": "execute_sql",
        "correct": "correct_sql",
        "end": END
    }
)

workflow.add_conditional_edges(
    "execute_sql",
    route_after_execution,
    {
        "correct": "correct_sql",
        "end": END
    }
)

workflow.add_edge("correct_sql", "validate_sql")


# 9. Compile the agent
agent = workflow.compile()


# 10. Run the agent
def run_agent(user_question, table_name=None):

    initial_state = {
        "user_question": user_question,
        "table_name": table_name,
        "attempts": 0,
        "max_attempts": 2,
        "success": False,
        "error": ""
    }

    return agent.invoke(initial_state)


# 11. Test the agent
if __name__ == "__main__":

    question = "Show the top 5 products by price"

    print("User Question:", question)

    response = run_agent(question)

    print("\n========== FINAL AGENT RESPONSE ==========")

    print("Success:", response.get("success"))
    print("SQL:", response.get("sql_query"))

    if response.get("success"):
        print("Results:")
        print(response.get("result"))
    else:
        print("Error:", response.get("error"))
