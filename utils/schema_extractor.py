# utils/schema_extractor.py
# ============================================================
# Schema Extractor — Phase 3
# Analyzes any uploaded CSV or Excel file and returns a
# detailed schema dictionary used by the AI prompt builder.
# ============================================================

import pandas as pd
import os


# ============================================================
# HELPER: Map pandas dtype to PostgreSQL data type
# ============================================================

def map_to_postgres_type(dtype, column_name, sample_values):
    """
    Converts a pandas dtype into the closest PostgreSQL type.

    Args:
        dtype       : pandas dtype object (e.g. int64, float64, object)
        column_name : column name string (used for date detection)
        sample_values: list of sample values from that column

    Returns:
        A PostgreSQL type string like 'INTEGER', 'NUMERIC', 'TEXT', etc.
    """

    dtype_str = str(dtype)

    # Integer types
    if dtype_str in ["int64", "int32", "int16", "int8"]:
        return "INTEGER"

    # Float / decimal types
    if dtype_str in ["float64", "float32"]:
        return "NUMERIC"

    # Boolean
    if dtype_str == "bool":
        return "BOOLEAN"

    # Datetime (pandas already parsed it)
    if "datetime" in dtype_str:
        return "TIMESTAMP"

    # Object dtype — could be TEXT, DATE, or VARCHAR
    # Try to detect dates by column name or sample values
    if dtype_str == "object":
        date_keywords = ["date", "time", "created", "updated", "dob", "birth"]
        col_lower = column_name.lower()

        # Check if column name suggests a date
        if any(kw in col_lower for kw in date_keywords):
            return "DATE"

        # Check sample values — try parsing as date
        for val in sample_values[:5]:
            try:
                pd.to_datetime(str(val))
                return "DATE"
            except Exception:
                break

        # Default for text columns
        return "VARCHAR(255)"

    # Fallback
    return "TEXT"


# ============================================================
# MAIN FUNCTION: Extract full schema from a file
# ============================================================

def extract_schema(file_path):
    """
    Reads a CSV or Excel file and returns a detailed schema dict.

    Args:
        file_path : full path to the uploaded file

    Returns:
        A dictionary with all schema information, or an error dict.

    Schema dict structure:
    {
        "table_name"    : "products",
        "file_name"     : "products.csv",
        "total_rows"    : 500,
        "total_columns" : 5,
        "columns"       : ["brand", "product", "rating", ...],
        "pg_types"      : {"brand": "VARCHAR(255)", ...},
        "nullable_cols" : ["rating"],
        "sample_values" : {"brand": ["Nike", "Adidas"], ...},
        "numeric_stats" : {"rating": {"min": 1.0, "max": 5.0, "avg": 4.2}},
        "schema_text"   : "CREATE TABLE products (...)"
    }
    """

    # ── Step 1: Read the file ────────────────────────────────
    try:
        if file_path.endswith(".csv"):
            df = pd.read_csv(file_path)
        elif file_path.endswith(".xlsx") or file_path.endswith(".xls"):
            df = pd.read_excel(file_path)
        else:
            return {"error": "Unsupported file type. Use CSV or Excel."}
    except Exception as e:
        return {"error": f"Could not read file: {str(e)}"}

    # ── Step 2: Get table name from filename ─────────────────
    # e.g. "products.csv" → "products"
    file_name = os.path.basename(file_path)
    table_name = os.path.splitext(file_name)[0]

    # Clean table name — remove spaces and special chars
    table_name = table_name.lower().replace(" ", "_").replace("-", "_")

    # ── Step 3: Basic shape ──────────────────────────────────
    total_rows, total_columns = df.shape
    columns = list(df.columns)

    # ── Step 4: Detect PostgreSQL types ─────────────────────
    pg_types = {}
    for col in columns:
        # Get up to 10 sample values (non-null)
        samples = df[col].dropna().head(10).tolist()
        pg_types[col] = map_to_postgres_type(df[col].dtype, col, samples)

    # ── Step 5: Detect nullable columns ─────────────────────
    # A column is nullable if it has ANY missing values
    nullable_cols = [
        col for col in columns if df[col].isnull().any()
    ]

    # ── Step 6: Get sample values per column ────────────────
    # First 5 unique non-null values for each column
    sample_values = {}
    for col in columns:
        unique_vals = df[col].dropna().unique()[:5].tolist()
        # Convert to strings for safe JSON/text handling
        sample_values[col] = [str(v) for v in unique_vals]

    # ── Step 7: Numeric statistics ───────────────────────────
    # For numeric columns: min, max, average
    numeric_stats = {}
    numeric_cols = df.select_dtypes(include=["number"]).columns.tolist()

    for col in numeric_cols:
        numeric_stats[col] = {
            "min": round(float(df[col].min()), 4),
            "max": round(float(df[col].max()), 4),
            "avg": round(float(df[col].mean()), 4),
        }

    # ── Step 8: Build CREATE TABLE statement ────────────────
    # This is what gets sent to the AI as context
    col_definitions = []
    for col in columns:
        pg_type = pg_types[col]
        nullable = "" if col in nullable_cols else " NOT NULL"
        col_definitions.append(f"    {col} {pg_type}{nullable}")

    schema_text = (
        f"CREATE TABLE {table_name} (\n"
        + ",\n".join(col_definitions)
        + "\n);"
    )

    # ── Step 9: Return everything as a dict ─────────────────
    return {
        "table_name"    : table_name,
        "file_name"     : file_name,
        "total_rows"    : total_rows,
        "total_columns" : total_columns,
        "columns"       : columns,
        "pg_types"      : pg_types,
        "nullable_cols" : nullable_cols,
        "sample_values" : sample_values,
        "numeric_stats" : numeric_stats,
        "schema_text"   : schema_text,
    }


# ============================================================
# HELPER: Format schema as readable text for display in UI
# ============================================================

def format_schema_for_display(schema):
    """
    Takes the schema dict and returns a clean readable string
    for showing in the Gradio UI status box.
    """

    if "error" in schema:
        return f"Error: {schema['error']}"

    lines = []
    lines.append(f"Table name   : {schema['table_name']}")
    lines.append(f"Total rows   : {schema['total_rows']}")
    lines.append(f"Total columns: {schema['total_columns']}")
    lines.append("")
    lines.append("Column details:")
    lines.append("-" * 40)

    for col in schema["columns"]:
        pg_type  = schema["pg_types"][col]
        nullable = "nullable" if col in schema["nullable_cols"] else "not null"
        samples  = ", ".join(schema["sample_values"].get(col, []))

        lines.append(f"  {col}")
        lines.append(f"    Type    : {pg_type}")
        lines.append(f"    Nullable: {nullable}")
        lines.append(f"    Samples : {samples}")

        # Add stats for numeric columns
        if col in schema["numeric_stats"]:
            stats = schema["numeric_stats"][col]
            lines.append(
                f"    Stats   : min={stats['min']}, "
                f"max={stats['max']}, avg={stats['avg']}"
            )
        lines.append("")

    lines.append("PostgreSQL CREATE TABLE:")
    lines.append("-" * 40)
    lines.append(schema["schema_text"])

    return "\n".join(lines)