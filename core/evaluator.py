import json
import os
from google import genai
import config

def load_vault():
    vault_path = os.path.join(os.path.dirname(__file__), "..", "data", "vault.json")
    if os.path.exists(vault_path):
        try:
            with open(vault_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {}

def evaluate_answer_script(answer_text, question_context="", max_marks=15, api_key=None):
    """
    Evaluates candidate's Sociology answer script against UPSC CSE standards and Topper Vault benchmarks.
    """
    key = api_key or os.environ.get("GEMINI_API_KEY")
    if not key:
        raise ValueError("Gemini API key is required. Please set GEMINI_API_KEY environment variable or provide it in the UI.")
    
    client = genai.Client(api_key=key)
    vault = load_vault()
    
    vault_summary = ""
    if vault:
        definitions = [d.get("term") + " (" + d.get("author", "") + ")" for d in vault.get("definitions", [])[:5]]
        quotes = [q.get("thinker") + ": '" + q.get("quote") + "'" for q in vault.get("thinker_quotes", [])[:5]]
        vault_summary = f"""
        Sociology Topper Vault Context for reference:
        - Key Definitions: {', '.join(definitions)}
        - Benchmark Thinker Quotes: {'; '.join(quotes)}
        """

    prompt = f"""
    Evaluate the following UPSC CSE Sociology Optional Answer Script.

    --- QUESTION CONTEXT ---
    {question_context if question_context else 'Question inferred from the candidate script below.'}
    
    Maximum Marks for Question: {max_marks} Marks

    {vault_summary}

    --- CANDIDATE ANSWER SCRIPT (OCR Extracted) ---
    {answer_text}

    Please provide a detailed, rigorous evaluation strictly following your system prompt guidelines.
    Include scores for each dimension and out of {max_marks} marks overall.
    """

    response = client.models.generate_content(
        model=config.DEFAULT_MODEL,
        contents=[config.SYSTEM_EVALUATOR_PROMPT, prompt]
    )

    return response.text
