"""Retrieval + evidence validation + grounded answer. Returns 'Not found' if the PDF doesn't support an answer."""
import json, re
from langchain_chroma import Chroma
from langchain_google_genai import ChatGoogleGenerativeAI
from ingest import DB, COLLECTION, embeddings

NOT_FOUND = "Not found"
MAX_DISTANCE = 1.1
PROMPT = """You answer questions about India's Manual of Designs Practice & Procedure using ONLY the context.
Never use outside knowledge. If the context does not directly answer the question, set supported=false.
If the context only points elsewhere for the exact figure (e.g. "fee is in the First Schedule"), set supported=false.
A question about trademarks, or about who currently holds an office, is unsupported unless the context states it.
Reply with JSON only: {{"supported": true|false, "answer": "simple English, 1-4 sentences", "pages": [PDF page numbers used]}}

Context:
{context}

Question: {question}"""

_db = _llm = None
def _init():
    global _db, _llm
    if _db is None:
        _db = Chroma(collection_name=COLLECTION, persist_directory=DB, embedding_function=embeddings())
        _llm = ChatGoogleGenerativeAI(model="gemini-3.5-flash-lite")

def count_chunks():
    _init(); return _db._collection.count()

def ask(question):
    _init()
    hits = [(d, s) for d, s in _db.similarity_search_with_score(question, k=5) if s <= MAX_DISTANCE]
    if not hits: return {"found": False, "answer": NOT_FOUND, "citations": []}
    ctx = "\n\n".join(f"[PDF page {d.metadata['page']}] {d.page_content}" for d, _ in hits)
    raw = _llm.invoke(PROMPT.format(context=ctx, question=question)).content
    if isinstance(raw, list):
        raw_str = "".join(part.get("text", "") if isinstance(part, dict) else str(part) for part in raw)
    else:
        raw_str = str(raw)
    try: data = json.loads(re.sub(r"^```(?:json)?|```$", "", raw_str.strip(), flags=re.M).strip())
    except Exception: raise RuntimeError("Model returned an unreadable response")
    if not data.get("supported"): return {"found": False, "answer": NOT_FOUND, "citations": []}
    used = set(data.get("pages") or [])
    cites, seen = [], set()
    for d, _ in hits:
        m = d.metadata
        if used and m["page"] not in used: continue
        key = (m["page"], d.page_content[:40])
        if key in seen: continue
        seen.add(key)
        cites.append({"source": m["source"], "page": m["page"],
            "printed_page": m["printed_page"] if m["printed_page"] > 0 else None,
            "chapter": f"Chapter {m['chapter_no']} - {m['chapter_title']}" if m["chapter_no"] else None,
            "section": m["section"] or None, "excerpt": d.page_content[:450]})
    return {"found": True, "answer": data["answer"], "citations": cites[:3]}
