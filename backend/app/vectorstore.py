"""
Thin wrapper around a local, persisted Chroma collection. Deliberately
embedding-agnostic: callers pass in already-computed embedding vectors
(from app.embeddings, which calls the Gemini API) rather than relying on
Chroma's bundled default embedding function. This keeps the backend's
only external dependency for "intelligence" being the Gemini API — no
extra multi-hundred-MB ML model has to be downloaded or loaded at runtime,
which matters on a 512 MB free-tier host.
"""
from typing import List, Optional

import chromadb
from chromadb.config import Settings

from app import config


def get_client() -> chromadb.ClientAPI:
    config.CHROMA_DIR.mkdir(parents=True, exist_ok=True)
    return chromadb.PersistentClient(
        path=str(config.CHROMA_DIR),
        settings=Settings(anonymized_telemetry=False),
    )


def get_collection(reset: bool = False):
    client = get_client()
    if reset:
        try:
            client.delete_collection(config.COLLECTION_NAME)
        except Exception:
            pass  # collection didn't exist yet — fine
    return client.get_or_create_collection(
        name=config.COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"},
    )


def add_chunks(ids: List[str], embeddings: List[List[float]], documents: List[str], metadatas: List[dict]):
    collection = get_collection()
    # Chroma chokes on very large single calls; batch to be safe.
    batch_size = 100
    for i in range(0, len(ids), batch_size):
        collection.add(
            ids=ids[i:i + batch_size],
            embeddings=embeddings[i:i + batch_size],
            documents=documents[i:i + batch_size],
            metadatas=metadatas[i:i + batch_size],
        )


def query(embedding: List[float], top_k: int, model_filter: Optional[str] = None):
    collection = get_collection()
    where = {"manual": model_filter} if model_filter else None
    return collection.query(query_embeddings=[embedding], n_results=top_k, where=where)


def count() -> int:
    try:
        return get_collection().count()
    except Exception as e:
        print(f"    (vectorstore.count() failed: {type(e).__name__}: {e})")
        return 0