
import sqlite3
import re
from pathlib import Path

import pandas as pd


BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "database" / "business.db"

# Create database directory automatically if it doesn't exist
DB_PATH.parent.mkdir(parents=True, exist_ok=True)

# Number of CSV rows processed at a time
CHUNK_SIZE = 10000


def clean_table_name(filename):
    """Convert filename into a safe SQLite table name."""

    name = Path(filename).stem.lower()
    name = re.sub(r"[^a-z0-9_]", "_", name)
    name = re.sub(r"_+", "_", name).strip("_")

    if not name:
        name = "uploaded_dataset"

    if name[0].isdigit():
        name = "dataset_" + name

    return name


def clean_column_names(df):
    """Clean column names and ensure uniqueness."""

    columns = []

    for index, column in enumerate(df.columns):

        clean_name = str(column).strip().lower()
        clean_name = re.sub(r"[^a-z0-9_]", "_", clean_name)
        clean_name = re.sub(r"_+", "_", clean_name).strip("_")

        if not clean_name:
            clean_name = f"column_{index + 1}"

        if clean_name[0].isdigit():
            clean_name = "column_" + clean_name

        columns.append(clean_name)

    unique_columns = []
    seen = {}

    for column in columns:

        count = seen.get(column, 0)
        seen[column] = count + 1

        if count:
            column = f"{column}_{count + 1}"

        unique_columns.append(column)

    df.columns = unique_columns

    return df


def load_dataset(file_path, filename):
    """Read CSV or XLSX and store it as a SQLite table."""

    extension = Path(filename).suffix.lower()
    table_name = clean_table_name(filename)

    # ======================================
    # CSV CHUNK PROCESSING
    # ======================================

    if extension == ".csv":

        total_rows = 0
        columns = None

        with sqlite3.connect(DB_PATH) as connection:

            # Remove previous table with the same name
            connection.execute(
                f'DROP TABLE IF EXISTS "{table_name}"'
            )

            for chunk in pd.read_csv(
                file_path,
                chunksize=CHUNK_SIZE
            ):

                if chunk.empty:
                    continue

                chunk = clean_column_names(chunk)

                if columns is None:

                    columns = list(chunk.columns)

                    chunk.to_sql(
                        table_name,
                        connection,
                        if_exists="replace",
                        index=False
                    )

                else:

                    if list(chunk.columns) != columns:
                        raise ValueError(
                            "CSV column names changed during processing."
                        )

                    chunk.to_sql(
                        table_name,
                        connection,
                        if_exists="append",
                        index=False
                    )

                total_rows += len(chunk)

            if total_rows == 0:
                raise ValueError(
                    "The uploaded dataset is empty."
                )

    # ======================================
    # EXCEL PROCESSING
    # ======================================

    elif extension == ".xlsx":

        df = pd.read_excel(
            file_path,
            engine="openpyxl"
        )

        if df.empty:
            raise ValueError("The uploaded dataset is empty.")

        df = clean_column_names(df)

        with sqlite3.connect(DB_PATH) as connection:

            df.to_sql(
                table_name,
                connection,
                if_exists="replace",
                index=False
            )

        total_rows = len(df)
        columns = list(df.columns)

    else:

        raise ValueError(
            "Only CSV and XLSX files are supported."
        )

    if not columns:
        raise ValueError("The dataset has no columns.")

    return {
        "success": True,
        "table_name": table_name,
        "rows": total_rows,
        "columns": columns
    }


if __name__ == "__main__":
    print("Dataset manager is ready.")
