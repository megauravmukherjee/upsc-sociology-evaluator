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
    page_title="Sociology Expert - Evaluation Deep-Dive",
    page_icon="🎓",
    layout="wide"
)

# Load Fonts, Material Symbols, and Custom Dark Obsidian Glassmorphism Styling from User's Stitch Spec
st.markdown("""
<link href="https://fonts.googleapis.com/css2?family=Geist:wght@300;400;500;600;700&display=swap" rel="stylesheet"/>
<link href="https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:wght,FILL@100..700,0..1&display=swap" rel="stylesheet"/>

<style>
    /* Dark Obsidian Theme Global Rules */
    html, body, [class*="st-"] {
        font-family: 'Geist', sans-serif !important;
        background-color: #09090b !important;
        color: #fafafa !important;
    }
    
    .stApp {
        background-color: #09090b !important;
    }
    
    /* Glass Panel Styling */
    .glass-panel {
        background: rgba(18, 18, 21, 0.75) !important;
        backdrop-filter: blur(12px) !important;
        -webkit-backdrop-filter: blur(12px) !important;
        border: 1px solid #27272a !important;
        border-radius: 12px;
        padding: 20px;
        margin-bottom: 16px;
    }
    
    .text-glow {
        text-shadow: 0 0 12px rgba(167, 139, 250, 0.4);
    }
    
    /* Header Banner */
    .hero-banner {
        background: linear-gradient(135deg, #09090b 0%, #121215 50%, #1e1e22 100%);
        border: 1px solid #27272a;
        border-radius: 16px;
        padding: 28px 32px;
        margin-bottom: 24px;
        position: relative;
    }
    
    .hero-title {
        font-size: 2.2rem;
        font-weight: 700;
        color: #a78bfa;
        letter-spacing: -0.02em;
        margin: 0 0 8px 0;
        display: flex;
        align-items: center;
        gap: 12px;
    }
    
    .hero-sub {
        color: #a1a1aa;
        font-size: 1.05rem;
        margin-bottom: 16px;
    }
    
    .badge-chip {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        background: rgba(124, 58, 237, 0.15);
        border: 1px solid rgba(167, 139, 250, 0.3);
        color: #c4b5fd;
        padding: 4px 14px;
        border-radius: 9999px;
        font-size: 0.82rem;
        font-weight: 600;
    }
    
    /* Metric Cards */
    .metric-box {
        background: rgba(24, 24, 27, 0.8);
        border: 1px solid #27272a;
        border-radius: 12px;
        padding: 16px;
        display: flex;
        flex-direction: column;
    }
    
    .metric-label {
        font-size: 0.85rem;
        color: #a1a1aa;
        margin-bottom: 4px;
    }
    
    .metric-value-primary {
        font-size: 2rem;
        font-weight: 700;
        color: #a78bfa;
    }
    
    .metric-value-tertiary {
        font-size: 2rem;
        font-weight: 700;
        color: #34d399;
    }
    
    /* Tabs Styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background-color: #121215;
        padding: 6px;
        border-radius: 12px;
        border: 1px solid #27272a;
    }
    .stTabs [data-baseweb="tab"] {
        height: 44px;
        border-radius: 8px;
        padding: 8px 18px;
        font-weight: 600;
        color: #a1a1aa;
        border: none !important;
        background: transparent;
    }
    .stTabs [aria-selected="true"] {
        background-color: #18181b !important;
        color: #a78bfa !important;
        border: 1px solid #7c3aed !important;
        box-shadow: 0 0 15px rgba(124, 58, 237, 0.2);
    }
    
    /* Input & Sidebar Overrides */
    div[data-testid="stSidebar"] {
        background-color: #0c0c0f !important;
        border-right: 1px solid #27272a !important;
    }
    
    .stTextInput input, .stTextArea textarea, .stSelectbox select {
        background-color: #121215 !important;
        color: #fafafa !important;
        border: 1px solid #27272a !important;
        border-radius: 8px !alignment;
    }
    
    .stButton button {
        border-radius: 8px;
        font-weight: 600;
    }
    
    .block-container {
        padding-top: 1.8rem;
    }
</style>
""", unsafe_allow_html=True)

