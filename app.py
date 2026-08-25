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
    page_title="Module 1: Evaluation Deep-Dive - Sociology Expert",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Styling to match the Google Stitch Screenshot 100%
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
    
    /* Thinker Mapping Cards */
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
    <div style="font-size: 1.35rem; font-weight: 700; color: #a78bfa; letter-spacing: -0.02em;">Sociology Expert</div>
    
    <div style="display: flex; items-center; gap: 12px; margin-top: 16px; padding: 10px; background: #121215; border: 1px solid #27272a; border-radius: 10px;">
        <div style="width: 38px; height: 38px; border-radius: 50%; background: #18181b; border: 1px solid #3f3f46; display: flex; align-items: center; justify-content: center; shrink-0;">
            <span class="ms" style="color: #a1a1aa; font-size: 20px;">person</span>
        </div>
        <div style="display: flex; flex-direction: column;">
            <span style="font-size: 0.88rem; font-weight: 600; color: #fafafa;">IAS Aspirant</span>
            <span style="font-size: 0.75rem; color: #a1a1aa;">Mains 2024</span>
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
        <span style="font-size: 0.9rem; font-weight: 500;">Sociology Hub</span>
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

# Upgrade Button on Sidebar
st.sidebar.markdown("""
<div style="margin-top: 20px;">
    <button style="width: 100%; padding: 10px; background: rgba(124, 58, 237, 0.12); border: 1px solid rgba(167, 139, 250, 0.4); color: #c4b5fd; border-radius: 8px; font-weight: 600; font-size: 0.85rem; cursor: pointer;">
        Upgrade to Premium
    </button>
</div>
""", unsafe_allow_html=True)

