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
    page_title="UPSC CSE Mains AI Evaluator & Strategy Hub",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Styling to match Google Stitch Dark Obsidian Spec
st.markdown("""
<link href="https://fonts.googleapis.com/css2?family=Geist:wght@300;400;500;600;700&display=swap" rel="stylesheet"/>
<link href="https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:wght,FILL@100..700,0..1&display=swap" rel="stylesheet"/>

<style>
    /* Hide Default Streamlit Chrome for Clean App Experience */
    header[data-testid="stHeader"] { display: none !important; }
    footer { display: none !important; }
    #MainMenu { visibility: hidden; }
    
    /* Reset & Geist Font */
    html, body, [class*="st-"] {
        font-family: 'Geist', sans-serif !important;
        background-color: #09090b !important;
        color: #fafafa !important;
    }
    
    .stApp {
        background-color: #09090b !important;
    }
    
    .block-container {
        padding: 1.5rem 2rem 2rem 2rem !important;
        max-width: 1600px !important;
    }
    
    /* Sidebar Styling */
    div[data-testid="stSidebar"] {
        background-color: #0c0c0f !important;
        border-right: 1px solid #18181b !important;
        width: 260px !important;
    }
    
    /* Glass Panel Cards */
    .glass-panel {
        background: rgba(18, 18, 21, 0.7) !important;
        backdrop-filter: blur(12px) !important;
        -webkit-backdrop-filter: blur(12px) !important;
        border: 1px solid #27272a !important;
        border-radius: 12px;
        padding: 20px;
    }
    
    /* Metric Cards */
    .metric-card {
        background: #121215;
        border: 1px solid #27272a;
        border-radius: 12px;
        padding: 16px;
        display: flex;
        flex-direction: column;
    }
    
    /* Thinker & Article Mapping Cards */
    .thinker-card {
        background: #121215;
        border: 1px solid #27272a;
        border-radius: 10px;
        padding: 14px;
    }
    
    /* Custom Input Fields */
    .stTextInput input, .stTextArea textarea, .stSelectbox select {
        background-color: #121215 !important;
        color: #fafafa !important;
        border: 1px solid #27272a !important;
        border-radius: 8px !important;
    }
    
    .stButton button {
        border-radius: 8px !important;
        font-weight: 600 !important;
    }
    
    /* Material Symbol Styling */
    .ms {
        font-family: 'Material Symbols Outlined' !important;
        font-weight: normal;
        font-style: normal;
        display: inline-block;
        line-height: 1;
        text-transform: none;
        letter-spacing: normal;
        word-wrap: normal;
        white-space: nowrap;
        direction: ltr;
    }
</style>
""", unsafe_allow_html=True)

# Sidebar - Matching Stitch Screenshot Nav
st.sidebar.markdown("""
<div style="padding: 10px 0 20px 0;">
    <div style="font-size: 1.35rem; font-weight: 700; color: #a78bfa; letter-spacing: -0.02em;">UPSC Mains Master</div>
    
    <div style="display: flex; items-center; gap: 12px; margin-top: 16px; padding: 10px; background: #121215; border: 1px solid #27272a; border-radius: 10px;">
        <div style="width: 38px; height: 38px; border-radius: 50%; background: #18181b; border: 1px solid #3f3f46; display: flex; align-items: center; justify-content: center; shrink-0;">
            <span class="ms" style="color: #a1a1aa; font-size: 20px;">person</span>
        </div>
        <div style="display: flex; flex-direction: column;">
            <span style="font-size: 0.88rem; font-weight: 600; color: #fafafa;">IAS Aspirant</span>
            <span style="font-size: 0.75rem; color: #a1a1aa;">Mains 2024 / All Subjects</span>
        </div>
    </div>
</div>

<div style="display: flex; flex-direction: column; gap: 6px; margin-bottom: 24px;">
    <div style="display: flex; align-items: center; gap: 12px; padding: 10px 12px; color: #a1a1aa; border-radius: 8px;">
        <span class="ms" style="font-size: 20px;">dashboard</span>
        <span style="font-size: 0.9rem; font-weight: 500;">Home</span>
    </div>
    <div style="display: flex; align-items: center; gap: 12px; padding: 10px 12px; color: #a1a1aa; border-radius: 8px;">
        <span class="ms" style="font-size: 20px;">quiz</span>
        <span style="font-size: 0.9rem; font-weight: 500;">Doubt Tracker</span>
    </div>
    <div style="display: flex; align-items: center; gap: 12px; padding: 10px 12px; color: #a1a1aa; border-radius: 8px;">
        <span class="ms" style="font-size: 20px;">menu_book</span>
        <span style="font-size: 0.9rem; font-weight: 500;">UPSC Hub & Vault</span>
    </div>
    <!-- Active Item -->
    <div style="display: flex; align-items: center; gap: 12px; padding: 10px 12px; color: #c4b5fd; background: #1e1e22; border-radius: 8px; font-weight: 700; border-left: 3px solid #7c3aed;">
        <span class="ms" style="font-size: 20px; color: #c4b5fd;">fact_check</span>
        <span style="font-size: 0.9rem;">Evaluation Deep-Dive</span>
    </div>
    <div style="display: flex; align-items: center; gap: 12px; padding: 10px 12px; color: #a1a1aa; border-radius: 8px;">
        <span class="ms" style="font-size: 20px;">settings</span>
        <span style="font-size: 0.9rem; font-weight: 500;">Settings</span>
    </div>
</div>
""", unsafe_allow_html=True)

