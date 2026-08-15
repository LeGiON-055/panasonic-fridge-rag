FROM python:3.12-slim

# Without this, plain print() output gets stuck in a buffer and never
# reaches Render's captured logs — only properly-flushed loggers (like
# uvicorn's own INFO lines) show up otherwise.
ENV PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    poppler-utils \
    tesseract-ocr \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app

COPY vectorstore ./vectorstore
COPY data/manual_images ./data/manual_images

RUN mkdir -p data/manuals

EXPOSE 8000
CMD uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}