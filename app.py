import os
import json
import importlib
import streamlit as st
import config
import core.ocr_engine
import core.evaluator
import core.qa_resolver
import core.topper_analyzer
importlib.reload(config)
importlib.reload(core.ocr_engine)
importlib.reload(core.evaluator)
importlib.reload(core.qa_resolver)
importlib.reload(core.topper_analyzer)

from core.ocr_engine import process_pdf_or_image
from core.evaluator import evaluate_answer_script, load_vault
from core.qa_resolver import resolve_sociology_question
from core.topper_analyzer import analyze_and_extract_topper_copy

st.set_page_config(
    page_title="UPSC CSE All-Subject Answer Evaluator",
    page_icon="🎓",
    layout="wide"
)

# Custom CSS matching deployed light mode layout
st.markdown("""
<style>
    .main-header {
        font-size: 2.3rem;
        font-weight: 700;
        color: #1E3A8A;
        margin-bottom: 0.2rem;
    }
    .sub-header {
        font-size: 1.1rem;
        color: #4B5563;
        margin-bottom: 1.5rem;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        white-space: pre-wrap;
        background-color: #F3F4F6;
        border-radius: 8px 8px 0px 0px;
        padding-top: 10px;
        padding-bottom: 10px;
        font-weight: 600;
    }
    .stTabs [aria-selected="true"] {
        background-color: #1E3A8A !important;
        color: white !important;
    }
    .metric-card {
        background-color: #EFF6FF;
        border-left: 5px solid #2563EB;
        padding: 12px;
        border-radius: 6px;
        margin-bottom: 10px;
    }
</style>
""", unsafe_allow_html=True)

# Sidebar Configuration
st.sidebar.title("🎓 UPSC CSE AI Evaluator")
st.sidebar.caption("Evaluator, Doubt Resolver & Strategy Vault")

# Subject Selector in Sidebar
selected_subject = st.sidebar.selectbox(
    "🎯 Select UPSC Subject",
    options=["Sociology Optional", "GS 1", "GS 2", "GS 3", "GS 4 (Ethics)", "Essay Evaluator"],
    index=0
)

# Secure API Key Management (Never expose server keys in UI text inputs)
server_key = os.environ.get("GEMINI_API_KEY")
if not server_key and hasattr(st, "secrets"):
    try:
        server_key = st.secrets.get("GEMINI_API_KEY")
    except Exception:
        pass

if server_key:
    st.sidebar.success("🔒 API Key: Active (Secured Backend)")
    with st.sidebar.expander("🔑 Override API Key (Optional)", expanded=False):
        user_override = st.text_input("Custom Gemini API Key", type="password", help="Leave blank to use secured backend API key.")
        api_key = user_override.strip() if user_override.strip() else server_key
else:
    user_key = st.sidebar.text_input("Enter Gemini API Key", type="password")
    if not user_key:
        st.sidebar.warning("⚠️ Please enter a Gemini API Key to enable AI features.")
    api_key = user_key.strip()

st.sidebar.divider()

# Load Vault Data for sidebar stats
vault_data = load_vault()
st.sidebar.markdown(f"### 📊 {selected_subject} Vault Stats")
col_s1, col_s2 = st.sidebar.columns(2)

if selected_subject == "Essay Evaluator":
    col_s1.metric("Essay Intro Hooks", len(vault_data.get("essay_hooks", [])))
    col_s2.metric("Rhetorical Endings", len(vault_data.get("essay_rhetorical_conclusions", [])))
    col_s3, col_s4 = st.sidebar.columns(2)
    col_s3.metric("Essay Structures", len(vault_data.get("essay_structures", [])))
    col_s4.metric("Benchmark Quotes", len(vault_data.get("thinker_quotes", [])))
else:
    col_s1.metric("Definitions / Articles", len(vault_data.get("definitions", [])))
    col_s2.metric("Thinker / Case Quotes", len(vault_data.get("thinker_quotes", [])))
    col_s3, col_s4 = st.sidebar.columns(2)
    col_s3.metric("Intro Templates", len(vault_data.get("intro_templates", [])))
    col_s4.metric("Diagram Schematics", len(vault_data.get("diagrams", [])))

st.sidebar.divider()

