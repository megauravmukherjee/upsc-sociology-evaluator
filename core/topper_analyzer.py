import json
import os
import re
from google import genai
from google.genai import types
import config

def analyze_and_extract_topper_copy(extracted_ocr_text, api_key=None):
    """
    Extracts reusable Sociology assets (definitions, thinker quotes, intro/outro templates, diagrams)
    from a topper's answer copy text and updates data/vault.json.
    """
    key = api_key or os.environ.get("GEMINI_API_KEY")
    if not key:
        raise ValueError("Gemini API key is required. Please set GEMINI_API_KEY environment variable or provide it in the UI.")
    
    client = genai.Client(api_key=key)

    prompt = f"""
    Analyze the following Topper Answer Copy text extracted via OCR:

    --- TOPPER ANSWER COPY TEXT ---
    {extracted_ocr_text}

    Extract reusable assets in JSON format with key structure:
    {{
        "analysis_summary": "Overall writing style and presentation summary of this topper copy",
        "definitions": [
            {{"term": "...", "author": "...", "definition": "...", "reusable_context": "..."}}
        ],
        "thinker_quotes": [
            {{"thinker": "...", "quote": "...", "context": "..."}}
        ],
        "intro_templates": [
            {{"topic": "...", "template": "..."}}
        ],
        "outro_templates": [
            {{"topic": "...", "template": "..."}}
        ],
        "diagrams": [
            {{"title": "...", "description": "...", "reusable_context": "..."}}
        ],
        "key_insights": ["Insight 1", "Insight 2", "Insight 3"]
    }}
    Return ONLY valid JSON. Do not include markdown code block backticks.
    """

    response = client.models.generate_content(
        model=config.DEFAULT_MODEL,
        contents=[config.SYSTEM_TOPPER_ANALYZER_PROMPT, prompt]
    )

    result_text = response.text.strip()
    # Clean code block backticks if present
    if result_text.startswith("```"):
        result_text = re.sub(r"^```(?:json)?\n?", "", result_text)
        result_text = re.sub(r"\n?```$", "", result_text)

    try:
        extracted_data = json.loads(result_text)
        # Update vault.json
        update_vault_data(extracted_data)
        return extracted_data
    except Exception as e:
        return {
            "error": f"Failed to parse JSON output: {str(e)}",
            "raw_response": response.text
        }

def update_vault_data(new_data):
    vault_path = os.path.join(os.path.dirname(__file__), "..", "data", "vault.json")
    vault = {
        "definitions": [],
        "thinker_quotes": [],
        "intro_templates": [],
        "outro_templates": [],
        "diagrams": []
    }
    
    if os.path.exists(vault_path):
        try:
            with open(vault_path, "r", encoding="utf-8") as f:
                vault = json.load(f)
        except Exception:
            pass

    # Append new items ensuring no duplicates
    for key in ["definitions", "thinker_quotes", "intro_templates", "outro_templates", "diagrams"]:
        if key in new_data and isinstance(new_data[key], list):
            vault.setdefault(key, [])
            vault[key].extend(new_data[key])

    with open(vault_path, "w", encoding="utf-8") as f:
        json.dump(vault, f, indent=2)
