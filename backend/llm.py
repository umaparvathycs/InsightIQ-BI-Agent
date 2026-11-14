
import os
import time
from pathlib import Path

from dotenv import load_dotenv
from google import genai
from google.genai import errors, types

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

API_KEY = os.getenv("GEMINI_API_KEY")

MODEL_NAME = "gemini-3.5-flash-lite"


def generate_response(prompt):

    if not API_KEY:
        raise ValueError("GEMINI_API_KEY not found. Check your .env file.")

    client = genai.Client(
        api_key=API_KEY,
        http_options=types.HttpOptions(timeout=20000)
    )

    for attempt in range(3):
        try:
            print("Connecting to Gemini...")

            response = client.models.generate_content(
                model=MODEL_NAME,
                contents=prompt
            )

            return response.text

        except (errors.ServerError, errors.ClientError) as error:

            print(f"Gemini API error: {error}")

            if attempt < 2:
                wait_time = 5 * (attempt + 1)
                print(f"Retrying in {wait_time} seconds...")
                time.sleep(wait_time)
            else:
                raise RuntimeError(
                    "Gemini is currently unavailable. Try again later."
                ) from error


if __name__ == "__main__":

    question = "What is Generative AI? Explain in two sentences."

    print("Testing Gemini API...\n")

    answer = generate_response(question)

    print("\nGemini Response:")
    print(answer)
