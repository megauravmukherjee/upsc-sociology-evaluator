# 🚀 Deployment Guide - UPSC CSE Sociology Answer Evaluator

This guide covers step-by-step instructions for deploying your Streamlit app to production using **Streamlit Community Cloud** (Free & Recommended), **Hugging Face Spaces**, or **Docker / Cloud Run**.

---

## Method 1: Deploy on Streamlit Community Cloud (Free & Recommended)

This is the easiest way to host your app online with a public URL (e.g. `https://upsc-sociology-evaluator.streamlit.app`).

### Step 1: Initialize Git & Push to GitHub
Open your terminal in the project directory:

```bash
cd "C:\Users\Gaurav Mukherjee\.gemini\antigravity\scratch\upsc_sociology_evaluator"
git init
git add .
git commit -m "Initial commit of UPSC Sociology Evaluator"
```

Create a new repository on [GitHub](https://github.com/new) and push your code:

```bash
git remote add origin https://github.com/YOUR_USERNAME/upsc-sociology-evaluator.git
git branch -M main
git push -u origin main
```

### Step 2: Deploy on Streamlit Community Cloud
1. Go to **[share.streamlit.io](https://share.streamlit.io)** and log in with your GitHub account.
2. Click **"New app"** -> Select your GitHub repository (`upsc-sociology-evaluator`).
3. Set **Main file path** to `app.py`.
4. Click **Advanced settings...** -> Under **Secrets**, add your Gemini API Key:
   ```toml
   GEMINI_API_KEY = "your-actual-gemini-api-key-here"
   ```
5. Click **Deploy!**

---

## Method 2: Deploy on Hugging Face Spaces (Free)

1. Go to **[huggingface.co/spaces](https://huggingface.co/spaces)** and click **"Create new Space"**.
2. Select **Streamlit** as the SDK.
3. Upload project files (`app.py`, `config.py`, `requirements.txt`, `core/`, `data/`, `.streamlit/`).
4. Go to **Settings > Secrets** and add `GEMINI_API_KEY`.
5. Hugging Face will build and launch your app automatically!

---

## Method 3: Deploy using Docker (Cloud Run / Render / AWS)

A `Dockerfile` is already included in your project folder.

### Run locally with Docker:
```bash
docker build -t upsc-sociology-evaluator .
docker run -p 8501:8501 -e GEMINI_API_KEY="your-api-key" upsc-sociology-evaluator
```

### Deploy to Google Cloud Run:
```bash
gcloud run deploy upsc-sociology-evaluator \
  --source . \
  --platform managed \
  --allow-unauthenticated \
  --set-env-vars GEMINI_API_KEY="your-api-key"
```

---

## 🔒 Security Tip
Never commit your private `GEMINI_API_KEY` into public GitHub repositories. Always set it via environment variables or platform Secrets!
