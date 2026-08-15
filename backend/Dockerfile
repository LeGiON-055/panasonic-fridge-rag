FROM python:3.12-slim

# poppler-utils + tesseract-ocr: not required to serve the pre-built index
# below, but kept so `python -m app.ingest` still works if you ever shell
# into this container to rebuild it.
RUN apt-get update && apt-get install -y --no-install-recommends \
    poppler-utils \
    tesseract-ocr \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app

# Pre-built vector store + extracted images — committed on this deploy
# branch only. Render's free tier has no persistent disk, so shipping the
# already-built index in the image (instead of rebuilding it, which would
# need the Gemini API key at build time) is what makes this work reliably.
COPY vectorstore ./vectorstore
COPY data/manual_images ./data/manual_images

RUN mkdir -p data/manuals

EXPOSE 8000
CMD uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}