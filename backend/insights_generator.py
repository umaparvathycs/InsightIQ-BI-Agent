
from backend.llm import generate_response
import json


def generate_business_insights(question, columns, rows):

    if not rows:
        return {
            "success": True,
            "insights": {
                "key_finding": "No records were found.",
                "business_insight": "There is no result data available to analyze.",
                "recommendation": "Try modifying your question or checking your dataset."
            }
        }

    data = {
        "columns": columns,
        "rows": rows[:50]
    }

    prompt = f"""
You are an expert Business Intelligence analyst.

Analyze the following SQL query results.

USER QUESTION:
{question}

QUERY RESULTS:
{json.dumps(data, default=str)}

Provide:
1. One important key finding.
2. One meaningful business insight.
3. One practical business recommendation.

Rules:
- Use only the information in the query results.
- Do not invent numbers or facts.
- Keep the language simple and professional.
- Return valid JSON only.
- Do not include Markdown.

Use exactly this JSON structure:
{{
    "key_finding": "Your finding",
    "business_insight": "Your insight",
    "recommendation": "Your recommendation"
}}
"""

    try:

        response = generate_response(prompt)

        cleaned_response = response.strip()

        if cleaned_response.startswith("```"):
            cleaned_response = cleaned_response.replace("```json", "")
            cleaned_response = cleaned_response.replace("```", "")

        insights = json.loads(cleaned_response.strip())

        required_keys = [
            "key_finding",
            "business_insight",
            "recommendation"
        ]

        if not all(key in insights for key in required_keys):
            raise ValueError("Gemini returned an incomplete insight response.")

        return {
            "success": True,
            "insights": insights
        }

    except Exception as error:

        print("Insight generation error:", error)

        return {
            "success": False,
            "error": "Unable to generate business insights."
        }
