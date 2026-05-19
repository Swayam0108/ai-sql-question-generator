# app.py
# SQL Question Bank Generator — Hugging Face Spaces deployment
# app.py
# ============================================================
# SQL Question Bank Generator — Main Application
# Phase 2: Full Gradio UI (no AI yet, just the interface)
# ============================================================

import gradio as gr        # UI framework
import pandas as pd        # For reading CSV/Excel and preview
from dotenv import load_dotenv  # Load .env variables
# Import our schema extractor from the utils folder
from utils.schema_extractor import extract_schema, format_schema_for_display
from utils.context_builder import build_prompt_context, format_context_for_display
from generators.question_generator import generate_sql_questions
import os                  # Access environment variables
from docx import Document  # For DOCX export
from docx.shared import Pt, RGBColor  # Font size and color
# Load .env file so os.getenv() can read API keys
load_dotenv()
# Global variable to store the current dataset schema
# Updated every time a new file is uploaded
current_schema = {}

# ============================================================
# SECTION 1: Topic and difficulty options
# These are the dropdown choices shown to the user
# ============================================================

TOPICS = [
    "SELECT",
    "WHERE",
    "ORDER BY",
    "GROUP BY",
    "HAVING",
    "JOINS",
    "Subqueries",
    "CTE",
    "Window Functions",
    "CASE WHEN",
    "Aggregate Functions",
    "Ranking Functions",
    "Date Functions",
]

DIFFICULTY_LEVELS = ["Easy", "Medium", "Hard"]

# ============================================================
# SECTION 2: Dataset upload and preview function
# Called when user uploads a file
# ============================================================

def load_dataset(file):
    """
    Reads the uploaded file, extracts full schema,
    and returns a preview dataframe + formatted schema text.
    """

    if file is None:
        return None, "No file uploaded yet."

    try:
        # Extract full schema using our new module
        schema = extract_schema(file)

        # Read file again for the preview table
        if file.endswith(".csv"):
            df = pd.read_csv(file)
        else:
            df = pd.read_excel(file)

        # Format schema info for display
        status = format_schema_for_display(schema)

        # Store schema in a global so generate_questions can use it
        global current_schema
        current_schema = schema

        return df.head(5), status

    except Exception as e:
        return None, f"Error: {str(e)}"


# ============================================================
# SECTION 3: Placeholder question generator
# This will be replaced with real AI in Phase 6-8
# For now it just confirms the UI inputs are working
# ============================================================

def generate_questions(file, topic, difficulty, num_questions):
    """
    Full pipeline:
    1. Check file and schema
    2. Build prompt context
    3. Call Groq AI
    4. Return formatted questions
    """

    # Check file uploaded
    if file is None:
        return "Please upload a dataset file first."

    # Check schema exists
    if not current_schema or "error" in current_schema:
        return "Schema not found. Please re-upload your dataset."

    # Build context
    context = build_prompt_context(
        schema=current_schema,
        topic=topic,
        difficulty=difficulty,
        num_questions=int(num_questions),
    )

    if "error" in context:
        return f"Error: {context['error']}"

    # Generate questions using AI
    result = generate_sql_questions(context)
    return result


# ============================================================
# SECTION 4: Export placeholder functions
# Real export logic added in Phase 10
# ============================================================

# ============================================================
# SECTION 4: Export functions
# All exports now use the structured exporter module
# ============================================================

from utils.exporter import export_to_txt, export_to_csv, export_to_docx
from generators.question_generator import get_last_raw_response

def export_txt(output_text):
    """Export generated questions as TXT file."""
    if not output_text or output_text.strip() == "":
        return None
    return export_to_txt(output_text)


def export_csv(output_text):
    """Export generated questions as CSV file."""
    if not output_text or output_text.strip() == "":
        return None
    _, context = get_last_raw_response()
    if not context:
        return None
    return export_to_csv(output_text, context)


def export_docx(output_text):
    """Export generated questions as DOCX file."""
    if not output_text or output_text.strip() == "":
        return None
    _, context = get_last_raw_response()
    if not context:
        return None
    return export_to_docx(output_text, context)


