# src/utils/rag_pdf_chat.py
"""
Ephemeral RAG engine for user-uploaded PDFs.

Design constraints:
  - Fully in-memory: no ChromaDB is persisted to disk, no data saved to MongoDB.
  - Each uploaded PDF gets its own session keyed by a UUID.
  - Sessions expire (LRU eviction) after MAX_SESSIONS uploads to avoid memory bloat.
  - Uses LangChain + GoogleGenerativeAI embeddings + Chroma in-memory vectorstore.
  - Query side uses Gemini 2.5-flash via the google-genai client (same as the existing
    chat.py so we reuse the same API key).
"""

import io
import uuid
import logging
from collections import OrderedDict
from typing import Optional

from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain_google_genai import GoogleGenerativeAIEmbeddings

from config.settings import settings

logger = logging.getLogger(__name__)

# ── Constants ─────────────────────────────────────────────────────────────────
CHUNK_SIZE    = 800
CHUNK_OVERLAP = 150
TOP_K         = 5
MAX_SESSIONS  = 10          # keep at most 10 in-memory sessions

# ── Session store: session_id → { vectorstore, filename, page_count } ─────────
_sessions: "OrderedDict[str, dict]" = OrderedDict()


# ── Public API ────────────────────────────────────────────────────────────────

def ingest_pdf(pdf_bytes: bytes, filename: str) -> str:
    """
    Chunk + embed a PDF file and store the vectorstore in memory.

    Args:
        pdf_bytes:  Raw bytes of the uploaded PDF.
        filename:   Original filename (used in chunk metadata).

    Returns:
        session_id  A UUID string the frontend passes back on every chat turn.

    Raises:
        ValueError  If the PDF contains no extractable text.
    """
    # Evict oldest session if we're at the cap
    while len(_sessions) >= MAX_SESSIONS:
        evicted_id, _ = _sessions.popitem(last=False)
        logger.info(f"RAG: evicted session {evicted_id} (cap reached)")

    # Write bytes to a NamedTemporaryFile so PyPDFLoader can open it
    import tempfile, os
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
        tmp.write(pdf_bytes)
        tmp_path = tmp.name

    try:
        loader = PyPDFLoader(tmp_path)
        pages  = loader.load()
    finally:
        try:
            os.unlink(tmp_path)
        except Exception:
            pass

    if not pages:
        raise ValueError("PDF appears to be empty or contains no extractable text.")

    # Stamp source metadata
    for page in pages:
        page.metadata["source"] = filename

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        separators=["\n\n", "\n", ".", " ", ""],
    )
    chunks = splitter.split_documents(pages)

    if not chunks:
        raise ValueError("Could not extract any text chunks from the PDF.")

    logger.info(f"RAG: '{filename}' → {len(pages)} pages, {len(chunks)} chunks")

    # Build in-memory Chroma (no persist_directory = stays in RAM)
    embeddings = GoogleGenerativeAIEmbeddings(
        model="models/gemini-embedding-001",
        google_api_key=settings.gemini_api_key,
    )
    vectorstore = Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
    )

    session_id = str(uuid.uuid4())
    _sessions[session_id] = {
        "vectorstore": vectorstore,
        "filename":    filename,
        "page_count":  len(pages),
        "chunk_count": len(chunks),
    }
    # Move to end (most recently used)
    _sessions.move_to_end(session_id)

    logger.info(f"RAG: new session {session_id} for '{filename}'")
    return session_id


def get_session_info(session_id: str) -> Optional[dict]:
    """Return metadata about a session (filename, page_count) or None."""
    sess = _sessions.get(session_id)
    if not sess:
        return None
    return {"filename": sess["filename"], "page_count": sess["page_count"], "chunk_count": sess["chunk_count"]}


def answer(session_id: str, question: str, history: list) -> str:
    """
    Run a RAG query against the session's vectorstore and get a Gemini answer.

    Args:
        session_id: ID returned by ingest_pdf().
        question:   The user's current message.
        history:    List of {role, content} dicts (most recent 20).

    Returns:
        The AI's reply string.

    Raises:
        KeyError   If session_id is not found.
        Exception  On Gemini or retrieval error.
    """
    if session_id not in _sessions:
        raise KeyError(f"Session '{session_id}' not found. The PDF may have been cleared.")

    sess = _sessions[session_id]
    # Touch to keep it fresh (move to end of LRU)
    _sessions.move_to_end(session_id)

    vectorstore: Chroma = sess["vectorstore"]

    # ── Retrieve top-k chunks ─────────────────────────────────────────────
    docs = vectorstore.similarity_search(question, k=TOP_K)
    if not docs:
        return "I could not find relevant content in the uploaded PDF for that question."

    context_parts = []
    for i, doc in enumerate(docs, 1):
        page = doc.metadata.get("page", "?")
        context_parts.append(f"[Excerpt {i} | page {page}]\n{doc.page_content}")
    context = "\n\n".join(context_parts)

    # ── Build conversation history string ─────────────────────────────────
    history_lines = []
    for msg in history[-10:]:          # cap at last 10 turns
        role    = "User" if msg.get("role") == "user" else "Assistant"
        content = msg.get("content", "")
        history_lines.append(f"{role}: {content}")
    history_text = "\n".join(history_lines)

    # ── System prompt ─────────────────────────────────────────────────────
    prompt = f"""You are a helpful document assistant. A user has uploaded a PDF document and is chatting about its contents.

Rules:
- Answer using ONLY the information in the document excerpts below.
- Quote exact numbers, names, and text where possible.
- If the excerpts don't contain the answer, say: "I could not find that information in the uploaded document."
- You understand Hinglish (Hindi + English). Reply in the same language style the user uses.
- Be concise, clear, and helpful.

Document excerpts from '{sess["filename"]}':
----------------
{context}
----------------

Previous conversation:
{history_text}

User: {question}
Assistant:"""

    # ── Call Gemini ───────────────────────────────────────────────────────
    from google import genai as _genai
    client   = _genai.Client(api_key=settings.gemini_api_key)
    response = client.models.generate_content(
        model="models/gemini-2.5-flash",
        contents=prompt,
    )
    return response.text.strip()


def delete_session(session_id: str) -> bool:
    """Remove a session from memory. Returns True if it existed."""
    if session_id in _sessions:
        del _sessions[session_id]
        logger.info(f"RAG: deleted session {session_id}")
        return True
    return False
