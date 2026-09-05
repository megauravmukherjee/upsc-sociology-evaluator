import json
import os
from google import genai
from google.genai import types
import config
from core import db

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
    
    # Filter vault items STRICTLY by subject to prevent ANY cross-contamination
    vault_summary = ""
    if vault:
        if subject == "Sociology Optional":
            defs = [d.get("term") + " (" + str(d.get("author", "")) + ")" for d in vault.get("definitions", []) if "Sociology" in d.get("reusable_context", "")][:4]
            quotes = [q.get("thinker") + ": '" + q.get("quote") + "'" for q in vault.get("thinker_quotes", []) if "Sociology" in q.get("context", "") or q.get("thinker") in ["Karl Marx", "Emile Durkheim", "M.N. Srinivas", "Max Weber"]][:4]
            vault_summary = f"\nRelevant {subject} Vault Benchmark Context:\n- Sociological Definitions: {', '.join(defs)}\n- Thinker Quotes: {'; '.join(quotes)}"
        
        elif subject == "GS 1":
            defs = [d.get("term") + ": " + d.get("definition") for d in vault.get("definitions", []) if "GS 1" in d.get("reusable_context", "") or "GS1" in d.get("reusable_context", "")][:4]
            quotes = [q.get("thinker") + ": '" + q.get("quote") + "'" for q in vault.get("thinker_quotes", []) if "GS 1" in q.get("context", "")][:3]
            vault_summary = f"\nRelevant {subject} Vault Benchmark Context:\n- Key Concepts/Locations: {', '.join(defs)}\n- Quotes/References: {'; '.join(quotes)}"
        
        elif subject == "GS 2":
            defs = [d.get("term") + ": " + d.get("definition") for d in vault.get("definitions", []) if "GS 2" in d.get("reusable_context", "") or "Polity" in d.get("reusable_context", "")][:4]
            quotes = [q.get("thinker") + ": '" + q.get("quote") + "'" for q in vault.get("thinker_quotes", []) if "GS 2" in q.get("context", "") or "Polity" in q.get("context", "")][:4]
            vault_summary = f"\nRelevant {subject} Vault Benchmark Context:\n- Articles & Precedents: {', '.join(defs)}\n- Key Quotes: {'; '.join(quotes)}"
        
        elif subject == "GS 3":
            defs = [d.get("term") + ": " + d.get("definition") for d in vault.get("definitions", []) if "GS 3" in d.get("reusable_context", "") or "Economy" in d.get("reusable_context", "")][:4]
            quotes = [q.get("thinker") + ": '" + q.get("quote") + "'" for q in vault.get("thinker_quotes", []) if "GS 3" in q.get("context", "")][:3]
            vault_summary = f"\nRelevant {subject} Vault Benchmark Context:\n- Sector Stats & Frameworks: {', '.join(defs)}\n- Key Quotes: {'; '.join(quotes)}"
        
        elif subject == "GS 4 (Ethics)":
            defs = [d.get("term") + ": " + d.get("definition") for d in vault.get("definitions", []) if "GS 4" in d.get("reusable_context", "") or "Ethics" in d.get("reusable_context", "")][:4]
            quotes = [q.get("thinker") + ": '" + q.get("quote") + "'" for q in vault.get("thinker_quotes", []) if "GS 4" in q.get("context", "") or "Ethics" in q.get("context", "")][:4]
            vault_summary = f"\nRelevant {subject} Vault Benchmark Context:\n- Ethics Values & Definitions: {', '.join(defs)}\n- Moral Thinker & Leader Quotes: {'; '.join(quotes)}"
        
        elif subject == "Essay Evaluator":
            hooks = [h.get("theme", "") + " Hook: " + h.get("hook_text", "") for h in vault.get("essay_hooks", [])][:3]
            quotes = [q.get("thinker") + ": '" + q.get("quote") + "'" for q in vault.get("thinker_quotes", []) if "Essay" in q.get("context", "") or q.get("subject") == "Essay Evaluator"][:4]
            rhetoricals = [r.get("type", "") + ": " + r.get("ending_text", "") for r in vault.get("essay_rhetorical_conclusions", [])][:2]
            
            vault_summary = f"\nBenchmark Essay Topper Vault Context (Anudeep Durishetty AIR 1 Standards):\n"
            if hooks:
                vault_summary += f"- Topper Intro Hooks: {'; '.join(hooks)}\n"
            if quotes:
                vault_summary += f"- Topper Essay Quotes: {'; '.join(quotes)}\n"
            if rhetoricals:
                vault_summary += f"- Topper Rhetorical Endings: {'; '.join(rhetoricals)}\n"

    # AI Grounding Memory
    past_evals = db.get_past_evaluations(subject, limit=2)
    memory_context = ""
    if past_evals:
        memory_context = "\n\n--- AI GROUNDING MEMORY: PAST EVALUATIONS ---\nFor consistency, align your grading strictness and style with these recent evaluations you performed:\n"
        for idx, ev in enumerate(past_evals):
            memory_context += f"Evaluation {idx+1} Score/Feedback Summary:\n{ev['evaluation_text'][:500]}...\n"

    subject_prompt = config.SUBJECT_PROMPTS.get(subject, config.SUBJECT_PROMPTS["Sociology Optional"])
    system_prompt = f"{config.SYSTEM_EVALUATOR_PROMPT_BASE}\n\n{subject_prompt}\n\n{vault_summary}{memory_context}"

    prompt = f"""
    Evaluate the following UPSC CSE Mains Answer Script.
    TARGET SUBJECT: {subject}
    
    CRITICAL SUBJECT ISOLATION RULE:
    You are evaluating a {subject} script. You MUST NOT demand, mention, or suggest Sociology optional thinkers (such as Marx, Durkheim, Weber, Srinivas, Ghurye, Parsons, Merton, Mead, Beteille) UNLESS the target subject is explicitly 'Sociology Optional'. Evaluate strictly and exclusively through the lens of {subject}!

    --- QUESTION CONTEXT ---
    {question_context if question_context else 'Question inferred from candidate script below.'}
    
    Maximum Marks for Question: {max_marks} Marks

    --- CANDIDATE ANSWER SCRIPT (OCR Extracted) ---
    {answer_text}

    Please provide a detailed, rigorous evaluation strictly following your subject prompt guidelines and Anudeep Durishetty AIR 1 frameworks.
    For Essay Evaluator: Assess 120-150 word Intro Hook (penalize GS dictionary intros!), PESTLE/Temporal Body, Paragraph Flow with Connectives, ALL-CAPS Subheadings, Simple Jargon-Free Language, and 2-Segment Conclusion (Summary + 30-50 word Rhetorical Ending).
    Include dimension scores, total marks out of {max_marks}, critical gaps, missing elements appropriate ONLY for {subject}, and a model approach.
    """

    eval_model = getattr(config, "EVAL_MODEL", config.DEFAULT_MODEL)
    
    # 3. Context Caching: Cuts input prompt cost by up to 75-90% for repeated evaluations
    cached_name = None
    if getattr(config, "ENABLE_CONTEXT_CACHING", False):
        try:
            cache = client.caches.create(
                model=eval_model,
                config=types.CreateCachedContentConfig(
                    contents=[system_prompt],
                    ttl="300s"
                )
            )
            cached_name = cache.name
        except Exception:
            cached_name = None

    if cached_name:
        response = client.models.generate_content(
            model=eval_model,
            contents=[prompt],
            config=types.GenerateContentConfig(cached_content=cached_name)
        )
    else:
        response = client.models.generate_content(
            model=eval_model,
            contents=[system_prompt, prompt]
        )

    eval_result = response.text
    
    # Save the evaluation to the memory database
    try:
        db.save_evaluation(subject, question_context, answer_text, eval_result, max_marks)
    except Exception as e:
        print(f"Failed to save evaluation to DB: {e}")

    return eval_result


