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

def evaluate_answer_script(answer_text, question_context="", max_marks=15, subject="Sociology Optional", api_key=None):
    """
    Evaluates candidate's answer script across GS 1, GS 2, GS 3, GS 4, Essay, or Sociology Optional.
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
        Topper Vault Benchmark Context:
        - Key Definitions/Articles: {', '.join(definitions)}
        - Benchmark Quotes: {'; '.join(quotes)}
        """

    subject_prompt = config.SUBJECT_PROMPTS.get(subject, config.SUBJECT_PROMPTS["Sociology Optional"])

    system_prompt = f"{config.SYSTEM_EVALUATOR_PROMPT_BASE}\n\n{subject_prompt}"

    prompt = f"""
    Evaluate the following UPSC CSE Mains Answer Script for Subject: {subject}.

    --- QUESTION CONTEXT ---
    {question_context if question_context else 'Question inferred from the candidate script below.'}
    
    Maximum Marks for Question: {max_marks} Marks

    {vault_summary}

    --- CANDIDATE ANSWER SCRIPT (OCR Extracted) ---
    {answer_text}

    Please provide a detailed, rigorous evaluation strictly following your system prompt guidelines.
    Include dimension scores, total marks out of {max_marks}, critical gaps, missing articles/thinkers, and a model approach.
    """

    response = client.models.generate_content(
        model=config.DEFAULT_MODEL,
        contents=[system_prompt, prompt]
    )

    return response.text
