import uuid
from datetime import datetime
from typing import List, Optional

class ChatMessage:
    def __init__(self, role: str, content: str, timestamp: str = None):
        self.role = role
        self.content = content
        self.timestamp = timestamp or datetime.now().strftime("%H:%M")

class ChatSession:
    def __init__(self, file_id: str, file_name: str):
        self.file_id = file_id
        self.file_name = file_name
        self.created_at = datetime.now().isoformat()
        self.messages: List[ChatMessage] = []
