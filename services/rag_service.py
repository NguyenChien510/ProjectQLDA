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
        # Save user message
        self.history.save_message(file_id, "user", question)
        
        if "tóm tắt tài liệu" in question.lower():
            return self.get_summary(file_id)

        context_chunks = self.chroma.query(question, file_id)
        context = "\n---\n".join(context_chunks)
        
        # PROMPT THÔNG MINH CHO HỎI ĐÁP
        prompt = f"""Bạn là một Chuyên gia Phân tích Tài liệu cấp cao. Nhiệm vụ của bạn là trả lời câu hỏi một cách chính xác, khách quan và chuyên sâu dựa trên ngữ cảnh được cung cấp.

--- NGỮ CẢNH TÀI LIỆU ---
{context}
-----------------------

HƯỚNG DẪN TRẢ LỜI:
1. Sử dụng NGỮ CẢNH trên làm căn cứ duy nhất để trả lời. 
2. Nếu thông tin KHÔNG CÓ trong ngữ cảnh, hãy phản hồi: "Dựa trên tài liệu hiện tại, tôi không tìm thấy thông tin cụ thể về vấn đề này. Tuy nhiên, tài liệu có đề cập đến [liệt kê các chủ đề gần liên quan nếu có]...". Tuyệt đối không tự bịa ra thông tin ngoài.
3. Trình bày câu trả lời theo cấu trúc rõ ràng, sử dụng gạch đầu dòng hoặc đánh số nếu cần thiết. 
4. Sử dụng định dạng Markdown (in đậm, in nghiêng) để làm nổi bật các từ khóa quan trọng.
5. Giữ thái độ lịch sự, chuyên nghiệp và khách quan.

CÂU HỎI CỦA NGƯỜI DÙNG: {question}

TRẢ LỜI CHI TIẾT:"""

        messages = [{"role": "user", "content": prompt}]
        answer = self.llm.chat_completion(messages)
        
        self.history.save_message(file_id, "assistant", answer)
        return answer

    def get_summary(self, file_id: str):
        # Lấy nhiều kết quả hơn để tóm tắt bao quát hơn
        context_chunks = self.chroma.query("Mục đích chính, nội dung quan trọng và kết luận của tài liệu", file_id, n_results=10)
        context = "\n---\n".join(context_chunks)
        
# PROMPT THÔNG MINH CHO TÓM TẮT
        prompt = f"""Hãy đóng vai một thư ký chuyên nghiệp, tóm tắt tài liệu sau một cách rõ ràng và đẹp mắt.

--- DỮ LIỆU TÀI LIỆU ---
{context}
-----------------------------

YÊU CẦU ĐỊNH DẠNG:
1. Sử dụng các tiêu đề (#) cho các phần lớn.
2. Trình bày các ý bằng dấu gạch đầu dòng (-) rõ ràng.
3. In đậm (**) các thông tin quan trọng như ngày tháng, số tiền, tên người.

BẢN TÓM TẮT SÚC TÍCH:"""

        messages = [{"role": "user", "content": prompt}]
        summary = self.llm.chat_completion(messages)
        
        self.history.save_message(file_id, "assistant", summary)
        return summary
