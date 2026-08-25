# 🎓 UPSC CSE Mains All-Subject AI Evaluator & Strategy Hub

An AI-powered evaluation, doubt resolution, and strategy mining platform designed specifically for the **UPSC Civil Services Examination (CSE) Mains**. 

Built with **Streamlit**, **Gemini 3.6 Multimodal Vision OCR**, and grounded in the official **UPSC Notification Syllabus** and **Anudeep Durishetty (AIR 1, UPSC CSE 2017)** answer writing frameworks.

---

## 📌 Core Features

- **📄 Module 1: Handwritten Answer Script Evaluator & Deep-Dive**
  - **Gemini Files API Vision OCR**: Fast multi-page OCR capable of reading handwritten cursive text, side notes, and diagram annotations directly from PDF or Image uploads.
  - **Strict Subject Isolation**:
    - **Sociology Optional**: Evaluated on Paper 1 & Paper 2 thinkers (Marx, Durkheim, Weber, Parsons, Merton, Mead, Ghurye, Srinivas, Desai).
    - **GS 1**: History chronology/facts, Art & Culture NAGARA/DRAVIDA style architectural diagrams, World/Physical Geography maps, and Indian Society.
    - **GS 2 (Polity & Governance)**: Mandatory start with Constitutional Articles (Art 14, 19, 21, 32, 243, 246, 262, 311, 356, 368), Supreme Court Landmark Judgments (*Bommai, Kesavananda, Puttaswamy, Maneka Gandhi*), 2nd ARC & Punchhi Commission recommendations. *(No Sociology thinkers allowed!)*
    - **GS 3 (Economy, Env, Security)**: Opening with sector statistics (GDP %, NPAs %, Debt %, Economic Survey), Sendai Disaster Framework, Environmental COP accords, and Border/Cyber Security maps. *(No Sociology thinkers allowed!)*
    - **GS 4 (Ethics & Case Studies)**: Part A Value Definitions + Personal Examples + Leader Value Mapping (Ambedkar, Gandhi, JRD Tata); Part B Case Studies (Subject Matter, Stakeholders Spoke-Wheel, Ethical Dilemma, Options Merits/Demerits Table, Justified Action Plan + Gandhiji's Talisman).
    - **Essay Evaluator**: 120-150 word Intro Hook (Fictitious Story / Historical Anecdote / Startling Statistic / Rhetorical Question / Quote Hook), NO bland GS-style dictionary definition intro, Coherence & Flow with Connectives, PESTLE & Temporal Body, 250-300 word Conclusion with Solutions + Rhetorical Ending (Tagore Gitanjali / Talisman / Echo Effect).
- **❓ Module 2: Doubt Tracker & Model Answer Generator**
  - Subject-specific model answer generation for GS 1-4, Essay, and Sociology Optional without cross-subject bleeding.
- **🏆 Module 3: Strategy Hub & Topper Vault**
  - Upload topper answer PDFs to extract reusable definitions, articles, thinker quotes, diagram schematics, and intro/outro templates into a persistent strategy bank (`data/vault.json`).

---

## 🛠️ Codebase Structure

```
upsc_sociology_evaluator/
├── app.py                      # Streamlit web application & user interface
├── config.py                  # Subject-isolated system prompts & Anudeep Durishetty AIR 1 frameworks
├── requirements.txt            # Python dependencies (google-genai, streamlit, pypdf, pillow)
├── Dockerfile                  # Container manifest for Cloud Run / Render deployment
├── DEPLOYMENT_GUIDE.md         # Deployment instructions for Streamlit Cloud & Docker
├── core/
│   ├── ocr_engine.py           # Gemini Files API PDF & Image multimodal OCR processor
│   ├── evaluator.py            # Subject-isolated answer evaluation engine
│   ├── qa_resolver.py          # Subject-wise doubt resolver & model answer generator
│   └── topper_analyzer.py      # Topper copy strategy extraction engine
└── data/
    ├── vault.json              # Persistent strategy vault (Articles, Thinkers, Quotes, Case Studies)
    └── syllabus.json           # Official UPSC syllabus structure for GS 1-4, Essay, and Sociology
```

---

## 🚀 How to Run Locally

```bash
# Navigate to project directory
cd upsc_sociology_evaluator

# Activate virtual environment
.\.venv\Scripts\activate

# Run Streamlit server
streamlit run app.py
```
App will open live at: `http://localhost:8501`

---

## ☁️ How to Deploy

To deploy live on **Streamlit Community Cloud** (Free):
1. Push this repository to GitHub: `git push origin main`
2. Go to **[share.streamlit.io](https://share.streamlit.io)** and select `app.py`.
3. Add `GEMINI_API_KEY` under Secrets.