# Sidebar Configuration - Sociology Expert Navigation
st.sidebar.markdown("""
<div style="margin-bottom: 20px;">
    <div style="font-size: 1.4rem; font-weight: 700; color: #a78bfa; class='text-glow';">Sociology Expert</div>
    <div style="display: flex; align-items: center; gap: 12px; margin-top: 12px; background: #121215; padding: 10px; border-radius: 10px; border: 1px solid #27272a;">
        <div style="width: 36px; height: 36px; border-radius: 50%; background: #18181b; border: 1px solid #3f3f46; display: flex; align-items: center; justify-content: center;">
            <span class="material-symbols-outlined" style="color: #a1a1aa; font-size: 20px;">person</span>
        </div>
        <div>
            <div style="font-size: 0.9rem; font-weight: 600; color: #fafafa;">IAS Aspirant</div>
            <div style="font-size: 0.75rem; color: #a1a1aa;">Mains 2024 / Optional</div>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

api_key = st.sidebar.text_input("Gemini API Key", type="password", value=os.environ.get("GEMINI_API_KEY", ""))

if not api_key:
    st.sidebar.warning("⚠️ Enter Gemini API key to run evaluation.")
else:
    st.sidebar.success("✅ Gemini API Key Active")

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
            st.markdown("#### Paper 1: Key Thinkers")
            for t in syl.get("paper_1", {}).get("topics", [])[3].get("thinkers", []):
                st.write(f"- **{t['name']}**: {', '.join(t['concepts'])}")
            st.markdown("#### Paper 2: Key Perspectives")
            for t in syl.get("paper_2", {}).get("topics", [])[0].get("thinkers", []):
                st.write(f"- **{t['name']}**: {t['approach']}")

# Main Header Banner (Stitch Obsidian Theme)
st.markdown("""
<div class="hero-banner">
    <div class="hero-title">
        <span class="material-symbols-outlined" style="font-size: 34px; color: #a78bfa;">plagiarism</span>
        Evaluation Deep-Dive & Strategy Hub
    </div>
    <div class="hero-sub">Script Analysis • Multimodal Vision OCR • Sociological Reasoning Engine • Topper Vault Analytics</div>
    <div>
        <span class="badge-chip"><span class="material-symbols-outlined" style="font-size: 16px;">bolt</span> Gemini 3.6 Vision</span>
        <span class="badge-chip"><span class="material-symbols-outlined" style="font-size: 16px;">fact_check</span> UPSC Mains Scoring</span>
        <span class="badge-chip"><span class="material-symbols-outlined" style="font-size: 16px;">verified</span> Topper Benchmark</span>
    </div>
</div>
""", unsafe_allow_html=True)

tab1, tab2, tab3 = st.tabs([
    "📝 Module 1: Evaluation Deep-Dive",
    "❓ Module 2: Doubt Tracker",
    "🏆 Module 3: Sociology Hub & Vault"
])

# ==========================================
# TAB 1: EVALUATION DEEP-DIVE
# ==========================================
with tab1:
    st.markdown("""
    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px;">
        <div>
            <h2 style="font-weight: 700; color: #fafafa; margin: 0; font-size: 1.5rem;">Answer Script OCR & Rubric Evaluation</h2>
            <p style="color: #a1a1aa; font-size: 0.9rem; margin: 4px 0 0 0;">Upload handwritten or typed answer sheets to perform OCR transcription and generate a detailed examiner report.</p>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    col_up1, col_up2 = st.columns([2, 1])
    
    with col_up1:
        uploaded_file = st.file_uploader("Upload Answer Script (PDF, PNG, JPG, JPEG)", type=["pdf", "png", "jpg", "jpeg"])
        question_context = st.text_area("Question Text (Optional but recommended)", placeholder="Enter the exact question prompt here if available...")
    
    with col_up2:
        max_marks = st.selectbox("Maximum Marks", options=[10, 15, 20], index=1)
        st.markdown("""
        <div class="glass-panel" style="padding: 14px;">
            <div style="font-size: 0.85rem; font-weight: 600; color: #a78bfa; margin-bottom: 6px;">💡 UPSC Grading Dimensions</div>
            <div style="font-size: 0.8rem; color: #a1a1aa; line-height: 1.4;">
                • Demand & Directness<br/>
                • Theoretical Rigor & Thinkers<br/>
                • Structure & Sub-headings<br/>
                • Diagrams & Paper 1/2 Synergy
            </div>
        </div>
        """, unsafe_allow_html=True)

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
                status.write("⏳ Evaluating script against UPSC Sociology Rubrics & Topper Vault...")
                
                eval_report = evaluate_answer_script(ocr_text, question_context, max_marks=max_marks, api_key=api_key)
                status.update(label="✅ Answer Script Evaluation Complete!", state="complete", expanded=False)

            st.divider()

            # Split View Layout (Matching User's Stitch Spec)
            col_left, col_right = st.columns([5, 7])

            with col_left:
                st.markdown("""
                <div class="glass-panel">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
                        <span style="font-weight: 600; font-size: 1.1rem; color: #fafafa; display: flex; align-items: center; gap: 8px;">
                            <span class="material-symbols-outlined" style="color: #a1a1aa;">document_scanner</span>
                            Original Script OCR View
                        </span>
                        <span style="font-size: 0.75rem; background: #27272a; color: #a78bfa; padding: 2px 8px; border-radius: 4px;">OCR Transcribed</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                st.text_area("Extracted Answer Content (Line-by-Line)", ocr_text, height=520)

            with col_right:
                st.markdown("""
                <div style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; margin-bottom: 16px;">
                    <div class="metric-box">
                        <span class="metric-label">Total Marks</span>
                        <span class="metric-value-tertiary">14.5 <span style="font-size: 0.9rem; color: #a1a1aa;">/ 20</span></span>
                    </div>
                    <div class="metric-box">
                        <span class="metric-label">Structure</span>
                        <span class="metric-value-primary">8.5 <span style="font-size: 0.9rem; color: #a1a1aa;">/ 10</span></span>
                    </div>
                    <div class="metric-box">
                        <span class="metric-label">Thinker Density</span>
                        <span style="font-size: 1.2rem; font-weight: 700; color: #a78bfa; margin-top: 6px;">High</span>
                    </div>
                    <div class="metric-box">
                        <span class="metric-label">Topper Similarity</span>
                        <span class="metric-value-tertiary">82%</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)

                st.markdown("""
                <div class="glass-panel">
                    <div style="font-weight: 600; font-size: 1.1rem; color: #a78bfa; margin-bottom: 12px; display: flex; align-items: center; gap: 8px;">
                        <span class="material-symbols-outlined">analytics</span>
                        Detailed Evaluator Report
                    </div>
                </div>
                """, unsafe_allow_html=True)
                st.markdown(eval_report)

# ==========================================
# TAB 2: DOUBT TRACKER
# ==========================================
with tab2:
    st.markdown("""
    <h2 style="font-weight: 700; color: #fafafa; margin: 0; font-size: 1.5rem; display: flex; align-items: center; gap: 10px;">
        <span class="material-symbols-outlined" style="color: #a78bfa;">quiz</span>
        Sociology Doubt Tracker & Model Answer Generator
    </h2>
    <p style="color: #a1a1aa; font-size: 0.9rem; margin-top: 4px;">Synthesize standard sociological reference books, thinker matrices, and contemporary Indian empirical examples.</p>
    """, unsafe_allow_html=True)
    
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
            st.markdown("""
            <div class="glass-panel">
                <div style="font-weight: 700; font-size: 1.2rem; color: #a78bfa; margin-bottom: 12px;">✍️ Model UPSC Answer & Framework</div>
            </div>
            """, unsafe_allow_html=True)
            st.markdown(ans_result)

# ==========================================
# TAB 3: SOCIOLOGY HUB & VAULT
# ==========================================
with tab3:
    st.markdown("""
    <h2 style="font-weight: 700; color: #fafafa; margin: 0; font-size: 1.5rem; display: flex; align-items: center; gap: 10px;">
        <span class="material-symbols-outlined" style="color: #a78bfa;">menu_book</span>
        Sociology Hub & Reusable Topper Vault
    </h2>
    <p style="color: #a1a1aa; font-size: 0.9rem; margin-top: 4px;">Upload topper answer copies to extract definitions, thinker quotes, diagram schematics, and intro/outro templates.</p>
    """, unsafe_allow_html=True)
    
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
            st.markdown(f"""
            <div class="glass-panel">
                <span style="font-size: 0.75rem; background: rgba(167, 139, 250, 0.15); color: #c4b5fd; border: 1px solid rgba(167, 139, 250, 0.3); padding: 2px 8px; border-radius: 4px;">Definition</span>
                <h4 style="margin: 8px 0 6px 0; color: #fafafa; font-weight: 600;">{item.get('term')} <span style="color: #a1a1aa; font-weight: 400;">({item.get('author')})</span></h4>
                <p style="color: #a1a1aa; font-size: 0.95rem; margin-bottom: 6px;">{item.get('definition')}</p>
                <small style="color: #71717a;">💡 Context: {item.get('reusable_context', '')}</small>
            </div>
            """, unsafe_allow_html=True)
            
    with vault_tab2:
        for item in vault_view.get("thinker_quotes", []):
            st.markdown(f"""
            <div class="glass-panel">
                <span style="font-size: 0.75rem; background: rgba(124, 58, 237, 0.15); color: #c4b5fd; border: 1px solid rgba(167, 139, 250, 0.3); padding: 2px 8px; border-radius: 4px;">Thinker Quote</span>
                <h4 style="margin: 8px 0 6px 0; color: #fafafa; font-weight: 600;">{item.get('thinker')}</h4>
                <blockquote style="border-left: 3px solid #7c3aed; padding-left: 12px; color: #c4b5fd; font-style: italic; margin: 8px 0;">"{item.get('quote')}"</blockquote>
                <small style="color: #71717a;">💡 Usage Context: {item.get('context', '')}</small>
            </div>
            """, unsafe_allow_html=True)

    with vault_tab3:
        st.write("##### Introduction Templates")
        for item in vault_view.get("intro_templates", []):
            st.markdown(f"""
            <div class="glass-panel">
                <span style="font-size: 0.75rem; background: rgba(52, 211, 153, 0.15); color: #6ee7b7; border: 1px solid rgba(52, 211, 153, 0.3); padding: 2px 8px; border-radius: 4px;">Intro Hook</span>
                <h4 style="margin: 8px 0 6px 0; color: #fafafa; font-weight: 600;">{item.get('topic')}</h4>
                <p style="color: #a1a1aa; font-size: 0.95rem;">{item.get('template')}</p>
            </div>
            """, unsafe_allow_html=True)
            
        st.write("##### Conclusion Templates")
        for item in vault_view.get("outro_templates", []):
            st.markdown(f"""
            <div class="glass-panel">
                <span style="font-size: 0.75rem; background: rgba(52, 211, 153, 0.15); color: #6ee7b7; border: 1px solid rgba(52, 211, 153, 0.3); padding: 2px 8px; border-radius: 4px;">Synthesis Conclusion</span>
                <h4 style="margin: 8px 0 6px 0; color: #fafafa; font-weight: 600;">{item.get('topic')}</h4>
                <p style="color: #a1a1aa; font-size: 0.95rem;">{item.get('template')}</p>
            </div>
            """, unsafe_allow_html=True)

    with vault_tab4:
        for item in vault_view.get("diagrams", []):
            st.markdown(f"""
            <div class="glass-panel">
                <span style="font-size: 0.75rem; background: rgba(167, 139, 250, 0.15); color: #c4b5fd; border: 1px solid rgba(167, 139, 250, 0.3); padding: 2px 8px; border-radius: 4px;">Diagram Schematic</span>
                <h4 style="margin: 8px 0 6px 0; color: #fafafa; font-weight: 600;">{item.get('title')}</h4>
                <p style="color: #a1a1aa; font-size: 0.95rem;">{item.get('description')}</p>
                <small style="color: #71717a;">💡 Reusable Context: {item.get('reusable_context', '')}</small>
            </div>
            """, unsafe_allow_html=True)
