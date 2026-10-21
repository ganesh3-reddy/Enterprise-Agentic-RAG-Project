import sqlite3
import json
from datetime import datetime,timezone
from app.core.config import get_settings
settings = get_settings()

def initialize_audit_db():
    conn = sqlite3.connect(settings.audit_db_path)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS audit_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            user_query TEXT NOT NULL,
            source_used TEXT NOT NULL,
            answer TEXT NOT NULL,
            web_grade TEXT NOT NULL,
            retry_count INTEGER NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

def write_audit_log(user_query: str, source_used: str, answer: str, web_grade: str, retry_count: int):
    conn = sqlite3.connect(settings.audit_db_path)
    cursor = conn.cursor()
    timestamp = datetime.now(timezone.utc).isoformat()
    cursor.execute('''
        INSERT INTO audit_log (timestamp, user_query, source_used, answer, web_grade, retry_count)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (timestamp, user_query, source_used, answer, web_grade, retry_count))
    conn.commit()
    conn.close()