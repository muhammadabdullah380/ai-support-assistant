"""Lightweight SQLite store for document metadata and query analytics.

Chroma holds the vectors; this holds everything the admin dashboard needs
to list/delete documents and show resolved-vs-unknown stats.
"""
import sqlite3
import time
from contextlib import contextmanager
from app.config import settings


def init_db():
    with _conn() as c:
        c.execute("""
            CREATE TABLE IF NOT EXISTS documents (
                doc_id TEXT PRIMARY KEY,
                filename TEXT NOT NULL,
                chunk_count INTEGER NOT NULL,
                uploaded_at REAL NOT NULL
            )
        """)
        c.execute("""
            CREATE TABLE IF NOT EXISTS query_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                question TEXT NOT NULL,
                resolved INTEGER NOT NULL,
                created_at REAL NOT NULL
            )
        """)


@contextmanager
def _conn():
    conn = sqlite3.connect(settings.SQLITE_PATH)
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def add_document_record(doc_id: str, filename: str, chunk_count: int):
    with _conn() as c:
        c.execute(
            "INSERT INTO documents (doc_id, filename, chunk_count, uploaded_at) VALUES (?, ?, ?, ?)",
            (doc_id, filename, chunk_count, time.time()),
        )


def delete_document_record(doc_id: str):
    with _conn() as c:
        c.execute("DELETE FROM documents WHERE doc_id = ?", (doc_id,))


def list_documents():
    with _conn() as c:
        rows = c.execute(
            "SELECT doc_id, filename, chunk_count, uploaded_at FROM documents ORDER BY uploaded_at DESC"
        ).fetchall()
    return [
        {"doc_id": r[0], "filename": r[1], "chunk_count": r[2], "uploaded_at": r[3]}
        for r in rows
    ]


def log_query(session_id: str, question: str, resolved: bool):
    with _conn() as c:
        c.execute(
            "INSERT INTO query_logs (session_id, question, resolved, created_at) VALUES (?, ?, ?, ?)",
            (session_id, question, int(resolved), time.time()),
        )


def get_analytics():
    with _conn() as c:
        total = c.execute("SELECT COUNT(*) FROM query_logs").fetchone()[0]
        resolved = c.execute("SELECT COUNT(*) FROM query_logs WHERE resolved = 1").fetchone()[0]
    return {
        "total_queries": total,
        "resolved": resolved,
        "unknown": total - resolved,
    }
