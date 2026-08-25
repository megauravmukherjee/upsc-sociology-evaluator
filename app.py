import os
import json
import importlib
import streamlit as st
import config
importlib.reload(config)
from core.ocr_engine import process_pdf_or_image
from core.evaluator import evaluate_answer_script, load_vault
from core.qa_resolver import resolve_sociology_question
from core.topper_analyzer import analyze_and_extract_topper_copy

st.set_page_config(
    page_title="UPSC CSE Sociology Answer Evaluator & Vault",
    page_icon="🎓",
    layout="wide"
)

# Custom CSS styling
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
st.sidebar.title("🎓 UPSC Sociology AI")
st.sidebar.caption("Evaluator, Doubt Resolver & Topper Vault")

api_key = st.sidebar.text_input("Gemini API Key", type="password", value=os.environ.get("GEMINI_API_KEY", ""))

if not api_key:
    st.sidebar.warning("⚠️ Please enter your Gemini API key to run evaluation and OCR features.")
else:
    st.sidebar.success("✅ Gemini API Key detected.")

st.sidebar.divider()

# Load Vault Data for sidebar stats
vault_data = load_vault()
st.sidebar.markdown("### 📚 Sociology Vault Stats")
col_s1, col_s2 = st.sidebar.columns(2)
col_s1.metric("Definitions", len(vault_data.get("definitions", [])))
col_s2.metric("Thinker Quotes", len(vault_data.get("thinker_quotes", [])))

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
            st.markdown("#### Paper 1: Thinkers")
            for t in syl.get("paper_1", {}).get("topics", [])[3].get("thinkers", []):
                st.write(f"- **{t['name']}**: {', '.join(t['concepts'])}")
            st.markdown("#### Paper 2: Key Perspectives")
            for t in syl.get("paper_2", {}).get("topics", [])[0].get("thinkers", []):
                st.write(f"- **{t['name']}**: {t['approach']}")

# Main App Header
st.markdown('<div class="main-header">UPSC CSE Sociology Answer Evaluator</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">Evaluate handwritten answer scripts with Vision OCR, solve tricky Sociology doubts, and build a reusable Topper Strategy Vault.</div>', unsafe_allow_html=True)

tab1, tab2, tab3 = st.tabs([
    "📝 Module 1: Answer Script Evaluator",
    "❓ Module 2: Doubt & PYQ Resolver",
    "🏆 Module 3: Topper Vault & Analytics"
])

# ==========================================
# TAB 1: ANSWER SCRIPT EVALUATOR
# ==========================================
with tab1:
    st.header("📝 Handwritten Answer Script Evaluator")
    st.markdown("Upload your handwritten or typed PDF / Image answer scripts for OCR extraction and UPSC rubric evaluation.")
    
    col_up1, col_up2 = st.columns([2, 1])
    
    with col_up1:
        uploaded_file = st.file_uploader("Upload Answer Script (PDF, PNG, JPG, JPEG)", type=["pdf", "png", "jpg", "jpeg"])
        question_context = st.text_area("Question Text (Optional but recommended)", placeholder="Enter the exact question prompt here if available...")
    
    with col_up2:
        max_marks = st.selectbox("Maximum Marks", options=[10, 15, 20], index=1)
        st.info("💡 **Evaluation Rubric**: Assesses Demand of Question, Sociological Depth, Thinker Integration (Paper 1 & 2 synergy), Structural Balance, Value Addition, and Scored Marks.")

    if uploaded_file and st.button("🚀 Process OCR & Evaluate Script", type="primary", use_container_width=True):
        if not api_key:
            st.error("Please enter a valid Gemini API Key in the sidebar.")
        else:
            with st.status("Processing Answer Script...", expanded=True) as status:
                def update_progress(msg):
                    status.write(f"⏳ {msg}")

                file_bytes = uploaded_file.read()
                ocr_text, images = process_pdf_or_image(file_bytes, uploaded_file.name, api_key=api_key, progress_callback=update_progress)
                
                status.write("✅ Multimodal Vision OCR complete!")
                status.write("⏳ Evaluating script against UPSC Sociology Rubrics...")
                
                eval_report = evaluate_answer_script(ocr_text, question_context, max_marks=max_marks, api_key=api_key)
                status.update(label="✅ Answer Script Evaluation Complete!", state="complete", expanded=False)
            
            # Show OCR Preview
            with st.expander("🔍 View Extracted Text (OCR Result)", expanded=False):
                st.text_area("Extracted Answer Content", ocr_text, height=200)

            st.markdown("---")
            st.subheader("📊 UPSC Evaluation Report & Scorecard")
            st.markdown(eval_report)

