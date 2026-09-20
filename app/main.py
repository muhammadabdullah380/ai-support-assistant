import os
import shutil
import uuid
from pathlib import Path

from fastapi import FastAPI, UploadFile, File, Depends, HTTPException, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from slowapi.errors import RateLimitExceeded
from slowapi import _rate_limit_exceeded_handler

from app.config import settings
from app.security import verify_api_key, limiter
from app.schemas import ChatRequest, ChatResponse, DocumentInfo, AnalyticsResponse
from app.services import loaders, chunker, vectorstore, db, chat_service

# --- App setup -----------------------------------------------------------
os.makedirs(Path(settings.CHROMA_DIR).parent, exist_ok=True)
os.makedirs("./data/uploads", exist_ok=True)
db.init_db()

app = FastAPI(title="AI Support Knowledge Assistant")
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

STATIC_DIR = Path(__file__).parent / "static"
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/")
def serve_dashboard():
    return FileResponse(STATIC_DIR / "index.html")


# --- Documents -------------------------------------------------------------
@app.post("/api/documents/upload", response_model=DocumentInfo, dependencies=[Depends(verify_api_key)])
async def upload_document(file: UploadFile = File(...)):
    doc_id = str(uuid.uuid4())
    temp_path = f"./data/uploads/{doc_id}_{file.filename}"

    with open(temp_path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    try:
        text = loaders.extract_text(temp_path, file.filename)
    except ValueError as e:
        os.remove(temp_path)
        raise HTTPException(status_code=400, detail=str(e))

    chunks = chunker.chunk_text(text)
    if not chunks:
        os.remove(temp_path)
        raise HTTPException(status_code=400, detail="No extractable text found in file.")

    chunk_count = vectorstore.add_document(doc_id, file.filename, chunks)
    db.add_document_record(doc_id, file.filename, chunk_count)

    return DocumentInfo(doc_id=doc_id, filename=file.filename, chunk_count=chunk_count, uploaded_at=0)


@app.get("/api/documents", response_model=list[DocumentInfo], dependencies=[Depends(verify_api_key)])
def get_documents():
    return db.list_documents()


@app.delete("/api/documents/{doc_id}", dependencies=[Depends(verify_api_key)])
def delete_document(doc_id: str):
    vectorstore.delete_document(doc_id)
    db.delete_document_record(doc_id)
    return {"status": "deleted", "doc_id": doc_id}


# --- Chat --------------------------------------------------------------
@app.post("/api/chat", response_model=ChatResponse)
@limiter.limit("30/minute")
def chat(request: Request, body: ChatRequest):
    result = chat_service.answer_query(body.session_id, body.message)
    db.log_query(body.session_id, body.message, result["resolved"])
    return result


# --- Analytics -----------------------------------------------------------
@app.get("/api/analytics", response_model=AnalyticsResponse, dependencies=[Depends(verify_api_key)])
def analytics():
    return db.get_analytics()
