import os
import sqlite3
import json
import numpy as np
from pypdf import PdfReader
from google import genai
import glob

# Try to get API key
api_key = os.environ.get("GEMINI_API_KEY")
if not api_key:
    print("WARNING: GEMINI_API_KEY environment variable not set. Please set it before running this script.")
    # In practice, user will run `set GEMINI_API_KEY=...` before running this.

# Initialize Gemini Client
client = genai.Client(api_key=api_key) if api_key else None

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "notes_vector_index.db")
NOTES_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "personal_notes")

# Map exact UI string to folder string
SUBJECT_MAP = {
    "Sociology Optional": "Sociology_Optional",
    "GS 1": "GS_1",
    "GS 2": "GS_2",
    "GS 3": "GS_3",
    "GS 4 (Ethics)": "GS_4_Ethics",
    "Essay Evaluator": "Essay_Evaluator"
}

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS notes_chunks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            subject TEXT,
            filename TEXT,
            chunk_text TEXT,
            embedding BLOB
        )
    ''')
    # Clear old data if re-running
    c.execute('DELETE FROM notes_chunks')
    conn.commit()
    conn.close()

def chunk_text(text, chunk_size=500, overlap=50):
    words = text.split()
    chunks = []
    for i in range(0, len(words), chunk_size - overlap):
        chunk = " ".join(words[i:i + chunk_size])
        if len(chunk.strip()) > 50: # Only save meaningful chunks
            chunks.append(chunk)
    return chunks

def extract_text_from_pdf(filepath):
    text = ""
    try:
        reader = PdfReader(filepath)
        for page in reader.pages:
            t = page.extract_text()
            if t:
                text += t + "\n"
    except Exception as e:
        print(f"Error reading {filepath}: {e}")
    return text

def get_embeddings_batch(chunks):
    if not client:
        return [np.zeros(3072).tolist() for _ in chunks]
    try:
        response = client.models.embed_content(
            model="gemini-embedding-001",
            contents=chunks
        )
        # response.embeddings is a list of embeddings matching the order of contents
        return [e.values for e in response.embeddings]
    except Exception as e:
        print(f"Batch embedding error: {e}")
        return [np.zeros(3072).tolist() for _ in chunks]

def ingest_all():
    if not os.path.exists(NOTES_DIR):
        print(f"Notes directory not found: {NOTES_DIR}")
        return

    init_db()
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    total_chunks = 0
    for ui_subject, folder_name in SUBJECT_MAP.items():
        subject_dir = os.path.join(NOTES_DIR, folder_name)
        if not os.path.exists(subject_dir):
            continue
            
        pdf_files = glob.glob(os.path.join(subject_dir, "*.pdf"))
        if not pdf_files:
            continue
            
        print(f"Processing {len(pdf_files)} PDFs for {ui_subject}...")
        
        for pdf_path in pdf_files:
            filename = os.path.basename(pdf_path)
            print(f"  -> Reading {filename}...")
            text = extract_text_from_pdf(pdf_path)
            if not text.strip():
                print(f"  -> WARNING: No text found in {filename} (might be a scanned image).")
                continue
                
            chunks = chunk_text(text)
            print(f"  -> Extracted {len(chunks)} chunks. Generating embeddings in batches...")
            
            # Batch process in groups of 100
            batch_size = 100
            for i in range(0, len(chunks), batch_size):
                batch_chunks = chunks[i:i + batch_size]
                embeddings = get_embeddings_batch(batch_chunks)
                
                for chunk, emb in zip(batch_chunks, embeddings):
                    emb_bytes = np.array(emb, dtype=np.float32).tobytes()
                    c.execute(
                        "INSERT INTO notes_chunks (subject, filename, chunk_text, embedding) VALUES (?, ?, ?, ?)",
                        (ui_subject, filename, chunk, emb_bytes)
                    )
                    total_chunks += 1
                
                print(f"     ... embedded {min(i + batch_size, len(chunks))}/{len(chunks)} chunks")
                conn.commit() # commit after every batch
                
    conn.close()
    print(f"\n✅ Ingestion complete! Saved {total_chunks} chunks to {DB_PATH}")
    print("Don't forget to run `git add .`, `git commit`, and `git push` so Streamlit Cloud gets the new database!")

if __name__ == "__main__":
    ingest_all()
