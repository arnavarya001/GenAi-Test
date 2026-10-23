"""Step 2: retrieve relevant chunks, answer with Gemini, print structured answer + citation.
Usage: python ask.py "your question"     (or run without args for the 5 assignment questions)
"""
import sys
from dotenv import load_dotenv
from langchain_chroma import Chroma
from langchain_google_genai import GoogleGenerativeAIEmbeddings, ChatGoogleGenerativeAI

load_dotenv()
DB_DIR = "chroma_db"
MAX_DISTANCE = 1.0   # Chroma distance; larger = less similar. Above this -> treat as not in document.

QUESTIONS = [
    "How long does a proprietor have copyright in a registered design, and can it be extended?",
    "Which classification system is used to register designs?",
    "What is the government fee to register a trademark?",
    "Who is the current Controller General of Patents?",
    "What is the fee to register a design?",
]

PROMPT = """You are a legal assistant for the Manual of Designs Practice & Procedure (IP India).
Answer ONLY from the context below. Do not use outside knowledge.
If the context does not contain the answer, reply with exactly: Not found
If the context only partly answers (e.g. it points to another document for the figure), say what the
document says and state clearly what it does not provide.
Keep the answer to 1-3 sentences.

Context:
{context}

Question: {question}
Answer:"""

def answer(question, db, llm):
    hits = db.similarity_search_with_score(question, k=4)
    hits = [(d, s) for d, s in hits if s <= MAX_DISTANCE]
    if not hits:
        return "Not found", []
    context = "\n\n".join(f"[Page {d.metadata['page']}] {d.page_content}" for d, _ in hits)
    raw = llm.invoke(PROMPT.format(context=context, question=question)).content
    if isinstance(raw, list):
        text = "".join(part.get("text", "") if isinstance(part, dict) else str(part) for part in raw).strip()
    else:
        text = str(raw).strip()
    if text.lower().startswith("not found"):
        return "Not found", []
    return text, [d for d, _ in hits]

def show(q, ans, docs):
    line = "=" * 70
    print(f"\n{line}\nQUESTION : {q}\n{line}\nANSWER   : {ans}")
    if docs:
        print("\nSOURCES:")
        seen = set()
        for d in docs:
            m = d.metadata
            key = (m.get("page"), m.get("section"))
            if key in seen:
                continue
            seen.add(key)
            ch = m.get("chapter") or (f"Chapter {m.get('chapter_no')} - {m.get('chapter_title')}" if m.get("chapter_title") else "General")
            sec = m.get("section") or "n/a"
            print(f"  - {ch} | Section {sec} | Page {m.get('page')}")
    else:
        print("SOURCES  : none (answer is not in the document)")

def main():
    emb = GoogleGenerativeAIEmbeddings(model="models/gemini-embedding-001")
    db = Chroma(collection_name="designs_manual", persist_directory=DB_DIR, embedding_function=emb)
    llm = ChatGoogleGenerativeAI(model="gemini-3.5-flash-lite")
    for q in (sys.argv[1:] and [" ".join(sys.argv[1:])]) or QUESTIONS:
        ans, docs = answer(q, db, llm)
        show(q, ans, docs)

if __name__ == "__main__":
    main()
