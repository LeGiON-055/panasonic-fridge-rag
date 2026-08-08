"""
Central configuration. Everything here can be overridden by environment
variables (see .env.example) so nothing sensitive is hard-coded.
"""
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent  # backend/

# --- Gemini API ---
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "gemini-embedding-001")
GENERATION_MODEL = os.getenv("GENERATION_MODEL", "gemini-flash-latest")

# --- Storage ---
MANUALS_DIR = Path(os.getenv("MANUALS_DIR", BASE_DIR / "data" / "manuals"))
CHROMA_DIR = Path(os.getenv("CHROMA_DIR", BASE_DIR / "vectorstore"))
COLLECTION_NAME = os.getenv("COLLECTION_NAME", "fridge_manuals")
IMAGES_DIR = Path(os.getenv("IMAGES_DIR", BASE_DIR / "data" / "manual_images"))
IMAGE_MANIFEST_PATH = CHROMA_DIR / "image_manifest.json"

# --- Chunking ---
CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "900"))       # characters
CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", "150")) # characters

# --- Retrieval / generation ---
TOP_K = int(os.getenv("TOP_K", "8"))
MAX_ANSWER_TOKENS = int(os.getenv("MAX_ANSWER_TOKENS", "2048"))

# --- CORS ---
# Comma-separated list of origins allowed to call this API in production.
# Defaults to "*" for local development only.
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "*").split(",")

SYSTEM_PROMPT = """You are a support assistant that answers questions about \
Panasonic refrigerators using ONLY the manual excerpts provided to you below.

Rules:
1. Answer only using the provided excerpts. Do not use outside knowledge about \
refrigerators in general, and do not guess at model-specific details.
2. If the excerpts don't contain the answer, say so plainly and suggest what the \
customer could do instead (e.g. check the model-specific manual, contact support) \
rather than guessing.
3. If excerpts come from more than one refrigerator model and they disagree, say \
so and briefly note the difference per model instead of picking one silently.
4. Always answer in the same language the question was asked in, even if the \
excerpt you're citing is in a different language.
5. Keep answers concise and practical. Use short steps or a short list for \
instructions. Mention the manual/model and page for anything safety-related.
6. Never invent a page number, model name, or error code that isn't present in \
the excerpts."""
