import json
import os
from google import genai
from google.genai import types
import config
from core import db
from core.rag_search import search_personal_notes

def resolve_upsc_question(user_question, word_limit=250, paper_type="Both", subject="Sociology Optional", api_key=None):
    """
    Generates a model answer or conceptual breakdown for a given UPSC question.
    """
    key = api_key or os.environ.get("GEMINI_API_KEY")
    if not key:
        raise ValueError("Gemini API key is required.")
    
    client = genai.Client(api_key=key)

    # Load from Vault for exact definitions
    vault_path = os.path.join(os.path.dirname(__file__), "..", "data", "vault.json")
    vault_data = {}
    if os.path.exists(vault_path):
        try:
            with open(vault_path, "r", encoding="utf-8") as f:
                vault_data = json.load(f)
        except Exception:
            pass

    # Basic Vault lookup
    relevant_defs = []
    if vault_data and "definitions" in vault_data:
        for d in vault_data["definitions"]:
            if d.get("term", "").lower() in user_question.lower():
                author_str = f" ({d.get('author')})" if d.get("author") else ""
                relevant_defs.append(f"{d.get('term')}{author_str}: {d.get('definition')}")

    vault_injection = ""
    if relevant_defs:
        vault_injection = f"\nRelevant Vault Definitions:\n" + "\n".join(relevant_defs)

    subject_prompt = config.SUBJECT_QA_PROMPTS.get(subject, config.SUBJECT_QA_PROMPTS["Sociology Optional"])

    # AI Grounding Memory
    past_answers = db.get_past_model_answers(subject, limit=2)
    memory_context = ""
    if past_answers:
        memory_context = "\n\n--- AI GROUNDING MEMORY: PAST MODEL ANSWERS ---\nFor consistency, maintain a similar analytical depth and style to these past model answers:\n"
        for idx, ans in enumerate(past_answers):
            memory_context += f"Model Answer {idx+1} (Preview):\n{ans['answer_text'][:500]}...\n"
            
    # Personal Notes RAG Injection
    rag_context = ""
    relevant_notes = search_personal_notes(user_question, subject, api_key=key, top_k=3)
    if relevant_notes:
        rag_context = "\n\n--- YOUR PERSONAL NOTES (RAG) ---\nIncorporate these highly relevant facts and arguments from your personal notes into the model answer:\n"
        for note in relevant_notes:
            rag_context += f"- {note}\n"

    system_prompt = f"{subject_prompt}\n\n{vault_injection}{memory_context}{rag_context}"

    prompt = f"""
    TARGET QUESTION / DOUBT: {user_question}
    TARGET WORD LIMIT: ~{word_limit} words
    TARGET PAPER: {paper_type}
    
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
        contents=[system_prompt, prompt]
    )

    ans_result = response.text
    
    # Save the model answer to the memory database
    try:
        db.save_model_answer(subject, user_question, ans_result)
    except Exception as e:
        print(f"Failed to save model answer to DB: {e}")

    return ans_result

# Alias for backwards compatibility
def resolve_sociology_question(user_question, word_limit=250, paper_type="Both", subject="Sociology Optional", api_key=None):
    return resolve_upsc_question(user_question, word_limit=word_limit, paper_type=paper_type, subject=subject, api_key=api_key)
