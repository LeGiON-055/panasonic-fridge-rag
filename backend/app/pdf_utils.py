"""
PDF extraction + chunking, hand-rolled on purpose (no LangChain) so the
mechanics are easy to read, explain, and tweak.
"""
import glob
import re
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import List, NamedTuple

from pypdf import PdfReader

# Manuals are sometimes scanned images with no embedded text layer at all
# (true for at least one real Panasonic manual in this project's test set).
# Below this many characters, we treat a page as "no usable text" and fall
# back to OCR instead of indexing an empty/near-empty chunk.
MIN_PAGE_TEXT_CHARS = 20

# Checked once, not per-page — avoids spamming warnings for every page of
# every manual when these simply aren't installed (common on Windows,
# where neither ships by default; see README for install steps).
_OCR_TOOLS_AVAILABLE = shutil.which("pdftoppm") is not None and shutil.which("tesseract") is not None
_WARNED_MISSING_OCR = False


class Chunk(NamedTuple):
    text: str
    manual: str   # friendly model/manual label
    source_file: str
    page: int     # 1-indexed


def label_from_filename(filename: str) -> str:
    """
    Turns a manual's filename into a friendly citation label.

    'User_Manual_NR-CY550.pdf'            -> 'NR-CY550'
    'User_Manual_NR-BD418_BD468.pdf'      -> 'NR-BD418 / NR-BD468'
    'User_Manual_NR-BX418_BX468_Hindi.pdf'-> 'NR-BX418 / NR-BX468 (Hindi)'
    'BK-IOT-Onboarding_20250327.pdf'      -> 'Smart/IoT Setup Guide (MirAIe App)'
    """
    stem = filename[:-4] if filename.lower().endswith(".pdf") else filename

    if stem.lower().startswith("bk-iot-onboarding"):
        return "Smart/IoT Setup Guide (MirAIe App)"

    is_hindi = stem.lower().endswith("_hindi")
    if is_hindi:
        stem = stem[: -len("_Hindi")]

    stem = stem.replace("User_Manual_", "")

    if "_" in stem:
        match = re.match(r"(NR-[A-Za-z0-9]+)_([A-Za-z0-9]+)", stem)
        if match:
            prefix = re.match(r"(NR-)", match.group(1)).group(1)
            label = f"{match.group(1)} / {prefix}{match.group(2)}"
        else:
            label = stem.replace("_", " / ")
    else:
        label = stem

    return f"{label} (Hindi)" if is_hindi else label


_ocr_unavailable_warned = False


def _ocr_page(pdf_path: Path, page_num: int) -> str:
    """
    Rasterizes a single page and runs Tesseract OCR on it. Used only as a
    fallback for pages with no embedded text layer (scanned manuals).
    Requires poppler-utils (pdftoppm) and tesseract-ocr on PATH. If they're
    not installed, this skips OCR quietly instead of crashing ingestion —
    those specific pages just won't be indexed.
    """
    global _ocr_unavailable_warned
    with tempfile.TemporaryDirectory() as tmp:
        prefix = str(Path(tmp) / "page")
        try:
            subprocess.run(
                ["pdftoppm", "-jpeg", "-r", "200", "-f", str(page_num), "-l", str(page_num),
                 str(pdf_path), prefix],
                check=True, capture_output=True,
            )
            matches = glob.glob(f"{prefix}*.jpg")
            if not matches:
                return ""
            result = subprocess.run(
                ["tesseract", matches[0], "stdout"],
                check=True, capture_output=True, text=True,
            )
            return result.stdout
        except (FileNotFoundError, subprocess.CalledProcessError) as e:
            if not _ocr_unavailable_warned:
                print(f"    (OCR unavailable: {e}. Skipping OCR for pages with no text layer — "
                      f"install Poppler + Tesseract if you need scanned-manual support.)")
                _ocr_unavailable_warned = True
            return ""


def extract_pages(pdf_path: Path, ocr_fallback: bool = True) -> List[str]:
    """
    Returns a list of page texts, index 0 = page 1. Pages with little or no
    embedded text (scanned pages) are OCR'd instead, when ocr_fallback=True
    and the OCR tools are actually available — otherwise those pages just
    come back with whatever (possibly empty) text pypdf found, rather than
    failing the whole run. See README for installing poppler/tesseract if
    you want OCR working (mainly matters for scanned/image-only manuals).
    """
    global _WARNED_MISSING_OCR
    reader = PdfReader(str(pdf_path))
    pages = []
    for i, page in enumerate(reader.pages, start=1):
        text = page.extract_text() or ""
        needs_ocr = ocr_fallback and len(text.strip()) < MIN_PAGE_TEXT_CHARS

        if needs_ocr and not _OCR_TOOLS_AVAILABLE:
            if not _WARNED_MISSING_OCR:
                print("  (note: poppler/tesseract not found — pages with no text layer "
                      "will be skipped instead of OCR'd. See README for install steps.)")
                _WARNED_MISSING_OCR = True
            needs_ocr = False

        if needs_ocr:
            try:
                text = _ocr_page(pdf_path, i)
            except Exception as e:
                print(f"    (OCR failed on {pdf_path.name} page {i}, skipping that page: {e})")
                # fall through with whatever (possibly empty) text pypdf gave us

        pages.append(text)
    return pages


_WHITESPACE_RE = re.compile(r"[ \t]+")
_BLANKLINES_RE = re.compile(r"\n{2,}")
_SENTENCE_SPLIT_RE = re.compile(r"(?<=[.!?])\s+(?=[A-Z0-9\u0900-\u097F•●])")


def _normalize(text: str) -> str:
    text = text.replace("\r", " ")
    text = _WHITESPACE_RE.sub(" ", text)
    text = _BLANKLINES_RE.sub("\n\n", text)
    return text.strip()


def _split_sentences(text: str) -> List[str]:
    text = _normalize(text)
    text = text.replace("•", "\n• ").replace("●", "\n● ")
    sentences: List[str] = []
    for line in re.split(r"\n+", text):
        line = line.strip()
        if not line:
            continue
        sentences.extend(s.strip() for s in _SENTENCE_SPLIT_RE.split(line) if s.strip())
    return sentences


def chunk_text(text: str, chunk_size: int, overlap: int) -> List[str]:
    """
    Greedy sentence packing: fill a chunk up to ~chunk_size characters,
    then start the next chunk with the trailing ~overlap characters of
    the previous one so context isn't lost at chunk boundaries.
    """
    sentences = _split_sentences(text)
    chunks: List[str] = []
    current: List[str] = []
    current_len = 0

    for sent in sentences:
        if current and current_len + len(sent) + 1 > chunk_size:
            chunks.append(" ".join(current))
            overlap_sents: List[str] = []
            overlap_len = 0
            for s in reversed(current):
                overlap_len += len(s) + 1
                overlap_sents.insert(0, s)
                if overlap_len >= overlap:
                    break
            current = overlap_sents
            current_len = sum(len(s) + 1 for s in current)
        current.append(sent)
        current_len += len(sent) + 1

    if current:
        chunks.append(" ".join(current))

    return [c for c in chunks if len(c) > 30]


def chunk_manual(pdf_path: Path, chunk_size: int, overlap: int) -> List[Chunk]:
    manual_label = label_from_filename(pdf_path.name)
    chunks: List[Chunk] = []
    for page_num, page_text in enumerate(extract_pages(pdf_path), start=1):
        if not page_text.strip():
            continue
        for piece in chunk_text(page_text, chunk_size, overlap):
            chunks.append(Chunk(text=piece, manual=manual_label, source_file=pdf_path.name, page=page_num))
    return chunks