import json
import os
import re
from google import genai
from google.genai import types
import config

def analyze_and_extract_topper_copy(extracted_ocr_text, subject="Sociology Optional", api_key=None):
    """
    Extracts reusable UPSC assets (definitions/articles, quotes/judgments, intro/outro templates, diagrams, essay hooks)
    from a topper's answer copy text for a SPECIFIC subject and updates data/vault.json with subject tags.
    """
    key = api_key or os.environ.get("GEMINI_API_KEY")
    if not key:
        raise ValueError("Gemini API key is required. Please set GEMINI_API_KEY environment variable or provide it in the UI.")
    
    client = genai.Client(api_key=key)

    if subject == "Essay Evaluator":
        prompt = f"""
        Analyze the following Topper Essay Copy text based on Anudeep Durishetty AIR 1 Essay Standards.
        TARGET SUBJECT: Essay Evaluator

        --- TOPPER ESSAY TEXT ---
        {extracted_ocr_text}

        Extract reusable Essay assets in JSON format with key structure:
        {{
            "analysis_summary": "Overall evaluation of this topper essay's hook, paragraph flow, connectives, subheadings, and rhetorical ending.",
            "essay_hooks": [
                {{"theme": "Education / Tech / Climate / Economy / Philosophy", "hook_type": "Fictitious Story / Anecdote / Statistic / Rhetorical Questions / Quote", "hook_text": "Extract exact opening hook (120-150 words)", "subject": "Essay Evaluator"}}
            ],
            "essay_structures": [
                {{"topic": "Essay Topic", "framework": "PESTLE / Temporal / Walks of Life / Debating For & Against", "subheadings": ["ALL-CAPS Subheading 1", "ALL-CAPS Subheading 2"], "subject": "Essay Evaluator"}}
            ],
            "essay_rhetorical_conclusions": [
                {{"type": "Tagore Gitanjali / Gandhiji Talisman / Echo Effect / Vision Statement", "ending_text": "Extract exact 30-50 word rhetorical ending", "subject": "Essay Evaluator"}}
            ],
            "thinker_quotes": [
                {{"thinker": "Name of Author/Leader", "quote": "Quote text", "context": "Essay topic context", "subject": "Essay Evaluator"}}
            ],
            "definitions": [
                {{"term": "Key Concept", "author": "Source/Author", "definition": "Brief definition", "reusable_context": "Essay Evaluator"}}
            ],
            "key_insights": ["Insight 1", "Insight 2", "Insight 3"]
        }}
        Return ONLY valid JSON. Do not include markdown code block backticks.
        """
    else:
        prompt = f"""
        Analyze the following Topper Answer Copy text for Target Subject: {subject}

        --- TOPPER ANSWER COPY TEXT ---
        {extracted_ocr_text}

        Extract reusable assets in JSON format specifically for {subject} with key structure:
        {{
            "analysis_summary": "Overall writing style and presentation summary of this topper copy for {subject}",
            "definitions": [
                {{"term": "...", "author": "...", "definition": "...", "reusable_context": "{subject}"}}
            ],
            "thinker_quotes": [
                {{"thinker": "...", "quote": "...", "context": "{subject}"}}
            ],
            "intro_templates": [
                {{"topic": "...", "template": "...", "subject": "{subject}"}}
            ],
            "outro_templates": [
                {{"topic": "...", "template": "...", "subject": "{subject}"}}
            ],
            "diagrams": [
                {{"title": "...", "description": "...", "reusable_context": "{subject}"}}
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
    if result_text.startswith("```"):
        result_text = re.sub(r"^```(?:json)?\n?", "", result_text)
        result_text = re.sub(r"\n?```$", "", result_text)

    try:
        extracted_data = json.loads(result_text)
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
        "diagrams": [],
        "essay_hooks": [],
        "essay_structures": [],
        "essay_rhetorical_conclusions": []
    }
    
    if os.path.exists(vault_path):
        try:
            with open(vault_path, "r", encoding="utf-8") as f:
                loaded = json.load(f)
                vault.update(loaded)
        except Exception:
            pass

    for key in ["definitions", "thinker_quotes", "intro_templates", "outro_templates", "diagrams", "essay_hooks", "essay_structures", "essay_rhetorical_conclusions"]:
        if key in new_data and isinstance(new_data[key], list):
            vault.setdefault(key, [])
            vault[key].extend(new_data[key])

    with open(vault_path, "w", encoding="utf-8") as f:
        json.dump(vault, f, indent=2)

