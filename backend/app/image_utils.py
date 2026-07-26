"""
Extracts embedded raster images (diagrams, control-panel photos, clearance
illustrations, etc.) from manual PDFs, so answers can show a picture
alongside the text instead of leaving anything visual behind.

Uses PyMuPDF (fitz) rather than a hosted parser (e.g. LlamaParse): it's a
local, open-source library with no extra API key or network dependency,
which fits this project's "minimal external services" approach — the same
reason ingestion doesn't depend on LangChain/LlamaIndex either.
"""
import re
from pathlib import Path
from typing import Dict, List

import fitz  # PyMuPDF

# Filters out small decorative elements (icons, bullet glyphs, background
# masks) that PDFs are full of — see pdf-reading skill notes on this.
MIN_DIMENSION_PX = 150


def _safe_dirname(pdf_filename: str) -> str:
    stem = pdf_filename[:-4] if pdf_filename.lower().endswith(".pdf") else pdf_filename
    return re.sub(r"[^A-Za-z0-9_-]", "_", stem)


def extract_images(pdf_path: Path, output_dir: Path) -> Dict[int, List[str]]:
    """
    Extracts images from a manual PDF into output_dir/<manual-slug>/, and
    returns a {page_number: [relative_image_paths]} mapping (paths are
    relative to output_dir, so they can be served directly as static files).
    """
    manual_slug = _safe_dirname(pdf_path.name)
    manual_dir = output_dir / manual_slug
    manual_dir.mkdir(parents=True, exist_ok=True)

    page_images: Dict[int, List[str]] = {}
    doc = fitz.open(str(pdf_path))
    try:
        for page_num, page in enumerate(doc, start=1):
            seen_xrefs = set()
            for img_index, img in enumerate(page.get_images(full=True)):
                xref = img[0]
                if xref in seen_xrefs:
                    continue  # same image referenced twice on one page
                seen_xrefs.add(xref)

                try:
                    pix = fitz.Pixmap(doc, xref)
                    if pix.width < MIN_DIMENSION_PX or pix.height < MIN_DIMENSION_PX:
                        continue
                    if pix.colorspace is None or pix.colorspace.name not in ("DeviceGray", "DeviceRGB"):
                        pix = fitz.Pixmap(fitz.csRGB, pix)
                    if pix.alpha:
                        pix = fitz.Pixmap(pix, 0)  # drop alpha — PNG save is pickier with it in some colorspaces

                    filename = f"page{page_num}_{img_index}.png"
                    pix.save(str(manual_dir / filename))
                    page_images.setdefault(page_num, []).append(f"{manual_slug}/{filename}")
                except Exception as e:
                    # A handful of malformed/exotic-colorspace images shouldn't
                    # take down ingestion for the whole manual.
                    print(f"    (skipped one image on page {page_num}: {e})")
                    continue
    finally:
        doc.close()

    return page_images