# Syllabus Reference Expander
with st.sidebar.expander("📖 Syllabus Quick Reference"):
    syllabus_path = os.path.join(os.path.dirname(__file__), "data", "syllabus.json")
    if os.path.exists(syllabus_path):
        with open(syllabus_path, "r", encoding="utf-8") as f:
            syl = json.load(f)
            st.markdown(f"#### {selected_subject} Syllabus Topics")
            sub_key = selected_subject.lower().replace(" ", "").replace("(ethics)", "4").replace("evaluator", "")
            sub_info = syl.get(sub_key, {})
            for topic in sub_info.get("subtopics", []):
                st.write(f"- {topic}")

# Main App Header
st.markdown(f'<div class="main-header">UPSC CSE {selected_subject} AI Hub</div>', unsafe_allow_html=True)
st.markdown(f'<div class="sub-header">Evaluate handwritten scripts for {selected_subject} with Vision OCR, solve doubts without subject bleeding, and train your Strategy Vault with Topper copies.</div>', unsafe_allow_html=True)

tab1, tab2, tab3, tab4 = st.tabs([
    "📄 Module 1: Answer Script Evaluator",
    "❓ Module 2: Doubt & PYQ Resolver",
    "🏆 Module 3: Topper Vault & Analytics",
    "📚 Module 4: Memory & Grounding"
])

# ==========================================
# TAB 1: ANSWER SCRIPT EVALUATOR
# ==========================================
with tab1:
    st.header(f"📝 Handwritten {selected_subject} Script Evaluator")
    st.markdown(f"Upload your handwritten or typed PDF / Image answer scripts for OCR extraction and {selected_subject} rubric evaluation.")
    
    col_up1, col_up2 = st.columns([2, 1])
    
    with col_up1:
        uploaded_file = st.file_uploader("Upload Answer Script (PDF, PNG, JPG, JPEG)", type=["pdf", "png", "jpg", "jpeg"])
        question_context = st.text_area("Question Text (Optional but recommended)", placeholder=f"Enter the exact {selected_subject} question prompt here if available...")
    
    with col_up2:
        max_marks = st.selectbox("Maximum Marks", options=[10, 15, 20, 125, 250], index=1 if selected_subject != "Essay Evaluator" else 3)
        
        st.write("📄 **Token Optimization (Page Slice)**")
        col_pr1, col_pr2 = st.columns(2)
        with col_pr1:
            start_p = st.number_input("Start Page", min_value=1, value=1, step=1, key="eval_start_p")
        with col_pr2:
            end_p = st.number_input("End Page (0 = All)", min_value=0, value=0, step=1, key="eval_end_p")
            
        st.info(f"💡 **Evaluation Rubric ({selected_subject})**: Assesses Demand of Question, Subject Rigor, Structural Balance, Value Addition, and Scored Marks.")

    if uploaded_file and st.button("🚀 Process OCR & Evaluate Script", type="primary", use_container_width=True):
        if not api_key:
            st.error("Please enter a valid Gemini API Key in the sidebar.")
        else:
            with st.status(f"Processing {selected_subject} Script...", expanded=True) as status:
                def update_progress(msg):
                    status.write(f"⏳ {msg}")

                file_bytes = uploaded_file.read()
                actual_end_p = end_p if end_p > 0 else None
                ocr_text, images = process_pdf_or_image(file_bytes, uploaded_file.name, start_page=start_p, end_page=actual_end_p, api_key=api_key, progress_callback=update_progress)
                
                status.write("✅ Multimodal OCR Complete!")
                status.write(f"⏳ Evaluating against {selected_subject} UPSC Rubrics & Vault...")
                
                eval_report = evaluate_answer_script(ocr_text, question_context, max_marks=max_marks, subject=selected_subject, api_key=api_key)
                status.update(label=f"✅ {selected_subject} Evaluation Complete!", state="complete", expanded=False)
            
            # Show OCR Preview
            with st.expander("🔍 View Extracted Text (OCR Result)", expanded=False):
                st.text_area("Extracted Answer Content", ocr_text, height=200)

            st.markdown("---")
            st.subheader(f"📊 UPSC {selected_subject} Evaluation Report & Scorecard")
            st.markdown(eval_report)

