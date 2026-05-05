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
        
        # 1. Base tables
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS sessions (
                file_id TEXT PRIMARY KEY,
                file_name TEXT,
                created_at TEXT
            )
        ''')
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
        
        # 2. Migrations
        cursor.execute("PRAGMA table_info(sessions)")
        cols = [c[1] for c in cursor.fetchall()]
        if "full_text" not in cols:
            cursor.execute("ALTER TABLE sessions ADD COLUMN full_text TEXT")
            
        cursor.execute("PRAGMA table_info(messages)")
        cols = [c[1] for c in cursor.fetchall()]
        if "metadata" not in cols:
            cursor.execute("ALTER TABLE messages ADD COLUMN metadata TEXT")
            
        conn.commit()
        conn.close()

    def save_session(self, file_id: str, file_name: str, full_text: str = ""):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('INSERT OR IGNORE INTO sessions (file_id, file_name, full_text, created_at) VALUES (?, ?, ?, ?)',
                       (file_id, file_name, full_text, datetime.now().isoformat()))
        conn.commit()
        conn.close()

    def get_session_text(self, file_id: str):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT full_text, file_name FROM sessions WHERE file_id = ?', (file_id,))
        row = cursor.fetchone()
        conn.close()
        if row:
            return row[0], row[1]
        return "", ""

    def save_message(self, file_id: str, role: str, content: str, metadata: str = None):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        timestamp = datetime.now().strftime("%H:%M")
        cursor.execute('INSERT INTO messages (file_id, role, content, metadata, timestamp) VALUES (?, ?, ?, ?, ?)',
                       (file_id, role, content, metadata, timestamp))
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
        cursor.execute('SELECT role, content, metadata, timestamp FROM messages WHERE file_id = ? ORDER BY id ASC', (file_id,))
        messages = [{"role": row[0], "content": row[1], "metadata": row[2], "timestamp": row[3]} for row in cursor.fetchall()]
        conn.close()
        return messages
    def delete_session(self, file_id: str):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        try:
            # Delete messages first due to foreign key
            cursor.execute('DELETE FROM messages WHERE file_id = ?', (file_id,))
            cursor.execute('DELETE FROM sessions WHERE file_id = ?', (file_id,))
            conn.commit()
            return True
        except Exception as e:
            print(f"Lỗi khi xóa session: {e}")
            return False
        finally:
            conn.close()
