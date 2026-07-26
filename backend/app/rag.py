"""
Retrieval-augmented answering. Kept deliberately simple and readable:
embed the question -> pull the top-k most similar chunks -> hand them to
Gemini with a strict grounding instruction -> return the answer plus the
sources (and any diagrams/photos from those pages) it was built from.
"""
import json
from typing import Optional

from google import genai
from google.genai import types

from app import config
from app.embeddings import embed_query
from app.vectorstore import query as vector_query
from app.schemas import AskResponse, Source

# A similarity floor below which we don't trust the retrieved chunks enough
# to answer from them. Chroma returns cosine *distance* (0 = identical), so
# lower is more similar; this is the max distance we'll accept.
MAX_DISTANCE = 0.8

_client: Optional[genai.Client] = None
_image_manifest: Optional[dict] = None


def _get_client() -> genai.Client:
    global _client
    if _client is None:
        if not config.GEMINI_API_KEY:
            raise RuntimeError("GEMINI_API_KEY is not set — see backend/.env.example")
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


def _build_context(documents, metadatas) -> str:
    blocks = []
    for doc, meta in zip(documents, metadatas):
        blocks.append(f"[Manual: {meta['manual']} | Page {meta['page']}]\n{doc}")
    return "\n\n---\n\n".join(blocks)


def answer_question(question: str, model_filter: Optional[str] = None) -> AskResponse:
    query_embedding = embed_query(question)
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
            grounded=False,
        )

    context = _build_context([d for d, _ in relevant], [m for _, m in relevant])

    client = _get_client()
    response = client.models.generate_content(
        model=config.GENERATION_MODEL,
        contents=f"Manual excerpts:\n\n{context}\n\n---\n\nCustomer question: {question}",
        config=types.GenerateContentConfig(
            system_instruction=config.SYSTEM_PROMPT,
            max_output_tokens=config.MAX_ANSWER_TOKENS,
            temperature=0.2,
        ),
    )

    sources = [
        Source(manual=meta["manual"], page=meta["page"], excerpt=doc[:220])
        for doc, meta in relevant
    ]

    images: list = []
    seen_images = set()
    for _, meta in relevant:
        for path in _images_for(meta["source_file"], meta["page"]):
            if path not in seen_images:
                seen_images.add(path)
                images.append(path)

    return AskResponse(answer=response.text or "", sources=sources, images=images, grounded=True)
