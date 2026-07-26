"""
Embeddings via the Gemini API (gemini-embedding-001). Kept as the only
place that knows about the embedding model, so swapping providers later
means editing one file.

Why an API-based embedding model instead of a local sentence-transformers
model: this backend is meant to run on a free-tier host with ~512 MB RAM.
Loading a local transformer model comfortably blows that budget; calling
an embedding API does not.
"""
from typing import List

from google import genai
from google.genai import types

from app import config

_client = None


def _get_client() -> genai.Client:
    global _client
    if _client is None:
        if not config.GEMINI_API_KEY:
            raise RuntimeError(
                "GEMINI_API_KEY is not set. Copy backend/.env.example to backend/.env "
                "and add your key (https://aistudio.google.com/apikey)."
            )
        _client = genai.Client(api_key=config.GEMINI_API_KEY)
    return _client


def embed_documents(texts: List[str], batch_size: int = 32) -> List[List[float]]:
    """Embeds manual chunks at ingestion time (task_type=RETRIEVAL_DOCUMENT)."""
    client = _get_client()
    vectors: List[List[float]] = []
    for i in range(0, len(texts), batch_size):
        batch = texts[i:i + batch_size]
        result = client.models.embed_content(
            model=config.EMBEDDING_MODEL,
            contents=batch,
            config=types.EmbedContentConfig(task_type="RETRIEVAL_DOCUMENT"),
        )
        vectors.extend(e.values for e in result.embeddings)
    return vectors


def embed_query(text: str) -> List[float]:
    """Embeds a user's question at query time (task_type=RETRIEVAL_QUERY —
    Gemini optimizes query and document embeddings slightly differently for
    retrieval, so it matters that this matches embed_documents)."""
    client = _get_client()
    result = client.models.embed_content(
        model=config.EMBEDDING_MODEL,
        contents=text,
        config=types.EmbedContentConfig(task_type="RETRIEVAL_QUERY"),
    )
    return result.embeddings[0].values
