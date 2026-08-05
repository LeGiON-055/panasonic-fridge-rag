"""
Embeddings via the Gemini API (gemini-embedding-001). Kept as the only
place that knows about the embedding model, so swapping providers later
means editing one file.

Why an API-based embedding model instead of a local sentence-transformers
model: this backend is meant to run on a free-tier host with ~512 MB RAM.
Loading a local transformer model comfortably blows that budget; calling
an embedding API does not.

Batching is deliberately conservative (small batches + a pause between
them + retry-with-backoff on 429s) because the Gemini free tier allows
only 100 embed_content requests/minute, and firing a big corpus at it
without pacing trips that limit almost immediately.
"""
import re
import time
from typing import List

from google import genai
from google.genai import types, errors

from app import config

_client = None

# Free-tier embed_content quota is 100 requests/minute. Small batches +
# a pause between them keeps us comfortably under that without needing to
# know the exact per-item accounting the API uses internally.
DEFAULT_BATCH_SIZE = 10
PAUSE_BETWEEN_BATCHES_SECONDS = 2.0
MAX_RETRY_ATTEMPTS = 6
DEFAULT_RETRY_DELAY_SECONDS = 30.0


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


def _retry_delay_from_error(e: Exception) -> float:
    """Gemini's 429 responses include a suggested retryDelay (e.g. '36s') —
    use it if present, plus a small buffer, instead of guessing."""
    match = re.search(r"retryDelay['\"]?\s*:\s*['\"]?(\d+(?:\.\d+)?)s", str(e))
    if match:
        return float(match.group(1)) + 3.0
    return DEFAULT_RETRY_DELAY_SECONDS


def _embed_with_retry(client: genai.Client, **kwargs):
    for attempt in range(1, MAX_RETRY_ATTEMPTS + 1):
        try:
            return client.models.embed_content(**kwargs)
        except errors.ClientError as e:
            is_rate_limit = getattr(e, "code", None) == 429 or "RESOURCE_EXHAUSTED" in str(e)
            if is_rate_limit and attempt < MAX_RETRY_ATTEMPTS:
                delay = _retry_delay_from_error(e)
                print(f"    (rate limited by Gemini — waiting {delay:.0f}s "
                      f"before retrying, attempt {attempt}/{MAX_RETRY_ATTEMPTS})")
                time.sleep(delay)
                continue
            raise


def embed_documents(texts: List[str], batch_size: int = DEFAULT_BATCH_SIZE) -> List[List[float]]:
    """Embeds manual chunks at ingestion time (task_type=RETRIEVAL_DOCUMENT)."""
    client = _get_client()
    vectors: List[List[float]] = []
    total_batches = (len(texts) + batch_size - 1) // batch_size

    for batch_num, i in enumerate(range(0, len(texts), batch_size), start=1):
        batch = texts[i:i + batch_size]
        result = _embed_with_retry(
            client,
            model=config.EMBEDDING_MODEL,
            contents=batch,
            config=types.EmbedContentConfig(task_type="RETRIEVAL_DOCUMENT"),
        )
        vectors.extend(e.values for e in result.embeddings)
        print(f"    embedded batch {batch_num}/{total_batches} "
              f"({len(vectors)}/{len(texts)} chunks)")

        if batch_num < total_batches:
            time.sleep(PAUSE_BETWEEN_BATCHES_SECONDS)

    return vectors


def embed_query(text: str) -> List[float]:
    """Embeds a user's question at query time (task_type=RETRIEVAL_QUERY —
    Gemini optimizes query and document embeddings slightly differently for
    retrieval, so it matters that this matches embed_documents)."""
    client = _get_client()
    result = _embed_with_retry(
        client,
        model=config.EMBEDDING_MODEL,
        contents=text,
        config=types.EmbedContentConfig(task_type="RETRIEVAL_QUERY"),
    )
    return result.embeddings[0].values