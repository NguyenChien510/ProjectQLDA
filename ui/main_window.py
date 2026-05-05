from fastapi import FastAPI, UploadFile, File, Form, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import shutil
import os
from services.rag_service import RAGService

app = FastAPI()
rag_service = RAGService()

# Setup paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
UPLOAD_DIR = os.path.join(BASE_DIR, "data", "uploads")
if not os.path.exists(UPLOAD_DIR):
    os.makedirs(UPLOAD_DIR)

app.mount("/static", StaticFiles(directory=os.path.join(BASE_DIR, "static")), name="static")
templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "ui", "templates"))

@app.get("/", response_class=HTMLResponse)
async def read_item(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/sessions")
async def get_sessions():
    return rag_service.history.get_all_sessions()

@app.get("/history/{file_id}")
async def get_history(file_id: str):
    return rag_service.history.get_messages(file_id)

@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    file_path = os.path.join(UPLOAD_DIR, file.filename)
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    file_id = rag_service.process_new_file(file_path, file.filename)
    if file_id:
        return {"file_id": file_id, "file_name": file.filename}
    return JSONResponse(status_code=400, content={"message": "Không thể xử lý file"})

@app.post("/chat")
async def chat(file_id: str = Form(...), message: str = Form(...)):
    answer = rag_service.get_answer(file_id, message)
    return {"answer": answer}
