# Designs Law Assistant (React + FastAPI + LangChain + ChromaDB)

RAG chatbot over the *Manual of Designs Practice & Procedure* (Office of the CGPDTM, 87 pp).
Answers cite chapter / section / PDF page and reply exactly `Not found` when the PDF has no answer.

## Flow
PDF -> pypdf (page by page) -> chunks (1000 chars, 150 overlap, tagged with PDF page, printed page, chapter, section)
-> Gemini embeddings -> ChromaDB -> question -> top-5 retrieval + distance check
-> Gemini validates the evidence and answers as JSON (`supported` true/false) -> citations -> React UI.

## Structure
backend/ (main.py API, rag.py, ingest.py) · frontend/ (Vite + React) · data/designs_manual.pdf · chroma_db/ (generated)
The older terminal version (`ingest.py`, `ask.py` in the repo root) is still included.

## Run
```bash
# Terminal 1 - backend
cd backend
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env      # add your NEW GOOGLE_API_KEY
python ingest.py
uvicorn main:app --reload --port 8000

# Terminal 2 - frontend
cd frontend
npm install
npm run dev               # open http://localhost:5173
```

## Answers (checked by reading the PDF text; the web app itself still needs to be run to capture screenshots)
1. 10 years from registration, extendable by 5 years - Ch.6 Sec 06.04 p.36; Ch.7 Sec 07.02 p.39
2. Locarno Classification (Third Schedule, Designs Rules 2001; India not a signatory) - Ch.3 Sec 03.06.02 p.14, p.20
3. Not found (designs manual only)
4. Not found as "current": Preface p.4 is signed by P.H. Kurian (2011 document)
5. Amount not stated; Sec 03.08 p.22 refers to the First Schedule of the Designs Rules, 2001

## Screenshots
Add your own after running the app (screenshots/ folder).

## Known limitations
No chat-history sidebar, document upload, or Forms & Fees panel yet. Section titles are not extracted (only section numbers).
The manual (2011) may not reflect later rule or fee changes.
