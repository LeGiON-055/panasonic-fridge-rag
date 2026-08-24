"""
Embeddings via the Gemini API (gemini-embedding-001). Kept as the only
place that knows about the embedding model, so swapping providers later
means editing one file.

Two different retry postures on purpose:
- embed_documents runs during ingestion, a one-time background job with
  nobody watching a spinner -- patient retries (up to 6 attempts, ~30s
  apart) are worth it to eventually succeed rather than fail fast.
- embed_query runs while a real person is waiting on a live chat answer --
  a couple of quick retries, then give up and let the caller show a clean
  "busy, try again" message, rather than making someone wait minutes.
"""
import re
import time
from typing import List

from google import genai
from google.genai import types

from app import config

_client = None

DEFAULT_BATCH_SIZE = 10
PAUSE_BETWEEN_BATCHES_SECONDS = 2.0
DOCUMENT_MAX_RETRY_ATTEMPTS = 6
DOCUMENT_RETRY_BASE_DELAY_SECONDS = 30.0

QUERY_MAX_RETRY_ATTEMPTS = 3
QUERY_RETRY_DELAYS_SECONDS = [3.0, 6.0]


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


def _retry_delay_from_error(e: Exception, default: float) -> float:
    match = re.search(r"retryDelay['\"]?\s*:\s*['\"]?(\d+(?:\.\d+)?)s", str(e))
    if match:
        return float(match.group(1)) + 3.0
    return default


def is_retryable(e: Exception) -> bool:
    text = str(e)
    return (
        getattr(e, "code", None) in (429, 503)
        or "RESOURCE_EXHAUSTED" in text
        or "UNAVAILABLE" in text
        or "high demand" in text.lower()
    )


def embed_documents(texts: List[str], batch_size: int = DEFAULT_BATCH_SIZE) -> List[List[float]]:
    """Embeds manual chunks at ingestion time (task_type=RETRIEVAL_DOCUMENT)."""
    client = _get_client()
    vectors: List[List[float]] = []
    total_batches = (len(texts) + batch_size - 1) // batch_size

    for batch_num, i in enumerate(range(0, len(texts), batch_size), start=1):
        batch = texts[i:i + batch_size]
        result = None
        for attempt in range(1, DOCUMENT_MAX_RETRY_ATTEMPTS + 1):
            try:
                result = client.models.embed_content(
                    model=config.EMBEDDING_MODEL,
                    contents=batch,
                    config=types.EmbedContentConfig(task_type="RETRIEVAL_DOCUMENT"),
                )
                break
            except Exception as e:
                if is_retryable(e) and attempt < DOCUMENT_MAX_RETRY_ATTEMPTS:
                    delay = _retry_delay_from_error(e, DOCUMENT_RETRY_BASE_DELAY_SECONDS)
                    print(f"    (rate limited by Gemini -- waiting {delay:.0f}s "
                          f"before retrying, attempt {attempt}/{DOCUMENT_MAX_RETRY_ATTEMPTS})")
                    time.sleep(delay)
                    continue
                raise

        vectors.extend(e.values for e in result.embeddings)
        print(f"    embedded batch {batch_num}/{total_batches} "
              f"({len(vectors)}/{len(texts)} chunks)")

        if batch_num < total_batches:
            time.sleep(PAUSE_BETWEEN_BATCHES_SECONDS)

    return vectors


def embed_query(text: str) -> List[float]:
    """Embeds a user's question at query time (task_type=RETRIEVAL_QUERY).
    Fails fast (a few seconds, not minutes) since a live request is
    waiting -- the caller is expected to show a friendly message if this
    ultimately raises."""
    client = _get_client()
    for attempt in range(1, QUERY_MAX_RETRY_ATTEMPTS + 1):
        try:
            result = client.models.embed_content(
                model=config.EMBEDDING_MODEL,
                contents=text,
                config=types.EmbedContentConfig(task_type="RETRIEVAL_QUERY"),
            )
            return result.embeddings[0].values
        except Exception as e:
            if is_retryable(e) and attempt < QUERY_MAX_RETRY_ATTEMPTS:
                delay = QUERY_RETRY_DELAYS_SECONDS[attempt - 1]
                print(f"    (Gemini busy during query embedding -- waiting {delay:.0f}s, "
                      f"attempt {attempt}/{QUERY_MAX_RETRY_ATTEMPTS})")
                time.sleep(delay)
                continue
            raise
