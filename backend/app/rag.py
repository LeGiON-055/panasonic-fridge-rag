"""
Retrieval-augmented answering. Kept deliberately simple and readable:
embed the question -> pull the top-k most similar chunks -> hand them to
Gemini with a strict grounding instruction -> return the answer plus the
sources (and any diagrams/photos from those pages) it was built from.

If Gemini is genuinely too busy (rate-limited or overloaded) even after a
couple of quick retries, this returns a clean, friendly message instead of
letting a raw API error reach whoever's using the live site.
"""
import json
import time
from typing import Optional

from google import genai
from google.genai import types

from app import config
from app.embeddings import embed_query, is_retryable
from app.vectorstore import query as vector_query
from app.schemas import AskResponse, Source

MAX_DISTANCE = 0.8

GENERATION_MAX_RETRY_ATTEMPTS = 3
GENERATION_RETRY_DELAYS_SECONDS = [3.0, 6.0]

BUSY_MESSAGE = (
    "The AI service is temporarily busy handling a lot of requests right now. "
    "This usually clears up within a minute or two -- please try asking again shortly."
)

_client: Optional[genai.Client] = None
_image_manifest: Optional[dict] = None


def _get_client() -> genai.Client:
    global _client
    if _client is None:
        if not config.GEMINI_API_KEY:
            raise RuntimeError("GEMINI_API_KEY is not set -- see backend/.env.example")
        _client = genai.Client(api_key=config.GEMINI_API_KEY)
    return _client


def _get_image_manifest() -> dict:
    global _image_manifest
    if _image_manifest is None:
        try:
            with open(config.IMAGE_MANIFEST_PATH) as f:
                _image_manifest = json.load(f)
        except FileNotFoundError:
            _image_manifest = {}
    return _image_manifest


def _images_for(source_file: str, page: int) -> list:
    return _get_image_manifest().get(f"{source_file}|{page}", [])


def _busy_response() -> AskResponse:
    return AskResponse(answer=BUSY_MESSAGE, sources=[], images=[], grounded=False)


def _build_context(documents, metadatas) -> str:
    blocks = []
    for doc, meta in zip(documents, metadatas):
        blocks.append(f"[Manual: {meta['manual']} | Page {meta['page']}]\n{doc}")
    return "\n\n---\n\n".join(blocks)


def _generate_with_retry(client: genai.Client, **kwargs):
    for attempt in range(1, GENERATION_MAX_RETRY_ATTEMPTS + 1):
        try:
            return client.models.generate_content(**kwargs)
        except Exception as e:
            if is_retryable(e) and attempt < GENERATION_MAX_RETRY_ATTEMPTS:
                delay = GENERATION_RETRY_DELAYS_SECONDS[attempt - 1]
                print(f"    (Gemini temporarily unavailable, retrying in {delay:.0f}s "
                      f"-- attempt {attempt}/{GENERATION_MAX_RETRY_ATTEMPTS})")
                time.sleep(delay)
                continue
            raise


def answer_question(question: str, model_filter: Optional[str] = None) -> AskResponse:
    try:
        query_embedding = embed_query(question)
    except Exception as e:
        if is_retryable(e):
            return _busy_response()
        raise

    results = vector_query(query_embedding, top_k=config.TOP_K, model_filter=model_filter)

    documents = results["documents"][0] if results["documents"] else []
    metadatas = results["metadatas"][0] if results["metadatas"] else []
    distances = results["distances"][0] if results["distances"] else []

    relevant = [
        (doc, meta) for doc, meta, dist in zip(documents, metadatas, distances)
        if dist <= MAX_DISTANCE
    ]

    if not relevant:
        return AskResponse(
            answer=(
                "I couldn't find anything in the indexed manuals that answers this. "
                "Try rephrasing, or check that the right manual has been ingested."
            ),
            sources=[],
            images=[],
            grounded=False,
        )

    context = _build_context([d for d, _ in relevant], [m for _, m in relevant])

    client = _get_client()
    try:
        response = _generate_with_retry(
            client,
            model=config.GENERATION_MODEL,
            contents=f"Manual excerpts:\n\n{context}\n\n---\n\nCustomer question: {question}",
            config=types.GenerateContentConfig(
                system_instruction=config.SYSTEM_PROMPT,
                max_output_tokens=config.MAX_ANSWER_TOKENS,
                temperature=0.2,
            ),
        )
    except Exception as e:
        if is_retryable(e):
            return _busy_response()
        raise

    sources = [
        Source(manual=meta["manual"], page=meta["page"], excerpt=doc[:220])
        for doc, meta in relevant
    ]

    finish_reason = None
    try:
        finish_reason = response.candidates[0].finish_reason
    except (AttributeError, IndexError, TypeError):
        pass
    if finish_reason is not None and "STOP" not in str(finish_reason):
        usage = getattr(response, "usage_metadata", None)
        print(f"    (warning: answer may be incomplete -- finish_reason={finish_reason}, "
              f"usage={usage})")

    images: list = []
    seen_images = set()
    for _, meta in relevant:
        for path in _images_for(meta["source_file"], meta["page"]):
            if path not in seen_images:
                seen_images.add(path)
                images.append(path)

    return AskResponse(answer=response.text or "", sources=sources, images=images, grounded=True)
