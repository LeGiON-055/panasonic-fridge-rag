FROM python:3.12-slim

# poppler-utils + tesseract-ocr: only needed for the OCR fallback path in
# app/pdf_utils.py, used when a manual PDF has no embedded text layer
# (i.e. it's a scanned image). Skip these if you know all your manuals
# have a real text layer — the app runs fine without them, OCR just won't
# be available.
RUN apt-get update && apt-get install -y --no-install-recommends \
    poppler-utils \
    tesseract-ocr \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app
RUN mkdir -p data/manuals vectorstore

# Render's free tier has no persistent disk — anything written at runtime
# (including the vector store) is wiped on every redeploy/restart. To get a
# working *deployed* demo on the free tier, the index has to be built into
# the image itself at Docker build time, which means the manual PDFs need
# to be present in the build context (i.e. not gitignored for whatever
# branch/repo you actually deploy from — see README's Deployment section
# for the trade-off this implies).
#
# Uncomment these two lines, and temporarily un-ignore your manual PDFs,
# to bake a ready-to-answer index into the image:
#
# COPY data/manuals ./data/manuals
# RUN --mount=type=secret,id=gemini_key \
#     GEMINI_API_KEY=$(cat /run/secrets/gemini_key) python -m app.ingest
#
# (Using a BuildKit secret keeps the API key out of the final image layers —
# pass it at build time with: docker build --secret id=gemini_key,env=GEMINI_API_KEY)

EXPOSE 8000
# Render (and similar PaaS hosts) inject $PORT and expect the app to bind to
# it; default to 8000 for local `docker run`.
CMD uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}
