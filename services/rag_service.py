from .chromadb_service import ChromaDBService
from .lmstudio_client import LMStudioClient
from .file_loader import FileLoader
from .chat_history_service import ChatHistoryService
import uuid
import json

class RAGService:
    def __init__(self):
        self.chroma = ChromaDBService()
        self.llm = LMStudioClient()
        self.history = ChatHistoryService()

    def process_new_file(self, file_path: str, file_name: str):
        file_id = str(uuid.uuid4())
        text = FileLoader.get_text(file_path)
        chunks = FileLoader.chunk_text(text)
        
        if chunks:
            # Tách riêng text để embedding và metadata để lưu vị trí
            texts = [c['text'] for c in chunks]
            metadatas = [{"start": c['start'], "end": c['end']} for c in chunks]
            
            self.chroma.add_documents(texts, file_id, file_name, metadatas=metadatas)
            self.history.save_session(file_id, file_name, text)
            return file_id
        return None

    def get_answer(self, file_id: str, question: str):
        # 0. Check if summary is requested
        if "tóm tắt tài liệu" in question.lower():
            return self.get_summary(file_id)

        # 1. Retrieve history (limit to last 5 messages to avoid token overflow)
        history_msgs = self.history.get_messages(file_id)[-5:]
        
        # 2. Search for relevant context
        search_results = self.chroma.query(question, file_id, n_results=5)
        
        context_parts = []
        for i, res in enumerate(search_results):
            source = res['metadata'].get('file_name', 'Tài liệu')
            context_parts.append(f"[{i+1}] Nguồn: {source}\nNội dung: {res['content']}")
        
        context_str = "\n\n".join(context_parts)
        
        # 3. Construct System Prompt
        system_prompt = """Bạn là một Trợ lý Phân tích Tài liệu tinh gọn và chuyên nghiệp. 
Nhiệm vụ của bạn là trả lời câu hỏi một cách NGẮN GỌN, TRỰC TIẾP và CHÍNH XÁC.

QUY TẮC BẮT BUỘC:
1. TRÍCH DẪN NGUỒN (CỰC KỲ QUAN TRỌNG): Bạn PHẢI sử dụng các ký hiệu [1], [2]... vào cuối các câu hoặc cụm từ mà bạn lấy thông tin từ ngữ cảnh. 
   - Ví dụ: "Hạn nộp hồ sơ là ngày 30/10 [1]. Sinh viên nộp tại phòng S03 [2]."
   - Nếu bạn không dùng [1], [2]..., câu trả lời sẽ bị coi là không hợp lệ.
2. ĐI THẲNG VÀO VẤN ĐỀ: Không dẫn chuyện, không giải thích quá trình suy luận. Trả lời ngay nội dung người dùng cần.
3. TỐI GIẢN VĂN BẢN: Nếu có thể trả lời trong 1 câu, đừng viết 2 câu.
4. ĐỊNH DẠNG SẠCH: Sử dụng in đậm cho các thông tin then chốt."""

        # 4. Prepare messages for LLM
        messages = [{"role": "system", "content": system_prompt}]
        
        # Add history
        for msg in history_msgs:
            messages.append({"role": msg['role'], "content": msg['content']})
            
        # Add current context and question
        current_input = f"""--- NGỮ CẢNH TÀI LIỆU ---
{context_str}
-----------------------

CÂU HỎI: {question}

Trả lời ngắn gọn và trực tiếp:"""
        
        messages.append({"role": "user", "content": current_input})
        
        # 5. Get answer and save
        sources = []
        for i, res in enumerate(search_results):
            sources.append({
                "content": res['content'],
                "id": i + 1,
                "start": res['metadata'].get('start'),
                "end": res['metadata'].get('end')
            })
        
        self.history.save_message(file_id, "user", question)
        answer = self.llm.chat_completion(messages, temperature=0.1)
        self.history.save_message(file_id, "assistant", answer, metadata=json.dumps(sources))
        
        return {
            "answer": answer,
            "sources": sources
        }

    def get_summary(self, file_id: str):
        search_results = self.chroma.query("Mục đích chính, nội dung quan trọng, quy định, thời hạn và kết luận", file_id, n_results=10)
        context = "\n---\n".join([r['content'] for r in search_results])
        
        prompt = f"""Bạn là một chuyên gia tóm tắt văn bản. Hãy tạo một bản tóm tắt chuyên sâu và chuyên nghiệp cho tài liệu sau.

--- DỮ LIỆU TÀI LIỆU ---
{context}
-----------------------------

YÊU CẦU BẢN TÓM TẮT:
1. Tiêu đề hấp dẫn và rõ ràng.
2. Tổng quan ngắn gọn (1-2 câu).
3. Các nội dung chính (Key Takeaways) trình bày dưới dạng danh sách.
4. Các mốc thời gian, con số hoặc quy định quan trọng (nếu có).
5. Kết luận hoặc khuyến nghị.
6. Sử dụng Markdown cao cấp (bảng, quote, bold).

Hãy trình bày một bản tóm tắt khiến người đọc nắm bắt được 90% nội dung chỉ trong 1 phút."""

        messages = [{"role": "user", "content": prompt}]
        summary = self.llm.chat_completion(messages)
        
        # Lưu vào lịch sử nhưng có ghi chú là tóm tắt
        self.history.save_message(file_id, "assistant", f"## Tóm tắt tài liệu\n{summary}")
        return {
            "answer": f"## Tóm tắt tài liệu\n{summary}",
            "sources": []
        }

    def delete_session(self, file_id: str):
        # 1. Xóa lịch sử trong SQLite
        h_ok = self.history.delete_session(file_id)
        # 2. Xóa vector trong ChromaDB
        c_ok = self.chroma.delete_documents(file_id)
        return h_ok and c_ok
