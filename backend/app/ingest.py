"""
Builds the vector store from every PDF in data/manuals/.

Run from the backend/ directory:
    python -m app.ingest

Re-run this any time you add, remove, or replace a manual PDF.
"""
import json
import sys
import time
from pathlib import Path

from app import config
from app.pdf_utils import chunk_manual
from app.embeddings import embed_documents
from app.vectorstore import get_collection, add_chunks
from app.image_utils import extract_images


def run() -> None:
    pdf_paths = sorted(config.MANUALS_DIR.glob("*.pdf"))
    if not pdf_paths:
        print(f"No PDFs found in {config.MANUALS_DIR}. Add manual PDFs there and re-run.")
        sys.exit(1)

    print(f"Found {len(pdf_paths)} manual(s) in {config.MANUALS_DIR}")

    all_chunks = []
    image_manifest: dict = {}  # "{source_file}|{page}" -> [relative image paths]

    for pdf_path in pdf_paths:
        t0 = time.time()
        chunks = chunk_manual(pdf_path, config.CHUNK_SIZE, config.CHUNK_OVERLAP)
        all_chunks.extend(chunks)

        page_images = extract_images(pdf_path, config.IMAGES_DIR)
        for page, paths in page_images.items():
            image_manifest[f"{pdf_path.name}|{page}"] = paths
        n_images = sum(len(v) for v in page_images.values())

        print(f"  {pdf_path.name:45s} {len(chunks):4d} chunks, {n_images:3d} images  ({time.time() - t0:.1f}s)")

    if not all_chunks:
        print("No text could be extracted from any manual. Nothing to index.")
        sys.exit(1)

    print(f"\nTotal chunks: {len(all_chunks)}")
    print(f"Embedding with {config.EMBEDDING_MODEL} ...")

    t0 = time.time()
    texts = [c.text for c in all_chunks]
    embeddings = embed_documents(texts)
    print(f"Embedded in {time.time() - t0:.1f}s")

    print("Resetting collection and writing to Chroma ...")
    get_collection(reset=True)  # ensures a clean slate before add_chunks
    ids = [f"{c.source_file}-p{c.page}-{i}" for i, c in enumerate(all_chunks)]
    metadatas = [{"manual": c.manual, "source_file": c.source_file, "page": c.page} for c in all_chunks]
    add_chunks(ids=ids, embeddings=embeddings, documents=texts, metadatas=metadatas)

    config.CHROMA_DIR.mkdir(parents=True, exist_ok=True)
    with open(config.IMAGE_MANIFEST_PATH, "w") as f:
        json.dump(image_manifest, f)
    n_total_images = sum(len(v) for v in image_manifest.values())

    print(f"\nDone. Indexed {len(all_chunks)} chunks and {n_total_images} images "
          f"from {len(pdf_paths)} manual(s) into {config.CHROMA_DIR}")


if __name__ == "__main__":
    run()
