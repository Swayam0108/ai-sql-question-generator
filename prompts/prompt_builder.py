# prompts/prompt_builder.py
# ============================================================
# Prompt Builder — Phase 7
# Builds dynamic AI prompts using schema + user selections.
# The quality of generated questions depends entirely on
# how well this prompt is written.
# ============================================================


# ============================================================
# DIFFICULTY GUIDELINES
# Tells the AI what complexity to use per difficulty level
# ============================================================

DIFFICULTY_GUIDELINES = {
    "Easy": """
- Use simple single-table queries
- Use basic clauses: SELECT, WHERE, ORDER BY, GROUP BY
- Use simple aggregations: COUNT, SUM, AVG, MIN, MAX
- No subqueries, no CTEs, no window functions
- Column aliases are simple and clear
- Maximum 2-3 clauses per query
""",
    "Medium": """
- Use moderate complexity queries
- Can use JOINs, GROUP BY with HAVING, subqueries
- Can use CASE WHEN, basic window functions
- Use COALESCE for null handling
- Can combine 2-3 concepts in one query
- Use meaningful column aliases
""",
    "Hard": """
- Use advanced PostgreSQL features
- Use window functions: ROW_NUMBER, RANK, DENSE_RANK, LAG, LEAD
- Use CTEs (WITH clause), nested subqueries
- Use complex aggregations with FILTER
- Use CAST, type conversions, NUMERIC precision
- Combine multiple advanced concepts in one query
- Queries should reflect real industry use cases
""",
}


# ============================================================
# TOPIC GUIDELINES
# Tells the AI which SQL concepts to focus on per topic
# ============================================================

TOPIC_GUIDELINES = {
    "SELECT": "Focus on SELECT with column selection, aliases, DISTINCT, LIMIT.",
    "WHERE": "Focus on WHERE clause with conditions, BETWEEN, IN, LIKE, IS NULL.",
    "ORDER BY": "Focus on ORDER BY with ASC/DESC, multiple columns, NULLS LAST.",
    "GROUP BY": "Focus on GROUP BY with aggregate functions, multiple grouping columns.",
    "HAVING": "Focus on HAVING clause to filter grouped results.",
    "JOINS": "Focus on INNER JOIN, LEFT JOIN, RIGHT JOIN between related tables.",
    "Subqueries": "Focus on correlated and non-correlated subqueries in SELECT, WHERE, FROM.",
    "CTE": "Focus on WITH clause (Common Table Expressions) for readable complex queries.",
    "Window Functions": "Focus on ROW_NUMBER, RANK, DENSE_RANK, LAG, LEAD, NTILE with OVER() and PARTITION BY.",
    "CASE WHEN": "Focus on CASE WHEN expressions for conditional logic inside queries.",
    "Aggregate Functions": "Focus on COUNT, SUM, AVG, MIN, MAX with GROUP BY and HAVING.",
    "Ranking Functions": "Focus on RANK, DENSE_RANK, ROW_NUMBER, NTILE for ranking rows.",
    "Date Functions": "Focus on NOW(), EXTRACT, DATE_TRUNC, AGE, TO_CHAR for date operations.",
}


# ============================================================
# MAIN FUNCTION: Build the full prompt
# ============================================================

def build_prompt(context):
    """
    Builds a complete prompt string for the AI using the
    context dictionary from Phase 4.

    Args:
        context : dict from build_prompt_context()

    Returns:
        A complete prompt string ready to send to Groq API.
    """

    # Extract values from context
    table_name    = context["table_name"]
    columns       = context["columns"]
    pg_types      = context["pg_types"]
    sample_values = context["sample_values"]
    numeric_stats = context["numeric_stats"]
    schema_text   = context["schema_text"]
    topic         = context["topic"]
    difficulty    = context["difficulty"]
    num_questions = context["num_questions"]

    # Get guidelines for this difficulty and topic
    diff_guide  = DIFFICULTY_GUIDELINES.get(difficulty, "")
    topic_guide = TOPIC_GUIDELINES.get(topic, f"Focus on {topic}.")

    # ── Build column details section ─────────────────────────
    col_details = []
    for col in columns:
        pg_type = pg_types.get(col, "TEXT")
        samples = ", ".join(sample_values.get(col, []))
        line    = f"  - {col} ({pg_type}) — sample values: {samples}"

        # Add numeric stats if available
        if col in numeric_stats:
            stats = numeric_stats[col]
            line += (
                f" | min={stats['min']}, "
                f"max={stats['max']}, avg={stats['avg']}"
            )
        col_details.append(line)

    col_details_text = "\n".join(col_details)

    # ── Build the full prompt ────────────────────────────────
    prompt = f"""You are an expert PostgreSQL instructor creating an industry-level SQL question bank.

DATABASE SCHEMA:
{schema_text}

COLUMN DETAILS:
{col_details_text}

YOUR TASK:
Generate exactly {num_questions} PostgreSQL SQL question(s) for the topic "{topic}" at "{difficulty}" difficulty level.

TOPIC FOCUS:
{topic_guide}

DIFFICULTY REQUIREMENTS:
{diff_guide}

STRICT OUTPUT FORMAT:
For each question, use EXACTLY this format with no deviations:

========================================
Question [NUMBER]:
========================================

QUESTION:
[Write a detailed natural language description of what the query should do.
 Mention specific column names, functions to use, and expected behavior.
 Be specific enough that a student knows exactly what to write.]

EXPECTED OUTPUT COLUMNS:
[comma separated list of output column names exactly as they appear in the SELECT]

POSTGRESQL SOLUTION:
[Write the complete, syntactically correct PostgreSQL query here.
 Use proper formatting with each clause on a new line.
 Use real column names from the schema above.]

DIFFICULTY: {difficulty}
TOPIC: {topic}
========================================

IMPORTANT RULES:
1. Use ONLY the table name: {table_name}
2. Use ONLY these column names: {", ".join(columns)}
3. All queries must be valid PostgreSQL syntax
4. Expected output columns must exactly match the SELECT clause aliases
5. Do not use columns that do not exist in the schema
6. Each question must be different — no repetition
7. Do not add any explanation outside the format above
8. Number questions starting from 1

Generate {num_questions} question(s) now:"""

    return prompt


# ============================================================
# HELPER: Preview the prompt without calling AI
# ============================================================

def preview_prompt(context):
    """
    Returns the prompt that would be sent to the AI.
    Useful for debugging and seeing what the AI receives.
    """
    return build_prompt(context)