# ==========================================
# TAB 2: DOUBT & PYQ RESOLVER
# ==========================================
with tab2:
    st.header(f"❓ {selected_subject} Conceptual Doubt & PYQ Resolver")
    st.markdown(f"Ask direct questions or previous year questions (PYQs) for **{selected_subject}**. The generator uses strict subject isolation to prevent cross-subject bleeding.")
    
    user_q = st.text_area(f"Enter your {selected_subject} Question / Doubt", placeholder=f"e.g. Enter any tricky PYQ or conceptual question for {selected_subject}...")
    
    options_list = ["Sociology Optional", "GS 1", "GS 2", "GS 3", "GS 4 (Ethics)", "Essay Evaluator"]
    default_idx = options_list.index(selected_subject) if selected_subject in options_list else 0

    col_q1, col_q2 = st.columns(2)
    with col_q1:
        word_limit = st.select_slider("Target Word Limit", options=[150, 250, 1000, 1200], value=250 if selected_subject != "Essay Evaluator" else 1000)
    with col_q2:
        paper_scope = st.selectbox("Target Paper Scope", options=options_list, index=default_idx)

    if user_q and st.button(f"💡 Generate {paper_scope} Model Answer / Blueprint", type="primary", use_container_width=True):
        if not api_key:
            st.error("Please enter a valid Gemini API Key in the sidebar.")
        else:
            with st.spinner(f"Synthesizing {paper_scope} model answer..."):
                ans_result = resolve_sociology_question(user_q, word_limit=word_limit, paper_type=paper_scope, subject=paper_scope, api_key=api_key)
            
            st.markdown("---")
            st.subheader(f"✍️ Model Answer / Essay Blueprint ({paper_scope})")
            st.markdown(ans_result)

# ==========================================
# TAB 3: TOPPER VAULT & ANALYTICS
# ==========================================
with tab3:
    st.header(f"🏆 {selected_subject} Topper Copy Learning & Reusable Bank")
    st.markdown(f"Upload topper answer copies (PDFs/Images) to train your Strategy Vault. Extracted hooks, quotes, structures, and definitions automatically refine future evaluations.")
    
    col_top1, col_top2 = st.columns([2, 1])
    with col_top1:
        topper_file = st.file_uploader("Upload Topper Copy PDF / Images", type=["pdf", "png", "jpg", "jpeg"], key="topper_upload")
    with col_top2:
        st.write("📄 **Page Slice (Save API Tokens)**")
        t_start_p = st.number_input("Start Page", min_value=1, value=1, step=1, key="topper_start_p")
        t_end_p = st.number_input("End Page (0 = All)", min_value=0, value=0, step=1, key="topper_end_p")
    
    if topper_file and st.button(f"⚡ Extract & Train Vault with {selected_subject} Topper Copy", type="primary"):
        if not api_key:
            st.error("Please enter a valid Gemini API Key in the sidebar.")
        else:
            with st.status(f"Analyzing {selected_subject} Topper Copy...", expanded=True) as status:
                def update_progress(msg):
                    status.write(f"⏳ {msg}")

                file_bytes = topper_file.read()
                t_actual_end = t_end_p if t_end_p > 0 else None
                ocr_text, _ = process_pdf_or_image(file_bytes, topper_file.name, start_page=t_start_p, end_page=t_actual_end, api_key=api_key, progress_callback=update_progress)
                status.write(f"⏳ Extracting {selected_subject} definitions, hooks, quotes, diagrams & templates...")
                extracted_data = analyze_and_extract_topper_copy(ocr_text, subject=selected_subject, api_key=api_key)
                status.update(label=f"🎉 Successfully analyzed and trained Vault with {selected_subject} Topper Copy!", state="complete", expanded=False)
            
            if "analysis_summary" in extracted_data:
                st.info(f"**Topper Copy Strategy Summary**: {extracted_data['analysis_summary']}")
            
            if selected_subject == "Essay Evaluator":
                t_col1, t_col2 = st.columns(2)
                with t_col1:
                    st.subheader("🎣 Extracted Essay Hooks")
                    for h in extracted_data.get("essay_hooks", []):
                        st.markdown(f"- **{h.get('theme')}** ({h.get('hook_type')}): *{h.get('hook_text')}*")
                    
                    st.subheader("💡 Extracted Quotes")
                    for q in extracted_data.get("thinker_quotes", []):
                        st.markdown(f"- **{q.get('thinker')}**: \"{q.get('quote')}\"")

                with t_col2:
                    st.subheader("🏛️ Extracted Essay Structures")
                    for s in extracted_data.get("essay_structures", []):
                        st.markdown(f"- **{s.get('topic')}** ({s.get('framework')}):\n  - Subheadings: {', '.join(s.get('subheadings', []))}")
                    
                    st.subheader("🎯 Rhetorical Conclusions")
                    for r in extracted_data.get("essay_rhetorical_conclusions", []):
                        st.markdown(f"- **{r.get('type')}**: {r.get('ending_text')}")
            else:
                t_col1, t_col2 = st.columns(2)
                with t_col1:
                    st.subheader("📌 Extracted Definitions / Articles")
                    for d in extracted_data.get("definitions", []):
                        st.markdown(f"- **{d.get('term')}** ({d.get('author')}): *{d.get('definition')}*")
                    
                    st.subheader("💡 Extracted Quotes / Judgments")
                    for q in extracted_data.get("thinker_quotes", []):
                        st.markdown(f"- **{q.get('thinker')}**: \"{q.get('quote')}\"")

                with t_col2:
                    st.subheader("🎨 Diagram Schematics")
                    for diag in extracted_data.get("diagrams", []):
                        st.markdown(f"- **{diag.get('title')}**: {diag.get('description')}")
                    
                    st.subheader("🚀 Intro & Outro Templates")
                    for intro in extracted_data.get("intro_templates", []):
                        st.markdown(f"- **{intro.get('topic')}**: {intro.get('template')}")

    st.markdown("---")
    st.subheader(f"📖 Browse Complete Strategy Vault")
    
    vault_view = load_vault()
    vtab1, vtab2, vtab3, vtab4, vtab5 = st.tabs([
        "Definitions & Articles", 
        "Quotes & Thinkers", 
        "Essay Hooks & Stories", 
        "Essay Rhetorical Endings", 
        "Diagrams & Templates"
    ])
    
    with vtab1:
        for item in vault_view.get("definitions", []):
            st.markdown(f"#### 🔹 {item.get('term')} ({item.get('author')})")
            st.write(item.get('definition'))
            st.caption(f"Subject Context: {item.get('reusable_context', '')}")
            st.divider()
            
    with vtab2:
        for item in vault_view.get("thinker_quotes", []):
            st.markdown(f"#### 💬 {item.get('thinker')}")
            st.write(f"*{item.get('quote')}*")
            st.caption(f"Usage Context: {item.get('context', '')}")
            st.divider()

    with vtab3:
        for item in vault_view.get("essay_hooks", []):
            st.markdown(f"#### 🎣 {item.get('theme')} ({item.get('hook_type', 'Hook')})")
            st.write(item.get('hook_text'))
            st.caption(f"Subject: {item.get('subject', 'Essay Evaluator')}")
            st.divider()

    with vtab4:
        for item in vault_view.get("essay_rhetorical_conclusions", []):
            st.markdown(f"#### 🎯 {item.get('type')}")
            st.write(item.get('ending_text'))
            st.divider()

    with vtab5:
        st.write("##### Diagram Schematics")
        for item in vault_view.get("diagrams", []):
            st.markdown(f"**{item.get('title')}**: {item.get('description')}")
        st.write("##### Intro/Outro Templates")
        for item in vault_view.get("intro_templates", []):
            st.markdown(f"**{item.get('topic')}**: {item.get('template')}")