# Main Canvas Header
st.markdown("""
<div style="display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid #27272a; padding-bottom: 18px; margin-bottom: 24px;">
    <div>
        <h1 style="font-size: 1.85rem; font-weight: 700; color: #fafafa; margin: 0; display: flex; align-items: center; gap: 12px;">
            <span class="ms" style="color: #a78bfa; font-size: 32px;">plagiarism</span>
            Evaluation Deep-Dive
        </h1>
        <p style="color: #a1a1aa; font-size: 0.88rem; margin: 6px 0 0 0;">Script ID: #SOC-2024-8892 • Submitted: Oct 24, 2024</p>
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

# Tab Navigation for Modules
tab1, tab2, tab3 = st.tabs([
    "📄 Script Evaluation & OCR Deep-Dive",
    "❓ Doubt Tracker & Model Answers",
    "🏆 Sociology Hub & Topper Vault"
])

# ==========================================
# TAB 1: EVALUATION DEEP-DIVE
# ==========================================
with tab1:
    col_up1, col_up2 = st.columns([2, 1])
    with col_up1:
        uploaded_file = st.file_uploader("Upload Answer Script PDF or Image", type=["pdf", "png", "jpg", "jpeg"])
        question_context = st.text_area("Question Text (Optional)", placeholder="Q1. Discuss the sociological perspectives on 'Suicide' with special reference to Emile Durkheim...")
    with col_up2:
        max_marks = st.selectbox("Maximum Marks", options=[10, 15, 20], index=2)

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
                status.update(label="✅ Evaluation Deep-Dive Complete!", state="complete", expanded=False)

    st.markdown("---")

    # Split View (5/12 Left Column, 7/12 Right Column)
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
                    Q1. Discuss the sociological perspectives on 'Suicide' with special reference to Emile Durkheim.
                </h3>
                <p style="color: #a1a1aa; font-size: 0.92rem; line-height: 1.6; margin-bottom: 16px;">
                    Emile Durkheim's study of suicide (1897) is a seminal work in sociology that sought to demonstrate that even a seemingly highly individual act like suicide is influenced by social facts. He argued that the suicide rate is a 'social fact'...
                </p>

                <div style="border: 1px solid #27272a; border-radius: 8px; background: #121215; padding: 30px; text-align: center; margin: 20px 0; position: relative;">
                    <span style="color: #71717a; font-size: 0.85rem; font-style: italic;">Handwritten diagram detected: Durkheim's Suicide Matrix</span>
                </div>

                <p style="color: #a1a1aa; font-size: 0.92rem; line-height: 1.6;">
                    He categorized suicide into four types based on the levels of integration and regulation in society: Egoistic (low integration), Altruistic (high integration), Anomic (low regulation), and Fatalistic (high regulation)...
                </p>
            </div>
        </div>
        """, unsafe_allow_html=True)

    # Right Column: Evaluation & Analytics (4 Metric Boxes + Detailed Report)
    with col_right:
        st.markdown("""
        <div style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; margin-bottom: 20px;">
            <div class="metric-card">
                <span style="font-size: 0.8rem; color: #a1a1aa; margin-bottom: 6px;">Total Marks</span>
                <div style="display: flex; align-items: baseline; gap: 4px;">
                    <span style="font-size: 1.85rem; font-weight: 700; color: #34d399;">14.5</span>
                    <span style="font-size: 0.85rem; color: #a1a1aa;">/ 20</span>
                </div>
            </div>
            
            <div class="metric-card">
                <span style="font-size: 0.8rem; color: #a1a1aa; margin-bottom: 6px;">Structure</span>
                <div style="display: flex; align-items: baseline; gap: 4px;">
                    <span style="font-size: 1.85rem; font-weight: 700; color: #a78bfa;">8.5</span>
                    <span style="font-size: 0.85rem; color: #a1a1aa;">/ 10</span>
                </div>
            </div>

            <div class="metric-card">
                <span style="font-size: 0.8rem; color: #a1a1aa; margin-bottom: 6px;">Thinker Density</span>
                <div style="margin-top: 8px;">
                    <div style="width: 100%; height: 6px; background: #27272a; border-radius: 9999px; overflow: hidden; margin-bottom: 4px;">
                        <div style="width: 75%; height: 100%; background: #a78bfa; border-radius: 9999px;"></div>
                    </div>
                    <span style="font-size: 0.75rem; color: #a1a1aa;">High</span>
                </div>
            </div>

            <div class="metric-card">
                <span style="font-size: 0.8rem; color: #a1a1aa; margin-bottom: 6px;">Topper Similarity</span>
                <div style="display: flex; align-items: center; gap: 6px; margin-top: 4px;">
                    <span style="font-size: 1.65rem; font-weight: 700; color: #34d399;">82%</span>
                    <span class="ms" style="color: #34d399; font-size: 18px;">trending_up</span>
                </div>
            </div>
        </div>

        <div class="glass-panel">
            <div style="display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid #27272a; padding-bottom: 12px; margin-bottom: 16px;">
                <div style="font-weight: 600; font-size: 1.05rem; color: #fafafa; display: flex; align-items: center; gap: 8px;">
                    <span class="ms" style="color: #a78bfa; font-size: 22px;">analytics</span>
                    Detailed Feedback Report
                </div>
                <span style="padding: 3px 10px; background: rgba(52, 211, 153, 0.15); color: #34d399; border: 1px solid rgba(52, 211, 153, 0.3); border-radius: 4px; font-size: 0.75rem; font-weight: 600;">
                    AI Evaluated
                </span>
            </div>

            <!-- Section 1 -->
            <div style="margin-bottom: 20px;">
                <h4 style="font-size: 0.95rem; font-weight: 600; color: #c4b5fd; margin-bottom: 8px;">1. Conceptual Clarity & Introduction</h4>
                <p style="font-size: 0.88rem; color: #a1a1aa; line-height: 1.5; margin-bottom: 10px;">
                    Excellent opening linking Durkheim's work to the establishment of sociology as a discipline. The definition of suicide as a 'social fact' is clearly articulated. However, a brief mention of his methodological approach (statistical method) in the intro would elevate the answer.
                </p>
                <div style="display: flex; align-items: center; gap: 8px; background: #09090b; padding: 10px 14px; border-radius: 8px; border: 1px solid #27272a;">
                    <span class="ms" style="color: #34d399; font-size: 18px;">check_circle</span>
                    <span style="font-size: 0.85rem; color: #fafafa;">Strong conceptual grounding; clear definition of terms.</span>
                </div>
            </div>

            <!-- Section 2: Thinker Mapping -->
            <div style="margin-bottom: 20px;">
                <h4 style="font-size: 0.95rem; font-weight: 600; color: #c4b5fd; margin-bottom: 12px;">2. Sociological Reasoning Engine: Thinker Mapping</h4>
                <div style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 10px;">
                    <div class="thinker-card">
                        <div style="display: flex; justify-content: space-between; font-size: 0.85rem; font-weight: 600; margin-bottom: 4px;">
                            <span>Primary: Emile Durkheim</span>
                            <span class="ms" style="color: #34d399; font-size: 16px;">check</span>
                        </div>
                        <span style="font-size: 0.78rem; color: #a1a1aa;">Core typology mapped effectively.</span>
                    </div>

                    <div class="thinker-card">
                        <div style="display: flex; justify-content: space-between; font-size: 0.85rem; font-weight: 600; margin-bottom: 4px;">
                            <span>Critique: J.D. Douglas</span>
                            <span style="color: #ef4444; font-size: 0.75rem;">Missing</span>
                        </div>
                        <span style="font-size: 0.78rem; color: #a1a1aa;">Failed to include phenomenological critique of official statistics.</span>
                    </div>

                    <div class="thinker-card" style="grid-column: span 2;">
                        <div style="display: flex; justify-content: space-between; font-size: 0.85rem; font-weight: 600; margin-bottom: 4px;">
                            <span>Contemporary: Jean Baechler</span>
                            <span class="ms" style="color: #34d399; font-size: 16px;">check</span>
                        </div>
                        <span style="font-size: 0.78rem; color: #a1a1aa;">Good inclusion of typological variations.</span>
                    </div>
                </div>

                <div style="margin-top: 12px; padding: 12px; background: rgba(239, 68, 68, 0.1); border: 1px solid rgba(239, 68, 68, 0.3); border-radius: 8px; display: flex; gap: 10px;">
                    <span class="ms" style="color: #ef4444; font-size: 20px;">lightbulb</span>
                    <span style="font-size: 0.83rem; color: #a1a1aa;"><strong style="color: #ef4444;">Recommendation:</strong> Incorporate J.D. Douglas's argument that coroners construct statistics based on social meanings, challenging Durkheim's objective social facts.</span>
                </div>
            </div>

            <!-- Section 3: Benchmark against Topper Vault -->
            <div>
                <h4 style="font-size: 0.95rem; font-weight: 600; color: #c4b5fd; margin-bottom: 8px;">3. Benchmark against Topper Vault</h4>
                <ul style="font-size: 0.85rem; color: #a1a1aa; line-height: 1.5; padding-left: 18px; margin-bottom: 12px;">
                    <li>Topper scripts for this question consistently feature a <strong style="color: #fafafa;">flowchart</strong> illustrating the relationship between integration/regulation and suicide types.</li>
                    <li>Your conclusion is slightly descriptive; top-scoring answers usually end with a contemporary application (e.g., farmer suicides in India).</li>
                </ul>
            </div>
        </div>
        """, unsafe_allow_html=True)

