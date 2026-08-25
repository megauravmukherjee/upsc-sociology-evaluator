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

    # Force alignment if paper_type is specified and subject defaults
    if paper_type in config.SUBJECT_QA_PROMPTS and subject == "Sociology Optional" and paper_type != "Sociology Optional":
        subject = paper_type

    subject_prompt = config.SUBJECT_QA_PROMPTS.get(subject, config.SUBJECT_QA_PROMPTS["Sociology Optional"])

    prompt = f"""
    Target Subject: {subject}
    Target Question: "{user_question}"
    Target Word Limit: {word_limit} words
    Target Paper Scope: {paper_type}

    CRITICAL SUBJECT ISOLATION RULE:
    You are generating a model response for {subject}.
    DO NOT include or demand Sociology optional thinkers (such as Marx, Durkheim, Weber, Srinivas, Parsons, Merton, Mead) UNLESS the subject is explicitly 'Sociology Optional'!

    Please generate a model answer / blueprint for this {subject} question strictly adhering to your subject prompt instructions and Anudeep Durishetty AIR 1 frameworks:
    - For Essay Evaluator: Provide 120-150 word Intro Hook (Story / Anecdote / Stat / Rhetorical Questions / Quote, NO GS dictionary intros), PESTLE & Temporal Main Body Outline with 3-4 ALL-CAPS Subheadings, Paragraph Flow Connectives Guide, and 2-Segment Conclusion (Summary + 30-50 word Rhetorical Ending like Tagore Gitanjali / Talisman / Echo Effect).
    - For GS 1: History accuracy, Art & Culture architectural diagrams (Nagara/Dravida), Geography maps, and Indian Society.
    - For GS 2: Start polity answers with exact Constitutional Article numbers (Art 14, 19, 21, 32, 243, 262, 311), Supreme Court Judgments (Bommai, Kesavananda, Puttaswamy), 2nd ARC, and IR.
    - For GS 3: Open with sector statistics (GDP %, Debt %, NPAs %), Economic Survey, Budget, Sendai Framework, and security maps.
    - For GS 4: Ethics theory definition + personal example + leader value mapping (Ambedkar, Gandhi, JRD Tata) + case study framework with Gandhiji's Talisman.
    """

    response = client.models.generate_content(
        model=config.DEFAULT_MODEL,
        contents=[subject_prompt, prompt]
    )

    return response.text

# Alias for backwards compatibility
def resolve_sociology_question(user_question, word_limit=250, paper_type="Both", subject="Sociology Optional", api_key=None):
    return resolve_upsc_question(user_question, word_limit=word_limit, paper_type=paper_type, subject=subject, api_key=api_key)

