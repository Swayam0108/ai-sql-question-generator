# generators/formatter.py
# ============================================================
# Formatting Engine — Phase 9
# Parses AI response into structured question objects
# and formats them for display and export.
# ============================================================

import re


# ============================================================
# DATA STRUCTURE: One SQL question
# ============================================================

class SQLQuestion:
    """
    Represents one generated SQL question with all its parts.
    """
    def __init__(self):
        self.number          = 0
        self.question_text   = ""
        self.expected_output = ""
        self.solution_query  = ""
        self.difficulty      = ""
        self.topic           = ""

    def is_valid(self):
        """Returns True if the question has all required parts."""
        return (
            self.question_text.strip() != "" and
            self.solution_query.strip() != ""
        )

    def to_display_text(self):
        """
        Formats the question as clean readable text
        for display in the Gradio output box.
        """
        lines = []
        lines.append(f"{'=' * 52}")
        lines.append(f"  Question {self.number}  |  {self.topic}  |  {self.difficulty}")
        lines.append(f"{'=' * 52}")
        lines.append("")
        lines.append("QUESTION:")
        lines.append(self.question_text.strip())
        lines.append("")
        lines.append("EXPECTED OUTPUT COLUMNS:")
        lines.append(self.expected_output.strip())
        lines.append("")
        lines.append("POSTGRESQL SOLUTION:")
        lines.append(self.solution_query.strip())
        lines.append("")
        return "\n".join(lines)

    def to_csv_row(self):
        """Returns a dict for CSV export."""
        return {
            "question_number" : self.number,
            "topic"           : self.topic,
            "difficulty"      : self.difficulty,
            "question"        : self.question_text.strip(),
            "expected_output" : self.expected_output.strip(),
            "solution_query"  : self.solution_query.strip(),
        }


# ============================================================
# MAIN FUNCTION: Parse AI response into question objects
# ============================================================

def parse_questions(raw_text, context):
    """
    Parses the raw AI response text into a list of
    SQLQuestion objects.

    Args:
        raw_text : raw string from Groq API
        context  : context dict for topic/difficulty defaults

    Returns:
        List of SQLQuestion objects.
    """

    questions = []
    topic      = context.get("topic", "")
    difficulty = context.get("difficulty", "")

    # Split by question separator lines
    # Handles both === and --- style separators
    blocks = re.split(
        r"={3,}[\s]*Question\s*\d+[\s]*:[\s]*={3,}|"
        r"-{3,}[\s]*Question\s*\d+[\s]*:[\s]*-{3,}",
        raw_text,
        flags=re.IGNORECASE
    )

    # If split did not work well, try splitting by "Question N:"
    if len(blocks) <= 1:
        blocks = re.split(
            r"Question\s+\d+\s*:",
            raw_text,
            flags=re.IGNORECASE
        )

    question_num = 1

    for block in blocks:
        block = block.strip()
        if not block or len(block) < 20:
            continue

        q = SQLQuestion()
        q.number     = question_num
        q.topic      = topic
        q.difficulty = difficulty

        # ── Extract QUESTION text ────────────────────────────
        q.question_text = extract_section(
            block,
            start_markers=["QUESTION:", "Question:"],
            end_markers=[
                "EXPECTED OUTPUT", "POSTGRESQL SOLUTION",
                "SOLUTION:", "DIFFICULTY:", "TOPIC:", "======", "------"
            ]
        )

        # ── Extract EXPECTED OUTPUT COLUMNS ─────────────────
        q.expected_output = extract_section(
            block,
            start_markers=["EXPECTED OUTPUT COLUMNS:", "EXPECTED OUTPUT:"],
            end_markers=[
                "POSTGRESQL SOLUTION", "SOLUTION:",
                "DIFFICULTY:", "TOPIC:", "======", "------"
            ]
        )

        # ── Extract POSTGRESQL SOLUTION ──────────────────────
        q.solution_query = extract_section(
            block,
            start_markers=["POSTGRESQL SOLUTION:", "SOLUTION:"],
            end_markers=[
                "DIFFICULTY:", "TOPIC:",
                "======", "------", "Question "
            ]
        )

        # Clean up SQL — remove markdown code fences
        q.solution_query = clean_sql(q.solution_query)

        # Only add if question has minimum required content
        if q.question_text or q.solution_query:
            questions.append(q)
            question_num += 1

    return questions


# ============================================================
# HELPER: Extract a section from a text block
# ============================================================

def extract_section(text, start_markers, end_markers):
    """
    Extracts text between a start marker and end marker.

    Args:
        text          : the full block of text
        start_markers : list of possible start strings
        end_markers   : list of possible end strings

    Returns:
        Extracted text string, or empty string if not found.
    """

    content = ""
    start_pos = -1

    # Find the first matching start marker
    for marker in start_markers:
        idx = text.upper().find(marker.upper())
        if idx != -1:
            start_pos = idx + len(marker)
            break

    if start_pos == -1:
        return ""

    # Find the first matching end marker after start
    end_pos = len(text)
    for marker in end_markers:
        idx = text.upper().find(marker.upper(), start_pos)
        if idx != -1 and idx < end_pos:
            end_pos = idx

    content = text[start_pos:end_pos].strip()
    return content


# ============================================================
# HELPER: Clean SQL query text
# ============================================================

def clean_sql(sql_text):
    """
    Removes markdown formatting from SQL queries.
    """
    if not sql_text:
        return ""

    # Remove ```sql and ``` markers
    sql_text = re.sub(r"```sql\s*", "", sql_text)
    sql_text = re.sub(r"```\s*", "", sql_text)

    # Remove leading/trailing whitespace
    sql_text = sql_text.strip()

    return sql_text


# ============================================================
# MAIN FORMAT FUNCTION: Format all questions for display
# ============================================================

def format_questions_for_display(raw_text, context):
    """
    Full pipeline:
    1. Parse raw AI text into SQLQuestion objects
    2. Format each question for display
    3. Return complete formatted string

    Args:
        raw_text : raw string from generate_sql_questions()
        context  : context dict

    Returns:
        Formatted string for Gradio output box.
    """

    # Parse questions
    questions = parse_questions(raw_text, context)

    if not questions:
        # If parsing failed, return the raw text with a header
        return (
            "Note: Could not parse structured questions.\n"
            "Raw AI output shown below:\n\n"
            + raw_text
        )

    # Build header
    lines = []
    lines.append("SQL QUESTION BANK — Generated by AI")
    lines.append("=" * 52)
    lines.append(f"Table      : {context['table_name']}")
    lines.append(f"Topic      : {context['topic']}")
    lines.append(f"Difficulty : {context['difficulty']}")
    lines.append(f"Questions  : {len(questions)}")
    lines.append("=" * 52)
    lines.append("")

    # Format each question
    for q in questions:
        lines.append(q.to_display_text())

    return "\n".join(lines)


# ============================================================
# HELPER: Get list of SQLQuestion objects for export
# ============================================================

def get_question_objects(raw_text, context):
    """
    Returns parsed SQLQuestion objects for use in export.
    """
    return parse_questions(raw_text, context)