# ==========================================
# TAB 4: MEMORY & GROUNDING
# ==========================================
with tab4:
    st.header("📚 AI Grounding Memory & Past Evaluations")
    st.markdown("Your past evaluations and model answers are stored here and automatically retrieved by the AI to maintain consistent grading strictness and style across sessions.")
    
    # Import db here just for the tab if needed, but better to import at the top. 
    # Since I can't easily replace the top and bottom at the exact same time without a single big replace, 
    # I'll import `from core import db` right here in the block.
    from core import db
    
    mtab1, mtab2 = st.tabs(["📝 Past Evaluations", "❓ Past Model Answers"])
    
    with mtab1:
        past_evals = db.get_all_evaluations()
        if not past_evals:
            st.info("No past evaluations found yet. Run an evaluation to start building memory!")
        else:
            for ev in past_evals:
                with st.expander(f"{ev['timestamp']} | {ev['subject']} | Score: {ev['max_marks']} Marks"):
                    st.write("**Question:**", ev.get("question_context") or "N/A")
                    st.markdown("**Evaluation Report:**")
                    st.markdown(ev["evaluation_text"])
    
    with mtab2:
        past_qas = db.get_all_model_answers()
        if not past_qas:
            st.info("No past model answers found yet.")
        else:
            for qa in past_qas:
                with st.expander(f"{qa['timestamp']} | {qa['subject']}"):
                    st.write("**Question/Doubt:**", qa["question"])
                    st.markdown("**Model Answer:**")
                    st.markdown(qa["answer_text"])