# ==========================================
# TAB 2: DOUBT TRACKER
# ==========================================
with tab2:
    st.header("❓ Doubt Tracker & Model Answer Generator")
    user_q = st.text_area("Enter your Sociology Question / Doubt", placeholder="e.g. Discuss the relevance of Weber's Protestant Ethic thesis in understanding contemporary Indian capitalism.")
    
    col_q1, col_q2 = st.columns(2)
    with col_q1:
        word_limit = st.select_slider("Target Word Limit", options=[150, 250], value=250)
    with col_q2:
        paper_scope = st.selectbox("Target Paper", options=["Paper 1 (Foundations)", "Paper 2 (Indian Society)", "Both / Inter-linked"], index=2)

    if user_q and st.button("💡 Generate Model Answer", type="primary", use_container_width=True):
        if not api_key:
            st.error("Please enter a valid Gemini API Key in the sidebar.")
        else:
            with st.spinner("Synthesizing model answer..."):
                ans_result = resolve_sociology_question(user_q, word_limit=word_limit, paper_type=paper_scope, api_key=api_key)
            st.markdown(ans_result)

# ==========================================
# TAB 3: SOCIOLOGY HUB
# ==========================================
with tab3:
    st.header("🏆 Sociology Hub & Topper Vault")
    topper_file = st.file_uploader("Upload Topper Answer PDF", type=["pdf", "png", "jpg", "jpeg"], key="topper_upload_2")
    if topper_file and st.button("⚡ Extract Strategy", type="primary"):
        if not api_key:
            st.error("Please enter Gemini API Key.")
        else:
            with st.status("Analyzing Topper Copy...", expanded=True) as status:
                file_bytes = topper_file.read()
                ocr_text, _ = process_pdf_or_image(file_bytes, topper_file.name, api_key=api_key)
                extracted_data = analyze_and_extract_topper_copy(ocr_text, api_key=api_key)
                status.update(label="🎉 Done!", state="complete", expanded=False)
            st.write(extracted_data)
