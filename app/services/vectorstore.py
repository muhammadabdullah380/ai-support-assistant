"""Wraps ChromaDB (local, persistent, free embeddings) for document chunks.

Incremental by design: adding a new document never touches existing chunks,
and deleting a document only removes its own chunk ids.
"""
import uuid
import chromadb
from chromadb.utils.embedding_functions import ONNXMiniLM_L6_V2
from app.config import settings

_client = chromadb.PersistentClient(path=settings.CHROMA_DIR)

# Force CPU-only execution. On some Macs, onnxruntime's CoreML execution
# provider intermittently fails ("Unable to compute the prediction") --
# CPU is slightly slower but reliable, and plenty fast for this use case.
_embedding_fn = ONNXMiniLM_L6_V2(preferred_providers=["CPUExecutionProvider"])

_collection = _client.get_or_create_collection(name="support_docs", embedding_function=_embedding_fn)


def add_document(doc_id: str, filename: str, chunks: list[str]) -> int:
    if not chunks:
        return 0

    ids = [f"{doc_id}::{i}" for i in range(len(chunks))]
    metadatas = [{"doc_id": doc_id, "filename": filename, "chunk_index": i} for i in range(len(chunks))]

    _collection.add(ids=ids, documents=chunks, metadatas=metadatas)
    return len(chunks)


def delete_document(doc_id: str) -> None:
    _collection.delete(where={"doc_id": doc_id})


def query(text: str, top_k: int = 4):
    """Returns list of dicts: {text, filename, doc_id, distance} sorted by relevance."""
    results = _collection.query(query_texts=[text], n_results=top_k)

    hits = []
    docs = results.get("documents", [[]])[0]
    metas = results.get("metadatas", [[]])[0]
    dists = results.get("distances", [[]])[0]

    for doc, meta, dist in zip(docs, metas, dists):
        hits.append({
            "text": doc,
            "filename": meta.get("filename"),
            "doc_id": meta.get("doc_id"),
            "distance": dist,
        })
    return hits