api_key = st.sidebar.text_input("Gemini API Key", type="password", value=os.environ.get("GEMINI_API_KEY", ""))

if not api_key:
    st.sidebar.warning("⚠️ Enter Gemini API key to run OCR & evaluation.")
else:
    st.sidebar.success("✅ Gemini API Key Active")

st.sidebar.divider()

# Load Vault Data for sidebar stats
vault_data = load_vault()
st.sidebar.markdown("### 📚 UPSC Vault Stats")
col_s1, col_s2 = st.sidebar.columns(2)
col_s1.metric("Definitions & Articles", len(vault_data.get("definitions", [])))
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
            st.markdown("#### GS 1, GS 2, GS 3, GS 4 & Essay")
            for sub, info in syl.items():
                st.write(f"- **{info.get('title')}**")

# Upgrade Button on Sidebar
st.sidebar.markdown("""
<div style="margin-top: 20px;">
    <button style="width: 100%; padding: 10px; background: rgba(124, 58, 237, 0.12); border: 1px solid rgba(167, 139, 250, 0.4); color: #c4b5fd; border-radius: 8px; font-weight: 600; font-size: 0.85rem; cursor: pointer;">
        Upgrade to Premium
    </button>
</div>
""", unsafe_allow_html=True)

# Main Canvas Header with Subject Switcher Selector
st.markdown("""
<div style="display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid #27272a; padding-bottom: 18px; margin-bottom: 20px;">
    <div>
        <h1 style="font-size: 1.85rem; font-weight: 700; color: #fafafa; margin: 0; display: flex; align-items: center; gap: 12px;">
            <span class="ms" style="color: #a78bfa; font-size: 32px;">plagiarism</span>
            UPSC Mains Evaluation Deep-Dive
        </h1>
        <p style="color: #a1a1aa; font-size: 0.88rem; margin: 6px 0 0 0;">Evaluation Engine • GS 1 • GS 2 • GS 3 • GS 4 Ethics • Essay • Sociology Optional</p>
    </div>
    <div style="display: flex; gap: 12px;">
        <button style="padding: 8px 16px; background: #121215; border: 1px solid #27272a; color: #fafafa; border-radius: 8px; font-size: 0.85rem; display: flex; align-items: center; gap: 8px; cursor: pointer;">
            <span class="ms" style="font-size: 18px;">download</span> Export PDF
        </button>
        <button style="padding: 8px 18px; background: #7c3aed; border: none; color: #ffffff; border-radius: 8px; font-weight: 600; font-size: 0.85rem; display: flex; align-items: center; gap: 8px; box-shadow: 0 0 15px rgba(124, 58, 237, 0.4); cursor: pointer;">
            <span class="ms" style="font-size: 18px;">share</span> Share Report
        </button>
    </div>
</div>
""", unsafe_allow_html=True)

# Subject Switcher Control
col_sub1, col_sub2 = st.columns([1, 3])
with col_sub1:
    selected_subject = st.selectbox(
        "🎯 Select UPSC Mains Target Subject",
        options=["Sociology Optional", "GS 1", "GS 2", "GS 3", "GS 4 (Ethics)", "Essay Evaluator"],
        index=0
    )
with col_sub2:
    st.markdown(f"""
    <div style="padding: 10px 16px; background: #121215; border: 1px solid #27272a; border-radius: 8px; display: flex; align-items: center; gap: 10px; margin-top: 26px;">
        <span class="ms" style="color: #a78bfa; font-size: 20px;">verified</span>
        <span style="font-size: 0.85rem; color: #a1a1aa;">Active Evaluator Rubric: <strong style="color: #fafafa;">{selected_subject}</strong> • Grounded in UPSC Marking Precedents & Topper Vault</span>
    </div>
    """, unsafe_allow_html=True)

# Tab Navigation for Modules
tab1, tab2, tab3 = st.tabs([
    "📄 Script Evaluation & OCR Deep-Dive",
    "❓ Doubt Tracker & Model Answers",
    "🏆 UPSC Hub & Topper Vault"
])

