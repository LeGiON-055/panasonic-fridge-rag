from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app import config
from app.schemas import AskRequest, AskResponse, HealthResponse
from app.rag import answer_question
from app.vectorstore import count as vectorstore_count

app = FastAPI(
    title="Panasonic Refrigerator Manual Assistant API",
    description="RAG API that answers customer questions from refrigerator manual PDFs.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=config.ALLOWED_ORIGINS,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

# Diagrams/photos extracted from manual pages at ingestion time (see
# app/image_utils.py) — AskResponse.images gives paths relative to this.
config.IMAGES_DIR.mkdir(parents=True, exist_ok=True)
app.mount("/images", StaticFiles(directory=str(config.IMAGES_DIR)), name="images")


@app.get("/api/health", response_model=HealthResponse)
def health() -> HealthResponse:
    n = vectorstore_count()
    return HealthResponse(status="ok" if n > 0 else "no_index", manuals_indexed=-1, chunks_indexed=n)


@app.post("/api/ask", response_model=AskResponse)
def ask(request: AskRequest) -> AskResponse:
    if vectorstore_count() == 0:
        raise HTTPException(
            status_code=503,
            detail="No manuals indexed yet. Run `python -m app.ingest` first.",
        )
    try:
        return answer_question(request.question, model_filter=request.model_filter)
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        # Catches Gemini API errors (bad model name, quota, etc.) so the
        # frontend gets a real error message instead of a raw 500 that
        # CORS then hides behind a fake "can't reach backend" message.
        raise HTTPException(status_code=500, detail=f"Gemini API error: {e}")
