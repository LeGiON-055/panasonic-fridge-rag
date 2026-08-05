"""
One-off: lists every Gemini model this API key can actually use for
generateContent/embedContent, so we stop guessing model names.
Run from backend/, with your venv active: python list_models.py
"""
from dotenv import load_dotenv
import os
from google import genai

load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    raise SystemExit("GEMINI_API_KEY not found — check your .env")

client = genai.Client(api_key=api_key)
models = list(client.models.list())

print("\n--- Models supporting generateContent ---")
for m in models:
    if "generateContent" in (getattr(m, "supported_actions", None) or []):
        print(" -", m.name)

print("\n--- Models supporting embedContent ---")
for m in models:
    if "embedContent" in (getattr(m, "supported_actions", None) or []):
        print(" -", m.name)