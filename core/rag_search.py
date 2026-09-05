import os
import sqlite3
import numpy as np
from google import genai

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "notes_vector_index.db")

def cosine_similarity(v1, v2):
    dot = np.dot(v1, v2)
    norm1 = np.linalg.norm(v1)
    norm2 = np.linalg.norm(v2)
    if norm1 == 0 or norm2 == 0:
        return 0.0
    return dot / (norm1 * norm2)

def search_personal_notes(query_text, subject, api_key=None, top_k=3):
    """
    Embeds the user query, searches the SQLite vector index for the target subject,
    and returns the top_k most mathematically relevant note chunks.
    """
    if not os.path.exists(DB_PATH):
        return []

    key = api_key or os.environ.get("GEMINI_API_KEY")
    if not key:
        return []
        
    try:
        client = genai.Client(api_key=key)
        
        # 1. Embed the query
        response = client.models.embed_content(
            model="gemini-embedding-001",
            contents=query_text
        )
        query_vec = np.array(response.embeddings[0].values, dtype=np.float32)
        
        # 2. Load candidate chunks for the subject
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("SELECT chunk_text, embedding, filename FROM notes_chunks WHERE subject = ?", (subject,))
        rows = c.fetchall()
        conn.close()
        
        if not rows:
            return []
            
        # 3. Calculate similarity
        scored_chunks = []
        for row in rows:
            chunk_text = row[0]
            emb_bytes = row[1]
            filename = row[2]
            
            chunk_vec = np.frombuffer(emb_bytes, dtype=np.float32)
            score = cosine_similarity(query_vec, chunk_vec)
            scored_chunks.append((score, chunk_text, filename))
            
        # 4. Sort and return top_k
        scored_chunks.sort(key=lambda x: x[0], reverse=True)
        top_results = []
        for score, text, fname in scored_chunks[:top_k]:
            if score > 0.3: # Minimum relevance threshold
                top_results.append(f"[From Your Notes: {fname}]: {text}")
                
        return top_results
        
    except Exception as e:
        print(f"RAG Search failed: {e}")
        return []
