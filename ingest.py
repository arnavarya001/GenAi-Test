"""Step 1: load the PDF, split into chunks (keeping page + chapter), store in ChromaDB."""
import os, re
from dotenv import load_dotenv
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from langchain_google_genai import GoogleGenerativeAIEmbeddings

load_dotenv()
PDF_PATH = "Manual_of_Designs_Practice_and_Procedure.pdf"
DB_DIR = "chroma_db"

# Chapter -> starting page, taken from the PDF's table of contents (printed page == PDF page)
CHAPTERS = [
    (5, "Chapter 1 - Introduction"), (7, "Chapter 2 - Important definitions"),
    (11, "Chapter 3 - Filing of Design Application"),
    (24, "Chapter 4 - Examination and registration of designs"),
    (34, "Chapter 5 - Patent Office Journal"),
    (35, "Chapter 6 - Piracy of registered designs and consequences thereof"),
    (37, "Chapter 7 - Post registration procedures"), (45, "Chapter 8 - Transfer of rights"),
    (47, "Chapter 9 - General Services"),
    (50, "Chapter 10 - Use and acquisition of registered design by Government"),
    (51, "Chapter 11 - General powers of Controller"), (54, "Chapter 12 - Evidences etc."),
    (58, "Chapter 13 - Restrictive conditions in contract etc."), (60, "Chapter 14 - Appeals"),
    (61, "Chapter 15 - Requirements before delivery on sales"), (63, "Chapter 16 - Timelines"),
]

def chapter_for(page: int) -> str:
    name = "Front matter / Preface"
    for start, title in CHAPTERS:
        if page >= start:
            name = title
    return name

def main():
    pages = PyPDFLoader(PDF_PATH).load()
    splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=150)
    chunks = []
    for doc in splitter.split_documents(pages):
        page = doc.metadata["page"] + 1  # PyPDF is 0-indexed
        doc.metadata["page"] = page
        doc.metadata["chapter"] = chapter_for(page)
        m = re.search(r"\b(\d{2}\.\d{2}(?:\.\d{2})?)\b", doc.page_content)  # e.g. 06.04
        doc.metadata["section"] = m.group(1) if m else "n/a"
        chunks.append(doc)

    emb = GoogleGenerativeAIEmbeddings(model="models/gemini-embedding-001")
    Chroma.from_documents(chunks, emb, persist_directory=DB_DIR)
    print(f"Indexed {len(chunks)} chunks from {len(pages)} pages into '{DB_DIR}/'")

if __name__ == "__main__":
    main()
