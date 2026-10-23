"""PDF -> pages -> chunks (with page/chapter/section/printed page) -> embeddings -> ChromaDB.
Run: python ingest.py   (re-running rebuilds the collection, so no duplicates)"""
import re, sys, time
from pathlib import Path
from dotenv import load_dotenv
from pypdf import PdfReader
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from langchain_google_genai import GoogleGenerativeAIEmbeddings

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(Path(__file__).parent / ".env")
PDF = ROOT / "data" / "designs_manual.pdf"
DB = str(ROOT / "chroma_db")
COLLECTION = "designs_manual"
# Chapter start pages from the PDF's own table of contents (page 2)
CHAPTERS = [(5,"1","Introduction"),(7,"2","Important definitions"),(11,"3","Filing of Design Application"),
 (24,"4","Examination and registration of designs"),(34,"5","Patent Office Journal"),
 (35,"6","Piracy of registered designs and consequences thereof"),(37,"7","Post registration procedures"),
 (45,"8","Transfer of rights"),(47,"9","General Services"),(50,"10","Use and acquisition of registered design by Government"),
 (51,"11","General powers of Controller"),(54,"12","Evidences etc."),(58,"13","Restrictive conditions in contract etc."),
 (60,"14","Appeals"),(61,"15","Requirements before delivery on sales"),(63,"16","Timelines")]

def chapter_of(page):
    best = None
    for start, num, title in CHAPTERS:
        if page >= start: best = (num, title)
    return best

def printed_page(text):
    m = re.search(r"(\d{1,3})\s*\Z", text.strip())
    return int(m.group(1)) if m else None

def embeddings():
    return GoogleGenerativeAIEmbeddings(model="models/gemini-embedding-001")

def ingest():
    if not PDF.exists(): raise FileNotFoundError(f"PDF not found: {PDF}")
    reader = PdfReader(str(PDF))
    splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=150)
    chunks = []
    for i, page in enumerate(reader.pages, start=1):
        text = page.extract_text() or ""
        if not text.strip(): continue
        ch = chapter_of(i)
        pp = printed_page(text)
        for part in splitter.split_text(text):
            sec = re.search(r"\b(\d{2}\.\d{2}(?:\.\d{2}){0,2})\b", part)
            chunks.append(Document(page_content=part, metadata={
                "source": PDF.name, "page": i, "printed_page": pp if pp else -1,
                "chapter_no": ch[0] if ch else "", "chapter_title": ch[1] if ch else "",
                "section": sec.group(1) if sec else ""}))
    if not chunks: raise RuntimeError("No text could be extracted from the PDF")
    vector_store = Chroma(collection_name=COLLECTION, persist_directory=DB, embedding_function=embeddings())
    try:
        vector_store.delete_collection()
    except Exception:
        pass
    vector_store = Chroma(collection_name=COLLECTION, persist_directory=DB, embedding_function=embeddings())
    
    batch_size = 40
    for i in range(0, len(chunks), batch_size):
        batch = chunks[i:i + batch_size]
        for attempt in range(5):
            try:
                vector_store.add_documents(batch)
                print(f"Indexed chunks {i+1} to {min(i+batch_size, len(chunks))} of {len(chunks)}")
                time.sleep(1)
                break
            except Exception as e:
                if "RESOURCE_EXHAUSTED" in str(e) or "429" in str(e):
                    print(f"Rate limited (attempt {attempt+1}/5). Waiting 25s...")
                    time.sleep(25)
                else:
                    raise e
    return {"pages": len(reader.pages), "chunks": len(chunks)}

if __name__ == "__main__":
    try: print(ingest())
    except Exception as e: print("Ingestion failed:", e); sys.exit(1)
