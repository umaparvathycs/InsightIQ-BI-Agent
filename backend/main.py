
from fastapi import FastAPI, HTTPException, UploadFile, File
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path
from typing import Any
import tempfile

from backend.agent_graph import run_agent
from backend.dataset_manager import load_dataset
from backend.insights_generator import generate_business_insights


# Create FastAPI application
app = FastAPI(
    title="Text-to-SQL BI Agent",
    description="Generative AI-powered Business Intelligence Agent",
    version="1.0.0"
)


# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://127.0.0.1:5500",
        "http://localhost:5500"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request models
class QuestionRequest(BaseModel):
    question: str
    table_name: str = None


class InsightRequest(BaseModel):
    question: str
    columns: list[str]
    rows: list[list[Any]]


# Home endpoint
@app.get("/")
def home():
    return {
        "message": "Welcome to the Text-to-SQL BI Agent API",
        "status": "running"
    }


# Ask endpoint
@app.post("/ask")
def ask_question(request: QuestionRequest):

    try:
        response = run_agent(
            request.question,
            table_name=request.table_name
        )

        if not response.get("success"):
            raise HTTPException(
                status_code=400,
                detail=response.get("error", "Query failed")
            )

        result = response["result"]

        return {
            "success": True,
            "question": request.question,
            "sql_query": response["sql_query"],
            "columns": result["columns"],
            "rows": [
                list(row) for row in result["rows"]
            ],
            "row_count": result["row_count"]
        }

    except HTTPException:
        raise

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=str(error)
        )


# AI Business Insights endpoint
@app.post("/generate-insights")
def generate_insights(request: InsightRequest):

    result = generate_business_insights(
        request.question,
        request.columns,
        request.rows
    )

    return result


# Dataset upload endpoint
@app.post("/upload-dataset")
async def upload_dataset(file: UploadFile = File(...)):

    filename = file.filename or ""
    extension = Path(filename).suffix.lower()

    if extension not in [".csv", ".xlsx"]:
        raise HTTPException(
            status_code=400,
            detail="Only CSV and XLSX files are supported."
        )

    content = await file.read()

    if not content:
        raise HTTPException(
            status_code=400,
            detail="Uploaded file is empty."
        )

    if len(content) > 50 * 1024 * 1024:
        raise HTTPException(
            status_code=400,
            detail="File size must not exceed 50 MB."
        )

    temp_path = None

    try:
        with tempfile.NamedTemporaryFile(
            suffix=extension,
            delete=False
        ) as temp_file:
            temp_file.write(content)
            temp_path = Path(temp_file.name)

        result = load_dataset(temp_path, filename)
        return result

    except Exception as error:
        raise HTTPException(
            status_code=400,
            detail=str(error)
        )

    finally:
        if temp_path and temp_path.exists():
            temp_path.unlink()

        await file.close()