# ==========================================
# TAB 2: DOUBT & PYQ RESOLVER
# ==========================================
with tab2:
    st.header("❓ Sociology Conceptual Doubt & PYQ Resolver")
    st.markdown("Ask direct questions or previous year questions (PYQs) for which you cannot find standard model answers.")
    
    user_q = st.text_area("Enter your Sociology Question / Doubt", placeholder="e.g. Discuss the relevance of Weber's Protestant Ethic thesis in understanding contemporary Indian capitalism.")
    
    col_q1, col_q2 = st.columns(2)
    with col_q1:
        word_limit = st.select_slider("Target Word Limit", options=[150, 250], value=250)
    with col_q2:
        paper_scope = st.selectbox("Target Paper", options=["Paper 1 (Foundations)", "Paper 2 (Indian Society)", "Both / Inter-linked"], index=2)

    if user_q and st.button("💡 Generate UPSC Model Answer", type="primary", use_container_width=True):
        if not api_key:
            st.error("Please enter a valid Gemini API Key in the sidebar.")
        else:
            with st.spinner("Synthesizing sociological literature, thinker matrices, and Indian case studies..."):
                ans_result = resolve_sociology_question(user_q, word_limit=word_limit, paper_type=paper_scope, api_key=api_key)
            
            st.markdown("---")
            st.subheader("✍️ Model Answer & Conceptual Framework")
            st.markdown(ans_result)

# ==========================================
# TAB 3: TOPPER VAULT & ANALYTICS
# ==========================================
with tab3:
    st.header("🏆 Topper Copy Learning & Reusable Bank")
    st.markdown("Upload topper answer copies (PDFs) to automatically extract reusable definitions, thinker quotes, diagram schematics, and intro/outro templates into your **Sociology Vault**.")
    
    topper_file = st.file_uploader("Upload Topper Answer PDF / Images", type=["pdf", "png", "jpg", "jpeg"], key="topper_upload")
    
    if topper_file and st.button("⚡ Extract & Learn Topper Strategy", type="primary"):
        if not api_key:
            st.error("Please enter a valid Gemini API Key in the sidebar.")
        else:
            with st.status("Analyzing Topper Copy...", expanded=True) as status:
                def update_progress(msg):
                    status.write(f"⏳ {msg}")

                file_bytes = topper_file.read()
                ocr_text, _ = process_pdf_or_image(file_bytes, topper_file.name, api_key=api_key, progress_callback=update_progress)
                status.write("⏳ Extracting definitions, quotes, diagrams & templates...")
                extracted_data = analyze_and_extract_topper_copy(ocr_text, api_key=api_key)
                status.update(label="🎉 Successfully analyzed Topper Copy!", state="complete", expanded=False)
            
            if "analysis_summary" in extracted_data:
                st.info(f"**Topper Copy Strategy Summary**: {extracted_data['analysis_summary']}")
            
            t_col1, t_col2 = st.columns(2)
            with t_col1:
                st.subheader("📌 Extracted Definitions")
                for d in extracted_data.get("definitions", []):
                    st.markdown(f"- **{d.get('term')}** ({d.get('author')}): *{d.get('definition')}*")
                
                st.subheader("💡 Extracted Thinker Quotes")
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
    st.subheader("📖 Browse Complete Sociology Vault Repository")
    
    vault_view = load_vault()
    vault_tab1, vault_tab2, vault_tab3, vault_tab4 = st.tabs(["Definitions", "Thinker Quotes", "Intro/Outro Templates", "Diagram Schematics"])
    
    with vault_tab1:
        for item in vault_view.get("definitions", []):
            st.markdown(f"#### 🔹 {item.get('term')} ({item.get('author')})")
            st.write(item.get('definition'))
            st.caption(f"Context: {item.get('reusable_context', '')}")
            st.divider()
            
    with vault_tab2:
        for item in vault_view.get("thinker_quotes", []):
            st.markdown(f"#### 💬 {item.get('thinker')}")
            st.write(f"*{item.get('quote')}*")
            st.caption(f"Usage Context: {item.get('context', '')}")
            st.divider()

    with vault_tab3:
        st.write("##### Introduction Templates")
        for item in vault_view.get("intro_templates", []):
            st.markdown(f"**{item.get('topic')}**: {item.get('template')}")
        st.write("##### Conclusion Templates")
        for item in vault_view.get("outro_templates", []):
            st.markdown(f"**{item.get('topic')}**: {item.get('template')}")

    with vault_tab4:
        for item in vault_view.get("diagrams", []):
            st.markdown(f"#### 📊 {item.get('title')}")
            st.write(item.get('description'))
            st.caption(f"Reusable Context: {item.get('reusable_context', '')}")
            st.divider()
