import os
from fastapi import FastAPI, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
import ingest, rag

app = FastAPI(title="Designs Law Assistant")
app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:5173"], allow_methods=["*"], allow_headers=["*"])

class Q(BaseModel):
    question: str = Field(min_length=3, max_length=500)

def status():
    try: n = rag.count_chunks()
    except Exception: n = 0
    return {"pdf_present": ingest.PDF.exists(), "indexed_chunks": n, "ready": n > 0}

@app.get("/api/health")
def health(): return status()

@app.get("/api/document")
def document():
    from pypdf import PdfReader
    if not ingest.PDF.exists(): raise HTTPException(404, "PDF missing: put it at data/designs_manual.pdf")
    return {"filename": ingest.PDF.name, "title": "Manual of Designs Practice & Procedure (Office of the CGPDTM)",
            "pages": len(PdfReader(str(ingest.PDF)).pages), **status()}

@app.get("/api/pdf")
def pdf(): return FileResponse(ingest.PDF, media_type="application/pdf")

@app.post("/api/chat")
def chat(q: Q):
    if not status()["ready"]: raise HTTPException(503, "Document not indexed yet. Run: python ingest.py")
    try: return rag.ask(q.question.strip())
    except Exception as e: raise HTTPException(500, f"Could not generate answer: {e}")

@app.post("/api/ingest")
def run_ingest(x_admin_token: str = Header(default="")):
    tok = os.getenv("ADMIN_TOKEN", "")
    if tok and x_admin_token != tok: raise HTTPException(401, "Invalid admin token")
    try: return ingest.ingest()
    except Exception as e: raise HTTPException(500, f"Ingestion failed: {e}")
