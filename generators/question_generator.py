# generators/question_generator.py
# ============================================================
# Question Generator — Phase 8 + 9 combined
# ============================================================

from prompts.prompt_builder import build_prompt
from utils.hf_client import call_huggingface_api
from generators.formatter import format_questions_for_display

# Store last raw response for export use
last_raw_response = ""
last_context = {}

def generate_sql_questions(context):
    """
    Full pipeline: prompt → AI → format → display
    """
    global last_raw_response, last_context

    if not context or "error" in context:
        return "Error: No valid context. Please upload a dataset first."

    # Build prompt
    prompt = build_prompt(context)

    # Call AI
    print(f"Calling Groq API — Topic: {context['topic']} | Difficulty: {context['difficulty']}")
    raw_response = call_huggingface_api(prompt=prompt, max_tokens=3000)

    # Check for errors
    if any(raw_response.startswith(e) for e in [
        "ERROR", "AUTH_ERROR", "RATE_LIMITED", "TIMEOUT"
    ]):
        return f"API Error: {raw_response}"

    # Store for export
    last_raw_response = raw_response
    last_context = context

    # Format and return
    return format_questions_for_display(raw_response, context)


def get_last_raw_response():
    """Returns the last raw AI response for export."""
    return last_raw_response, last_context