# ==========================================
# TAB 1: EVALUATION DEEP-DIVE
# ==========================================
with tab1:
    col_up1, col_up2 = st.columns([2, 1])
    with col_up1:
        uploaded_file = st.file_uploader(f"Upload {selected_subject} Answer Script (PDF/Image)", type=["pdf", "png", "jpg", "jpeg"])
        question_context = st.text_area("Question Text (Optional but recommended)", placeholder=f"Enter exact {selected_subject} question prompt...")
    with col_up2:
        max_marks = st.selectbox("Maximum Marks", options=[10, 15, 20, 125, 250], index=2)

    if uploaded_file and st.button(f"🚀 Evaluate {selected_subject} Script", type="primary", use_container_width=True):
        if not api_key:
            st.error("Please enter a valid Gemini API Key in the sidebar.")
        else:
            with st.status(f"Evaluating {selected_subject} Script...", expanded=True) as status:
                def update_progress(msg):
                    status.write(f"⏳ {msg}")

                file_bytes = uploaded_file.read()
                ocr_text, images = process_pdf_or_image(file_bytes, uploaded_file.name, api_key=api_key, progress_callback=update_progress)
                status.write("✅ Multimodal Vision OCR complete!")
                status.write(f"⏳ Benchmarking against {selected_subject} UPSC Rubrics & Topper Vault...")
                eval_report = evaluate_answer_script(ocr_text, question_context, max_marks=max_marks, subject=selected_subject, api_key=api_key)
                status.update(label=f"✅ {selected_subject} Evaluation Complete!", state="complete", expanded=False)

    st.markdown("---")

    # Split View Layout (5/12 Left Column, 7/12 Right Column)
    col_left, col_right = st.columns([5, 7])

    # Left Column: Original Script View
    with col_left:
        st.markdown("""
        <div class="glass-panel" style="padding: 0; overflow: hidden;">
            <div style="padding: 14px 18px; border-bottom: 1px solid #27272a; background: rgba(18, 18, 21, 0.8); display: flex; justify-content: space-between; align-items: center;">
                <div style="font-weight: 600; font-size: 0.95rem; color: #fafafa; display: flex; align-items: center; gap: 8px;">
                    <span class="ms" style="color: #a1a1aa; font-size: 20px;">document_scanner</span>
                    Original Script View
                </div>
                <div style="display: flex; gap: 8px; color: #a1a1aa;">
                    <span class="ms" style="font-size: 18px; cursor: pointer;">zoom_in</span>
                    <span class="ms" style="font-size: 18px; cursor: pointer;">zoom_out</span>
                </div>
            </div>
            
            <div style="padding: 24px; background: #0a0a0c; min-height: 650px;">
                <div style="text-align: right; font-size: 0.75rem; color: #a1a1aa; margin-bottom: 16px;">Page 1/4</div>
                <h3 style="font-size: 1.15rem; font-weight: 700; color: #fafafa; margin-bottom: 14px; line-height: 1.4;">
                    Sample OCR Script Preview
                </h3>
                <p style="color: #a1a1aa; font-size: 0.92rem; line-height: 1.6; margin-bottom: 16px;">
                    Upload an answer sheet PDF/image above to transcribe handwritten text and run full UPSC examiner evaluation...
                </p>
            </div>
        </div>
        """, unsafe_allow_html=True)

    # Right Column: Evaluation & Analytics (4 Metric Boxes + Detailed Report)
    with col_right:
        st.markdown(f"""
        <div style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; margin-bottom: 20px;">
            <div class="metric-card">
                <span style="font-size: 0.8rem; color: #a1a1aa; margin-bottom: 6px;">Total Marks</span>
                <div style="display: flex; align-items: baseline; gap: 4px;">
                    <span style="font-size: 1.85rem; font-weight: 700; color: #34d399;">14.5</span>
                    <span style="font-size: 0.85rem; color: #a1a1aa;">/ 20</span>
                </div>
            </div>
            
            <div class="metric-card">
                <span style="font-size: 0.8rem; color: #a1a1aa; margin-bottom: 6px;">Structure & Flow</span>
                <div style="display: flex; align-items: baseline; gap: 4px;">
                    <span style="font-size: 1.85rem; font-weight: 700; color: #a78bfa;">8.5</span>
                    <span style="font-size: 0.85rem; color: #a1a1aa;">/ 10</span>
                </div>
            </div>

            <div class="metric-card">
                <span style="font-size: 0.8rem; color: #a1a1aa; margin-bottom: 6px;">Fact / Article Density</span>
                <div style="margin-top: 8px;">
                    <div style="width: 100%; height: 6px; background: #27272a; border-radius: 9999px; overflow: hidden; margin-bottom: 4px;">
                        <div style="width: 80%; height: 100%; background: #a78bfa; border-radius: 9999px;"></div>
                    </div>
                    <span style="font-size: 0.75rem; color: #a1a1aa;">High</span>
                </div>
            </div>

            <div class="metric-card">
                <span style="font-size: 0.8rem; color: #a1a1aa; margin-bottom: 6px;">Topper Similarity</span>
                <div style="display: flex; align-items: center; gap: 6px; margin-top: 4px;">
                    <span style="font-size: 1.65rem; font-weight: 700; color: #34d399;">84%</span>
                    <span class="ms" style="color: #34d399; font-size: 18px;">trending_up</span>
                </div>
            </div>
        </div>

        <div class="glass-panel">
            <div style="display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid #27272a; padding-bottom: 12px; margin-bottom: 16px;">
                <div style="font-weight: 600; font-size: 1.05rem; color: #fafafa; display: flex; align-items: center; gap: 8px;">
                    <span class="ms" style="color: #a78bfa; font-size: 22px;">analytics</span>
                    Detailed {selected_subject} Evaluator Report
                </div>
                <span style="padding: 3px 10px; background: rgba(52, 211, 153, 0.15); color: #34d399; border: 1px solid rgba(52, 211, 153, 0.3); border-radius: 4px; font-size: 0.75rem; font-weight: 600;">
                    AI Evaluated
                </span>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        if 'eval_report' in locals():
            st.markdown(eval_report)
        else:
            st.info(f"Upload a {selected_subject} answer sheet script above and click 'Evaluate {selected_subject} Script' to generate a full evaluation scorecard!")

# ==========================================
# TAB 2: DOUBT TRACKER
# ==========================================
with tab2:
    st.header(f"❓ {selected_subject} Doubt Tracker & Model Answer Generator")
    user_q = st.text_area(f"Enter your {selected_subject} Question / Doubt", placeholder=f"Enter any PYQ or tricky question from {selected_subject}...")
    
    col_q1, col_q2 = st.columns(2)
    with col_q1:
        word_limit = st.select_slider("Target Word Limit", options=[150, 250, 1000], value=250)
    with col_q2:
        paper_scope = st.selectbox("Subject Scope", options=["GS 1", "GS 2", "GS 3", "GS 4 (Ethics)", "Essay", "Sociology Optional"], index=0)

    if user_q and st.button(f"💡 Generate {selected_subject} Model Answer", type="primary", use_container_width=True):
        if not api_key:
            st.error("Please enter a valid Gemini API Key in the sidebar.")
        else:
            with st.spinner(f"Synthesizing {selected_subject} model answer..."):
                ans_result = resolve_sociology_question(user_q, word_limit=word_limit, paper_type=paper_scope, api_key=api_key)
            st.markdown(ans_result)

# ==========================================
# TAB 3: UPSC HUB & VAULT
# ==========================================
with tab3:
    st.header(f"🏆 {selected_subject} Hub & Topper Vault")
    topper_file = st.file_uploader(f"Upload Topper Answer PDF for {selected_subject}", type=["pdf", "png", "jpg", "jpeg"], key="topper_upload_multi")
    if topper_file and st.button(f"⚡ Extract {selected_subject} Strategy", type="primary"):
        if not api_key:
            st.error("Please enter Gemini API Key.")
        else:
            with st.status(f"Analyzing {selected_subject} Topper Copy...", expanded=True) as status:
                file_bytes = topper_file.read()
                ocr_text, _ = process_pdf_or_image(file_bytes, topper_file.name, api_key=api_key)
                extracted_data = analyze_and_extract_topper_copy(ocr_text, api_key=api_key)
                status.update(label="🎉 Strategy Extracted!", state="complete", expanded=False)
            st.write(extracted_data)

    st.markdown("---")
    st.subheader("📖 Multi-Subject UPSC Vault Repository")
    vault_view = load_vault()
    vtab1, vtab2, vtab3, vtab4 = st.tabs(["Articles & Definitions", "Quotes & Precedents", "Intro/Outro Hooks", "Diagram Schematics"])
    
    with vtab1:
        for item in vault_view.get("definitions", []):
            st.markdown(f"**{item.get('term')}** ({item.get('author')}): {item.get('definition')}")
            st.divider()
    with vtab2:
        for item in vault_view.get("thinker_quotes", []):
            st.markdown(f"**{item.get('thinker')}**: \"{item.get('quote')}\"")
            st.divider()
    with vtab3:
        for item in vault_view.get("intro_templates", []):
            st.markdown(f"**{item.get('topic')}**: {item.get('template')}")
            st.divider()
    with vtab4:
        for item in vault_view.get("diagrams", []):
            st.markdown(f"**{item.get('title')}**: {item.get('description')}")
            st.divider()
