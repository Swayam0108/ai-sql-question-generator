# utils/hf_client.py
# ============================================================
# AI Client — Phase 6
# Uses Groq API (free, fast, reliable)
# Model: Llama 3 8B — excellent for SQL generation
# ============================================================

import os
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

# ============================================================
# CONFIG
# ============================================================

# Llama 3 is free on Groq and excellent at SQL
MODEL_ID = "llama-3.1-8b-instant"

# ============================================================
# MAIN FUNCTION: Call Groq API
# ============================================================

def call_huggingface_api(prompt, max_tokens=2000):
    """
    Sends a prompt to Groq API and returns generated text.
    Named call_huggingface_api to keep compatibility with
    the rest of the app — just uses Groq under the hood.

    Args:
        prompt     : full prompt string
        max_tokens : max tokens to generate

    Returns:
        Generated text string or error message.
    """

    # Get API key
    api_key = os.getenv("GROQ_API_KEY", "")

    if not api_key or api_key == "your_groq_api_key_here":
        return "ERROR: GROQ_API_KEY not set in .env file."

    try:
        # Create Groq client
        client = Groq(api_key=api_key)

        # Call the API
        chat_completion = client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are an expert PostgreSQL instructor. "
                        "You generate industry-level SQL questions "
                        "with correct PostgreSQL syntax. "
                        "Always follow the exact format requested."
                    ),
                },
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
            model=MODEL_ID,
            max_tokens=max_tokens,
            temperature=0.7,
        )

        # Extract and return the response text
        return chat_completion.choices[0].message.content.strip()

    except Exception as e:
        error_msg = str(e)

        if "401" in error_msg or "auth" in error_msg.lower():
            return "AUTH_ERROR: Invalid Groq API key. Check your .env file."

        if "429" in error_msg or "rate" in error_msg.lower():
            return "RATE_LIMITED: Too many requests. Wait a moment."

        return f"ERROR: {error_msg}"


# ============================================================
# HELPER: Test the connection
# ============================================================

def test_api_connection():
    """Tests Groq API with a simple SQL prompt."""

    print(f"Testing Groq API...")
    print(f"Model: {MODEL_ID}")
    print("")

    result = call_huggingface_api(
        "Write one simple PostgreSQL SELECT query for a products table "
        "with columns: brand, product, rating, price.",
        max_tokens=150
    )

    if any(result.startswith(e) for e in ["ERROR", "AUTH_ERROR", "RATE_LIMITED"]):
        print(f"FAILED: {result}")
        return result

    print(f"SUCCESS!")
    print(f"Response preview: {result[:200]}")
    return result


# ============================================================
# Run directly to test: python utils/hf_client.py
# ============================================================

if __name__ == "__main__":
    test_api_connection()