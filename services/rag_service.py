from .chromadb_service import ChromaDBService
from .lmstudio_client import LMStudioClient
from .file_loader import FileLoader
from .chat_history_service import ChatHistoryService
import uuid

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
            self.chroma.add_documents(chunks, file_id, file_name)
            self.history.save_session(file_id, file_name)
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

QUY TẮC PHẢI TUÂN THỦ:
1. ĐI THẲNG VÀO VẤN ĐỀ: Không bắt đầu bằng các câu dẫn như "Dựa trên tài liệu...", "Trong trường hợp này...", "Câu trả lời là...". Trả lời ngay lập tức nội dung người dùng cần.
2. TỐI GIẢN VĂN BẢN: Bỏ qua các giải thích rườm rà không cần thiết. Nếu có thể trả lời trong 1 câu, đừng viết 2 câu.
3. TRÍCH DẪN NGẮN: Sử dụng [1], [2] ngay sau thông tin.
4. SUY LUẬN NGẦM: Thực hiện suy luận logic trong đầu và đưa ra kết quả cuối cùng, không trình bày quá trình suy luận trừ khi được hỏi.
5. ĐỊNH DẠNG SẠCH: Sử dụng bullet points nếu có nhiều ý.
6. THÁI ĐỘ: Chuyên nghiệp, không xã giao thừa thãi."""

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
        self.history.save_message(file_id, "user", question)
        answer = self.llm.chat_completion(messages, temperature=0.1)
        self.history.save_message(file_id, "assistant", answer)
        
        return answer

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
        return summary
