import json
import os
from google import genai
import config

def resolve_sociology_question(user_question, word_limit=250, paper_type="Both", api_key=None):
    """
    Answers direct user conceptual doubts or UPSC PYQs in UPSC Mains standard format.
    """
    key = api_key or os.environ.get("GEMINI_API_KEY")
    if not key:
        raise ValueError("Gemini API key is required. Please set GEMINI_API_KEY environment variable or provide it in the UI.")
    
    client = genai.Client(api_key=key)

    prompt = f"""
    Target Question: "{user_question}"
    Target Word Limit: {word_limit} words
    Target Syllabus Scope: {paper_type} (Paper 1 / Paper 2 / Inter-linked)

    Please answer this Sociology optional question following the structured UPSC Mains format defined in your system prompt.
    Ensure to include:
    1. Model UPSC Answer ({word_limit} words)
    2. Thinkers Matrix Table
    3. Contemporary Indian Examples & Case Studies
    4. Diagram/Flowchart Suggestion
    5. Common Pitfalls to Avoid
    """

    response = client.models.generate_content(
        model=config.DEFAULT_MODEL,
        contents=[config.SYSTEM_QA_PROMPT, prompt]
    )

    return response.text
