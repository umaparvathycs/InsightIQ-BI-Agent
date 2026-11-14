
import os
import re
from pathlib import Path

import pandas as pd
from sqlalchemy import create_engine, text
from dotenv import load_dotenv


# Load environment variables
BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise ValueError(
        "DATABASE_URL environment variable is not configured."
    )


# PostgreSQL connection using SQLAlchemy
DATABASE_URL = DATABASE_URL.replace(
    "postgresql://",
    "postgresql+psycopg2://",
    1
)

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True
)

CHUNK_SIZE = 10000


def clean_table_name(filename):
    """Convert filename into a safe PostgreSQL table name."""

    name = Path(filename).stem.lower()

    name = re.sub(r"[^a-z0-9_]", "_", name)
    name = re.sub(r"_+", "_", name).strip("_")

    if not name:
        name = "uploaded_dataset"

    if name[0].isdigit():
        name = "dataset_" + name

    return name[:63]


def clean_column_names(df):
    """Clean column names and ensure uniqueness."""

    columns = []

    for index, column in enumerate(df.columns):

        clean_name = str(column).strip().lower()

        clean_name = re.sub(
            r"[^a-z0-9_]",
            "_",
            clean_name
        )

        clean_name = re.sub(
            r"_+",
            "_",
            clean_name
        ).strip("_")

        if not clean_name:
            clean_name = f"column_{index + 1}"

        if clean_name[0].isdigit():
            clean_name = "column_" + clean_name

        columns.append(clean_name[:63])

    unique_columns = []
    seen = {}

    for column in columns:

        count = seen.get(column, 0)
        seen[column] = count + 1

        if count:
            suffix = f"_{count + 1}"
            column = column[:63 - len(suffix)] + suffix

        unique_columns.append(column)

    df.columns = unique_columns

    return df


def load_dataset(file_path, filename):
    """Read CSV or XLSX and store it as a PostgreSQL table."""

    extension = Path(filename).suffix.lower()
    table_name = clean_table_name(filename)

    total_rows = 0
    columns = None

    # CSV upload
    if extension == ".csv":

        for chunk in pd.read_csv(
            file_path,
            chunksize=CHUNK_SIZE
        ):

            if chunk.empty:
                continue

            chunk = clean_column_names(chunk)

            if columns is None:

                columns = list(chunk.columns)

                # Remove an existing table before uploading
                with engine.begin() as connection:
                    connection.execute(
                        text(
                            f'DROP TABLE IF EXISTS "{table_name}"'
                        )
                    )

            elif list(chunk.columns) != columns:

                raise ValueError(
                    "CSV column names changed during processing."
                )

            # Insert data into PostgreSQL
            chunk.to_sql(
                table_name,
                engine,
                if_exists="replace" if total_rows == 0 else "append",
                index=False,
                chunksize=500,
                method="multi"
            )

            total_rows += len(chunk)

        if total_rows == 0:
            raise ValueError(
                "The uploaded dataset is empty."
            )

    # Excel upload
    elif extension == ".xlsx":

        df = pd.read_excel(
            file_path,
            engine="openpyxl"
        )

        if df.empty:
            raise ValueError(
                "The uploaded dataset is empty."
            )

        df = clean_column_names(df)

        columns = list(df.columns)

        df.to_sql(
            table_name,
            engine,
            if_exists="replace",
            index=False,
            chunksize=500,
            method="multi"
        )

        total_rows = len(df)

    else:

        raise ValueError(
            "Only CSV and XLSX files are supported."
        )

    if not columns:
        raise ValueError(
            "The dataset has no columns."
        )

    return {
        "success": True,
        "table_name": table_name,
        "rows": total_rows,
        "columns": columns
    }


if __name__ == "__main__":

    print("PostgreSQL dataset manager is ready.")
