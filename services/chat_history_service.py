import sqlite3
import json
import os
from datetime import datetime

class ChatHistoryService:
    def __init__(self, db_path: str = "data/history.db"):
        if not os.path.exists("data"):
            os.makedirs("data")
            
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        # Table for files/sessions
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS sessions (
                file_id TEXT PRIMARY KEY,
                file_name TEXT,
                created_at TEXT
            )
        ''')
        # Table for messages
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                file_id TEXT,
                role TEXT,
                content TEXT,
                timestamp TEXT,
                FOREIGN KEY (file_id) REFERENCES sessions (file_id)
            )
        ''')
        conn.commit()
        conn.close()

    def save_session(self, file_id: str, file_name: str):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('INSERT OR IGNORE INTO sessions (file_id, file_name, created_at) VALUES (?, ?, ?)',
                       (file_id, file_name, datetime.now().isoformat()))
        conn.commit()
        conn.close()

    def save_message(self, file_id: str, role: str, content: str):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        timestamp = datetime.now().strftime("%H:%M")
        cursor.execute('INSERT INTO messages (file_id, role, content, timestamp) VALUES (?, ?, ?, ?)',
                       (file_id, role, content, timestamp))
        conn.commit()
        conn.close()

    def get_all_sessions(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT file_id, file_name FROM sessions ORDER BY created_at DESC')
        sessions = [{"file_id": row[0], "file_name": row[1]} for row in cursor.fetchall()]
        conn.close()
        return sessions

    def get_messages(self, file_id: str):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT role, content, timestamp FROM messages WHERE file_id = ? ORDER BY id ASC', (file_id,))
        messages = [{"role": row[0], "content": row[1], "timestamp": row[2]} for row in cursor.fetchall()]
        conn.close()
        return messages
