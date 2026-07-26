from typing import List, Optional
from pydantic import BaseModel, Field


class AskRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=1000)
    # Optional: let the frontend restrict retrieval to one model's manual,
    # e.g. if the customer already told us which fridge they own.
    model_filter: Optional[str] = None


class Source(BaseModel):
    manual: str        # friendly manual/model label, e.g. "NR-CY550"
    page: int
    excerpt: str        # short snippet of the retrieved chunk, for transparency


class AskResponse(BaseModel):
    answer: str
    sources: List[Source]
    images: List[str] = []  # relative paths, served under /images/ — see main.py
    grounded: bool       # False if retrieval found nothing relevant enough


class HealthResponse(BaseModel):
    status: str
    manuals_indexed: int
    chunks_indexed: int
