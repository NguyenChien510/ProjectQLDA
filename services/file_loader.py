import os
import pytesseract
from pdf2image import convert_from_path
from pypdf import PdfReader
from docx import Document

# --- CẤU HÌNH TESSERACT & POPPLER ---
TESSERACT_PATH = r"C:\Users\minhc\Desktop\Tesseract-OCR\tesseract.exe"
TESSDATA_PREFIX = r"C:\Users\minhc\Desktop\Tesseract-OCR\tessdata"
# Điền đường dẫn thư mục bin của Poppler vào đây
POPPLER_PATH = r"c:\Users\minhc\Desktop\poppler\Library\bin" 

pytesseract.pytesseract.tesseract_cmd = TESSERACT_PATH
os.environ['TESSDATA_PREFIX'] = TESSDATA_PREFIX

class FileLoader:
    @staticmethod
    def load_pdf(file_path: str) -> str:
        text = ""
        try:
            # 1. Thử đọc text bình thường trước
            reader = PdfReader(file_path)
            for page in reader.pages:
                extracted = page.extract_text()
                if extracted:
                    text += extracted + "\n"
            
            # 2. Nếu text trích xuất được quá ít (có thể là PDF ảnh), dùng OCR
            if len(text.strip()) < 50:
                print(f"PDF có vẻ là dạng ảnh, đang bắt đầu OCR: {file_path}")
                # Chuyển các trang PDF thành danh sách ảnh (Sử dụng poppler_path)
                images = convert_from_path(file_path, poppler_path=POPPLER_PATH)
                ocr_text = ""
                for i, image in enumerate(images):
                    page_text = pytesseract.image_to_string(image, lang='vie+eng')
                    ocr_text += page_text + "\n"
                return ocr_text
                
        except Exception as e:
            print(f"Lỗi khi đọc PDF: {e}")
            print("Lưu ý: Bạn có thể cần cài đặt Poppler để pdf2image hoạt động.")
        return text

    @staticmethod
    def load_docx(file_path: str) -> str:
        text = ""
        try:
            doc = Document(file_path)
            for para in doc.paragraphs:
                text += para.text + "\n"
        except Exception as e:
            print(f"Error loading DOCX: {e}")
        return text

    @staticmethod
    def load_txt(file_path: str) -> str:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            print(f"Error loading TXT: {e}")
            return ""

    @classmethod
    def get_text(cls, file_path: str) -> str:
        ext = os.path.splitext(file_path)[1].lower()
        if ext == '.pdf':
            return cls.load_pdf(file_path)
        elif ext == '.docx':
            return cls.load_docx(file_path)
        elif ext == '.txt':
            return cls.load_txt(file_path)
        return ""

    @staticmethod
    def chunk_text(text: str, chunk_size: int = 1000, chunk_overlap: int = 200) -> list:
        chunks = []
        if not text:
            return chunks
            
        start = 0
        while start < len(text):
            end = start + chunk_size
            chunks.append(text[start:end])
            start += chunk_size - chunk_overlap
        return chunks
