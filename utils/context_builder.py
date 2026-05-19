# utils/context_builder.py
# ============================================================
# Context Builder — Phase 4
# Takes the extracted schema + user selections and builds
# a structured context dictionary ready for the AI prompt.
# ============================================================


# ============================================================
# MAIN FUNCTION: Build prompt context
# ============================================================

def build_prompt_context(schema, topic, difficulty, num_questions):
    """
    Combines schema information with user selections into one
    clean context dictionary.

    Args:
        schema        : dict returned by extract_schema()
        topic         : string e.g. "Window Functions"
        difficulty    : string e.g. "Hard"
        num_questions : int e.g. 3

    Returns:
        A context dict ready to be passed to the prompt builder.
    """

    # Validate schema is not empty or errored
    if not schema or "error" in schema:
        return {"error": "No valid schema found. Please upload a dataset first."}

    # Build the context dictionary
    context = {
        # ── Dataset info ─────────────────────────────────────
        "table_name"    : schema.get("table_name", "my_table"),
        "file_name"     : schema.get("file_name", ""),
        "total_rows"    : schema.get("total_rows", 0),
        "total_columns" : schema.get("total_columns", 0),

        # ── Column info ──────────────────────────────────────
        "columns"       : schema.get("columns", []),
        "pg_types"      : schema.get("pg_types", {}),
        "nullable_cols" : schema.get("nullable_cols", []),
        "sample_values" : schema.get("sample_values", {}),
        "numeric_stats" : schema.get("numeric_stats", {}),

        # ── PostgreSQL CREATE TABLE statement ────────────────
        "schema_text"   : schema.get("schema_text", ""),

        # ── User selections ──────────────────────────────────
        "topic"         : topic,
        "difficulty"    : difficulty,
        "num_questions" : int(num_questions),

        # ── Derived helpers for prompt building ─────────────
        # List of only numeric column names
        "numeric_columns": list(schema.get("numeric_stats", {}).keys()),

        # List of only text column names
        "text_columns": [
            col for col, dtype in schema.get("pg_types", {}).items()
            if dtype in ["TEXT", "VARCHAR(255)"]
        ],

        # Column names as a comma-separated string
        "columns_csv": ", ".join(schema.get("columns", [])),
    }

    return context


# ============================================================
# HELPER: Format context as readable text for UI display
# ============================================================

def format_context_for_display(context):
    """
    Formats the prompt context as readable text.
    Shows user exactly what information will be sent to the AI.

    Args:
        context : dict from build_prompt_context()

    Returns:
        A formatted string for display in the Gradio output box.
    """

    if "error" in context:
        return f"Error: {context['error']}"

    lines = []

    lines.append("=" * 50)
    lines.append("  PROMPT CONTEXT — ready for AI generation")
    lines.append("=" * 50)
    lines.append("")

    # Dataset summary
    lines.append("DATASET INFO:")
    lines.append(f"  Table name     : {context['table_name']}")
    lines.append(f"  File           : {context['file_name']}")
    lines.append(f"  Rows           : {context['total_rows']}")
    lines.append(f"  Columns        : {context['total_columns']}")
    lines.append("")

    # User selections
    lines.append("QUESTION SETTINGS:")
    lines.append(f"  Topic          : {context['topic']}")
    lines.append(f"  Difficulty     : {context['difficulty']}")
    lines.append(f"  Num questions  : {context['num_questions']}")
    lines.append("")

    # Column details
    lines.append("COLUMNS DETECTED:")
    for col in context["columns"]:
        pg_type = context["pg_types"].get(col, "TEXT")
        samples = ", ".join(context["sample_values"].get(col, []))
        lines.append(f"  {col} ({pg_type}) — samples: {samples}")

        # Add numeric stats if available
        if col in context["numeric_stats"]:
            stats = context["numeric_stats"][col]
            lines.append(
                f"    stats: min={stats['min']}, "
                f"max={stats['max']}, avg={stats['avg']}"
            )
    lines.append("")

    # Numeric and text column groups
    lines.append(f"NUMERIC COLUMNS : {', '.join(context['numeric_columns'])}")
    lines.append(f"TEXT COLUMNS    : {', '.join(context['text_columns'])}")
    lines.append("")

    # Schema text
    lines.append("POSTGRESQL SCHEMA:")
    lines.append(context["schema_text"])
    lines.append("")

    lines.append("=" * 50)
    lines.append("  AI will generate questions using this context")
    lines.append("=" * 50)

    return "\n".join(lines)