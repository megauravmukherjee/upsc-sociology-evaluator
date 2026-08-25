# 📋 Project Context - UPSC Mains All-Subject AI Evaluator

This file serves as the primary context document for AI agents and developers working on this codebase in future sessions.

---

## 🎯 Project Overview
- **Project Location**: `C:\Users\Gaurav Mukherjee\.gemini\antigravity\scratch\upsc_sociology_evaluator`
- **Application Type**: Streamlit Web Application
- **AI Model Engine**: `gemini-3.6-flash` (via `google-genai` Python SDK)
- **Deployment Platform**: Streamlit Community Cloud (`https://upscsociologyevaluator.streamlit.app`) / GitHub Repository (`https://github.com/megauravmukherjee/upsc-sociology-evaluator`)

---

## 🔒 Key Architectural Rules (MUST BE MAINTAINED)

1. **Absolute Subject Isolation**:
   - **Sociology Optional**: Evaluated ONLY on Paper 1 & Paper 2 sociological thinkers (Marx, Durkheim, Weber, Parsons, Merton, Mead, Ghurye, Srinivas, Desai, Andre Beteille).
   - **GS 1**: History accuracy, Art & Culture NAGARA/DRAVIDA diagrams, Physical/Human Geography maps, Indian Society. NO Sociology thinkers!
   - **GS 2**: Starts with Constitutional Articles (Art 14, 19, 21, 32, 243, 262, 311, 356, 368), Supreme Court Judgments (*Bommai, Kesavananda, Puttaswamy*), 2nd ARC & Commission Reports. NO Sociology thinkers!
   - **GS 3**: Starts with Economic Statistics (GDP %, NPAs %, Debt %), Economic Survey, Sendai Disaster Framework, Environmental accords, Cyber/Border security maps. NO Sociology thinkers!
   - **GS 4 (Ethics)**: Part A Theory (Value Definitions + Personal Examples + Leader Value Mapping e.g. Ambedkar, Gandhi, JRD Tata); Part B Case Studies (Subject Matter, Stakeholders Spoke-Wheel, Ethical Dilemma, Options Merits/Demerits Table, Justified Action Plan + Gandhiji's Talisman). NO Sociology thinkers!
   - **Essay Evaluator**: 120-150 word Intro Hook (Fictitious Story / Historical Anecdote / Startling Statistic / Rhetorical Question / Quote Hook), NO bland GS-style dictionary definition intro, Coherence & Flow with Connectives, PESTLE & Temporal Body, 250-300 word Conclusion with Solutions + Rhetorical Ending (Tagore Gitanjali / Talisman / Echo Effect). NO Sociology thinkers!

2. **OCR Pipeline (`core/ocr_engine.py`)**:
   - Uses Gemini Files API (`client.files.upload`) for high-speed multi-page PDF processing directly in Google cloud storage.
   - Multithreaded `ThreadPoolExecutor` for parallel image OCR fallback.

3. **UI Theme**:
   - Preserves the clean light-mode Streamlit layout currently deployed at `upscsociologyevaluator.streamlit.app`.

---

## 🚀 Quick Context Summary for New Agent Conversations:
When starting a new conversation, instruct the agent:
> *"I am working on the project at `C:\Users\Gaurav Mukherjee\.gemini\antigravity\scratch\upsc_sociology_evaluator`. Please read `README.md` and `PROJECT_CONTEXT.md` to understand the codebase context."*
