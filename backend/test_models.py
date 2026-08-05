"""
One-off: tries a trivial generate_content call against several candidate
models and reports which ones actually work for this API key — faster
than guessing one model name at a time via config.py + restart + retest.
Run from backend/, with your venv active: python test_models.py
"""
from dotenv import load_dotenv
import os
from google import genai

load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    raise SystemExit("GEMINI_API_KEY not found — check your .env")

client = genai.Client(api_key=api_key)

candidates = [
    "gemini-flash-latest",
    "gemini-2.5-flash",
    "gemini-2.5-flash-lite",
    "gemini-2.0-flash",
    "gemini-3-flash-preview",
    "gemini-3.1-flash-lite",
]

for model in candidates:
    try:
        resp = client.models.generate_content(model=model, contents="Say OK")
        print(f"WORKS   {model:30s} -> {resp.text.strip()[:40]!r}")
    except Exception as e:
        msg = str(e).split("\n")[0][:100]
        print(f"BLOCKED {model:30s} -> {msg}")