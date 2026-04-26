import base64
import json
import re
import time
import urllib.request
from pathlib import Path

import fitz
import pymupdf4llm
import pdfplumber
from pdfminer.high_level import extract_pages
from pdfminer.layout import LAParams, LTTextBox
from langchain_core.documents import Document

from core.config import (
    POPPLER_PATH,
    OLLAMA_BASE_URL,
    OLLAMA_VISION_MODEL,
    VISION_EXTRACTION_PROMPT,
    BASE_DIR,
)

VISION_PAGE_DELAY = 5
VISION_MAX_RETRIES = 3
VISION_TIMEOUT = 300  # 5 minutes per page


def _is_scanned(file_path: Path) -> bool:
    doc = fitz.open(str(file_path))
    total = "".join(p.get_text() for p in doc)
    count = doc.page_count
    doc.close()
    return len(total.strip()) / max(count, 1) < 50


def _has_tables(file_path: Path) -> bool:
    doc = fitz.open(str(file_path))
    for page in doc:
        if page.find_tables().tables:
            doc.close()
            return True
    doc.close()
    return False


def _has_spaced_text(text: str) -> bool:
    words = text.split()
    if not words:
        return False
    single = sum(1 for w in words[:100] if len(w) == 1)
    return single / min(len(words), 100) > 0.3


def _normalize(text: str) -> str:
    return "\n".join(
        re.sub(r'\s+', ' ', line).strip()
        for line in text.splitlines()
        if re.sub(r'\s+', ' ', line).strip()
    )


def _is_quality(text: str) -> bool:
    words = text.split()
    if len(words) < 5:
        return False
    single = sum(1 for w in words[:30] if len(w) == 1)
    return single / min(len(words), 30) <= 0.6


def _call_vision(img_b64: str, page_num: int, total: int) -> str:
    payload = json.dumps({
        "model": OLLAMA_VISION_MODEL,
        "prompt": VISION_EXTRACTION_PROMPT,
        "images": [img_b64],
        "stream": False,
    }).encode()

    for attempt in range(1, VISION_MAX_RETRIES + 1):
        try:
            print(f"   👁️  Page {page_num}/{total} (attempt {attempt})...")
            req = urllib.request.Request(
                f"{OLLAMA_BASE_URL}/api/generate",
                data=payload,
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=VISION_TIMEOUT) as resp:
                result = json.loads(resp.read().decode())
            return result.get("response", "").strip()
        except Exception as e:
            print(f"   ⚠️  Page {page_num} attempt {attempt} failed: {e}")
            if attempt < VISION_MAX_RETRIES:
                wait = VISION_PAGE_DELAY * attempt * 2
                print(f"   ⏳ Waiting {wait}s before retry...")
                time.sleep(wait)

    print(f"   ❌ Page {page_num} failed after {VISION_MAX_RETRIES} attempts, skipping.")
    return ""


def _extract_vision(file_path: Path) -> list:
    try:
        from pdf2image import convert_from_path
    except ImportError:
        raise ImportError("Run: pip install pdf2image")

    print(f"   👁️  Vision extraction ({OLLAMA_VISION_MODEL}) — all pages...")

    kwargs = {"dpi": 200}
    if POPPLER_PATH:
        kwargs["poppler_path"] = POPPLER_PATH

    pages_img = convert_from_path(str(file_path), **kwargs)
    img_dir = BASE_DIR / "data"
    img_dir.mkdir(exist_ok=True)

    documents = []
    total = len(pages_img)

    for i, page_img in enumerate(pages_img):
        img_path = img_dir / f"_vision_p{i}.jpg"
        page_img.save(str(img_path), "JPEG")

        with open(str(img_path), "rb") as f:
            img_b64 = base64.b64encode(f.read()).decode()

        img_path.unlink(missing_ok=True)

        text = _call_vision(img_b64, i + 1, total)
        if text:
            documents.append(Document(
                page_content=text,
                metadata={"source": str(file_path), "page": i + 1, "extraction": "vision"},
            ))

        if i < total - 1:
            print(f"   ⏳ Waiting {VISION_PAGE_DELAY}s...")
            time.sleep(VISION_PAGE_DELAY)

    return documents


def _extract_layout(file_path: Path) -> list:
    print(f"   🔍 Layout analysis (PDFMiner)...")
    laparams = LAParams(char_margin=2.0, line_margin=0.5, word_margin=0.1, all_texts=True)
    documents = []

    for page_num, page_layout in enumerate(extract_pages(str(file_path), laparams=laparams)):
        elements = []
        for el in page_layout:
            if isinstance(el, LTTextBox):
                text = el.get_text().strip()
                if text:
                    elements.append((round(-el.y1, 0), round(el.x0, 0), text))
        if not elements:
            continue

        elements.sort(key=lambda e: (e[0], e[1]))
        rows, current_row, current_y = [], [], None
        for y, x, text in elements:
            if current_y is None or abs(y - current_y) <= 8:
                current_row.append((x, text))
                current_y = y
            else:
                rows.append(sorted(current_row))
                current_row, current_y = [(x, text)], y
        if current_row:
            rows.append(sorted(current_row))

        lines = [re.sub(r'\s+', ' ', " | ".join(t for _, t in row)).strip() for row in rows]
        page_text = "\n".join(l for l in lines if l)
        if page_text and _is_quality(page_text):
            documents.append(Document(
                page_content=page_text,
                metadata={"source": str(file_path), "page": page_num + 1, "extraction": "layout"},
            ))

    return documents


def load_pdf(file_path: Path) -> list:
    """
    Intelligent PDF loader — 4 strategies:
    1. Scanned PDF         → vision (all pages)
    2. Tables + spaced     → vision (all pages)
    3. Tables              → pdfplumber
    4. Plain text          → pymupdf4llm
    """
    if _is_scanned(file_path):
        print(f"   ⚠️  Scanned PDF → vision (all pages)...")
        return _extract_vision(file_path)

    if _has_tables(file_path):
        with pdfplumber.open(str(file_path)) as pdf:
            first = pdf.pages[0].extract_text() or ""

        if _has_spaced_text(first):
            print(f"   📊 Tables + encoding issue → vision (all pages)...")
            return _extract_vision(file_path)

        print(f"   📊 Tables → pdfplumber...")
        pages = []
        with pdfplumber.open(str(file_path)) as pdf:
            for i, page in enumerate(pdf.pages):
                parts = []
                if t := page.extract_text():
                    parts.append(_normalize(t))
                for table in page.extract_tables() or []:
                    if table:
                        parts.append("\n".join(" | ".join(c or "" for c in row) for row in table))
                if parts:
                    pages.append(Document(
                        page_content="\n\n".join(parts),
                        metadata={"source": str(file_path), "page": i + 1},
                    ))
        return pages

    print(f"   📄 Plain text → pymupdf4llm...")
    md = pymupdf4llm.to_markdown(str(file_path))
    if _has_spaced_text(md):
        print(f"   ⚠️  Encoding issue → vision (all pages)...")
        return _extract_vision(file_path)
    return [Document(page_content=_normalize(md), metadata={"source": str(file_path)})]