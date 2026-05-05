import uvicorn
import os
from ui.main_window import app

if __name__ == "__main__":
    # Ensure data directories exist
    os.makedirs("data/uploads", exist_ok=True)
    os.makedirs("data/chroma", exist_ok=True)
    
    print("--- Ứng dụng Local RAG Chatbot đang khởi động ---")
    print("Truy cập: http://localhost:8000")
    uvicorn.run(app, host="0.0.0.0", port=8000)
