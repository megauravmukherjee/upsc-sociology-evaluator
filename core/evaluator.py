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
    Enforces ABSOLUTE SUBJECT ISOLATION based on Anudeep Durishetty (AIR 1) frameworks.
    """
    key = api_key or os.environ.get("GEMINI_API_KEY")
    if not key:
        raise ValueError("Gemini API key is required. Please set GEMINI_API_KEY environment variable or provide it in the UI.")
    
    client = genai.Client(api_key=key)
    vault = load_vault()
    
    # Filter vault items by subject to prevent ANY cross-contamination
    vault_summary = ""
    if vault:
        if subject == "Sociology Optional":
            defs = [d.get("term") + " (" + d.get("author", "") + ")" for d in vault.get("definitions", []) if "Sociology" in d.get("reusable_context", "Sociology")][:4]
            quotes = [q.get("thinker") + ": '" + q.get("quote") + "'" for q in vault.get("thinker_quotes", []) if q.get("thinker") in ["Karl Marx", "Emile Durkheim", "M.N. Srinivas"]][:3]
        elif subject == "GS 2":
            defs = [d.get("term") + ": " + d.get("definition") for d in vault.get("definitions", []) if "GS 2" in d.get("reusable_context", "GS 2")][:4]
            quotes = [q.get("thinker") + ": '" + q.get("quote") + "'" for q in vault.get("thinker_quotes", []) if "GS 2" in q.get("context", "")][:3]
        elif subject == "GS 3":
            defs = [d.get("term") + ": " + d.get("definition") for d in vault.get("definitions", []) if "GS 3" in d.get("reusable_context", "GS 3")][:4]
            quotes = [q.get("thinker") + ": '" + q.get("quote") + "'" for q in vault.get("thinker_quotes", []) if "GS 3" in q.get("context", "")][:3]
        elif subject == "GS 4 (Ethics)":
            defs = [d.get("term") + ": " + d.get("definition") for d in vault.get("definitions", []) if "GS 4" in d.get("reusable_context", "GS 4")][:4]
            quotes = [q.get("thinker") + ": '" + q.get("quote") + "'" for q in vault.get("thinker_quotes", []) if "GS 4" in q.get("context", "")][:3]
        elif subject == "Essay Evaluator":
            defs = [d.get("term") + ": " + d.get("definition") for d in vault.get("definitions", []) if "Essay" in d.get("reusable_context", "Essay")][:3]
            quotes = [q.get("thinker") + ": '" + q.get("quote") + "'" for q in vault.get("thinker_quotes", []) if q.get("thinker") in ["Mahatma Gandhi", "Immanuel Kant"]][:3]
        else:
            defs = []
            quotes = []

        if defs or quotes:
            vault_summary = f"""
            Relevant {subject} Vault Benchmark Context:
            - Key Definitions/Articles/Terms: {', '.join(defs)}
            - Benchmark Quotes/Precedents: {'; '.join(quotes)}
            """

    subject_prompt = config.SUBJECT_PROMPTS.get(subject, config.SUBJECT_PROMPTS["Sociology Optional"])
    system_prompt = f"{config.SYSTEM_EVALUATOR_PROMPT_BASE}\n\n{subject_prompt}"

    prompt = f"""
    Evaluate the following UPSC CSE Mains Answer Script.
    TARGET SUBJECT: {subject}
    CRITICAL MANDATE: Evaluate ONLY through the lens of {subject}. DO NOT mention or demand Sociology optional thinkers unless the subject is explicitly Sociology Optional!

    --- QUESTION CONTEXT ---
    {question_context if question_context else 'Question inferred from candidate script below.'}
    
    Maximum Marks for Question: {max_marks} Marks

    {vault_summary}

    --- CANDIDATE ANSWER SCRIPT (OCR Extracted) ---
    {answer_text}

    Please provide a detailed, rigorous evaluation strictly following your subject prompt guidelines and Anudeep Durishetty AIR 1 frameworks.
    Include dimension scores, total marks out of {max_marks}, critical gaps, missing articles/facts/thinkers appropriate ONLY for {subject}, and a model approach.
    """

    response = client.models.generate_content(
        model=config.DEFAULT_MODEL,
        contents=[system_prompt, prompt]
    )

    return response.text
