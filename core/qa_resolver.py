import json
import os
from google import genai
import config

def resolve_upsc_question(user_question, word_limit=250, paper_type="Both", subject="Sociology Optional", api_key=None):
    """
    Answers direct user conceptual doubts or UPSC PYQs using Anudeep Durishetty AIR 1 subject frameworks.
    Guarantees strict subject isolation without forcing Sociology thinkers into GS or Essay papers.
    """
    key = api_key or os.environ.get("GEMINI_API_KEY")
    if not key:
        raise ValueError("Gemini API key is required. Please set GEMINI_API_KEY environment variable or provide it in the UI.")
    
    client = genai.Client(api_key=key)

    subject_prompt = config.SUBJECT_QA_PROMPTS.get(subject, config.SUBJECT_QA_PROMPTS["Sociology Optional"])

    prompt = f"""
    Target Subject: {subject}
    Target Question: "{user_question}"
    Target Word Limit: {word_limit} words
    Target Paper Scope: {paper_type}

    Please generate a model answer / blueprint for this {subject} question strictly adhering to your subject prompt instructions and Anudeep Durishetty AIR 1 frameworks.
    CRITICAL RULE: DO NOT include Sociology thinkers unless the subject is explicitly Sociology Optional!
    """

    response = client.models.generate_content(
        model=config.DEFAULT_MODEL,
        contents=[subject_prompt, prompt]
    )

    return response.text

# Alias for backwards compatibility
def resolve_sociology_question(user_question, word_limit=250, paper_type="Both", subject="Sociology Optional", api_key=None):
    return resolve_upsc_question(user_question, word_limit=word_limit, paper_type=paper_type, subject=subject, api_key=api_key)
