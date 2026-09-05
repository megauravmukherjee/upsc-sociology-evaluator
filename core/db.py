import sqlite3
import os
from datetime import datetime

# Define DB path in the data folder
DB_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "memory.db")

def get_connection():
    # Create data directory if it doesn't exist
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_connection()
    cursor = conn.cursor()
    
    # Table for storing Evaluations
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS evaluations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        subject TEXT NOT NULL,
        question_context TEXT,
        answer_ocr TEXT NOT NULL,
        evaluation_text TEXT NOT NULL,
        max_marks INTEGER,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    # Table for storing Model Answers (QA)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS model_answers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        subject TEXT NOT NULL,
        question TEXT NOT NULL,
        answer_text TEXT NOT NULL,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    conn.commit()
    conn.close()

def save_evaluation(subject, question_context, answer_ocr, evaluation_text, max_marks):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO evaluations (subject, question_context, answer_ocr, evaluation_text, max_marks) VALUES (?, ?, ?, ?, ?)",
        (subject, question_context, answer_ocr, evaluation_text, max_marks)
    )
    conn.commit()
    conn.close()

def get_past_evaluations(subject, limit=2):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM evaluations WHERE subject = ? ORDER BY timestamp DESC LIMIT ?",
        (subject, limit)
    )
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def save_model_answer(subject, question, answer_text):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO model_answers (subject, question, answer_text) VALUES (?, ?, ?)",
        (subject, question, answer_text)
    )
    conn.commit()
    conn.close()

def get_past_model_answers(subject, limit=2):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM model_answers WHERE subject = ? ORDER BY timestamp DESC LIMIT ?",
        (subject, limit)
    )
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def get_all_evaluations(limit=50):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM evaluations ORDER BY timestamp DESC LIMIT ?", (limit,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def get_all_model_answers(limit=50):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM model_answers ORDER BY timestamp DESC LIMIT ?", (limit,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

# Initialize tables when module is loaded
init_db()