# ============================================================
# SECTION 5: Build the Gradio UI
# gr.Blocks lets us control layout precisely
# ============================================================

with gr.Blocks(
    title="SQL Question Bank Generator",
    theme=gr.themes.Soft(),       # Clean soft theme
) as app:

    # ── App header ──────────────────────────────────────────
    gr.Markdown("""
    # SQL Question Bank Generator
    **AI-powered PostgreSQL question generator** — upload a dataset,
    choose your topic and difficulty, and get industry-level SQL questions.
    """)

    # ── Step 1: File Upload ──────────────────────────────────
    gr.Markdown("---")
    gr.Markdown("## Step 1 — Upload your dataset")

    with gr.Row():
        with gr.Column(scale=1):
            # File upload component
            file_input = gr.File(
                label="Upload CSV or Excel file",
                file_types=[".csv", ".xlsx", ".xls"],
                type="filepath",
            )

        with gr.Column(scale=2):
            # Status message shown after upload
            upload_status = gr.Textbox(
                label="File info",
                lines=3,
                interactive=False,
                placeholder="Upload a file to see dataset info here...",
            )

    # ── Step 2: Dataset Preview ──────────────────────────────
    gr.Markdown("## Step 2 — Dataset preview")

    dataset_preview = gr.Dataframe(
        label="First 5 rows of your dataset",
        interactive=False,
        wrap=True,
    )

    # When a file is uploaded, auto-trigger load_dataset()
    file_input.change(
        fn=load_dataset,
        inputs=[file_input],
        outputs=[dataset_preview, upload_status],
    )

    # ── Step 3: Question Settings ────────────────────────────
    gr.Markdown("---")
    gr.Markdown("## Step 3 — Configure question settings")

    with gr.Row():
        with gr.Column():
            # Topic dropdown
            topic_dropdown = gr.Dropdown(
                choices=TOPICS,
                value="Window Functions",
                label="PostgreSQL topic",
            )

        with gr.Column():
            # Difficulty dropdown
            difficulty_dropdown = gr.Dropdown(
                choices=DIFFICULTY_LEVELS,
                value="Medium",
                label="Difficulty level",
            )

        with gr.Column():
            # Number of questions slider
            num_questions_slider = gr.Slider(
                minimum=1,
                maximum=10,
                value=3,
                step=1,
                label="Number of questions",
            )

    # Generate button
    generate_btn = gr.Button(
        "Generate SQL Questions",
        variant="primary",    # Blue button
        size="lg",
    )

    # ── Step 4: Output ───────────────────────────────────────
    gr.Markdown("---")
    gr.Markdown("## Step 4 — Generated questions")

    output_box = gr.Textbox(
        label="Generated SQL questions will appear here",
        lines=20,
        interactive=False,
        placeholder="Click 'Generate SQL Questions' to see results...",
    )

    # Wire the generate button to the function
    generate_btn.click(
        fn=generate_questions,
        inputs=[file_input, topic_dropdown, difficulty_dropdown, num_questions_slider],
        outputs=[output_box],
    )

    # ── Step 5: Export ───────────────────────────────────────
    gr.Markdown("---")
    gr.Markdown("## Step 5 — Export")

    with gr.Row():
        export_txt_btn = gr.Button("Download as TXT", size="sm")
        export_docx_btn = gr.Button("Download as DOCX (Google Docs)", size="sm")
        export_csv_btn = gr.Button("Download as CSV", size="sm")

    export_file = gr.File(label="Your download", visible=True)

    # TXT export button wired to export_txt function
    export_txt_btn.click(
        fn=export_txt,
        inputs=[output_box],
        outputs=[export_file],
    )

    # DOCX export button wired to export_docx function
    export_docx_btn.click(
        fn=export_docx,
        inputs=[output_box],
        outputs=[export_file],
    )

    # CSV export button wired to export_csv function
    export_csv_btn.click(
    fn=export_csv,
    inputs=[output_box],
    outputs=[export_file],
    )

# ============================================================
# SECTION 6: Run the app
# ============================================================

if __name__ == "__main__":
    app.launch(
        show_error=True,    # Show full errors in browser
    )